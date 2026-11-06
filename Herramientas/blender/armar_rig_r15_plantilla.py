# PLANTILLA para armar el rig R15 de un personaje nuevo (ejemplo real: Crista).
# 1) Copiar este archivo a la carpeta del personaje: Personajes/<Protagonista|Secundarios|Pueblo_NPC>/<Nombre>/build_<nombre>_rig.py
# 2) Cambiar "Crista" por el nombre, y ajustar PARTS (grupo del OBJ -> pieza R15) y ACC (accesorios).
# 3) blender -b --factory-startup --python build_<nombre>_rig.py   -> <Nombre>_R15_Rig.blend + previews/
#
# Arma a Crista (cuerpo R15 + accesorios) con un rig R15 tipo "Blocky R15" ajustado a sus medidas.
# Uso: blender -b --factory-startup --python build_crista_rig.py
# Resultado: Crista_R15_Rig.blend en esta misma carpeta.
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

D = os.path.dirname(os.path.abspath(__file__))   # carpeta del personaje (donde esta Personaje.obj)
OUT_BLEND = os.path.join(D, "Crista_R15_Rig.blend")
PREV = os.path.join(D, "previews")
os.makedirs(PREV, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Crista"

# ---------------- importar ----------------
bpy.ops.wm.obj_import(filepath=os.path.join(D, "Personaje.obj"), forward_axis='NEGATIVE_Z', up_axis='Y', use_split_groups=True)
body = {o.name: o for o in bpy.context.selected_objects}
bpy.ops.wm.obj_import(filepath=os.path.join(D, "Accesorios", "acc.obj"), forward_axis='NEGATIVE_Z', up_axis='Y', use_split_groups=True)
accs = {o.name: o for o in bpy.context.selected_objects}

PARTS = {  # grupo del OBJ -> nombre R15 (Right = lado derecho de Crista = -X)
    "Crista5": "Head", "Crista6": "UpperTorso", "Crista15": "LowerTorso",
    "Crista3": "RightUpperArm", "Crista2": "RightLowerArm", "Crista12": "RightHand",
    "Crista4": "LeftUpperArm", "Crista14": "LeftLowerArm", "Crista9": "LeftHand",
    "Crista1": "RightUpperLeg", "Crista11": "RightLowerLeg", "Crista13": "RightFoot",
    "Crista8": "LeftUpperLeg", "Crista7": "LeftLowerLeg", "Crista10": "LeftFoot",
}
ACC = {  # accesorio -> (nombre, hueso al que va pegado)
    "Handle3": ("Acc_Cabello_Coletas", "Head"), "Handle5": ("Acc_Cabello_Frente", "Head"),
    "Handle6": ("Acc_Cabeza", "Head"), "Handle1": ("Acc_Mono_Cuello", "UpperTorso"),
    "Handle2": ("Acc_Falda_Exterior", "LowerTorso"), "Handle4": ("Acc_Falda_Interior", "LowerTorso"),
}
P = {}
for g, n in PARTS.items():
    o = body[g]; o.name = "Crista_" + n; o.data.name = o.name; P[n] = o
A = {}
for g, (n, bone) in ACC.items():
    o = accs[g]; o.name = "Crista_" + n; o.data.name = o.name; A[n] = (o, bone)

# subir todo para que los pies toquen el piso (z = 0)
allv = [o.matrix_world @ v.co for o in list(P.values()) + [a[0] for a in A.values()] for v in o.data.vertices]
lift = -min(p.z for p in allv)
for o in list(P.values()) + [a[0] for a in A.values()]:
    # el importador deja las piezas giradas: se "aplica" la transformacion y luego se sube
    o.data.transform(Matrix.Translation((0, 0, lift)) @ o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    o.data.update()
print("subida:", round(lift, 3))

# ---------------- materiales: alpha + menos brillo ----------------
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    tx = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
    if bs:
        bs.inputs["Roughness"].default_value = 0.65
        bs.inputs["Specular IOR Level"].default_value = 0.2
        if tx and not bs.inputs["Alpha"].is_linked:
            nt.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
    m.surface_render_method = 'DITHERED'
    m.use_backface_culling = False


# ---------------- articulaciones a partir de la geometria ----------------
def verts(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]


def cap(o, top=True, eps=0.06):
    vs = verts(o)
    zt = max(v.z for v in vs) if top else min(v.z for v in vs)
    sel = [v for v in vs if abs(v.z - zt) < eps]
    return sum(sel, Vector()) / len(sel)


def mid(a, b):
    return (a + b) / 2


J = {}
for s in ("Right", "Left"):
    ua, la, ha = P[s + "UpperArm"], P[s + "LowerArm"], P[s + "Hand"]
    ul, ll, ft = P[s + "UpperLeg"], P[s + "LowerLeg"], P[s + "Foot"]
    J[s + "Shoulder"] = cap(ua, True) - Vector((0, 0, 0.18))
    J[s + "Elbow"] = mid(cap(ua, False), cap(la, True))
    J[s + "Wrist"] = mid(cap(la, False), cap(ha, True))
    J[s + "HandEnd"] = cap(ha, False)
    J[s + "Hip"] = cap(ul, True) - Vector((0, 0, 0.12))
    J[s + "Knee"] = mid(cap(ul, False), cap(ll, True))
    J[s + "Ankle"] = mid(cap(ll, False), cap(ft, True))
    fv = verts(ft)
    J[s + "Toe"] = Vector((J[s + "Ankle"].x, min(v.y for v in fv) + 0.05, J[s + "Ankle"].z * 0.5))
J["Waist"] = mid(cap(P["LowerTorso"], True), cap(P["UpperTorso"], False))
J["Pelvis"] = Vector((0, 0, cap(P["LowerTorso"], False).z))
J["Neck"] = mid(cap(P["UpperTorso"], True), cap(P["Head"], False))
J["HeadTop"] = cap(P["Head"], True)
for k in ("Waist", "Pelvis", "Neck", "HeadTop"):
    J[k].x = 0.0
for k, v in J.items():
    print("  %-14s (%6.2f, %6.2f, %6.2f)" % (k, v.x, v.y, v.z))

# ---------------- armadura ----------------
COL = bpy.data.collections.new("CRISTA"); sc.collection.children.link(COL)
WCOL = bpy.data.collections.new("CRISTA_Widgets"); sc.collection.children.link(WCOL)
arm_d = bpy.data.armatures.new("Crista_Rig")
rig = bpy.data.objects.new("Crista_Rig", arm_d)
COL.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_d.edit_bones


def bone(name, head, tail, parent=None, connect=False, roll=0.0, deform=False):
    b = eb.new(name); b.head = head; b.tail = tail; b.roll = roll
    if parent:
        b.parent = eb[parent]; b.use_connect = connect
    b.use_deform = deform
    return b


up = Vector((0, 0, 1))
bone("Root", (0, 0, 0), (0, 1.6, 0))
bone("HumanoidRootPart", J["Pelvis"], J["Pelvis"] + Vector((0, 0.9, 0)), "Root")
bone("LowerTorso", J["Pelvis"], J["Waist"], "HumanoidRootPart")
bone("UpperTorso", J["Waist"], J["Neck"], "LowerTorso", True)
bone("Head", J["Neck"], J["HeadTop"], "UpperTorso", True)
for s, sx in (("Right", -1), ("Left", 1)):
    bone(s + "UpperArm", J[s + "Shoulder"], J[s + "Elbow"], "UpperTorso")
    bone(s + "LowerArm", J[s + "Elbow"], J[s + "Wrist"], s + "UpperArm", True)
    bone(s + "Hand", J[s + "Wrist"], J[s + "HandEnd"], s + "LowerArm", True)
    bone(s + "UpperLeg", J[s + "Hip"], J[s + "Knee"], "LowerTorso")
    bone(s + "LowerLeg", J[s + "Knee"], J[s + "Ankle"], s + "UpperLeg", True)
    bone(s + "Foot", J[s + "Ankle"], J[s + "Toe"], s + "LowerLeg", True)
# orientar los huesos: X = giro adelante/atras, Z = giro hacia el lado (igual que el rig de Sikelpa)
for n in ("LowerTorso", "UpperTorso", "Head") + tuple(s + p for s in ("Right", "Left") for p in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg")):
    eb[n].align_roll(Vector((0, -1, 0)))
for s in ("Right", "Left"):
    eb[s + "Foot"].align_roll(Vector((0, 0, 1)))
for s, sx in (("Right", -1), ("Left", 1)):
    side = ".R" if s == "Right" else ".L"
    # controles IK: misma forma que mano/pie para que la rotacion coincida
    f = eb[s + "Foot"]
    bone("IK_Pie" + side, f.head.copy(), f.tail.copy(), "Root", roll=f.roll)
    bone("Polo_Rodilla" + side, J[s + "Knee"] + Vector((0, -3.0, 0)), J[s + "Knee"] + Vector((0, -3.4, 0)), "Root")
    h = eb[s + "Hand"]
    bone("IK_Mano" + side, h.head.copy(), h.tail.copy(), "Root", roll=h.roll)
    bone("Polo_Codo" + side, J[s + "Elbow"] + Vector((0, 3.0, 0)), J[s + "Elbow"] + Vector((0, 3.4, 0)), "UpperTorso")
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------- propiedades IK y constraints ----------------
rig["IK_Piernas"] = 1.0
rig["IK_Brazos"] = 0.0
for k, d in (("IK_Piernas", "1 = piernas con IK (pies fijos al piso), 0 = FK"), ("IK_Brazos", "1 = brazos con IK, 0 = FK")):
    rig.id_properties_ui(k).update(min=0.0, max=1.0, description=d)
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = 'XYZ'


def drive(con, prop):
    fc = con.driver_add("influence")
    while len(fc.keyframe_points):
        fc.keyframe_points.remove(fc.keyframe_points[0])
    d = fc.driver; d.type = 'AVERAGE'
    v = d.variables.new(); v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'; v.targets[0].id = rig; v.targets[0].data_path = '["%s"]' % prop


def rest_error(names):
    bpy.context.view_layer.update()
    err = 0.0
    for n in names:
        b = pb[n]
        err += (rig.matrix_world @ b.tail - rig.matrix_world @ b.bone.tail_local).length
        err += (b.matrix.to_3x3() - b.bone.matrix_local.to_3x3()).to_quaternion().angle if False else 0
        ax_rest = b.bone.matrix_local.to_3x3() @ Vector((1, 0, 0))
        ax_now = b.matrix.to_3x3() @ Vector((1, 0, 0))
        err += (ax_rest - ax_now).length
    return err


for s in ("Right", "Left"):
    side = ".R" if s == "Right" else ".L"
    for lower, upper, tgt, pole, end, prop in ((s + "LowerLeg", s + "UpperLeg", "IK_Pie" + side, "Polo_Rodilla" + side, s + "Foot", "IK_Piernas"),
                                               (s + "LowerArm", s + "UpperArm", "IK_Mano" + side, "Polo_Codo" + side, s + "Hand", "IK_Brazos")):
        c = pb[lower].constraints.new('IK'); c.name = "IK"
        c.target = rig; c.subtarget = tgt; c.pole_target = rig; c.pole_subtarget = pole; c.chain_count = 2
        best = None
        for ang in range(-180, 180, 5):          # elegir el angulo de polo que no tuerce el miembro en reposo
            c.pole_angle = math.radians(ang)
            e = rest_error([upper, lower])
            if best is None or e < best[0]:
                best = (e, ang)
        c.pole_angle = math.radians(best[1])
        drive(c, prop)
        cr = pb[end].constraints.new('COPY_ROTATION'); cr.name = "Rotacion_IK"
        cr.target = rig; cr.subtarget = tgt
        drive(cr, prop)
        print("  IK", lower, "polo", best[1], "error", round(best[0], 4))
for d_ in rig.animation_data.drivers:
    d_.driver.expression = d_.driver.expression
    d_.update()

# ---------------- widgets y colores ----------------
def wgt_circle(name, r=1.0, seg=32):
    me = bpy.data.meshes.new(name)
    vs = [(r * math.cos(2 * math.pi * i / seg), 0, r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    me.from_pydata(vs, [(i, (i + 1) % seg) for i in range(seg)], [])
    o = bpy.data.objects.new(name, me); WCOL.objects.link(o); return o


def wgt_box(name):
    me = bpy.data.meshes.new(name)
    v = [(x, y, z) for x in (-0.5, 0.5) for y in (0, 1) for z in (-0.5, 0.5)]
    e = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    me.from_pydata(v, e, [])
    o = bpy.data.objects.new(name, me); WCOL.objects.link(o); return o


W_CIRC = wgt_circle("WGT_Circulo")
W_ROOT = wgt_circle("WGT_Root")
W_BOX = wgt_box("WGT_Caja")
W_ROOT.rotation_euler = (math.radians(90), 0, 0)
pb["Root"].custom_shape = W_CIRC; pb["Root"].custom_shape_scale_xyz = (1.6, 1.6, 1.6); pb["Root"].custom_shape_rotation_euler = (math.radians(90), 0, 0)
pb["HumanoidRootPart"].custom_shape = W_CIRC; pb["HumanoidRootPart"].custom_shape_scale_xyz = (0.9, 0.9, 0.9)
pb["HumanoidRootPart"].custom_shape_rotation_euler = (math.radians(90), 0, 0)
for n in ("UpperTorso", "LowerTorso", "Head"):
    pb[n].custom_shape = W_CIRC; pb[n].custom_shape_scale_xyz = (0.75, 0.75, 0.75)
    pb[n].custom_shape_rotation_euler = (math.radians(90), 0, 0)
for s in ("Right", "Left"):
    for n in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot"):
        b = pb[s + n]; b.custom_shape = W_CIRC; b.custom_shape_scale_xyz = (0.45, 0.45, 0.45)
        b.custom_shape_rotation_euler = (math.radians(90), 0, 0)
    side = ".R" if s == "Right" else ".L"
    for n in ("IK_Pie", "IK_Mano"):
        b = pb[n + side]; b.custom_shape = W_BOX; b.custom_shape_scale_xyz = (1.2, 1.0, 1.2)
    for n in ("Polo_Rodilla", "Polo_Codo"):
        b = pb[n + side]; b.custom_shape = W_CIRC; b.custom_shape_scale_xyz = (0.5, 0.5, 0.5)
pal = {"Right": 'THEME01', "Left": 'THEME04'}
for b in pb:
    s = "Right" if (b.name.startswith("Right") or b.name.endswith(".R")) else "Left" if (b.name.startswith("Left") or b.name.endswith(".L")) else None
    b.color.palette = pal[s] if s else 'THEME09'
    if b.name.startswith(("IK_", "Polo_")):
        b.color.palette = 'THEME03'
for b in pb:
    b.bone.color.palette = b.color.palette
# colecciones de huesos
c_fk = arm_d.collections.new("Cuerpo (FK)"); c_ik = arm_d.collections.new("Controles IK"); c_root = arm_d.collections.new("Root")
for b in arm_d.bones:
    (c_ik if b.name.startswith(("IK_", "Polo_")) else c_root if b.name == "Root" else c_fk).assign(b)
arm_d.display_type = 'OCTAHEDRAL'
rig.show_in_front = True

# ---------------- pegar piezas y accesorios a los huesos ----------------
bpy.context.view_layer.update()


def attach(o, bname):
    mw = o.matrix_world.copy()
    for c in list(o.users_collection):
        c.objects.unlink(o)
    COL.objects.link(o)
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bname
    bpy.context.view_layer.update()
    o.matrix_world = mw


for n, o in P.items():
    attach(o, n)
for n, (o, bname) in A.items():
    attach(o, bname)
for c in list(bpy.data.collections):
    if c not in (COL, WCOL) and len(c.objects) == 0 and c.name != "CRISTA":
        pass
bpy.context.view_layer.layer_collection.children["CRISTA_Widgets"].exclude = True

# ---------------- renders de prueba ----------------
if not sc.world:
    sc.world = bpy.data.worlds.new("Cielo")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.68, 0.76, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sol", bpy.data.lights.new("Sol", 'SUN')); sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(25)); sc.collection.objects.link(sun)
floor_me = bpy.data.meshes.new("Piso"); floor_me.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("Piso_Preview", floor_me); sc.collection.objects.link(floor)
fm = bpy.data.materials.new("Piso_Preview"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.38, 0.42, 1); floor_me.materials.append(fm)
sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 600, 800
H = J["HeadTop"].z


def shot(name, loc, target, ortho=None, lens=50):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cam = bpy.data.objects.new(name, cd); sc.collection.objects.link(cam)
    cam.location = loc; cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(PREV, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


tgt = (0, 0, H / 2)
shot("frente", (0, -30, H / 2), tgt, ortho=H * 1.25)
shot("lado", (30, 0, H / 2), tgt, ortho=H * 1.25)
shot("espalda", (0, 30, H / 2), tgt, ortho=H * 1.25)
# pose de prueba: saluda con la mano derecha, brazo izq. al frente, se agacha (IK piernas), cabeza ladeada
pb["RightUpperArm"].rotation_euler = (math.radians(0), 0, math.radians(-150))
pb["RightLowerArm"].rotation_euler = (math.radians(30), 0, 0)
pb["LeftUpperArm"].rotation_euler = (math.radians(70), 0, math.radians(10))
pb["LeftLowerArm"].rotation_euler = (math.radians(45), 0, 0)
pb["HumanoidRootPart"].location = (0, 0, -0.28)   # bajar la cadera: las rodillas se doblan solas (IK)
pb["Head"].rotation_euler = (math.radians(8), math.radians(-12), math.radians(10))
pb["IK_Pie.L"].location = (0, 0, 0)
bpy.context.view_layer.update()
shot("pose_prueba", (4.2, -7.8, H * 0.65), (0, 0, H * 0.5), lens=38)
for b in pb:
    b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0); b.rotation_quaternion = (1, 0, 0, 0); b.scale = (1, 1, 1)
for o in (sun, floor):
    bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("CRISTA OK ->", OUT_BLEND)
