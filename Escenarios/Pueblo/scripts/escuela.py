# Escuela con pasillo de lockers y dos salones. Se puede repetir (borra y recrea).
# Todo cuelga del vacio "Escuela": moverlo/rotarlo mueve la escuela completa.
# Para ver el interior desde arriba: ocultar los objetos "Escuela_Techo*".
import bpy, bmesh, math, random
from mathutils import Vector

random.seed(9)
sc = bpy.context.scene
FONT = r"C:\Windows\Fonts\ariblk.ttf"
FRONT_Y = 388.0                   # linea de la fachada en el mundo (queda a 19 de la acera)
SIDEWALK_Y = 407.0                # borde de la acera de la calle norte
RZ = math.pi                      # girada 180: el frente mira hacia la calle norte (+Y)

# medidas (locales)
HW, HD = 38.0, 26.0     # medio ancho / medio fondo del edificio (mas larga)
S = Vector((-188.0, FRONT_Y - HD, 0.0))  # terreno al oeste de las tiendas, al sur de la calle norte
SW_L = -(SIDEWALK_Y - S.y)               # la acera en coordenadas locales
T = 0.8                 # grosor muro exterior
TI = 0.5                # grosor muro interior
Z0, Z1 = 0.6, 11.6      # piso / techo interior
HALL = 8.0              # medio ancho del pasillo (pasillo amplio)
ROOM_W = (HW - T / 2) - (HALL + TI / 2)          # ancho libre de cada salon
_RC = HALL + TI / 2 + ROOM_W / 2
ROOM_C = (-_RC, _RC)                              # centros X de los salones
DOOR_Y = -HD + 6.0


def lin(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (o[0], o[1], o[2], 1.0)


# ---------------- limpiar ----------------
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


nuke("Escuela")
nuke("Escuela_Modelos")
COL = bpy.data.collections.new("Escuela"); sc.collection.children.link(COL)
MODS = bpy.data.collections.new("Escuela_Modelos"); sc.collection.children.link(MODS)
ROOT = bpy.data.objects.new("Escuela", None); ROOT.empty_display_size = 6; ROOT.location = S
ROOT.rotation_euler = (0, 0, RZ); COL.objects.link(ROOT)


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


def mk(name, hexc, rough=0.85, scale=6, amount=0.1, metal=0.0, emit=None, es=0.0, bump_s=0.08, alpha=1.0):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 1 - amount
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1; mx.inputs["A"].default_value = lin(hexc)
    nt.links.new(mr.outputs["Result"], mx.inputs["B"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if bump_s:
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump_s
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if emit:
        b.inputs["Emission Color"].default_value = lin(emit); b.inputs["Emission Strength"].default_value = es
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha; m.surface_render_method = 'BLENDED'
    return m


def mk_tiles(name, a, mortar, w, h, dark=0.88, rough=0.6):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1; br.inputs["Brick Width"].default_value = w; br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = 0.03
    c1 = lin(a); br.inputs["Color1"].default_value = c1
    br.inputs["Color2"].default_value = (c1[0] * dark, c1[1] * dark, c1[2] * dark, 1)
    br.inputs["Mortar"].default_value = lin(mortar)
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


def mk_checker(name, a, b_, scale, rough=0.25):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ck = nt.nodes.new("ShaderNodeTexChecker"); ck.inputs["Scale"].default_value = scale
    ck.inputs["Color1"].default_value = lin(a); ck.inputs["Color2"].default_value = lin(b_)
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"])
    nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.5
    return m


def mk_exterior_wall():
    """muro exterior: por fuera ladrillo abajo y crema arriba; por dentro azul abajo, franja blanca y crema arriba"""
    m, nt, b = base_mat("Escuela_Pared")
    g = nt.nodes.new("ShaderNodeNewGeometry")
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = (S.x, S.y, 6.0)
    nt.links.new(g.outputs["Position"], sub.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'
    nt.links.new(sub.outputs[0], dot.inputs[0]); nt.links.new(g.outputs["Normal"], dot.inputs[1])
    inside = nt.nodes.new("ShaderNodeMath"); inside.operation = 'LESS_THAN'; inside.inputs[1].default_value = 0.0
    nt.links.new(dot.outputs["Value"], inside.inputs[0])
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Position"], sx.inputs[0])
    # ladrillo
    ad = nt.nodes.new("ShaderNodeMath"); ad.operation = 'ADD'
    nt.links.new(sx.outputs[0], ad.inputs[0]); nt.links.new(sx.outputs[1], ad.inputs[1])
    cb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(ad.outputs[0], cb.inputs[0]); nt.links.new(sx.outputs[2], cb.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1; br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 0.4
    br.inputs["Mortar Size"].default_value = 0.035
    br.inputs["Color1"].default_value = lin("#A0503C"); br.inputs["Color2"].default_value = lin("#8A4232")
    br.inputs["Mortar"].default_value = lin("#D9CFC0")
    nt.links.new(cb.outputs[0], br.inputs["Vector"])

    def band(z, name):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = 'LESS_THAN'; n.inputs[1].default_value = z
        nt.links.new(sx.outputs[2], n.inputs[0]); return n

    lo_ext = band(3.6, "e")
    ext = nt.nodes.new("ShaderNodeMix"); ext.data_type = 'RGBA'
    ext.inputs["A"].default_value = lin("#F1E4C8"); nt.links.new(br.outputs["Color"], ext.inputs["B"])
    nt.links.new(lo_ext.outputs[0], ext.inputs["Factor"])
    lo_in = band(4.2, "i"); rail = band(4.5, "r")
    inn = nt.nodes.new("ShaderNodeMix"); inn.data_type = 'RGBA'
    inn.inputs["A"].default_value = lin("#FFFFFF"); inn.inputs["B"].default_value = lin("#86B9E0")
    nt.links.new(lo_in.outputs[0], inn.inputs["Factor"])
    inn2 = nt.nodes.new("ShaderNodeMix"); inn2.data_type = 'RGBA'
    inn2.inputs["A"].default_value = lin("#F6F0E2"); nt.links.new(inn.outputs["Result"], inn2.inputs["B"])
    nt.links.new(rail.outputs[0], inn2.inputs["Factor"])
    fin = nt.nodes.new("ShaderNodeMix"); fin.data_type = 'RGBA'
    nt.links.new(ext.outputs["Result"], fin.inputs["A"]); nt.links.new(inn2.outputs["Result"], fin.inputs["B"])
    nt.links.new(inside.outputs[0], fin.inputs["Factor"])
    nt.links.new(fin.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    return m


def mk_interior_wall():
    m, nt, b = base_mat("Escuela_ParedInterior")
    g = nt.nodes.new("ShaderNodeNewGeometry")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Position"], sx.inputs[0])
    lo = nt.nodes.new("ShaderNodeMath"); lo.operation = 'LESS_THAN'; lo.inputs[1].default_value = 4.2
    rl = nt.nodes.new("ShaderNodeMath"); rl.operation = 'LESS_THAN'; rl.inputs[1].default_value = 4.5
    nt.links.new(sx.outputs[2], lo.inputs[0]); nt.links.new(sx.outputs[2], rl.inputs[0])
    a = nt.nodes.new("ShaderNodeMix"); a.data_type = 'RGBA'
    a.inputs["A"].default_value = lin("#FFFFFF"); a.inputs["B"].default_value = lin("#86B9E0")
    nt.links.new(lo.outputs[0], a.inputs["Factor"])
    c = nt.nodes.new("ShaderNodeMix"); c.data_type = 'RGBA'
    c.inputs["A"].default_value = lin("#F6F0E2"); nt.links.new(a.outputs["Result"], c.inputs["B"])
    nt.links.new(rl.outputs[0], c.inputs["Factor"])
    nt.links.new(c.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    return m


def mk_globe():
    m, nt, b = base_mat("Globo_Terraqueo")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.55
    nt.links.new(nz.outputs["Fac"], gt.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin("#2D7BC4"); mx.inputs["B"].default_value = lin("#4E9B3A")
    nt.links.new(gt.outputs[0], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    return m


M = {
    "pared": mk_exterior_wall(), "pared_int": mk_interior_wall(),
    "blanco": bpy.data.materials.get("Casa_Borde") or mk("Casa_Borde", "#F4F0E6"),
    "vidrio": bpy.data.materials.get("Vidrio_Claro") or mk("Vidrio_Claro", "#A9C9E6", 0.1, alpha=0.15),
    "acera": bpy.data.materials.get("Acera") or mk("Acera", "#B8B4AC"),
    "hojas": bpy.data.materials.get("Hojas") or mk("Hojas", "#3C7D30"),
    "bandera": bpy.data.materials.get("Bandera"),
    "concreto": mk("Esc_Concreto", "#A7A39B", 0.9, 4, 0.15, bump_s=0.2),
    "techo": mk("Esc_TechoGris", "#6F7176", 0.9, 3, 0.15),
    "cielo": mk("Esc_Plafon", "#F7F5F0", 0.9, 3, 0.04, bump_s=0),
    "piso_pasillo": mk_checker("Esc_PisoPasillo", "#EEECE7", "#9FB4C8", 0.6),
    "piso_salon": mk_tiles("Esc_PisoMadera", "#C79A68", "#8A6440", 4.0, 0.55, 0.86, 0.5),
    "locker": mk("Esc_Locker", "#2F6FC9", 0.4, 5, 0.06, metal=0.45),
    "locker_osc": mk("Esc_LockerOscuro", "#1A2A45", 0.5, 5, 0.05),
    "plata": mk("Esc_Plata", "#C9CDD2", 0.3, 5, 0.05, metal=0.8),
    "pizarron": mk("Esc_Pizarron", "#2E5A3A", 0.95, 5, 0.12, bump_s=0.05),
    "tiza": mk("Esc_Tiza", "#F4F4EE", 0.9, 8, 0.1, emit="#FFFFFF", es=0.15),
    "madera": mk("Esc_Madera", "#9A6538", 0.7, 3, 0.18),
    "madera_clara": mk("Esc_MaderaClara", "#C99560", 0.6, 3, 0.15),
    "metal": mk("Esc_MetalGris", "#7E848B", 0.4, 5, 0.05, metal=0.6),
    "silla_azul": mk("Esc_SillaAzul", "#3A78C2", 0.45, 4, 0.05),
    "silla_naranja": mk("Esc_SillaNaranja", "#E8833A", 0.45, 4, 0.05),
    "puerta": mk("Esc_PuertaAzul", "#24508F", 0.5, 4, 0.06),
    "corcho": mk("Esc_Corcho", "#C49460", 0.95, 30, 0.3, bump_s=0.4),
    "globo": mk_globe(),
    "luz": mk("Esc_PanelLuz", "#FFFFFF", 0.3, 2, 0.01, emit="#FFF6E8", es=6),
    "salida": mk("Esc_Salida", "#1E9E4A", 0.4, 2, 0.02, emit="#3CFF7A", es=3),
    "rojo": mk("Esc_Rojo", "#D6342C", 0.5, 4, 0.05), "amarillo": mk("Esc_Amarillo", "#F2C230", 0.5, 4, 0.05),
    "verde": mk("Esc_Verde", "#3FA34D", 0.5, 4, 0.05), "azul": mk("Esc_Azul", "#2E6FD1", 0.5, 4, 0.05),
    "morado": mk("Esc_Morado", "#8E4FC8", 0.5, 4, 0.05), "rosa": mk("Esc_Rosa", "#EF7FA9", 0.5, 4, 0.05),
    "papel": mk("Esc_Papel", "#FBF8EF", 0.9, 4, 0.03), "negro": mk("Esc_Negro", "#18181A", 0.6, 4, 0.03),
    "dorado": bpy.data.materials.get("Dorado") or mk("Dorado", "#C9A23A", 0.35, metal=0.8),
    "maceta": bpy.data.materials.get("Maceta") or mk("Maceta", "#B5603A"),
    "cancha": mk("Esc_Cancha", "#3E7D6A", 0.8, 3, 0.1), "linea_blanca": mk("Esc_LineaBlanca", "#F2F2F2", 0.7, 3, 0.05),
    "naranja": mk("Esc_Aro", "#E2621B", 0.4, 3, 0.05),
}
COLORS = [M["rojo"], M["amarillo"], M["verde"], M["azul"], M["morado"], M["rosa"]]
FONT_DATA = bpy.data.fonts.load(FONT, check_existing=True)


# ---------------- geometria ----------------
def obj(name, me, loc, m, rot=(0, 0, 0), smooth=False, parent=ROOT, col=None):
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    if m:
        me.materials.append(m)
    (col or COL).objects.link(o)
    if parent:
        o.parent = parent
    return o


def box(name, loc, size, m, rot=(0, 0, 0), parent=ROOT, col=None, bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
    bm.to_mesh(me); bm.free()
    return obj(name, me, loc, m, rot, parent=parent, col=col)


def cyl(name, loc, r, depth, m, rot=(0, 0, 0), seg=20, parent=ROOT, col=None, r2=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    bm.to_mesh(me); bm.free()
    return obj(name, me, loc, m, rot, True, parent, col)


def ball(name, loc, r, m, squash=1.0, parent=ROOT, col=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co.z *= squash
    bm.to_mesh(me); bm.free()
    return obj(name, me, loc, m, smooth=True, parent=parent, col=col)


def torus(name, loc, R, r, m, rot=(0, 0, 0), parent=ROOT, col=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    seg, ring = 32, 8
    vs = [[bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
           for b in [2 * math.pi * j / ring for j in range(ring)]] for a in [2 * math.pi * i / seg for i in range(seg)]]
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((vs[i][j], vs[(i + 1) % seg][j], vs[(i + 1) % seg][(j + 1) % ring], vs[i][(j + 1) % ring]))
    bm.to_mesh(me); bm.free()
    return obj(name, me, loc, m, rot, True, parent, col)


def text(name, body, loc, size, m, rot=(90, 0, 0), parent=ROOT, align='CENTER', extrude=0.03):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body; cu.font = FONT_DATA
    cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = 'CENTER'
    cu.materials.append(m)
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    COL.objects.link(o); o.parent = parent
    return o


def inst(name, src, loc, rz=0.0, parent=ROOT):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = src
    e.location = loc; e.rotation_euler = (0, 0, rz); COL.objects.link(e); e.parent = parent; return e


def model(name):
    c = bpy.data.collections.new(name); MODS.children.link(c); return c


# ---- muro con huecos (puertas/ventanas) ----
def wall(name, axis, fixed, a, b, thick, m, openings):
    """axis='X': muro a lo largo de X en y=fixed. axis='Y': a lo largo de Y en x=fixed.
    openings: lista de (centro, ancho, z_abajo, z_arriba)"""
    def put(u0, u1, z0, z1):
        if u1 - u0 < 1e-3 or z1 - z0 < 1e-3:
            return
        c = (u0 + u1) / 2
        if axis == 'X':
            box(name, (c, fixed, (z0 + z1) / 2), (u1 - u0, thick, z1 - z0), m)
        else:
            box(name, (fixed, c, (z0 + z1) / 2), (thick, u1 - u0, z1 - z0), m)
    cur = a
    for (c, w, zb, zt) in sorted(openings):
        put(cur, c - w / 2, Z0, Z1)
        put(c - w / 2, c + w / 2, Z0, zb)
        put(c - w / 2, c + w / 2, zt, Z1)
        cur = c + w / 2
    put(cur, b, Z0, Z1)


def window(axis, fixed, c, w, zb, zt, thick, outward):
    """marco blanco + vidrio + repisas. outward = +1/-1: hacia donde esta el exterior"""
    h = zt - zb; zc = (zb + zt) / 2
    def B(nm, u, du, z, dz, off, dd, m):
        if axis == 'X':
            box(nm, (u, fixed + off, z), (du, dd, dz), m)
        else:
            box(nm, (fixed + off, u, z), (dd, du, dz), m)
    fw = 0.3
    B("Esc_VentanaMarco", c, w, zt - fw / 2, fw, 0, thick + 0.12, M["blanco"])
    B("Esc_VentanaMarco", c, w, zb + fw / 2, fw, 0, thick + 0.12, M["blanco"])
    B("Esc_VentanaMarco", c - w / 2 + fw / 2, fw, zc, h, 0, thick + 0.12, M["blanco"])
    B("Esc_VentanaMarco", c + w / 2 - fw / 2, fw, zc, h, 0, thick + 0.12, M["blanco"])
    B("Esc_VentanaParteV", c, 0.18, zc, h, 0, 0.2, M["blanco"])
    B("Esc_VentanaParteH", c, w, zc + h * 0.18, 0.18, 0, 0.2, M["blanco"])
    B("Esc_Vidrio", c, w - 0.3, zc, h - 0.3, 0, 0.05, M["vidrio"])
    B("Esc_RepisaExt", c, w + 0.6, zb - 0.15, 0.3, outward * (thick / 2 + 0.3), 0.7, M["blanco"])
    B("Esc_RepisaInt", c, w + 0.3, zb - 0.1, 0.2, -outward * (thick / 2 + 0.35), 0.8, M["madera_clara"])


# =================== ESTRUCTURA ===================
box("Esc_Cimiento", (0, 0, 0.3), (2 * HW + 1.6, 2 * HD + 1.6, 0.6), M["concreto"])
box("Esc_PisoPasillo", (0, 0, Z0 + 0.02), (2 * HALL - TI, 2 * HD - T, 0.04), M["piso_pasillo"])
for s in (-1, 1):
    box("Esc_PisoSalon", (s * (HALL + TI / 2 + ROOM_W / 2), 0, Z0 + 0.02), (ROOM_W, 2 * HD - T, 0.04), M["piso_salon"])

WIN_FRONT = sorted(sd * _RC + d for sd in (-1, 1) for d in (-9.0, 0.0, 9.0))
WIN_SIDE = [-18.0, -9.0, 0.0, 9.0]
WZ = (3.4, 9.2)
# frente (y = -HD) con puerta principal
wall("Esc_MuroFrente", 'X', -HD, -HW, HW, T, M["pared"],
     [(0, 6.0, Z0, 8.6)] + [(x, 5.0, WZ[0], WZ[1]) for x in WIN_FRONT])
# fondo (y = +HD): pizarrones en los salones, puerta trasera en el pasillo
wall("Esc_MuroFondo", 'X', HD, -HW, HW, T, M["pared"], [(0, 4.0, Z0, 8.0)])
for sx_ in (-1, 1):
    wall("Esc_MuroLado", 'Y', sx_ * HW, -HD - T / 2, HD + T / 2, T, M["pared"], [(y, 5.0, WZ[0], WZ[1]) for y in WIN_SIDE])
    wall("Esc_MuroPasillo", 'Y', sx_ * HALL, -HD + T / 2, HD - T / 2, TI, M["pared_int"], [(DOOR_Y, 3.6, Z0, 7.8)])
for x in WIN_FRONT:
    window('X', -HD, x, 5.0, WZ[0], WZ[1], T, -1)
for sx_ in (-1, 1):
    for y in WIN_SIDE:
        window('Y', sx_ * HW, y, 5.0, WZ[0], WZ[1], T, sx_)

# ---------- todo lo que esta arriba del plafon se llama "Escuela_Techo_*" (ocultarlo = ver el interior) ----------
def mk_blind():
    m, nt, b = base_mat("Esc_Persiana")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.78
    nt.links.new(wv.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1
    mx.inputs["A"].default_value = lin("#EFE6D2"); nt.links.new(mr.outputs["Result"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    return m


M["persiana"] = mk_blind()
M["interior_p2"] = mk("Esc_InteriorP2", "#3A332D", 0.9, 3, 0.1, bump_s=0)
Z2 = Z1 + 0.6           # nivel del segundo piso (solo fachada)
H2 = 9.4
ZT = Z2 + H2            # azotea
box("Escuela_Techo_Plafon", (0, 0, Z1 + 0.05), (2 * HW, 2 * HD, 0.1), M["cielo"])
box("Escuela_Techo_Entrepiso", (0, 0, Z1 + 0.3), (2 * HW + 1.2, 2 * HD + 1.2, 0.6), M["blanco"])
box("Escuela_Techo_Piso2", (0, 0, Z2 + H2 / 2), (2 * HW, 2 * HD, H2), M["pared"])
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        box("Escuela_Techo_Esquinero", (sx_ * HW, sy_ * HD, Z2 + H2 / 2), (1.0, 1.0, H2), M["blanco"])
        box("Esc_Esquinero", (sx_ * HW, sy_ * HD, (Z0 + Z1) / 2), (1.0, 1.0, Z1 - Z0), M["blanco"])
W2Z = (Z2 + 2.3, Z2 + 7.4)


def win2(axis, face, o, c, w):
    """ventana del 2o piso: fondo oscuro, persiana a media altura, vidrio y marco"""
    zb, zt = W2Z; h = zt - zb; zc = (zb + zt) / 2

    def B(nm, u, du, z, dz, off, dd, m):
        if axis == 'X':
            box(nm, (u, face + o * off, z), (du, dd, dz), m)
        else:
            box(nm, (face + o * off, u, z), (dd, du, dz), m)
    B("Escuela_Techo_P2Fondo", c, w, zc, h, 0.03, 0.04, M["interior_p2"])
    frac = random.uniform(0.25, 0.7)
    B("Escuela_Techo_P2Persiana", c, w - 0.1, zt - h * frac / 2, h * frac, 0.08, 0.04, M["persiana"])
    B("Escuela_Techo_P2Vidrio", c, w, zc, h, 0.15, 0.04, M["vidrio"])
    fw = 0.32
    for (u, du, z, dz) in ((c, w + 2 * fw, zt + fw / 2, fw), (c, w + 2 * fw, zb - fw / 2, fw),
                           (c - w / 2 - fw / 2, fw, zc, h), (c + w / 2 + fw / 2, fw, zc, h)):
        B("Escuela_Techo_P2Marco", u, du, z, dz, 0.15, 0.3, M["blanco"])
    B("Escuela_Techo_P2Parteluz", c, 0.16, zc, h, 0.2, 0.12, M["blanco"])
    B("Escuela_Techo_P2Repisa", c, w + 0.8, zb - fw - 0.12, 0.25, 0.35, 0.7, M["blanco"])


for x in WIN_FRONT:
    win2('X', -HD, -1, x, 5.0)
for x in WIN_FRONT + [0.0]:
    win2('X', HD, 1, x, 5.0)
for sx_ in (-1, 1):
    for y in WIN_SIDE + [18.0]:
        win2('Y', sx_ * HW, sx_, y, 5.0)
# reloj grande al centro de la fachada (2o piso)
RC = Vector((0, -HD - 0.3, Z2 + 4.9))
cyl("Escuela_Techo_RelojMarco", (RC.x, RC.y, RC.z), 2.9, 0.5, M["blanco"], rot=(90, 0, 0), seg=48)
cyl("Escuela_Techo_RelojCara", (RC.x, RC.y - 0.28, RC.z), 2.5, 0.08, M["papel"], rot=(90, 0, 0), seg=48)
torus("Escuela_Techo_RelojAro", (RC.x, RC.y - 0.33, RC.z), 2.5, 0.1, M["puerta"], rot=(90, 0, 0))
for k in range(12):
    a = 2 * math.pi * k / 12
    box("Escuela_Techo_RelojMarca", (RC.x + 2.1 * math.sin(a), RC.y - 0.36, RC.z + 2.1 * math.cos(a)),
        (0.16, 0.05, 0.5 if k % 3 == 0 else 0.3), M["negro"], rot=(0, math.degrees(a), 0))
box("Escuela_Techo_RelojHoras", (RC.x + 0.45, RC.y - 0.42, RC.z + 0.4), (0.22, 0.05, 1.3), M["negro"], rot=(0, 45, 0))
box("Escuela_Techo_RelojMinutos", (RC.x, RC.y - 0.46, RC.z + 0.9), (0.14, 0.05, 1.9), M["negro"])
ball("Escuela_Techo_RelojCentro", (RC.x, RC.y - 0.5, RC.z), 0.18, M["dorado"])
# azotea
box("Escuela_Techo_Losa", (0, 0, ZT + 0.3), (2 * HW + 1.2, 2 * HD + 1.2, 0.6), M["techo"])
for sx_ in (-1, 1):
    box("Escuela_Techo_Pretil", (sx_ * (HW + 0.35), 0, ZT + 1.2), (0.7, 2 * HD + 1.4, 1.6), M["pared"])
for sy_ in (-1, 1):
    box("Escuela_Techo_Pretil", (0, sy_ * (HD + 0.35), ZT + 1.2), (2 * HW + 1.4, 0.7, 1.6), M["pared"])
box("Escuela_Techo_Remate", (0, -HD - 0.35, ZT + 2.1), (2 * HW + 1.6, 1.0, 0.25), M["blanco"])
box("Escuela_Techo_TinacoBase", (22, 10, ZT + 1.1), (4, 4, 1.0), M["concreto"])
cyl("Escuela_Techo_Tinaco", (22, 10, ZT + 3.0), 1.6, 2.8, M["negro"], seg=24)

# =================== FACHADA ===================
box("Escuela_Techo_Letrero", (0, -HD - 0.9, ZT + 3.2), (28, 0.5, 3.6), M["puerta"], bevel=0.1)
text("Escuela_Techo_LetreroTexto", "ESCUELA PRIMARIA", (0, -HD - 1.2, ZT + 3.6), 1.55, M["papel"])
text("Escuela_Techo_LetreroTexto2", "\"EL PUEBLO\"", (0, -HD - 1.2, ZT + 2.3), 0.95, M["amarillo"])
# marquesina de la entrada
box("Esc_Marquesina", (0, -HD - 3.0, 9.3), (11, 6.0, 0.5), M["blanco"])
for sx_ in (-1, 1):
    cyl("Esc_ColumnaEntrada", (sx_ * 4.8, -HD - 5.4, 4.95), 0.4, 8.7, M["blanco"])
# puertas de vidrio de la entrada
for sx_ in (-1, 1):
    box("Esc_PuertaEntradaMarco", (sx_ * 1.5, -HD, 4.6), (2.9, 0.35, 8.0), M["puerta"])
    box("Esc_PuertaEntradaVidrio", (sx_ * 1.5, -HD - 0.05, 4.9), (2.2, 0.4, 6.8), M["vidrio"])
    box("Esc_PuertaEntradaJaladera", (sx_ * 0.45, -HD - 0.4, 4.4), (0.12, 0.12, 2.2), M["plata"])
box("Esc_Rampa", (0, -HD - 2.5, 0.3), (8, 4.6, 0.6), M["concreto"])
box("Esc_Camino", (0, (-HD - 4.6 + SW_L) / 2, 0.05), (6, -HD - 4.6 - SW_L, 0.12), M["acera"])
# asta con bandera
cyl("Esc_AstaBase", (-12, -HD - 9, 0.4), 1.2, 0.8, M["concreto"])
cyl("Esc_Asta", (-12, -HD - 9, 13.0), 0.15, 25, M["plata"])
ball("Esc_AstaRemate", (-12, -HD - 9, 25.6), 0.3, M["dorado"])
if M["bandera"]:
    me = bpy.data.meshes.new("Esc_Bandera"); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=20, y_segments=10, size=0.5)
    for v in bm.verts:
        u = v.co.x + 0.5
        v.co = Vector((u * 5.0, 0.35 * math.sin(u * 7) * u, v.co.y * 3.0))
    bm.to_mesh(me); bm.free()
    obj("Esc_Bandera", me, (-11.85, -HD - 9, 23.4), M["bandera"], smooth=True)
# arbustos frente a la fachada
for x in [sd * _RC + d for sd in (-1, 1) for d in (-13.0, -4.5, 4.5, 13.0)]:
    ball("Esc_Arbusto", (x, -HD - 1.6, 1.0), 1.25, M["hojas"], 0.8)
# letrero de salida sobre la puerta trasera (dentro)
box("Esc_Salida", (0, HD - T / 2 - 0.2, 8.9), (2.6, 0.2, 0.9), M["salida"])
text("Esc_SalidaTexto", "SALIDA", (0, HD - T / 2 - 0.32, 8.9), 0.5, M["papel"], rot=(90, 0, 0))
box("Esc_PuertaTrasera", (0, HD, 4.3), (3.8, 0.3, 7.4), M["puerta"])
box("Esc_BarraAntipanico", (0, HD - 0.3, 4.2), (3.0, 0.15, 0.2), M["plata"])

# =================== MODELOS ===================
# locker (espalda en x=0, puerta mirando a +X)
LK = model("Esc_Locker_Modelo")
box("Locker_Cuerpo", (0.5, 0, 3.0), (1.0, 1.2, 6.0), M["locker"], col=LK, parent=None)
box("Locker_Junta", (1.01, 0.59, 3.0), (0.02, 0.03, 5.9), M["locker_osc"], col=LK, parent=None)
for k in range(4):
    box("Locker_Rejilla", (1.01, 0, 5.0 + k * 0.22), (0.04, 0.7, 0.1), M["locker_osc"], col=LK, parent=None)
    box("Locker_RejillaB", (1.01, 0, 0.6 + k * 0.22), (0.04, 0.7, 0.1), M["locker_osc"], col=LK, parent=None)
box("Locker_Manija", (1.06, -0.35, 3.0), (0.1, 0.12, 0.7), M["plata"], col=LK, parent=None)
box("Locker_Numero", (1.02, 0, 4.5), (0.03, 0.42, 0.22), M["plata"], col=LK, parent=None)
box("Locker_Zoclo", (0.5, 0, 0.12), (1.0, 1.2, 0.24), M["locker_osc"], col=LK, parent=None)


def pupitre(nm, chair_mat):
    c = model(nm)
    box("Pup_Cubierta", (0, 0, 2.7), (2.6, 1.9, 0.14), M["madera_clara"], col=c, parent=None, bevel=0.04)
    box("Pup_Canasta", (0, 0.1, 2.15), (2.3, 1.5, 0.08), M["metal"], col=c, parent=None)
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            box("Pup_Pata", (sx_ * 1.15, sy_ * 0.8, 1.32), (0.11, 0.11, 2.64), M["metal"], col=c, parent=None)
    box("Pup_Silla", (0, -1.95, 1.62), (2.0, 1.7, 0.14), chair_mat, col=c, parent=None, bevel=0.05)
    box("Pup_Respaldo", (0, -2.78, 2.75), (2.0, 0.14, 1.3), chair_mat, col=c, parent=None, bevel=0.05)
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            box("Pup_SillaPata", (sx_ * 0.85, -1.95 + sy_ * 0.7, 0.78), (0.1, 0.1, 1.56), M["metal"], col=c, parent=None)
        box("Pup_RespaldoTubo", (sx_ * 0.85, -2.72, 2.1), (0.1, 0.1, 1.2), M["metal"], col=c, parent=None)
    box("Pup_Cuaderno", (-0.4, -0.1, 2.8), (1.0, 1.3, 0.07), random.choice(COLORS), col=c, parent=None)
    box("Pup_Hoja", (-0.4, -0.1, 2.84), (0.85, 1.15, 0.02), M["papel"], col=c, parent=None)
    cyl("Pup_Lapiz", (0.6, -0.2, 2.82), 0.05, 1.0, M["amarillo"], rot=(90, 0, 25), col=c, parent=None, seg=6)
    return c


PUP_A = pupitre("Esc_PupitreAzul_Modelo", M["silla_azul"])
PUP_B = pupitre("Esc_PupitreNaranja_Modelo", M["silla_naranja"])

# =================== PASILLO ===================
lockers = 0
for side in (-1, 1):
    x = side * (HALL - TI / 2)
    y = -HD + T / 2 + 1.2
    while y < HD - T / 2 - 1.0:
        skip = abs(y - DOOR_Y) < 2.7 or (side > 0 and 6.5 < y < 13.5)
        if not skip:
            inst("Esc_Locker_%s%02d" % ("I" if side < 0 else "D", lockers), LK, (x, y, Z0), 0.0 if side < 0 else math.pi)
            lockers += 1
        y += 1.22
# vitrina de trofeos (lado derecho)
vx = HALL - TI / 2 - 0.75
box("Esc_VitrinaBase", (vx, 10, Z0 + 1.0), (1.5, 6.6, 2.0), M["madera"])
box("Esc_VitrinaVidrio", (vx, 10, Z0 + 4.0), (1.5, 6.6, 4.0), M["vidrio"])
box("Esc_VitrinaTecho", (vx, 10, Z0 + 6.1), (1.6, 6.8, 0.2), M["madera"])
for k, yy in enumerate((8.0, 10.0, 12.0)):
    cyl("Esc_TrofeoBase", (vx, yy, Z0 + 2.25), 0.35, 0.5, M["madera"])
    cyl("Esc_Trofeo", (vx, yy, Z0 + 2.95), 0.12, 0.9, M["dorado"])
    cyl("Esc_TrofeoCopa", (vx, yy, Z0 + 3.7), 0.5, 0.8, M["dorado"], r2=0.2)
    cyl("Esc_TrofeoAsa", (vx, yy, Z0 + 3.75), 0.62, 0.12, M["dorado"])
# tablero de avisos sobre los lockers
box("Esc_AvisosCorcho", (-(HALL - TI / 2) + 0.06, 2, 8.7), (0.1, 10, 3.2), M["corcho"])
box("Esc_AvisosMarco", (-(HALL - TI / 2) + 0.05, 2, 8.7), (0.08, 10.4, 3.6), M["madera"])
text("Esc_AvisosTitulo", "AVISOS", (-(HALL - TI / 2) + 0.14, 2, 9.85), 0.55, M["rojo"], rot=(90, 0, 90))
for k in range(7):
    box("Esc_AvisoHoja", (-(HALL - TI / 2) + 0.13, -2 + k * 1.3, 8.4 + random.uniform(-0.4, 0.3)), (0.03, 1.0, 1.3), random.choice([M["papel"], M["amarillo"], M["rosa"], M["azul"]]),
        rot=(random.uniform(-6, 6), 0, 0))
# letrero de bienvenida
box("Esc_Bienvenidos", ((HALL - TI / 2) - 0.06, -6, 9.2), (0.1, 9, 1.6), M["amarillo"])
text("Esc_BienvenidosTexto", "¡BIENVENIDOS!", ((HALL - TI / 2) - 0.14, -6, 9.2), 0.8, M["azul"], rot=(90, 0, -90))
# bebedero y bote en el fondo del pasillo
box("Esc_Bebedero", (-3.3, HD - T / 2 - 0.6, 3.0), (1.6, 1.0, 1.0), M["plata"])
box("Esc_BebederoPie", (-3.3, HD - T / 2 - 0.3, 1.8), (0.5, 0.4, 2.4), M["plata"])
cyl("Esc_BotePasillo", (3.4, HD - T / 2 - 0.9, Z0 + 1.2), 0.6, 2.4, M["azul"])
# reloj del pasillo y paneles de luz
cyl("Esc_RelojPasillo", (0, -HD + T / 2 + 0.1, 10.0), 0.8, 0.12, M["papel"], rot=(90, 0, 0), seg=32)
torus("Esc_RelojPasilloAro", (0, -HD + T / 2 + 0.14, 10.0), 0.8, 0.07, M["negro"], rot=(90, 0, 0))
for y in (-18, -6, 6, 18):
    for x in (-3.5, 3.5):
        box("Escuela_Techo_PanelLuzPasillo", (x, y, Z1 - 0.05), (2.4, 4.0, 0.08), M["luz"])
for y in (-14, 0, 14):
    L = bpy.data.lights.new("Esc_LuzPasillo", 'AREA'); L.energy = 900; L.size = 7; L.color = lin("#FFF4E5")[:3]
    lo = bpy.data.objects.new("Esc_LuzPasillo", L); lo.location = (0, y, Z1 - 0.3); COL.objects.link(lo); lo.parent = ROOT
# bancas del pasillo
for y in (-4, 4):
    box("Esc_BancaPasillo", (-(HALL - TI / 2) + 1.7, y + 0.5, 1.6), (1.1, 3.5, 0.2), M["madera"])
    for yy in (-1.2, 1.2):
        box("Esc_BancaPasilloPata", (-(HALL - TI / 2) + 1.7, y + 0.5 + yy, 1.05), (0.9, 0.15, 0.9), M["metal"])
# tapete central a lo largo del pasillo y macetas en la entrada
box("Esc_TapetePasillo", (0, 0, Z0 + 0.06), (4.2, 2 * HD - 8.0, 0.04), M["azul"])
for sx_ in (-1, 1):
    box("Esc_TapeteBorde", (sx_ * 2.0, 0, Z0 + 0.07), (0.22, 2 * HD - 8.0, 0.04), M["amarillo"])
    cyl("Esc_MacetaEntrada", (sx_ * 5.2, -HD + T / 2 + 1.6, Z0 + 0.9), 0.85, 1.8, M["maceta"])
    ball("Esc_PlantaEntrada", (sx_ * 5.2, -HD + T / 2 + 1.6, Z0 + 2.9), 1.3, M["hojas"], 1.2)

# =================== SALONES ===================
def salon(idx, cx, side, pup, board_title, board_lines, accent):
    """side: -1 salon izquierdo, +1 derecho. El pizarron esta en el muro del fondo (y=+HD)."""
    inner_x = cx + side * 0.0
    wall_hall = side * (HALL + TI / 2)          # cara del muro del pasillo que da al salon
    wall_out = side * (HW - T / 2)              # cara interior del muro lateral
    by = HD - T / 2                             # cara interior del muro del fondo
    fy = -HD + T / 2                            # cara interior del muro del frente
    tag = "Salon%d_" % idx
    # pizarron
    box(tag + "PizarronMarco", (cx, by - 0.12, 6.0), (17.0, 0.2, 5.8), M["madera"])
    box(tag + "Pizarron", (cx, by - 0.24, 6.0), (16.2, 0.1, 5.0), M["pizarron"])
    box(tag + "Repisa", (cx, by - 0.5, 3.35), (16.6, 0.6, 0.15), M["madera"])
    for k in range(4):
        cyl(tag + "Gis", (cx - 6 + k * 0.6, by - 0.5, 3.47), 0.06, 0.45, random.choice([M["tiza"], M["amarillo"], M["rosa"]]), rot=(0, 90, 0), seg=6)
    box(tag + "Borrador", (cx + 5.5, by - 0.5, 3.55), (1.0, 0.45, 0.28), M["negro"])
    text(tag + "PizarronTitulo", board_title, (cx, by - 0.32, 7.6), 0.95, M["tiza"], rot=(90, 0, 0))
    for k, ln in enumerate(board_lines):
        text(tag + "PizarronTexto", ln, (cx, by - 0.32, 6.3 - k * 1.1), 0.7, M["tiza"], rot=(90, 0, 0))
    # abecedario sobre el pizarron
    for k, ch in enumerate("ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"):
        x = cx - 13.0 + k * 1.0
        box(tag + "Letra", (x, by - 0.06, 10.0), (0.85, 0.05, 0.95), COLORS[k % len(COLORS)])
        text(tag + "LetraTexto", ch, (x, by - 0.1, 10.0), 0.6, M["papel"], rot=(90, 0, 0))
    # reloj de pared
    cyl(tag + "Reloj", (cx + side * 11.5, by - 0.1, 8.3), 1.0, 0.15, M["papel"], rot=(90, 0, 0), seg=32)
    torus(tag + "RelojAro", (cx + side * 11.5, by - 0.17, 8.3), 1.0, 0.09, M["negro"], rot=(90, 0, 0))
    box(tag + "RelojMinutero", (cx + side * 11.5, by - 0.2, 8.6), (0.08, 0.04, 0.7), M["negro"])
    box(tag + "RelojHorario", (cx + side * 11.5 + 0.2, by - 0.2, 8.3), (0.45, 0.04, 0.09), M["negro"])
    # calendario
    box(tag + "Calendario", (cx - side * 11.5, by - 0.06, 7.6), (2.6, 0.05, 3.0), M["papel"])
    box(tag + "CalendarioTop", (cx - side * 11.5, by - 0.08, 8.85), (2.6, 0.05, 0.5), M["rojo"])
    for r in range(4):
        for c in range(5):
            box(tag + "CalDia", (cx - side * 11.5 - 1.0 + c * 0.5, by - 0.09, 8.2 - r * 0.6), (0.35, 0.03, 0.4), M["papel"] if (r + c) % 6 else M["amarillo"])
    # escritorio del maestro (mirando a los alumnos)
    tx, ty = cx - side * 4.5, by - 6.6
    box(tag + "EscritorioTapa", (tx, ty, 3.0), (6.5, 3.0, 0.2), M["madera"], bevel=0.05)
    box(tag + "EscritorioFrente", (tx, ty - 1.35, 1.8), (6.4, 0.15, 2.3), M["madera"])
    for s in (-1, 1):
        box(tag + "EscritorioLado", (tx + s * 3.0, ty, 1.8), (0.2, 2.9, 2.4), M["madera"])
    box(tag + "Cajonera", (tx + 2.0, ty, 1.8), (2.0, 2.6, 2.3), M["madera_clara"])
    for z in (1.2, 2.3):
        box(tag + "CajonManija", (tx + 2.0, ty + 1.32, z), (0.6, 0.06, 0.1), M["plata"])
    box(tag + "SillaMaestro", (tx, ty + 2.4, 1.7), (2.0, 1.9, 0.2), M["negro"])
    box(tag + "SillaMaestroResp", (tx, ty + 3.3, 3.1), (2.0, 0.2, 2.4), M["negro"])
    cyl(tag + "SillaMaestroPie", (tx, ty + 2.4, 0.9), 0.12, 1.5, M["metal"])
    ball(tag + "Manzana", (tx - 2.2, ty - 0.4, 3.4), 0.3, M["rojo"])
    cyl(tag + "ManzanaRabo", (tx - 2.2, ty - 0.4, 3.75), 0.03, 0.2, M["madera"], seg=6)
    for k in range(4):
        box(tag + "Libro", (tx - 0.6, ty + 0.2, 3.2 + k * 0.22), (1.4, 1.0, 0.2), COLORS[(k + idx) % 6], rot=(0, 0, random.uniform(-8, 8)))
    cyl(tag + "Lapicero", (tx + 1.0, ty - 0.6, 3.45), 0.25, 0.7, M["azul"])
    for k in range(4):
        cyl(tag + "LapiceroLapiz", (tx + 1.0 + random.uniform(-0.1, 0.1), ty - 0.6 + random.uniform(-0.1, 0.1), 3.95), 0.04, 0.8, random.choice(COLORS), rot=(random.uniform(-10, 10), random.uniform(-10, 10), 0), seg=6)
    # globo terraqueo
    cyl(tag + "GloboBase", (tx + 2.3, ty + 0.4, 3.2), 0.4, 0.2, M["madera"])
    cyl(tag + "GloboEje", (tx + 2.3, ty + 0.4, 3.75), 0.04, 1.0, M["dorado"])
    ball(tag + "Globo", (tx + 2.3, ty + 0.4, 4.15), 0.6, M["globo"])
    torus(tag + "GloboAro", (tx + 2.3, ty + 0.4, 4.15), 0.68, 0.035, M["dorado"], rot=(70, 0, 0))
    # pupitres: 4 columnas x 3 filas, bien separados, mirando al pizarron
    n = 0
    for r, yy in enumerate((by - 29.0, by - 21.0, by - 13.0)):
        for c, dx in enumerate((-9.0, -3.0, 3.0, 9.0)):
            inst(tag + "Pupitre_%02d" % (n + 1), pup, (cx + dx, yy, Z0), 0.0)
            n += 1
    # rincon de lectura al fondo: alfombra redonda, puffs y canasta de libros
    rx_, ry_ = cx + side * 8.0, fy + 4.4
    cyl(tag + "Alfombra", (rx_, ry_, Z0 + 0.06), 2.7, 0.06, M["amarillo"], seg=40)
    torus(tag + "AlfombraBorde", (rx_, ry_, Z0 + 0.08), 2.55, 0.08, M["rojo"])
    cyl(tag + "AlfombraCentro", (rx_, ry_, Z0 + 0.1), 1.1, 0.03, M["azul"], seg=32)
    for k, ang in enumerate((200, 270, 340)):
        a = math.radians(ang + (0 if side < 0 else 180))
        ball(tag + "Puff", (rx_ + 1.9 * math.cos(a), ry_ + 1.9 * math.sin(a), Z0 + 0.65), 0.95, [M["morado"], M["verde"], M["rosa"]][k], 0.6)
    box(tag + "CanastaLibros", (rx_ - side * 2.6, ry_ + 1.6, Z0 + 0.55), (1.4, 1.0, 0.9), M["madera_clara"])
    for k in range(4):
        box(tag + "CanastaLibro", (rx_ - side * 2.6 - 0.45 + k * 0.3, ry_ + 1.6, Z0 + 1.15), (0.22, 0.8, 0.9), COLORS[(k + idx) % 6])
    # librero con libros (esquina junto al muro lateral)
    lx = wall_out - side * 0.9
    LBY = by - 6.1
    box(tag + "Librero", (lx, 13.5, 3.6), (1.8, 7.0, 6.0), M["madera"])
    for lvl in range(4):
        z = Z0 + 0.5 + lvl * 1.45
        box(tag + "LibreroEntrepano", (lx - side * 0.05, LBY, z), (1.6, 6.6, 0.12), M["madera_clara"])
        yb = LBY - 3.1
        while yb < LBY + 2.9:
            wbk = random.uniform(0.25, 0.45); hbk = random.uniform(0.9, 1.25)
            box(tag + "LibroEstante", (lx - side * 0.1, yb + wbk / 2, z + hbk / 2 + 0.06), (1.2, wbk, hbk), random.choice(COLORS))
            yb += wbk + 0.04
    # casilleros de colores bajo las ventanas del frente
    for k in range(3):
        bx = cx + (-9 + k * 9)
        box(tag + "Cubby", (bx, fy + 0.9, 1.9), (6.0, 1.6, 2.6), M["madera_clara"])
        for j in range(4):
            box(tag + "CubbyCaja", (bx - 2.25 + j * 1.5, fy + 1.75, 1.9), (1.2, 0.2, 1.0), COLORS[(j + k) % 6])
    # macetas en las repisas interiores de las ventanas laterales
    for y in WIN_SIDE:
        px = wall_out - side * 0.55
        cyl(tag + "Maceta", (px, y, WZ[0] + 0.3), 0.32, 0.6, M["maceta"])
        ball(tag + "Planta", (px, y, WZ[0] + 0.95), 0.5, M["hojas"], 1.1)
    # tablero de corcho con trabajos (muro del pasillo)
    box(tag + "Corcho", (wall_hall + side * 0.06, 2.0, 6.4), (0.08, 12, 4.0), M["corcho"])
    box(tag + "CorchoMarco", (wall_hall + side * 0.05, 2.0, 6.4), (0.06, 12.4, 4.4), M["madera"])
    text(tag + "CorchoTitulo", "NUESTROS TRABAJOS", (wall_hall + side * 0.12, 2.0, 7.95), 0.45, accent, rot=(90, 0, 90 * side))
    for k in range(8):
        yy = -3.0 + (k % 4) * 2.6
        zz = 6.8 - (k // 4) * 1.8
        box(tag + "Dibujo", (wall_hall + side * 0.12, yy, zz), (0.03, 1.8, 1.4), M["papel"], rot=(random.uniform(-5, 5), 0, 0))
        ball(tag + "DibujoSol", (wall_hall + side * 0.15, yy + 0.4, zz + 0.25), 0.25, random.choice([M["amarillo"], M["rojo"], M["azul"]]), 0.15)
        box(tag + "DibujoPasto", (wall_hall + side * 0.15, yy, zz - 0.5), (0.02, 1.6, 0.25), M["verde"])
    # carteles entre ventanas del muro lateral
    px = wall_out - side * 0.06
    box(tag + "CartelPlanetas", (px, -13.5, 6.6), (0.05, 3.0, 3.6), M["negro"])
    for k, (r_, m_) in enumerate(((0.45, M["amarillo"]), (0.18, M["rojo"]), (0.25, M["azul"]), (0.35, M["rosa"]), (0.22, M["verde"]))):
        ball(tag + "Planeta", (px - side * 0.05, -14.6 + k * 0.6, 6.6 + 0.4 * math.sin(k * 1.7)), r_, m_, 0.3)
    text(tag + "CartelPlanetasTxt", "PLANETAS", (px - side * 0.06, -13.5, 8.0), 0.35, M["papel"], rot=(90, 0, -90 * side))
    box(tag + "CartelReglas", (px, -4.5, 6.6), (0.05, 3.0, 3.8), M["papel"])
    text(tag + "CartelReglasTxt", "REGLAS", (px - side * 0.06, -4.5, 8.0), 0.45, M["rojo"], rot=(90, 0, -90 * side))
    for k in range(4):
        box(tag + "CartelRegla", (px - side * 0.05, -4.5, 7.3 - k * 0.6), (0.02, 2.2, 0.15), COLORS[k])
    # mapa del mundo en el muro del frente (entre ventanas)
    mx_ = cx - 4.5
    box(tag + "MapaMundi", (mx_, fy + 0.06, 7.0), (3.4, 0.05, 2.4), M["azul"])
    for k in range(5):
        ball(tag + "Continente", (mx_ - 1.2 + k * 0.6, fy + 0.1, 7.0 + random.uniform(-0.6, 0.6)), random.uniform(0.25, 0.45), M["verde"], 0.2)
    # bote de basura y perchero junto a la puerta
    cyl(tag + "BoteBasura", (wall_hall + side * 1.2, DOOR_Y + 3.0, Z0 + 0.9), 0.55, 1.8, M["verde"])
    box(tag + "Perchero", (wall_hall + side * 0.1, DOOR_Y - 4.0, 6.4), (0.1, 4.0, 0.3), M["madera"])
    for k in range(5):
        cyl(tag + "Gancho", (wall_hall + side * 0.35, DOOR_Y - 5.6 + k * 0.8, 6.3), 0.06, 0.5, M["plata"], rot=(0, 90, 0), seg=6)
        if k % 2 == 0:
            box(tag + "Mochila", (wall_hall + side * 0.65, DOOR_Y - 5.6 + k * 0.8, 5.5), (0.7, 0.75, 1.3), random.choice(COLORS), bevel=0.15)
    # puerta del salon (abierta) con marco
    hinge = (wall_hall, DOOR_Y - 1.8)
    pv = bpy.data.objects.new(tag + "PuertaBisagra", None); pv.location = (hinge[0] - side * 0.1, hinge[1], Z0); COL.objects.link(pv); pv.parent = ROOT
    pv.rotation_euler = (0, 0, math.radians(-70 * side))
    d = box(tag + "Puerta", (0, 1.75, 3.6), (0.18, 3.5, 7.2), M["puerta"], parent=pv)
    box(tag + "PuertaVentanita", (0, 1.75, 5.3), (0.22, 1.2, 1.6), M["vidrio"], parent=pv)
    box(tag + "PuertaManija", (side * 0.18, 3.1, 3.6), (0.12, 0.5, 0.12), M["plata"], parent=pv)
    for s in (-1, 1):
        box(tag + "PuertaMarco", (side * HALL, DOOR_Y + s * 1.9, 4.2), (TI + 0.2, 0.25, 7.2), M["blanco"])
    box(tag + "PuertaMarcoSup", (side * HALL, DOOR_Y, 7.9), (TI + 0.2, 4.05, 0.25), M["blanco"])
    text(tag + "PuertaNumero", "SALÓN %d" % idx, (side * HALL - side * (TI / 2 + 0.12), DOOR_Y, 8.6), 0.45, M["azul"], rot=(90, 0, -90 * side))
    # luces del techo
    for xx in (-6.5, 6.5):
        for yy in (-18, -6, 6, 18):
            box("Escuela_Techo_PanelLuz", (cx + xx, yy, Z1 - 0.05), (2.4, 4.0, 0.08), M["luz"])
    for yy in (-14, 0, 14):
        L = bpy.data.lights.new(tag + "Luz", 'AREA'); L.energy = 2200; L.shape = 'RECTANGLE'; L.size = 12; L.size_y = 9
        L.color = lin("#FFF4E5")[:3]
        lo = bpy.data.objects.new(tag + "Luz", L); lo.location = (cx, yy, Z1 - 0.3); COL.objects.link(lo); lo.parent = ROOT


salon(1, ROOM_C[0], -1, PUP_A, "MATEMÁTICAS", ["2 + 3 = 5", "4 x 2 = 8", "10 - 7 = 3"], M["rojo"])
salon(2, ROOM_C[1], 1, PUP_B, "ESPAÑOL", ["El sol brilla.", "Mi casa es azul.", "Hoy es lunes."], M["azul"])

# =================== CANCHA (grande y detallada) ===================
def mk_fence():
    """malla ciclonica: rombos con alpha"""
    m, nt, b = base_mat("Esc_Malla")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    lines = []
    for op in ('ADD', 'SUBTRACT'):
        a = nt.nodes.new("ShaderNodeMath"); a.operation = op
        nt.links.new(sx.outputs[0], a.inputs[0]); nt.links.new(sx.outputs[1], a.inputs[1])
        ml = nt.nodes.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = 1.6
        nt.links.new(a.outputs[0], ml.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; nt.links.new(ml.outputs[0], fr.inputs[0])
        sb = nt.nodes.new("ShaderNodeMath"); sb.operation = 'SUBTRACT'; sb.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], sb.inputs[0])
        ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(sb.outputs[0], ab.inputs[0])
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.43
        nt.links.new(ab.outputs[0], gt.inputs[0]); lines.append(gt)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
    nt.links.new(lines[0].outputs[0], mx.inputs[0]); nt.links.new(lines[1].outputs[0], mx.inputs[1])
    nt.links.new(mx.outputs[0], b.inputs["Alpha"])
    b.inputs["Base Color"].default_value = lin("#9DA4AB"); b.inputs["Metallic"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.4
    m.surface_render_method = 'DITHERED'; m.use_backface_culling = False
    return m


M["malla"] = mk_fence()
M["cancha_azul"] = mk("Esc_CanchaAzul", "#2B5FA6", 0.75, 3, 0.08)
M["cancha_rojo"] = mk("Esc_CanchaRojo", "#A8463A", 0.85, 3, 0.1)
M["grada"] = mk("Esc_GradaMetal", "#9AA3AD", 0.4, 5, 0.06, metal=0.6)
M["tablero"] = mk("Esc_Tablero", "#F4F6F8", 0.2, 3, 0.02, alpha=0.75)
M["foco"] = mk("Esc_Reflector", "#FFFFFF", 0.2, 2, 0.01, emit="#FFF6E0", es=10)
M["led_rojo"] = mk("Esc_LedRojo", "#FF3B30", 0.4, 2, 0.01, emit="#FF3B30", es=5)
M["led_amarillo"] = mk("Esc_LedAmarillo", "#FFD23F", 0.4, 2, 0.01, emit="#FFD23F", es=5)


def plane(name, loc, sx, sy, m, rot):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0)], [], [(0, 1, 2, 3)])
    return obj(name, me, loc, m, rot)


def arc(name, cx, cy, r, w, a0, a1, z, m, seg=48, fill=False):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    angs = [a0 + (a1 - a0) * i / seg for i in range(seg + 1)]
    if fill:
        c = bm.verts.new((0, 0, 0))
        ring = [bm.verts.new((r * math.cos(a), r * math.sin(a), 0)) for a in angs]
        for i in range(seg):
            bm.faces.new((c, ring[i], ring[i + 1]))
    else:
        inn = [bm.verts.new(((r - w / 2) * math.cos(a), (r - w / 2) * math.sin(a), 0)) for a in angs]
        out = [bm.verts.new(((r + w / 2) * math.cos(a), (r + w / 2) * math.sin(a), 0)) for a in angs]
        for i in range(seg):
            bm.faces.new((inn[i], out[i], out[i + 1], inn[i + 1]))
    bm.to_mesh(me); bm.free()
    return obj(name, me, (cx, cy, z), m)


PX0 = HW + 5.0
PX1, PY = PX0 + 54.0, 34.0              # plataforma (local)
CCX, CHL, CHW = PX0 + 21.0, 28.0, 17.0  # centro, medio largo y medio ancho de la duela
ZB = 0.3
ZL = ZB + 0.09
box("Esc_CanchaBase", ((PX0 + PX1) / 2, 0, ZB / 2), (PX1 - PX0, 2 * PY, ZB), M["concreto"])
box("Esc_CanchaMargen", (CCX, 0, ZB + 0.02), (2 * CHW + 4, 2 * CHL + 4, 0.04), M["cancha_rojo"])
box("Esc_CanchaPiso", (CCX, 0, ZB + 0.05), (2 * CHW, 2 * CHL, 0.04), M["cancha"])


def strip(x, y, sx_, sy_):
    box("Esc_CanchaLinea", (x, y, ZL), (sx_, sy_, 0.02), M["linea_blanca"])


strip(CCX, -CHL, 2 * CHW + 0.3, 0.3); strip(CCX, CHL, 2 * CHW + 0.3, 0.3)
strip(CCX - CHW, 0, 0.3, 2 * CHL); strip(CCX + CHW, 0, 0.3, 2 * CHL)
strip(CCX, 0, 2 * CHW, 0.3)
arc("Esc_CanchaCirculoRelleno", CCX, 0, 3.6, 0, 0, 2 * math.pi, ZB + 0.075, M["cancha_azul"], fill=True)
arc("Esc_CanchaCirculo", CCX, 0, 3.6, 0.3, 0, 2 * math.pi, ZL + 0.005, M["linea_blanca"])
text("Esc_CanchaLogo", "EP", (CCX, 0, ZL + 0.02), 2.0, M["linea_blanca"], rot=(0, 0, -90), extrude=0.0)
for s in (-1, 1):
    by, hoop_y, ft_y = s * CHL, s * (CHL - 1.6), s * (CHL - 11.6)
    box("Esc_CanchaPintura", (CCX, (by + ft_y) / 2, ZB + 0.075), (7.6, 11.6, 0.02), M["cancha_azul"])
    strip(CCX - 3.8, (by + ft_y) / 2, 0.3, 11.6); strip(CCX + 3.8, (by + ft_y) / 2, 0.3, 11.6); strip(CCX, ft_y, 7.9, 0.3)
    a0 = 0.0 if s < 0 else math.pi
    arc("Esc_CanchaTiroLibre", CCX, ft_y, 3.6, 0.3, a0, a0 + math.pi, ZL, M["linea_blanca"])
    arc("Esc_CanchaTriple", CCX, hoop_y, 14.0, 0.3, a0, a0 + math.pi, ZL, M["linea_blanca"], seg=72)
    for sx_ in (-1, 1):
        strip(CCX + sx_ * 14.0, (by + hoop_y) / 2, 0.3, abs(by - hoop_y))
    # tablero, aro y red
    pole_y = s * (CHL + 2.8)
    box("Esc_AroLastre", (CCX, pole_y + s * 0.6, ZB + 0.5), (2.4, 2.6, 1.0), M["metal"])
    cyl("Esc_AroPoste", (CCX, pole_y, ZB + 6.2), 0.32, 12.4, M["metal"])
    cyl("Esc_AroAcolchado", (CCX, pole_y, ZB + 3.0), 0.6, 5.0, M["azul"])
    bb_y = s * (CHL - 0.5)
    box("Esc_AroBrazo", (CCX, (pole_y + bb_y) / 2, ZB + 11.2), (0.4, abs(pole_y - bb_y), 0.4), M["metal"])
    box("Esc_AroBrazoDiag", (CCX, (pole_y + bb_y) / 2, ZB + 10.0), (0.25, abs(pole_y - bb_y) * 1.05, 0.25), M["metal"],
        rot=(s * 25, 0, 0))
    box("Esc_Tablero", (CCX, bb_y, ZB + 11.2), (6.0, 0.15, 3.6), M["tablero"])
    for (dx, dz, sx_, sz_) in ((0, 1.75, 6.1, 0.18), (0, -1.75, 6.1, 0.18), (-3.0, 0, 0.18, 3.6), (3.0, 0, 0.18, 3.6),
                               (0, 0.75, 2.0, 0.12), (0, -0.55, 2.0, 0.12), (-1.0, 0.1, 0.12, 1.4), (1.0, 0.1, 0.12, 1.4)):
        box("Esc_TableroLinea", (CCX + dx, bb_y - s * 0.1, ZB + 11.2 + dz), (sx_, 0.04, sz_), M["rojo"] if abs(dz) < 1 else M["blanco"])
    rim_z = ZB + 10.0
    box("Esc_AroSoporte", (CCX, (bb_y + hoop_y) / 2, rim_z), (0.4, abs(bb_y - hoop_y) - 0.6, 0.15), M["naranja"])
    torus("Esc_Aro", (CCX, hoop_y, rim_z), 0.75, 0.07, M["naranja"])
    me = bpy.data.meshes.new("Esc_Red"); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=12, radius1=0.45, radius2=0.72, depth=1.4)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5], cuts=3)
    for v in bm.verts:   # trenzado
        a = math.atan2(v.co.y, v.co.x) + (v.co.z + 0.7) * 0.5
        r = math.hypot(v.co.x, v.co.y)
        v.co.x, v.co.y = r * math.cos(a), r * math.sin(a)
    bm.to_mesh(me); bm.free()
    net = obj("Esc_Red", me, (CCX, hoop_y, rim_z - 0.72), M["linea_blanca"])
    wf = net.modifiers.new("Malla", 'WIREFRAME'); wf.thickness = 0.04
# gradas de 4 niveles mirando a la cancha
GX = PX1 - 12.0
for k in range(4):
    x = GX + k * 2.1
    z = ZB + 1.1 + k * 1.3
    box("Esc_GradaEscalon", (x, 0, (ZB + z) / 2), (2.1, 34, z - ZB), M["grada"])
    box("Esc_GradaAsiento", (x - 0.25, 0, z + 0.14), (1.5, 34, 0.28), M["madera_clara"], bevel=0.05)
top_z = ZB + 1.1 + 3 * 1.3
for y in range(-17, 18, 5):
    cyl("Esc_GradaBarandalPoste", (GX + 3 * 2.1 + 1.0, y, top_z + 1.6), 0.09, 3.2, M["metal"], seg=8)
cyl("Esc_GradaBarandal", (GX + 3 * 2.1 + 1.0, 0, top_z + 3.1), 0.1, 34, M["metal"], rot=(90, 0, 0), seg=8)
# bancas de los equipos con hielera y toallas
for s in (-1, 1):
    y0 = s * 9.0
    box("Esc_BancaEquipo", (GX - 2.6, y0, ZB + 1.5), (1.3, 7.0, 0.25), M["azul"], bevel=0.05)
    box("Esc_BancaEquipoResp", (GX - 2.0, y0, ZB + 2.6), (0.2, 7.0, 1.6), M["azul"], bevel=0.05)
    for yy in (-3, 3):
        box("Esc_BancaEquipoPata", (GX - 2.6, y0 + yy, ZB + 0.7), (1.1, 0.2, 1.4), M["metal"])
    cyl("Esc_Hielera", (GX - 2.6, y0 + s * 2.6, ZB + 2.25), 0.5, 1.2, M["naranja"])
    cyl("Esc_HieleraTapa", (GX - 2.6, y0 + s * 2.6, ZB + 2.9), 0.52, 0.15, M["papel"])
    box("Esc_Toalla", (GX - 2.6, y0 - s * 1.5, ZB + 1.7), (1.0, 1.2, 0.08), M["papel"])
# reflectores en las 4 esquinas
for (x, y) in ((PX0 + 1.5, -PY + 1.5), (PX0 + 1.5, PY - 1.5), (PX1 - 1.5, -PY + 1.5), (PX1 - 1.5, PY - 1.5)):
    cyl("Esc_ReflectorPoste", (x, y, ZB + 11), 0.3, 22, M["metal"])
    d = Vector((CCX - x, -y, 0)).normalized()
    ang = math.degrees(math.atan2(d.y, d.x)) - 90
    hd = box("Esc_ReflectorCabeza", (x + d.x * 0.6, y + d.y * 0.6, ZB + 22.3), (3.4, 0.6, 2.0), M["metal"], rot=(-20, 0, ang))
    for i in range(2):
        for j in range(2):
            loc_ = Vector((x + d.x * 0.95, y + d.y * 0.95, ZB + 22.3)) + Vector((-d.y, d.x, 0)) * (-0.8 + i * 1.6)
            box("Esc_ReflectorFoco", (loc_.x, loc_.y, ZB + 21.85 + j * 0.9), (1.2, 0.08, 0.7), M["foco"], rot=(-20, 0, ang))
    L = bpy.data.lights.new("Esc_LuzCancha", 'SPOT'); L.energy = 3500; L.spot_size = math.radians(75); L.spot_blend = 0.5
    L.color = lin("#FFF4E0")[:3]
    lo = bpy.data.objects.new("Esc_LuzCancha", L); lo.location = (x + d.x * 1.2, y + d.y * 1.2, ZB + 21.5)
    lo.rotation_euler = (Vector((CCX, 0, 0)) - Vector(lo.location)).to_track_quat('-Z', 'Y').to_euler()
    COL.objects.link(lo); lo.parent = ROOT
# marcador detras de un aro
SBY = PY - 1.0
for sx_ in (-1, 1):
    cyl("Esc_MarcadorPoste", (CCX + sx_ * 5.0, SBY, ZB + 8.5), 0.25, 17, M["metal"])
box("Esc_Marcador", (CCX, SBY, ZB + 16.5), (11.0, 0.8, 4.6), M["negro"], bevel=0.1)
box("Esc_MarcadorMarco", (CCX, SBY + 0.05, ZB + 16.5), (11.4, 0.7, 5.0), M["azul"])
for (body, x, z, sz, m) in (("LOCAL", -3.2, 18.0, 0.7, M["papel"]), ("VISITA", 3.2, 18.0, 0.7, M["papel"]),
                            ("24", -3.2, 16.1, 1.8, M["led_rojo"]), ("18", 3.2, 16.1, 1.8, M["led_rojo"]),
                            ("4°", 0, 17.4, 0.9, M["led_amarillo"]), ("2:35", 0, 15.6, 0.8, M["led_amarillo"])):
    text("Esc_MarcadorTexto", body, (CCX + x, SBY - 0.45, ZB + z), sz, m)
# malla perimetral con puerta hacia la calle
FH = 7.0
def fence_run(axis, fixed, a, b):
    L_ = b - a
    if L_ <= 0.1:
        return
    c = (a + b) / 2
    if axis == 'X':
        plane("Esc_Malla", (c, fixed, ZB + FH / 2), L_, FH, M["malla"], (90, 0, 0))
        cyl("Esc_MallaTubo", (c, fixed, ZB + FH), 0.08, L_, M["metal"], rot=(0, 90, 0), seg=8)
        cyl("Esc_MallaTubo", (c, fixed, ZB + 0.3), 0.06, L_, M["metal"], rot=(0, 90, 0), seg=8)
    else:
        plane("Esc_Malla", (fixed, c, ZB + FH / 2), L_, FH, M["malla"], (90, 0, 90))
        cyl("Esc_MallaTubo", (fixed, c, ZB + FH), 0.08, L_, M["metal"], rot=(90, 0, 0), seg=8)
        cyl("Esc_MallaTubo", (fixed, c, ZB + 0.3), 0.06, L_, M["metal"], rot=(90, 0, 0), seg=8)
    n_ = max(1, int(L_ / 6.5))
    for i in range(n_ + 1):
        u = a + L_ * i / n_
        p = (u, fixed) if axis == 'X' else (fixed, u)
        cyl("Esc_MallaPoste", (p[0], p[1], ZB + FH / 2), 0.13, FH + 0.3, M["metal"], seg=10)


GATE = (PX0 + 10.0, PX0 + 17.0)
fence_run('X', -PY, PX0, GATE[0]); fence_run('X', -PY, GATE[1], PX1)
fence_run('X', PY, PX0, PX1)
fence_run('Y', PX0, -PY, PY); fence_run('Y', PX1, -PY, PY)
box("Esc_CaminoCancha", ((GATE[0] + GATE[1]) / 2, (-PY + SW_L) / 2, 0.05), (GATE[1] - GATE[0] - 1, -PY - SW_L, 0.12), M["acera"])
# equipo de entrenamiento
BRX, BRY = GX - 3.0, 21.0
for sx_ in (-1, 1):
    box("Esc_PorteBalonesLado", (BRX + sx_ * 0.0, BRY + sx_ * 2.0, ZB + 1.6), (1.2, 0.15, 3.2), M["metal"])
for z in (1.0, 2.4):
    box("Esc_PorteBalonesNivel", (BRX, BRY, ZB + z), (1.2, 4.0, 0.12), M["metal"])
    for k in range(3):
        ball("Esc_Balon", (BRX, BRY - 1.3 + k * 1.3, ZB + z + 0.6), 0.55, M["naranja"])
for k in range(6):                       # conos en zigzag
    x, y = CCX + (-4 if k % 2 == 0 else 4), 4.0 + k * 2.2
    cyl("Esc_Cono", (x, y, ZB + 0.5), 0.4, 0.9, M["naranja"], r2=0.06, seg=12)
    box("Esc_ConoBase", (x, y, ZB + 0.12), (0.9, 0.9, 0.1), M["naranja"])
    torus("Esc_ConoFranja", (x, y, ZB + 0.6), 0.27, 0.05, M["papel"])
for k in range(10):                      # escalera de agilidad
    box("Esc_EscaleraPeldano", (CCX + 9.0, -14.0 + k * 0.9, ZL + 0.01), (1.4, 0.12, 0.03), M["amarillo"])
for sx_ in (-1, 1):
    box("Esc_EscaleraCinta", (CCX + 9.0 + sx_ * 0.7, -14.0 + 4.05, ZL + 0.01), (0.1, 8.4, 0.03), M["amarillo"])
for k in range(3):                       # mini vallas
    y = -6.0 - k * 3.0
    for sx_ in (-1, 1):
        box("Esc_VallaPata", (CCX - 9.0 + sx_ * 0.9, y, ZB + 0.5), (0.12, 0.12, 0.9), M["amarillo"])
    box("Esc_VallaBarra", (CCX - 9.0, y, ZB + 0.92), (1.9, 0.12, 0.12), M["amarillo"])
for (x, y) in ((CCX + 2.5, -3.0), (CCX - 6.0, 10.0), (CCX + 12.0, 18.0)):
    ball("Esc_Balon", (x, y, ZB + 0.6), 0.55, M["naranja"])

# =================== LIMPIAR ARBOLES EN EL TERRENO ===================
_c, _s = math.cos(RZ), math.sin(RZ)
_pts = [S + Vector((x * _c - y * _s, x * _s + y * _c, 0)) for x in (-HW - 12, PX1 + 6) for y in (SW_L + 2, max(PY, HD) + 10)]
xmin, xmax = min(p.x for p in _pts), max(p.x for p in _pts)
ymin, ymax = min(p.y for p in _pts), max(p.y for p in _pts)
removed = 0
for o in list(bpy.data.objects):
    if o.instance_type == 'COLLECTION' and o.instance_collection and o.instance_collection.name in ("Pino_Modelo", "Arbol_Modelo"):
        if xmin < o.location.x < xmax and ymin < o.location.y < ymax:
            bpy.data.objects.remove(o); removed += 1

# modelos ocultos
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == "Escuela_Modelos":
        lc.exclude = True

# =================== CAMARAS DE PRUEBA ===================
CAMS = bpy.data.collections.get("Camaras_Centro") or COL


def cam(name, loc, target, fov):
    o = bpy.data.objects.get(name)
    if o is None:
        cd = bpy.data.cameras.new(name); cd.sensor_fit = 'VERTICAL'
        o = bpy.data.objects.new(name, cd); CAMS.objects.link(o)
    o.data.clip_end = 4000; o.data.clip_start = 0.1; o.data.angle_y = math.radians(fov)
    def w(v):   # local de la escuela -> mundo
        v = Vector(v); c, s_ = math.cos(RZ), math.sin(RZ)
        return S + Vector((v.x * c - v.y * s_, v.x * s_ + v.y * c, v.z))
    o.location = w(loc)
    o.rotation_euler = (w(target) - o.location).to_track_quat('-Z', 'Y').to_euler()


cam("Cam_EscuelaFrente", (34, -80, 16), (0, 0, 11), 42)
cam("Cam_Cancha", (PX0 + 56, -78, 44), (PX0 + 26, -2, 2), 45)
cam("Cam_CanchaPiso", (PX0 + 10, -24, 5.5), (CCX, 20, 8.5), 58)
cam("Cam_EscuelaCorte", (0, -72, 86), (0, 0, 0), 50)
cam("Cam_EscuelaPasillo", (2.0, -HD + 1.8, 5.6), (0, 14, 4.6), 62)
cam("Cam_Salon1", (-(HW - 2.0), -HD + 2.0, 9.5), (ROOM_C[0] + 4, 14, 4.0), 62)
cam("Cam_Salon2", (HALL + 4.0, HD - 4.0, 8.5), (ROOM_C[1] + 4, -14, 3.5), 62)
print("escuela ok | lockers:", lockers, "| arboles quitados:", removed)
