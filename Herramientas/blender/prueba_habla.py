# Prueba: un personaje (Sikelpa) hablando a camara con las bocas 21-25 de bocas.json. Render chico.
#   blender -b --factory-startup --python prueba_habla.py -- <carpeta_fotogramas> <bocas.json>
import bpy, sys, os, math, json, random
from mathutils import Vector
sys.path.insert(0, r"C:\Users\PC\Documents\YOUTUBE ANIMACION\Herramientas\blender")
import extras_npc as ex
a = sys.argv[sys.argv.index("--") + 1:]
out, bocas = a[0], json.load(open(a[1]))["bocas"]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; col = sc.collection
sk = ex.anexar("Sikelpa"); ex.poner(sk, (0, 0), 0, "parado")
pb = sk.pose.bones
sk.id_properties_ui("cara").update(max=30)            # la propiedad venia con tope 20: las bocas 21-25 no salian
N = len(bocas)
sc.frame_start, sc.frame_end = 1, N
sc.render.fps = 30
for i, b in enumerate(bocas):                          # una boca por fotograma (cambio seco)
    sk["cara"] = b; sk.keyframe_insert('["cara"]', frame=i + 1)
ac = sk.animation_data.action
for fc in (getattr(ac, "fcurves", None) or []):
    for k in fc.keyframe_points:
        k.interpolation = 'CONSTANT'
rnd = random.Random(3)
for b_ in pb:
    b_.rotation_mode = 'XYZ'
for f in range(1, N + 1, 6):                           # cabeza y torso vivos (sin exagerar), manos que acompanan
    t = f / 30
    pb["Head"].rotation_euler = (math.radians(3 * math.sin(t * 5.1) + rnd.uniform(-1.5, 1.5)), math.radians(5 * math.sin(t * 2.3)), math.radians(2 * math.sin(t * 3.7)))
    pb["Head"].keyframe_insert("rotation_euler", frame=f)
    pb["UpperTorso"].rotation_euler = (math.radians(1.5 * math.sin(t * 2.0)), math.radians(3 * math.sin(t * 1.4)), 0)
    pb["UpperTorso"].keyframe_insert("rotation_euler", frame=f)
    habla = sum(1 for k in bocas[f - 1:f + 5] if k != 21) > 2
    pb["RightUpperArm"].rotation_euler = (math.radians((18 if habla else 5) + rnd.uniform(-5, 6)), 0, math.radians(rnd.uniform(-6, 6)))
    pb["RightLowerArm"].rotation_euler = (math.radians((30 if habla else 8) + rnd.uniform(-6, 6)), 0, 0)
    pb["RightUpperArm"].keyframe_insert("rotation_euler", frame=f); pb["RightLowerArm"].keyframe_insert("rotation_euler", frame=f)
w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.7, 0.9, 1)
sun = bpy.data.objects.new("Sol", bpy.data.lights.new("Sol", 'SUN')); sun.data.energy = 3.2; col.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(25))
me = bpy.data.meshes.new("Piso"); me.from_pydata([(-30, -30, 0), (30, -30, 0), (30, 30, 0), (-30, 30, 0)], [], [(0, 1, 2, 3)])
pi = bpy.data.objects.new("Piso", me); col.objects.link(pi)
m = bpy.data.materials.new("Piso"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.62, 0.42, 1)
me.materials.append(m)
cd = bpy.data.cameras.new("C"); cd.lens = 50; cam = bpy.data.objects.new("C", cd); col.objects.link(cam); sc.camera = cam
cam.location = (0.4, -5.0, 4.9); cam.rotation_euler = (Vector((0, 0, 4.55)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 8; sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 540, 960
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(out, "f_")
bpy.ops.render.render(animation=True)
print("OK", N)
