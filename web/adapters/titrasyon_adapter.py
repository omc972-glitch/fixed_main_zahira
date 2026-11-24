import numpy as np
from web.helpers import build_info_html, results_table
from ui.zahira_konusmalar import Zahira

META = {
    "id": "titrasyon",
    "title": "Asit-Baz Titrasyonu",
    "subtitle": "Kuvvetli/zayıf asit + kuvvetli baz titrasyon eğrisi ve eşdeğerlik noktası",
    "icon": "🧪",
    "accent": "#e74c3c",
    "zahira_key": "titrasyon",
    "info_html": build_info_html(
        "Asit–Baz Titrasyonu",
        "Bilinmeyen veya bilinen derişimli bir asidi standart bazla titre ederek eşdeğerlik noktasını ve pH eğrisini belirlemek.",
        "Kuvvetli asit–kuvvetli baz titrasyonunda eşdeğerlik noktasında pH = 7'dir. "
        "Zayıf asit–kuvvetli bazda yarı eşdeğerlikte pH = pKa, eşdeğerlikte ise konjuge baz hidrolizi nedeniyle pH > 7 olur.",
        ["Büret (50 mL)", "Erlenmayer (250 mL)", "pH metre", "Manyetik karıştırıcı", "Asit ve NaOH çözeltisi"],
        ["Asit örneğini erlene alın.", "Büreti standart NaOH ile doldurun.", "Damla damla baz ekleyip pH kaydedin.",
         "Eşdeğerlik noktasındaki ani pH sıçramasını gözlemleyin."],
        "Kuvvetli asit ve bazlar yakıcıdır; koruyucu gözlük ve eldiven kullanın.", "#e74c3c",
    ),
    "parameters": [
        {"key": "acid_type", "label": "Asit türü", "type": "select", "value": "strong",
         "options": [{"label": "Kuvvetli Asit (HCl)", "value": "strong"}, {"label": "Zayıf Asit (CH₃COOH)", "value": "weak"}]},
        {"key": "ca", "label": "Asit derişimi (Ca)", "type": "slider", "min": 0.02, "max": 0.5, "value": 0.1, "step": 0.01, "unit": "M"},
        {"key": "va", "label": "Asit hacmi (Va)", "type": "slider", "min": 10.0, "max": 50.0, "value": 25.0, "step": 1.0, "unit": "mL"},
        {"key": "cb", "label": "Baz derişimi (Cb)", "type": "slider", "min": 0.02, "max": 0.5, "value": 0.1, "step": 0.01, "unit": "M"},
        {"key": "pka", "label": "pKa (zayıf asit)", "type": "slider", "min": 2.0, "max": 7.0, "value": 4.76, "step": 0.05, "unit": ""},
    ],
}


def _to_lines(lines):
    return [{"sprite": l.sprite, "text": l.text} for l in lines]


def _ph_curve(vb_arr, ca, va, cb, acid_type, pka):
    kw = 1e-14
    ka = 10.0 ** (-pka)
    ph = np.zeros_like(vb_arr, dtype=float)
    for i, vb in enumerate(vb_arr):
        vtot = va + vb
        na = ca * va
        nb = cb * vb
        if acid_type == "strong":
            if nb < na:
                h = (na - nb) / vtot
                h = 0.5 * (h + np.sqrt(h * h + 4 * kw))
                ph[i] = -np.log10(h)
            elif nb > na:
                oh = (nb - na) / vtot
                oh = 0.5 * (oh + np.sqrt(oh * oh + 4 * kw))
                ph[i] = 14.0 + np.log10(oh)
            else:
                ph[i] = 7.0
        else:
            if vb == 0:
                h = 0.5 * (-ka + np.sqrt(ka * ka + 4 * ka * ca))
                ph[i] = -np.log10(h)
            elif nb < na:
                c_acid = (na - nb) / vtot
                c_salt = nb / vtot
                # Exact quadratic for H+
                b_coef = ka + c_salt
                c_coef = -ka * c_acid
                h = 0.5 * (-b_coef + np.sqrt(b_coef * b_coef - 4 * c_coef))
                ph[i] = -np.log10(max(h, 1e-14))
            elif np.isclose(nb, na, rtol=1e-6):
                c_salt = na / vtot
                kb = kw / ka
                oh = 0.5 * (-kb + np.sqrt(kb * kb + 4 * kb * c_salt))
                ph[i] = 14.0 + np.log10(max(oh, 1e-14))
            else:
                oh = (nb - na) / vtot
                oh = 0.5 * (oh + np.sqrt(oh * oh + 4 * kw))
                ph[i] = 14.0 + np.log10(oh)
    return ph


def run(params: dict) -> dict:
    z = Zahira("titrasyon")
    acid_type = params.get("acid_type", "strong")
    ca = float(params["ca"])
    va = float(params["va"])
    cb = float(params["cb"])
    pka = float(params.get("pka", 4.76))

    veq = (ca * va) / cb
    vmax = max(veq * 1.8, 10.0)
    vb = np.linspace(0, vmax, 120)
    ph = _ph_curve(vb, ca, va, cb, acid_type, pka)
    eq_idx = int(np.argmin(np.abs(vb - veq)))
    ph_eq = float(ph[eq_idx])

    frames, events = [], []
    prev_frac = 0.0
    eq_fired = False

    for i in range(1, len(vb) + 1):
        frac = i / float(len(vb))
        traces = [{
            "x": vb[:i].tolist(),
            "y": ph[:i].tolist(),
            "mode": "lines",
            "name": "Titrasyon Eğrisi",
            "line": {"color": "#e74c3c", "width": 2.5},
        }]
        if i - 1 >= eq_idx:
            traces.append({
                "x": [veq],
                "y": [ph_eq],
                "mode": "markers",
                "name": f"Eşdeğerlik ({veq:.2f} mL)",
                "marker": {"color": "#2ecc71", "size": 11, "symbol": "diamond"},
            })
            if not eq_fired:
                eq_fired = True
                events.append({
                    "id": "equivalence",
                    "frame": i - 1,
                    "kind": "event",
                    "lines": _to_lines(z.say("equivalence", veq=veq, ph_eq=ph_eq)),
                })

        prog = z.progress(prev_frac, frac)
        if prog:
            events.append({"id": f"prog_{i}", "frame": i - 1, "kind": "progress", "lines": _to_lines(prog)})
        prev_frac = frac

        frames.append({
            "traces": traces,
            "layout": {
                "title": f"Eklenen NaOH: {vb[i-1]:.2f} mL | pH: {ph[i-1]:.2f}",
                "xaxis": {"title": "Eklenen Baz Hacmi (mL)", "range": [0, vmax]},
                "yaxis": {"title": "pH", "range": [0, 14]},
            },
        })

    rows = [
        ("Asit Türü", "Kuvvetli Asit" if acid_type == "strong" else f"Zayıf Asit (pKa={pka:.2f})"),
        ("Başlangıç pH", f"{ph[0]:.2f}"),
        ("Eşdeğerlik Hacmi (Veq)", f"{veq:.2f} mL"),
        ("Eşdeğerlik pH", f"{ph_eq:.2f}"),
        ("Son pH", f"{ph[-1]:.2f}"),
    ]

    return {
        "start_lines": _to_lines(z.say("start")),
        "finish_lines": _to_lines(z.say("finish_strong" if acid_type == "strong" else "finish_weak", veq=veq, ph_eq=ph_eq, ph_half=float(np.interp(veq / 2.0, vb, ph)))),
        "frames": frames,
        "events": events,
        "results_html": results_table(rows),
    }

# KONUSMA-FIX-V1
