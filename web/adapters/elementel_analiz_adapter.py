import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

AW = {"C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999, "S": 32.06}
PRESETS = [
    ("Kafein",         (8, 10, 4, 2, 0)),
    ("Aspirin",        (9,  8, 0, 4, 0)),
    ("Glukoz",         (6, 12, 0, 6, 0)),
    ("Parasetamol",    (8,  9, 1, 2, 0)),
    ("Sistein",        (3,  7, 1, 2, 1)),
    ("Özel (elle giriş)", None),
]
# TCD dedektörde çıkış sırası: N₂, CO₂, H₂O, SO₂
PEAKS = [("N₂", 1.2, 28), ("CO₂", 2.5, 44), ("H₂O", 4.0, 18), ("SO₂", 6.0, 64)]
# Zahira event key mapping (subscript → ASCII)
_PEAK_KEYS = {"N₂": "peak_N2", "CO₂": "peak_CO2", "H₂O": "peak_H2O", "SO₂": "peak_SO2"}

META = {
    "id": "elementel_analiz",
    "title": "Elementel Analiz",
    "subtitle": "CHN(S) yanma analizi ile bileşik doğrulama",
    "icon": "🔥",
    "accent": "#7f8c8d",
    "zahira_key": "elementel_analiz",
    "info_html": build_info_html(
        "CHN(S) Elementel Analiz",
        "Bir bileşiğin %C, %H, %N, %S içeriğini yanma analiziyle bulmak ve teorik değerlerle karşılaştırmak.",
        "Numune ~1000 °C'de O₂ ile yakılır: C→CO₂, H→H₂O, N→N₂, S→SO₂. Gazlar GC kolonunda ayrılıp "
        "TCD ile ölçülür. % Element = (n·Aᵢ / M)·100. Kabul kriteri: |bulunan − teorik| ≤ 0.3 %.",
        ["Mikroterazi", "Kalay kapsül", "CHNS analizörü", "Standart (asetanilid)", "He taşıyıcı gaz, O₂"],
        ["Cihazı standartla kalibre edin.", "1–5 mg numuneyi kapsüle tartın.", "Numuneyi yakma fırınına verin.",
         "Kromatogramdaki pikleri entegre edin.", "Sonuçları teorik değerle karşılaştırın."],
        None, "#7f8c8d",
    ),
    "parameters": [
        {"key": "preset", "label": "Hazır bileşik", "type": "select", "value": 0,
         "options": [{"label": p[0], "value": i} for i, p in enumerate(PRESETS)]},
        {"key": "w",  "label": "Numune ağırlığı", "type": "slider", "min": 0.5, "max": 5.0, "value": 2.0, "step": 0.1, "unit": "mg"},
        {"key": "C",  "label": "C atom sayısı",   "type": "int",    "min": 0, "max": 100, "value": 8},
        {"key": "H",  "label": "H atom sayısı",   "type": "int",    "min": 0, "max": 100, "value": 10},
        {"key": "N",  "label": "N atom sayısı",   "type": "int",    "min": 0, "max": 100, "value": 4},
        {"key": "O",  "label": "O atom sayısı",   "type": "int",    "min": 0, "max": 100, "value": 2},
        {"key": "S",  "label": "S atom sayısı",   "type": "int",    "min": 0, "max": 100, "value": 0},
        {"key": "sd", "label": "Cihaz hatası (σ)","type": "slider", "min": 0.0,"max": 0.5,"value": 0.12,"step": 0.01,"unit": "%"},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("elementel_analiz")

    preset_idx = int(params.get("preset", 0))
    if PRESETS[preset_idx][1] is not None:
        C, H, N_at, O_at, S = PRESETS[preset_idx][1]
    else:
        C    = int(params.get("C", 8))
        H    = int(params.get("H", 10))
        N_at = int(params.get("N", 4))
        O_at = int(params.get("O", 2))
        S    = int(params.get("S", 0))

    n = {"C": C, "H": H, "N": N_at, "O": O_at, "S": S}

    if sum(n.values()) == 0:
        raise ValueError("En az bir element için atom sayısı girilmelidir.")
    if n["C"] == 0:
        raise ValueError("CHN analizi için bileşik en az bir karbon atomu içermelidir.")

    w  = float(params.get("w",  2.0))
    sd = float(params.get("sd", 0.12))

    mw   = sum(n[e] * AW[e] for e in n)
    theo = {e: n[e] * AW[e] / mw * 100 for e in "CHNS"}

    rng   = np.random.default_rng()
    found = {e: (max(0.0, v + rng.normal(0, sd)) if v > 0 else 0.0) for e, v in theo.items()}

    mol = w / mw  # mmol
    gas = {
        "N₂":  mol * n["N"] / 2,
        "CO₂": mol * n["C"],
        "H₂O": mol * n["H"] / 2,
        "SO₂": mol * n["S"],
    }

    tt  = np.linspace(0, 7.5, 151)
    sig = sum(gas[g] * np.exp(-((tt - t0) / 0.12) ** 2) for g, t0, _ in PEAKS)
    sig_max = max(sig.max(), 1e-6) * 1.2

    frames, events = [], []
    prev_frac = 0.0
    fired_peaks = set()

    for i in range(len(tt)):
        frac = i / float(len(tt) - 1)
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        # peak events
        for g, t0, _ in PEAKS:
            key = _PEAK_KEYS[g]
            if key not in fired_peaks and tt[i] >= t0 and gas[g] > 0:
                fired_peaks.add(key)
                ev_lines = _to_lines(z.say(key))
                events.append({"id": key, "frame": i, "kind": "event", "lines": ev_lines})

        frames.append({
            "traces": [{
                "x": tt[:i + 1].tolist(),
                "y": sig[:i + 1].tolist(),
                "mode": "lines",
                "name": "TCD Sinyali",
                "line": {"color": "#7f8c8d", "width": 2.5},
            }],
            "layout": {
                "title": f"TCD Kromatogramı — {tt[i]:.2f} dk",
                "xaxis": {"title": "Zaman (dk)", "range": [0, 7.5]},
                "yaxis": {"title": "Sinyal",     "range": [0, sig_max]},
            },
        })

    # Build results HTML (matches on_simulation_finished logic)
    formula = "".join(
        f"{e}{n[e]}" if n[e] > 1 else (e if n[e] == 1 else "")
        for e in "CHNOS"
        if n[e] > 0
    )
    els = [e for e in "CHNS" if theo[e] > 0 or e in "CHN"]
    ok_all = True

    html  = results_table([
        ("Formül",     formula),
        ("Mol kütlesi",f"{mw:.3f} g/mol"),
        ("Numune",     f"{w:.3f} mg ({w/mw:.4f} mmol)"),
    ], "Bileşik")
    html += ("<h3>Karşılaştırma</h3><table width='100%' cellpadding='3'>"
             "<tr><th>El.</th><th>Teorik</th><th>Bulunan</th><th>Δ</th><th>Durum</th></tr>")
    for e in els:
        d  = found[e] - theo[e]
        ok = abs(d) <= 0.3
        ok_all &= ok
        col = "green" if ok else "red"
        sym = "✔" if ok else "✘"
        html += (f"<tr><td>{e}</td><td>{theo[e]:.2f}</td><td>{found[e]:.2f}</td>"
                 f"<td>{d:+.2f}</td><td style='color:{col}'>{sym}</td></tr>")
    html += "</table><p><b>Sonuç:</b> "
    if ok_all:
        html += "<span style='color:green'>Bileşik doğrulandı (tüm sapmalar ≤ 0.3 %).</span>"
    else:
        html += "<span style='color:red'>Kabul kriteri sağlanmadı — saflığı kontrol edin / tekrarlayın.</span>"
    html += "</p>"

    fin_key   = "finish_ok" if ok_all else "finish_fail"
    fin_lines = _to_lines(z.say(fin_key, formula=formula, mw=mw))

    return {
        "start_lines":  _to_lines(z.say("start")),
        "finish_lines": fin_lines,
        "frames":       frames,
        "events":       events,
        "results_html": html,
    }
