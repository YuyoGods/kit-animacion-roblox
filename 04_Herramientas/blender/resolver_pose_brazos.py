# Busca los angulos de brazos para que las manos lleguen a un punto (y pies planos), y guarda vistas de la pose.
# Uso: blender.exe -b --factory-startup --python resolver_pose_brazos.py -- RIG.blend [NombreDelRig]
#   ej. -- "01_Personajes/2_Secundarios/Crista/Crista_R15_Rig.blend" Crista_Rig
# Editar BODY (pose del cuerpo) y el objetivo de las manos antes de correrlo.
import bpy, math, itertools, os, sys
from mathutils import Vector
_a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not _a:
    sys.exit("Uso: blender -b --factory-startup --python resolver_pose_brazos.py -- RIG.blend [NombreDelRig]")
RIG_BLEND = os.path.abspath(_a[0])
RIG_NOMBRE = _a[1] if len(_a) > 1 else "Crista_Rig"
bpy.ops.wm.open_mainfile(filepath=RIG_BLEND)
sc = bpy.context.scene
rig = bpy.data.objects[RIG_NOMBRE]; pb = rig.pose.bones
rig["IK_Piernas"] = 0.0; rig["IK_Brazos"] = 0.0
D = math.radians
BODY = {"RightUpperLeg": (86, 0, 4), "RightLowerLeg": (-86, 0, 0),
        "LeftUpperLeg": (-12, 0, -3), "LeftLowerLeg": (-78, 0, 0),
        "LowerTorso": (0, 0, 0), "UpperTorso": (34, 0, 0), "Head": (30, 0, 0)}
HRP_Z = -0.76


def upd():
    bpy.context.view_layer.update()


def W(b, tail=True):
    return rig.matrix_world @ (pb[b].tail if tail else pb[b].head)


for b in pb:
    b.rotation_mode = 'XYZ'; b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
for b, r in BODY.items():
    pb[b].rotation_euler = [D(a) for a in r]
pb["HumanoidRootPart"].location = (0, 0, HRP_Z)
upd()
# pies planos: buscar el giro de cada pie para que quede horizontal
for s in ("Right",):
    best = None
    for a in range(-70, 71, 1):
        pb[s + "Foot"].rotation_euler = (D(a), 0, 0); upd()
        v = W(s + "Foot") - W(s + "Foot", False)
        e = abs(v.z)
        if best is None or e < best[0]:
            best = (e, a)
    pb[s + "Foot"].rotation_euler = (D(best[1]), 0, 0)
    print("pie", s, "X =", best[1])
pb["LeftFoot"].rotation_euler = (D(-55), 0, 0)
upd()
for s in ("Right", "Left"):
    print("  tobillo", s, [round(v, 2) for v in W(s + "LowerLeg")], "punta", [round(v, 2) for v in W(s + "Foot")], "rodilla", [round(v, 2) for v in W(s + "UpperLeg")])
# objetivo: el zapato derecho (empeine), una mano a cada lado del cordon
ank = W("RightLowerLeg"); toe = W("RightFoot")
shoe = ank.lerp(toe, 0.45) + Vector((0, 0, 0.32))
TGT = {"Right": shoe + Vector((-0.22, 0, 0)), "Left": shoe + Vector((0.22, 0, 0.05))}
SOL = {}
for s in ("Right", "Left"):
    best = None
    for ux, uz, lx in itertools.product(range(0, 141, 5), range(-75, 76, 5), range(0, 101, 10)):
        pb[s + "UpperArm"].rotation_euler = (D(ux), 0, D(uz))
        pb[s + "LowerArm"].rotation_euler = (D(lx), 0, 0)
        upd()
        e = (W(s + "Hand") - TGT[s]).length + 0.002 * (abs(uz) + lx * 0.3)
        if best is None or e < best[0]:
            best = (e, ux, uz, lx)
    pb[s + "UpperArm"].rotation_euler = (D(best[1]), 0, D(best[2]))
    pb[s + "LowerArm"].rotation_euler = (D(best[3]), 0, 0)
    SOL[s] = best
    print("brazo", s, "UpperArm X=%d Z=%d LowerArm X=%d" % tuple(best[1:]), "error=%.3f" % best[0])
upd()
print("SOL", {k: v[1:] for k, v in SOL.items()}, "pies", {s: round(math.degrees(pb[s + "Foot"].rotation_euler.x)) for s in ("Right", "Left")})
# vistas de la pose
OUT = os.path.join(os.path.dirname(RIG_BLEND), "pruebas_pose")   # junto al rig
sun = bpy.data.objects.new("Sol", bpy.data.lights.new("Sol", 'SUN')); sun.data.energy = 3; sun.rotation_euler = (D(50), 0, D(25)); sc.collection.objects.link(sun)
if not sc.world:
    sc.world = bpy.data.worlds.new("W")
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 16; sc.render.resolution_x, sc.render.resolution_y = 420, 560
sc.view_settings.view_transform = 'Standard'
for k, off in enumerate((Vector((6, 0.5, 1.8)), Vector((0.5, -6, 1.8)), Vector((-4.5, -4.5, 2.2)))):
    cd = bpy.data.cameras.new("c"); cd.lens = 40
    c = bpy.data.objects.new("c", cd); sc.collection.objects.link(c)
    c.location = off; c.rotation_euler = (Vector((0, 0, 1.5)) - c.location).to_track_quat('-Z', 'Y').to_euler(); sc.camera = c
    sc.render.filepath = os.path.join(OUT, "tie_%d.png" % k); bpy.ops.render.render(write_still=True)
