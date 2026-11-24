# -*- coding: utf-8 -*-
"""Web sürümü için yardımcılar (PyQt5 gerektirmez)."""


def build_info_html(title, purpose, theory, materials, steps, safety=None, accent="#3498db"):
    mats = "".join("<li>{}</li>".format(m) for m in materials)
    stps = "".join("<li>{}</li>".format(s) for s in steps)
    html = (
        "<h2 style='color:{a};'>{t}</h2>"
        "<h3>🎯 Amaç</h3><p>{p}</p>"
        "<h3>📘 Teori</h3><p>{th}</p>"
        "<h3>🧪 Malzemeler</h3><ul>{m}</ul>"
        "<h3>📋 Deney Adımları</h3><ol>{s}</ol>"
    ).format(a=accent, t=title, p=purpose, th=theory, m=mats, s=stps)
    if safety:
        html += "<h3>⚠️ Güvenlik</h3><p>{}</p>".format(safety)
    return html


def results_table(rows, title=None):
    html = ""
    if title:
        html += "<h3>{}</h3>".format(title)
    html += "<table cellspacing='0' cellpadding='4' width='100%' style='border-collapse:collapse;'>"
    for i, (k, v) in enumerate(rows):
        bg = "rgba(127,127,127,0.12)" if i % 2 == 0 else "transparent"
        html += ("<tr style='background:{bg};'><td><b>{k}</b></td>"
                 "<td align='right'>{v}</td></tr>").format(bg=bg, k=k, v=v)
    html += "</table>"
    return html
