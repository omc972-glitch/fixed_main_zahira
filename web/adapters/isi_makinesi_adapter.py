import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

R = 8.314
GASES  = [("Tek atomlu (He, γ=5/3)", 5 / 3), ("İki atomlu (Hava, γ=1.4)", 1.4)]
PHASES = [
    "1→2 İzotermal genleşme (T_H)",
    "2→3 Adyabatik genleşme",
    "3→4 İzotermal sıkışma (T_C)",
    "4→1 Adyabatik sıkışma",
]
N = 60  # her süreç için nokta sayısı

META = {
    "id": "isi_makinesi",
    "title": "Isı Makinesi",
    "subtitle": "Carnot çevrimi: iki izotermal + iki adyabatik süreç",
    "icon": "⚙️",
    "accent": "#d35400",
    "zahira_key": "isi_makinesi",
    "info_html": build_info_html(
        "Carnot Isı Makinesi",
        "İdeal bir ısı makinesinin P–V çevrimini, ısı/iş dengesini ve verimini incelemek.",
        "İzotermal: PV = sabit, Q = nRT·ln(V₂/V₁). Adyabatik: TV^(γ−1) = sabit, Q = 0. "
        "W = Q_H − Q_C, η = 1 − T_C/T_H (iki sıcaklık arasında mümkün olan en yüksek verim).",
        ["Piston–silindir (ideal gaz)", "Sıcak rezervuar (T_H)", "Soğuk rezervuar (T_C)", "Yalıtkan taban"],
        ["Gazı sıcak rezervuarla temas ettirip genleştirin.", "Yalıtıp adyabatik genleştirin.",
         "Soğuk rezervuarla temasta sıkıştırın.", "Yalıtıp adyabatik olarak başlangıca dönün."],
        None, "#d35400",
    ),
    "parameters": [
        {"key": "th",  "label": "Sıcak rezervuar T_H",          "type": "slider", "min": 300,  "max": 1500, "value": 600, "step": 10,  "unit": "K"},
        {"key": "tc",  "label": "Soğuk rezervuar T_C",          "type": "slider", "min": 150,  "max": 800,  "value": 300, "step": 10,  "unit": "K"},
        {"key": "v1",  "label": "Başlangıç hacmi V₁",           "type": "slider", "min": 1.0,  "max": 10.0, "value": 2.0, "step": 0.5, "unit": "L"},
        {"key": "r",   "label": "İzotermal genleşme oranı V₂/V₁","type": "slider","min": 1.2,  "max": 5.0,  "value": 2.0, "step": 0.1},
        {"key": "cyc", "label": "Çevrim sayısı",                 "type": "int",    "min": 1,    "max": 5,    "value": 2},
        {"key": "gas", "label": "Gaz türü",                     "type": "select", "value": 1,
         "options": [{"label": GASES[0][0], "value": 0}, {"label": GASES[1][0], "value": 1}]},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def run(params: dict) -> dict:
    z   = Zahira("isi_makinesi")
    th  = float(params.get("th",  600))
    tc  = float(params.get("tc",  300))
    v1  = float(params.get("v1",  2.0))
    r   = float(params.get("r",   2.0))
    cyc = int(params.get("cyc",   2))
    gas_idx = int(params.get("gas", 1))

    if tc >= th:
        raise ValueError("Soğuk rezervuar sıcaklığı (T_C), sıcak rezervuar sıcaklığından (T_H) küçük olmalıdır.")

    g = GASES[gas_idx][1]
    v2 = v1 * r
    f  = (th / tc) ** (1 / (g - 1))
    v3, v4 = v2 * f, v1 * f

    Va = np.linspace(v1, v2, N);  Ta = np.full(N, th)
    Vb = np.linspace(v2, v3, N);  Tb = th * (v2 / Vb) ** (g - 1)
    Vc = np.linspace(v3, v4, N);  Tc_arr = np.full(N, tc)
    Vd = np.linspace(v4, v1, N);  Td = tc * (v4 / Vd) ** (g - 1)

    V_cycle = np.concatenate([Va, Vb, Vc, Vd])
    T_cycle = np.concatenate([Ta, Tb, Tc_arr, Td])
    P_cycle = R * T_cycle / V_cycle  # kPa (R J/(mol·K), V in L → 1 kPa per unit)

    qh  = R * th * np.log(v2 / v1)
    qc  = R * tc * np.log(v3 / v4)
    w   = qh - qc
    eta = 1 - tc / th

    total = 4 * N * cyc
    p_max = P_cycle.max() * 1.15
    v_max_range = v3 * 1.1
    e_ymax = qh * cyc * 1.15

    # Corner labels for static overlay
    corners = [(v1, R*th/v1), (v2, R*th/v2), (v3, R*tc/v3), (v4, R*tc/v4)]

    frames, events = [], []
    prev_frac = 0.0
    prev_zp   = None

    for frame in range(total):
        frac  = frame / float(total - 1)
        k_pos = frame % (4 * N)
        cyc_i = frame // (4 * N)
        phase = k_pos // N

        # Zahira events
        if (cyc_i, phase) != prev_zp:
            if phase == 0 and cyc_i > 0:
                ev_lines = _to_lines(z.say("cycle_end"))
                events.append({"id": f"cycle_end_{cyc_i}", "frame": frame, "kind": "event", "lines": ev_lines})
            prev_zp = (cyc_i, phase)
            if cyc_i == 0:
                ev_lines = _to_lines(z.say(f"phase_{phase}"))
                events.append({"id": f"phase_{phase}", "frame": frame, "kind": "event", "lines": ev_lines})

        # progress
        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{frame}", "frame": frame, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        # Accumulated energy
        done  = cyc_i + (k_pos + 1) / float(4 * N)

        # Left panel: P-V diagram
        traces = [
            # full cycle outline (gray)
            {
                "x": V_cycle.tolist(), "y": P_cycle.tolist(),
                "mode": "lines", "name": "Tam çevrim",
                "line": {"color": "lightgray", "width": 1},
                "showlegend": False,
                "xaxis": "x", "yaxis": "y",
            },
            # current traced path
            {
                "x": V_cycle[:k_pos + 1].tolist(),
                "y": P_cycle[:k_pos + 1].tolist(),
                "mode": "lines",
                "name": PHASES[phase],
                "line": {"color": "#d35400", "width": 2.5},
                "xaxis": "x", "yaxis": "y",
            },
            # current position dot
            {
                "x": [V_cycle[k_pos]], "y": [P_cycle[k_pos]],
                "mode": "markers", "name": "Mevcut konum",
                "marker": {"color": "#2c3e50", "size": 10},
                "showlegend": False,
                "xaxis": "x", "yaxis": "y",
            },
            # Energy bars (right panel)
            {
                "type": "bar",
                "x": ["Q_H", "W", "Q_C"],
                "y": [qh * done, w * done, qc * done],
                "marker": {"color": ["#e74c3c", "#27ae60", "#3498db"]},
                "name": "Enerji (J)",
                "xaxis": "x2", "yaxis": "y2",
            },
        ]

        frames.append({
            "traces": traces,
            "layout": {
                "title": f"P–V diyagramı — Çevrim {cyc_i+1}: {PHASES[phase]}",
                "xaxis":  {"title": "V (L)", "domain": [0, 0.47],
                           "range": [v1 * 0.85, v_max_range]},
                "yaxis":  {"title": "P (kPa)", "range": [0, p_max]},
                "xaxis2": {"title": "Enerji bileşeni", "domain": [0.56, 1.0], "anchor": "y2"},
                "yaxis2": {"title": "Toplam enerji (J)", "anchor": "x2",
                           "range": [0, e_ymax]},
            },
        })

    # Results
    rows = [
        ("Carnot verimi η",                  f"{eta*100:.1f} %"),
        ("Q_H (çevrim başına)",              f"{qh:.1f} J"),
        ("Q_C (çevrim başına)",              f"{qc:.1f} J"),
        ("W (çevrim başına)",                f"{w:.1f} J"),
        (f"Toplam iş ({cyc} çevrim)",        f"{w*cyc:.1f} J"),
        ("W/Q_H kontrol",                    f"{w/qh:.3f}"),
        ("P_max / P_min",                    f"{P_cycle.max():.1f} / {P_cycle.min():.1f} kPa"),
        ("V_max (V₃)",                       f"{v3:.2f} L"),
        ("Gaz türü",                         GASES[gas_idx][0]),
    ]

    return {
        "start_lines":  _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say("finish", eta=eta*100, qh=qh, qc=qc, w=w)),
        "frames":       frames,
        "events":       events,
        "results_html": results_table(rows, "Carnot Sonuçları"),
    }
