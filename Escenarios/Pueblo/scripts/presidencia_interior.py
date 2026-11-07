# INTERIOR DE LA PRESIDENCIA (estilo Roblox, todo con cajas). Coordenadas del MUNDO.
#   blender -b Pueblo_v2_set.blend --python presidencia_interior.py -- [salida.blend]
# Planta baja (z 1.5): vestibulo con piso de ajedrez, alfombra roja, escalera principal, retratos de alcaldes, banderas,
#   mostrador de INFORMES, bancas, candil y maqueta del pueblo.
# 2.o piso (z 10.8): despacho del alcalde (al frente), sala de cabildo (ala izquierda) y archivo (ala derecha).
# Torre (z 22): cuarto del reloj con engranes, pendulo y campana (se ve la parte de atras de la caratula).
# Animables: vacios "Pres_PuertaIzq/Der_Bisagra" (girar Z), "Pres_Engrane*" (girar Y local), "Pres_Pendulo" (girar Y).
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from util_interiores import *  # noqa: E402,F401

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SALIDA = ARGS[0] if ARGS else bpy.data.filepath
TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "texturas")
T = 0.6
ZP, ZL0, ZL1, ZT = 1.5, 10.2, 10.8, 17.9


def caja_mundo(o):
    ps = [o.matrix_world @ Vector(b) for b in o.bound_box]
    return (Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps))),
            Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps))))


def mat_imagen(nombre, archivo, u="x", alfa=False):
    """imagen sobre una pieza plana. u = eje del mundo que va de izquierda a derecha para quien la mira:
    'x' (cuadro mirando a -y), 'y' (mirando a +x), '-y' (mirando a -x). Usa coordenadas Generated (sin UVs)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = mat(nombre, "#FFFFFF", 0.7)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    img = bpy.data.images.load(os.path.join(TEX, archivo), check_existing=True)
    img.pack()
    co = nt.nodes.new("ShaderNodeTexCoord"); se = nt.nodes.new("ShaderNodeSeparateXYZ"); cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(co.outputs["Generated"], se.inputs[0])
    if u == "-y":
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        nt.links.new(se.outputs["Y"], inv.inputs[1]); nt.links.new(inv.outputs[0], cb.inputs["X"])
    else:
        nt.links.new(se.outputs["X" if u == "x" else "Y"], cb.inputs["X"])
    nt.links.new(se.outputs["Z"], cb.inputs["Y"])
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'
    nt.links.new(cb.outputs[0], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
    if alfa:
        nt.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
        m.surface_render_method = 'DITHERED'
    return m


def mat_ajedrez(nombre):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = mat(nombre, "#FFFFFF", 0.35)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    co = nt.nodes.new("ShaderNodeTexCoord"); ch = nt.nodes.new("ShaderNodeTexChecker")
    ch.inputs["Scale"].default_value = 0.25
    ch.inputs["Color1"].default_value = (0.82, 0.80, 0.76, 1); ch.inputs["Color2"].default_value = (0.05, 0.05, 0.06, 1)
    nt.links.new(co.outputs["Object"], ch.inputs["Vector"]); nt.links.new(ch.outputs["Color"], bs.inputs["Base Color"])
    return m


def texto(nombre, cuerpo, pos, rot, tam, m, col):
    cu = bpy.data.curves.new(nombre, 'FONT')
    cu.body = cuerpo; cu.size = tam; cu.extrude = 0.03; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    if "Arial Black" in bpy.data.fonts:
        cu.font = bpy.data.fonts["Arial Black"]
    o = bpy.data.objects.new(nombre, cu); col.objects.link(o)
    o.location = pos; o.rotation_euler = rot
    o.data.materials.append(m)
    return o


def engrane(nombre, centro, r, dientes, m, col):
    p = Pieza(nombre, None, col)
    p.cil((0, 0, -0.15), r, 0.3, m, 24)
    p.cil((0, 0, -0.3), r * 0.25, 0.6, m, 12)
    for k in range(dientes):
        a = 2 * math.pi * k / dientes
        p.M = Matrix.Rotation(a, 4, 'Z')
        p.caja((r - 0.05, -0.18, -0.15), (r + 0.35, 0.18, 0.15), m)
    p.M = Matrix.Identity(4)
    o = p.fin()
    o.location = centro
    o.rotation_euler = (math.radians(90), 0, 0)    # eje del engrane a lo largo de Y
    return o


def construir():
    if "Presidencia_Interior" in bpy.data.collections:
        print("la presidencia ya tiene interior")
        return
    col = bpy.data.collections.new("Presidencia_Interior")
    bpy.context.scene.collection.children.link(col)
    cuerpo = bpy.data.objects["Cuerpo"]
    mn, mx = caja_mundo(cuerpo)
    x0, y0, z0 = mn; x1, y1, z1 = mx
    m_ext = cuerpo.material_slots[0].material
    pared = mat("Pres_ParedInt", "#F3E9D2", 0.85); madera = mat("Int_Madera", "#8A5A35"); madera_os = mat("Pres_MaderaOscura", "#5A3820")
    blanco = mat("Int_Blanco", "#F4F1EA"); oro = mat("Pres_Oro", "#D9A93A", 0.3); rojo = mat("Pres_Alfombra", "#A3202A", 0.9)
    marmol = mat("Pres_Marmol", "#E8E4DC", 0.3); negro = mat("Int_Negro", "#202226", 0.4); metal = mat("Int_Metal", "#9AA0A6", 0.35)
    verde = mat("Pres_Cuero", "#2F5E3B", 0.6); foco = mat("Int_Foco", "#FFE9C2", 0.5, emit=6.0); vidrio = mat("Pres_VidrioVitrina", "#CFE8F5", 0.05, alpha=0.18)
    hojas = mat("Int_Hojas", "#3F8F3A", 0.8); maceta = mat("Int_Maceta", "#B5603A")
    # ---------- muros huecos con puerta y ventanas
    muros = {"Frente": ((x0, y0, z0), (x1, y0 + T, z1)), "Fondo": ((x0, y1 - T, z0), (x1, y1, z1)),
             "Izq": ((x0, y0 + T, z0), (x0 + T, y1 - T, z1)), "Der": ((x1 - T, y0 + T, z0), (x1, y1 - T, z1))}
    tmp = bpy.data.collections.new("tmp_cortes"); bpy.context.scene.collection.children.link(tmp)
    cortes = {k: [] for k in muros}
    pa, _ = caja_mundo(bpy.data.objects["Puerta_Hoja"]); _, pb = caja_mundo(bpy.data.objects["Puerta_Hoja.001"])
    cortes["Frente"].append(Pieza("corte_puerta", None, tmp).caja((pa.x - 0.03, y0 - 1, z0 - 0.5), (pb.x + 0.03, y0 + 1, pb.z + 0.03), m_ext).fin())
    cortes["Frente"].append(Pieza("corte_arco", None, tmp).caja((-2.5, y0 - 1, pb.z), (2.5, y0 + 1, 9.4), m_ext).fin())
    for o in bpy.data.objects:
        if o.type != 'MESH' or "Vidrio" not in o.name or o.name.startswith("Puerta"):
            continue
        a, b = caja_mundo(o); c = (a + b) / 2
        if not (x0 - 1 < c.x < x1 + 1 and y0 - 1.5 < c.y < y1 + 1.5 and z0 < c.z < z1):
            continue
        d = {"Frente": abs(c.y - y0), "Fondo": abs(c.y - y1), "Izq": abs(c.x - x0), "Der": abs(c.x - x1)}
        lado = min(d, key=d.get)
        if d[lado] > 1.2:
            continue
        e = 0.03
        if lado in ("Frente", "Fondo"):
            yy = y0 if lado == "Frente" else y1
            cortes[lado].append(Pieza("corte_" + o.name, None, tmp).caja((a.x - e, yy - 1, a.z - e), (b.x + e, yy + 1, b.z + e), m_ext).fin())
        else:
            xx = x0 if lado == "Izq" else x1
            cortes[lado].append(Pieza("corte_" + o.name, None, tmp).caja((xx - 1, a.y - e, a.z - e), (xx + 1, b.y + e, b.z + e), m_ext).fin())
    print("huecos:", {k: len(v) for k, v in cortes.items()})
    obs = []
    for lado, (a, b) in muros.items():
        ob = Pieza("Pres_Muro" + lado, None, col).caja(a, b, m_ext).fin()
        ob.data.materials.append(pared)
        for i, c in enumerate(cortes[lado]):
            md = ob.modifiers.new("h%d" % i, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = c
        obs.append(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for ob in obs:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear(); ob.data = me
        for p in me.polygons:
            v = Vector((cx - p.center.x, cy - p.center.y, 0))
            if v.length and Vector((p.normal.x, p.normal.y, 0)).dot(v.normalized()) > 0.7:
                p.material_index = 1
    for c in list(tmp.objects):
        bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.collections.remove(tmp)
    cuerpo.hide_render = True; cuerpo.hide_viewport = True; cuerpo.name = "Cuerpo_original_oculto"
    for o in list(bpy.data.objects):     # fondos oscuros falsos detras de las ventanas
        if "Fondo" in o.name and o.type == 'MESH' and not o.name.startswith("Pres_"):   # no borrar nuestro Pres_MuroFondo
            a, b = caja_mundo(o); c = (a + b) / 2
            if x0 - 1 < c.x < x1 + 1 and y0 - 1.5 < c.y < y1 + 1.5 and z0 < c.z < z1:
                bpy.data.objects.remove(o, do_unlink=True)
    # ---------- puertas con bisagra
    for nom, lado_x in (("Puerta_Hoja", pa.x), ("Puerta_Hoja.001", pb.x)):
        h = bpy.data.objects.new("Pres_Puerta%s_Bisagra" % ("Izq" if lado_x < 0 else "Der"), None); col.objects.link(h)
        h.location = (lado_x, 465.7, ZP); h.empty_display_size = 0.8
        o = bpy.data.objects[nom]; W = o.matrix_world.copy()
        o.parent = h; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_world = W
    ix0, iy0, ix1, iy1 = x0 + T, y0 + T, x1 - T, y1 - T
    # ---------- pisos, losa (hueco de escalera x -5..5, y 474..486), techo
    p = Pieza("Pres_Pisos", None, col)
    p.caja((ix0, iy0, ZP), (ix1, iy1, ZP + 0.06), mat_ajedrez("Pres_PisoAjedrez"))
    for a, b in (((ix0, iy0), (ix1, 474)), ((ix0, 474), (-5, iy1)), ((5, 474), (ix1, iy1)), ((-5, 486), (5, iy1))):
        p.caja((a[0], a[1], ZL0), (b[0], b[1], ZL1), blanco)
        p.caja((a[0], a[1], ZL1), (b[0], b[1], ZL1 + 0.06), mat("Pres_Duela", "#A8743F", 0.6))
    p.caja((ix0, iy0, ZT), (ix1, iy1, ZT + 0.6), blanco)
    for z in (ZP + 0.06,):                                   # lambrin de madera en planta baja
        p.caja((ix0, iy0, z), (pa.x - 0.3, iy0 + 0.15, z + 3.0), madera_os)
        p.caja((pb.x + 0.3, iy0, z), (ix1, iy0 + 0.15, z + 3.0), madera_os)
        p.caja((ix0, iy1 - 0.15, z), (ix1, iy1, z + 3.0), madera_os)
        p.caja((ix0, iy0, z), (ix0 + 0.15, iy1, z + 3.0), madera_os)
        p.caja((ix1 - 0.15, iy0, z), (ix1, iy1, z + 3.0), madera_os)
    p.caja((-2.2, iy0, ZP + 0.06), (2.2, 474, ZP + 0.1), rojo)            # alfombra roja
    p.fin()
    # ---------- escalera principal
    e = Pieza("Pres_Escalera", None, col)
    n, ya, yb = 14, 474.0, 486.0
    d, s = (yb - ya) / n, (ZL1 - ZP) / n
    for k in range(n):
        e.caja((-5, ya + k * d, ZP), (5, ya + (k + 1) * d, ZP + (k + 1) * s), marmol)
        e.caja((-3, ya + k * d, ZP + (k + 1) * s), (3, ya + (k + 1) * d, ZP + (k + 1) * s + 0.04), rojo)
        if k % 2 == 0:
            for sx in (-4.85, 4.6):
                e.caja((sx, ya + k * d + 0.3, ZP + (k + 1) * s), (sx + 0.25, ya + k * d + 0.55, ZP + (k + 1) * s + 3.0), oro)
        for sx in (-4.95, 4.55):
            e.caja((sx, ya + k * d, ZP + (k + 1) * s + 3.0), (sx + 0.4, ya + (k + 1) * d, ZP + (k + 1) * s + 3.25), madera_os)
    for y in [ya + 1.0 * k for k in range(13)]:              # barandal del hueco en el 2.o piso
        for sx in (-5.1, 4.9):
            e.caja((sx, y, ZL1), (sx + 0.2, y + 0.2, ZL1 + 3.0), oro)
    for sx in (-5.2, 4.8):
        e.caja((sx, ya, ZL1 + 3.0), (sx + 0.4, yb, ZL1 + 3.25), madera_os)
    e.caja((-5.2, ya - 0.2, ZL1 + 3.0), (5.2, ya + 0.2, ZL1 + 3.25), madera_os)
    e.fin()
    # ---------- planta baja: mostrador, bancas, banderas, plantas, maqueta, candil, retratos, escudo
    mo = Pieza("Pres_Mostrador", None, col)
    mo.caja((15, 469, ZP), (23, 471.5, ZP + 2.6), madera); mo.caja((14.8, 468.8, ZP + 2.6), (23.2, 471.7, ZP + 2.8), marmol)
    mo.cil((17, 470.2, ZP + 2.8), 0.3, 0.25, oro, 12)
    mo.fin()
    texto("Pres_Letrero_Informes", "INFORMES", (19, 468.75, ZP + 1.4), (math.radians(90), 0, 0), 0.75, oro, col)
    for k, y in enumerate((470.5, 480.5)):
        b = Pieza("Pres_Banca%d" % k, None, col)
        b.caja((ix0 + 0.3, y, ZP + 1.6), (ix0 + 2.3, y + 5.5, ZP + 1.9), madera)
        b.caja((ix0 + 0.3, y, ZP + 1.9), (ix0 + 0.6, y + 5.5, ZP + 3.8), madera)
        for yy in (y + 0.2, y + 5.0):
            b.caja((ix0 + 0.5, yy, ZP), (ix0 + 2.1, yy + 0.3, ZP + 1.6), madera_os)
        b.fin()
    band = bpy.data.objects.get("Bandera")
    m_band = band.material_slots[0].material if band and band.material_slots else rojo
    for k, sx in enumerate((-6.8, 6.8)):
        f = Pieza("Pres_BanderaInt%d" % k, None, col)
        f.cil((sx, 475.0, ZP), 0.5, 0.4, oro, 12).cil((sx, 475.0, ZP + 0.4), 0.09, 8.2, madera_os, 8).esfera((sx, 475.0, ZP + 8.7), 0.25, oro, 8)
        fx = (sx - 3.1, sx - 0.1) if sx < 0 else (sx + 0.1, sx + 3.1)      # la tela hacia afuera
        f.caja((fx[0], 474.97, ZP + 5.6), (fx[1], 475.03, ZP + 8.4), m_band)
        f.fin()
    for k, (px, py) in enumerate(((-4.5, 467.8), (4.5, 467.8), (-8.5, 486.8), (8.5, 486.8))):
        pl = Pieza("Pres_Planta%d" % k, None, col)
        pl.cil((px, py, ZP), 0.75, 1.5, maceta, 12).esfera((px, py, ZP + 2.6), 1.2, hojas, 8).esfera((px + 0.4, py, ZP + 3.4), 0.8, hojas, 8)
        pl.fin()
    mq = Pieza("Pres_Maqueta", None, col)
    mq.caja((-21, 477, ZP), (-14, 482, ZP + 3.0), madera_os)
    mq.caja((-20.8, 477.2, ZP + 3.0), (-14.2, 481.8, ZP + 3.1), mat("Pres_PastoMini", "#5DA34B", 0.9))
    for k in range(10):
        hx_, hy_ = -20.2 + (k % 5) * 1.25, 477.8 + (k // 5) * 3.0
        mq.caja((hx_, hy_, ZP + 3.1), (hx_ + 0.8, hy_ + 0.8, ZP + 3.8), mat("Pres_CasaMini%d" % (k % 4), ("#E8A87C", "#C38D9E", "#85C7DE", "#F6E27F")[k % 4]))
    mq.caja((-17.9, 479.3, ZP + 3.1), (-16.9, 480.3, ZP + 4.6), blanco)
    mq.caja((-21, 477, ZP + 3.1), (-14, 482, ZP + 5.2), vidrio)
    mq.fin()
    cd = Pieza("Pres_Candil", None, col)
    cd.cil((0, 471.5, 8.4), 1.8, 0.2, oro, 20).cil((0, 471.5, 8.6), 0.07, 1.6, oro, 6)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cd.cil((1.7 * math.cos(a), 471.5 + 1.7 * math.sin(a), 8.6), 0.12, 0.6, foco, 8)
    cd.fin()
    for k, (y, img) in enumerate(((470.0, "retrato_alcalde_1"), (476.5, "retrato_alcalde_2"), (470.0, "retrato_alcalde_3"), (476.5, "retrato_alcalde_4"))):
        izq = k < 2
        cuadro("Pres_Retrato%d" % (k + 1), None, col, Matrix.Translation((ix0 if izq else ix1, y, ZP + 6.0)) @ Matrix.Rotation(math.radians(90 if izq else -90), 4, 'Z'),
               2.6, 3.4, oro, mat_imagen("Pres_" + img, img + ".png", "y" if izq else "-y"))
    esc = Pieza("Pres_Escudo", None, col, Matrix.Translation((0, iy1 - 0.02, ZL1 + 3.8)))
    esc.caja((-1.8, -0.06, 0), (1.8, 0, 4.3), mat_imagen("Pres_EscudoMat", "escudo_pueblo.png", "x", alfa=True))
    esc.fin()
    # ---------- 2.o piso: tabiques (despacho al frente x -12..12 hasta y 474; alas a los lados)
    z2 = ZL1 + 0.06
    tb = Pieza("Pres_Tabiques", None, col)
    tb.caja((-12, 473.4, ZL1), (-2, 474.0, ZT), pared); tb.caja((2, 473.4, ZL1), (12, 474.0, ZT), pared); tb.caja((-2, 473.4, 17.0), (2, 474.0, ZT), pared)
    for sx in (-12.3, 11.7):
        tb.caja((sx, iy0, ZL1), (sx + 0.6, 477, ZT), pared); tb.caja((sx, 480, ZL1), (sx + 0.6, iy1, ZT), pared); tb.caja((sx, 477, 17.0), (sx + 0.6, 480, ZT), pared)
    tb.fin()
    texto("Pres_Letrero_Cabildo", "CABILDO", (-11.65, 478.5, 17.45), (math.radians(90), 0, math.radians(90)), 0.45, oro, col)
    texto("Pres_Letrero_Despacho", "DESPACHO DEL ALCALDE", (11.65, 478.5, 17.45), (math.radians(90), 0, math.radians(-90)), 0.33, oro, col)
    texto("Pres_Letrero_Secretaria", "SECRETARIA", (0, 474.05, 17.45), (math.radians(90), 0, math.radians(180)), 0.45, oro, col)
    libros = [mat("Int_Libro_%d" % i, c) for i, c in enumerate(("#C0392B", "#2E86C1", "#27AE60", "#F1C40F", "#8E44AD", "#E67E22"))]
    # despacho del alcalde: ala derecha completa (15 x 23). El alcalde se sienta mirando a la puerta (-x)
    al = Pieza("Pres_AlfombraDespacho", None, col); al.caja((15.0, 470.0, z2), (26.6, 487.0, z2 + 0.04), rojo); al.fin()
    es = Pieza("Pres_Escritorio", None, col)
    es.caja((21.0, 474.0, z2), (23.6, 483.0, z2 + 2.6), madera_os)
    es.caja((20.8, 473.8, z2 + 2.6), (23.8, 483.2, z2 + 2.9), madera)
    es.caja((21.6, 477.2, z2 + 2.9), (22.6, 479.8, z2 + 3.1), verde)                      # carpeta de cuero
    es.cil((22.6, 481.8, z2 + 2.9), 0.3, 1.3, oro, 10).cil((22.6, 481.8, z2 + 4.2), 0.6, 0.5, verde, 12)
    es.cil((22.4, 475.2, z2 + 2.9), 0.25, 0.7, oro, 8)                                    # portaplumas
    es.fin()
    texto("Pres_Placa_Alcalde", "ALCALDE", (20.75, 478.5, z2 + 1.6), (math.radians(90), 0, math.radians(-90)), 0.6, oro, col)
    sl = Pieza("Pres_SillonAlcalde", None, col, M_en(25.1, 478.5, z2, 90))                 # sillon grande
    sl.caja((-1.7, -1.1, 1.5), (1.7, 1.2, 2.1), verde); sl.caja((-1.7, -1.3, 2.1), (1.7, -0.8, 7.0), verde)
    sl.caja((-2.0, -1.1, 1.5), (-1.6, 1.2, 3.2), madera_os); sl.caja((1.6, -1.1, 1.5), (2.0, 1.2, 3.2), madera_os)
    sl.cil((0, 0, 0), 1.1, 0.2, metal, 10).cil((0, 0, 0.2), 0.18, 1.3, metal, 8)
    sl.fin()
    for k, y in enumerate((476.6, 480.4)):
        silla("Pres_SillaVisita%d" % k, None, col, M_en(18.9, y, z2, 90), madera_os, verde)
    for k, x in enumerate((15.5, 20.5)):
        librero("Pres_Librero%d" % k, None, col, M_en(x, iy1 - 0.45, z2), madera_os, libros, 4.2, 6.2)
    for k, y in enumerate((474.2, 482.8)):
        f = Pieza("Pres_BanderaDesp%d" % k, None, col)
        f.cil((26.6, y, z2), 0.45, 0.35, oro, 12).cil((26.6, y, z2 + 0.35), 0.08, 6.4, madera_os, 8).esfera((26.6, y, z2 + 6.9), 0.22, oro, 8)
        f.caja((26.57, y - 2.7 if k == 0 else y + 0.1, z2 + 4.0), (26.63, y - 0.1 if k == 0 else y + 2.7, z2 + 6.5), m_band)
        f.fin()
    cuadro("Pres_RetratoActual", None, col, Matrix.Translation((ix1, 478.5, z2 + 5.2)) @ Matrix.Rotation(math.radians(-90), 4, 'Z'),
           2.8, 3.6, oro, mat_imagen("Pres_retrato_alcalde_actual", "retrato_alcalde_actual.png", "-y"))
    cf = Pieza("Pres_CajaFuerte", None, col)
    cf.caja((25.0, 487.4, z2), (27.0, 489.0, z2 + 2.4), mat("Pres_Acero", "#3B4045", 0.35))
    cf.cil((26.0, 487.35, z2 + 1.4), 0.35, 0.05, oro, 16)
    cf.fin()
    gl = Pieza("Pres_Globo", None, col)
    gl.cil((14.2, 487.6, z2), 0.5, 0.15, madera_os, 10).cil((14.2, 487.6, z2 + 0.15), 0.08, 2.2, madera_os, 6).esfera((14.2, 487.6, z2 + 3.0), 0.85, mat("Pres_Globo", "#3A7CC0", 0.5), 12)
    gl.fin()
    sofa("Pres_SofaVisitas", None, col, M_en(19.8, 468.3, z2, 180), 6.0, verde, mat("Pres_Cuero2", "#3B7049", 0.6), madera_os)
    mesa("Pres_MesitaVisitas", None, col, M_en(19.8, 471.4, z2), 3.0, 1.4, 1.2, madera)
    for k, (px, py) in enumerate(((13.3, 467.6), (26.4, 467.6))):
        pl = Pieza("Pres_PlantaDesp%d" % k, None, col)
        pl.cil((px, py, z2), 0.6, 1.3, maceta, 12).esfera((px, py, z2 + 2.3), 1.0, hojas, 8)
        pl.fin()
    # secretaria (frente, entre las alas): escritorio, sillas de espera y archiveros
    mesa("Pres_EscritorioSecretaria", None, col, M_en(0, 469.6, z2), 5.0, 1.8, 2.6, madera)
    silla("Pres_SillaSecretaria", None, col, M_en(0, 467.8, z2, 180), madera_os, verde)
    for k, x in enumerate((-8.5, -6.5, 6.5, 8.5)):
        silla("Pres_SillaEspera%d" % k, None, col, M_en(x, 472.3, z2, 0), madera_os, rojo)
    ar = Pieza("Pres_Archiveros", None, col)
    for k, x in enumerate((-11.0, 11.0)):
        for j in range(2):
            y = 467.2 + j * 2.9
            x0_ = x - 0.6 if x < 0 else x - 0.8
            ar.caja((x0_, y, z2), (x0_ + 1.4, y + 2.5, z2 + 4.4), mat("Pres_Archivero", "#7D8A93", 0.4))
    ar.fin()
    # cabildo (ala izquierda)
    mesa("Pres_MesaCabildo", None, col, M_en(-19.5, 478, z2), 3.0, 14.0, 2.9, madera_os)
    for k in range(5):
        y = 472.5 + k * 2.75
        silla("Pres_SillaCabI%d" % k, None, col, M_en(-22.0, y, z2, 90), madera_os, rojo)
        silla("Pres_SillaCabD%d" % k, None, col, M_en(-17.0, y, z2, -90), madera_os, rojo)
    # ---------- torre: cuarto del reloj
    torre = bpy.data.objects.get("Torre")
    if torre:
        ta, tb_ = caja_mundo(torre)
        t = 0.5
        corte = Pieza("corte_reloj", None, col).caja((-2.6, ta.y - 1, 26.9), (2.6, ta.y + 1, 32.1), m_ext).fin()
        mt = torre.material_slots[0].material if torre.material_slots else m_ext
        partes = {"F": ((ta.x, ta.y, ta.z), (tb_.x, ta.y + t, tb_.z)), "B": ((ta.x, tb_.y - t, ta.z), (tb_.x, tb_.y, tb_.z)),
                  "I": ((ta.x, ta.y + t, ta.z), (ta.x + t, tb_.y - t, tb_.z)), "D": ((tb_.x - t, ta.y + t, ta.z), (tb_.x, tb_.y - t, tb_.z))}
        tobs = []
        for k, (a, b) in partes.items():
            ob = Pieza("Pres_TorreMuro" + k, None, col).caja(a, b, mt).fin()
            ob.data.materials.append(mat("Pres_TorreInt", "#9C7B5B", 0.9))
            if k == "F":
                md = ob.modifiers.new("h", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = corte
            tobs.append(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        tcx, tcy = (ta.x + tb_.x) / 2, (ta.y + tb_.y) / 2
        for ob in tobs:
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear(); ob.data = me
            for p in me.polygons:
                v = Vector((tcx - p.center.x, tcy - p.center.y, 0))
                if v.length and Vector((p.normal.x, p.normal.y, 0)).dot(v.normalized()) > 0.7:
                    p.material_index = 1
        bpy.data.objects.remove(corte, do_unlink=True)
        torre.hide_render = True; torre.hide_viewport = True; torre.name = "Torre_original_oculta"
        tz = ta.z + 0.3
        tp = Pieza("Pres_TorrePiso", None, col)
        tp.caja((ta.x + t, ta.y + t, ta.z), (tb_.x - t, tb_.y - t, tz), mat("Pres_Duela", "#A8743F", 0.6))
        tp.caja((ta.x + t, 477.75, 34.4), (tb_.x - t, 478.25, 34.9), madera_os)             # viga
        for z in [tz + 0.8 * k for k in range(16)]:                                          # escalera de mano
            tp.caja((-0.8, tb_.y - t - 0.2, z), (0.8, tb_.y - t - 0.1, z + 0.12), madera_os)
        tp.caja((-0.9, tb_.y - t - 0.25, tz), (-0.75, tb_.y - t - 0.05, tz + 12.8), madera_os)
        tp.caja((0.75, tb_.y - t - 0.25, tz), (0.9, tb_.y - t - 0.05, tz + 12.8), madera_os)
        tp.fin()
        bronce = mat("Pres_Bronce", "#B07A2A", 0.35)
        engrane("Pres_EngraneGrande", (0, ta.y + t + 0.6, 29.5), 2.0, 22, bronce, col)
        engrane("Pres_EngraneMediano", (2.9, ta.y + t + 1.2, 27.2), 1.2, 14, bronce, col)
        engrane("Pres_EngraneChico", (-2.6, ta.y + t + 1.2, 31.6), 0.9, 11, bronce, col)
        pe = Pieza("Pres_Pendulo", None, col)
        pe.caja((-0.08, -0.08, -6.0), (0.08, 0.08, 0), oro)
        pe.M = Matrix.Rotation(math.radians(90), 4, 'X')
        pe.cil((0, -6.6, -0.15), 0.8, 0.3, oro, 20)
        pe.M = Matrix.Identity(4)
        po = pe.fin(); po.location = (0, 478.0, 33.0)
        ca = Pieza("Pres_Campana", None, col)
        for k, (r, h) in enumerate(((1.7, 0.35), (1.45, 0.5), (1.2, 0.7), (1.0, 0.8), (0.85, 0.5))):
            ca.cil((0, 0, -3.0 + sum(hh for _, hh in ((1.7, 0.35), (1.45, 0.5), (1.2, 0.7), (1.0, 0.8), (0.85, 0.5))[:k])), r, h, bronce, 20)
        ca.esfera((0, 0, -2.85), 0.3, bronce, 8)
        co_ = ca.fin(); co_.location = (3.0, 478.0, 34.4)
        luz(None, col, "Pres_LuzTorre", (0, 476.0, 31.5), 600, radio=1.0)
    # ---------- luces
    for k, (x, y) in enumerate(((-16, 471), (0, 471.5), (16, 471), (-16, 482), (16, 482))):
        luz(None, col, "Pres_LuzPB%d" % k, (x, y, 8.6), 1300, radio=1.2)
    for k, (x, y) in enumerate(((0, 470), (-19.5, 474), (-19.5, 484), (19.5, 470.5), (19.5, 481.5), (0, 481))):
        luz(None, col, "Pres_LuzP2%d" % k, (x, y, 16.6), 900, radio=1.0)
    print("presidencia lista:", len(col.objects), "objetos")


construir()
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print("GUARDADO", SALIDA)
