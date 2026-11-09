# Hoja de contacto: renderiza inicio / mitad / fin de cada toma (marcadores con camara) en fotos chicas.
#   blender.exe -b episodio.blend --python hoja_contacto.py -- carpeta [porcentaje=22] [muestras=8] [toma_desde] [toma_hasta]
# Despues: py Herramientas/componer_hoja.py carpeta hoja.jpg   (junta las fotos con etiquetas)
# No guarda nada en el .blend.
import bpy, os, sys, json

a = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(a[0])     # ruta completa: Blender toma las relativas desde la raiz del disco
pct = int(a[1]) if len(a) > 1 else 22
S = int(a[2]) if len(a) > 2 else 8
t0 = int(a[3]) if len(a) > 3 else 1
t1 = int(a[4]) if len(a) > 4 else 999
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_percentage = pct
try:
    sc.eevee.taa_render_samples = S
except Exception:
    pass
sc.render.image_settings.file_format = 'JPEG'
marcas = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
indice = []
for i, m in enumerate(marcas):
    if not (t0 <= i + 1 <= t1):
        continue
    fa = m.frame
    fb = (marcas[i + 1].frame - 1) if i + 1 < len(marcas) else sc.frame_end
    fotos = []
    for f in sorted({min(fb, fa + 1), (fa + fb) // 2, max(fa, fb - 1)}):
        sc.frame_set(f)
        sc.camera = m.camera
        p = os.path.join(out, "%02d_%s_%04d.jpg" % (i + 1, m.name, f))
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        fotos.append([os.path.basename(p), f])
    indice.append({"toma": i + 1, "nombre": m.name, "desde": fa, "hasta": fb, "fotos": fotos})
    print("TOMA", i + 1, m.name, [f for _, f in fotos])
json.dump(indice, open(os.path.join(out, "indice.json"), "w", encoding="utf-8"), indent=1)
