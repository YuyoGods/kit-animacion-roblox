# INTERIORES DE CASAS del Pueblo (estilo Roblox, todo con cajas).
# Usa las 2 casas ANCHAS frente a frente cerca de la plaza (CasaAncha_02 = Sikelpa y Ajolota, CasaAncha_01 = Lila).
# 1) Las convierte en piezas propias (eran copias del modelo Casa_Base, estirado 1.25 a lo ancho).
# 2) Las ALARGA hacia atras (FONDO_EXTRA) sin mover la fachada: por el frente se ven igual, por dentro hay mas espacio.
# 3) Paredes huecas con puerta y ventanas (se ve afuera), pisos, losa, escalera, techo, muebles y luces.
#   blender -b Pueblo_v2_set.blend --python interiores.py -- [salida.blend]
# Coordenadas LOCALES de la casa: frente (puerta) hacia -Y, planta baja z 1.0, 2.o piso z 9.4.
# Puerta: rotar en Z el vacio "<Casa>_PuertaBisagra" (0 cerrada, ~1.6 rad abierta hacia adentro).
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from util_interiores import *  # noqa: E402,F401

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SALIDA = ARGS[0] if ARGS else bpy.data.filepath
CASAS = {"CasaAncha_02": "familia", "CasaAncha_01": "lila"}
FONDO_EXTRA = 1.25
T = 0.4
Z0, ZS0, ZS1, ZTECHO = 1.0, 8.6, 9.4, 16.6


# ----------------------------------------------------------------- 1) casa propia (+ alargar hacia atras)
def realizar(inst):
    src = inst.instance_collection
    off = Matrix.Translation(-Vector(src.instance_offset))
    S = Matrix.Diagonal((*inst.scale, 1.0))
    hijos = {c: c.matrix_world.copy() for c in inst.children}          # cortinas que ya cuelgan de la casa
    col = bpy.data.collections.new(inst.name + "_Real")
    bpy.data.collections["Casas"].children.link(col)
    colores = {k: tuple(inst[k]) for k in ("wall_color", "roof_color", "door_color", "accent_color") if k in inst}
    copias, cache = {}, {}
    for o in src.objects:
        n = o.copy()
        if o.data:
            n.data = o.data.copy()
        n.name = inst.name + "_" + o.name
        col.objects.link(n)
        n.parent = inst
        n.matrix_parent_inverse = Matrix.Identity(4)
        n.matrix_basis = S @ off @ o.matrix_world
        if n.type == 'MESH':
            for slot in n.material_slots:
                m = slot.material
                if not (m and m.use_nodes):
                    continue
                if any(nd.type == 'ATTRIBUTE' and nd.attribute_type == 'INSTANCER' for nd in m.node_tree.nodes):
                    if m.name not in cache:
                        mc = m.copy(); mc.name = inst.name + "_" + m.name
                        for nd in list(mc.node_tree.nodes):
                            if nd.type == 'ATTRIBUTE' and nd.attribute_type == 'INSTANCER' and nd.attribute_name in colores:
                                rgb = mc.node_tree.nodes.new("ShaderNodeRGB")
                                rgb.outputs[0].default_value = (*colores[nd.attribute_name], 1)
                                for sal in ("Color", "Vector"):
                                    for l in list(nd.outputs[sal].links):
                                        mc.node_tree.links.new(rgb.outputs[0], l.to_socket)
                                mc.node_tree.nodes.remove(nd)
                        cache[m.name] = mc
                    slot.material = cache[m.name]
        copias[o.name] = n
    inst.instance_type = 'NONE'
    inst.scale = (1.0, 1.0, 1.0)            # la escala ya quedo dentro de cada pieza
    for c, W in hijos.items():
        c.matrix_world = W
    # alargar hacia atras: lo que no esta delante de la fachada se estira desde el plano del frente
    y0 = caja_local(copias["Paredes"])[0].y
    D = Matrix.Translation((0, y0, 0)) @ Matrix.Diagonal((1.0, FONDO_EXTRA, 1.0, 1.0)) @ Matrix.Translation((0, -y0, 0))
    for n in copias.values():
        if n.type == 'MESH' and caja_local(n)[1].y >= y0 + 0.1:
            n.matrix_basis = D @ n.matrix_basis
    inst["interior"] = 1
    return col, copias


# ----------------------------------------------------------------- 2) paredes huecas con puerta y ventanas
def ahuecar(inst, col, copias, pintura):
    par = copias["Paredes"]
    mn, mx = caja_local(par)
    x0, y0, z0 = mn; x1, y1, z1 = mx
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    muros = {"Frente": ((x0, y0, z0), (x1, y0 + T, z1)), "Fondo": ((x0, y1 - T, z0), (x1, y1, z1)),
             "Izq": ((x0, y0 + T, z0), (x0 + T, y1 - T, z1)), "Der": ((x1 - T, y0 + T, z0), (x1, y1 - T, z1))}
    m_ext = par.material_slots[0].material
    tmp = bpy.data.collections.new("tmp_cortes")
    bpy.context.scene.collection.children.link(tmp)
    cortes = {k: [] for k in muros}
    for n in [n for n in copias if n.endswith("_Vidrio") and not n.startswith("Ojo")] + ["Puerta"]:
        a, b = caja_local(copias[n])
        c = (a + b) / 2
        d = {"Frente": abs(c.y - y0), "Fondo": abs(c.y - y1), "Izq": abs(c.x - x0), "Der": abs(c.x - x1)}
        lado = min(d, key=d.get)
        if d[lado] > 1.0:
            continue
        e = 0.03
        if lado in ("Frente", "Fondo"):
            yy = y0 if lado == "Frente" else y1
            cmn, cmx = (a.x - e, yy - 1, a.z - e), (b.x + e, yy + 1, b.z + e)
        else:
            xx = x0 if lado == "Izq" else x1
            cmn, cmx = (xx - 1, a.y - e, a.z - e), (xx + 1, b.y + e, b.z + e)
        if n == "Puerta":
            cmn = (cmn[0], cmn[1], z0 - 0.5)
        cortes[lado].append(Pieza("corte_" + n, inst, tmp).caja(cmn, cmx, m_ext).fin())
    obs = []
    for lado, (a, b) in muros.items():
        ob = Pieza(inst.name + "_Muro" + lado, inst, col).caja(a, b, m_ext).fin()
        ob.data.materials.append(pintura)
        for i, c in enumerate(cortes[lado]):
            md = ob.modifiers.new("h%d" % i, 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = c
        obs.append(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in obs:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg)); ob.modifiers.clear(); ob.data = me
        for p in me.polygons:
            v = Vector((cx - p.center.x, cy - p.center.y, 0))
            if v.length and Vector((p.normal.x, p.normal.y, 0)).dot(v.normalized()) > 0.7:
                p.material_index = 1
    for c in list(tmp.objects):
        bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.collections.remove(tmp)
    bpy.data.objects.remove(par, do_unlink=True)
    for n in [n for n in copias if n.endswith("_Fondo")]:
        bpy.data.objects.remove(copias[n], do_unlink=True)
    return (x0 + T, y0 + T, x1 - T, y1 - T)


def bisagra(inst, col, copias):
    pa, pb = caja_local(copias["Puerta"])
    h = bpy.data.objects.new(inst.name + "_PuertaBisagra", None); col.objects.link(h)
    h.parent = inst; h.matrix_parent_inverse = Matrix.Identity(4)
    h.location = (pa.x, (pa.y + pb.y) / 2, pa.z); h.empty_display_size = 0.6
    H = h.matrix_basis.copy()
    for n, o in copias.items():
        if n.startswith(("Puerta", "Manija")) and n != "Puerta_Marco":
            L = o.matrix_basis.copy()
            o.parent = h; o.matrix_parent_inverse = H.inverted(); o.matrix_basis = L
    h["uso"] = "girar en Z: 0 cerrada, 1.6 abierta hacia adentro"
    return h


# ----------------------------------------------------------------- 3) pisos, losa, escalera, techo
def estructura(inst, col, caja_in, P):
    ix0, iy0, ix1, iy1 = caja_in
    hx = ix0 + 3.0
    y_ini = iy1 - 9.6                                    # 12 escalones de 0.8 que suben hacia el fondo
    piso = Pieza(inst.name + "_Pisos", inst, col)
    piso.caja((ix0, iy0, Z0), (ix1, iy1, Z0 + 0.06), P["piso"])
    piso.caja((hx, iy0, ZS0), (ix1, iy1, ZS1), P["techo"]); piso.caja((ix0, iy0, ZS0), (hx, y_ini, ZS1), P["techo"])
    piso.caja((hx, iy0, ZS1), (ix1, iy1, ZS1 + 0.06), P["piso2"]); piso.caja((ix0, iy0, ZS1), (hx, y_ini, ZS1 + 0.06), P["piso2"])
    piso.caja((ix0, iy0, ZTECHO), (ix1, iy1, ZTECHO + 0.4), P["techo"])
    for z in (Z0 + 0.06, ZS1 + 0.06):
        piso.caja((ix0, iy0, z), (ix1, iy0 + 0.12, z + 0.4), P["zoclo"])
        piso.caja((ix0, iy1 - 0.12, z), (ix1, iy1, z + 0.4), P["zoclo"])
        piso.caja((ix1 - 0.12, iy0, z), (ix1, iy1, z + 0.4), P["zoclo"])
    piso.fin()
    esc = Pieza(inst.name + "_Escalera", inst, col)
    n = 12
    d, s = (iy1 - y_ini) / n, (ZS1 - Z0) / n
    for k in range(n):
        esc.caja((ix0, y_ini + k * d, Z0), (hx, y_ini + (k + 1) * d, Z0 + (k + 1) * s), P["escalon"])
        esc.caja((ix0, y_ini + k * d, Z0 + (k + 1) * s - 0.08), (hx, y_ini + (k + 1) * d, Z0 + (k + 1) * s + 0.02), P["madera"])
    for y in [y_ini + 0.1 + 1.15 * k for k in range(7)]:
        esc.caja((hx - 0.08, y, ZS1), (hx + 0.08, y + 0.16, ZS1 + 3.0), P["barandal"])
    esc.caja((hx - 0.12, y_ini, ZS1 + 3.0), (hx + 0.12, iy1 - 1.6, ZS1 + 3.25), P["madera"])
    esc.caja((ix0, y_ini - 0.12, ZS1), (hx, y_ini + 0.12, ZS1 + 3.25), P["madera"])
    esc.fin()
    return hx, y_ini


# ----------------------------------------------------------------- 4) amueblar (posiciones relativas al tamano de la casa)
PALETAS = {
    "familia": {"pared": "#F1E2C4", "piso": "#B9834F", "piso2": "#C98F57", "sofa": "#3E6FB0", "cojin": "#5C8BCB", "alfombra": "#C0504D",
                "colchaA": "#D23B2E", "colchaB": "#7EC8E3", "acento": "#F2B134"},
    "lila": {"pared": "#DCCBEE", "piso": "#8E5E44", "piso2": "#9C6B4E", "sofa": "#6B4C9A", "cojin": "#8C6CBF", "alfombra": "#2F8F83",
             "colchaA": "#5E3A8C", "colchaB": "#5E3A8C", "acento": "#45B7A8"},
}


def amueblar(inst, col, tipo, caja_in, hx, y_ini):
    C = PALETAS[tipo]
    ix0, iy0, ix1, iy1 = caja_in
    N = inst.name
    madera = mat("Int_Madera", "#8A5A35"); madera_cl = mat("Int_MaderaClara", "#C99A63")
    blanco = mat("Int_Blanco", "#F4F1EA"); negro = mat("Int_Negro", "#202226", 0.4); metal = mat("Int_Metal", "#9AA0A6", 0.35)
    tela = mat("Int_Sofa_" + tipo, C["sofa"], 0.9); cojin = mat("Int_Cojin_" + tipo, C["cojin"], 0.9)
    alfombra = mat("Int_Alfombra_" + tipo, C["alfombra"], 0.95); acento = mat("Int_Acento_" + tipo, C["acento"])
    pantalla = mat("Int_Pantalla", "#1B2A3A", 0.2, emit=0.4); foco = mat("Int_Foco", "#FFE9C2", 0.5, emit=6.0)
    hojas = mat("Int_Hojas", "#3F8F3A", 0.8); maceta = mat("Int_Maceta", "#B5603A")
    libros = [mat("Int_Libro_%d" % i, c) for i, c in enumerate(("#C0392B", "#2E86C1", "#27AE60", "#F1C40F", "#8E44AD", "#E67E22"))]
    z = Z0 + 0.06
    # ---- sala (frente-derecha): sillon mirando a la tele en la pared derecha
    ys = iy0 + 4.2
    p = Pieza(N + "_Alfombra", inst, col); p.caja((ix1 - 7.4, iy0 + 1.0, z), (ix1 - 0.6, iy0 + 7.4, z + 0.05), alfombra); p.fin()
    sofa(N + "_Sofa", inst, col, M_en(ix1 - 5.2, ys, z, 90), 5.4, tela, cojin, madera)
    mesa(N + "_MesaCentro", inst, col, M_en(ix1 - 2.7, ys, z), 1.3, 2.2, 1.15, madera_cl)
    tv = Pieza(N + "_Tele", inst, col)
    tv.caja((ix1 - 0.8, ys - 1.4, z), (ix1 - 0.1, ys + 1.4, z + 1.5), madera)
    tv.caja((ix1 - 0.45, ys - 1.7, z + 1.7), (ix1 - 0.3, ys + 1.7, z + 3.9), negro)
    tv.caja((ix1 - 0.47, ys - 1.55, z + 1.85), (ix1 - 0.44, ys + 1.55, z + 3.75), pantalla)
    tv.fin()
    pl = Pieza(N + "_LamparaPie", inst, col, M_en(ix1 - 6.9, iy0 + 1.3, z))
    pl.cil((0, 0, 0), 0.45, 0.15, metal, 10).cil((0, 0, 0.15), 0.07, 4.2, metal, 6).cil((0, 0, 4.0), 0.6, 0.9, foco, 12)
    pl.fin()
    # ---- comedor (fondo-derecha), lejos del sillon
    mx_, my_ = ix1 - 5.0, iy1 - 5.2
    mesa(N + "_MesaComedor", inst, col, M_en(mx_, my_, z), 4.4, 2.8, 2.9, madera)
    for k, (dx, dy, g) in enumerate(((-1.1, -2.3, 180), (1.1, -2.3, 180), (-1.1, 2.3, 0), (1.1, 2.3, 0))):
        silla(N + "_Silla%d" % k, inst, col, M_en(mx_ + dx, my_ + dy, z, g), madera, acento)
    lampara_techo(N + "_LamparaComedor", inst, col, (mx_, my_, ZS0), metal, foco)
    # ---- cocina (pared del fondo, junto a la escalera) con barra y bancos
    kx = hx + 0.3
    coc = Pieza(N + "_Cocina", inst, col)
    coc.caja((kx, iy1 - 1.7, z), (kx + 1.8, iy1, z + 6.4), blanco)                          # refri
    coc.caja((kx - 0.05, iy1 - 1.75, z + 4.0), (kx + 1.85, iy1 - 1.7, z + 4.05), metal)
    coc.caja((kx + 1.5, iy1 - 1.8, z + 2.2), (kx + 1.6, iy1 - 1.75, z + 3.6), metal)
    c0, c1 = kx + 2.0, kx + 8.4
    coc.caja((c0, iy1 - 1.6, z), (c1, iy1, z + 2.1), blanco)                                 # alacena baja
    coc.caja((c0 - 0.05, iy1 - 1.7, z + 2.1), (c1 + 0.05, iy1, z + 2.3), madera_cl)
    coc.caja((c0 + 1.0, iy1 - 1.4, z + 2.25), (c0 + 2.6, iy1 - 0.4, z + 2.32), metal)       # tarja
    coc.caja((c1 - 1.9, iy1 - 1.5, z + 2.3), (c1 - 0.3, iy1 - 0.2, z + 2.36), negro)       # parrilla
    for bx, by in ((-1.5, -1.2), (-0.7, -1.2), (-1.5, -0.5), (-0.7, -0.5)):
        coc.cil((c1 + bx, iy1 + by, z + 2.36), 0.25, 0.04, metal, 10)
    coc.caja((c0, iy1 - 0.8, z + 4.4), (c1, iy1, z + 6.2), blanco)                          # alacena alta
    coc.caja((c0 + 1.0, iy1 - 4.2, z), (c0 + 4.6, iy1 - 2.8, z + 2.3), madera_cl)          # barra
    coc.fin()
    for k, bx in enumerate((c0 + 1.8, c0 + 3.8)):
        b = Pieza(N + "_Banco%d" % k, inst, col)
        b.cil((bx, iy1 - 4.9, z), 0.12, 2.0, metal, 6).cil((bx, iy1 - 4.9, z + 2.0), 0.45, 0.2, acento, 10)
        b.fin()
    lampara_techo(N + "_LamparaCocina", inst, col, (c0 + 2.8, iy1 - 3.2, ZS0), metal, foco)
    # ---- entrada (frente-izquierda)
    librero(N + "_Librero", inst, col, M_en(ix0 + 4.6, iy0 + 0.4, z, 180), madera, libros)
    planta(N + "_Planta", inst, col, M_en(ix0 + 1.0, iy0 + 1.0, z), maceta, hojas)
    p = Pieza(N + "_Tapete", inst, col); p.caja((-1.8, iy0 + 0.2, z), (1.8, iy0 + 1.9, z + 0.04), acento); p.fin()
    cuadro(N + "_Cuadro1", inst, col, Matrix.Translation((mx_, iy1, z + 5.2)), 2.6, 1.7, madera, mat("Int_Lienzo_" + tipo, C["acento"]))
    lampara_techo(N + "_LamparaSala", inst, col, (ix1 - 4.4, ys, ZS0), metal, foco)
    # ---- 2.o piso
    z2 = ZS1 + 0.06
    p = Pieza(N + "_Alfombra2", inst, col); p.caja((hx + 1.0, iy0 + 3.0, z2), (ix1 - 6.6, iy1 - 3.5, z2 + 0.05), alfombra); p.fin()
    colA = mat("Int_ColchaA_" + tipo, C["colchaA"], 0.9); colB = mat("Int_ColchaB_" + tipo, C["colchaB"], 0.9)
    if tipo == "familia":
        cama(N + "_CamaSikelpa", inst, col, M_en(ix1 - 3.1, iy0 + 3.2, z2, -90), colA, blanco, madera)
        cama(N + "_CamaAjolota", inst, col, M_en(ix1 - 3.1, iy0 + 11.2, z2, -90), colB, blanco, madera)
        buro = Pieza(N + "_Buro", inst, col)
        buro.caja((ix1 - 1.3, iy0 + 6.2, z2), (ix1, iy0 + 8.2, z2 + 1.8), madera_cl)
        buro.cil((ix1 - 0.65, iy0 + 7.2, z2 + 1.8), 0.25, 0.9, metal, 8).cil((ix1 - 0.65, iy0 + 7.2, z2 + 2.6), 0.5, 0.6, foco, 10)
        buro.fin()
        pu = Pieza(N + "_Puff", inst, col); pu.esfera((hx + 3.0, iy0 + 5.0, z2 + 0.8), 1.1, acento, esc=(1, 1, 0.65)); pu.fin()
    else:
        cama(N + "_CamaLila", inst, col, M_en(ix1 - 3.1, iy0 + 6.5, z2, -90), colA, blanco, madera, 5.8, 4.2)
        tocador = Pieza(N + "_Tocador", inst, col)
        tocador.caja((ix1 - 6.6, iy1 - 1.2, z2), (ix1 - 3.4, iy1, z2 + 2.6), madera_cl)
        tocador.caja((ix1 - 5.9, iy1 - 0.15, z2 + 3.0), (ix1 - 4.1, iy1, z2 + 5.6), mat("Int_Espejo", "#BFD7E6", 0.05))
        tocador.fin()
        librero(N + "_LibreroCuarto", inst, col, M_en(hx + 2.0, iy1 - 0.45, z2), madera,
                [mat("Int_Pocion_%d" % i, c) for i, c in enumerate(("#6B4C9A", "#45B7A8", "#C0392B", "#2F8F83"))], 3.0, 5.0)
    esc2 = Pieza(N + "_Escritorio", inst, col)
    esc2.caja((ix0 + 0.3, iy0, z2 + 2.4), (ix0 + 3.3, iy0 + 1.5, z2 + 2.65), madera_cl)
    esc2.caja((ix0 + 0.3, iy0, z2), (ix0 + 0.6, iy0 + 1.5, z2 + 2.4), madera_cl)
    esc2.caja((ix0 + 3.0, iy0, z2), (ix0 + 3.3, iy0 + 1.5, z2 + 2.4), madera_cl)
    esc2.fin()
    silla(N + "_SillaEscritorio", inst, col, M_en(ix0 + 1.8, iy0 + 2.3, z2, 0), madera, acento)
    ropero = Pieza(N + "_Ropero", inst, col)
    rx = ix1 - 10.4 if tipo == "familia" else hx + 6.0
    ropero.caja((rx, iy1 - 1.3, z2), (rx + 3.4, iy1, z2 + 6.2), madera)
    ropero.caja((rx + 1.65, iy1 - 1.35, z2 + 0.3), (rx + 1.75, iy1 - 1.3, z2 + 5.9), negro)
    ropero.fin()
    for k, (px, pc) in enumerate(((hx + 4.0, "#E74C3C"), (hx + 8.0, "#3498DB"))):
        cuadro(N + "_Poster%d" % k, inst, col, Matrix.Translation((px, iy0 + 0.02, z2 + 4.6)) @ Matrix.Rotation(math.pi, 4, 'Z'),
               1.6, 2.2, blanco, mat("Int_Poster%d_%s" % (k, tipo), pc))
    lampara_techo(N + "_LamparaCuarto", inst, col, ((hx + ix1) / 2, (iy0 + iy1) / 2, ZTECHO), metal, foco)
    # ---- luces
    luz(inst, col, N + "_LuzSala", (ix1 - 4.4, ys, ZS0 - 1.4), 340)
    luz(inst, col, N + "_LuzComedor", (mx_, my_, ZS0 - 1.4), 300)
    luz(inst, col, N + "_LuzCocina", (c0 + 2.8, iy1 - 3.2, ZS0 - 1.4), 260)
    luz(inst, col, N + "_LuzCuarto", ((hx + ix1) / 2, iy0 + 4.0, ZTECHO - 1.4), 320)
    luz(inst, col, N + "_LuzCuarto2", ((hx + ix1) / 2, iy1 - 4.0, ZTECHO - 1.4), 300)


def construir():
    for nombre, tipo in CASAS.items():
        inst = bpy.data.objects[nombre]
        if inst.get("interior"):
            print("ya tiene interior:", nombre)
            continue
        C = PALETAS[tipo]
        P = {"piso": mat("Int_Piso_" + tipo, C["piso"], 0.55), "piso2": mat("Int_Piso2_" + tipo, C["piso2"], 0.6),
             "techo": mat("Int_Techo", "#F6F2EA", 0.9), "zoclo": mat("Int_Zoclo", "#FFFFFF", 0.6),
             "escalon": mat("Int_Contrahuella", "#F4F1EA", 0.7), "madera": mat("Int_Madera", "#8A5A35"),
             "barandal": mat("Int_Blanco", "#F4F1EA")}
        col, copias = realizar(inst)
        caja_in = ahuecar(inst, col, copias, mat("Int_Pared_" + tipo, C["pared"], 0.85))
        bisagra(inst, col, copias)
        hx, y_ini = estructura(inst, col, caja_in, P)
        amueblar(inst, col, tipo, caja_in, hx, y_ini)
        print("interior listo:", nombre, tipo, "medidas interiores %.1f x %.1f" % (caja_in[2] - caja_in[0], caja_in[3] - caja_in[1]),
              "objetos:", len(col.objects))


construir()
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, compress=True)
print("GUARDADO", SALIDA)
