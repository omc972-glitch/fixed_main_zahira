import numpy as np
from scipy.optimize import least_squares
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

F_CONST, R, T = 96485.0, 8.314, 298.15

META = {
    "id": "impedimetri",
    "title": "İmpedimetri (EIS)",
    "subtitle": "Randles eşdeğer devresi: Rs + (Cdl ∥ (Rct + Zw))",
    "icon": "📡",
    "accent": "#c0392b",
    "zahira_key": "impedimetri",
    "info_html": build_info_html(
        "Elektrokimyasal Empedans Spektroskopisi",
        "Bir elektrot/çözelti arayüzünün direnç, kapasitans ve difüzyon özelliklerini frekans taramasıyla belirlemek.",
        "Z(ω) = Rs + 1 / (jωCdl + 1/(Rct + Zw)), Warburg: Zw = σ(1−j)/√ω. Nyquist grafiğinde yüksek frekansta "
        "Rs, yarım daire çapı Rct, düşük frekansta 45° difüzyon kuyruğu görülür. i₀ = RT/(nF·Rct).",
        ["Potansiyostat / FRA", "Çalışma, karşıt ve referans elektrot", "5 mM [Fe(CN)₆]³⁻/⁴⁻ + 0.1 M KCl"],
        ["Hücreyi kurun ve açık devre potansiyelini ölçün.", "10 mV AC genlik seçin.",
         "Frekansı yüksekten düşüğe tarayın.", "Nyquist ve Bode grafiklerini çizin.", "Randles devresine fit edin."],
        None, "#c0392b",
    ),
    "parameters": [
        {"key": "rs",   "label": "Çözelti direnci Rs",           "type": "slider", "min": 1,    "max": 1000,  "value": 50,  "step": 1,   "unit": "Ω"},
        {"key": "rct",  "label": "Yük transfer direnci Rct",     "type": "slider", "min": 10,   "max": 10000, "value": 1000,"step": 10,  "unit": "Ω"},
        {"key": "cdl",  "label": "Çift tabaka kapasitansı Cdl",  "type": "slider", "min": 0.1,  "max": 100,   "value": 10,  "step": 0.1, "unit": "µF"},
        {"key": "sig",  "label": "Warburg katsayısı σ",          "type": "slider", "min": 0,    "max": 1000,  "value": 150, "step": 1,   "unit": "Ω·s⁻¹ᐟ²"},
        {"key": "fmin", "label": "Min. frekans (log₁₀ Hz)",     "type": "slider", "min": -2.0, "max": 1.0,   "value": -2.0,"step": 0.5},
        {"key": "fmax", "label": "Maks. frekans (log₁₀ Hz)",    "type": "slider", "min": 2.0,  "max": 6.0,   "value": 6.0, "step": 0.5},
        {"key": "ppd",  "label": "Nokta / dekad",                "type": "int",    "min": 3,    "max": 20,    "value": 8},
        {"key": "noise","label": "Ölçüm gürültüsü",              "type": "slider", "min": 0,    "max": 5,     "value": 1,   "step": 0.1, "unit": "%"},
    ],
}


def randles(f, rs, rct, cdl, sigma):
    w  = 2 * np.pi * f
    zw = sigma * (1 - 1j) / np.sqrt(w)
    return rs + 1 / (1j * w * cdl + 1 / (rct + zw))


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z   = Zahira("impedimetri")
    rs  = float(params.get("rs",   50))
    rct = float(params.get("rct",  1000))
    cdl = float(params.get("cdl",  10))   # µF — converted below
    sig = float(params.get("sig",  150))
    fmin_log = float(params.get("fmin", -2.0))
    fmax_log = float(params.get("fmax",  6.0))
    ppd  = int(params.get("ppd",  8))
    noise = float(params.get("noise", 1))

    if fmax_log <= fmin_log:
        raise ValueError("Maksimum frekans minimum frekanstan büyük olmalıdır.")

    cdl_si = cdl * 1e-6  # F
    n_pts  = int((fmax_log - fmin_log) * ppd) + 1
    n_pts  = max(n_pts, 5)

    freq  = np.logspace(fmax_log, fmin_log, n_pts)   # high → low
    true_params = (rs, rct, cdl_si, sig)
    z_true = randles(freq, *true_params)

    rng = np.random.default_rng()
    nz  = noise / 100.0
    z_meas = (z_true.real * (1 + rng.normal(0, nz, n_pts))
              + 1j * z_true.imag * (1 + rng.normal(0, nz, n_pts)))

    zmax  = max(z_meas.real.max(), -z_meas.imag.min()) * 1.1
    zmin_abs = np.abs(z_meas).min() * 0.7
    zmax_abs = np.abs(z_meas).max() * 1.5

    frames, events = [], []
    prev_frac = 0.0

    for i in range(1, n_pts + 1):
        frac = i / float(n_pts)
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i - 1, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        z_i = z_meas[:i]
        traces = [
            # Nyquist (left panel)
            {
                "x": z_i.real.tolist(), "y": (-z_i.imag).tolist(),
                "mode": "markers", "name": "Nyquist",
                "marker": {"color": "#c0392b", "size": 5},
                "xaxis": "x", "yaxis": "y",
            },
            # Bode |Z| (right top)
            {
                "x": freq[:i].tolist(), "y": np.abs(z_i).tolist(),
                "mode": "markers+lines", "name": "|Z|",
                "marker": {"color": "#c0392b", "size": 3},
                "line": {"color": "#c0392b", "width": 1.5},
                "xaxis": "x2", "yaxis": "y2",
            },
            # Bode phase (right bottom)
            {
                "x": freq[:i].tolist(), "y": (-np.degrees(np.angle(z_i))).tolist(),
                "mode": "markers+lines", "name": "Faz",
                "marker": {"color": "#2980b9", "size": 3},
                "line": {"color": "#2980b9", "width": 1.5},
                "xaxis": "x3", "yaxis": "y3",
            },
        ]
        frames.append({
            "traces": traces,
            "layout": {
                "title": f"EIS Tarama — {freq[i-1]:.3g} Hz",
                "xaxis":  {"title": "Z' (Ω)", "domain": [0, 0.44], "range": [0, zmax]},
                "yaxis":  {"title": "−Z'' (Ω)", "range": [0, zmax]},
                "xaxis2": {"title": "", "domain": [0.56, 1.0], "anchor": "y2",
                           "type": "log", "range": [fmin_log, fmax_log]},
                "yaxis2": {"title": "|Z| (Ω)", "anchor": "x2", "domain": [0.52, 1.0],
                           "type": "log", "range": [np.log10(zmin_abs), np.log10(zmax_abs)]},
                "xaxis3": {"title": "f (Hz)", "domain": [0.56, 1.0], "anchor": "y3",
                           "type": "log", "range": [fmin_log, fmax_log]},
                "yaxis3": {"title": "−Faz (°)", "anchor": "x3", "domain": [0, 0.45],
                           "range": [0, 90]},
            },
        })

    # ── Fit (after scan) ──
    def resid(p):
        zf = randles(freq, p[0], p[1], 10 ** p[2], p[3])
        m  = np.abs(z_meas)
        return np.concatenate([(zf.real - z_meas.real) / m, (zf.imag - z_meas.imag) / m])

    x0  = [z_meas.real[0], max(z_meas.real.max() - z_meas.real[0], 1) * 0.8, -5, 100]
    fit = least_squares(resid, x0, bounds=([0, 0, -10, 0], [1e5, 1e6, -1, 1e5]))
    rs_f, rct_f, lc_f, sig_f = fit.x
    cdl_f = 10 ** lc_f

    # Dense fit curve for overlay
    ff   = np.logspace(fmax_log, fmin_log, 300)
    zfit = randles(ff, rs_f, rct_f, cdl_f, sig_f)

    # Append fit traces to last frame
    frames[-1]["traces"] += [
        {
            "x": zfit.real.tolist(), "y": (-zfit.imag).tolist(),
            "mode": "lines", "name": "Fit",
            "line": {"color": "black", "dash": "dash", "width": 1.5},
            "xaxis": "x", "yaxis": "y",
        },
        {
            "x": ff.tolist(), "y": np.abs(zfit).tolist(),
            "mode": "lines", "name": "Fit |Z|",
            "line": {"color": "black", "dash": "dash", "width": 1.5},
            "xaxis": "x2", "yaxis": "y2",
        },
        {
            "x": ff.tolist(), "y": (-np.degrees(np.angle(zfit))).tolist(),
            "mode": "lines", "name": "Fit faz",
            "line": {"color": "black", "dash": "dash", "width": 1.5},
            "xaxis": "x3", "yaxis": "y3",
        },
    ]

    i0 = R * T / (F_CONST * rct_f) if rct_f > 0 else float("inf")
    tau_rc = rct_f * cdl_f
    fc_rc  = 1 / (2 * np.pi * rct_f * cdl_f) if rct_f * cdl_f > 0 else float("inf")

    rows = [
        ("Rs (fit / gerçek)",   f"{rs_f:.1f} / {rs:.1f} Ω"),
        ("Rct (fit / gerçek)",  f"{rct_f:.1f} / {rct:.1f} Ω"),
        ("Cdl (fit / gerçek)",  f"{cdl_f*1e6:.2f} / {cdl:.2f} µF"),
        ("σ (fit / gerçek)",    f"{sig_f:.1f} / {sig:.1f}"),
        ("τ = Rct·Cdl",         f"{tau_rc:.3g} s"),
        ("Karakteristik frekans",f"{fc_rc:.3g} Hz"),
        ("i₀ (A=1 cm²)",        f"{i0:.3g} A/cm²"),
        ("Kinetik",             "Hızlı" if rct_f < 100 else ("Orta" if rct_f < 2000 else "Yavaş") + " yük transferi"),
    ]

    return {
        "start_lines":  _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say("finish",
                                        rs=rs_f, rct=rct_f, cdl=cdl_f*1e6,
                                        tau=tau_rc, fc=fc_rc, i0=i0)),
        "frames":       frames,
        "events":       events,
        "results_html": results_table(rows, "EIS Fit Sonuçları"),
    }
