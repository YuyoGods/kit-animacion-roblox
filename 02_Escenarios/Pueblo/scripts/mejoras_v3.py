# Mejoras v3: cortinas animables, casas faltantes, 4 tiendas y plaza redisenada.
# Ejecutar despues de build_pueblo.py + add_faroles.py + add_centro.py. Se puede repetir.
import bpy, bmesh, math, random
from mathutils import Vector

random.seed(5)
sc = bpy.context.scene
FONT = r"C:\Windows\Fonts\ariblk.ttf"
FY = -7.0                    # fachada de la casa modelo (local)
PC = Vector((0, 380))
ZP = 0.36
EDGE = 30.2


def lin(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (o[0], o[1], o[2], 1.0)


def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o)
    else:
        c = bpy.data.collections.new(name)
        (parent or sc.collection).children.link(c)
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


def mk_noise(name, hexc, rough=0.85, scale=6, amount=0.12, metal=0.0, emit=None, es=0.0, alpha=1.0, bump_s=0.1):
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 1 - amount
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1.0; mx.inputs["A"].default_value = lin(hexc)
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


def mk_stripes(name, hex_a, hex_b, scale=1.0, axis='X'):
    """toldo a rayas"""
    m, nt, b = base_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    ml = nt.nodes.new("ShaderNodeMath"); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = scale
    nt.links.new(sx.outputs[{'X': 0, 'Y': 1, 'Z': 2}[axis]], ml.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath"); fr.operation = 'FRACT'; nt.links.new(ml.outputs[0], fr.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
    nt.links.new(fr.outputs[0], gt.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin(hex_a); mx.inputs["B"].default_value = lin(hex_b)
    nt.links.new(gt.outputs[0], mx.inputs["Factor"]); nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    return m


def mk_curtain():
    """tela: el color sale de la propiedad 'curtain_color' de cada cortina"""
    m, nt, b = base_mat("Cortina_Tela")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'OBJECT'; at.attribute_name = "curtain_color"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'
    wv.inputs["Scale"].default_value = 6.0; wv.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Generated"], wv.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.72
    nt.links.new(wv.outputs["Fac"], mr.inputs["Value"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs["Factor"].default_value = 1
    nt.links.new(at.outputs["Color"], mx.inputs["A"]); nt.links.new(mr.outputs["Result"], mx.inputs["B"])
    nt.links.new(mx.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    m.use_backface_culling = False
    return m


M = {
    "blanco": bpy.data.materials["Casa_Borde"],
    "acera": bpy.data.materials["Acera"],
    "hojas": bpy.data.materials["Hojas"],
    "madera": bpy.data.materials["Madera"],
    "metal": bpy.data.materials["Farol_Metal"],
    "tierra": bpy.data.materials["Tierra"],
    "piedra": bpy.data.materials["Fuente_Piedra"],
    "zocalo": bpy.data.materials["Pres_Zocalo"],
    "vidrio_claro": mk_noise("Vidrio_Claro", "#A9C9E6", 0.12, 2, 0.02, alpha=0.12, bump_s=0),
    "interior": mk_noise("Interior_Oscuro", "#2B2420", 0.9, 3, 0.15, bump_s=0),
    "interior_tienda": mk_noise("Interior_Tienda", "#C9AE88", 0.9, 3, 0.1, emit="#FFE2B0", es=0.15, bump_s=0),
    "cortina": mk_curtain(),
    "letrero": mk_noise("Letrero_Fondo", "#1E2A38", 0.6, 4, 0.05),
    "letra": mk_noise("Letrero_Letra", "#F7E7C1", 0.5, 4, 0.02, emit="#FFF1D0", es=0.3),
    "pan": mk_noise("Pan", "#C98A4B", 0.8, 8, 0.25),
    "rojo": mk_noise("Rojo_Plastico", "#B3262C", 0.5, 4, 0.05),
    "fruta_n": mk_noise("Fruta_Naranja", "#F08A1C", 0.5, 6, 0.1),
    "fruta_r": mk_noise("Fruta_Roja", "#C7242B", 0.45, 6, 0.1),
    "fruta_a": mk_noise("Fruta_Amarilla", "#F2D032", 0.5, 6, 0.1),
    "fruta_v": mk_noise("Fruta_Verde", "#6DAA2C", 0.5, 6, 0.1),
    "poste_barb": mk_stripes("Poste_Barberia", "#D62828", "#F7F7F7", 2.2, 'Z'),
}
FLOWERS = [m for m in bpy.data.materials if m.name.startswith("Flor_")]


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


def cyl(name, col, loc, r, depth, m, rot=(0, 0, 0), seg=24, parent=None, r2=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, rot, True, parent)


def ball(name, col, loc, r, m, squash=1.0, parent=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in bm.verts:
        v.co.z *= squash
    bm.to_mesh(me); bm.free()
    return obj(name, col, me, loc, m, smooth=True, parent=parent)


def text(name, col, body, loc, size, m, parent=None):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = body
    cu.font = bpy.data.fonts.load(FONT, check_existing=True)
    cu.size = size; cu.extrude = 0.06; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = (math.radians(90), 0, 0)
    cu.materials.append(m); col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def curtain_mesh(name, half_w, h, sign):
    """paño con pliegues; nace en el borde de la ventana y se extiende hacia el centro (sign=+1 o -1)"""
    me = bpy.data.meshes.get(name)
    if me:
        return me
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    nx, nz = 18, 2
    vs = [[bm.verts.new((sign * half_w * i / nx, 0.06 * math.sin(i * math.pi / 1.5), -h / 2 + h * j / nz))
           for j in range(nz + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(nz):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(M["cortina"])
    return me


def window_parts(col, cx, cz, w, h, fy, tag, parent=None, interior="interior", rod=True):
    """ventana con hueco: marco de 4 piezas, fondo oscuro, vidrio transparente"""
    d, yc = 0.37, fy - 0.135
    box(tag + "_MarcoSup", col, (cx, yc, cz + h / 2 + 0.14), (w + 0.56, d, 0.28), M["blanco"], parent=parent)
    box(tag + "_MarcoInf", col, (cx, yc, cz - h / 2 - 0.14), (w + 0.56, d, 0.28), M["blanco"], parent=parent)
    for s in (-1, 1):
        box(tag + "_MarcoLat", col, (cx + s * (w / 2 + 0.14), yc, cz), (0.28, d, h), M["blanco"], parent=parent)
    if interior:
        box(tag + "_Fondo", col, (cx, fy - 0.01, cz), (w, 0.02, h), M[interior], parent=parent)
    if rod:
        box(tag + "_Barra", col, (cx, fy - 0.05, cz + h / 2 - 0.12), (w, 0.06, 0.08), M["metal"], parent=parent)
    box(tag + "_Vidrio", col, (cx, fy - 0.2, cz), (w, 0.04, h), M["vidrio_claro"], parent=parent)


def add_curtains(col, owner, windows, fy, color):
    """2 cortinas por ventana; su ancho depende de owner['cortinas'] (0 = abiertas, 1 = cerradas)"""
    if "cortinas" not in owner:
        owner["cortinas"] = 0.0
    owner.id_properties_ui("cortinas").update(min=0.0, max=1.0, description="0 = abiertas, 1 = cerradas")
    for k, (cx, cz, w, h) in enumerate(windows):
        for s, tag in ((1, "I"), (-1, "D")):
            me = curtain_mesh("CortinaMalla_%.2f_%.2f_%s" % (w, h, tag), w / 2 + 0.02, h - 0.25, s)
            o = bpy.data.objects.new("Cortina_%s_%d%s" % (owner.name, k + 1, tag), me)
            o.location = (cx - s * w / 2, fy - 0.09, cz - 0.1)
            o["curtain_color"] = color
            col.objects.link(o)
            o.parent = owner
            fc = o.driver_add("scale", 0)
            drv = fc.driver; drv.type = 'SCRIPTED'
            v = drv.variables.new(); v.name = "c"; v.type = 'SINGLE_PROP'
            v.targets[0].id_type = 'OBJECT'; v.targets[0].id = owner; v.targets[0].data_path = '["cortinas"]'
            drv.expression = "0.28 + 0.72 * c"


# =============== 1) VENTANAS DE LA CASA MODELO ===============
CB = bpy.data.collections["Casa_Base"]
for o in list(CB.objects):
    n = o.name
    if (n.startswith(("VentanaPB_Marco", "VentanaPB_Vidrio", "VentanaBalcon_Marco", "VentanaBalcon_Vidrio",
                      "VentanaP2_Marco", "VentanaP2_Vidrio")) or n.startswith("Win_")):
        bpy.data.objects.remove(o)
HOUSE_WINDOWS = [(-4.9, 5.2, 3.0, 3.6), (4.9, 5.2, 3.0, 3.6), (0, 13.2, 3.4, 4.6), (-5.4, 13.3, 2.6, 3.0), (5.4, 13.3, 2.6, 3.0)]
for i, (cx, cz, w, h) in enumerate(HOUSE_WINDOWS):
    window_parts(CB, cx, cz, w, h, FY, "Win_%d" % (i + 1))

# =============== 2) CASAS QUE FALTABAN ===============
casas = bpy.data.collections["Casas"]
for side, tag, cols in ((-1, "Izq", ("#CFE0F5", "#5B3A29", "#2E5E3A", "#C27C2C")), (1, "Der", ("#F5E3A1", "#3E4A5C", "#8B1E1E", "#3C6E8F"))):
    n = "Casa_%s_11" % tag
    e = bpy.data.objects.get(n)
    if e is None:
        e = bpy.data.objects.new(n, None); e.instance_type = 'COLLECTION'; e.instance_collection = CB
        casas.objects.link(e)
    e.location = (side * 29.5, 260, 0); e.rotation_euler = (0, 0, math.radians(90 if side < 0 else -90))
    for key, hx in zip(("wall_color", "roof_color", "door_color", "accent_color"), cols):
        e[key] = lin(hx)[:3]

# =============== 3) CORTINAS EN TODAS LAS CASAS ===============
CORT = coll("Cortinas", bpy.data.collections.get("Casas"))
CURTAIN_COLORS = ["#C0392B", "#2E86C1", "#F4D03F", "#8E44AD", "#27AE60", "#E67E22", "#F5B7B1", "#ECE5D6", "#5D6D7E", "#16A085", "#D35400", "#7FB3D5"]
houses = [o for o in bpy.data.objects if o.instance_type == 'COLLECTION' and o.instance_collection == CB]
for o in list(bpy.data.objects):
    if o.name.startswith("CasaAncha_0") and int(o.name[-2:]) >= 5:
        bpy.data.objects.remove(o)            # se convierten en tiendas
houses = [o for o in bpy.data.objects if o.instance_type == 'COLLECTION' and o.instance_collection == CB]
for i, hse in enumerate(sorted(houses, key=lambda o: o.name)):
    add_curtains(CORT, hse, HOUSE_WINDOWS, FY, lin(CURTAIN_COLORS[(i * 5) % len(CURTAIN_COLORS)])[:3])

# =============== 4) TIENDAS ===============
TI = coll("Tiendas", bpy.data.collections.get("Centro"))
SW, SD = 30.0, 16.0        # ancho y fondo
SFY = -SD / 2              # fachada local


def shop(name, kind, loc, rz, wall_hex, awn_a, awn_b, curtain_hex):
    root = bpy.data.objects.new(name, None); root.empty_display_size = 3
    root.location = loc; root.rotation_euler = (0, 0, rz); TI.objects.link(root)
    mw = mk_noise("Tienda_Muro_" + kind, wall_hex, 0.9, 3, 0.1, bump_s=0.25)
    awn = mk_stripes("Tienda_Toldo_" + kind, awn_a, awn_b, 0.8, 'X')
    P = root
    REC = SFY + 3.0      # pared interior del local (el frente de la planta baja queda hueco 3 de fondo)
    box(name + "_Zocalo", TI, (0, 0, 0.3), (SW + 0.4, SD + 0.4, 0.6), M["zocalo"], parent=P)
    box(name + "_MurosAltos", TI, (0, 0, 12.0), (SW, SD, 7.2), mw, parent=P)
    box(name + "_Local", TI, (0, (REC + SD / 2) / 2, 4.5), (SW, SD / 2 - REC, 7.8), M["interior_tienda"], parent=P)
    for s in (-1, 1):
        box(name + "_LocalLado", TI, (s * (SW / 2 - 0.25), (SFY + REC) / 2, 4.5), (0.5, 3.0, 7.8), mw, parent=P)
        box(name + "_Relleno", TI, (s * 2.9, SFY + 0.2, 3.75), (1.84, 0.4, 6.3), mw, parent=P)
        box(name + "_RellenoExt", TI, (s * 13.94, SFY + 0.2, 3.75), (1.12, 0.4, 6.3), mw, parent=P)
        box(name + "_Zoclo", TI, (s * 8.6, SFY + 0.2, 1.06), (9.56, 0.4, 0.92), mw, parent=P)
    box(name + "_Dintel", TI, (0, SFY + 0.2, 7.65), (SW, 0.4, 1.5), mw, parent=P)
    L = bpy.data.lights.new(name + "_LuzLocal", 'POINT'); L.energy = 160; L.color = lin("#FFE0B0")[:3]; L.shadow_soft_size = 1.0
    lo = bpy.data.objects.new(name + "_LuzLocal", L); lo.location = (0, SFY + 1.6, 7.0); lo.parent = P; TI.objects.link(lo)
    box(name + "_Faja", TI, (0, 0, 8.6), (SW + 0.5, SD + 0.5, 0.4), M["blanco"], parent=P)
    box(name + "_Cornisa", TI, (0, 0, 15.9), (SW + 1.0, SD + 1.0, 0.6), M["blanco"], parent=P)
    box(name + "_Pretil", TI, (0, 0, 16.9), (SW, SD, 1.4), mw, parent=P)
    box(name + "_Remate", TI, (0, 0, 17.75), (SW + 0.5, SD + 0.5, 0.3), M["blanco"], parent=P)
    for s in (-1, 1):
        box(name + "_Pilastra", TI, (s * SW / 2, SFY, 8.1), (1.0, 1.0, 15.0), M["blanco"], parent=P)
    box(name + "_Explanada", TI, (0, SFY - 1.5, 0.15), (SW, 3.0, 0.3), M["acera"], parent=P)
    # planta baja: 2 aparadores + puerta de vidrio
    for s in (-1, 1):
        window_parts(TI, s * 8.6, 4.2, 9.0, 4.8, SFY, name + "_Aparador", P, interior=None, rod=False)
        box(name + "_Repisa", TI, (s * 8.6, SFY - 0.35, 1.55), (9.6, 0.8, 0.3), M["blanco"], parent=P)
    window_parts(TI, 0, 3.6, 3.4, 6.0, SFY, name + "_Puerta", P, interior=None, rod=False)
    box(name + "_PuertaManija", TI, (1.2, SFY - 0.35, 3.6), (0.12, 0.12, 1.2), M["metal"], parent=P)
    # toldo a rayas + letrero
    box(name + "_Toldo", TI, (0, SFY - 1.55, 7.55), (27.0, 3.3, 0.18), awn, rot=(20, 0, 0), parent=P)
    box(name + "_ToldoFaldon", TI, (0, SFY - 3.1, 6.75), (27.0, 0.08, 0.7), awn, parent=P)
    box(name + "_Letrero", TI, (0, SFY - 0.25, 9.7), (17.0, 0.4, 2.0), M["letrero"], parent=P, bevel=0.08)
    text(name + "_LetreroTexto", TI, kind, (0, SFY - 0.5, 9.7), 1.35, M["letra"], parent=P)
    # planta alta: 4 ventanas con cortinas
    up = [(-10.5, 12.6, 2.6, 3.0), (-3.5, 12.6, 2.6, 3.0), (3.5, 12.6, 2.6, 3.0), (10.5, 12.6, 2.6, 3.0)]
    for k, (cx, cz, w, h) in enumerate(up):
        window_parts(TI, cx, cz, w, h, SFY, name + "_VentanaAlta%d" % k, P)
        box(name + "_RepisaAlta", TI, (cx, SFY - 0.4, cz - h / 2 - 0.35), (w + 0.9, 0.9, 0.28), M["blanco"], parent=P)
    add_curtains(TI, root, up, SFY, lin(curtain_hex)[:3])
    # detalles por tipo
    if kind == "BARBERÍA":
        cyl(name + "_PosteBarb", TI, (5.0, SFY - 0.55, 4.2), 0.32, 3.0, M["poste_barb"], parent=P)
        for z in (2.6, 5.8):
            ball(name + "_PosteTapa", TI, (5.0, SFY - 0.55, z), 0.38, M["blanco"], 0.7, parent=P)
        for s in (-1, 1):
            for k in range(2):
                x = s * (5.5 + k * 5.0)
                box(name + "_SillaPie", TI, (x, SFY + 1.5, 1.2), (0.5, 0.5, 1.2), M["metal"], parent=P)
                box(name + "_Silla", TI, (x, SFY + 1.5, 2.1), (1.6, 1.4, 0.6), M["rojo"], parent=P)
                box(name + "_SillaResp", TI, (x, SFY + 2.1, 3.1), (1.6, 0.3, 1.8), M["rojo"], parent=P)
                box(name + "_Espejo", TI, (x, SFY + 2.94, 4.8), (2.2, 0.08, 2.4), M["blanco"], parent=P)
    elif kind == "PANADERÍA":
        for s in (-1, 1):
            for lvl, z in enumerate((2.3, 4.0)):
                box(name + "_Estante", TI, (s * 8.6, SFY + 1.6, z), (8.4, 1.4, 0.15), M["madera"], parent=P)
                for k in range(7):
                    ball(name + "_Pan", TI, (s * 8.6 - 3.6 + k * 1.2, SFY + 1.6, z + 0.35), 0.45, M["pan"], 0.6, parent=P)
    elif kind == "ABARROTES":
        frutas = [M["fruta_n"], M["fruta_r"], M["fruta_a"], M["fruta_v"]]
        for s in (-1, 1):
            for k in range(3):
                x = s * (4.6 + k * 3.4)
                box(name + "_Caja", TI, (x, SFY - 1.6, 0.85), (2.8, 1.8, 1.1), M["madera"], parent=P)
                fm = frutas[(k + (s > 0) * 2) % 4]
                for a in range(4):
                    for b in range(2):
                        ball(name + "_Fruta", TI, (x - 0.95 + a * 0.63, SFY - 2.0 + b * 0.75, 1.55), 0.32, fm, parent=P)
    elif kind == "CAFETERÍA":
        for s in (-1, 1):
            x = s * 11.0
            cyl(name + "_MesaPata", TI, (x, SFY - 1.7, 1.0), 0.1, 1.6, M["metal"], parent=P)
            cyl(name + "_Mesa", TI, (x, SFY - 1.7, 1.85), 0.9, 0.1, M["blanco"], parent=P)
            ball(name + "_Taza", TI, (x + 0.2, SFY - 1.6, 2.0), 0.18, M["blanco"], 0.8, parent=P)
            for t in (-1, 1):
                box(name + "_Silla", TI, (x + t * 1.5, SFY - 1.7, 1.0), (0.9, 0.9, 0.12), M["madera"], parent=P)
                box(name + "_SillaResp", TI, (x + t * 1.95, SFY - 1.7, 1.6), (0.12, 0.9, 1.2), M["madera"], parent=P)
                for u in (-1, 1):
                    for v in (-1, 1):
                        box(name + "_SillaPata", TI, (x + t * 1.5 + u * 0.38, SFY - 1.7 + v * 0.38, 0.5), (0.08, 0.08, 0.9), M["metal"], parent=P)
        box(name + "_Mostrador", TI, (0, SFY + 2.2, 1.9), (24, 1.2, 2.6), M["madera"], parent=P)
        for k in range(5):
            ball(name + "_Pastel", TI, (-8 + k * 4, SFY + 2.2, 3.5), 0.5, M["pan"], 0.7, parent=P)
    return root


SHOP_X = 48 + 5 + 3 + SD / 2     # borde glorieta + acera + explanada + medio fondo = 64
shop("Tienda_Panaderia", "PANADERÍA", (-SHOP_X, 360, 0), math.radians(90), "#F3DDB3", "#E8A33D", "#FFF6E0", "#E67E22")
shop("Tienda_Barberia", "BARBERÍA", (-SHOP_X, 400, 0), math.radians(90), "#D6E4F0", "#C0392B", "#F7F7F7", "#2E86C1")
shop("Tienda_Abarrotes", "ABARROTES", (SHOP_X, 360, 0), math.radians(-90), "#D7EAC8", "#2E7D32", "#F1F8E9", "#27AE60")
shop("Tienda_Cafeteria", "CAFETERÍA", (SHOP_X, 400, 0), math.radians(-90), "#E8D5C4", "#6D4C41", "#F5EBDD", "#8E44AD")

# =============== 5) PLAZA REDISEÑADA ===============
PL = bpy.data.collections["Plaza"]
for o in list(PL.objects):
    if o.name.startswith(("Arbusto", "Banca", "Bote", "Jardinera", "Flor_")):
        bpy.data.objects.remove(o)
BANCA = bpy.data.collections["Banca_Modelo"]
BOTE = bpy.data.collections["Bote_Modelo"]


def inst(name, src, x, y, rz=0.0):
    e = bpy.data.objects.new(name, None); e.instance_type = 'COLLECTION'; e.instance_collection = src
    e.location = (PC.x + x, PC.y + y, ZP); e.rotation_euler = (0, 0, rz); PL.objects.link(e); return e


def big_bush(name, x, y, r, flower_mats, n_flowers=16, zoff=0.0):
    cx, cy, cz = PC.x + x, PC.y + y, ZP + r * 0.75 + zoff
    ball(name, PL, (cx, cy, cz), r, M["hojas"], 0.85)
    for k in range(3):
        a = random.uniform(0, 6.28)
        ball(name + "_Lobulo", PL, (cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, cz - r * 0.2), r * 0.6, M["hojas"], 0.85)
    for k in range(n_flowers):
        th = random.uniform(0, 2 * math.pi); ph = random.uniform(0.15, 1.25)
        p = Vector((math.cos(th) * math.sin(ph), math.sin(th) * math.sin(ph), math.cos(ph) * 0.85)) * (r * 1.0)
        ball(name + "_Flor", PL, (cx + p.x, cy + p.y, cz + p.z), random.uniform(0.16, 0.22), random.choice(flower_mats))


def fl(*names):
    return [m for m in FLOWERS if any(n in m.name for n in names)] or FLOWERS


# alrededor de la fuente: 4 bancas mirando al agua y detras 4 arbustos grandes con flores
for k, ang in enumerate((45, 135, 225, 315)):
    a = math.radians(ang)
    inst("Banca_Centro_%d" % (k + 1), BANCA, 14.5 * math.cos(a), 14.5 * math.sin(a), a - math.pi / 2)
    big_bush("Arbusto_Centro_%d" % (k + 1), 20.5 * math.cos(a), 20.5 * math.sin(a), 1.9,
             [fl("Rosa", "Blanca"), fl("Amarilla", "Roja"), fl("Morada", "Blanca"), fl("Roja", "Rosa")][k])
# bordes: 2 bancas por lado mirando hacia la fuente + 2 arbustos grandes por lado
B = EDGE - 1.6
edge_benches = [((-11, -B), math.pi), ((11, -B), math.pi), ((-11, B), 0.0), ((11, B), 0.0),
                ((-B, -11), math.pi / 2), ((-B, 11), math.pi / 2), ((B, -11), -math.pi / 2), ((B, 11), -math.pi / 2)]
for k, ((x, y), rz) in enumerate(edge_benches):
    inst("Banca_Borde_%d" % (k + 1), BANCA, x, y, rz)
bush_pts = [(-21, -B), (21, -B), (-21, B), (21, B), (-B, -21), (-B, 21), (B, -21), (B, 21)]
for k, (x, y) in enumerate(bush_pts):
    big_bush("Arbusto_Borde_%d" % (k + 1), x, y, 1.6, random.choice([fl("Rosa", "Blanca"), fl("Amarilla", "Roja"), fl("Morada", "Blanca")]), 12)
# esquinas: jardinera de piedra con arbusto florido
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        x, y = sx_ * (EDGE - 2.6), sy_ * (EDGE - 2.6)
        cyl("Jardinera", PL, (PC.x + x, PC.y + y, ZP + 0.45), 2.6, 0.9, M["piedra"])
        cyl("Jardinera_Tierra", PL, (PC.x + x, PC.y + y, ZP + 0.88), 2.3, 0.1, M["tierra"])
        big_bush("Jardinera_Arbusto", x, y + 0.1, 1.7, fl("Roja", "Amarilla", "Rosa"), 14, zoff=0.6)
# botes de basura: pocos y repartidos sin simetria
for k, (x, y) in enumerate(((14.0, -27.6), (-27.6, -7.4), (27.6, 14.6), (-14.4, 27.6), (13.6, 6.4))):
    inst("Bote_%02d" % (k + 1), BOTE, x, y, random.uniform(0, 6.28))

print("v3 ok | casas con cortinas:", len(houses), "| tiendas: 4 | cortinas:", len(CORT.objects))

# vidrio con poco reflejo para que se vean las cortinas desde cualquier angulo
_b = bpy.data.materials["Vidrio_Claro"].node_tree.nodes["BSDF"]
_b.inputs["IOR"].default_value = 1.05
_b.inputs["Specular IOR Level"].default_value = 0.15

# los drivers recien creados a veces quedan "invalidos": se reinician aqui
for _o in bpy.data.objects:
    if _o.name.startswith("Cortina_") and _o.animation_data:
        for _fc in _o.animation_data.drivers:
            while len(_fc.keyframe_points):
                _fc.keyframe_points.remove(_fc.keyframe_points[0])
            _fc.driver.expression = _fc.driver.expression
            _fc.update()
