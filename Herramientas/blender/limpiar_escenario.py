# Abre un .blend de episodio y guarda solo el escenario (sin personajes, camaras ni marcadores del episodio).
# Uso: blender -b EPISODIO.blend --python limpiar_escenario.py -- SALIDA.blend
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
for cname in ("CRISTA", "CR_Camaras"):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.all_objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)
sc = bpy.context.scene
for m in list(sc.timeline_markers):
    if m.name.startswith("CR_"):
        sc.timeline_markers.remove(m)
sc.frame_start, sc.frame_end = 1, 250
cam = bpy.data.objects.get("Cam_CentroAerea") or bpy.data.objects.get("Cam_Calle")
if cam:
    sc.camera = cam
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("ESCENARIO LIMPIO ->", out, "| objetos:", len(bpy.data.objects))
