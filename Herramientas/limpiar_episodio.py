# Limpia los residuos de un episodio TERMINADO para liberar espacio (pedido del usuario 2026-11-11: cada episodio
# dejaba 2-6 GB de fotogramas PNG). Se queda con los videos entregados (MP4 de preview/ y final/) y con el .blend.
#   py Herramientas/limpiar_episodio.py                          -> SIMULACRO de todos: que borraria y cuanto libera
#   py Herramientas/limpiar_episodio.py EP007 EP008              -> simulacro de esos episodios
#   py Herramientas/limpiar_episodio.py EP007 --borrar           -> lo hace de verdad (NO se puede deshacer)
#   py Herramientas/limpiar_episodio.py --todos --excepto EP011 EP012 --borrar
#   py Herramientas/limpiar_episodio.py EP007 --restaurar [final] -> vuelve a sacar los PNG del video comprimido
# Que borra (solo dentro de Episodios/EP###/renders/):
#   - borrador/, pruebas/ y cualquier otra carpeta de pruebas (revision/, espejo/...) y archivos sueltos (.log)
#   - los PNG de preview/fotogramas y final/fotogramas. ANTES los guarda en fotogramas/fotogramas.mp4 (~5 % del peso,
#     calidad casi identica) para que "rehacer la toma 12" siga funcionando sin renderizar todo de nuevo:
#     rehacer_tramo.py y armar_video.py los restauran solos (o con --restaurar).
#   - otras carpetas fotogramas_* de versiones viejas (ej. fotogramas_voz_temporal)
#   - con --respaldos: los respaldos de fotogramas de rehacer_tramo en Respaldos/EP###_<modo>_<fecha>_f####-####
# Protecciones: no toca un episodio sin video MP4 en preview/ o final/, ni uno con archivos de render de los ultimos
# 20 min (se esta renderizando), ni fotogramas que no pudo comprimir y comprobar (mismo numero de cuadros).
import argparse, glob, os, re, shutil, stat, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import EPISODIOS, FPS, RESPALDOS  # noqa: E402

VIDEO_FOTOGRAMAS = "fotogramas.mp4"
RECIENTE_MIN = 20
MODOS = ("preview", "final")


def peso(ruta):
    if os.path.isfile(ruta):
        return os.path.getsize(ruta)
    total = 0
    for d, _, fs in os.walk(ruta):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(d, f))
            except OSError:
                pass
    return total


def mb(b):
    return "%.2f GB" % (b / 1024 ** 3) if b >= 1024 ** 3 else "%.0f MB" % (b / 1024 ** 2)


def ultimo_cambio(ruta):
    ult = 0
    for d, _, fs in os.walk(ruta):
        for f in fs:
            try:
                ult = max(ult, os.path.getmtime(os.path.join(d, f)))
            except OSError:
                pass
    return ult


def pngs(carpeta):
    return sorted(glob.glob(os.path.join(carpeta, "c_*.png")))


def contiguos(fs):
    nums = [int(m.group(1)) for m in (re.match(r"c_(\d+)\.png$", os.path.basename(f)) for f in fs) if m]
    return bool(nums) and nums[0] == 1 and nums[-1] == len(nums)


def cuadros_video(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=nb_read_packets", "-of", "csv=p=0", mp4], capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return -1


def borrar(ruta):
    def _forzar(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if os.path.isdir(ruta):
        shutil.rmtree(ruta, onerror=_forzar)
    elif os.path.exists(ruta):
        os.chmod(ruta, stat.S_IWRITE)
        os.remove(ruta)


def comprimir(carpeta):
    """guarda los PNG en fotogramas.mp4 (H.264 4:4:4, crf 12) y comprueba el numero de cuadros."""
    fs = pngs(carpeta)
    out = os.path.join(carpeta, VIDEO_FOTOGRAMAS)
    tmp = out + ".tmp.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(carpeta, "c_%04d.png"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv444p", tmp]
    t = time.time()
    if subprocess.run(cmd).returncode != 0 or cuadros_video(tmp) != len(fs):
        borrar(tmp)
        return False
    os.replace(tmp, out)
    print("      comprimidos %d fotogramas -> %s (%s, %.0f s)" % (len(fs), VIDEO_FOTOGRAMAS, mb(peso(out)), time.time() - t))
    return True


def restaurar(carpeta):
    """saca los PNG c_0001.png... de fotogramas.mp4 (lo usan rehacer_tramo.py y armar_video.py)."""
    mp4 = os.path.join(carpeta, VIDEO_FOTOGRAMAS)
    if pngs(carpeta) or not os.path.exists(mp4):
        return False
    print("Restaurando los fotogramas desde", os.path.relpath(mp4, EPISODIOS), "...")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-pix_fmt", "rgb24", "-start_number", "1",
                    os.path.join(carpeta, "c_%04d.png")], check=True)
    print("  %d fotogramas listos" % len(pngs(carpeta)))
    return True


def plan(ep_dir, con_respaldos):
    """devuelve (motivo_para_no_tocar | None, [(accion, ruta, bytes)])"""
    renders = os.path.join(ep_dir, "renders")
    if not os.path.isdir(renders):
        return "sin carpeta renders", []
    videos = [v for m in MODOS for v in glob.glob(os.path.join(renders, m, "*.mp4"))]
    if not videos:
        return "sin video terminado (no hay MP4 en preview/ ni final/)", []
    hace = (time.time() - ultimo_cambio(renders)) / 60
    if hace < RECIENTE_MIN:
        return "hay archivos de render de hace %.0f min (¿se está renderizando?)" % hace, []
    acc = []
    for n in sorted(os.listdir(renders)):
        p = os.path.join(renders, n)
        if n in MODOS:
            continue
        acc.append(("borrar", p, peso(p)))
    for m in MODOS:
        md = os.path.join(renders, m)
        if not os.path.isdir(md):
            continue
        for n in sorted(os.listdir(md)):
            p = os.path.join(md, n)
            if n == "fotogramas" and os.path.isdir(p):
                fs = pngs(p)
                if not fs:
                    continue
                b = sum(os.path.getsize(f) for f in fs)
                if not glob.glob(os.path.join(md, "*.mp4")):
                    continue                     # este modo no tiene video: no se tocan sus fotogramas
                acc.append(("comprimir" if contiguos(fs) else "dejar (fotogramas incompletos)", p, b))
            elif n.startswith("fotogramas") and os.path.isdir(p):
                acc.append(("borrar", p, peso(p)))
    if con_respaldos:
        nombre = os.path.basename(ep_dir)
        for p in sorted(glob.glob(os.path.join(RESPALDOS, nombre + "_*"))):
            if os.path.isdir(p) and re.search(r"_(preview|final)_\d{8}-\d{6}_f\d{4}-\d{4}$", p):
                acc.append(("borrar", p, peso(p)))
    return None, acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("eps", nargs="*", help="EP007 o EP007_Titulo (vacio = todos)")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--excepto", nargs="*", default=[])
    ap.add_argument("--borrar", action="store_true", help="borrar de verdad (sin esto solo es simulacro)")
    ap.add_argument("--respaldos", action="store_true", help="tambien los respaldos de fotogramas en Respaldos/")
    ap.add_argument("--restaurar", nargs="?", const="preview", choices=MODOS, help="sacar los PNG de fotogramas.mp4")
    a = ap.parse_args()

    todos = sorted(d for d in glob.glob(os.path.join(EPISODIOS, "EP*")) if os.path.isdir(d))
    if a.eps:
        sel = [d for d in todos if any(os.path.basename(d) == e or os.path.basename(d).startswith(e + "_") for e in a.eps)]
        if not sel:
            sys.exit("No encuentro los episodios: " + " ".join(a.eps))
    else:
        sel = todos
    sel = [d for d in sel if not any(os.path.basename(d) == e or os.path.basename(d).startswith(e + "_") for e in a.excepto)]

    if a.restaurar:
        for d in sel:
            if not restaurar(os.path.join(d, "renders", a.restaurar, "fotogramas")):
                print(os.path.basename(d), ": no hay nada que restaurar (ya tiene PNG o no hay", VIDEO_FOTOGRAMAS + ")")
        return

    print("SIMULACRO (no se borra nada; agrega --borrar para hacerlo)\n" if not a.borrar else "BORRANDO DE VERDAD\n")
    libera = 0
    for d in sel:
        motivo, acc = plan(d, a.respaldos)
        nombre = os.path.basename(d)
        if motivo:
            print("%s: NO SE TOCA — %s" % (nombre, motivo))
            continue
        if not acc:
            print("%s: ya está limpio" % nombre)
            continue
        sub = sum(b for x, _, b in acc if x in ("borrar", "comprimir"))
        print("%s: libera ~%s" % (nombre, mb(sub)))
        for x, p, b in acc:
            rel = os.path.relpath(p, os.path.dirname(EPISODIOS))
            print("   %-9s %8s  %s" % (x if x != "comprimir" else "PNG->mp4", mb(b), rel))
            if not a.borrar:
                continue
            if x == "borrar":
                borrar(p)
            elif x == "comprimir":
                if comprimir(p):
                    for f in pngs(p):
                        borrar(f)
                else:
                    print("      NO se pudo comprimir y comprobar: se dejan los PNG")
                    sub -= b
        libera += sub
    print("\nTotal %s: ~%s" % ("liberado" if a.borrar else "que se liberaría", mb(libera)))


if __name__ == "__main__":
    main()
