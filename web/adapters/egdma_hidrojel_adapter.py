import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

R, TEMP, RHO, M0, V1, CHI = 8.314, 298.15, 1.15, 130.14, 18.0, 0.45

META = {
    "id": "egdma_hidrojel",
    "title": "EGDMA Hidrojel Deneyi",
    "subtitle": "Etilen glikol dimetakrilat ile çapraz bağlı (p)HEMA hidrojel",
    "icon": "🫧",
    "accent": "#16a085",
    "zahira_key": "egdma_hidrojel",
    "info_html": build_info_html(
        "EGDMA Çapraz Bağlı Hidrojel",
        "Çapraz bağlayıcı oranının polimerizasyon, şişme ve mekanik özelliklere etkisini incelemek.",
        "Serbest radikal polimerizasyonunda dönüşüm p(t)=1−e^(−kt), k ∝ √[I]. Flory–Rehner: "
        "Q^(5/3) ≈ (½−χ)/(V₁·νₑ). Kauçuk elastisitesi: E = 3νₑRT·Q^(−1/3). Mc = ρ/νₑ.",
        ["HEMA monomeri", "EGDMA (çapraz bağlayıcı)", "APS / TEMED (başlatıcı)", "Kalıp", "Saf su", "Terazi"],
        ["Monomer, EGDMA ve suyu karıştırın.", "Başlatıcıyı ekleyip kalıba dökün.", "Belirtilen sürede polimerleştirin.",
         "Jeli kurutup tartın (W₀).", "Suda bekletip aralıklarla tartın: Q = W/W₀."],
        "Metakrilatlar hassasiyet yapabilir; eldiven kullanın.", "#16a085",
    ),
    "parameters": [
        {"key": "x",  "label": "EGDMA miktarı",         "type": "slider", "min": 0.5,  "max": 10.0, "value": 2.0, "step": 0.1,  "unit": "mol%"},
        {"key": "m",  "label": "Monomer derişimi",       "type": "slider", "min": 0.5,  "max": 6.0,  "value": 3.0, "step": 0.1,  "unit": "M"},
        {"key": "i",  "label": "Başlatıcı (APS)",        "type": "slider", "min": 0.1,  "max": 2.0,  "value": 0.5, "step": 0.05, "unit": "ağ.%"},
        {"key": "tp", "label": "Polimerizasyon süresi",  "type": "slider", "min": 5.0,  "max": 120.0,"value": 60.0,"step": 1.0,  "unit": "dk"},
    ],
}


def network(egdma_pct, mono, conv):
    """Etkin ağ yoğunluğu (mol/cm³), denge şişme oranı, Young modülü (kPa)."""
    eff = 0.6 * mono / (mono + 1.5)
    nu  = max(2 * (egdma_pct / 100) * RHO / M0 * conv * eff, 1e-7)
    q   = ((0.5 - CHI) / (V1 * nu)) ** 0.6
    q   = max(q, 1.05)
    E   = 3 * nu * 1e6 * R * TEMP * q ** (-1 / 3) / 1000
    return nu, q, E


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z   = Zahira("egdma_hidrojel")
    x   = float(params.get("x",  2.0))
    m   = float(params.get("m",  3.0))
    ini = float(params.get("i",  0.5))
    tp  = float(params.get("tp", 60.0))

    k    = 0.04 * np.sqrt(ini / 0.5) * (m / 3.0) ** 0.5
    t_p  = np.linspace(0, tp, 81)
    conv = 1 - np.exp(-k * t_p)
    nu, qeq, E = network(x, m, conv[-1])
    tau  = 1.0 + 0.25 * qeq
    t_s  = np.linspace(0, 24, 81)
    q_sw = 1 + (qeq - 1) * (1 - np.exp(-t_s / tau))
    mc   = RHO / nu

    n_frames = 2 * 81  # 162 total
    frames, events = [], []
    prev_frac = 0.0
    swelling_fired = False

    for frame in range(n_frames):
        frac = frame / float(n_frames - 1)

        # progress events
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{frame}", "frame": frame, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        traces = []

        if frame < 81:
            # Polimerizasyon: left panel (conversion)
            traces.append({
                "x": t_p[:frame + 1].tolist(),
                "y": (conv[:frame + 1] * 100).tolist(),
                "mode": "lines",
                "name": "Dönüşüm (%)",
                "line": {"color": "#16a085", "width": 2.5},
                "xaxis": "x",
                "yaxis": "y",
            })
            # right panel: placeholder (empty swelling trace)
            traces.append({
                "x": [],
                "y": [],
                "mode": "lines",
                "name": "Şişme oranı Q",
                "line": {"color": "#2980b9", "width": 2.5},
                "xaxis": "x2",
                "yaxis": "y2",
            })
            title = f"Polimerizasyon — {t_p[frame]:.1f} dk | Dönüşüm: %{conv[frame]*100:.1f}"
        else:
            if not swelling_fired:
                swelling_fired = True
                ev_lines = _to_lines(z.say("swelling_start"))
                events.append({"id": "swelling_start", "frame": frame, "kind": "event", "lines": ev_lines})

            j = frame - 81
            # left panel: completed polymerization curve
            traces.append({
                "x": t_p.tolist(),
                "y": (conv * 100).tolist(),
                "mode": "lines",
                "name": "Dönüşüm (%)",
                "line": {"color": "#16a085", "width": 2.5},
                "xaxis": "x",
                "yaxis": "y",
            })
            # right panel: swelling kinetics
            traces.append({
                "x": t_s[:j + 1].tolist(),
                "y": q_sw[:j + 1].tolist(),
                "mode": "lines",
                "name": "Şişme oranı Q",
                "line": {"color": "#2980b9", "width": 2.5},
                "xaxis": "x2",
                "yaxis": "y2",
            })
            title = f"Şişme — {t_s[j]:.1f} sa | Q = {q_sw[j]:.2f}"

        frames.append({
            "traces": traces,
            "layout": {
                "title": title,
                "xaxis":  {"title": "Polimerizasyon süresi (dk)", "domain": [0, 0.44],
                           "range": [0, tp]},
                "yaxis":  {"title": "Dönüşüm (%)", "range": [0, 105]},
                "xaxis2": {"title": "Şişme süresi (sa)", "domain": [0.56, 1.0],
                           "anchor": "y2", "range": [0, 24]},
                "yaxis2": {"title": "Şişme oranı Q", "anchor": "x2",
                           "range": [0, qeq * 1.1 + 0.5]},
            },
        })

    # results
    rows = [
        ("Son dönüşüm",             f"{conv[-1]*100:.1f} %"),
        ("Denge şişme oranı Qₑ",   f"{qeq:.2f}"),
        ("Ağ yoğunluğu νₑ",        f"{nu:.2e} mol/cm³"),
        ("Mc (çapraz bağlar arası)",f"{mc:.0f} g/mol"),
        ("Young modülü E",          f"{E:.1f} kPa"),
        ("Su içeriği (denge)",      f"{(1 - 1/qeq)*100:.1f} %"),
    ]
    if conv[-1] < 0.5:
        rows.append(("Uyarı", "Düşük dönüşüm — jel noktası oluşmayabilir"))

    if conv[-1] < 0.5:
        fin_lines = _to_lines(z.say("warn_low_conv"))
    else:
        fin_lines = _to_lines(z.say("finish", qeq=qeq, E=E, mc=mc))

    return {
        "start_lines":  _to_lines(z.say("start")),
        "finish_lines": fin_lines,
        "frames":       frames,
        "events":       events,
        "results_html": results_table(rows, "Hidrojel Sonuçları"),
    }
