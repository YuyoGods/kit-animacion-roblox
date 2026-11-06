# Centro del pueblo: glorieta, plaza con fuente, presidencia, casas anchas y pinos.
# Se puede volver a ejecutar: borra la coleccion "Centro" y la recrea.
import bpy, bmesh, math, random
from mathutils import Vector

random.seed(23)
sc = bpy.context.scene
FONT = r"C:\Windows\Fonts\ariblk.ttf"

# --- medidas de la calle existente ---
ROAD_HW = 8.0
WALK = 5.0
STREET_END = 264.0
HOUSE_OFF = 29.5            # distancia del centro de la casa al eje de la calle
# --- glorieta / plaza ---
PC = Vector((0, 380))       # centro de la plaza (fuente)
RING = 40.0                 # eje de la glorieta (cuadrado)
PLAZA_HALF = RING - ROAD_HW # 32: borde interior
OUTER = RING + ROAD_HW      # 48: borde exterior de la calzada
# --- presidencia ---
ESP_Y0 = OUTER + WALK + PC.y   # 433 inicio de la explanada
WALL_Y = 466.0                 # fachada


def lin(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (o[0], o[1], o[2], 1.0)


# ---------------- limpiar version anterior ----------------
def nuke(name):
    c = bpy.data.collections.get(name)
    if not c:
        return
    for ch in list(c.children_recursive):
        for o in list(ch.objects):
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(ch)
    for o in list(c.objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)


nuke("Centro")
nuke("Centro_Modelos")
ROOT = bpy.data.collections.new("Centro"); sc.collection.children.link(ROOT)
MODELS = bpy.data.collections.new("Centro_Modelos"); sc.collection.children.link(MODELS)


def sub(parent, name):
    c = bpy.data.collections.new(name); parent.children.link(c); return c


C_CALLES, C_PLAZA, C_FUENTE, C_PRES, C_CASAS, C_PINOS, C_LUCES, C_CAMS = [sub(ROOT, n) for n in (
    "Glorieta", "Plaza", "Fuente", "Presidencia", "Casas_Anchas", "Pinos", "Luces_Centro", "Camaras_Centro")]


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


def mk_noise(name, hexc, rough=0.85, scale=6, amount=0.12, metal=0.0, emit=None, es=0.0, alpha=1.0, bump_s=0.1):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 5
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 1 - amount
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1.0; mx.inputs["A"].default_value = lin(hexc)
    nt.links.new(mr.outputs["Result"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if bump_s:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump_s
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit); b.inputs["Emission Strength"].default_value = es
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha; m.surface_render_method = 'BLENDED'
    return m


def mk_tiles(name, hexc, mortar, w, h, dark=0.9, vertical=False):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0; br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h; br.inputs["Mortar Size"].default_value = 0.04
    c1 = lin(hexc); br.inputs["Color1"].default_value = c1
    br.inputs["Color2"].default_value = (c1[0] * dark, c1[1] * dark, c1[2] * dark, 1)
    br.inputs["Mortar"].default_value = lin(mortar)
    if vertical:
        sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
        ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'
        nt.links.new(sx.outputs[0], ad.inputs[0]); nt.links.new(sx.outputs[1], ad.inputs[1])
        cb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ad.outputs[0], cb.inputs[0]); nt.links.new(sx.outputs[2], cb.inputs[1])
        nt.links.new(cb.outputs[0], br.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3
    nt.links.new(inv.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def mk_water(name, alpha, streaks=False):
    m, nt, b = base_mat(name)
    b.inputs["Base Color"].default_value = lin("#6FBFEA")
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["Specular IOR Level"].default_value = 0.6
    b.inputs["Emission Color"].default_value = lin("#A8E2FF")
    b.inputs["Emission Strength"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Z' if streaks else 'X'
    wv.inputs["Scale"].default_value = 2.5 if streaks else 1.2
    wv.inputs["Distortion"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    if streaks:
        # chorros: rayas verticales semitransparentes
        sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
        at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'
        nt.links.new(sx.outputs[1], at.inputs[0]); nt.links.new(sx.outputs[0], at.inputs[1])
        sn = nt.nodes.new("ShaderNodeMath"); sn.operation = 'SINE'
        ml = nt.nodes.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = 22.0
        nt.links.new(at.outputs[0], ml.inputs[0]); nt.links.new(ml.outputs[0], sn.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = -1; mr.inputs["To Min"].default_value = alpha * 0.35; mr.inputs["To Max"].default_value = alpha
        nt.links.new(sn.outputs[0], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Alpha"])
    else:
        b.inputs["Alpha"].default_value = alpha
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35
    nt.links.new(wv.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    return m


def get(name, fallback):
    return bpy.data.materials.get(name) or fallback()


M = {
    "asfalto": get("Asfalto", lambda: mk_noise("Asfalto", "#28282C", 0.92, 30, 0.2)),
    "linea": get("Linea_Amarilla", lambda: mk_noise("Linea_Amarilla", "#FAC726", 0.7)),
    "acera": get("Acera", lambda: mk_tiles("Acera", "#B8B4AC", "#7D7973", 2, 2)),
    "blanco": get("Casa_Borde", lambda: mk_noise("Casa_Borde", "#F4F0E6", 0.7, 8, 0.08)),
    "vidrio": get("Casa_Vidrio", lambda: mk_noise("Casa_Vidrio", "#2B3E57", 0.08, 2, 0.05)),
    "hojas": get("Hojas", lambda: mk_noise("Hojas", "#3C7D30", 0.8, 6, 0.3, bump_s=0.4)),
    "madera": get("Madera", lambda: mk_noise("Madera", "#6B4A2B", 0.8, 4, 0.2)),
    "metal": get("Farol_Metal", lambda: mk_noise("Farol_Metal", "#2C3036", 0.55, 9, 0.2, metal=0.55)),
    "pasto": get("Pasto", lambda: mk_noise("Pasto", "#3A7528", 0.95, 0.4, 0.2)),
    "plaza": mk_tiles("Plaza_Piso", "#C9B79C", "#8E8070", 2.2, 2.2, dark=0.9),
    "piedra": mk_noise("Fuente_Piedra", "#DCD5C6", 0.8, 5, 0.12),
    "agua": mk_water("Agua", 0.6),
    "agua_caida": mk_water("Agua_Caida", 0.55, streaks=True),
    "espuma": mk_noise("Espuma", "#F4FBFF", 0.6, 12, 0.2, emit="#FFFFFF", es=0.3, alpha=0.75, bump_s=0.5),
    "muro": mk_noise("Pres_Muro", "#EAD8B6", 0.9, 3, 0.1, bump_s=0.25),
    "zocalo": mk_tiles("Pres_Zocalo", "#9C948A", "#6A645D", 3.0, 1.0, dark=0.9, vertical=True),
    "teja": mk_noise("Pres_Cupula", "#B5603A", 0.6, 4, 0.18, bump_s=0.2),
    "puerta": mk_noise("Pres_Puerta", "#5A341C", 0.7, 3, 0.2),
    "negro": mk_noise("Negro_Mate", "#141416", 0.6, 4, 0.05),
    "reloj": mk_noise("Reloj_Cara", "#FBF6E8", 0.5, 4, 0.04, emit="#FFF6DD", es=0.15),
    "oro": mk_noise("Dorado", "#C9A23A", 0.35, 6, 0.1, metal=0.8),
    "texto": mk_noise("Pres_Texto", "#5A3A22", 0.6, 4, 0.05),
    "verde_metal": mk_noise("Bote_Verde", "#2E5E3A", 0.55, 6, 0.12, metal=0.3),
    "corteza": mk_noise("Pino_Corteza", "#4E3524", 0.95, 14, 0.35, bump_s=0.6),
    "pino": mk_noise("Pino_Hojas", "#1F4D2B", 0.85, 3, 0.35, bump_s=0.6),
    "pino2": mk_noise("Pino_Hojas_Claro", "#2C6537", 0.85, 3, 0.35, bump_s=0.6),
    "globo": mk_noise("Globo_Luz", "#FFF1D6", 0.3, 3, 0.02, emit="#FFC98A", es=6.0),
    "tierra": get("Tierra", lambda: mk_noise("Tierra", "#4A3324", 0.95, 8, 0.25)),
}
# bandera tricolor (franjas verticales con ColorRamp constante)
mflag, nt, b = base_mat("Bandera")
tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sx.inputs[0])
cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = 'CONSTANT'
cr.color_ramp.elements[0].color = lin("#006847"); cr.color_ramp.elements[1].position = 0.333
cr.color_ramp.elements[1].color = lin("#F5F5F0"); e3 = cr.color_ramp.elements.new(0.666); e3.color = lin("#CE1126")
nt.links.new(sx.outputs[0], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.8
mflag.use_backface_culling = False
M["bandera"] = mflag


# ---------------- geometria ----------------
def obj(name, col, me, loc, m, rot=(0, 0, 0), smooth=False):
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    me.materials.append(m)
    col.objects.link(o)
    return o


def box(name, col, loc, size, m, rot=(0, 0, 0), bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot)


def cone(name, col, loc, r1, r2, depth, m, rot=(0, 0, 0), seg=32, caps=True, smooth=True):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=seg, radius1=r1, radius2=r2, depth=depth)
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot, smooth)


def cyl(name, col, loc, r, depth, m, rot=(0, 0, 0), seg=32):
    return cone(name, col, loc, r, r, depth, m, rot, seg)


def ball(name, col, loc, r, m, squash=1.0, sub=2):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    for v in bm.verts:
        v.co.z *= squash
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, smooth=True)


def torus(name, col, loc, R, r, m, rot=(0, 0, 0), seg=48, ring=10):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [[bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
           for b in [2 * math.pi * j / ring for j in range(ring)]] for a in [2 * math.pi * i / seg for i in range(seg)]]
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % ring], vs[i][(j + 1) % ring]))
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot, True)


def text(name, col, body, loc, size, m, rot=(90, 0, 0)):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size; cu.extrude = 0.08; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    cu.materials.append(m); col.objects.link(o); return o


def instance(name, col, src, loc, rot_z=0.0, scale=(1, 1, 1)):
    e = bpy.data.objects.new(name, None)
    e.instance_type = 'COLLECTION'; e.instance_collection = src
    e.location = loc; e.rotation_euler = (0, 0, rot_z); e.scale = scale
    col.objects.link(e); return e


def model(name):
    c = bpy.data.collections.new(name); MODELS.children.link(c); return c


# ================= GLORIETA Y CALLES =================
Z_ROAD, Z_WALK = 0.02, 0.15
# tramo que conecta la calle con la glorieta
y0, y1 = STREET_END, PC.y - OUTER
box("Calle_Conector", C_CALLES, (0, (y0 + y1) / 2, Z_ROAD), (ROAD_HW * 2, y1 - y0, 0.1), M["asfalto"])
for sx_ in (-1, 1):
    box("Acera_Conector", C_CALLES, (sx_ * (ROAD_HW + WALK / 2), (y0 + y1 - WALK) / 2, Z_WALK), (WALK, y1 - y0 - WALK, 0.3), M["acera"])
# glorieta cuadrada (4 tramos)
box("Glorieta_Sur", C_CALLES, (PC.x, PC.y - RING, Z_ROAD), (OUTER * 2, ROAD_HW * 2, 0.1), M["asfalto"])
box("Glorieta_Norte", C_CALLES, (PC.x, PC.y + RING, Z_ROAD), (OUTER * 2, ROAD_HW * 2, 0.1), M["asfalto"])
for sx_ in (-1, 1):
    box("Glorieta_Lado", C_CALLES, (sx_ * RING, PC.y, Z_ROAD), (ROAD_HW * 2, (RING - ROAD_HW) * 2, 0.1), M["asfalto"])
# aceras exteriores
OW = OUTER + WALK
for sx_ in (-1, 1):
    box("Acera_Ext_Lado", C_CALLES, (sx_ * (OUTER + WALK / 2), PC.y, Z_WALK), (WALK, OW * 2, 0.3), M["acera"])
    box("Acera_Ext_Sur", C_CALLES, (sx_ * (ROAD_HW + (OUTER - ROAD_HW) / 2), PC.y - OUTER - WALK / 2, Z_WALK), (OUTER - ROAD_HW, WALK, 0.3), M["acera"])
box("Acera_Ext_Norte", C_CALLES, (0, PC.y + OUTER + WALK / 2, Z_WALK), (OUTER * 2, WALK, 0.3), M["acera"])
# linea amarilla discontinua
def dashes(p0, p1, step=8.0, dash=4.0):
    d = Vector(p1) - Vector(p0); L = d.length; u = d / L; t = 2.0
    while t + dash < L - 2.0:
        c = Vector(p0) + u * (t + dash / 2)
        horiz = abs(u.x) > abs(u.y)
        box("Linea", C_CALLES, (c.x, c.y, 0.08), (dash, 0.35, 0.03) if horiz else (0.35, dash, 0.03), M["linea"])
        t += step
dashes((0, y0), (0, PC.y - RING - ROAD_HW))
dashes((-RING, PC.y - RING), (RING, PC.y - RING))
dashes((-RING, PC.y + RING), (RING, PC.y + RING))
dashes((-RING, PC.y - RING + ROAD_HW), (-RING, PC.y + RING - ROAD_HW))
dashes((RING, PC.y - RING + ROAD_HW), (RING, PC.y + RING - ROAD_HW))
# pasto extra hacia el norte
box("Pasto_Norte", C_CALLES, (0, 430, -0.07), (280, 260, 0.1), M["pasto"])

# ================= PLAZA =================
box("Plaza_Piso", C_PLAZA, (PC.x, PC.y, 0.18), (PLAZA_HALF * 2, PLAZA_HALF * 2, 0.36), M["plaza"])
box("Plaza_Bordillo", C_PLAZA, (PC.x, PC.y, 0.12), (PLAZA_HALF * 2 + 0.6, PLAZA_HALF * 2 + 0.6, 0.24), M["acera"])
ZP = 0.36  # nivel del piso de la plaza

# --- banca modelo (mira hacia -Y) ---
BANCA = model("Banca_Modelo")
for k in range(3):
    box("Banca_Tabla", BANCA, (0, -0.35 + k * 0.42, 1.55), (5.0, 0.36, 0.14), M["madera"], bevel=0.04)
for k in range(2):
    box("Banca_Respaldo", BANCA, (0, 0.62, 2.25 + k * 0.5), (5.0, 0.12, 0.34), M["madera"], rot=(-12, 0, 0), bevel=0.03)
for sx_ in (-1, 1):
    box("Banca_Pata", BANCA, (sx_ * 2.1, 0.0, 0.78), (0.22, 1.3, 1.55), M["metal"])
    box("Banca_PataResp", BANCA, (sx_ * 2.1, 0.62, 2.35), (0.18, 0.18, 1.6), M["metal"], rot=(-12, 0, 0))
    box("Banca_Brazo", BANCA, (sx_ * 2.25, 0.05, 2.15), (0.2, 1.4, 0.16), M["metal"])

# --- bote de basura modelo ---
BOTE = model("Bote_Modelo")
cyl("Bote_Cuerpo", BOTE, (0, 0, 1.35), 0.75, 2.7, M["verde_metal"], seg=24)
torus("Bote_Aro", BOTE, (0, 0, 2.72), 0.78, 0.09, M["metal"])
cone("Bote_Tapa", BOTE, (0, 0, 2.95), 0.82, 0.45, 0.45, M["verde_metal"], seg=24)
for k in range(8):
    a = 2 * math.pi * k / 8
    box("Bote_Franja", BOTE, (math.cos(a) * 0.74, math.sin(a) * 0.74, 1.35), (0.12, 0.12, 2.3), M["metal"], rot=(0, 0, math.degrees(a)))

# --- farol de plaza modelo (globo) ---
FAROLP = model("FarolPlaza_Modelo")
cone("FP_Pie", FAROLP, (0, 0, 0.45), 0.55, 0.35, 0.9, M["metal"], seg=16)
cyl("FP_Poste", FAROLP, (0, 0, 4.2), 0.16, 6.8, M["metal"], seg=12)
torus("FP_Aro", FAROLP, (0, 0, 7.55), 0.35, 0.08, M["metal"])
ball("FP_Globo", FAROLP, (0, 0, 8.25), 0.75, M["globo"]).visible_shadow = False
cone("FP_Tapa", FAROLP, (0, 0, 9.05), 0.35, 0.05, 0.4, M["metal"], seg=16)
plaza_light = bpy.data.lights.get("Plaza_Luz") or bpy.data.lights.new("Plaza_Luz", 'POINT')
plaza_light.energy = 420; plaza_light.color = lin("#FFC98A")[:3]; plaza_light.shadow_soft_size = 0.5


def farol_plaza(name, x, y, z=ZP):
    instance(name, C_LUCES, FAROLP, (x, y, z))
    L = bpy.data.objects.new("Luz_" + name, plaza_light); L.location = (x, y, z + 8.25); C_LUCES.objects.link(L)


# bancas alrededor de la fuente, mirando al centro
R_BANCA = 15.5
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    instance("Banca_%02d" % (k + 1), C_PLAZA, BANCA, (PC.x + R_BANCA * math.cos(a), PC.y + R_BANCA * math.sin(a), ZP), a - math.pi / 2)
# botes de basura entre bancas
for k in range(4):
    a = math.radians(45 + 90 * k)
    instance("Bote_%02d" % (k + 1), C_PLAZA, BOTE, (PC.x + 16.5 * math.cos(a), PC.y + 16.5 * math.sin(a), ZP))
# arbustos: anillo alrededor de la fuente (con huecos en los 4 accesos) + borde de la plaza
for k in range(48):
    ang = 360 * k / 48
    if min(abs(((ang - a0) + 180) % 360 - 180) for a0 in (0, 90, 180, 270)) < 12:
        continue
    a = math.radians(ang)
    ball("Arbusto_Fuente", C_PLAZA, (PC.x + 10.8 * math.cos(a), PC.y + 10.8 * math.sin(a), ZP + 0.6), random.uniform(0.9, 1.15), M["hojas"], 0.8)
EDGE = PLAZA_HALF - 1.8
for side in range(4):
    for k in range(17):
        t = -EDGE + k * (2 * EDGE / 16)
        if abs(t) < 6.5:
            continue  # pasillos al centro
        x, y = [(t, -EDGE), (t, EDGE), (-EDGE, t), (EDGE, t)][side]
        ball("Arbusto_Borde", C_PLAZA, (PC.x + x, PC.y + y, ZP + 0.75), random.uniform(1.1, 1.4), M["hojas"], 0.75)
# jardineras en las esquinas con flores
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        cx, cy = PC.x + sx_ * (EDGE - 4), PC.y + sy_ * (EDGE - 4)
        cyl("Jardinera", C_PLAZA, (cx, cy, ZP + 0.4), 2.4, 0.8, M["piedra"])
        cyl("Jardinera_Tierra", C_PLAZA, (cx, cy, ZP + 0.78), 2.1, 0.1, M["tierra"])
        ball("Jardinera_Arbusto", C_PLAZA, (cx, cy, ZP + 1.8), 1.9, M["hojas"], 0.9)
# faroles de plaza (moderados): 4 en accesos + 2 en la explanada
for k, (dx, dy) in enumerate(((0, -24), (0, 24), (-24, 0), (24, 0))):
    farol_plaza("FarolPlaza_%d" % (k + 1), PC.x + dx + 3.2, PC.y + dy + (3.2 if dx else 0), )

# ================= FUENTE =================
F = C_FUENTE
fx, fy, z0 = PC.x, PC.y, ZP
cyl("Fuente_Pileta", F, (fx, fy, z0 + 0.7), 7.5, 1.4, M["piedra"], seg=64)
torus("Fuente_Borde", F, (fx, fy, z0 + 1.42), 7.45, 0.4, M["piedra"], seg=64)
cyl("Fuente_Agua", F, (fx, fy, z0 + 1.2), 7.0, 0.08, M["agua"], seg=64)
cyl("Fuente_Pedestal", F, (fx, fy, z0 + 3.4), 1.0, 4.2, M["piedra"])
torus("Fuente_PedAro", F, (fx, fy, z0 + 1.6), 1.15, 0.25, M["piedra"])
cone("Fuente_Taza1", F, (fx, fy, z0 + 5.6), 1.0, 3.3, 1.2, M["piedra"], seg=48)
cyl("Fuente_Agua1", F, (fx, fy, z0 + 6.17), 3.05, 0.06, M["agua"], seg=48)
cyl("Fuente_Columna", F, (fx, fy, z0 + 7.5), 0.6, 2.6, M["piedra"])
cone("Fuente_Taza2", F, (fx, fy, z0 + 9.0), 0.55, 1.8, 0.8, M["piedra"], seg=40)
cyl("Fuente_Agua2", F, (fx, fy, z0 + 9.37), 1.62, 0.05, M["agua"], seg=40)
ball("Fuente_Remate", F, (fx, fy, z0 + 9.8), 0.42, M["piedra"])
# agua "cayendo" (cortinas fijas) + chorro central + espuma
cone("Fuente_Chorro", F, (fx, fy, z0 + 10.9), 0.2, 0.08, 2.2, M["agua_caida"], seg=12)
ball("Fuente_ChorroTope", F, (fx, fy, z0 + 12.0), 0.32, M["agua"], 0.7)
cone("Fuente_Cortina1", F, (fx, fy, z0 + 7.75), 2.55, 1.8, 3.2, M["agua_caida"], seg=48, caps=False)
cone("Fuente_Cortina2", F, (fx, fy, z0 + 3.65), 4.4, 3.3, 4.9, M["agua_caida"], seg=64, caps=False)
torus("Fuente_Espuma1", F, (fx, fy, z0 + 6.2), 2.55, 0.14, M["espuma"])
torus("Fuente_Espuma2", F, (fx, fy, z0 + 1.25), 4.4, 0.2, M["espuma"], seg=64)
for k in range(10):
    a = 2 * math.pi * k / 10
    ball("Fuente_Salpicadura", F, (fx + 4.4 * math.cos(a), fy + 4.4 * math.sin(a), z0 + 1.35), random.uniform(0.18, 0.3), M["espuma"])

# ================= PRESIDENCIA =================
P = C_PRES
W, D = 56.0, 24.0
YC = WALL_Y + D / 2
ZB = 1.5
# explanada para discursos
ESP_Y1 = WALL_Y - 11
box("Explanada", P, (0, (ESP_Y0 + ESP_Y1) / 2, 0.15), (OUTER * 2 + WALK * 2, ESP_Y1 - ESP_Y0, 0.3), M["plaza"])
box("Zocalo", P, (0, YC - 3, ZB / 2), (W + 6, D + 12, ZB), M["zocalo"])
for k in range(3):
    box("Escalinata", P, (0, ESP_Y1 + 0.9 + k * 0.9 - 2.7 + 2.7, 0.25 + k * 0.5), (30 - k * 2, 1.8 + (2 - k) * 1.8, 0.5), M["zocalo"])
box("Cuerpo", P, (0, YC, ZB + 8.5), (W, D, 17.0), M["muro"])
box("Faja_Media", P, (0, YC, ZB + 9.0), (W + 0.6, D + 0.6, 0.5), M["blanco"])
box("Cornisa", P, (0, YC, ZB + 17.2), (W + 1.4, D + 1.4, 0.8), M["blanco"])
box("Pretil", P, (0, YC, ZB + 18.8), (W, D, 2.6), M["muro"])
box("Pretil_Remate", P, (0, YC, ZB + 20.2), (W + 0.6, D + 0.6, 0.35), M["blanco"])
text("Letrero", P, "PRESIDENCIA MUNICIPAL", (0, WALL_Y - 0.12, ZB + 18.75), 1.55, M["texto"])
for sx_ in (-1, 1):
    box("Pilastra", P, (sx_ * (W / 2), WALL_Y, ZB + 8.5), (1.4, 1.4, 17), M["blanco"])
# portico de columnas blancas que sostiene el balcon
COL_Y = WALL_Y - 4.6
xs_cols = [-26.5, -19.5, -12, -4.6, 4.6, 12, 19.5, 26.5]
for i, x in enumerate(xs_cols):
    box("Columna_Base", P, (x, COL_Y, ZB + 0.3), (2.2, 2.2, 0.6), M["blanco"])
    cyl("Columna", P, (x, COL_Y, ZB + 4.75), 0.85, 8.3, M["blanco"], seg=24)
    box("Columna_Capitel", P, (x, COL_Y, ZB + 9.1), (2.2, 2.2, 0.5), M["blanco"])
box("Balcon_Losa", P, (0, WALL_Y - 3.0, ZB + 9.65), (W + 2, 6.0, 0.7), M["blanco"])
for k in range(48):
    x = -28.2 + k * (56.4 / 47)
    cyl("Balaustre", P, (x, WALL_Y - 5.6, ZB + 10.75), 0.2, 1.5, M["blanco"], seg=10)
box("Balcon_Pasamanos", P, (0, WALL_Y - 5.6, ZB + 11.6), (W + 1.2, 0.5, 0.3), M["blanco"])


def pres_window(x, cz, w, h, tag):
    box(tag + "_Marco", P, (x, WALL_Y - 0.12, cz), (w + 0.7, 0.35, h + 0.7), M["blanco"])
    box(tag + "_Vidrio", P, (x, WALL_Y - 0.26, cz), (w, 0.2, h), M["vidrio"])
    box(tag + "_ParteV", P, (x, WALL_Y - 0.38, cz), (0.16, 0.12, h), M["blanco"])
    for zz in (cz - h / 6, cz + h / 6):
        box(tag + "_ParteH", P, (x, WALL_Y - 0.38, zz), (w, 0.12, 0.16), M["blanco"])
    box(tag + "_Cornisa", P, (x, WALL_Y - 0.4, cz + h / 2 + 0.6), (w + 1.4, 0.8, 0.35), M["blanco"])


for x in (-23, -15.75, -8.3, 8.3, 15.75, 23):
    pres_window(x, ZB + 4.6, 3.2, 5.2, "VentanaPB")
for x in (-23, -15.75, -8.3, 0, 8.3, 15.75, 23):
    pres_window(x, ZB + 13.6, 3.0, 5.0, "VentanaPA")
# puerta principal doble con arco
box("Puerta_Marco", P, (0, WALL_Y - 0.15, ZB + 2.9), (6.8, 0.4, 5.8), M["blanco"])
cyl("Puerta_Arco", P, (0, WALL_Y - 0.15, ZB + 5.6), 3.4, 0.4, M["blanco"], rot=(90, 0, 0))
cyl("Puerta_ArcoVidrio", P, (0, WALL_Y - 0.3, ZB + 5.6), 2.6, 0.2, M["vidrio"], rot=(90, 0, 0))
for sx_ in (-1, 1):
    box("Puerta_Hoja", P, (sx_ * 1.47, WALL_Y - 0.32, ZB + 2.8), (2.9, 0.25, 5.6), M["puerta"])
    box("Puerta_Panel", P, (sx_ * 1.47, WALL_Y - 0.47, ZB + 4.1), (2.1, 0.08, 2.0), M["puerta"], bevel=0.05)
    box("Puerta_Panel", P, (sx_ * 1.47, WALL_Y - 0.47, ZB + 1.5), (2.1, 0.08, 2.0), M["puerta"], bevel=0.05)
    ball("Puerta_Manija", P, (sx_ * 0.4, WALL_Y - 0.55, ZB + 2.9), 0.2, M["oro"])
# torre del reloj
TZ0 = ZB + 20.4
box("Torre", P, (0, YC - 2, TZ0 + 7), (12, 10, 14), M["muro"])
for sx_ in (-1, 1):
    box("Torre_Pilastra", P, (sx_ * 6, YC - 7, TZ0 + 7), (1.0, 1.0, 14), M["blanco"])
box("Torre_Cornisa", P, (0, YC - 2, TZ0 + 14.3), (13.2, 11.2, 0.7), M["blanco"])
CLK = Vector((0, YC - 7.05, TZ0 + 7.6))
cyl("Reloj_Marco", P, (CLK.x, CLK.y - 0.2, CLK.z), 4.3, 0.45, M["blanco"], rot=(90, 0, 0), seg=64)
cyl("Reloj_Cara", P, (CLK.x, CLK.y - 0.45, CLK.z), 3.8, 0.1, M["reloj"], rot=(90, 0, 0), seg=64)
torus("Reloj_Aro", P, (CLK.x, CLK.y - 0.5, CLK.z), 3.8, 0.14, M["negro"], rot=(90, 0, 0), seg=64)
for k in range(12):
    a = 2 * math.pi * k / 12
    big = (k % 3 == 0)
    box("Reloj_Marca", P, (CLK.x + 3.25 * math.sin(a), CLK.y - 0.55, CLK.z + 3.25 * math.cos(a)),
        (0.22 if big else 0.14, 0.06, 0.8 if big else 0.5), M["negro"], rot=(0, math.degrees(a), 0))


def hand(name, length, width, m):
    """manecilla con el pivote en el centro del reloj: girar en Y para moverla"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * width, v.co.y * 0.08, (v.co.z + 0.5) * length - 0.4))
    bm.to_mesh(me); bm.free()
    return obj(name, P, me, (CLK.x, CLK.y - 0.62, CLK.z), m)


h_hour = hand("Reloj_Horario", 2.0, 0.32, M["negro"])
h_min = hand("Reloj_Minutero", 3.0, 0.2, M["negro"])
h_min.location.y -= 0.08
ball("Reloj_Centro", P, (CLK.x, CLK.y - 0.75, CLK.z), 0.25, M["oro"])
# hora inicial 10:10 (rotacion Y en grados: minutos*6, horas*30 + minutos*0.5)
h_min.rotation_euler = (0, math.radians(10 * 6), 0)
h_hour.rotation_euler = (0, math.radians(10 * 30 + 10 * 0.5), 0)
# cupula + asta + bandera
cyl("Cupula_Tambor", P, (0, YC - 2, TZ0 + 15.6), 4.2, 2.0, M["blanco"], seg=48)
dome = ball("Cupula", P, (0, YC - 2, TZ0 + 16.6), 4.4, M["teja"], 0.75, sub=3)
cyl("Asta", P, (0, YC - 2, TZ0 + 24.2), 0.16, 12, M["blanco"], seg=12)
ball("Asta_Remate", P, (0, YC - 2, TZ0 + 30.3), 0.3, M["oro"])
me = bpy.data.meshes.new("Bandera"); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=24, y_segments=12, size=0.5)
for v in bm.verts:
    u = v.co.x + 0.5
    v.co = Vector((u * 6.5, 0.45 * math.sin(u * 7.0) * u, (v.co.y) * 3.8))
bm.to_mesh(me); bm.free()
obj("Bandera", P, me, (0.15, YC - 2, TZ0 + 28.0), M["bandera"], smooth=True)
# podio con microfono sobre una tarima
STG_Y = ESP_Y0 + 9
box("Tarima", P, (0, STG_Y, 0.75), (14, 7, 0.9), M["madera"])
box("Tarima_Escalon", P, (0, STG_Y - 4.1, 0.45), (5, 1.2, 0.5), M["madera"])
box("Podio", P, (0, STG_Y - 1.0, 1.2 + 1.8), (2.6, 1.5, 3.6), M["puerta"], bevel=0.06)
box("Podio_Tapa", P, (0, STG_Y - 0.9, 1.2 + 3.7), (3.0, 1.9, 0.25), M["puerta"], rot=(-12, 0, 0))
box("Podio_Escudo", P, (0, STG_Y - 1.8, 1.2 + 2.2), (1.2, 0.06, 1.4), M["oro"])
mic_base = Vector((0, STG_Y - 1.2, 1.2 + 3.85))
cyl("Microfono_Brazo", P, (0, mic_base.y + 0.45, mic_base.z + 0.55), 0.06, 1.3, M["negro"], rot=(-40, 0, 0), seg=8)
ball("Microfono", P, (0, mic_base.y + 0.95, mic_base.z + 1.1), 0.22, M["negro"], 1.3)
for sx_ in (-1, 1):
    farol_plaza("FarolExplanada_%s" % ("I" if sx_ < 0 else "D"), sx_ * 11, STG_Y, 0.3)
    box("Maceton", P, (sx_ * 17, WALL_Y - 9.5, 1.0), (2.4, 2.4, 1.8), M["zocalo"])
    ball("Maceton_Arbusto", P, (sx_ * 17, WALL_Y - 9.5, 2.9), 1.6, M["hojas"], 1.1)

# ================= CASAS ANCHAS (mismo modelo, 25% mas anchas) =================
casa = bpy.data.collections.get("Casa_Base")
PAL = [("#F7D1A8", "#5B3A29", "#1F3B73", "#3C6E8F"), ("#C9E4C5", "#7A2E2E", "#8B1E1E", "#8F3C4A"),
       ("#BFD8E8", "#3E4A5C", "#2E5E3A", "#4F7F45"), ("#F2C6C2", "#2F4F3A", "#6B3E1F", "#7A5A9E"),
       ("#F5E3A1", "#4A3B5C", "#3B3B3B", "#C27C2C"), ("#E3D2F0", "#6E4B3A", "#B8892C", "#2F4858"),
       ("#F4B6A1", "#3E4A5C", "#1F3B73", "#3C6E8F"), ("#B9D3C9", "#5B3A29", "#8B1E1E", "#8F3C4A")]
spots = []
for y in (286.0, 312.0):            # junto al tramo conector
    spots += [(-HOUSE_OFF, y, math.radians(90)), (HOUSE_OFF, y, math.radians(-90))]
for y in (PC.y - 20, PC.y + 20):    # a los lados de la plaza
    spots += [(-(RING + HOUSE_OFF), y, math.radians(90)), (RING + HOUSE_OFF, y, math.radians(-90))]
if casa:
    for i, (x, y, rz) in enumerate(spots):
        e = instance("CasaAncha_%02d" % (i + 1), C_CASAS, casa, (x, y, 0), rz, (1.25, 1, 1))
        w_, r_, d_, a_ = PAL[i % len(PAL)]
        e["wall_color"] = lin(w_)[:3]; e["roof_color"] = lin(r_)[:3]
        e["door_color"] = lin(d_)[:3]; e["accent_color"] = lin(a_)[:3]

# faroles de calle (modelo existente) en el conector y la glorieta
far = bpy.data.collections.get("Farol_Base")
spot_d = bpy.data.lights.get("Farol_Luz")
if far and spot_d:
    H, ARM, PX = 13.2, 2.6, ROAD_HW + 0.9
    lamp_spots = [(-PX, 299, math.pi), (PX, 299, 0.0),
                  (-(OUTER + 0.9), PC.y, math.pi), (OUTER + 0.9, PC.y, 0.0),
                  (-24, PC.y - OUTER - 0.9, -math.pi / 2), (24, PC.y - OUTER - 0.9, -math.pi / 2),
                  (-24, PC.y + OUTER + 0.9, math.pi / 2), (24, PC.y + OUTER + 0.9, math.pi / 2)]
    for i, (x, y, rz) in enumerate(lamp_spots):
        instance("FarolCentro_%02d" % (i + 1), C_LUCES, far, (x, y, 0.3), rz)
        arm = Vector((-ARM * math.cos(rz), -ARM * math.sin(rz)))
        L = bpy.data.objects.new("Luz_FarolCentro_%02d" % (i + 1), spot_d)
        L.location = (x + arm.x, y + arm.y, 0.3 + H - 1.75); C_LUCES.objects.link(L)

# ================= PINOS =================
PINO = model("Pino_Modelo")
cyl("Pino_Tronco", PINO, (0, 0, 2.2), 0.55, 4.4, M["corteza"], seg=10)
for i, (r, h, z) in enumerate(((4.4, 5.2, 5.2), (3.6, 4.6, 8.2), (2.7, 4.2, 10.9), (1.7, 3.6, 13.4))):
    cone("Pino_Copa%d" % i, PINO, (0, 0, z), r, 0.15, h, M["pino"] if i % 2 == 0 else M["pino2"], seg=12, smooth=False)
blocked = [  # (xmin, xmax, ymin, ymax)
    (-44, 44, -60, 275), (-44, 44, 264, 334), (-58, 58, 322, 440), (-82, -56, 340, 420), (56, 82, 340, 420),
    (-60, 60, 428, 500), (-50, 50, 270, 330),
]
trees = []
tries = 0
while len(trees) < 150 and tries < 20000:
    tries += 1
    y = random.uniform(-85, 545)
    lim = 115 if y < 300 else 135          # no salirse del pasto
    x = random.uniform(-lim, lim)
    if any(a <= x <= b and c <= y <= d for a, b, c, d in blocked):
        continue
    if any((x - tx) ** 2 + (y - ty) ** 2 < 8.5 ** 2 for tx, ty in trees):
        continue
    trees.append((x, y))
for i, (x, y) in enumerate(trees):
    s = random.uniform(1.0, 1.7)
    instance("Pino_%03d" % (i + 1), C_PINOS, PINO, (x, y, 0), random.uniform(0, 6.28), (s, s, s * random.uniform(0.95, 1.15)))

# modelos ocultos (solo se ven sus copias)
for ch in bpy.context.view_layer.layer_collection.children["Centro_Modelos"].children:
    ch.exclude = True

# ================= CAMARAS DE PRUEBA =================
def cam(name, loc, target, fov):
    cd = bpy.data.cameras.new(name); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov); cd.clip_end = 1500
    o = bpy.data.objects.new(name, cd); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    C_CAMS.objects.link(o); return o


cam("Cam_CentroAerea", (95, 250, 110), (0, 395, 0), 42)
cam("Cam_Fuente", (9, 352, 6.5), (0, 380, 6), 55)
cam("Cam_Presidencia", (6, 405, 7), (0, 465, 18), 58)
print("centro ok | pinos:", len(trees), "| casas anchas:", len(spots), "| casa base:", bool(casa), "| faroles:", bool(far))
