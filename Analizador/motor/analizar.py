# ANALIZADOR DE VIDEOS — programa principal.
#   py -X utf8 Analizador/motor/analizar.py                      -> analiza todo lo NUEVO de Videos_para_analizar/<Creador>/ y actualiza las formulas
#   py -X utf8 Analizador/motor/analizar.py --creador ClusterK    -> solo ese creador
#   py -X utf8 Analizador/motor/analizar.py --video X.mp4 --creador Nosotros   -> un video suelto (de cualquier carpeta)
#   opciones: --forzar (re-analizar aunque ya este), --solo-formula, --sin-ocr, --sin-clip, --umbral 22
import argparse, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from comun import (VIDEOS, RESULTADOS, REGISTRO, VERSION, EXT_VIDEO, log, video_id, ffprobe, hacer_proxy, leer_audio,
                   guardar_json, leer_json, r)


def resumen(datos):
    tomas = datos["tomas"]
    dur = datos["video"]["duracion"]
    d = np.array([t["duracion"] for t in tomas]) if tomas else np.array([dur])

    def reparto(clave):
        c = {}
        for t in tomas:
            k = t.get(clave)
            if k is not None:
                c[k] = c.get(k, 0) + 1
        return {k: "%d%%" % round(100 * v / len(tomas)) for k, v in sorted(c.items(), key=lambda kv: -kv[1])} if tomas else {}
    tr = {}
    for x in datos["transiciones"]:
        tr[x["tipo"]] = tr.get(x["tipo"], 0) + 1
    ef = {}
    for x in datos["efectos"]:
        ef[x["tipo"]] = ef.get(x["tipo"], 0) + 1
    tercios = [[t["duracion"] for t in tomas if k * dur / 3 <= t["inicio"] < (k + 1) * dur / 3] for k in range(3)]
    pal = datos["audio"].get("palabras", [])
    alineados = 0
    if pal and len(tomas) > 1:
        ini = np.array([w["t0"] for w in pal])
        alineados = sum(1 for t in tomas[1:] if np.min(np.abs(ini - t["inicio"])) < 0.25)
    voz = datos["audio"].get("voz", {})
    return {
        "tomas": len(tomas), "cortes_por_minuto": r((len(tomas) - 1) / max(1e-6, dur) * 60, 1),
        "toma_media_s": r(d.mean()), "toma_mediana_s": r(np.median(d)), "toma_p10_s": r(np.percentile(d, 10)), "toma_p90_s": r(np.percentile(d, 90)),
        "toma_mediana_por_tercio_s": [r(np.median(x)) if x else None for x in tercios],
        "primeros_3s_cortes": sum(1 for t in tomas[1:] if t["inicio"] < 3),
        "tomas_con_temblor_pct": r(100 * np.mean([t["temblor"] for t in tomas]), 0) if tomas else 0,
        "golpes_zoom_por_minuto": r(sum(1 for t in tomas if t["camara"] == "golpe de zoom") / max(1e-6, dur) * 60, 1),
        "planos_pct": reparto("plano"), "camara_pct": reparto("camara"), "ambiente_pct": reparto("ambiente"), "hora_pct": reparto("hora"),
        "transiciones_pct": {k: "%d%%" % round(100 * v / max(1, len(datos["transiciones"]))) for k, v in sorted(tr.items(), key=lambda kv: -kv[1])},
        "efectos_por_tipo": dict(sorted(ef.items(), key=lambda kv: -kv[1])),
        "efectos_por_minuto": r(len(datos["efectos"]) / max(1e-6, dur) * 60, 1),
        "palabras_por_s": voz.get("palabras_por_s"),
        "cortes_en_palabra_pct": r(100 * alineados / max(1, len(tomas) - 1), 0) if pal else None,
    }


def analizar_video(ruta, creador, args):
    import vision, subtitulos, audio, historia, reporte
    t_ini = time.time()
    vid = video_id(ruta)
    out = os.path.join(RESULTADOS, creador, vid)
    os.makedirs(out, exist_ok=True)
    info = ffprobe(ruta)
    log("\n== %s / %s  (%.0f s, %dx%d, %.0f fps)" % (creador, os.path.basename(ruta), info["duracion"], info["ancho"], info["alto"], info["fps"]))
    proxy = os.path.join(out, "proxy.mp4")
    if not os.path.exists(proxy) or args.forzar:
        hacer_proxy(ruta, proxy, info["fps"])
    pinfo = ffprobe(proxy)
    fps = pinfo["fps"] or 30.0
    import cv2
    cap = cv2.VideoCapture(proxy)
    nf = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    datos = {"version": VERSION, "creador": creador, "id": vid,
             "video": {"archivo": os.path.basename(ruta), "ruta": ruta, **info, "fps_analisis": fps, "fotogramas_analisis": nf}}

    log("  1/6 cortes y movimiento de cámara...")
    cortes = vision.detectar_cortes(proxy, fps, nf, args.umbral)
    m, nf = vision.medir_fotogramas(proxy, cortes, nf)
    cortes = [c for c in cortes if c < nf] + [nf]
    datos["video"]["fotogramas_analisis"] = nf
    tomas = vision.analizar_tomas(m, cortes, fps)
    trans = vision.detectar_transiciones(m, cortes, fps, tomas, proxy)
    for x in trans:
        tomas[x["toma"] - 1]["transicion_entrada"] = x["tipo"]
    if tomas:
        tomas[0]["transicion_entrada"] = "inicio"
    efectos = vision.detectar_efectos(m, cortes, fps, tomas)
    log("    %d tomas, %d transiciones especiales, %d posibles efectos" % (len(tomas), sum(1 for x in trans if x["tipo"] != "corte directo"), len(efectos)))

    log("  2/6 voz y audio...")
    au = {}
    if info["audio"]:
        a16 = leer_audio(ruta)
        pal, segs, idi = audio.transcribir(a16)
        au = {"palabras": pal, "segmentos": segs, "idioma": idi, "voz": audio.voz(pal, info["duracion"]),
              "sonoridad": audio.sonoridad(ruta), "sonidos": audio.sonidos(a16, pal, info["duracion"])}
        log("    %d palabras (%s), %s LUFS" % (len(pal), (idi or {}).get("idioma"), au["sonoridad"].get("lufs")))
    for t in tomas:
        t["texto"] = " ".join(w["p"] for w in au.get("palabras", []) if t["inicio"] <= w["t0"] < t["fin"])

    log("  3/6 tipo de plano, personajes y ambiente (CLIP + Grounding DINO)...")
    if not args.sin_clip and tomas:
        vision.clasificar_tomas(proxy, tomas)
        vision.medir_personajes(proxy, tomas)

    log("  4/6 subtítulos (OCR)...")
    subs = {"hay_subtitulos": False}
    if not args.sin_ocr:
        subs = subtitulos.analizar(proxy, fps, nf, au.get("palabras", []))

    log("  5/6 historia...")
    hist = historia.analizar(au.get("segmentos", []), au.get("palabras", []), info["duracion"])

    datos.update({"tomas": tomas, "transiciones": trans, "efectos": efectos, "audio": au, "subtitulos": subs, "historia": hist})
    datos["resumen"] = resumen(datos)
    datos["segundos_de_analisis"] = r(time.time() - t_ini, 1)

    log("  6/6 imágenes y reportes...")
    vision.imagenes(proxy, tomas, efectos, out)
    guardar_json(os.path.join(out, "datos.json"), datos)
    reporte.grafica(out, datos, m)
    reporte.ficha(out, datos)
    reporte.html_reporte(out, datos)
    historia.para_claude(out, os.path.basename(ruta), creador, datos)
    log("  listo en %.0f s -> %s" % (time.time() - t_ini, out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creador")
    ap.add_argument("--video")
    ap.add_argument("--forzar", action="store_true")
    ap.add_argument("--solo-formula", action="store_true")
    ap.add_argument("--sin-ocr", action="store_true")
    ap.add_argument("--sin-clip", action="store_true")
    ap.add_argument("--umbral", type=float, default=22.0)
    args = ap.parse_args()
    import estilo

    if args.video:
        if not args.creador:
            sys.exit("Con --video hay que decir --creador")
        lista = [(args.creador, os.path.abspath(args.video))]
    else:
        creadores = [args.creador] if args.creador else sorted(d for d in os.listdir(VIDEOS) if os.path.isdir(os.path.join(VIDEOS, d)))
        lista = []
        for c in creadores:
            carpeta = os.path.join(VIDEOS, c)
            for raiz, _, fs in os.walk(carpeta):
                for f in sorted(fs):
                    if f.lower().endswith(EXT_VIDEO):
                        lista.append((c, os.path.join(raiz, f)))
    reg = leer_json(REGISTRO, {})
    tocados = set()
    if not args.solo_formula:
        pendientes = []
        for c, ruta in lista:
            st = os.stat(ruta)
            clave = c + "|" + ruta
            prev = reg.get(clave)
            hecho = prev and prev.get("tam") == st.st_size and prev.get("version") == VERSION and \
                os.path.exists(os.path.join(prev.get("salida", ""), "datos.json"))
            if hecho and not args.forzar:
                continue
            pendientes.append((c, ruta, clave, st))
        log("Videos encontrados: %d · por analizar: %d" % (len(lista), len(pendientes)))
        for k, (c, ruta, clave, st) in enumerate(pendientes, 1):
            log("\n[%d/%d]" % (k, len(pendientes)))
            try:
                out = analizar_video(ruta, c, args)
                reg[clave] = {"tam": st.st_size, "version": VERSION, "salida": out, "fecha": time.strftime("%Y-%m-%d %H:%M")}
                guardar_json(REGISTRO, reg)
                tocados.add(c)
            except Exception:
                log("  ERROR con este video (se sigue con los demás):")
                traceback.print_exc()
    creadores_formula = {args.creador} if args.creador else (tocados or {c for c, _ in lista})
    if args.solo_formula and not args.creador:
        creadores_formula = {d for d in os.listdir(RESULTADOS) if os.path.isdir(os.path.join(RESULTADOS, d))}
    for c in sorted(creadores_formula):
        if not c.startswith("_"):          # _Tutoriales y similares: se analizan pero no son un estilo
            estilo.construir(c)
    estilo.comparar()
    log("\nFórmulas actualizadas en Analizador/Estilos/")


if __name__ == "__main__":
    main()
