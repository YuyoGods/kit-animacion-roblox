# Agrega postes de luz a la calle del pueblo (se puede volver a ejecutar: borra y recrea)
import bpy, bmesh, math
from mathutils import Vector

sc = bpy.context.scene
ROAD_HW = 8.0
SPACING = 26.0
N = 10
POLE_X = ROAD_HW + 0.9      # poste sobre la acera, junto al bordillo
ARM = 2.6                   # brazo hacia la carretera
H = 13.2                    # altura del poste
LAMP_W = 4200               # potencia de cada foco


def lin(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


# ---------- limpiar version anterior ----------
for cname in ("Faroles", "Farol_Base"):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)

# ---------- materiales ----------
def mat_metal():
    m = bpy.data.materials.get("Farol_Metal") or bpy.data.materials.new("Farol_Metal")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin("#24272C"); mx.inputs["B"].default_value = lin("#353A41")
    nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.55
    b.inputs["Roughness"].default_value = 0.55
    return m


def mat_bulb():
    m = bpy.data.materials.get("Farol_Bombilla") or bpy.data.materials.new("Farol_Bombilla")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.name = "BSDF"
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = lin("#FFE7C2")
    b.inputs["Emission Color"].default_value = lin("#FFBD6B")
    b.inputs["Emission Strength"].default_value = 9.0
    b.inputs["Roughness"].default_value = 0.3
    return m


MET, BULB = mat_metal(), mat_bulb()


# ---------- geometria ----------
def add(col, name, bm_fn, loc, m, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bm_fn(bm); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    me.materials.append(m)
    col.objects.link(o)
    return o


def cyl(r1, r2, d, seg=20):
    return lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=d)


def cube(sx, sy, sz):
    def f(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    return f


def sphere(r, squash=1.0):
    def f(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=r)
        for v in bm.verts:
            v.co.z *= squash
    return f


# Farol modelo: poste en el origen, brazo hacia -X (hacia la carretera si esta en el lado derecho)
BASE = bpy.data.collections.new("Farol_Base")
sc.collection.children.link(BASE)
add(BASE, "Farol_Pie", cyl(0.65, 0.5, 1.0), (0, 0, 0.5), MET)
add(BASE, "Farol_Anillo", cyl(0.42, 0.42, 0.25), (0, 0, 1.1), MET)
add(BASE, "Farol_Poste", cyl(0.24, 0.17, H - 1.0), (0, 0, 1.0 + (H - 1.0) / 2), MET)
add(BASE, "Farol_Remate", sphere(0.3), (0, 0, H + 0.1), MET)
add(BASE, "Farol_Brazo", cube(ARM + 0.3, 0.22, 0.22), (-(ARM / 2), 0, H - 0.4), MET)
add(BASE, "Farol_Refuerzo", cube(1.6, 0.14, 0.14), (-0.6, 0, H - 1.05), MET, rot=(0, 35, 0))
add(BASE, "Farol_Cabeza", cyl(0.95, 0.35, 0.7, 24), (-ARM, 0, H - 0.75), MET)
bulb = add(BASE, "Farol_Bombilla", sphere(0.55, 0.55), (-ARM, 0, H - 1.15), BULB)
bulb.visible_shadow = False
bpy.context.view_layer.layer_collection.children["Farol_Base"].exclude = True

# ---------- copias + focos ----------
FAR = bpy.data.collections.new("Faroles")
sc.collection.children.link(FAR)
spot = bpy.data.lights.get("Farol_Luz") or bpy.data.lights.new("Farol_Luz", 'SPOT')
spot.energy = LAMP_W
spot.color = lin("#FFBD6B")[:3]
spot.spot_size = math.radians(118)
spot.spot_blend = 0.45
spot.shadow_soft_size = 0.35
count = 0
for side in (-1, 1):
    for k in range(-1, N, 2):   # una fila si, una no
        y = SPACING / 2 + k * SPACING
        e = bpy.data.objects.new("Farol_%s_%02d" % ("Izq" if side < 0 else "Der", k + 2), None)
        e.instance_type = 'COLLECTION'
        e.instance_collection = BASE
        e.location = (side * POLE_X, y, 0.3)          # 0.3 = altura de la acera
        e.rotation_euler = (0, 0, 0 if side > 0 else math.pi)
        FAR.objects.link(e)
        L = bpy.data.objects.new("Luz_" + e.name, spot)   # todas comparten el mismo foco (editar uno = editar todos)
        L.location = (side * (POLE_X - ARM), y, 0.3 + H - 1.75)
        FAR.objects.link(L)
        count += 1
print("faroles:", count)
