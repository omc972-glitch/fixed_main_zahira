import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

META = {
    "id": "coumarin",
    "title": "Kumarin Sentezi",
    "subtitle": "Pechmann yoğunlaşması ve UV floresans karakterizasyonu",
    "icon": "✨",
    "accent": "#d35400",
    "zahira_key": "coumarin",
    "info_html": build_info_html(
        "Kumarin Sentezi",
        "Pechmann yoğunlaşması ile kumarin türevi sentezlemek ve floresans emisyonunu incelemek.",
        "Resorsinol ve etil asetoasetat asit katalizörlüğünde yoğunlaşarak 4-metilumbelliferon (kumarin türevi) oluşturur.",
        ["Resorsinol", "Etil asetoasetat", "Katalizör asit", "Reflü düzeneği", "UV lamba (365 nm)"],
        ["Reaktifleri soğukta karıştırın.", "Katalizörü yavaşça ekleyin.", "Karışımı ısıtarak reaksiyonu tamamlayın.",
         "Buzlu suya döküp ürünü süzün ve UV altında floresansı gözlemleyin."],
        "UV ışığına doğrudan bakmayın; koruyucu gözlük takın.", "#d35400",
    ),
    "parameters": [
        {"key": "temp", "label": "Reaksiyon sıcaklığı", "type": "slider", "min": 25.0, "max": 90.0, "value": 60.0, "step": 5.0, "unit": "°C"},
        {"key": "time_min", "label": "Reaksiyon süresi", "type": "slider", "min": 15.0, "max": 90.0, "value": 45.0, "step": 5.0, "unit": "dk"},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("coumarin")
    temp = float(params["temp"])
    time_min = float(params["time_min"])

    k = 0.04 * np.exp((temp - 55.0) / 22.0)
    t = np.linspace(0, time_min, 75)
    y = (1.0 - np.exp(-k * t)) * 90.0
    final_y = float(y[-1])

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
                "y": y[:i].tolist(),
                "mode": "lines",
                "name": "Kumarin Verimi (%)",
                "line": {"color": "#d35400", "width": 2.5},
            }],
            "layout": {
                "title": f"Kumarin Sentezi — {t[i-1]:.1f} dk ({temp:.0f} °C)",
                "xaxis": {"title": "Reaksiyon Süresi (dk)", "range": [0, time_min]},
                "yaxis": {"title": "Verim (%)", "range": [0, 100]},
            },
        })

    for _si, _fr in enumerate((0.05, 0.28, 0.52, 0.76)):
        events.append({"id": f"step_{_si}", "frame": max(0, int(_fr * len(t)) - 1), "kind": "event",
                       "lines": _to_lines(z.say(f"step_{_si}"))})

    rows = [
        ("Reaksiyon Sıcaklığı", f"{temp:.0f} °C"),
        ("Reaksiyon Süresi", f"{time_min:.0f} dk"),
        ("Yüzde Verim", f"%{final_y:.1f}"),
        ("UV Floresans (365 nm)", "Parlak Mavi Emisyon"),
    ]
    return {
        "start_lines": _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say("finish", name="7-hidroksi-4-metilkumarin (4-metilumbelliferon)", conv=(1.0 - float(np.exp(-k * t[-1]))) * 100.0, yield_pct=final_y, mp="yaklaşık 185–187 °C") + (z.say("warn_side") if temp > 85 else [])),
        "frames": frames,
        "events": events,
        "results_html": results_table(rows),
    }

# KONUSMA-FIX-V1
