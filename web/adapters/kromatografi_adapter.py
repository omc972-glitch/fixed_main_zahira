import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

META = {
    "id": "kromatografi",
    "title": "Kolon Kromatografisi",
    "subtitle": "İki bileşenli karışımın kolonda ayrılması ve çözünürlük (Rs)",
    "icon": "📊",
    "accent": "#27ae60",
    "zahira_key": "kromatografi",
    "info_html": build_info_html(
        "Kolon Kromatografisi",
        "İki bileşenin sabit ve hareketli faz arasındaki dağılma farkından yararlanarak ayrılmasını incelemek.",
        "Alıkonma zamanı tR, kuramsal plaka sayısı N ve çözünürlük Rs = 2(tR2 - tR1) / (w1 + w2) ile ayrım kalitesi ölçülür. Rs ≥ 1.5 taban çizgisi ayrımıdır.",
        ["Kromatografi kolonu", "Dedektör", "Hareketli faz (elüent)", "Enjektör", "Karışım numunesi"],
        ["Kolonu hareketli faz ile dengeleyin.", "Numuneyi enjekte edin.", "Dedektör sinyalini zamana karşı kaydedin.",
         "Piklerin alıkonma zamanlarını ve çözünürlüğünü hesaplayın."],
        "Organik çözücüleri çeker ocakta kullanın.", "#27ae60",
    ),
    "parameters": [
        {"key": "tr1", "label": "1. Bileşen tR1", "type": "slider", "min": 2.0, "max": 10.0, "value": 4.5, "step": 0.2, "unit": "dk"},
        {"key": "tr2", "label": "2. Bileşen tR2", "type": "slider", "min": 3.0, "max": 15.0, "value": 7.5, "step": 0.2, "unit": "dk"},
        {"key": "n_plates", "label": "Plaka sayısı (N)", "type": "slider", "min": 200, "max": 5000, "value": 1500, "step": 100, "unit": ""},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z = Zahira("kromatografi")
    tr1 = float(params["tr1"])
    tr2 = float(params["tr2"])
    n_plates = float(params["n_plates"])

    if tr2 <= tr1:
        raise ValueError("2. bileşenin alıkonma zamanı (tR2), 1. bileşenden (tR1) büyük olmalıdır.")

    s1 = tr1 / np.sqrt(n_plates)
    s2 = tr2 / np.sqrt(n_plates)
    w1, w2 = 4 * s1, 4 * s2
    rs = 2.0 * (tr2 - tr1) / (w1 + w2)

    tmax = tr2 + 4 * s2 + 1.0
    t = np.linspace(0, tmax, 120)
    y1 = np.exp(-0.5 * ((t - tr1) / s1) ** 2)
    y2 = 0.85 * np.exp(-0.5 * ((t - tr2) / s2) ** 2)
    ytot = y1 + y2

    frames, events = [], []
    prev_frac = 0.0
    for i in range(1, len(t) + 1):
        frac = i / float(len(t))
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i - 1, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        frames.append({
            "traces": [
                {"x": t[:i].tolist(), "y": ytot[:i].tolist(), "mode": "lines", "name": "Dedektör Sinyali", "line": {"color": "#27ae60", "width": 2.5}},
                {"x": t[:i].tolist(), "y": y1[:i].tolist(), "mode": "lines", "name": "Bileşen A", "line": {"color": "#2980b9", "dash": "dot"}},
                {"x": t[:i].tolist(), "y": y2[:i].tolist(), "mode": "lines", "name": "Bileşen B", "line": {"color": "#e67e22", "dash": "dot"}},
            ],
            "layout": {
                "title": f"Kromatogram — Zaman: {t[i-1]:.2f} dk",
                "xaxis": {"title": "Zaman (dk)", "range": [0, tmax]},
                "yaxis": {"title": "Dedektör Sinyali (mAU)", "range": [0, 1.3]},
            },
        })

    rows = [
        ("tR1 / tR2", f"{tr1:.2f} dk / {tr2:.2f} dk"),
        ("Pik Genişlikleri (w1 / w2)", f"{w1:.3f} / {w2:.3f} dk"),
        ("Plaka Sayısı (N)", f"{int(n_plates)}"),
        ("Çözünürlük (Rs)", f"{rs:.2f}"),
        ("Ayrım Durumu", "Tam Ayrım (Rs ≥ 1.5)" if rs >= 1.5 else "Kısmi Örtüşme"),
    ]
    finish_key = "finish_good" if rs >= 1.5 else "finish_overlap"
    return {
        "start_lines": _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say(finish_key, rs=rs)),
        "frames": frames,
        "events": events,
        "results_html": results_table(rows),
    }
