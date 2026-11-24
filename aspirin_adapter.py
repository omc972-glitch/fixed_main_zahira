import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

META = {
    "id": "aspirin",
    "title": "Aspirin Sentezi",
    "subtitle": "Salisilik asit + asetik anhidrit → asetilsalisilik asit",
    "icon": "💊",
    "accent": "#8e44ad",
    "zahira_key": "aspirin",
    "info_html": build_info_html(
        "Aspirin (Asetilsalisilik Asit) Sentezi",
        "Salisilik asidin asetik anhidrit ile esterleştirilerek aspirin sentezlenmesi ve verim analizi.",
        "H₂SO₄ veya H₃PO₄ katalizörlüğünde fenolik –OH grubu asetillenir. Sıcaklık ve katalizör reaksiyon hızını ve verimi belirler.",
        ["Salisilik asit", "Asetik anhidrit", "Derişik H₂SO₄ (katalizör)", "Su banyosu", "Buz banyosu", "Büchner hunisi"],
        ["Salisilik asidi ve asetik anhidriti erlene alın.", "Katalizör ekleyin ve su banyosunda ısıtın.",
         "Soğutup buzlu su ekleyerek kristallendirin.", "Vakumla süzüp kurutun ve verimi hesaplayın."],
        "Asetik anhidrit ve H₂SO₄ aşındırıcıdır; çeker ocakta çalışın.", "#8e44ad",
    ),
    "parameters": [
        {"key": "mass_sa", "label": "Salisilik asit kütlesi", "type": "slider", "min": 1.0, "max": 10.0, "value": 2.0, "step": 0.5, "unit": "g"},
        {"key": "temp", "label": "Su banyosu sıcaklığı", "type": "slider", "min": 40.0, "max": 95.0, "value": 75.0, "step": 5.0, "unit": "°C"},
        {"key": "catalyst", "label": "H₂SO₄ katalizörü kullan", "type": "checkbox", "value": True},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("aspirin")
    mass_sa = float(params["mass_sa"])
    temp = float(params["temp"])
    catalyst = bool(params.get("catalyst", True))

    mol_sa = mass_sa / 138.12
    theo_mass = mol_sa * 180.16
    k = (0.08 if catalyst else 0.015) * np.exp((temp - 70.0) / 25.0)
    t = np.linspace(0, 30, 80)
    conv = 1.0 - np.exp(-k * t)
    max_eff = 0.88 if temp <= 85 else max(0.65, 0.88 - (temp - 85) * 0.015)
    yield_pct = float(conv[-1] * max_eff * 100.0)
    actual_mass = theo_mass * (yield_pct / 100.0)

    frames, events = [], []
    prev_frac = 0.0
    for i in range(1, len(t) + 1):
        frac = i / float(len(t))
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i - 1, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        frames.append({
            "traces": [{
                "x": t[:i].tolist(),
                "y": (conv[:i] * max_eff * 100.0).tolist(),
                "mode": "lines",
                "name": "Aspirin Verimi (%)",
                "line": {"color": "#8e44ad", "width": 2.5},
            }],
            "layout": {
                "title": f"Aspirin Sentezi — {t[i-1]:.1f} dk ({temp:.0f} °C)",
                "xaxis": {"title": "Reaksiyon Süresi (dk)", "range": [0, 30]},
                "yaxis": {"title": "Verim (%)", "range": [0, 100]},
            },
        })

    rows = [
        ("Salisilik Asit", f"{mass_sa:.2f} g ({mol_sa*1000:.2f} mmol)"),
        ("Teorik Aspirin Kütlesi", f"{theo_mass:.2f} g"),
        ("Elde Edilen Aspirin", f"{actual_mass:.2f} g"),
        ("Yüzde Verim", f"%{yield_pct:.1f}"),
        ("Katalizör", "Var (H₂SO₄)" if catalyst else "Yok"),
    ]
    start_key = "start_cat" if catalyst else "start_nocat"
    return {
        "start_lines": _to_lines(z.say(start_key)),
        "finish_lines": _to_lines(z.say("finish", limname="salisilik asit", conv=float(conv[-1]) * 100.0, theo=theo_mass, prac=actual_mass, yield_pct=yield_pct) + (z.say("warn_high_T") if temp > 90 else [])),
        "frames": frames,
        "events": events,
        "results_html": results_table(rows),
    }

# KONUSMA-FIX-V1
