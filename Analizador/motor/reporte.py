# Salidas para personas: grafica.png, ficha.md y reporte.html (linea de tiempo con miniaturas).
import html, os
import numpy as np
from comun import mmss, suav

COLOR_PLANO = {"primerísimo primer plano": "#e74c3c", "primer plano": "#e67e22", "plano medio": "#f1c40f", "plano entero": "#2ecc71",
               "plano general": "#3498db", "plano aéreo": "#9b59b6", "plano detalle": "#1abc9c", "texto en pantalla": "#95a5a6", "negro": "#333"}


def grafica(out, datos, m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fps, tomas = datos["video"]["fps_analisis"], datos["tomas"]
    nf = len(m["brillo"])
    tt = np.arange(nf) / fps
    fig, ax = plt.subplots(5, 1, figsize=(15, 9), sharex=True)
    ax[0].bar([t["inicio"] for t in tomas], [t["duracion"] for t in tomas], width=[t["duracion"] * 0.95 for t in tomas], align="edge",
              color=[COLOR_PLANO.get(t.get("plano"), "#888") for t in tomas])
    ax[0].set_ylabel("toma (s)\ncolor = plano")
    z = np.ones(nf)
    for t in tomas:
        z[t["f0"]:t["f1"]] = np.cumprod(m["escala"][t["f0"]:t["f1"]])
    ax[1].plot(tt, (z - 1) * 100, color="#d9534f", lw=1); ax[1].set_ylabel("zoom %")
    sh = np.hypot(m["dx"] - suav(m["dx"]), m["dy"] - suav(m["dy"])) * 100
    ax[2].plot(tt, sh, color="#5cb85c", lw=0.7); ax[2].set_ylabel("temblor")
    ax[3].plot(tt, m["brillo"], color="#f0ad4e", lw=0.8); ax[3].set_ylabel("brillo")
    for e in datos.get("efectos", []):
        ax[3].axvspan(e["inicio"], max(e["fin"], e["inicio"] + 0.05), color="#c0392b", alpha=0.25)
    for w in datos["audio"].get("palabras", []):
        ax[4].plot([w["t0"], w["t1"]], [1, 1], color="#333", lw=4, solid_capstyle="butt")
    for s in datos["subtitulos"].get("eventos", []):
        ax[4].plot([s["inicio"], s["fin"]], [0.5, 0.5], color="#2980b9", lw=6, solid_capstyle="butt")
    for t in datos["audio"].get("sonidos", {}).get("golpes_sonido", []):
        ax[4].plot([t], [0], "v", color="#c0392b", ms=5)
    ax[4].set_yticks([0, 0.5, 1]); ax[4].set_yticklabels(["efectos", "subtítulos", "voz"]); ax[4].set_ylim(-0.4, 1.4)
    ax[4].set_xlabel("segundos")
    for a_ in ax:
        for t in tomas[1:]:
            a_.axvline(t["inicio"], color="#bbb", lw=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "grafica.png"), dpi=85)
    plt.close(fig)


def ficha(out, datos):
    rs, v = datos["resumen"], datos["video"]
    L = ["# %s — %s" % (datos["creador"], v["archivo"]), "",
         "Duración %.1f s · %dx%d · %.0f fps · %d tomas · reporte visual: `reporte.html`" % (v["duracion"], v["ancho"], v["alto"], v["fps"], rs["tomas"]), "",
         "| Dato | Valor |", "|---|---|"]
    for k, val in rs.items():
        if not isinstance(val, (dict, list)):
            L.append("| %s | %s |" % (k.replace("_", " "), val))
    for k in ("planos_pct", "camara_pct", "transiciones_pct", "efectos_por_tipo"):
        if rs.get(k):
            L.append("| %s | %s |" % (k.replace("_", " "), ", ".join("%s %s" % kv for kv in rs[k].items())))
    es = datos["subtitulos"].get("estilo") or {}
    if es:
        L += ["", "## Subtítulos", ""] + ["- **%s**: %s" % (k.replace("_", " "), v_) for k, v_ in es.items()]
    hi = datos.get("historia", {})
    if hi.get("hay_narracion"):
        L += ["", "## Historia (automático)", "", "- Gancho: “%s” (termina en %.1f s)" % (hi["gancho"]["frase"], hi["gancho"]["fin_s"]),
              "- Preguntas: %d · giros: %d · final: “%s”" % (hi["preguntas"], len(hi["giros"]), hi["final"]["frase"])]
    L += ["", "Revisión cualitativa pendiente: `para_claude.md` → `notas_claude.md`."]
    open(os.path.join(out, "ficha.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def html_reporte(out, datos):
    e = html.escape
    v, rs, tomas = datos["video"], datos["resumen"], datos["tomas"]
    dur = max(1e-6, v["duracion"])
    css = """body{font-family:Segoe UI,Arial;background:#15161a;color:#e8e8e8;margin:24px}h1,h2{color:#ffd166}
    table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #333;padding:4px 8px;font-size:13px;vertical-align:top}
    th{background:#23252b}.tl{display:flex;width:100%;height:120px;border:1px solid #444;overflow:hidden}
    .tl div{height:100%;background-size:cover;background-position:center;border-right:2px solid #000;position:relative}
    .tl span{position:absolute;bottom:0;left:0;right:0;font-size:10px;background:rgba(0,0,0,.6);padding:1px 2px;white-space:nowrap;overflow:hidden}
    .kpi{display:inline-block;background:#23252b;border-radius:8px;padding:10px 14px;margin:4px;min-width:120px}
    .kpi b{display:block;font-size:22px;color:#fff}.kpi small{color:#aaa}img{max-width:100%}.chip{padding:1px 6px;border-radius:6px;color:#000}"""
    H = ["<!DOCTYPE html><html lang='es'><meta charset='utf-8'><title>%s</title><style>%s</style><body>" % (e(v["archivo"]), css),
         "<h1>%s · %s</h1>" % (e(datos["creador"]), e(v["archivo"]))]
    kpis = [("Duración", "%.1f s" % v["duracion"]), ("Tomas", rs["tomas"]), ("Toma mediana", "%.2f s" % rs["toma_mediana_s"]),
            ("Cortes/min", rs["cortes_por_minuto"]), ("Palabras/s", rs.get("palabras_por_s")), ("Subtítulos", (datos["subtitulos"].get("estilo") or {}).get("modo", "—")),
            ("Volumen", "%s LUFS" % datos["audio"].get("sonoridad", {}).get("lufs")), ("Efectos", len(datos.get("efectos", [])))]
    H.append("".join("<div class='kpi'><small>%s</small><b>%s</b></div>" % (e(str(a)), e(str(b))) for a, b in kpis))
    H.append("<h2>Línea de tiempo</h2><div class='tl'>")
    for t in tomas:
        H.append("<div title='Toma %d · %.2f s · %s · %s' style='width:%.3f%%;background-image:url(miniaturas/toma_%03d.jpg)'><span style='background:%s;color:#000'>%d %s</span></div>"
                 % (t["n"], t["duracion"], e(t.get("plano", "")), e(t["camara"]), 100 * t["duracion"] / dur, t["n"],
                    COLOR_PLANO.get(t.get("plano"), "#888"), t["n"], e(t.get("plano", "")[:12])))
    H.append("</div><p><img src='grafica.png'></p>")
    H.append("<h2>Tomas</h2><table><tr><th>#</th><th>Inicio</th><th>Dur</th><th>Plano</th><th>Cámara</th><th>Zoom</th><th>Temblor</th><th>Entra con</th><th>Ambiente</th><th>Texto</th></tr>")
    for t in tomas:
        H.append("<tr><td>%d</td><td>%s</td><td>%.2f</td><td><span class='chip' style='background:%s'>%s</span></td><td>%s</td><td>%+.1f%%</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (t["n"], mmss(t["inicio"]), t["duracion"], COLOR_PLANO.get(t.get("plano"), "#888"), e(t.get("plano", "")), e(t["camara"]),
                    t["zoom_total_pct"], "sí %.2f" % t["temblor_pct"] if t["temblor"] else "—", e(t.get("transicion_entrada", "")),
                    e("%s · %s" % (t.get("ambiente", ""), t.get("hora", ""))), e(t.get("texto", ""))))
    H.append("</table>")
    es = datos["subtitulos"].get("estilo") or {}
    if es:
        H.append("<h2>Subtítulos</h2><table>" + "".join("<tr><th>%s</th><td>%s</td></tr>" % (e(k.replace("_", " ")), e(str(v_))) for k, v_ in es.items()) + "</table>")
        H.append("<details><summary>Primeros subtítulos</summary><table><tr><th>Inicio</th><th>Texto</th><th>Pal.</th><th>Color</th><th>Resaltado</th></tr>")
        for s in datos["subtitulos"]["eventos"][:60]:
            H.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (mmss(s["inicio"]), e(s["texto"]), s["palabras_voz"] or s["palabras_ocr"],
                                                                                    e(str(s["relleno"])), e(str(s["resaltado"] or ""))))
        H.append("</table></details>")
    ef = datos.get("efectos", [])
    if ef:
        H.append("<h2>Posibles efectos</h2>")
        for x in ef[:60]:
            H.append("<p><b>%d. %s</b> · %s (%.2f s)<br><img src='efectos/efecto_%02d.jpg'></p>" % (x["n"], e(x["tipo"]), mmss(x["inicio"]), x["duracion"], x["n"]))
    au = datos["audio"]
    H.append("<h2>Audio</h2><table>")
    for k, v_ in {**au.get("voz", {}), **au.get("sonoridad", {}), **{k: v for k, v in au.get("sonidos", {}).items() if k != "golpes_sonido"}}.items():
        H.append("<tr><th>%s</th><td>%s</td></tr>" % (e(k.replace("_", " ")), e(str(v_))))
    H.append("</table>")
    if au.get("segmentos"):
        H.append("<h2>Narración</h2><table>" + "".join("<tr><td>%s</td><td>%s</td></tr>" % (mmss(s["t0"]), e(s["texto"])) for s in au["segmentos"]) + "</table>")
    H.append("<h2>Hojas de contacto</h2>")
    for f in sorted(os.listdir(os.path.join(out, "hojas"))):
        H.append("<p><img src='hojas/%s'></p>" % f)
    H.append("</body></html>")
    open(os.path.join(out, "reporte.html"), "w", encoding="utf-8").write("\n".join(H))
