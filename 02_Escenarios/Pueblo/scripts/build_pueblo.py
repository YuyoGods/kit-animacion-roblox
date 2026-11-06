# Pueblo - calle con 10 casas por lado
# Uso: blender -b --factory-startup --python build_pueblo.py
import bpy, bmesh, math, random, os
from mathutils import Vector

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # 02_Escenarios/Pueblo
RENDERS = os.path.join(OUT, "renders")
os.makedirs(RENDERS, exist_ok=True)
random.seed(11)

# ---------------- escena limpia ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Pueblo"


def lin(h):
    """hex sRGB -> RGBA lineal (sin esto Blender lo ve lavado)"""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


# ---------------- materiales ----------------
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.name = "BSDF"
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Specular IOR Level"].default_value = 0.25
    return m, nt, b


def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def color_source(nt, attr=None, fixed=None):
    """color por casa (propiedad del instanciador) o color fijo"""
    if attr:
        a = node(nt, "ShaderNodeAttribute", attribute_type='INSTANCER', attribute_name=attr)
        return a.outputs["Color"]
    rgb = node(nt, "ShaderNodeRGB")
    rgb.outputs[0].default_value = fixed
    return rgb.outputs[0]


def noisy(nt, col_socket, scale=6.0, amount=0.12, coords="Object"):
    """multiplica un color por ruido suave -> textura simple, no plastico"""
    tc = node(nt, "ShaderNodeTexCoord")
    nz = node(nt, "ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs[coords], nz.inputs["Vector"])
    mr = node(nt, "ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 1 - amount
    mr.inputs["To Max"].default_value = 1.0
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mul = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(col_socket, mul.inputs["A"])
    nt.links.new(mr.outputs["Result"], mul.inputs["B"])
    return mul.outputs["Result"], tc


def bump(nt, b, height_socket, strength=0.2, dist=0.05):
    bp = node(nt, "ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    nt.links.new(height_socket, bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])


def mat_simple(name, hexc, rough=0.85, noise_scale=6, amount=0.12, attr=None, emit=None, emit_strength=0.0):
    m, nt, b = new_mat(name)
    col = color_source(nt, attr, lin(hexc) if hexc else None)
    col, _ = noisy(nt, col, noise_scale, amount)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def mat_siding(name):
    """pared con tablillas horizontales (color por casa)"""
    m, nt, b = new_mat(name)
    col = color_source(nt, "wall_color")
    col, tc = noisy(nt, col, 3.0, 0.08)
    wv = node(nt, "ShaderNodeTexWave", wave_type='BANDS', bands_direction='Z', wave_profile='SAW')
    wv.inputs["Scale"].default_value = 0.9
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = node(nt, "ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.86
    mr.inputs["To Max"].default_value = 1.0
    nt.links.new(wv.outputs["Fac"], mr.inputs["Value"])
    mul = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY')
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(col, mul.inputs["A"]); nt.links.new(mr.outputs["Result"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], b.inputs["Base Color"])
    bump(nt, b, wv.outputs["Fac"], 0.25, 0.03)
    return m


def mat_bricks(name, attr=None, hexc=None, mortar="#3A3530", w=1.2, h=0.45, scale=1.0, dark=0.82, rough=0.9, vertical=False):
    """ladrillo/tejas/baldosas con Brick Texture (vertical=True para paredes)"""
    m, nt, b = new_mat(name)
    col = color_source(nt, attr, lin(hexc) if hexc else None)
    col, tc = noisy(nt, col, 5.0, 0.1)
    dk = node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY')
    dk.inputs["Factor"].default_value = 1.0
    dk.inputs["B"].default_value = (dark, dark, dark, 1)
    nt.links.new(col, dk.inputs["A"])
    br = node(nt, "ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = scale
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = 0.035
    br.inputs["Mortar"].default_value = lin(mortar)
    if vertical:
        # (x + y, z): hiladas horizontales en las 4 caras
        sx = node(nt, "ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sx.inputs[0])
        add = node(nt, "ShaderNodeMath", operation='ADD')
        nt.links.new(sx.outputs[0], add.inputs[0]); nt.links.new(sx.outputs[1], add.inputs[1])
        cb = node(nt, "ShaderNodeCombineXYZ")
        nt.links.new(add.outputs[0], cb.inputs[0]); nt.links.new(sx.outputs[2], cb.inputs[1])
        nt.links.new(cb.outputs[0], br.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(col, br.inputs["Color1"]); nt.links.new(dk.outputs["Result"], br.inputs["Color2"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    inv = node(nt, "ShaderNodeMath", operation='SUBTRACT')
    inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    bump(nt, b, inv.outputs[0], 0.35, 0.05)
    return m


def mat_two_tone(name, hex_a, hex_b, scale, rough=0.9, bump_s=0.15):
    """pasto / asfalto: mezcla de dos tonos con ruido"""
    m, nt, b = new_mat(name)
    tc = node(nt, "ShaderNodeTexCoord")
    nz = node(nt, "ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = node(nt, "ShaderNodeMix", data_type='RGBA')
    mx.inputs["A"].default_value = lin(hex_a); mx.inputs["B"].default_value = lin(hex_b)
    nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    bump(nt, b, nz.outputs["Fac"], bump_s, 0.05)
    return m


M = {
    "pared": mat_siding("Casa_Pared"),
    "techo": mat_bricks("Casa_Techo", attr="roof_color", w=1.1, h=0.55, dark=0.78),
    "borde": mat_simple("Casa_Borde", "#F4F0E6", 0.7, 8, 0.08),
    "puerta": mat_simple("Casa_Puerta", None, 0.6, 2, 0.15, attr="door_color"),
    "acento": mat_simple("Casa_Acento", None, 0.7, 3, 0.12, attr="accent_color"),
    "vidrio": mat_simple("Casa_Vidrio", "#2B3E57", 0.08, 2, 0.05, emit="#FCC773", emit_strength=0.0),
    "base": mat_bricks("Casa_Base", hexc="#8C877F", mortar="#55514B", w=2.0, h=0.7, dark=0.88, vertical=True),
    "chimenea": mat_bricks("Casa_Chimenea", hexc="#8A3B2C", mortar="#C9BFAF", w=0.8, h=0.3, dark=0.8, vertical=True),
    "manija": mat_simple("Casa_Manija", "#D4AF37", 0.3, 2, 0.05),
    "lampara": mat_simple("Casa_Lampara", "#FFE2A8", 0.4, 2, 0.02, emit="#FFBD6B", emit_strength=0.5),
    "piedra": mat_simple("Camino_Piedra", "#A69C8B", 0.9, 4, 0.25),
    "tierra": mat_simple("Tierra", "#4A3324", 0.95, 8, 0.25),
    "maceta": mat_simple("Maceta", "#B5603A", 0.8, 5, 0.15),
    "hojas": mat_two_tone("Hojas", "#2F6B28", "#4C8F35", 6.0, 0.8, 0.4),
    "madera": mat_simple("Madera", "#6B4A2B", 0.8, 4, 0.2),
    "buzon": mat_simple("Buzon", "#2B4C7E", 0.5, 3, 0.08),
    "pasto": mat_two_tone("Pasto", "#336B24", "#42802B", 0.35, 0.95, 0.2),
    "asfalto": mat_two_tone("Asfalto", "#212126", "#2E2E33", 3.0, 0.92, 0.1),
    "linea": mat_simple("Linea_Amarilla", "#FAC726", 0.7, 6, 0.15),
    "acera": mat_bricks("Acera", hexc="#B8B4AC", mortar="#7D7973", w=2.0, h=2.0, dark=0.93),
    "bordillo": mat_simple("Bordillo", "#9C9890", 0.9, 5, 0.12),
}
FLOWERS = [mat_simple("Flor_%s" % n, c, 0.6, 4, 0.1) for n, c in
           (("Roja", "#E2343B"), ("Rosa", "#F27BB0"), ("Amarilla", "#F7D038"), ("Morada", "#9B59D0"), ("Blanca", "#F5F5F0"))]


# ---------------- geometria ----------------
def box(name, col, center, size, m, rot=None, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.location = center
    if rot:
        o.rotation_euler = [math.radians(a) for a in rot]
    me.materials.append(m)
    col.objects.link(o)
    return o


def cyl(name, col, center, r, depth, m, rot=None, seg=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = center
    if rot:
        o.rotation_euler = [math.radians(a) for a in rot]
    me.materials.append(m)
    col.objects.link(o)
    return o


def ball(name, col, center, r, m, squash=1.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co.z *= squash
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = center
    me.materials.append(m)
    col.objects.link(o)
    return o


def prism(name, col, half_w, z0, z1, y0, y1, m):
    """triangulo del techo (frontón) a lo largo de Y"""
    me = bpy.data.meshes.new(name)
    v = [(-half_w, y0, z0), (half_w, y0, z0), (0, y0, z1), (-half_w, y1, z0), (half_w, y1, z0), (0, y1, z1)]
    f = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    me.from_pydata(v, [], f)
    o = bpy.data.objects.new(name, me)
    me.materials.append(m)
    col.objects.link(o)
    return o


# ================= CASA BASE (frente mirando a -Y) =================
CASA = bpy.data.collections.new("Casa_Base")
sc.collection.children.link(CASA)
W, D = 16.0, 14.0          # ancho (X) y fondo (Y)
F1, F2 = 9.0, 8.0          # altura piso 1 y piso 2
TOP = 1.0 + F1 + F2 - 1.0  # 17: altura de las paredes (con base de 1)
RIDGE = TOP + 7.0          # cumbrera
FY = -D / 2                # cara frontal

box("Base", CASA, (0, 0, 0.5), (W + 0.5, D + 0.5, 1.0), M["base"])
box("Paredes", CASA, (0, 0, 1 + (TOP - 1) / 2), (W, D, TOP - 1), M["pared"])
prism("Fronton", CASA, W / 2, TOP, RIDGE, FY, -FY, M["pared"])
box("Faja_Pisos", CASA, (0, 0, 9.0), (W + 0.4, D + 0.4, 0.45), M["borde"])
for sx in (-1, 1):
    for sy in (-1, 1):
        box("Esquinero", CASA, (sx * W / 2, sy * D / 2, 1 + (TOP - 1) / 2), (0.6, 0.6, TOP - 1), M["borde"])

# techo a dos aguas
over = 0.9
slope = math.atan((RIDGE - TOP) / (W / 2))
hw = W / 2 + over
length = hw / math.cos(slope)
for sx in (-1, 1):
    cx = sx * hw / 2
    cz = RIDGE - (hw / 2) * math.tan(slope) + 0.28
    box("Techo", CASA, (cx, 0, cz), (length + 0.1, D + 1.8, 0.5), M["techo"], rot=(0, sx * math.degrees(slope), 0))
box("Cumbrera", CASA, (0, 0, RIDGE + 0.55), (0.7, D + 1.9, 0.45), M["borde"])
box("Chimenea", CASA, (4.8, 3.0, RIDGE - 1.0), (1.8, 1.8, 6.0), M["chimenea"])
box("Chimenea_Tapa", CASA, (4.8, 3.0, RIDGE + 2.1), (2.2, 2.2, 0.35), M["borde"])


def window(cx, cz, w, h, shutters=False, flowerbox=False, tag="Ventana"):
    y = FY
    box(tag + "_Marco", CASA, (cx, y - 0.12, cz), (w + 0.55, 0.35, h + 0.55), M["borde"])
    box(tag + "_Vidrio", CASA, (cx, y - 0.25, cz), (w, 0.2, h), M["vidrio"])
    box(tag + "_ParteV", CASA, (cx, y - 0.38, cz), (0.16, 0.12, h), M["borde"])
    box(tag + "_ParteH", CASA, (cx, y - 0.38, cz), (w, 0.12, 0.16), M["borde"])
    box(tag + "_Repisa", CASA, (cx, y - 0.4, cz - h / 2 - 0.35), (w + 0.9, 0.9, 0.28), M["borde"])
    if shutters:
        for s in (-1, 1):
            box(tag + "_Contraventana", CASA, (cx + s * (w / 2 + 0.75), y - 0.15, cz), (0.85, 0.22, h + 0.3), M["acento"])
            for k in range(5):
                box(tag + "_Lama", CASA, (cx + s * (w / 2 + 0.75), y - 0.28, cz - h / 2 + 0.4 + k * (h - 0.5) / 4), (0.7, 0.08, 0.12), M["borde"])
    if flowerbox:
        zb = cz - h / 2 - 0.85
        box(tag + "_Jardinera", CASA, (cx, y - 0.75, zb), (w + 0.4, 0.8, 0.65), M["acento"])
        n = max(3, int(w / 0.55))
        for k in range(n):
            x = cx - w / 2 + 0.2 + k * (w - 0.4) / (n - 1)
            ball(tag + "_Hoja", CASA, (x, y - 0.75, zb + 0.45), 0.36, M["hojas"], 0.8)
            ball(tag + "_Flor", CASA, (x + random.uniform(-0.1, 0.1), y - 0.95, zb + 0.75), 0.2, random.choice(FLOWERS))


# planta baja: puerta + 2 ventanas con contraventanas
box("Puerta_Marco", CASA, (0, FY - 0.15, 1 + 3.9), (4.6, 0.4, 7.8), M["borde"])
box("Puerta", CASA, (0, FY - 0.3, 1 + 3.55), (3.7, 0.3, 7.1), M["puerta"])
for z in (2.9, 6.1):
    box("Puerta_Panel", CASA, (0, FY - 0.48, z), (2.7, 0.08, 2.4), M["puerta"], bevel=0.05)
ball("Manija", CASA, (1.3, FY - 0.55, 4.6), 0.22, M["manija"])
box("Lampara_Porche", CASA, (3.1, FY - 0.35, 7.0), (0.55, 0.45, 0.8), M["lampara"])
box("Escalon1", CASA, (0, FY - 0.9, 0.75), (5.2, 1.4, 0.5), M["base"])
box("Escalon2", CASA, (0, FY - 2.1, 0.25), (5.8, 1.2, 0.5), M["base"])
for sx in (-1, 1):
    window(sx * 4.9, 5.2, 3.0, 3.6, shutters=True, tag="VentanaPB")

# segundo piso: balcon central + 2 ventanas con jardinera
window(0, 13.2, 3.4, 4.6, tag="VentanaBalcon")
window(-5.4, 13.3, 2.6, 3.0, flowerbox=True, tag="VentanaP2")
window(5.4, 13.3, 2.6, 3.0, flowerbox=True, tag="VentanaP2")
BY0, BY1 = FY, FY - 3.4
box("Balcon_Piso", CASA, (0, (BY0 + BY1) / 2, 10.45), (8.4, 3.4, 0.4), M["borde"])
for sx in (-1, 1):
    box("Balcon_Mensula", CASA, (sx * 3.3, FY - 1.0, 9.6), (0.4, 2.0, 0.5), M["borde"], rot=(-30, 0, 0))
nposts = 11
for k in range(nposts):
    x = -4.0 + k * 8.0 / (nposts - 1)
    box("Balcon_Barrote", CASA, (x, BY1 + 0.15, 11.5), (0.16, 0.16, 1.7), M["borde"])
for k in range(4):
    for sx in (-1, 1):
        box("Balcon_BarroteLat", CASA, (sx * 4.0, BY1 + 0.15 + k * 0.85, 11.5), (0.16, 0.16, 1.7), M["borde"])
box("Balcon_Baranda", CASA, (0, BY1 + 0.15, 12.42), (8.3, 0.3, 0.22), M["borde"])
for sx in (-1, 1):
    box("Balcon_BarandaLat", CASA, (sx * 4.0, (BY0 + BY1) / 2, 12.42), (0.3, 3.4, 0.22), M["borde"])
# jardinera del balcon + flores
box("Balcon_Jardinera", CASA, (0, BY1 + 0.75, 11.05), (5.6, 0.8, 0.8), M["acento"])
for k in range(10):
    x = -2.55 + k * 0.567
    ball("Balcon_Hoja", CASA, (x, BY1 + 0.75, 11.6), 0.38, M["hojas"], 0.8)
    ball("Balcon_Flor", CASA, (x + random.uniform(-0.1, 0.1), BY1 + 0.6, 11.95), 0.22, random.choice(FLOWERS))
for sx in (-1, 1):
    cyl("Maceta", CASA, (sx * 3.35, FY - 1.3, 11.1), 0.5, 0.9, M["maceta"])
    ball("Planta", CASA, (sx * 3.35, FY - 1.3, 12.1), 0.85, M["hojas"], 1.15)

# ventana redonda en el frontón
cyl("Ojo_Marco", CASA, (0, FY - 0.12, 20.2), 1.15, 0.3, M["borde"], rot=(90, 0, 0), seg=32)
cyl("Ojo_Vidrio", CASA, (0, FY - 0.22, 20.2), 0.88, 0.25, M["vidrio"], rot=(90, 0, 0), seg=32)

# jardin delantero: camino, arbustos, buzon
for k in range(6):
    y = FY - 3.3 - k * 1.35
    box("Camino_Piedra", CASA, (random.uniform(-0.2, 0.2), y, 0.06), (2.8, 1.1, 0.14), M["piedra"],
        rot=(0, 0, random.uniform(-6, 6)), bevel=0.08)
for sx in (-1, 1):
    ball("Arbusto", CASA, (sx * 6.2, FY - 1.6, 0.9), 1.5, M["hojas"], 0.75)
    ball("Arbusto", CASA, (sx * 3.9, FY - 1.3, 0.7), 1.0, M["hojas"], 0.75)
    box("Cantero", CASA, (sx * 5.3, FY - 3.0, 0.2), (4.6, 1.2, 0.4), M["tierra"])
    for k in range(6):
        ball("Cantero_Flor", CASA, (sx * 5.3 - 1.9 + k * 0.76, FY - 3.0, 0.6), 0.25, random.choice(FLOWERS))
box("Buzon_Poste", CASA, (2.6, FY - 10.6, 1.4), (0.3, 0.3, 2.8), M["madera"])
box("Buzon", CASA, (2.6, FY - 10.6, 3.0), (0.9, 1.6, 0.9), M["buzon"], bevel=0.1)

# la casa base queda oculta: solo se ven sus copias
bpy.context.view_layer.layer_collection.children["Casa_Base"].exclude = True

# ================= CALLE =================
CALLE = bpy.data.collections.new("Calle")
sc.collection.children.link(CALLE)
N = 10
SPACING = 26.0
L0, L1 = -30.0, SPACING * (N - 1) + 30.0
LEN = L1 - L0
MID = (L0 + L1) / 2
ROAD_HW = 8.0
WALK = 5.0
HOUSE_X = ROAD_HW + WALK + 9.5 + D / 2   # centro de cada casa

box("Pasto", CALLE, (0, MID, -0.05), (240, LEN + 120, 0.1), M["pasto"])
box("Carretera", CALLE, (0, MID, 0.02), (ROAD_HW * 2, LEN, 0.1), M["asfalto"])
y = L0 + 2
while y < L1 - 2:
    box("Linea_Centro", CALLE, (0, y + 2, 0.08), (0.35, 4.0, 0.03), M["linea"])
    y += 8
for sx in (-1, 1):
    box("Acera", CALLE, (sx * (ROAD_HW + WALK / 2), MID, 0.15), (WALK, LEN, 0.3), M["acera"])
    box("Bordillo", CALLE, (sx * (ROAD_HW + 0.2), MID, 0.2), (0.4, LEN, 0.42), M["bordillo"])

PALETA = {
    "wall_color": ["#F2C6C2", "#BFD8E8", "#F5E3A1", "#C9E4C5", "#E3D2F0", "#F7D1A8", "#E6E1D8", "#B9D3C9", "#F4B6A1", "#CFE0F5"],
    "roof_color": ["#7A2E2E", "#3E4A5C", "#5B3A29", "#2F4F3A", "#4A3B5C", "#6E4B3A"],
    "door_color": ["#8B1E1E", "#1F3B73", "#2E5E3A", "#6B3E1F", "#3B3B3B", "#B8892C"],
    "accent_color": ["#3C6E8F", "#8F3C4A", "#4F7F45", "#7A5A9E", "#C27C2C", "#2F4858"],
}
CASAS = bpy.data.collections.new("Casas")
sc.collection.children.link(CASAS)
i = 0
for side in (-1, 1):
    for k in range(N):
        e = bpy.data.objects.new("Casa_%s_%02d" % ("Izq" if side < 0 else "Der", k + 1), None)
        e.instance_type = 'COLLECTION'
        e.instance_collection = CASA
        e.location = (side * HOUSE_X, k * SPACING + (0 if side < 0 else SPACING * 0.0), 0)
        e.rotation_euler = (0, 0, math.radians(90 if side < 0 else -90))
        for key, pal in PALETA.items():
            idx = (i * (3 if key == "wall_color" else 5 if key == "roof_color" else 7) + (1 if side > 0 else 0)) % len(pal)
            e[key] = lin(pal[idx])[:3]
        CASAS.objects.link(e)
        i += 1

# ================= LUZ Y RENDER =================
w = bpy.data.worlds.new("Cielo")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = lin("#A9CBEA")
bg.inputs[1].default_value = 0.9
sun_d = bpy.data.lights.new("Sol", 'SUN')
sun_d.energy = 3.2
sun_d.angle = math.radians(3)
sun_d.color = lin("#FFF2DD")[:3]
sun = bpy.data.objects.new("Sol", sun_d)
sun.rotation_euler = (math.radians(52), 0, math.radians(35))
sc.collection.objects.link(sun)

r = sc.render
r.engine = 'BLENDER_EEVEE'
r.fps = 30
r.use_motion_blur = False
ee = sc.eevee
for a, v in (("taa_render_samples", 32), ("use_raytracing", True), ("use_shadows", True), ("shadow_pool_size", '1024')):
    try:
        setattr(ee, a, v)
    except Exception as ex:
        print("skip", a, ex)
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0

CAMS = bpy.data.collections.new("Camaras")
sc.collection.children.link(CAMS)


def cam(name, loc, target, fov_deg):
    cd = bpy.data.cameras.new(name)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(fov_deg)
    cd.clip_end = 1000
    o = bpy.data.objects.new(name, cd)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    CAMS.objects.link(o)
    return o


c_aerea = cam("Cam_Aerea", (75, -55, 70), (0, 105, 0), 45)
c_calle = cam("Cam_Calle", (3.5, -18, 5.5), (0, 80, 5), 62)
c_casa = cam("Cam_Casa", (-2, 38, 7.5), (-HOUSE_X + D / 2, SPACING * 2, 11), 58)
sc.camera = c_calle

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "Pueblo.blend"))

# --- renders de prueba ---
r.image_settings.file_format = 'PNG'
for c, (rx, ry), fn in ((c_aerea, (1920, 1080), "aerea.png"), (c_calle, (1080, 1920), "calle.png"), (c_casa, (1080, 1920), "casa.png")):
    sc.camera = c
    r.resolution_x, r.resolution_y = rx, ry
    r.resolution_percentage = 50
    r.filepath = os.path.join(RENDERS, fn)
    bpy.ops.render.render(write_still=True)
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
sc.camera = c_calle
bpy.ops.wm.save_mainfile()
print("PUEBLO OK")
