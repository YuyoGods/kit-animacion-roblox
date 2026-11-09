# OBJETOS Y EFECTOS CARICATURA (estilo Roblox, low poly) para cualquier episodio.
# Uso dentro de Blender:  import objetos_cartoon as oc ; oc.elefante("Elefante", coleccion) ...
# Cada funcion crea UN objeto (con su origen en la base, mirando a -Y) y lo devuelve. Tamanos pensados
# para personajes de ~5 unidades de alto.
#   burbuja_pensamiento · puff (humo del "¡pop!") + animar_puff · nube_lluvia · pan · elefante · sombrero_bruja
#   escoba · gato · paraguas · cuaderno · linterna · lonchera · crear_monstruo (desde el rig de un personaje)
import bpy, bmesh, math, os
from mathutils import Vector, Matrix


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat(nombre, color, rough=0.6, emit=0.0, cull=False):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        sal = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(bs.outputs["BSDF"], sal.inputs["Surface"])
    h = color.lstrip("#")
    c = tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    bs.inputs["Base Color"].default_value = (*c, 1)
    bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = (*c, 1); bs.inputs["Emission Strength"].default_value = emit
    m.use_backface_culling = cull
    m.diffuse_color = (*c, 1)
    return m


class P:
    """junta cajas/cilindros/conos/esferas en un solo objeto."""
    def __init__(self, nombre, col):
        self.nombre, self.col, self.bm, self.mats, self.M = nombre, col, bmesh.new(), [], Matrix.Identity(4)

    def _i(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _marcar(self, res, m):
        i = self._i(m)
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = i
        return self

    def caja(self, c, t, m, rot=None):
        R = Matrix.Rotation(math.radians(rot[1]), 4, rot[0]) if rot else Matrix.Identity(4)
        res = bmesh.ops.create_cube(self.bm, size=1.0, matrix=self.M @ Matrix.Translation(c) @ R @ Matrix.Diagonal((*t, 1)))
        return self._marcar(res, m)

    def cono(self, c, r1, r2, h, m, segs=12, rot=None):
        R = Matrix.Rotation(math.radians(rot[1]), 4, rot[0]) if rot else Matrix.Identity(4)
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r1, radius2=r2, depth=h,
                                    matrix=self.M @ Matrix.Translation(c) @ R @ Matrix.Translation((0, 0, h / 2)))
        return self._marcar(res, m)

    def esfera(self, c, r, m, esc=(1, 1, 1), segs=10):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r,
                                        matrix=self.M @ Matrix.Translation(c) @ Matrix.Diagonal((*esc, 1)))
        return self._marcar(res, m)

    def ico(self, c, r, m, sub=1):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=self.M @ Matrix.Translation(c))
        return self._marcar(res, m)

    def fin(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.nombre); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        o = bpy.data.objects.new(self.nombre, me); self.col.objects.link(o)
        for p in me.polygons:
            p.use_smooth = False
        return o


def contorno(o, grosor=0.06):
    """borde negro de caricatura (casco invertido).
    El borde NO proyecta sombra (prueba D, 2026-11-08): si la proyecta, oscurece y llena de grano la cara de objetos
    delgados (galleta: brillo 134 -> 126 con grano); con el rayo de sombra transparente queda igual que sin borde."""
    negro = mat("CT_Contorno", "#111111", 0.9, cull=True)
    nt = negro.node_tree
    if "SinSombra" not in nt.nodes:
        sal = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        bs = sal.inputs["Surface"].links[0].from_node
        lp = nt.nodes.new("ShaderNodeLightPath")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader"); mx.name = "SinSombra"
        nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
        nt.links.new(bs.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], sal.inputs["Surface"])
    o.data.materials.append(negro)
    md = o.modifiers.new("Contorno", 'SOLIDIFY')
    md.thickness = grosor; md.offset = 1.0; md.use_flip_normals = True; md.material_offset = len(o.data.materials) - 1
    return o


# ----------------------------------------------------------------- burbuja de pensamiento
def burbuja_pensamiento(nombre, col):
    """nube blanca con contorno y dos bolitas abajo a la izquierda. Origen = punta de la cola (donde va la cabeza).
    Ponerle un icono adentro (objeto aparte) y girarla hacia la camara de cada toma."""
    b = mat("CT_Burbuja", "#FFFFFF", 0.5, emit=0.9)   # siempre blanca, aunque este en sombra
    p = P(nombre, col)
    for (x, z, r) in ((0.0, 3.4, 1.35), (-1.25, 3.1, 1.0), (1.25, 3.1, 1.05), (-0.6, 2.5, 0.95), (0.7, 2.5, 0.95), (0.1, 4.1, 0.9)):
        p.esfera((x, 0, z), r, b, esc=(1.0, 0.3, 0.85), segs=16)
    p.esfera((-1.1, 0, 1.25), 0.38, b, esc=(1, 0.4, 1), segs=12)
    p.esfera((-1.5, 0, 0.45), 0.22, b, esc=(1, 0.4, 1), segs=10)
    return contorno(p.fin(), 0.07)


# ----------------------------------------------------------------- humo del "¡pop!"
def puff(nombre, col):
    m = mat("CT_Humo", "#F2F2F2", 0.9)
    p = P(nombre, col)
    for k in range(7):
        a = 2 * math.pi * k / 7
        p.ico((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.3 * math.sin(3 * a)), 0.75, m)
    p.ico((0, 0, 0.5), 1.0, m)
    return p.fin()


def animar_puff(o, f0, tam=1.0, sube=1.2):
    """aparece de golpe y se deshace en ~12 fotogramas."""
    z0 = o.location.z
    for f, s, dz in ((f0 - 1, 0.0, 0), (f0, 0.4, 0), (f0 + 3, 1.25, 0.3), (f0 + 7, 1.0, 0.7), (f0 + 12, 0.0, sube)):
        o.scale = (s * tam,) * 3; o.location.z = z0 + dz
        o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", index=2, frame=f)


def aparecer_pop(o, f0, tam=1.0):
    """objeto que aparece con rebote (0 -> 120 % -> 100 %)."""
    for f, s in ((f0 - 1, 0.0), (f0 + 2, 1.2), (f0 + 5, 0.95), (f0 + 7, 1.0)):
        o.scale = (s * tam,) * 3
        o.keyframe_insert("scale", frame=f)


# ----------------------------------------------------------------- nube que llueve (sigue a un personaje)
def nube_lluvia(nombre, col):
    g = mat("CT_NubeGris", "#8A93A0", 0.9); a = mat("CT_Gota", "#7FB6E6", 0.2)
    p = P(nombre, col)
    for (x, y, z, r) in ((0, 0, 0, 1.0), (-1.1, 0.1, -0.1, 0.8), (1.1, -0.1, -0.1, 0.85), (0.4, 0.5, 0.25, 0.75), (-0.5, -0.4, 0.2, 0.7)):
        p.esfera((x, y, z), r, g, esc=(1.1, 1.0, 0.7), segs=12)
    nube = p.fin()
    gotas = P(nombre + "_Gotas", col)
    k = 0
    for gx in (-1.4, -0.7, 0.0, 0.7, 1.4):
        for gy in (-0.6, 0.5):
            for capa in range(3):
                z = -0.8 - capa * 2.0 - (k % 3) * 0.65
                gotas.caja((gx + 0.15 * (k % 2), gy, z), (0.06, 0.06, 0.45), a)
                k += 1
    go = gotas.fin()
    go.parent = nube
    fc = go.driver_add("location", 2)
    fc.driver.expression = "-((frame * 0.45) % 2.0)"    # lluvia en bucle
    return nube


# ----------------------------------------------------------------- comida y objetos
def pan(nombre, col):
    c = mat("CT_Pan", "#C98A3E", 0.7); cl = mat("CT_PanClaro", "#E8C084", 0.7)
    p = P(nombre, col)
    p.esfera((0, 0, 0.35), 0.5, c, esc=(1.6, 0.9, 0.75), segs=14)
    for x in (-0.4, 0.0, 0.4):
        p.caja((x, 0, 0.72), (0.08, 0.55, 0.04), cl, rot=('Z', 20))
    return p.fin()


def elefante(nombre, col):
    r = mat("CT_ElefanteRosa", "#F2A6C4", 0.7); o = mat("CT_ElefanteOreja", "#DE7EA6", 0.7)
    n = mat("CT_Negro", "#151515", 0.4); bl = mat("CT_Blanco", "#F7F4EC", 0.5)
    p = P(nombre, col)
    p.caja((0, 0.4, 3.6), (3.2, 5.0, 3.0), r)                       # cuerpo (frente hacia -y)
    for x in (-1.0, 1.0):
        for y in (-1.4, 2.2):
            p.caja((x, y, 1.05), (0.95, 0.95, 2.1), r)
    p.caja((0, -2.6, 4.6), (2.4, 2.0, 2.3), r)                      # cabeza
    for x in (-1.5, 1.5):
        p.caja((x, -2.3, 4.7), (0.25, 1.8, 2.3), o)                 # orejas
    for k, (z, s) in enumerate(((3.6, 0.8), (2.8, 0.65), (2.1, 0.5))):
        p.caja((0, -3.75 - 0.1 * k, z), (s, 0.7, 0.85), r)            # trompa
    for x in (-0.6, 0.6):
        p.caja((x, -3.62, 5.15), (0.3, 0.05, 0.35), n)
        p.caja((x * 1.3, -3.7, 3.55), (0.18, 0.6, 0.18), bl, rot=('X', -25))
    p.caja((0, 3.0, 3.6), (0.15, 0.15, 1.4), r, rot=('X', 25))
    return p.fin()


def sombrero_bruja(nombre, col):
    n = mat("CT_SombreroNegro", "#1F1B2E", 0.6); mo = mat("CT_Morado", "#6B4C9A", 0.6)
    p = P(nombre, col)
    p.cono((0, 0, 0), 1.25, 1.25, 0.08, n, 20)
    p.cono((0, 0, 0.08), 0.62, 0.05, 1.8, n, 14, rot=('X', 8))
    p.cono((0, 0, 0.08), 0.64, 0.6, 0.25, mo, 14)
    return p.fin()


def escoba(nombre, col):
    mad = mat("CT_PaloEscoba", "#7A4A28", 0.7); paja = mat("CT_Paja", "#D9B45A", 0.9)
    p = P(nombre, col)
    p.cono((0, 0, 1.0), 0.06, 0.06, 4.0, mad, 8)
    p.cono((0, 0, 0), 0.45, 0.12, 1.1, paja, 12)
    p.cono((0, 0, 0.95), 0.14, 0.14, 0.12, mat("CT_Morado", "#6B4C9A"), 10)
    return p.fin()


def gato(nombre, col, color="#1C1C22", cabeza_aparte=False):
    """gato mirando a -Y. Con cabeza_aparte=True la cabeza es un objeto hijo que se puede girar
    (<nombre>_Cabeza, origen en el cuello) y los ojos otro (<nombre>_Ojos, escalar en Z = parpadear)."""
    c = mat("CT_Gato_" + color, color, 0.8); oj = mat("CT_OjoGato", "#C9F25A", 0.3, emit=1.5); ro = mat("CT_NarizGato", "#F29BB2", 0.5)
    p = P(nombre, col)
    p.caja((0, 0.2, 0.75), (0.7, 1.4, 0.65), c)                      # cuerpo
    for x in (-0.25, 0.25):
        for y in (-0.3, 0.7):
            p.caja((x, y, 0.22), (0.2, 0.2, 0.45), c)
    for k, (y, z) in enumerate(((0.95, 0.95), (1.1, 1.3), (1.1, 1.7))):
        p.caja((0, y, z), (0.14, 0.14, 0.4), c, rot=('X', 30 - 30 * k))
    cuello, centro_ojos = Vector((0, -0.5, 1.0)), Vector((0, -1.11, 1.2))
    h = P(nombre + "_Cabeza", col) if cabeza_aparte else p
    e = P(nombre + "_Ojos", col) if cabeza_aparte else p
    if cabeza_aparte:
        h.M = Matrix.Translation(-cuello); e.M = Matrix.Translation(-centro_ojos)
    h.caja((0, -0.75, 1.15), (0.8, 0.7, 0.65), c)                    # cabeza
    for x in (-0.25, 0.25):
        h.cono((x, -0.75, 1.47), 0.17, 0.0, 0.35, c, 4)
        e.caja((x, -1.11, 1.2), (0.16, 0.03, 0.14), oj)
    h.caja((0, -1.11, 1.05), (0.08, 0.03, 0.06), ro)
    cuerpo = p.fin()
    if cabeza_aparte:
        cab = h.fin(); cab.parent = cuerpo; cab.location = cuello
        ojos = e.fin(); ojos.parent = cab; ojos.location = centro_ojos - cuello
    return cuerpo


def paraguas(nombre, col, color="#1E1E24"):
    t = mat("CT_Paraguas_" + color, color, 0.6); mad = mat("CT_PaloEscoba", "#7A4A28", 0.7)
    p = P(nombre, col)
    p.cono((0, 0, 3.0), 2.3, 0.05, 0.9, t, 8)                        # tela abierta
    p.cono((0, 0, 0.3), 0.05, 0.05, 3.7, mad, 6)
    p.caja((0.15, 0, 0.3), (0.35, 0.1, 0.1), mad); p.caja((0.32, 0, 0.45), (0.1, 0.1, 0.35), mad)
    return p.fin()


def cuaderno(nombre, col, imagen_izq=None, imagen_der=None):
    """cuaderno abierto; las hojas pueden llevar una imagen (png)."""
    tapa = mat("CT_TapaCuaderno", "#2B2F3A", 0.6)
    p = P(nombre, col)
    p.caja((0, 0, 0.03), (2.2, 1.5, 0.06), tapa)
    hoja_i = _mat_hoja(nombre + "_HojaI", imagen_izq); hoja_d = _mat_hoja(nombre + "_HojaD", imagen_der)
    cu = p.fin()
    for k, (x, m) in enumerate(((-0.53, hoja_i), (0.53, hoja_d))):
        h = P(nombre + ("_HojaI" if k == 0 else "_HojaD"), col)
        h.caja((x, 0, 0.075), (1.0, 1.4, 0.03), m)
        ho = h.fin(); ho.parent = cu
    return cu


def _mat_hoja(nombre, imagen):
    m = mat(nombre, "#FAF8F0", 0.8)
    if imagen and os.path.exists(imagen):
        nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        img = bpy.data.images.load(imagen, check_existing=True); img.pack()
        co = nt.nodes.new("ShaderNodeTexCoord"); tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.extension = 'CLIP'
        nt.links.new(co.outputs["Generated"], tx.inputs["Vector"]); nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
    return m


def linterna(nombre, col, con_luz=True):
    me = mat("CT_MetalNegro", "#26262B", 0.4); fu = mat("CT_FuegoLinterna", "#FFC45C", 0.4, emit=8.0)
    p = P(nombre, col)
    p.caja((0, 0, 0.1), (0.7, 0.7, 0.2), me); p.caja((0, 0, 1.0), (0.7, 0.7, 0.15), me)
    for x in (-0.3, 0.3):
        for y in (-0.3, 0.3):
            p.caja((x, y, 0.55), (0.08, 0.08, 0.9), me)
    p.caja((0, 0, 0.55), (0.45, 0.45, 0.7), fu)
    p.cono((0, 0, 1.07), 0.08, 0.08, 0.5, me, 6)
    o = p.fin()
    if con_luz:
        ld = bpy.data.lights.new(nombre + "_Luz", 'POINT'); ld.energy = 120; ld.color = (1.0, 0.75, 0.4); ld.shadow_soft_size = 0.4
        lo = bpy.data.objects.new(nombre + "_Luz", ld); col.objects.link(lo); lo.parent = o; lo.location = (0, 0, 0.6)
    return o


def lonchera(nombre, col, color="#D9433A"):
    c = mat("CT_Lonchera_" + color, color, 0.5); n = mat("CT_Negro", "#151515", 0.4)
    p = P(nombre, col)
    p.caja((0, 0, 0.45), (1.4, 0.6, 0.9), c)
    p.caja((-0.35, 0, 1.0), (0.08, 0.08, 0.25), n); p.caja((0.35, 0, 1.0), (0.08, 0.08, 0.25), n); p.caja((0, 0, 1.13), (0.78, 0.08, 0.08), n)
    return p.fin()


# ----------------------------------------------------------------- galleta de la fortuna
# Referencia (foto del usuario y recetas): un disco delgado doblado a la mitad sobre el papelito y con las puntas juntas
# (forma de media luna con un pliegue). Abierta: se parte en el pliegue en DOS mitades como triangulos y el papelito
# blanco con el texto queda en medio, horizontal.
def _mat_galleta():
    m = bpy.data.materials.get("CT_Galleta")
    if m:
        return m
    m = mat("CT_Galleta", "#e3ab5f", 0.55)
    nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*[lin(int("cf8f43"[i:i + 2], 16) / 255) for i in (0, 2, 4)], 1)   # tostado
    cr.color_ramp.elements[1].color = (*[lin(int("efc27e"[i:i + 2], 16) / 255) for i in (0, 2, 4)], 1)   # claro
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], bs.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _malla_galleta(nombre, r=0.55, lado=0):
    """disco de radio r doblado (taco) y con las puntas hacia abajo y juntas. lado: 0 = entera, +1/-1 = solo esa mitad."""
    bm = bmesh.new()
    nr, ns = 10, 40
    filas = []
    for i in range(nr + 1):
        rr = r * i / nr
        fila = []
        for j in range(ns):
            t = 2 * math.pi * j / ns
            x, y = rr * math.cos(t), rr * math.sin(t)
            if lado and x * lado < -1e-6:
                x = 0.0                                   # media galleta: lo del otro lado se aplasta al pliegue
            # 1) doblez de taco alrededor del eje X: los bordes suben y casi se cierran (dos capas sobre el papelito)
            a = (y / r) * math.radians(118)
            Rf = r / math.radians(118)
            y1, z1 = Rf * math.sin(a), Rf * (1 - math.cos(a))
            # 2) pliegue en medio: cada mitad gira hacia adelante (vista de arriba: una V) y las puntas bajan un poco.
            #    Asi cada mitad queda gordita y triangular, como la galleta real.
            g = math.radians(48) * min(1.0, abs(x) / (0.35 * r))
            sx = 1 if x >= 0 else -1
            x2 = sx * abs(x) * math.cos(g) * 0.95
            y2 = y1 - abs(x) * math.sin(g) * 0.9
            z2 = z1 - 0.18 * (abs(x) / r) ** 2 * r
            fila.append(bm.verts.new((x2, y2, z2)))
        filas.append(fila)
    centro = filas[0][0]
    for j in range(ns):
        bm.faces.new((centro, filas[1][j], filas[1][(j + 1) % ns])) if j == 0 or True else None
    for i in range(1, nr):
        for j in range(ns):
            bm.faces.new((filas[i][j], filas[i + 1][j], filas[i + 1][(j + 1) % ns], filas[i][(j + 1) % ns]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    return me


def galleta_fortuna(nombre, col, abierta=False, texto="Hoy, tu crush te va a decir que no", tam=1.0):
    """galleta de la fortuna. Cerrada: un objeto. Abierta: devuelve el vacio padre con las dos mitades
    (<nombre>_Izq, <nombre>_Der) y el papelito (<nombre>_Papel, con su texto <nombre>_Texto, editable con .data.body).
    Origen en la base; mira a -Y; tamano pensado para la mano de un personaje de ~5 (tam escala todo)."""
    mg = _mat_galleta()
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.empty_display_size = 0.4
    def pieza(nom, lado):
        o = bpy.data.objects.new(nom, _malla_galleta(nom, lado=lado)); col.objects.link(o)
        o.data.materials.append(mg)
        s = o.modifiers.new("Grosor", 'SOLIDIFY'); s.thickness = 0.06; s.offset = 0
        d = o.modifiers.new("Liso", 'SUBSURF'); d.levels = 1; d.render_levels = 2
        o.parent = raiz
        return o
    if not abierta:
        g = pieza(nombre + "_Galleta", 0)
        g.location = (0, 0, 0.42)
        # papelito asomando por un costado (como en la vida real)
        pap = bpy.data.objects.new(nombre + "_Papel", _papel(nombre + "_Papel", 0.5, 0.11)); col.objects.link(pap)
        pap.parent = raiz; pap.location = (0.48, -0.02, 0.32); pap.rotation_euler = (math.radians(90), 0, math.radians(-12))
    else:
        for lado, nom in ((-1, "_Izq"), (1, "_Der")):
            h = pieza(nombre + nom, lado)
            h.location = (lado * 1.15, 0, 0.36)
            h.rotation_euler = (0, 0, math.radians(lado * 18))
        # papel grande y letra gruesa: tiene que leerse en un celular (formato Short)
        pap = bpy.data.objects.new(nombre + "_Papel", _papel(nombre + "_Papel", 2.1, 0.62)); col.objects.link(pap)
        pap.parent = raiz; pap.location = (0, -0.05, 0.42); pap.rotation_euler = (math.radians(90), 0, 0)
        cu = bpy.data.curves.new(nombre + "_Texto", 'FONT')
        cu.body = _partir(texto, 18).upper(); cu.size = 0.17; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_line = 0.95
        f = r"C:\Windows\Fonts\arialbd.ttf"
        if os.path.exists(f):
            cu.font = bpy.data.fonts.load(f, check_existing=True)
        cu.materials.append(mat("CT_Tinta", "#2b2b2b", 0.6))
        t = bpy.data.objects.new(nombre + "_Texto", cu); col.objects.link(t)
        t.parent = pap; t.location = (0, 0, 0.045)          # delante de la curvita del papel (el papel ya esta girado)
    raiz.scale = (tam, tam, tam)
    return raiz


def _papel(nombre, w, h):
    me = bpy.data.meshes.new(nombre)
    n = 8
    vs, fs = [], []
    for i in range(n + 1):                                  # tira con una curvita, como papel de verdad
        x = -w / 2 + w * i / n
        z = 0.03 * math.sin(math.pi * i / n)
        vs += [(x, -h / 2, z), (x, h / 2, z)]
    for i in range(n):
        fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me.from_pydata(vs, [], fs)
    me.materials.append(mat("CT_Papelito", "#fbfbf6", 0.7))
    return me


def _partir(texto, ancho):
    """parte el texto en renglones de ~ancho letras (para que quepa en el papelito)."""
    out, linea = [], ""
    for w in texto.split():
        if len(linea) + len(w) + 1 > ancho and linea:
            out.append(linea); linea = w
        else:
            linea = (linea + " " + w).strip()
    out.append(linea)
    return "\n".join(out)


# ----------------------------------------------------------------- personajes
def excluir(col):
    """excluye una coleccion de la capa de vista (ej. las figuras de control '_Widgets' de un rig)."""
    def buscar(lc):
        if lc.collection == col:
            return lc
        for h in lc.children:
            r = buscar(h)
            if r:
                return r
    lc = buscar(bpy.context.view_layer.layer_collection)
    if lc:
        lc.exclude = True


def anexar_personaje(rig_blend, col_origen, destino):
    """trae un personaje ya rigueado (su coleccion) a la escena y devuelve su rig."""
    with bpy.data.libraries.load(rig_blend, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c in (col_origen, col_origen + "_Widgets")]
    rig = None
    for c in dst.collections:
        if not c:
            continue
        destino.children.link(c)
        if c.name.endswith("_Widgets"):
            excluir(c)
        else:
            rig = next(o for o in c.objects if o.type == 'ARMATURE')
    return rig


# ----------------------------------------------------------------- monstruo hecho desde el rig de un personaje
def _a_hueso(o, rig, hueso, W):
    """pega el objeto al hueso dejandolo donde esta W (matriz del mundo)."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[hueso]
    padre = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = hueso
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_basis = padre.inverted() @ W


def copiar_personaje(rig, prefijo, col):
    """copia un personaje que ya esta en la escena (rig + piezas), con sus restricciones e IK apuntando a la copia."""
    viejo = rig.name.replace("_Rig", "")
    nuevo = rig.copy(); nuevo.data = rig.data.copy(); nuevo.name = prefijo + "_Rig"
    col.objects.link(nuevo)
    for pb in nuevo.pose.bones:
        for c in pb.constraints:
            for at in ("target", "pole_target"):
                if getattr(c, at, None) == rig:
                    setattr(c, at, nuevo)
    if nuevo.animation_data:
        for d in nuevo.animation_data.drivers:
            for v in d.driver.variables:
                for t in v.targets:
                    if t.id == rig:
                        t.id = nuevo
    for o in rig.children:
        c = o.copy()
        if o.data:
            c.data = o.data.copy()
        c.name = o.name.replace(viejo, prefijo)
        col.objects.link(c)
        c.parent = nuevo; c.parent_type = o.parent_type; c.parent_bone = o.parent_bone
        c.matrix_parent_inverse = o.matrix_parent_inverse.copy(); c.matrix_basis = o.matrix_basis.copy()
    nuevo["copia_de"] = viejo
    return nuevo


def monstruo_desde(rig, prefijo, col, escala=3.0, piezas_venda=("RightLowerArm", "RightUpperArm")):
    """crea el monstruo como COPIA de un personaje que ya esta en la escena (el original no cambia)."""
    return monstruizar(copiar_personaje(rig, prefijo, col), prefijo, col, escala, piezas_venda)


def crear_monstruo(rig_blend, col_origen, prefijo, destino, escala=3.0, piezas_venda=("RightLowerArm", "RightUpperArm")):
    """anexa el personaje desde su .blend y lo convierte en monstruo (usar monstruo_desde si el personaje ya esta en escena)."""
    with bpy.data.libraries.load(rig_blend, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c in (col_origen, col_origen + "_Widgets")]
    col = next(c for c in dst.collections if c and c.name.startswith(col_origen) and not c.name.endswith("_Widgets"))
    col.name = prefijo.upper()
    destino.children.link(col)
    for c in dst.collections:
        if c and c.name.endswith("_Widgets"):
            destino.children.link(c)
            excluir(c)
    rig = next(o for o in col.objects if o.type == 'ARMATURE')
    viejo = rig.name.replace("_Rig", "")
    rig.name = prefijo + "_Rig"
    for o in list(rig.children):
        o.name = o.name.replace(viejo, prefijo)
    rig["copia_de"] = viejo
    return monstruizar(rig, prefijo, col, escala, piezas_venda)


def monstruizar(rig, prefijo, col, escala=3.0, piezas_venda=("RightLowerArm", "RightUpperArm")):
    """oscurece (dejando la venda clara), pone ojos que brillan y picos, encorva, alarga brazos, agranda manos y escala."""
    viejo = rig.get("copia_de", "")
    oscuro = mat("CT_Monstruo", "#17121F", 0.85)
    ojo = mat("CT_OjoMonstruo", "#FFF3B0", 0.3, emit=12.0)
    for o in list(rig.children):
        if o.type != 'MESH':
            continue
        venda = any(o.name.endswith(p) for p in piezas_venda)
        for i, slot in enumerate(o.material_slots):
            if not slot.material:
                continue
            if venda and slot.material.use_nodes:
                m = slot.material.copy(); m.name = prefijo + "_Venda_" + slot.material.name
                nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
                tx = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
                if tx:
                    bw = nt.nodes.new("ShaderNodeRGBToBW"); cr = nt.nodes.new("ShaderNodeValToRGB")
                    cr.color_ramp.elements[0].position = 0.62; cr.color_ramp.elements[1].position = 0.78
                    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
                    mx.inputs[6].default_value = (0.009, 0.006, 0.014, 1)
                    nt.links.new(tx.outputs["Color"], bw.inputs[0]); nt.links.new(bw.outputs[0], cr.inputs[0])
                    nt.links.new(cr.outputs["Color"], mx.inputs[0]); nt.links.new(tx.outputs["Color"], mx.inputs[7])
                    nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
                slot.material = m
            else:
                slot.material = oscuro
    bpy.context.view_layer.update()
    # ojos y picos (en pose de descanso, coordenadas del rig)
    cab = rig.data.bones["Head"]
    hz = (cab.head_local.z + cab.tail_local.z) / 2
    for k, x in enumerate((-0.27, 0.27)):
        p = P(prefijo + "_Ojo%d" % k, col); p.esfera((0, 0, 0), 0.17, ojo, esc=(1.0, 0.5, 1.25), segs=12)
        o = p.fin()
        _a_hueso(o, rig, "Head", rig.matrix_world @ Matrix.Translation((x, -0.66, hz + 0.08)))
    ut = rig.data.bones["UpperTorso"]
    for k, (x, z) in enumerate(((0, 0.15), (0, 0.5), (0, 0.85), (-0.35, 0.35), (0.35, 0.35))):
        p = P(prefijo + "_Pico%d" % k, col); p.cono((0, 0, 0), 0.22, 0.0, 0.75, oscuro, 6, rot=('X', -70))
        o = p.fin()
        _a_hueso(o, rig, "UpperTorso", rig.matrix_world @ Matrix.Translation((x, 0.62, ut.head_local.z + z * (ut.length))))
    # pose encorvada, brazos largos y manos grandes
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'
    pb["UpperTorso"].rotation_euler.x = math.radians(22)
    pb["Head"].rotation_euler.x = math.radians(-14)
    for s in ("Right", "Left"):
        pb[s + "UpperArm"].scale = (1.0, 1.3, 1.0); pb[s + "LowerArm"].scale = (1.0, 1.3, 1.0); pb[s + "Hand"].scale = (1.35, 1.35, 1.35)
        pb[s + "UpperArm"].rotation_euler.x = math.radians(18)
    rig.scale = (escala,) * 3
    rig["monstruo_de"] = viejo
    return rig


# ----------------------------------------------------------------- billete, globo y pastel (EP004, mejorados a pedido)
TEXTURAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vfx_texturas")


def _mat_imagen(nombre, png, rough=0.7, brillo=0.0):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(png, check_existing=True)
    nt.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    if brillo:
        nt.links.new(tx.outputs["Color"], bs.inputs["Emission Color"]); bs.inputs["Emission Strength"].default_value = brillo
    return m


def billete(nombre, col, tam=1.0):
    """billete de caricatura (textura vfx_texturas/billete.png, la hace hacer_billete.py): papel delgado con una curvita
    (como billete de verdad), se ve de los dos lados. Origen al centro; el frente mira a -Y. Ancho 1.2 * tam."""
    w, h, nx, ny = 1.2, 0.512, 16, 6
    me = bpy.data.meshes.new(nombre)
    vs, fs = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            x = (u - 0.5) * w; z = (v - 0.5) * h
            y = 0.05 * math.sin(math.pi * u) + 0.02 * math.sin(2.3 * math.pi * u + 0.6) * (v - 0.5)   # dobladito
            vs.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            fs.append((a, a + 1, a + nx + 2, a + nx + 1))
    me.from_pydata(vs, [], fs)
    lay = me.uv_layers.new(name="UV")
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index
            lay.data[li].uv = ((vi % (nx + 1)) / nx, (vi // (nx + 1)) / ny)
    me.materials.append(_mat_imagen("CT_Billete", os.path.join(TEXTURAS, "billete.png"), 0.65, 0.15))
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    s = o.modifiers.new("Grosor", 'SOLIDIFY'); s.thickness = 0.008
    o.scale = (tam,) * 3
    return o


def globo(nombre, col, color="#ff3d7f", radio=1.0, hilo=3.2):
    """globo de helio brillante (forma de gota, nudito y un hilo con ondita). El ORIGEN es la punta del hilo (la mano):
    el globo queda arriba. Devuelve el vacio raiz; hijos <nombre>_Globo, _Nudo, _Hilo."""
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.empty_display_size = 0.3
    perfil = []                                                 # perfil de gota girado: mas ancho arriba
    for k in range(25):
        t = k / 24.0
        z = -math.cos(math.pi * t)
        r = math.sin(math.pi * t) * (0.86 + 0.14 * t) * (1 - 0.1 * (1 - t) ** 3)
        perfil.append((max(r, 0.0), z * 1.12))
    N = 32
    vs, fs = [], []
    for (r, z) in perfil:
        for i in range(N):
            a = 2 * math.pi * i / N
            vs.append((r * math.cos(a) * radio, r * math.sin(a) * radio, z * radio))
    for k in range(len(perfil) - 1):
        for i in range(N):
            a, b = k * N + i, k * N + (i + 1) % N
            fs.append((a, b, b + N, a + N))
    me = bpy.data.meshes.new(nombre + "_Globo"); me.from_pydata(vs, [], fs)
    for p in me.polygons:
        p.use_smooth = True
    m = bpy.data.materials.get("CT_Globo_" + color)
    if m is None:
        m = mat("CT_Globo_" + color, color, 0.18)
        bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for k, v in (("Coat Weight", 1.0), ("Coat Roughness", 0.05), ("Specular IOR Level", 0.8)):
            if k in bs.inputs:
                bs.inputs[k].default_value = v
    me.materials.append(m)
    g = bpy.data.objects.new(nombre + "_Globo", me); col.objects.link(g); g.parent = raiz
    zb = hilo + 1.12 * radio
    g.location = (0, 0, zb)
    nu = P(nombre + "_Nudo", col)
    nu.cono((0, 0, -0.16 * radio), 0.11 * radio, 0.03 * radio, 0.17 * radio, m, segs=10)
    nudo = nu.fin(); nudo.parent = raiz; nudo.location = (0, 0, zb - 1.12 * radio)
    for p in nudo.data.polygons:
        p.use_smooth = True
    cu = bpy.data.curves.new(nombre + "_Hilo", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.012; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); n = 24; sp.points.add(n - 1)
    zt = zb - 1.12 * radio - 0.15 * radio
    for k in range(n):
        t = k / (n - 1)
        sp.points[k].co = (0.06 * math.sin(t * 9.0), 0.04 * math.sin(t * 6.0 + 1.0), t * zt, 1)
    cu.materials.append(mat("CT_Hilo", "#f4f4f4", 0.6))
    hi = bpy.data.objects.new(nombre + "_Hilo", cu); col.objects.link(hi); hi.parent = raiz
    return raiz


def pastel(nombre, col, tam=1.0):
    """pastel de dos pisos (pan, betun rosa escurrido, fresas y velitas) en su plato, y su gemelo QUEMADO (negro,
    hundido, sin velas) en el mismo lugar. Devuelve la raiz; hijos <nombre>_Bien y <nombre>_Quemado (se cambia uno por
    otro con la escala, ej. en el "puf"). Origen en la base del plato."""
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.empty_display_size = 0.3
    plato = mat("CT_Plato", "#f7f7fb", 0.35)

    def hacer(sufijo, quemado):
        pan_ = mat("CT_Pan_Quemado" if quemado else "CT_Pan", "#2a1a12" if quemado else "#e3b072", 0.9 if quemado else 0.7)
        betun = mat("CT_Betun_Quemado" if quemado else "CT_Betun", "#1b1412" if quemado else "#ff9cc8", 0.95 if quemado else 0.35)
        fresa = mat("CT_Fresa_Quemada" if quemado else "CT_Fresa", "#241612" if quemado else "#e8263f", 0.9 if quemado else 0.3)
        hoja = mat("CT_Hojita", "#3fa34d", 0.5)
        p = P(nombre + sufijo, col)
        p.cono((0, 0, 0), 0.78, 0.82, 0.05, plato, segs=28)
        hund = 0.82 if quemado else 1.0
        p.cono((0, 0, 0.05), 0.58, 0.58, 0.34 * hund, pan_, segs=24)
        p.cono((0, 0, 0.05 + 0.34 * hund), 0.6, 0.6, 0.07, betun, segs=24)
        for i in range(12):                                                      # escurridos de betun
            a = 2 * math.pi * i / 12
            largo = (0.10 + 0.07 * ((i * 7) % 3)) * hund
            p.esfera((0.585 * math.cos(a), 0.585 * math.sin(a), 0.05 + 0.34 * hund - largo / 2 + 0.03), 0.06, betun,
                     esc=(1, 1, largo / 0.12 + 0.6), segs=8)
        z2 = 0.05 + 0.41 * hund
        p.cono((0, 0, z2), 0.38, 0.38, 0.26 * hund, pan_, segs=20)
        p.cono((0, 0, z2 + 0.26 * hund), 0.4, 0.4, 0.06, betun, segs=20)
        zt = z2 + 0.32 * hund
        for i in range(6):                                                       # fresas alrededor
            a = 2 * math.pi * i / 6 + 0.3
            c = (0.27 * math.cos(a), 0.27 * math.sin(a), zt + 0.05)
            p.esfera(c, 0.075, fresa, esc=(1, 1, 1.15), segs=8)
            if not quemado:
                p.cono((c[0], c[1], c[2] + 0.06), 0.05, 0.0, 0.04, hoja, segs=6)
        if not quemado:                                                          # velitas con flamita
            vela, flama = mat("CT_Vela", "#7fd3ff", 0.4), mat("CT_Flama", "#ffc23d", 0.3, emit=4.0)
            for i in range(3):
                a = 2 * math.pi * i / 3
                c = (0.1 * math.cos(a), 0.1 * math.sin(a), zt)
                p.cono(c, 0.022, 0.022, 0.2, vela, segs=8)
                p.esfera((c[0], c[1], zt + 0.25), 0.035, flama, esc=(1, 1, 1.6), segs=8)
        o = p.fin(); o.parent = raiz
        for poly in o.data.polygons:
            poly.use_smooth = True
        return o
    hacer("_Bien", False); q = hacer("_Quemado", True); q.scale = (0, 0, 0)
    raiz.scale = (tam,) * 3
    return raiz


# ----------------------------------------------------------------- objetos nuevos para EP005 (2026-11-08, plano de construccion)
def _acabado(o, angulo=35, bisel=0.015):
    """sombreado suave con bordes duros (> angulo) + bisel chico: se ve terminado sin costo (leccion 66)."""
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        o.data.set_sharp_from_angle(angle=math.radians(angulo))
    except Exception:
        pass
    if bisel:
        b = o.modifiers.new("Bisel", 'BEVEL'); b.width = bisel; b.segments = 2; b.limit_method = 'ANGLE'
    return o


def _arco(p, centro, r, m, grosor=0.035, k=10, desde=0.0, hasta=180.0):
    """arco de tubitos en el plano XZ (para asas y candados)."""
    a0, a1 = math.radians(desde), math.radians(hasta)
    pts = [Vector((centro[0] + r * math.cos(a0 + (a1 - a0) * i / k), centro[1], centro[2] + r * math.sin(a0 + (a1 - a0) * i / k)))
           for i in range(k + 1)]
    for a, b in zip(pts, pts[1:]):
        d = b - a
        p.cono(tuple(a), grosor, grosor, d.length, m, segs=8, rot=('Y', math.degrees(math.atan2(d.x, d.z))))


def candado(nombre, col, tam=1.0, color="#e2b23a"):
    """candado dorado (cuerpo, ojo de la llave y arco gris). Origen en la base; el frente mira a -Y. Alto ~0,8 * tam."""
    p = P(nombre, col)
    oro, gris, negro = mat("CT_Oro_Candado", color, 0.35), mat("CT_Metal", "#9aa3ad", 0.3), mat("CT_Negro", "#151515", 0.5)
    p.caja((0, 0, 0.22), (0.5, 0.18, 0.42), oro)
    p.esfera((0, -0.095, 0.27), 0.045, negro, segs=8)
    p.caja((0, -0.095, 0.2), (0.03, 0.012, 0.09), negro)
    for x in (-0.17, 0.17):
        p.cono((x, 0, 0.4), 0.035, 0.035, 0.08, gris, segs=8)
    _arco(p, (0, 0, 0.48), 0.17, gris)
    o = _acabado(p.fin()); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def camita_gato(nombre, col, color="#d9433a", tam=1.0):
    """camita redonda de mascota: base, cojin claro y borde de bolitas. Origen en la base. Ancho ~1,6 * tam."""
    p = P(nombre, col)
    c, claro = mat("CT_Camita_" + color.lstrip("#"), color, 0.8), mat("CT_Cojin", "#f3d2c7", 0.9)
    p.cono((0, 0, 0), 0.78, 0.78, 0.12, c, segs=24)
    p.cono((0, 0, 0.1), 0.6, 0.6, 0.1, claro, segs=24)
    for i in range(16):
        a = 2 * math.pi * i / 16
        p.esfera((0.68 * math.cos(a), 0.68 * math.sin(a), 0.2), 0.16, c, esc=(1, 1, 0.9), segs=10)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.025); o.scale = (tam,) * 3
    return o


def platito(nombre, col, color="#6fb7ff", tam=1.0):
    """platito de mascota con croquetas. Origen en la base. Ancho ~0,8 * tam."""
    p = P(nombre, col)
    c, cafe = mat("CT_Platito_" + color.lstrip("#"), color, 0.4), mat("CT_Croqueta", "#8a5a2b", 0.8)
    p.cono((0, 0, 0), 0.28, 0.4, 0.13, c, segs=20)
    for i in range(9):
        a = 2.4 * i
        p.esfera((0.16 * math.cos(a) * (i % 3) / 2, 0.16 * math.sin(a) * (i % 3) / 2, 0.13), 0.06, cafe, segs=6)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def tenedor(nombre, col, tam=1.0):
    """tenedor plateado de caricatura, de pie (mango abajo); el frente mira a -Y. Alto ~0,8 * tam."""
    p = P(nombre, col)
    plata = mat("CT_Plata", "#c9ced6", 0.25)
    p.caja((0, 0, 0.27), (0.06, 0.025, 0.54), plata)
    p.caja((0, 0, 0.57), (0.14, 0.025, 0.07), plata)
    for x in (-0.05, 0, 0.05):
        p.caja((x, 0, 0.68), (0.025, 0.025, 0.17), plata)
    o = _acabado(p.fin(), bisel=0.006); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def peluche(nombre, col, color="#b07a4a", tam=1.0):
    """osito de peluche sentado (cafe con panza y hocico claros). Origen en la base; mira a -Y. Alto ~1 * tam."""
    p = P(nombre, col)
    c = mat("CT_Peluche_" + color.lstrip("#"), color, 0.95)
    claro, negro = mat("CT_Peluche_Claro", "#ecd3ad", 0.95), mat("CT_Negro", "#151515", 0.5)
    p.esfera((0, 0, 0.32), 0.32, c, esc=(1, 0.85, 1.05), segs=14)
    p.esfera((0, -0.17, 0.3), 0.2, claro, esc=(1, 0.6, 1.1), segs=12)
    p.esfera((0, 0, 0.78), 0.25, c, segs=14)
    for x in (-0.18, 0.18):
        p.esfera((x, 0, 0.97), 0.09, c, segs=10)
        p.esfera((x * 0.45, -0.22, 0.84), 0.03, negro, segs=6)
        p.esfera((x * 1.7, -0.05, 0.42), 0.1, c, esc=(1, 1, 1.4), segs=10)
        p.esfera((x * 0.95, -0.14, 0.09), 0.12, c, segs=10)
    p.esfera((0, -0.21, 0.73), 0.1, claro, segs=10)
    p.esfera((0, -0.3, 0.76), 0.035, negro, segs=6)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def mochila(nombre, col, color="#1c1c22", color2="#c8323c", tam=1.0):
    """mochila escolar (cuerpo, bolsa de enfrente de otro color, tirantes y asa). Origen en la base; el frente mira a -Y."""
    p = P(nombre, col)
    c, c2 = mat("CT_Mochila_" + color.lstrip("#"), color, 0.7), mat("CT_Mochila2_" + color2.lstrip("#"), color2, 0.7)
    negro = mat("CT_Negro", "#151515", 0.5)
    p.caja((0, 0, 0.45), (0.7, 0.32, 0.86), c)
    p.esfera((0, 0, 0.88), 0.35, c, esc=(1, 0.46, 0.35), segs=16)
    p.caja((0, -0.2, 0.3), (0.52, 0.1, 0.38), c2)
    p.caja((0, -0.255, 0.47), (0.52, 0.012, 0.025), negro)
    for x in (-0.2, 0.2):
        p.caja((x, 0.18, 0.5), (0.08, 0.04, 0.78), c)
    _arco(p, (0, 0, 0.98), 0.08, c, grosor=0.025, k=6)
    o = _acabado(p.fin()); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def mochila_abre(nombre, col, color="#1c1c22", color2="#c8323c", interior="#2a2233", cuaderno="#3f7fd6", tam=1.0):
    """mochila que SE ABRE (igual que mochila(), mismas medidas): la TAPA de arriba (con el asa) es un hijo aparte
    <nombre>_Tapa con la bisagra atras arriba -> tapa.rotation_euler.x = radians(-115) la abre hacia atras.
    Adentro: hueco oscuro, un cuaderno y un lapiz asomados. Origen en la base; el frente mira a -Y. Devuelve el cuerpo."""
    c, c2 = mat("CT_Mochila_" + color.lstrip("#"), color, 0.7), mat("CT_Mochila2_" + color2.lstrip("#"), color2, 0.7)
    negro, hueco = mat("CT_Negro", "#151515", 0.5), mat("CT_MochilaHueco_" + interior.lstrip("#"), interior, 0.95)
    cua, lap = mat("CT_Cuaderno_" + cuaderno.lstrip("#"), cuaderno, 0.6), mat("CT_Lapiz", "#f2c230", 0.6)
    p = P(nombre, col)
    p.caja((0, 0, 0.05), (0.7, 0.32, 0.1), c)                       # fondo
    for x in (-0.33, 0.33):
        p.caja((x, 0, 0.47), (0.04, 0.32, 0.84), c)                 # lados
    for y in (-0.14, 0.14):
        p.caja((0, y, 0.47), (0.7, 0.04, 0.84), c)                  # frente y espalda (arriba queda abierta)
    p.caja((0, 0, 0.6), (0.62, 0.24, 0.02), hueco)                  # el fondo oscuro que se ve al abrir
    for x in (-0.31, 0.31):
        p.caja((x, 0, 0.74), (0.005, 0.24, 0.28), hueco)
    p.caja((0, 0, 0.74), (0.62, 0.005, 0.28), hueco, rot=None)
    p.caja((-0.1, 0.04, 0.7), (0.36, 0.05, 0.34), cua, rot=('X', -8))    # cuaderno asomado (cabe con la tapa cerrada)
    p.caja((0.17, -0.03, 0.71), (0.035, 0.035, 0.34), lap, rot=('Y', 12))  # lapiz
    p.caja((0, -0.2, 0.3), (0.52, 0.1, 0.38), c2)                   # bolsa de enfrente
    p.caja((0, -0.255, 0.47), (0.52, 0.012, 0.025), negro)
    for x in (-0.2, 0.2):
        p.caja((x, 0.18, 0.5), (0.08, 0.04, 0.78), c)               # tirantes
    o = _acabado(p.fin()); contorno(o, 0.02)
    t = P(nombre + "_Tapa", col)                                     # la tapa: origen en la BISAGRA (atras arriba)
    t.esfera((0, -0.16, 0.0), 0.36, c, esc=(1, 0.5, 0.38), segs=18)
    abajo = [vv for vv in t.bm.verts if vv.co.z < -0.001]
    bmesh.ops.delete(t.bm, geom=abajo, context='VERTS')
    t.caja((0, -0.16, 0.012), (0.72, 0.34, 0.024), c)                # orilla de la tapa (la cierra por abajo)
    t.caja((0, -0.33, 0.03), (0.4, 0.012, 0.02), negro)              # cierre
    _arco(t, (0, -0.16, 0.13), 0.08, c, grosor=0.025, k=6)
    tp = _acabado(t.fin()); contorno(tp, 0.02)
    tp.parent = o; tp.location = (0, 0.16, 0.89)
    o.scale = (tam,) * 3
    return o


def gorra(nombre, col, color="#d9433a", visera=None, tam=1.0):
    """gorra de beisbol: media esfera, visera al frente (-Y) y boton arriba. Origen en el centro de la base (va sobre la
    cabeza). Ancho ~1 * tam (para cabeza R15 de ~1,2 usar tam 1,25)."""
    p = P(nombre, col)
    c, v = mat("CT_Gorra_" + color.lstrip("#"), color, 0.7), mat("CT_Visera_" + (visera or color).lstrip("#"), visera or color, 0.7)
    p.esfera((0, 0, 0), 0.5, c, esc=(1, 1, 0.78), segs=20)
    abajo = [vv for vv in p.bm.verts if vv.co.z < -0.001]
    bmesh.ops.delete(p.bm, geom=abajo, context='VERTS')
    p.esfera((0, -0.55, 0.03), 0.42, v, esc=(1, 0.85, 0.07), segs=16)        # visera grande: que se lea "gorra"
    p.esfera((0, 0, 0.39), 0.05, c, segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def carta(nombre, col, texto="PARA EL CHICO DE LA GORRA", dibujo="gorra_helice", color="#FFE8A2", tam=1.0):
    """carta de papel CREMA (se distingue de una mano blanca) con texto arriba y un dibujito abajo (por ahora
    "gorra_helice": la gorra con helice de Sikelpa). Devuelve un vacio padre; el papel queda de pie mirando a -Y.
    Ancho ~1,6 * tam. Hijos: <nombre>_Papel, <nombre>_Texto, <nombre>_Dibujo."""
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.empty_display_size = 0.3
    me = _papel(nombre + "_Papel", 1.6, 1.1)
    me.materials.clear(); me.materials.append(mat("CT_Papel_Carta", color, 0.75))
    pap = bpy.data.objects.new(nombre + "_Papel", me); col.objects.link(pap)
    pap.parent = raiz; pap.location = (0, 0, 0.6); pap.rotation_euler = (math.radians(90), 0, 0)
    cu = bpy.data.curves.new(nombre + "_Texto", 'FONT')
    cu.body = _partir(texto, 14).upper(); cu.size = 0.19; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_line = 0.95
    f = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(f):
        cu.font = bpy.data.fonts.load(f, check_existing=True)
    cu.materials.append(mat("CT_Tinta", "#2b2b2b", 0.6))
    t = bpy.data.objects.new(nombre + "_Texto", cu); col.objects.link(t)
    t.parent = pap; t.location = (0, 0.25, 0.045)
    if dibujo == "gorra_helice":                       # dibujo plano sobre el papel (coordenadas del papel: XY, Z afuera)
        d = P(nombre + "_Dibujo", col)
        rojo, verde = mat("CT_Dib_Rojo", "#d9433a", 0.8), mat("CT_Dib_Verde", "#3aa655", 0.8)
        azul, amar, negro = mat("CT_Dib_Azul", "#2f6fd6", 0.8), mat("CT_Dib_Amarillo", "#f2c230", 0.8), mat("CT_Negro", "#151515", 0.5)
        d.esfera((0, -0.24, 0), 0.2, rojo, esc=(1, 0.75, 0.05), segs=16)
        abajo = [vv for vv in d.bm.verts if vv.co.y < -0.24 - 0.001]
        bmesh.ops.delete(d.bm, geom=abajo, context='VERTS')
        d.caja((-0.12, -0.25, 0), (0.3, 0.035, 0.02), verde)
        d.caja((0, -0.03, 0), (0.012, 0.07, 0.02), negro)
        d.esfera((-0.09, 0.01, 0), 0.08, azul, esc=(1, 0.3, 0.2), segs=10)
        d.esfera((0.09, 0.01, 0), 0.08, amar, esc=(1, 0.3, 0.2), segs=10)
        dob = d.fin(); dob.parent = pap; dob.location = (0, -0.02, 0.05); dob.scale = (1.6,) * 3   # grande y dentro del papel
    raiz.scale = (tam,) * 3
    return raiz
