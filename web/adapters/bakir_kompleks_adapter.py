import numpy as np
from scipy.optimize import brentq
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

LOGK = np.array([4.31, 3.67, 3.04, 2.30])
BETA = np.concatenate([[1.0], 10 ** np.cumsum(LOGK)])
NAMES = ["Cu²⁺(aq)", "[Cu(NH₃)]²⁺", "[Cu(NH₃)₂]²⁺", "[Cu(NH₃)₃]²⁺", "[Cu(NH₃)₄]²⁺"]
LMAX = np.array([800, 745, 700, 650, 610])
EPS  = np.array([12,  25,  40,  50,  55])
COLS = np.array([
    [0.62, 0.85, 0.95],
    [0.45, 0.70, 0.92],
    [0.30, 0.50, 0.85],
    [0.20, 0.30, 0.75],
    [0.12, 0.12, 0.60],
])
_CSS = [f"rgb({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)})" for c in COLS]
_COLOR_NAMES = ["Açık mavi", "Mavi", "Koyu mavi", "Kobalt mavisi", "Koyu lacivert/mor-mavi"]

META = {
    "id": "bakir_kompleks",
    "title": "Tetra Amin Bakır(II) Kompleksi",
    "subtitle": "Cu²⁺ + 4 NH₃ ⇌ [Cu(NH₃)₄]²⁺ — basamaklı kompleks oluşumu",
    "icon": "🫙",
    "accent": "#1f3a93",
    "zahira_key": "bakir_kompleks",
    "info_html": build_info_html(
        "[Cu(NH₃)₄]²⁺ Kompleksi",
        "Amonyak eklendikçe bakır(II) amin komplekslerinin basamaklı oluşumunu, renk ve spektrum değişimini incelemek.",
        "Basamaklı kararlılık sabitleri: log K₁=4.31, K₂=3.67, K₃=3.04, K₄=2.30; log β₄ = 13.32. "
        "Ligand alan kuvveti arttıkça d–d geçişi kısa dalga boyuna kayar (≈800 → 610 nm), renk açık maviden koyu laciverte döner.",
        ["CuSO₄·5H₂O", "Derişik NH₃ çözeltisi", "Beher", "UV-Vis spektrofotometre", "Etanol (kristallendirme)"],
        ["CuSO₄ çözeltisi hazırlayın.", "NH₃'ü damla damla ekleyin (önce Cu(OH)₂ çökeleği görülür).",
         "Fazla NH₃ ile koyu mavi çözelti oluşur.", "Spektrumu alın.", "Etanol ekleyerek kompleksi kristallendirin."],
        "Derişik amonyak buharı tahriş edicidir; çeker ocakta çalışın.", "#1f3a93",
    ),
    "parameters": [
        {"key": "cu",  "label": "Cu²⁺ derişimi",           "type": "slider", "min": 0.001, "max": 0.1,  "value": 0.05, "step": 0.001, "unit": "M"},
        {"key": "eq",  "label": "NH₃ eşdeğeri",             "type": "slider", "min": 0.0,   "max": 4.0,  "value": 4.0,  "step": 0.1,  "unit": "eşd."},
        {"key": "xs",  "label": "Fazla NH₃ (ek eşdeğer)",   "type": "slider", "min": 0.0,   "max": 20.0, "value": 0.0,  "step": 0.5,  "unit": "eşd."},
    ],
}


def speciation(cu, nh3):
    if nh3 <= 0:
        return np.array([1.0, 0, 0, 0, 0])
    def f(logL):
        L = 10 ** logL
        terms = BETA * L ** np.arange(5)
        return L + cu * (np.arange(5) * terms).sum() / terms.sum() - nh3
    L = 10 ** brentq(f, -14, np.log10(nh3) + 0.01)
    terms = BETA * L ** np.arange(5)
    return terms / terms.sum()


def _spectrum(fr, cu):
    wl = np.linspace(450, 900, 300)
    A = sum(fr[k] * EPS[k] * cu * np.exp(-((wl - LMAX[k]) / 90) ** 2) for k in range(5))
    return wl, A


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("bakir_kompleks")
    cu     = float(params.get("cu",  0.05))
    eq     = float(params.get("eq",  4.0))
    xs     = float(params.get("xs",  0.0))
    target = eq + xs
    eqs    = np.linspace(0, max(target, 0.01), 101)
    fr_all = np.array([speciation(cu, e * cu) for e in eqs])

    wl_arr = np.linspace(450, 900, 300)
    amax_global = max(EPS) * cu * 1.15

    frames, events = [], []
    prev_dom = -1
    prev_frac = 0.0

    for i in range(len(eqs)):
        frac = i / float(len(eqs) - 1)
        fr_i = fr_all[i]
        dom_i = int(np.argmax(fr_i))

        # species change event
        if dom_i != prev_dom:
            prev_dom = dom_i
            ev_lines = _to_lines(z.say(f"species_{dom_i}"))
            if ev_lines:
                events.append({"id": f"species_{dom_i}", "frame": i, "kind": "event", "lines": ev_lines})

        # progress events
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        # species fraction traces (left panel)
        traces = []
        for k in range(5):
            traces.append({
                "x": eqs[:i + 1].tolist(),
                "y": fr_all[:i + 1, k].tolist(),
                "mode": "lines",
                "name": NAMES[k],
                "line": {"color": _CSS[k], "width": 2},
                "xaxis": "x",
                "yaxis": "y",
            })

        # absorbance spectrum (right panel)
        _, A_i = _spectrum(fr_i, cu)
        traces.append({
            "x": wl_arr.tolist(),
            "y": A_i.tolist(),
            "mode": "lines",
            "name": "Absorbans",
            "line": {"color": "#1f3a93", "width": 2.5},
            "xaxis": "x2",
            "yaxis": "y2",
        })

        frames.append({
            "traces": traces,
            "layout": {
                "title": f"NH₃: {eqs[i]:.2f} eşd. — Baskın: {NAMES[dom_i]}",
                "xaxis":  {"title": "NH₃ eşdeğeri", "domain": [0, 0.44], "range": [0, max(target, 0.1)]},
                "yaxis":  {"title": "Kesir", "range": [0, 1.05]},
                "xaxis2": {"title": "λ (nm)", "domain": [0.56, 1.0], "anchor": "y2", "range": [450, 900]},
                "yaxis2": {"title": f"A (b=1 cm, [Cu]={cu:.3f} M)", "anchor": "x2", "range": [0, amax_global]},
                "showlegend": True,
                "legend": {"x": 0.0, "y": -0.15, "orientation": "h"},
            },
        })

    # finish
    fr_fin = fr_all[-1]
    dom    = int(np.argmax(fr_fin))
    color  = _COLOR_NAMES[dom]
    wl_fin, A_fin = _spectrum(fr_fin, cu)
    lmax_peak = float(wl_fin[np.argmax(A_fin)])
    amax_val  = float(A_fin.max())
    log_b4    = float(np.log10(BETA[4]))

    rows = [
        ("Baskın tür",   NAMES[dom]),
        ("Renk",         color),
        ("λmax",         f"{lmax_peak:.0f} nm"),
        ("Amax",         f"{amax_val:.3f}"),
        ("log β₄",       f"{log_b4:.2f}"),
    ]
    for k in range(5):
        rows.append((f"% {NAMES[k]}", f"{fr_fin[k]*100:.1f}"))
    for k in range(4):
        rows.append((f"K{k+1}", f"10^{LOGK[k]:.2f}"))

    fin_lines = _to_lines(z.say("finish",
        dom_name=NAMES[dom], color=color, lmax=lmax_peak, amax=amax_val, log_beta4=log_b4))
    if dom == 4:
        fin_lines += _to_lines(z.say("finish_tetra"))

    return {
        "start_lines":  _to_lines(z.say("start")),
        "finish_lines": fin_lines,
        "frames":       frames,
        "events":       events,
        "results_html": results_table(rows, "Kompleks Sonuçları"),
    }
