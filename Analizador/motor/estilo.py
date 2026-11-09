# Junta todos los videos analizados de un creador y escribe su FORMULA:
#   Estilos/<Creador>.json        -> receta en numeros (la leen los scripts de animacion)
#   Estilos/<Creador>_formula.md  -> la misma receta explicada (se regenera cada vez)
#   Estilos/<Creador>_notas.md    -> reglas cualitativas que escribe Claude al revisar (NUNCA se sobrescribe)
#   Estilos/COMPARACION.md        -> creadores lado a lado
import glob, os
from collections import Counter
import numpy as np
from comun import RESULTADOS, ESTILOS, VERSION, leer_json, guardar_json, r, log


def _med(xs, q=50):
    xs = [x for x in xs if x is not None]
    return r(np.percentile(xs, q)) if xs else None


def _mezcla(items):
    c = Counter(x for x in items if x)
    tot = sum(c.values())
    return {k: round(100 * v / tot) for k, v in c.most_common()} if tot else {}


def _top(items):
    c = Counter(x for x in items if x)
    return c.most_common(1)[0][0] if c else None


# Nombres viejos de un mismo creador: sus resultados se juntan con los del nombre actual.
# "ClusterK" se escribio por error; el canal es Custerk (@CusterkBloxy). Los informes viejos se quedan en su carpeta.
ALIAS = {"Custerk": ["ClusterK"]}
ES_ALIAS = {v for vs in ALIAS.values() for v in vs}


def cargar(creador):
    vids = []
    rutas = []
    for c in [creador] + ALIAS.get(creador, []):
        rutas += glob.glob(os.path.join(RESULTADOS, c, "*", "datos.json"))
    for f in sorted(rutas):
        d = leer_json(f)
        if d and d.get("version") == VERSION:
            d["_carpeta"] = os.path.dirname(f)
            vids.append(d)
    return vids


def construir(creador):
    vids = cargar(creador)
    if not vids:
        return None
    os.makedirs(ESTILOS, exist_ok=True)
    tomas = [t for d in vids for t in d["tomas"]]
    durs = [t["duracion"] for t in tomas]
    mins = sum(d["video"]["duracion"] for d in vids) / 60
    from subtitulos import palabras_evento, modo_subtitulos
    for d in vids:   # recalcula con la regla actual (sirve para videos analizados con una version anterior)
        es, ev = d["subtitulos"].get("estilo"), d["subtitulos"].get("eventos") or []
        if es and ev:
            es["palabras_por_subtitulo"] = r(np.median([palabras_evento(e) for e in ev]), 1)
            es["modo"] = modo_subtitulos(es["palabras_por_subtitulo"])
    subs = [d["subtitulos"].get("estilo") or {} for d in vids if d["subtitulos"].get("hay_subtitulos")]
    voz = [d["audio"].get("voz", {}) for d in vids if d["audio"].get("voz", {}).get("hay_voz")]
    son = [d["audio"].get("sonidos", {}) for d in vids]
    lou = [d["audio"].get("sonoridad", {}) for d in vids]
    his = [d["historia"] for d in vids if d["historia"].get("hay_narracion")]
    temb = [t for t in tomas if t["temblor"]]
    acerc = [t for t in tomas if t["camara"] == "acercamiento lento"]
    giros_pos = [g["pct"] for h in his for g in h["giros"]]
    ef_tipo = Counter(e["tipo"] for d in vids for e in d["efectos"])
    n = len(vids)
    F = {
        "creador": creador, "videos": n, "minutos": r(mins, 1),
        "confiabilidad": "baja (menos de 5 videos)" if n < 5 else "media (5-14 videos)" if n < 15 else "alta (15+ videos)",
        "video": {"duracion_s": _med([d["video"]["duracion"] for d in vids]), "duracion_p10_s": _med([d["video"]["duracion"] for d in vids], 10),
                  "duracion_p90_s": _med([d["video"]["duracion"] for d in vids], 90),
                  "vertical_pct": round(100 * np.mean([d["video"]["alto"] > d["video"]["ancho"] for d in vids]))},
        "ritmo": {"toma_mediana_s": _med(durs), "toma_p10_s": _med(durs, 10), "toma_p90_s": _med(durs, 90), "toma_media_s": r(np.mean(durs)) if durs else None,
                  "cortes_por_minuto": _med([d["resumen"]["cortes_por_minuto"] for d in vids]),
                  "toma_mediana_por_tercio_s": [_med([d["resumen"]["toma_mediana_por_tercio_s"][k] for d in vids]) for k in range(3)],
                  "cortes_en_primeros_3s": _med([d["resumen"]["primeros_3s_cortes"] for d in vids]),
                  "cortes_en_palabra_pct": _med([d["resumen"].get("cortes_en_palabra_pct") for d in vids])},
        "planos_pct": _mezcla(t.get("plano") for t in tomas),
        "camara_pct": _mezcla(t["camara"] for t in tomas),
        "camara": {"temblor_tomas_pct": round(100 * len(temb) / max(1, len(tomas))), "temblor_amplitud": _med([t["temblor_pct"] for t in temb]),
                   "temblor_hz": _med([t["temblor_hz"] for t in temb]), "acercamiento_tipico_pct": _med([t["zoom_total_pct"] for t in acerc]),
                   "golpes_zoom_por_minuto": _med([d["resumen"]["golpes_zoom_por_minuto"] for d in vids]),
                   "movimiento_en_cuadro_pct": _med([t["movimiento_en_cuadro_pct"] for t in tomas])},
        "transiciones_pct": _mezcla(x["tipo"] for d in vids for x in d["transiciones"]),
        "efectos_candidatos_por_minuto": {k: r(v / max(1e-6, mins), 2) for k, v in ef_tipo.most_common()},   # sin confirmar: los reales van en _notas.md
        "ambiente_pct": _mezcla(t.get("ambiente") for t in tomas), "hora_pct": _mezcla(t.get("hora") for t in tomas),
        "lugar_pct": _mezcla(t.get("lugar") for t in tomas), "personajes_pct": _mezcla({0: "ninguno", 1: "uno", 2: "dos"}.get(t.get("personajes_n"), "tres o más") if t.get("personajes_n") is not None else None for t in tomas),
        "subtitulos": {"videos_con_subtitulos_pct": round(100 * len(subs) / n), "modo": _top(s.get("modo") for s in subs),
                       "palabras_por_subtitulo": _med([s.get("palabras_por_subtitulo") for s in subs]),
                       "duracion_s": _med([s.get("duracion_subtitulo_s") for s in subs]),
                       "posicion_y_pct": _med([s.get("posicion_y_pct") for s in subs]), "alto_letra_pct": _med([s.get("alto_letra_pct") for s in subs]),
                       "lineas": _med([s.get("lineas") for s in subs]), "color": _top(s.get("color_relleno") for s in subs),
                       "resaltado_pct": _med([s.get("resaltado_pct") for s in subs]), "color_resaltado": _top(s.get("color_resaltado") for s in subs),
                       "contorno_oscuro_pct": _med([s.get("contorno_oscuro_pct") for s in subs]), "mayusculas_pct": _med([s.get("mayusculas_pct") for s in subs]),
                       "aparece_vs_voz_ms": _med([s.get("aparece_vs_voz_ms") for s in subs]), "entrada_pop_pct": _med([s.get("entrada_pop_pct") for s in subs])},
        "voz": {"idioma": _top((d["audio"].get("idioma") or {}).get("idioma") for d in vids), "palabras_por_s": _med([v.get("palabras_por_s") for v in voz]),
                "pausas_por_minuto": _med([v.get("pausas_por_minuto") for v in voz]), "primera_palabra_s": _med([v.get("primera_palabra_s") for v in voz]),
                "tiempo_hablando_pct": _med([v.get("tiempo_hablando_pct") for v in voz])},
        "audio": {"lufs": _med([x.get("lufs") for x in lou]), "golpes_sonido_por_minuto": _med([s.get("golpes_por_minuto") for s in son]),
                  "musica_probable_pct": round(100 * np.mean([bool(s.get("musica_probable")) for s in son])) if son else None,
                  "bpm": _med([s.get("bpm_estimado") for s in son]), "fondo_sonoro_pct": _med([s.get("fondo_sonoro_pct") for s in son])},
        "historia": {"gancho_dura_s": _med([h["gancho"]["fin_s"] for h in his]), "preguntas_por_minuto": _med([h["preguntas_por_minuto"] for h in his]),
                     "giros_por_minuto": _med([h["giros_por_minuto"] for h in his]),
                     "giros_por_decimo_del_video": [sum(1 for p in giros_pos if k * 10 <= p < (k + 1) * 10) for k in range(10)],
                     "termina_en_pregunta_pct": round(100 * np.mean([h["final"]["termina_en_pregunta"] for h in his])) if his else None,
                     "llamado_accion_pct": round(100 * np.mean([bool(h["llamados_accion"]) for h in his])) if his else None},
    }
    F["reglas"] = reglas(F)
    guardar_json(os.path.join(ESTILOS, creador + ".json"), F)
    escribir_md(creador, F, vids)
    notas = os.path.join(ESTILOS, creador + "_notas.md")
    if not os.path.exists(notas):
        open(notas, "w", encoding="utf-8").write(
            "# Notas de Claude — %s\n\n> Reglas que Claude saca al REVISAR los videos (imágenes, historia, efectos). Este archivo no se regenera: se va completando.\n\n"
            "## Historia\n- ...\n\n## Cámara y tomas\n- ...\n\n## Efectos visuales\n- ...\n\n## Subtítulos\n- ...\n\n## Sonido\n- ...\n\n## Personajes\n- ...\n" % creador)
    log("  fórmula de %s: %d videos, %d tomas" % (creador, n, len(tomas)))
    return F


def reglas(F):
    R = []
    rt, cam, su, vz, au, hi = F["ritmo"], F["camara"], F["subtitulos"], F["voz"], F["audio"], F["historia"]
    if rt["toma_mediana_s"]:
        R.append("Cortar cada %.1f s en promedio (casi todas las tomas entre %.1f y %.1f s)." % (rt["toma_mediana_s"], rt["toma_p10_s"], rt["toma_p90_s"]))
    tt = rt["toma_mediana_por_tercio_s"]
    if all(tt):
        R.append("Ritmo por partes: inicio %.1f s · medio %.1f s · final %.1f s por toma." % tuple(tt))
    if rt["cortes_en_primeros_3s"] is not None:
        R.append("En los primeros 3 s hace %.0f cortes (gancho visual)." % rt["cortes_en_primeros_3s"])
    if F["planos_pct"]:
        R.append("Planos más usados: " + ", ".join("%s %d%%" % kv for kv in list(F["planos_pct"].items())[:4]) + ".")
    if F["camara_pct"]:
        R.append("Cámara: " + ", ".join("%s %d%%" % kv for kv in list(F["camara_pct"].items())[:4]) + ".")
    if cam["temblor_tomas_pct"]:
        R.append("Temblor en %d%% de las tomas (amplitud %s, %s Hz)." % (cam["temblor_tomas_pct"], cam["temblor_amplitud"], cam["temblor_hz"]))
    if cam["golpes_zoom_por_minuto"]:
        R.append("Golpes de zoom: %.1f por minuto." % cam["golpes_zoom_por_minuto"])
    trans = {k: v for k, v in F["transiciones_pct"].items() if k != "corte directo"}
    if trans:
        R.append("Transiciones especiales: " + ", ".join("%s %d%%" % kv for kv in trans.items()) + " (el resto, corte directo).")
    if su.get("modo"):
        R.append("Subtítulos: %s, %s palabras, a %s%% de altura, letra %s%% del alto, color %s%s%s." % (
            su["modo"], su["palabras_por_subtitulo"], su["posicion_y_pct"], su["alto_letra_pct"], su["color"],
            ", resalta en %s" % su["color_resaltado"] if su.get("color_resaltado") else "",
            ", MAYÚSCULAS" if (su.get("mayusculas_pct") or 0) > 60 else ""))
    if vz.get("palabras_por_s"):
        R.append("Narración a %.1f palabras/s; empieza a hablar en %.1f s." % (vz["palabras_por_s"], vz["primera_palabra_s"] or 0))
    if au.get("lufs") is not None:
        R.append("Volumen final ≈ %.0f LUFS; %s golpes de sonido por minuto; música %s." % (
            au["lufs"], au["golpes_sonido_por_minuto"], "casi siempre" if (au["musica_probable_pct"] or 0) > 60 else "a veces" if (au["musica_probable_pct"] or 0) > 20 else "casi nunca"))
    if hi.get("giros_por_minuto") is not None:
        R.append("Historia: %.1f giros y %.1f preguntas por minuto; termina en pregunta en %s%% de los videos." % (
            hi["giros_por_minuto"], hi["preguntas_por_minuto"] or 0, hi["termina_en_pregunta_pct"]))
    return R


def escribir_md(creador, F, vids):
    L = ["# Fórmula de %s" % creador, "",
         "> Generado automáticamente con %d video(s), %.1f min. Confiabilidad: **%s**. Reglas cualitativas: `%s_notas.md`." % (F["videos"], F["minutos"], F["confiabilidad"], creador),
         "", "## Receta (para nuestras animaciones)", ""] + ["- " + x for x in F["reglas"]]
    for titulo, clave in [("Ritmo", "ritmo"), ("Cámara", "camara"), ("Subtítulos", "subtitulos"), ("Voz", "voz"), ("Audio", "audio"), ("Historia", "historia")]:
        L += ["", "## " + titulo, "", "| Dato | Valor |", "|---|---|"] + ["| %s | %s |" % (k.replace("_", " "), v) for k, v in F[clave].items()]
    for titulo, clave in [("Planos", "planos_pct"), ("Movimientos de cámara", "camara_pct"), ("Transiciones", "transiciones_pct"), ("Efectos CANDIDATOS por minuto (sin confirmar; los reales están en las notas)", "efectos_candidatos_por_minuto"),
                          ("Ambiente", "ambiente_pct"), ("Hora", "hora_pct"), ("Personajes en cuadro", "personajes_pct")]:
        if F[clave]:
            L += ["", "**%s:** " % titulo + ", ".join("%s %s%s" % (k, v, "" if clave == "efectos_candidatos_por_minuto" else "%") for k, v in F[clave].items())]
    L += ["", "## Videos analizados", ""]
    for d in vids:
        rel = os.path.relpath(os.path.join(d["_carpeta"], "reporte.html"), ESTILOS).replace("\\", "/")
        L.append("- [%s](%s) — %.0f s, %d tomas, toma mediana %.2f s" % (d["video"]["archivo"], rel, d["video"]["duracion"], d["resumen"]["tomas"], d["resumen"]["toma_mediana_s"]))
    L += ["", "> Los tipos de plano, ambiente y personajes los estima CLIP (aprox.). Los efectos son *candidatos*: Claude los confirma mirando `efectos/`."]
    open(os.path.join(ESTILOS, creador + "_formula.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def comparar():
    fs = sorted(glob.glob(os.path.join(ESTILOS, "*.json")))
    Fs = [leer_json(f) for f in fs]
    Fs = [F for F in Fs if F and "ritmo" in F]
    if not Fs:
        return
    filas = [("Videos analizados", lambda F: F["videos"]), ("Duración típica (s)", lambda F: F["video"]["duracion_s"]),
             ("Toma mediana (s)", lambda F: F["ritmo"]["toma_mediana_s"]), ("Cortes por minuto", lambda F: F["ritmo"]["cortes_por_minuto"]),
             ("Ritmo inicio/medio/final (s)", lambda F: " / ".join(str(x) for x in F["ritmo"]["toma_mediana_por_tercio_s"])),
             ("Cortes en primeros 3 s", lambda F: F["ritmo"]["cortes_en_primeros_3s"]),
             ("Plano más usado", lambda F: next(iter(F["planos_pct"].items()), ("—", ""))),
             ("Cámara más usada", lambda F: next(iter(F["camara_pct"].items()), ("—", ""))),
             ("Tomas con temblor %", lambda F: F["camara"]["temblor_tomas_pct"]), ("Golpes de zoom/min", lambda F: F["camara"]["golpes_zoom_por_minuto"]),
             ("Subtítulos", lambda F: F["subtitulos"]["modo"]), ("Palabras por subtítulo", lambda F: F["subtitulos"]["palabras_por_subtitulo"]),
             ("Color subtítulo / resaltado", lambda F: "%s / %s" % (F["subtitulos"]["color"], F["subtitulos"]["color_resaltado"])),
             ("Altura subtítulo %", lambda F: F["subtitulos"]["posicion_y_pct"]), ("Palabras por segundo", lambda F: F["voz"]["palabras_por_s"]),
             ("LUFS", lambda F: F["audio"]["lufs"]), ("Golpes de sonido/min", lambda F: F["audio"]["golpes_sonido_por_minuto"]),
             ("Música probable %", lambda F: F["audio"]["musica_probable_pct"]), ("Giros por minuto", lambda F: F["historia"]["giros_por_minuto"]),
             ("Termina en pregunta %", lambda F: F["historia"]["termina_en_pregunta_pct"]), ("Confiabilidad", lambda F: F["confiabilidad"])]
    # COMPARACION.md (se comparte) solo con creadores; Nosotros_comparacion.md (personal) agrega nuestro estilo
    nombres = {F["creador"] for F in Fs}
    Fs = [F for F in Fs if not (F["creador"] in ES_ALIAS and any(F["creador"] in ALIAS.get(n, []) for n in nombres))]
    creadores = [F for F in Fs if F["creador"] != "Nosotros"]
    if creadores:
        _tabla("COMPARACION.md", creadores, filas)
    if len(creadores) < len(Fs):
        _tabla("Nosotros_comparacion.md", Fs, filas)


def _tabla(nombre_md, Fs, filas):
    L = ["# Comparación de estilos", "", "| | " + " | ".join(F["creador"] for F in Fs) + " |", "|---|" + "---|" * len(Fs)]
    for nombre, fn in filas:
        vals = []
        for F in Fs:
            try:
                v = fn(F)
                vals.append("%s %s%%" % v if isinstance(v, tuple) and v[1] != "" else str(v[0] if isinstance(v, tuple) else v))
            except Exception:
                vals.append("—")
        L.append("| %s | %s |" % (nombre, " | ".join(vals)))
    L += ["", "> Medido automáticamente. Las reglas de historia, efectos y estilo que revisa Claude están en `<Creador>_notas.md`."]
    open(os.path.join(ESTILOS, nombre_md), "w", encoding="utf-8").write("\n".join(L) + "\n")
