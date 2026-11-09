# Saca fotos de revision de un escenario desde camaras temporales (no modifica el .blend).
#   blender -b escenario.blend --python fotos_escenario.py -- vistas.json carpeta_salida [ancho alto muestras]
# vistas.json: [{"nombre": "sala", "ref": "Casa_Der_09", "cam": [x,y,z], "mira": [x,y,z], "lente": 18}, ...]
#   "ref": objeto cuyas coordenadas LOCALES se usan para cam/mira (omitir = coordenadas del mundo).
#   "noche": true -> apaga el sol y pone noche SUAVE (un poco luminosa, como gusta en el canal); "noche": "oscura" -> mas oscura.
#   "props": {"Parque_Control": {"luces": 1.0}} -> cambia propiedades de objetos antes de la foto (drivers incluidos).
import bpy, json, math, os, sys
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
vistas = json.load(open(a[0], encoding="utf-8"))
out = os.path.abspath(a[1])     # ruta completa: Blender toma las relativas desde la raiz del disco
W, H, S = (int(a[2]), int(a[3]), int(a[4])) if len(a) >= 5 else (960, 540, 16)
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
try:
    sc.eevee.taa_render_samples = S
except Exception:
    pass
sc.render.image_settings.file_format = 'JPEG'
for m in list(sc.timeline_markers):      # que los marcadores no cambien la camara
    m.camera = None
cd = bpy.data.cameras.new("FotoCam")
cam = bpy.data.objects.new("FotoCam", cd)
sc.collection.objects.link(cam)
cd.clip_start = 0.1
cd.clip_end = 3000
sc.camera = cam
soles = [o for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SUN']
for v in vistas:
    ref = bpy.data.objects.get(v.get("ref", "")) if v.get("ref") else None
    M = ref.matrix_world if ref else None
    p = Vector(v["cam"]); t = Vector(v["mira"])
    if M:
        p, t = M @ p, M @ t
    cam.location = p
    cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = v.get("lente", 24)
    noche = v.get("noche", False)
    for s in soles:
        s.hide_render = noche
    if sc.world and sc.world.use_nodes:
        # el Background que ilumina (no el del cielo decorativo "Cielo_"): de noche se oscurece su color y el cielo
        # decorativo pasa solo a estrellas
        fondos = [n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND']
        bg = next((n for n in fondos if not n.name.startswith("Cielo_")), fondos[0] if fondos else None)
        if bg:
            if "_color_dia" not in sc.world:
                sc.world["_color_dia"] = list(bg.inputs[0].default_value)
            if noche:
                bg.inputs[0].default_value = (0.012, 0.016, 0.035, 1) if noche == "oscura" else (0.045, 0.055, 0.1, 1)
            else:
                bg.inputs[0].default_value = sc.world["_color_dia"]
                bg.inputs[1].default_value = v.get("cielo", bg.inputs[1].default_value)
    for nom, d in v.get("props", {}).items():
        ob = bpy.data.objects.get(nom)
        for k, val in (d.items() if ob else []):
            ob[k] = val
    sc.frame_set(sc.frame_current)          # que los drivers tomen los valores nuevos
    sc.render.filepath = os.path.join(out, v["nombre"] + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("FOTO", v["nombre"])
