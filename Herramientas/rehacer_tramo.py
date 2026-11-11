# Rehace SOLO un tramo del video (ej. del segundo 10 al 15) sin volver a renderizar todo.
#   py Herramientas/rehacer_tramo.py EP001_Crista_Llega_Tarde 10 15              -> vista previa (50 %, 16 muestras)
#   py Herramientas/rehacer_tramo.py EP001_Crista_Llega_Tarde 10 15 --final      -> calidad final
#   py Herramientas/rehacer_tramo.py EP001_Crista_Llega_Tarde --deshacer         -> regresa los fotogramas del ultimo respaldo
#   py Herramientas/rehacer_tramo.py EP004_Titulo --toma 12          -> rehace SOLO la toma 12 (un cambio de camara)
#   py Herramientas/rehacer_tramo.py EP004_Titulo --toma 12-14       -> rehace las tomas 12 a 14
#   py Herramientas/rehacer_tramo.py EP004_Titulo --tomas            -> lista las tomas con sus segundos y fotogramas
# Las tomas salen de audio/tomas_voz.json (una linea de narracion = una toma = una camara). Trabajar por toma es la
# regla del kit: si algo no gusta se cambia y se renderiza solo esa toma; el sonido se vuelve a mezclar solo.
# Pasos: 1) respalda en Respaldos/ los fotogramas viejos de ese tramo, 2) renderiza solo ese tramo en segundo plano
# desde el .blend GUARDADO del episodio, 3) si ya estan todos los fotogramas, vuelve a armar el MP4 (voz, efectos, subtitulos).
# Antes de correrlo: guardar el .blend con los cambios del tramo (Ctrl+S en Blender).
import argparse, glob, math, os, shutil, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BLENDER, FPS, RESPALDOS, episodio, HERRAMIENTAS  # noqa: E402

SEG_POR_CUADRO = {"preview": 1.0, "final": 5.0}     # medido en EP001 (RTX 5070)
AJUSTES = {
    "preview": "import bpy; s=bpy.context.scene; s.render.resolution_percentage=50; s.eevee.taa_render_samples=16; s.eevee.shadow_ray_count=4; "
               "s.render.image_settings.file_format='PNG'; s.render.use_overwrite=True",
    "final": "import bpy; s=bpy.context.scene; s.render.resolution_percentage=100; s.eevee.taa_render_samples=48; s.eevee.shadow_ray_count=4; "
             "s.render.image_settings.file_format='PNG'; s.render.use_overwrite=True",
}


def fotogramas(carpeta):
    return sorted(glob.glob(os.path.join(carpeta, "c_*.png")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("desde", nargs="?", type=float)
    ap.add_argument("hasta", nargs="?", type=float)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--blend", help="otro .blend (por defecto EP###/EP###.blend)")
    ap.add_argument("--confirmado", action="store_true", help="aceptar renders de mas de 15 min")
    ap.add_argument("--sin-armar", action="store_true")
    ap.add_argument("--deshacer", action="store_true")
    ap.add_argument("--toma", help="N o N-M: rehacer solo esas tomas (de audio/tomas_voz.json)")
    ap.add_argument("--tomas", action="store_true", help="listar las tomas y sus segundos")
    a = ap.parse_args()
    modo = "final" if a.final else "preview"
    EP = episodio(a.ep)
    carpeta = os.path.join(EP, "renders", modo, "fotogramas")
    os.makedirs(carpeta, exist_ok=True)
    import limpiar_episodio                      # episodio ya limpio: sus PNG quedaron en fotogramas/fotogramas.mp4
    limpiar_episodio.restaurar(carpeta)

    if a.deshacer:
        resp = sorted(glob.glob(os.path.join(RESPALDOS, "%s_%s_*" % (a.ep, modo))))
        if not resp:
            sys.exit("No hay respaldos de %s (%s)" % (a.ep, modo))
        ult = resp[-1]
        for f in glob.glob(os.path.join(ult, "c_*.png")):
            shutil.copy2(f, carpeta)
        print("Regresados los fotogramas de", ult)
        armar(a.ep, modo, carpeta)
        return

    if a.tomas or a.toma:
        tv = os.path.join(EP, "audio", "tomas_voz.json")
        if not os.path.exists(tv):
            sys.exit("Falta audio/tomas_voz.json (se crea con tomas_desde_voz.py despues de la voz)")
        import json
        tomas = {t["n"]: t for t in json.load(open(tv, encoding="utf-8"))["tomas"]}
        if a.tomas:
            for n, t in tomas.items():
                print("Toma %2d  %6.2f–%6.2f s  f%04d–%04d  %s" % (n, (t["f_ini"] - 1) / FPS, t["f_fin"] / FPS,
                                                                  t["f_ini"], t["f_fin"], t["texto"][:60]))
            return
        n0, n1 = (int(x) for x in (a.toma.split("-") + [a.toma])[:2]) if "-" in a.toma else (int(a.toma), int(a.toma))
        if n0 not in tomas or n1 not in tomas:
            sys.exit("No existe esa toma (hay %d)" % len(tomas))
        a.desde = (tomas[n0]["f_ini"] - 1) / FPS
        a.hasta = tomas[n1]["f_fin"] / FPS
        print("Tomas %d–%d: %s" % (n0, n1, tomas[n0]["texto"][:70]))
    if a.desde is None or a.hasta is None or a.hasta <= a.desde:
        sys.exit("Uso: py rehacer_tramo.py EP###_Titulo DESDE HASTA (segundos) [--final]")
    blend = a.blend or os.path.join(EP, a.ep + ".blend")
    if not os.path.exists(blend):
        sys.exit("No encuentro el .blend: " + blend)
    f0 = int(math.floor(a.desde * FPS)) + 1          # fotogramas de Blender empiezan en 1 (c_0001 = segundo 0)
    f1 = int(math.ceil(a.hasta * FPS))
    n = f1 - f0 + 1
    est = n * SEG_POR_CUADRO[modo] + 20
    print("Tramo %.2f–%.2f s = fotogramas %d–%d (%d) · %s · estimado %.0f s" % (a.desde, a.hasta, f0, f1, n, modo, est))
    if est > 15 * 60 and not a.confirmado:
        sys.exit("Tarda más de 15 min: confirmar con el usuario y repetir con --confirmado")

    # 1) respaldo de los fotogramas viejos del tramo
    viejos = [os.path.join(carpeta, "c_%04d.png" % f) for f in range(f0, f1 + 1)]
    viejos = [f for f in viejos if os.path.exists(f)]
    if viejos:
        dest = os.path.join(RESPALDOS, "%s_%s_%s_f%04d-%04d" % (a.ep, modo, time.strftime("%Y%m%d-%H%M%S"), f0, f1))
        os.makedirs(dest, exist_ok=True)
        for f in viejos:
            shutil.copy2(f, dest)
        print("Respaldo de %d fotogramas -> %s" % (len(viejos), dest))

    # 2) render solo del tramo, en segundo plano
    t = time.time()
    cmd = [BLENDER, "-b", blend, "--python-expr", AJUSTES[modo], "-o", os.path.join(carpeta, "c_####"),
           "-F", "PNG", "-x", "1", "-s", str(f0), "-e", str(f1), "-a"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    hechos = [f for f in range(f0, f1 + 1) if os.path.exists(os.path.join(carpeta, "c_%04d.png" % f))
              and os.path.getmtime(os.path.join(carpeta, "c_%04d.png" % f)) >= t - 1]
    if len(hechos) < n:
        print(p.stdout[-1500:], p.stderr[-1500:])
        sys.exit("Render incompleto: %d de %d fotogramas" % (len(hechos), n))
    print("Render listo: %d fotogramas en %.0f s" % (n, time.time() - t))
    if not a.sin_armar:
        armar(a.ep, modo, carpeta)


def armar(ep, modo, carpeta):
    """vuelve a armar el MP4 si ya existen todos los fotogramas del episodio."""
    fs = fotogramas(carpeta)
    nums = sorted(int(os.path.basename(f)[2:6]) for f in fs)
    if not nums:
        return
    faltan = [k for k in range(1, nums[-1] + 1) if k not in set(nums)]
    if faltan or nums[0] != 1:
        rangos, ini = [], None
        for k in faltan:
            if ini is None or k != prev + 1:
                if ini is not None:
                    rangos.append((ini, prev))
                ini = k
            prev = k
        if ini is not None:
            rangos.append((ini, prev))
        print("Aún faltan fotogramas para armar el video completo:",
              ", ".join("%d–%d (%.1f–%.1f s)" % (x, y, (x - 1) / FPS, y / FPS) for x, y in rangos[:8]))
        return
    script = os.path.join(episodio(ep), "scripts", "armar_video.py")
    if not os.path.exists(script):
        script = os.path.join(HERRAMIENTAS, "audio", "armar_video.py")
    print("Armando el video con", os.path.relpath(script, os.path.dirname(HERRAMIENTAS)))
    subprocess.run([sys.executable, script, ep, modo], check=False)


if __name__ == "__main__":
    main()
