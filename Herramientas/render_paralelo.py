# Renderiza un episodio (o un tramo) con VARIOS Blender a la vez: cada uno hace un pedazo seguido de fotogramas.
# Con una sola tarjeta de video no es N veces mas rapido, pero se aprovecha mejor la tarjeta
# (medido en EP002 con RTX 5070: 1 proceso = 0,96 fotogramas/s; 2 procesos = 1,5 fotogramas/s, x1,6).
#   py Herramientas/render_paralelo.py EP###_Titulo [preview|final] [--procesos 2] [--desde F] [--hasta F] [--confirmado] [--rapida]
# --rapida (solo vista previa): 8 muestras + sombras a media resolucion. Medido en EP004 (2 tramos reales, 2026-11-08):
#   36 % menos tiempo, PSNR 53,6 dB contra la vista previa normal (no se nota a simple vista). Ver docs/02_LECCIONES.md.
# Renderiza desde el .blend GUARDADO del episodio a renders/<modo>/fotogramas/c_####.png (no arma el MP4).
import argparse, json, math, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BLENDER, episodio  # noqa: E402

AJUSTES = {
    "preview": "import bpy; s=bpy.context.scene; s.render.resolution_percentage=50; s.eevee.taa_render_samples=16; s.eevee.shadow_ray_count=4; "
               "s.render.image_settings.file_format='PNG'; s.render.use_overwrite=True",
    "final": "import bpy; s=bpy.context.scene; s.render.resolution_percentage=100; s.eevee.taa_render_samples=48; s.eevee.shadow_ray_count=4; "
             "s.render.image_settings.file_format='PNG'; s.render.use_overwrite=True",
}
SEG_POR_CUADRO = {"preview": 1.0, "final": 5.0}     # un solo proceso (EP001/EP002)
GANANCIA = {1: 1.0, 2: 1.6, 3: 1.8}                 # aceleracion aproximada con N procesos en una tarjeta

ap = argparse.ArgumentParser()
ap.add_argument("ep")
ap.add_argument("modo", nargs="?", default="preview", choices=["preview", "final"])
ap.add_argument("--procesos", type=int, default=2)
ap.add_argument("--desde", type=int, default=1)
ap.add_argument("--hasta", type=int)
ap.add_argument("--confirmado", action="store_true", help="aceptar renders de mas de 15 min")
ap.add_argument("--rapida", action="store_true", help="vista previa 36%% mas rapida (8 muestras, sombras a media resolucion)")
a = ap.parse_args()
EP = episodio(a.ep)
blend = os.path.join(EP, a.ep + ".blend")
if not os.path.exists(blend):
    sys.exit("No encuentro el .blend: " + blend)
hasta = a.hasta
if hasta is None:
    tv = os.path.join(EP, "audio", "tomas_voz.json")
    if not os.path.exists(tv):
        sys.exit("Indica --hasta (ultimo fotograma)")
    hasta = json.load(open(tv, encoding="utf-8"))["frames"]
if a.rapida and a.modo == "preview":
    AJUSTES["preview"] = AJUSTES["preview"].replace("taa_render_samples=16", "taa_render_samples=8") +         "; s.eevee.shadow_resolution_scale=0.5"
    SEG_POR_CUADRO["preview"] = 0.65
n = hasta - a.desde + 1
P = max(1, min(a.procesos, 3))
est = n * SEG_POR_CUADRO[a.modo] / GANANCIA[P]
print("Fotogramas %d-%d (%d) · %s · %d procesos · estimado %.1f min" % (a.desde, hasta, n, a.modo, P, est / 60))
if est > 15 * 60 and not a.confirmado:
    sys.exit("Tarda mas de 15 min: confirmar con el usuario y repetir con --confirmado")
carpeta = os.path.join(EP, "renders", a.modo, "fotogramas")
os.makedirs(carpeta, exist_ok=True)
paso = math.ceil(n / P)
procs, t = [], time.time()
for k in range(P):
    s0 = a.desde + k * paso
    s1 = min(hasta, s0 + paso - 1)
    if s0 > s1:
        continue
    cmd = [BLENDER, "-b", blend, "--python-expr", AJUSTES[a.modo], "-o", os.path.join(carpeta, "c_####"),
           "-F", "PNG", "-x", "1", "-s", str(s0), "-e", str(s1), "-a"]
    procs.append((s0, s1, subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)))
    print("  proceso %d: fotogramas %d-%d" % (k + 1, s0, s1))
for s0, s1, p in procs:
    p.wait()
faltan = [f for f in range(a.desde, hasta + 1) if not os.path.exists(os.path.join(carpeta, "c_%04d.png" % f))
          or os.path.getmtime(os.path.join(carpeta, "c_%04d.png" % f)) < t - 1]
dur = time.time() - t
print("Listo en %.1f min (%.2f fotogramas/s)" % (dur / 60, n / dur) + ("" if not faltan else " · FALTAN %d fotogramas: %s..." % (len(faltan), faltan[:5])))
