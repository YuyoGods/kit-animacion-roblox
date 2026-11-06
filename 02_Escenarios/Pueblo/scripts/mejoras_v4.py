# Mejoras v4: carrito de nieves, calle norte alargada, terreno exterior, estanque, colinas y mas vegetacion.
# Ejecutar despues de mejoras_v3.py. Se puede repetir.
import bpy, bmesh, math, random
from mathutils import Vector

random.seed(41)
sc = bpy.context.scene
FONT = r"C:\Windows\Fonts\ariblk.ttf"
PC = Vector((0, 380))
ZP = 0.36
ROAD_Y = 420.0          # eje de la calle norte de la glorieta
ROAD_HW, WALK = 8.0, 5.0
ROAD_END = 300.0        # hasta donde llega la calle alargada (cada lado)
POND = Vector((-205, 150))
POND_R = 36.0


def lin(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (o[0], o[1], o[2], 1.0)


def coll(name, parent=None, exclude=False):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o)
    else:
        c = bpy.data.collections.new(name)
        (parent or sc.collection).children.link(c)
    if exclude:
        def find(l):
            if l.collection == c:
                return l
            for ch in l.children:
                r = find(ch)
                if r:
                    return r
        lc = find(bpy.context.view_layer.layer_collection)
        if lc:
            lc.exclude = True
    return c


# ---------------- materiales ----------------
def base_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.name = "BSDF"
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m, nt, b


def mk_noise(name, hexc, rough=0.85, scale=6, amount=0.12, metal=0.0, bump_s=0.1, coords="Object"):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs[coords], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 1 - amount
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1.0; mx.inputs["A"].default_value = lin(hexc)
    nt.links.new(mr.outputs["Result"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if bump_s:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump_s
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mk_two_tone(name, a, b_, scale, rough=0.95, bump_s=0.2):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin(a); mx.inputs["B"].default_value = lin(b_)
    nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump_s
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mk_stripes(name, hex_a, hex_b, scale=1.0, axis=0):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'
    nt.links.new(sx.outputs[1], at.inputs[0]); nt.links.new(sx.outputs[0], at.inputs[1])
    ml = nt.nodes.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = scale
    nt.links.new(at.outputs[0], ml.inputs[0])
    sn = nt.nodes.new("ShaderNodeMath"); sn.operation = 'SINE'; nt.links.new(ml.outputs[0], sn.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.0
    nt.links.new(sn.outputs[0], gt.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin(hex_a); mx.inputs["B"].default_value = lin(hex_b)
    nt.links.new(gt.outputs[0], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    m.use_backface_culling = False
    return m


def mk_pond_water():
    m, nt, b = base_mat("Agua_Estanque")
    b.inputs["Base Color"].default_value = lin("#1F5E6B")
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Specular IOR Level"].default_value = 0.5
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M = {
    "asfalto": bpy.data.materials["Asfalto"], "acera": bpy.data.materials["Acera"],
    "linea": bpy.data.materials["Linea_Amarilla"], "blanco": bpy.data.materials["Casa_Borde"],
    "metal": bpy.data.materials["Farol_Metal"], "madera": bpy.data.materials["Madera"],
    "hojas": bpy.data.materials["Hojas"],
    "pasto_ext": mk_two_tone("Pasto_Exterior", "#356E25", "#47852D", 0.08),
    "colina": mk_two_tone("Pasto_Colina", "#3E7A2A", "#5A9638", 0.03, bump_s=0.35),
    "arena": mk_noise("Orilla_Arena", "#B9A57A", 0.95, 1.5, 0.25, bump_s=0.4),
    "lodo": mk_noise("Orilla_Lodo", "#5B4A33", 0.95, 2.0, 0.3, bump_s=0.4),
    "agua": mk_pond_water(),
    "roca": mk_noise("Roca", "#7E7A73", 0.9, 3.0, 0.35, bump_s=0.8),
    "junco": mk_noise("Junco", "#5E8A2E", 0.8, 6, 0.3),
    "nenufar": mk_noise("Nenufar", "#3E8C3A", 0.6, 4, 0.2),
    "flor_agua": mk_noise("Flor_Nenufar", "#F6B6D0", 0.5, 4, 0.1),
    "copa1": mk_two_tone("Arbol_Copa", "#3F8A2E", "#5BA83B", 0.9, bump_s=0.6),
    "copa2": mk_two_tone("Arbol_Copa_Oscura", "#2F6E2A", "#468A33", 0.9, bump_s=0.6),
    "tronco": mk_noise("Arbol_Tronco", "#5A3D27", 0.95, 10, 0.3, bump_s=0.6),
    "carrito": mk_noise("Carrito_Blanco", "#F7F4EC", 0.5, 4, 0.05),
    "carrito_rosa": mk_noise("Carrito_Rosa", "#EF7FA9", 0.5, 4, 0.05),
    "llanta": mk_noise("Llanta", "#202022", 0.8, 6, 0.1),
    "nieve_r": mk_noise("Nieve_Fresa", "#F5A3BE", 0.6, 8, 0.1),
    "nieve_c": mk_noise("Nieve_Chocolate", "#6B4127", 0.6, 8, 0.1),
    "nieve_v": mk_noise("Nieve_Limon", "#B9E07A", 0.6, 8, 0.1),
    "sombrilla": mk_stripes("Sombrilla_Rayas", "#F7F4EC", "#EF7FA9", 8.0),
    "letra": mk_noise("Carrito_Letra", "#C2185B", 0.5, 4, 0.05),
}


# ---------------- geometria ----------------
def obj(name, col, me, loc, m, rot=(0, 0, 0), smooth=False, parent=None):
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    if m:
        me.materials.append(m)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def box(name, col, loc, size, m, rot=(0, 0, 0), parent=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot, parent=parent)


def cone(name, col, loc, r1, r2, depth, m, rot=(0, 0, 0), seg=24, parent=None, smooth=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot, smooth, parent)


def cyl(name, col, loc, r, depth, m, rot=(0, 0, 0), seg=24, parent=None):
    return cone(name, col, loc, r, r, depth, m, rot, seg, parent)


def ball(name, col, loc, r, m, squash=1.0, parent=None, sub=2):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co.z *= squash
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, smooth=True, parent=parent)


def blob(name, col, center, z, radius_fn, m, seg=96):
    """disco irregular (para agua y orillas)"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    c = bm.verts.new((0, 0, 0))
    ring = [bm.verts.new((math.cos(2 * math.pi * i / seg) * radius_fn(2 * math.pi * i / seg),
                          math.sin(2 * math.pi * i / seg) * radius_fn(2 * math.pi * i / seg), 0)) for i in range(seg)]
    for i in range(seg):
        bm.faces.new((c, ring[i], ring[(i + 1) % seg]))
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, (center.x, center.y, z), m)


def inst(name, col, src, loc, rz=0.0, s=1.0, sz=None):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = src
    e.location = loc; e.rotation_euler = (0, 0, rz); e.scale = (s, s, sz or s); col.objects.link(e); return e


ROOT = bpy.data.collections["Centro"]
AF = coll("Afueras")
MOD = coll("Afueras_Modelos", exclude=False)

# =============== 1) BANCAS: solo quedan las 4 de la fuente ===============
for o in list(bpy.data.objects):
    if o.name.startswith("Banca_Borde_"):
        bpy.data.objects.remove(o)

# =============== 2) CARRITO DE NIEVES ===============
CAR = coll("Carrito_Nieves", ROOT)
root = bpy.data.objects.new("Carrito_Nieves", None); root.empty_display_size = 2
root.location = (PC.x - 8.5, PC.y - 21.5, ZP); root.rotation_euler = (0, 0, math.radians(8)); CAR.objects.link(root)
R = root
box("Carrito_Caja", CAR, (0, 0, 2.05), (4.2, 2.2, 2.1), M["carrito"], parent=R, bevel=0.12)
box("Carrito_Franja", CAR, (0, 0, 2.55), (4.26, 2.26, 0.45), M["carrito_rosa"], parent=R)
box("Carrito_Tapa", CAR, (0, 0, 3.15), (4.3, 2.3, 0.14), M["carrito_rosa"], parent=R)
for k, mm in enumerate((M["nieve_r"], M["nieve_c"], M["nieve_v"])):
    cyl("Carrito_Bote", CAR, (-1.3 + k * 1.3, 0, 3.4), 0.48, 0.4, M["metal"], parent=R)
    ball("Carrito_Nieve", CAR, (-1.3 + k * 1.3, 0, 3.6), 0.42, mm, 0.6, parent=R)
for s in (-1, 1):
    cyl("Carrito_Rueda", CAR, (-0.9, s * 1.2, 0.85), 0.85, 0.25, M["llanta"], rot=(90, 0, 0), parent=R)
    cyl("Carrito_Rin", CAR, (-0.9, s * 1.34, 0.85), 0.35, 0.06, M["metal"], rot=(90, 0, 0), parent=R)
    box("Carrito_Brazo", CAR, (2.55, s * 0.8, 2.6), (1.1, 0.12, 0.12), M["metal"], parent=R)
box("Carrito_Pata", CAR, (1.6, 0, 0.5), (0.25, 1.6, 1.0), M["metal"], parent=R)
cyl("Carrito_Manubrio", CAR, (3.1, 0, 2.6), 0.08, 1.8, M["metal"], rot=(90, 0, 0), parent=R)
cyl("Carrito_Poste", CAR, (0, 0, 5.2), 0.08, 4.0, M["metal"], parent=R)
cone("Carrito_Sombrilla", CAR, (0, 0, 7.3), 3.1, 0.12, 1.1, M["sombrilla"], seg=32, parent=R)
cu = bpy.data.curves.new("Carrito_Letrero", 'FONT'); cu.body = "NIEVES"
cu.font = bpy.data.fonts.load(FONT, check_existing=True); cu.size = 0.5; cu.extrude = 0.03
cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.materials.append(M["letra"])
t = bpy.data.objects.new("Carrito_Letrero", cu); t.location = (0.75, -1.12, 1.75); t.rotation_euler = (math.radians(90), 0, 0)
CAR.objects.link(t); t.parent = R

# =============== 3) CALLE NORTE ALARGADA ===============
CALLE = coll("Calle_Norte", ROOT)
# las tiendas de arriba se recorren para dejar pasar la calle
for n, y in (("Tienda_Panaderia", 354), ("Tienda_Abarrotes", 354), ("Tienda_Barberia", 391), ("Tienda_Cafeteria", 391)):
    o = bpy.data.objects.get(n)
    if o:
        o.location.y = y
# la acera lateral de la glorieta se corta donde cruza la calle
for o in list(bpy.data.objects):
    if o.name.startswith("Acera_Ext_Lado"):
        bpy.data.objects.remove(o)
for sx_ in (-1, 1):
    box("Acera_Ext_Lado", CALLE, (sx_ * 50.5, (327 + ROAD_Y - ROAD_HW) / 2, 0.15), (WALK, ROAD_Y - ROAD_HW - 327, 0.3), M["acera"])
for sx_ in (-1, 1):
    x0, x1 = 48.0, ROAD_END
    cxm = sx_ * (x0 + x1) / 2
    box("CalleNorte", CALLE, (cxm, ROAD_Y, 0.02), (x1 - x0, ROAD_HW * 2, 0.1), M["asfalto"])
    box("CalleNorte_AceraSur", CALLE, (sx_ * (53 + x1) / 2, ROAD_Y - ROAD_HW - WALK / 2, 0.15), (x1 - 53, WALK, 0.3), M["acera"])
    box("CalleNorte_AceraNorte", CALLE, (sx_ * (48 + x1) / 2, ROAD_Y + ROAD_HW + WALK / 2, 0.15), (x1 - 48, WALK, 0.3), M["acera"])
    x = 52.0
    while x + 4 < x1 - 2:
        box("CalleNorte_Linea", CALLE, (sx_ * (x + 2), ROAD_Y, 0.08), (4.0, 0.35, 0.03), M["linea"])
        x += 8.0
# farolas a lo largo de la calle nueva (una cada 52)
far = bpy.data.collections.get("Farol_Base"); spot_d = bpy.data.lights.get("Farol_Luz")
if far and spot_d:
    for sx_ in (-1, 1):
        for k, x in enumerate(range(90, int(ROAD_END), 52)):
            for side in (-1, 1):
                y = ROAD_Y + side * (ROAD_HW + 0.9)
                rz = -math.pi / 2 if side < 0 else math.pi / 2
                inst("FarolNorte_%s%d%s" % ("O" if sx_ < 0 else "E", k, "S" if side < 0 else "N"), CALLE, far, (sx_ * x, y, 0.3), rz)
                L = bpy.data.objects.new("Luz_FarolNorte_%s%d%s" % ("O" if sx_ < 0 else "E", k, "S" if side < 0 else "N"), spot_d)
                L.location = (sx_ * x, y - side * 2.6, 0.3 + 13.2 - 1.75); CALLE.objects.link(L)
# quitar pinos que quedaron sobre la calle nueva
for o in list(bpy.data.objects):
    if o.name.startswith("Pino_") and o.instance_type == 'COLLECTION':
        if abs(o.location.y - ROAD_Y) < ROAD_HW + WALK + 4 and abs(o.location.x) > 44:
            bpy.data.objects.remove(o)

# =============== 4) TERRENO, ESTANQUE Y COLINAS ===============
box("Terreno_Exterior", AF, (0, 300, -0.13), (1400, 1500, 0.1), M["pasto_ext"])

HILLS = [(-470, 760, 95, 150), (-300, 700, 60, 120), (-120, 840, 120, 170), (60, 730, 70, 130),
         (240, 810, 105, 160), (420, 720, 75, 140), (600, 860, 90, 170), (-640, 880, 80, 160)]
HILL_Y0 = 560.0


def hill_z(x, y):
    z = 0.0
    for hx, hy, hh, hr in HILLS:
        d2 = ((x - hx) ** 2 + (y - hy) ** 2) / (hr * hr)
        z += hh * math.exp(-d2 * 1.6)
    z += 6 * math.sin(x * 0.013) * math.cos(y * 0.011)
    fade = max(0.0, min(1.0, (y - HILL_Y0) / 90.0))
    return z * (fade * fade * (3 - 2 * fade))


me = bpy.data.meshes.new("Colinas"); bm = bmesh.new()
NX, NY = 140, 60
X0, X1, Y1 = -700.0, 700.0, 1050.0
grid = [[bm.verts.new((X0 + (X1 - X0) * i / NX, HILL_Y0 + (Y1 - HILL_Y0) * j / NY, 0)) for j in range(NY + 1)] for i in range(NX + 1)]
for i in range(NX):
    for j in range(NY):
        bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
for v in bm.verts:
    v.co.z = hill_z(v.co.x, v.co.y) - 0.05
bm.to_mesh(me); bm.free()
obj("Colinas", AF, me, (0, 0, 0), M["colina"], smooth=True)

# estanque
def pond_r(a, k=1.0):
    return POND_R * k * (1 + 0.16 * math.sin(3 * a + 0.7) + 0.08 * math.cos(5 * a + 1.3))


blob("Estanque_Orilla", AF, POND, -0.06, lambda a: pond_r(a, 1.22), M["arena"])
blob("Estanque_Lodo", AF, POND, -0.045, lambda a: pond_r(a, 1.06), M["lodo"])
blob("Estanque_Agua", AF, POND, -0.03, lambda a: pond_r(a, 1.0), M["agua"])
for k in range(26):
    a = random.uniform(0, 2 * math.pi); rr = pond_r(a, random.uniform(1.04, 1.18))
    ball("Estanque_Roca", AF, (POND.x + math.cos(a) * rr, POND.y + math.sin(a) * rr, 0.2), random.uniform(0.8, 2.2), M["roca"], random.uniform(0.45, 0.7))
for k in range(9):            # grupos de juncos en la orilla
    a = random.uniform(0, 2 * math.pi); rr = pond_r(a, 0.98)
    for j in range(9):
        p = Vector((POND.x + math.cos(a) * rr + random.uniform(-1.6, 1.6), POND.y + math.sin(a) * rr + random.uniform(-1.6, 1.6)))
        hgt = random.uniform(2.5, 4.5)
        cone("Junco", AF, (p.x, p.y, hgt / 2), 0.09, 0.03, hgt, M["junco"], seg=6, rot=(random.uniform(-8, 8), random.uniform(-8, 8), 0))
for k in range(14):           # nenufares
    a = random.uniform(0, 2 * math.pi); rr = pond_r(a, random.uniform(0.3, 0.85))
    p = (POND.x + math.cos(a) * rr, POND.y + math.sin(a) * rr)
    cyl("Nenufar", AF, (p[0], p[1], 0.0), random.uniform(0.9, 1.5), 0.05, M["nenufar"], seg=16)
    if k % 3 == 0:
        ball("Nenufar_Flor", AF, (p[0] + 0.3, p[1], 0.18), 0.32, M["flor_agua"], 0.6)
# muelle de madera
dock_a = math.radians(20)
dx, dy = math.cos(dock_a), math.sin(dock_a)
for k in range(10):
    d = POND_R * 1.15 - k * 1.25
    box("Muelle_Tabla", AF, (POND.x + dx * d, POND.y + dy * d, 0.7), (1.1, 4.0, 0.22), M["madera"], rot=(0, 0, math.degrees(dock_a)))
for k in range(0, 10, 3):
    d = POND_R * 1.15 - k * 1.25
    for s in (-1, 1):
        cyl("Muelle_Poste", AF, (POND.x + dx * d - dy * s * 1.8, POND.y + dy * d + dx * s * 1.8, 0.3), 0.18, 1.6, M["madera"], seg=8)

# =============== 5) MAS VEGETACION ===============
# arbol redondo (modelo)
ARB = coll("Arbol_Modelo", MOD)
cone("Arbol_Tronco", ARB, (0, 0, 2.5), 0.55, 0.35, 5.0, M["tronco"], seg=10)
for (x, y, z, r, mm) in ((0, 0, 6.6, 3.0, "copa1"), (1.7, 0.6, 5.6, 2.1, "copa2"), (-1.6, -0.5, 5.8, 2.2, "copa1"),
                         (0.3, -1.6, 7.6, 1.9, "copa2"), (-0.4, 1.4, 8.0, 1.8, "copa1")):
    ball("Arbol_Copa", ARB, (x, y, z), r, M[mm], 0.9)
PINO = bpy.data.collections.get("Pino_Modelo")
VEG = coll("Vegetacion", AF)
# arboles redondos entre las casas de la calle (en el hueco entre casa y casa)
for side in (-1, 1):
    for k in range(10):
        y = 13 + 26 * k
        inst("ArbolCalle_%s%02d" % ("I" if side < 0 else "D", k + 1), VEG, ARB, (side * 31.5, y, 0), random.uniform(0, 6.28), random.uniform(0.85, 1.1))
# arbustos con flores en los jardines junto a la acera (uno cada 2 casas)
flores = [m for m in bpy.data.materials if m.name.startswith("Flor_")]
for side in (-1, 1):
    for k in range(0, 11, 2):
        y = k * 26 + random.uniform(-4, 4)
        cx = side * 16.5
        ball("ArbustoJardin", VEG, (cx, y + 6.5, 0.8), 1.3, M["hojas"], 0.75)
        for j in range(8):
            th = random.uniform(0, 6.28)
            ball("ArbustoJardin_Flor", VEG, (cx + math.cos(th) * 1.0, y + 6.5 + math.sin(th) * 1.0, 1.25 + random.uniform(0, 0.4)), 0.17, random.choice(flores))
# afueras: pinos y arboles redondos (sin tapar calles, estanque, pueblo ni colinas)


def free_spot(x, y):
    if abs(x) < 128 and y < 560:
        return False                      # el pueblo ya tiene sus pinos
    if abs(y - ROAD_Y) < 20:
        return False
    if (Vector((x, y)) - POND).length < POND_R * 1.45:
        return False
    if y > HILL_Y0 - 10:
        return False
    return True


pts = []
tries = 0
while len(pts) < 230 and tries < 40000:
    tries += 1
    x, y = random.uniform(-560, 560), random.uniform(-300, HILL_Y0)
    if not free_spot(x, y) or any((x - a) ** 2 + (y - b) ** 2 < 11 ** 2 for a, b in pts):
        continue
    pts.append((x, y))
for i, (x, y) in enumerate(pts):
    if PINO and random.random() < 0.65:
        s = random.uniform(1.1, 2.0)
        inst("PinoAfuera_%03d" % i, VEG, PINO, (x, y, 0), random.uniform(0, 6.28), s, s * random.uniform(0.95, 1.2))
    else:
        inst("ArbolAfuera_%03d" % i, VEG, ARB, (x, y, 0), random.uniform(0, 6.28), random.uniform(1.0, 1.6))
# pinos sobre las colinas (pocos, en las faldas)
k = 0
for _ in range(400):
    if k >= 70:
        break
    x, y = random.uniform(-650, 650), random.uniform(HILL_Y0 + 40, 950)
    z = hill_z(x, y)
    if 4 < z < 55:
        s = random.uniform(1.4, 2.2)
        inst("PinoColina_%03d" % k, VEG, PINO, (x, y, z - 0.6), random.uniform(0, 6.28), s, s)
        k += 1

for ch in ("Arbol_Modelo",):
    def find(l, n):
        if l.name == n:
            return l
        for c in l.children:
            r = find(c, n)
            if r:
                return r
    lc = find(bpy.context.view_layer.layer_collection, "Afueras_Modelos")
    if lc:
        lc.exclude = True

# camaras de prueba
CAMS = bpy.data.collections["Camaras_Centro"]


def cam(name, loc, target, fov):
    o = bpy.data.objects.get(name)
    if o is None:
        cd = bpy.data.cameras.new(name); cd.sensor_fit = 'VERTICAL'
        o = bpy.data.objects.new(name, cd); CAMS.objects.link(o)
    o.data.clip_end = 3000; o.data.angle_y = math.radians(fov); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


cam("Cam_PuebloGeneral", (260, -160, 230), (-20, 330, 0), 42)
cam("Cam_Estanque", (-165, 105, 14), (-210, 160, 0), 50)
cam("Cam_Carrito", (-4, 349, 5.5), (-8.5, 358.5, 3.5), 50)
cam("Cam_Colinas", (0, 300, 12), (0, 760, 60), 50)
print("v4 ok | arboles afuera:", len(pts), "| pinos colina:", k)
