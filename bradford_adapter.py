import numpy as np
from scipy.stats import linregress
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

META = {
    "id": "bradford",
    "title": "Bradford Deneyi",
    "subtitle": "Coomassie Brilliant Blue G-250 ile protein tayini (595 nm)",
    "icon": "🧬",
    "accent": "#2980b9",
    "zahira_key": "bradford",
    "info_html": build_info_html(
        "Bradford Protein Tayini",
        "BSA standartlarıyla kalibrasyon eğrisi oluşturup bilinmeyen numunenin protein derişimini bulmak.",
        "Coomassie boyası proteine bağlanınca maksimum absorbansı 465 nm'den 595 nm'ye kayar. "
        "Beer–Lambert: A = ε·b·c; doğrusal bölgede A ile derişim orantılıdır.",
        ["BSA stok (2 mg/mL)", "Bradford reaktifi", "Test tüpleri / küvet", "Spektrofotometre", "Mikropipet"],
        ["0–2 mg/mL aralığında BSA standartları hazırlayın.", "Her tüpe Bradford reaktifi ekleyin.",
         "5 dk inkübe edin.", "595 nm'de absorbansları okuyun.", "Kalibrasyon doğrusundan numuneyi hesaplayın."],
        None, "#2980b9",
    ),
    "parameters": [
        {"key": "cmax", "label": "En yüksek standart", "type": "slider", "min": 0.5, "max": 2.0, "value": 2.0, "step": 0.05, "unit": "mg/mL"},
        {"key": "n", "label": "Standart sayısı", "type": "int", "min": 4, "max": 10, "value": 6},
        {"key": "cs", "label": "Numune derişimi (gerçek)", "type": "slider", "min": 0.0, "max": 2.0, "value": 0.85, "step": 0.05, "unit": "mg/mL"},
        {"key": "noise", "label": "Ölçüm gürültüsü", "type": "slider", "min": 0.0, "max": 10.0, "value": 2.0, "step": 0.5, "unit": "%"},
    ],
}


def _absorb(c):
    return 0.05 + 0.55 * c


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("bradford")
    cmax = float(params["cmax"])
    n = int(params["n"])
    cs = float(params["cs"])
    noise = float(params["noise"])

    rng = np.random.default_rng(params.get("seed"))
    conc = np.linspace(0, cmax, n)
    nz = noise / 100.0
    abs_vals = _absorb(conc) * (1 + rng.normal(0, nz, n))
    a_s = float(_absorb(cs) * (1 + rng.normal(0, nz)))

    r = linregress(conc, abs_vals)
    xs = np.linspace(0, conc[-1], 50)
    cs_calc = float((a_s - r.intercept) / r.slope)
    r2 = float(r.rvalue ** 2)

    frames, events = [], []
    prev_frac = 0.0
    xmax = max(cmax, cs, cs_calc) * 1.15
    ymax = _absorb(2.0) * 1.25

    for k in range(1, n + 2):
        frac = k / float(n + 1)
        traces = [{
            "x": conc[: min(k, n)].tolist(),
            "y": abs_vals[: min(k, n)].tolist(),
            "mode": "markers",
            "name": "BSA Standartları",
            "marker": {"color": "#2980b9", "size": 9},
        }]
        if k >= n + 1:
            traces.append({
                "x": xs.tolist(),
                "y": (r.intercept + r.slope * xs).tolist(),
                "mode": "lines",
                "name": f"A = {r.slope:.3f}c + {r.intercept:.3f}",
                "line": {"color": "gray", "dash": "dash"},
            })
            traces.append({
                "x": [cs_calc],
                "y": [a_s],
                "mode": "markers",
                "name": "Numune",
                "marker": {"color": "red", "symbol": "star", "size": 14},
            })

        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{k}", "frame": k - 1, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        frames.append({
            "traces": traces,
            "layout": {
                "title": "Bradford Kalibrasyon Eğrisi (595 nm)",
                "xaxis": {"title": "Protein Derişimi (mg/mL)", "range": [0, xmax]},
                "yaxis": {"title": "Absorbans (595 nm)", "range": [0, ymax]},
            },
        })

    err = abs(cs_calc - cs) / cs * 100.0 if cs > 0 else 0.0
    rows = [
        ("Eğim (m)", f"{r.slope:.4f}"),
        ("Kesişim (b)", f"{r.intercept:.4f}"),
        ("R²", f"{r2:.5f}"),
        ("Numune Absorbansı", f"{a_s:.4f}"),
        ("Hesaplanan Derişim", f"{cs_calc:.3f} mg/mL"),
        ("Bağıl Hata", f"%{err:.2f}"),
    ]

    return {
        "start_lines": _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say("finish", cs_calc=cs_calc, cs_true=cs, r2=r2) + (z.say("tip_noise") if r2 < 0.98 else []) + (z.say("warn_range") if not (0.0 <= cs_calc <= cmax) else [])),
        "frames": frames,
        "events": events,
        "results_html": results_table(rows),
    }

# KONUSMA-FIX-V1
