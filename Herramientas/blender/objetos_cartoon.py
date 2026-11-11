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

    def anillo(self, c, r_in, r_out, h, m, segs=24, eje='Y'):
        """aro (disco con hoyo) de grosor h centrado en c: eje 'Y' = de pie, de frente a -Y; 'Z' = acostado."""
        bm = self.bm
        M = self.M @ Matrix.Translation(c) @ (Matrix.Rotation(math.radians(90), 4, 'X') if eje == 'Y' else Matrix.Identity(4))
        anillos = []
        for z in (-h / 2, h / 2):
            anillos.append([[bm.verts.new(M @ Vector((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)))
                             for i in range(segs)] for r in (r_in, r_out)])
        (i0, o0), (i1, o1) = anillos
        k = self._i(m)
        for i in range(segs):
            j = (i + 1) % segs
            for q in ((i0[i], o0[i], o0[j], i0[j]), (i1[j], o1[j], o1[i], i1[i]),
                      (o0[i], o1[i], o1[j], o0[j]), (i0[j], i1[j], i1[i], i0[i])):
                bm.faces.new(q).material_index = k
        return self

    def loft(self, secciones, m, tapa_abajo=True, tapa_arriba=True):
        """superficie que une anillos de puntos [(z, [(x, y), ...]), ...] (todos con el mismo numero de puntos)."""
        bm = self.bm
        k = self._i(m)
        an = [[bm.verts.new(self.M @ Vector((x, y, z))) for x, y in pts] for z, pts in secciones]
        n = len(an[0])
        for a, b in zip(an, an[1:]):
            for i in range(n):
                j = (i + 1) % n
                bm.faces.new((a[i], a[j], b[j], b[i])).material_index = k
        if tapa_abajo:
            bm.faces.new(list(reversed(an[0]))).material_index = k
        if tapa_arriba:
            bm.faces.new(an[-1]).material_index = k
        return self

    def placa_xz(self, contorno_xz, y0, grosor, m):
        """placa plana con el contorno dado en el plano XZ (lista de (x, z), sin repetir el primero), de y0 a y0+grosor."""
        bm = self.bm
        k = self._i(m)
        fr = [bm.verts.new(self.M @ Vector((x, y0, z))) for x, z in contorno_xz]
        at = [bm.verts.new(self.M @ Vector((x, y0 + grosor, z))) for x, z in contorno_xz]
        bm.faces.new(fr).material_index = k
        bm.faces.new(list(reversed(at))).material_index = k
        n = len(fr)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((fr[i], at[i], at[j], fr[j])).material_index = k
        return self

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
def burbuja_pensamiento(nombre, col, bolitas=1):
    """nube blanca con contorno y UNA bolita abajo a la izquierda (pedido del usuario 2026-11-11: solo una bolita blanca
    entre la cabeza y la nube; bolitas=2 = la version vieja con dos). Origen = punta de la cola (donde va la cabeza).
    Ponerle un icono adentro (objeto aparte) y girarla hacia la camara de cada toma."""
    b = mat("CT_Burbuja", "#FFFFFF", 0.5, emit=0.9)   # siempre blanca, aunque este en sombra
    p = P(nombre, col)
    for (x, z, r) in ((0.0, 3.4, 1.35), (-1.25, 3.1, 1.0), (1.25, 3.1, 1.05), (-0.6, 2.5, 0.95), (0.7, 2.5, 0.95), (0.1, 4.1, 0.9)):
        p.esfera((x, 0, z), r, b, esc=(1.0, 0.3, 0.85), segs=16)
    if bolitas >= 2:
        p.esfera((-1.1, 0, 1.25), 0.38, b, esc=(1, 0.4, 1), segs=12)
        p.esfera((-1.5, 0, 0.45), 0.22, b, esc=(1, 0.4, 1), segs=10)
    else:
        p.esfera((-1.2, 0, 1.05), 0.3, b, esc=(1, 0.4, 1), segs=12)     # una sola bolita, entre la cabeza y la nube
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


# ----------------------------------------------------------------- objetos de EP006 ("La fuente eligio a mi hermana")
def moneda(nombre, col, tam=1.0, color="#e8b53a", hoyito=True, brillo=0.0):
    """moneda de caricatura DE PIE (cara hacia -Y) con hoyito en medio (como la de 5 yenes: laton, orilla lisa),
    orilla y aro del hoyo en relieve y 8 rayitas. Origen en el centro. Diametro ~0,5 * tam.
    Material propio (CT_Moneda_<nombre>) para hacerla brillar en su momento con brillar(o, f0, f1)."""
    p = P(nombre, col)
    oro = mat("CT_Moneda_" + nombre, color, 0.3, emit=brillo)
    oscuro = mat("CT_Moneda_Rayas", "#a8741c", 0.45)
    R, r = 0.25, 0.065
    if hoyito:
        p.anillo((0, 0, 0), r, R, 0.05, oro, segs=32)
        p.anillo((0, 0, 0), r, r + 0.03, 0.068, oro, segs=24)
    else:
        p.cono((0, 0.025, 0), R, R, 0.05, oro, segs=32, rot=('X', 90))
    p.anillo((0, 0, 0), R - 0.032, R, 0.072, oro, segs=32)
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        p.caja((0.155 * math.cos(a), 0, 0.155 * math.sin(a)), (0.055, 0.066, 0.018), oscuro, rot=('Y', -math.degrees(a)))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01); o.scale = (tam,) * 3
    return o


def brillar(o, f0, f1, fuerza=4.0, rampa=4, color="#ffd34d"):
    """hace BRILLAR un objeto (su primer material: moneda, letras...) de f0 a f1, con subida y bajada de 'rampa' cuadros.
    Se puede llamar varias veces para varios tramos."""
    m = o.data.materials[0]
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    h = color.lstrip("#")
    bs.inputs["Emission Color"].default_value = (*[lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)], 1)
    s = bs.inputs["Emission Strength"]
    for f, v in ((f0 - rampa, 0.0), (f0, fuerza), (f1, fuerza), (f1 + rampa, 0.0)):
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)
    return o


def helado(nombre, col, color="#ff9cc2", tam=1.0, aplastado=False):
    """cono de helado: barquillo con rayas, bola de fresa con chorreadas y una cereza. Origen en la PUNTA del cono (donde
    se agarra); alto ~0,95 * tam. aplastado=True: el helado ya en el piso (charquito, bola chata y el cono tirado),
    origen en el piso."""
    p = P(nombre, col)
    barq, barq2 = mat("CT_Barquillo", "#e0a65a", 0.8), mat("CT_Barquillo_Rayas", "#b97b35", 0.8)
    bola, cereza = mat("CT_Helado_" + color.lstrip("#"), color, 0.45), mat("CT_Cereza", "#d61f3a", 0.3)
    if not aplastado:
        p.cono((0, 0, 0), 0.02, 0.19, 0.55, barq, segs=16)
        for z in (0.2, 0.34, 0.46):
            rr = 0.02 + 0.17 * z / 0.55
            p.cono((0, 0, z), rr + 0.008, rr + 0.008, 0.025, barq2, segs=16)
        p.cono((0, 0, 0.52), 0.205, 0.205, 0.05, barq2, segs=16)
        p.esfera((0, 0, 0.7), 0.215, bola, esc=(1, 1, 0.92), segs=16)
        for k in range(10):                                   # faldita ondulada de la bola sobre el cono
            ar = 2 * math.pi * k / 10
            p.esfera((0.17 * math.cos(ar), 0.17 * math.sin(ar), 0.56 - 0.025 * (k % 2)), 0.065, bola, esc=(1, 1, 0.8), segs=8)
        p.esfera((0, 0, 0.93), 0.05, cereza, segs=10)
    else:
        p.esfera((0, 0, 0.0), 0.45, bola, esc=(1, 0.8, 0.07), segs=20)
        p.esfera((0.04, 0.0, 0.05), 0.21, bola, esc=(1, 1, 0.5), segs=14)
        p.cono((0.25, 0.12, 0.13), 0.02, 0.17, 0.5, barq, segs=14, rot=('Y', 100))
        p.esfera((-0.24, 0.14, 0.04), 0.045, cereza, segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def control(nombre, col, color="#2a2a33", tam=1.0):
    """control de videojuego (sin marca): cuerpo redondeado con dos agarraderas, cruceta, 4 botones de colores y dos
    palancas. ACOSTADO (botones hacia +Z), las agarraderas hacia -Y. Origen en el centro. Ancho ~0,9 * tam."""
    p = P(nombre, col)
    c, gris, negro = mat("CT_Control_" + color.lstrip("#"), color, 0.5), mat("CT_Control_Gris", "#5a5a66", 0.5), mat("CT_Negro", "#151515", 0.5)
    p.esfera((0, 0.02, 0), 0.3, c, esc=(1.25, 0.62, 0.32), segs=18)
    for x in (-0.27, 0.27):
        p.esfera((x, -0.12, -0.01), 0.15, c, esc=(0.9, 1.25, 0.75), segs=12)
    p.caja((-0.2, 0.04, 0.08), (0.13, 0.042, 0.03), negro)
    p.caja((-0.2, 0.04, 0.08), (0.042, 0.13, 0.03), negro)
    for (dx, dy), cb in zip(((0, 0.055), (0.055, 0), (0, -0.055), (-0.055, 0)), ("#3aa655", "#d9433a", "#2f6fd6", "#f2c230")):
        p.cono((0.2 + dx, 0.04 + dy, 0.055), 0.027, 0.027, 0.04, mat("CT_Boton_" + cb.lstrip("#"), cb, 0.3), segs=10)
    for x in (-0.08, 0.08):
        p.cono((x, -0.07, 0.065), 0.046, 0.046, 0.03, gris, segs=12)
        p.cono((x, -0.07, 0.09), 0.03, 0.035, 0.04, negro, segs=10)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def _superelipse(w, d, n=20, e=4.0):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        pts.append((w * math.copysign(abs(c) ** (2 / e), c), d * math.copysign(abs(s) ** (2 / e), s)))
    return pts


def bolsa_papas(nombre, col, color="#f2c230", color2="#d9433a", tam=1.0, abierta=True):
    """bolsa de papas (sin marca): inflada en medio y plana en los cierres, cierre de abajo en zigzag, franja roja y una
    papa dibujada al frente. abierta=True: arriba abierta con papas asomando (para comer de ella). De pie, frente -Y.
    Origen en la base. Alto ~1,0 * tam, ancho ~0,62."""
    p = P(nombre, col)
    c, c2 = mat("CT_Bolsa_" + color.lstrip("#"), color, 0.3), mat("CT_Bolsa2_" + color2.lstrip("#"), color2, 0.35)
    papa, dentro = mat("CT_Papa", "#f6d36b", 0.7), mat("CT_Bolsa_Dentro", "#7a5a2a", 0.8)
    z0, z1 = 0.08, 0.92
    secs = []
    for k in range(11):
        u = k / 10
        z = z0 + (z1 - z0) * u
        d = 0.015 + 0.14 * (1 - abs(2 * u - 1) ** 3)
        if abierta and u > 0.5:                       # abierta: arriba se queda ancha (la boca de la bolsa)
            d = 0.155 - 0.06 * (2 * u - 1)
        secs.append((z, _superelipse(0.31, d)))
    p.loft(secs, c, tapa_arriba=not abierta)
    banda = [(z, [(x * 1.02, y * 1.08) for x, y in pts]) for z, pts in secs[3:6]]
    p.loft(banda, c2)
    dz = 0.015 + 0.14 * (1 - abs(2 * 0.68 - 1) ** 3)
    p.esfera((0, -dz - 0.012, 0.66), 0.1, papa, esc=(1.25, 0.12, 0.85), segs=12)
    dien = 12
    zz = [(-0.31 + 0.62 * i / dien, 0.0 if i % 2 == 0 else 0.035) for i in range(dien + 1)]
    contorno_ab = [(-0.31, z0 + 0.01), (0.31, z0 + 0.01)] + [(x, z) for x, z in reversed(zz)]
    p.placa_xz(contorno_ab, -0.012, 0.024, c)
    if abierta:
        p.esfera((0, 0, z1 - 0.03), 0.3, dentro, esc=(1, 0.31, 0.1), segs=14)
        for (x, a) in ((-0.12, 20), (0.02, -15), (0.15, 35)):
            p.esfera((x, 0, z1 + 0.06), 0.1, papa, esc=(1.1, 0.25, 0.8), segs=10)
    else:
        zt = [(-0.31 + 0.62 * i / dien, z1 + (0.035 if i % 2 else 0.0)) for i in range(dien + 1)]
        p.placa_xz([(0.31, z1 - 0.01), (-0.31, z1 - 0.01)] + zt, -0.012, 0.024, c)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def papa_frita(nombre, col, tam=1.0):
    """una papa frita (para la mano o la boca): ovalada y ondulada, amarilla. De pie, frente -Y. ~0,22 * tam."""
    p = P(nombre, col)
    p.esfera((0, 0, 0), 0.11, mat("CT_Papa", "#f6d36b", 0.7), esc=(1.15, 0.22, 0.85), segs=12)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008); o.scale = (tam,) * 3
    return o


def trofeo(nombre, col, tam=1.0):
    """copa de trofeo dorada: copa con dos asas, tallo, base de madera de dos pisos con estrella. Origen en la base;
    frente -Y. Alto ~0,75 * tam."""
    p = P(nombre, col)
    oro, base = mat("CT_Oro_Trofeo", "#f2c230", 0.22), mat("CT_Trofeo_Base", "#5b3a29", 0.6)
    p.cono((0, 0, 0), 0.22, 0.22, 0.1, base, segs=16)
    p.cono((0, 0, 0.1), 0.17, 0.17, 0.08, base, segs=16)
    p.cono((0, 0, 0.18), 0.08, 0.04, 0.05, oro, segs=12)
    p.cono((0, 0, 0.23), 0.035, 0.035, 0.14, oro, segs=10)
    p.cono((0, 0, 0.37), 0.05, 0.22, 0.3, oro, segs=18)
    p.cono((0, 0, 0.66), 0.228, 0.228, 0.035, oro, segs=18)
    _arco(p, (0.21, 0, 0.53), 0.085, oro, grosor=0.022, desde=-90, hasta=90)
    _arco(p, (-0.21, 0, 0.53), 0.085, oro, grosor=0.022, desde=90, hasta=270)
    estrella = [(0.07 * (1 if i % 2 == 0 else 0.42) * math.sin(math.pi * i / 5), 0.135 + 0.07 * (1 if i % 2 == 0 else 0.42) * math.cos(math.pi * i / 5)) for i in range(10)]
    p.placa_xz(estrella, -0.19, 0.02, oro)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def caja_monedas(nombre, col, tam=1.0, brillo=1.6, semilla=4):
    """caja de madera ABIERTA llena de monedas doradas que brillan (la caja del presidente), con bandas oscuras y
    cerradura; la tapa queda abierta hacia atras. Origen en la base; frente -Y. ~1,1 x 0,7 x 0,5 * tam."""
    import random
    rnd = random.Random(semilla)
    p = P(nombre, col)
    mad, mad2 = mat("CT_Madera_Caja", "#8a5a33", 0.7), mat("CT_Madera_Caja_Osc", "#5e3b20", 0.7)
    oro, metal = mat("CT_Moneda_Caja", "#ffcf3f", 0.3, emit=brillo), mat("CT_Metal", "#9aa3ad", 0.3)
    W, D, H, t = 1.1, 0.7, 0.5, 0.06
    p.caja((0, 0, t / 2), (W, D, t), mad)
    p.caja((0, -D / 2 + t / 2, H / 2), (W, t, H), mad)
    p.caja((0, D / 2 - t / 2, H / 2), (W, t, H), mad)
    p.caja((-W / 2 + t / 2, 0, H / 2), (t, D, H), mad)
    p.caja((W / 2 - t / 2, 0, H / 2), (t, D, H), mad)
    for z in (0.12, 0.38):
        p.caja((0, -D / 2 - 0.006, z), (W + 0.012, 0.02, 0.05), mad2)
    p.caja((0, -D / 2 - 0.016, H - 0.09), (0.11, 0.02, 0.13), metal)
    for i in range(80):
        x, y = rnd.uniform(-W / 2 + 0.11, W / 2 - 0.11), rnd.uniform(-D / 2 + 0.11, D / 2 - 0.11)
        z = H - 0.06 + 0.13 * (1 - (x / (W / 2)) ** 2) * (1 - (y / (D / 2)) ** 2) + rnd.uniform(-0.02, 0.03)
        p.cono((x, y, z), 0.07, 0.07, 0.022, oro, segs=12, rot=('X', rnd.uniform(-30, 30)))
    p.M = Matrix.Translation((0, D / 2, H)) @ Matrix.Rotation(math.radians(-105), 4, 'X')
    p.caja((0, -D / 2, t / 2), (W, D, t), mad)
    p.caja((0, -D + 0.04, t + 0.012), (W + 0.012, 0.06, 0.024), mad2)
    p.M = Matrix.Identity(4)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def marco_foto(nombre, col, imagen=None, tam=1.0, color="#f3e6c8"):
    """portarretratos de pie con una foto (png) y patita atras. Frente -Y. Origen en la base. ~0,62 x 0,78 * tam.
    Devuelve el marco; la foto es su hijo <nombre>_Foto."""
    p = P(nombre, col)
    c = mat("CT_Marco_" + color.lstrip("#"), color, 0.5)
    W, H, g = 0.62, 0.78, 0.07
    p.caja((0, 0, g / 2), (W, 0.05, g), c); p.caja((0, 0, H - g / 2), (W, 0.05, g), c)
    p.caja((-W / 2 + g / 2, 0, H / 2), (g, 0.05, H), c); p.caja((W / 2 - g / 2, 0, H / 2), (g, 0.05, H), c)
    p.caja((0, 0.02, H / 2), (W - g, 0.012, H - g), c)
    p.caja((0, 0.16, H * 0.33), (0.06, 0.03, H * 0.7), c, rot=('X', 25))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01); o.scale = (tam,) * 3
    if imagen:
        me = bpy.data.meshes.new(nombre + "_Foto")
        w, h = W - g * 1.6, H - g * 1.6
        me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(name="UVMap")
        for lp, cc in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[lp.index].uv = cc
        me.materials.append(_mat_imagen("CT_Foto_" + os.path.basename(imagen), imagen, 0.5, brillo=0.15))
        f = bpy.data.objects.new(nombre + "_Foto", me); col.objects.link(f)
        f.parent = o; f.location = (0, 0.008, H / 2)
    return o


def placa_fuente(nombre, col, lineas=("YO NO ELIJO.", "YO CUMPLO DESEOS."), lodo=True, tam=1.0):
    """PLACA DE PIEDRA de una fuente (letras grabadas oscuras en 2 lineas) con LODO opcional que tapa todo menos
    "YO NO" (EP006). De pie, frente -Y. Origen en el centro de la placa. ~2,6 x 1,1 * tam.
    Devuelve la placa; hijos <nombre>_Texto y, si lodo, <nombre>_Lodo (ocultarlo = la placa limpia)."""
    import random
    rnd = random.Random(8)
    p = P(nombre, col)
    piedra, piedra2 = mat("CT_Placa_Piedra", "#cfc8b8", 0.85), mat("CT_Placa_Piedra_Orilla", "#a59d8c", 0.85)
    W, H = 2.6, 1.1
    p.caja((0, 0.03, 0), (W + 0.14, 0.08, H + 0.14), piedra2)
    p.caja((0, 0, 0), (W, 0.08, H), piedra)
    for x, z in ((-W / 2 + 0.12, H / 2 - 0.12), (W / 2 - 0.12, H / 2 - 0.12), (-W / 2 + 0.12, -H / 2 + 0.12), (W / 2 - 0.12, -H / 2 + 0.12)):
        p.esfera((x, -0.045, z), 0.04, piedra2, segs=8)
    o = _acabado(p.fin(), bisel=0.02); contorno(o, 0.015); o.scale = (tam,) * 3
    cu = bpy.data.curves.new(nombre + "_Texto", 'FONT')
    cu.body = "\n".join(lineas); cu.size = 0.25; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.space_line = 1.1
    cu.extrude = 0.012
    fnt = r"C:\Windows\Fonts\ariblk.ttf"
    if os.path.exists(fnt):
        cu.font = bpy.data.fonts.load(fnt, check_existing=True)
    cu.materials.append(mat("CT_Letras_Grabadas", "#2a2622", 0.7))
    t = bpy.data.objects.new(nombre + "_Texto", cu); col.objects.link(t)
    t.parent = o; t.location = (0, -0.045, 0); t.rotation_euler = (math.radians(90), 0, 0)
    if lodo:
        q = P(nombre + "_Lodo", col)
        lod, lod2 = mat("CT_Lodo", "#4f3520", 0.35), mat("CT_Lodo_Claro", "#6e4c2c", 0.45)   # lodo mojado (brilla un poco)
        musgo = mat("CT_Musgo", "#5d7a35", 0.95)
        # UNA MANCHA PLANA en forma de L que tapa "ELIJO." (arriba a la derecha) y TODA la linea 2, con orilla
        # irregular y chorreadas hacia abajo (como lodo de verdad, no piedras)
        ruta = [(-1.25, 0.03), (-1.27, -0.36), (1.25, -0.37), (1.17, 0.35), (0.05, 0.36), (0.04, 0.03)]
        pts = []
        for (ax, az), (bx, bz) in zip(ruta, ruta[1:] + ruta[:1]):
            L = math.hypot(bx - ax, bz - az); n = max(2, int(L / 0.07))
            nx, nz = (bz - az) / L, -(bx - ax) / L                # normal hacia afuera (la ruta va en sentido horario)
            for k in range(n):
                u = k / n
                x, z = ax + (bx - ax) * u, az + (bz - az) * u
                j = rnd.uniform(-0.01, 0.045) if ax > 0.5 or az < 0.3 or bz < 0.3 else rnd.uniform(-0.02, 0.0)
                pts.append((x + nx * j, z + nz * j))
        q.placa_xz(pts, -0.085, 0.03, lod)
        for i in range(11):                                      # chorreadas que cuelgan de la orilla de abajo
            x, largo = rnd.uniform(-1.15, 1.15), rnd.uniform(0.09, 0.22)
            q.esfera((x, -0.085, -0.37 - largo / 2), 0.035, lod, esc=(1, 0.5, largo / 0.07), segs=10)
            q.esfera((x, -0.085, -0.37 - largo), 0.042, lod, esc=(1, 0.5, 1), segs=10)
        for i in range(6):                                       # vetas un poco mas claras (que no sea plano de un color)
            q.esfera((rnd.uniform(-1.0, 1.0) if i > 1 else rnd.uniform(0.3, 0.95), -0.088,
                      rnd.uniform(-0.3, -0.08) if i > 1 else rnd.uniform(0.12, 0.26)), rnd.uniform(0.06, 0.1), lod2,
                     esc=(2.4, 0.06, 0.45), segs=14)
        for i in range(14):                                      # salpicaduras alrededor
            a = rnd.uniform(0, 2 * math.pi)
            q.esfera((rnd.uniform(-1.3, 1.3), -0.08, rnd.uniform(-0.48, 0.45)), rnd.uniform(0.02, 0.045), lod, esc=(1, 0.3, 1), segs=8)
        for i in range(4):                                       # un poco de musgo en la orilla de arriba
            q.esfera((rnd.uniform(0.1, 1.1), -0.09, 0.33), rnd.uniform(0.05, 0.08), musgo, esc=(1.6, 0.3, 0.7), segs=10)
        lo = _acabado(q.fin(), angulo=85, bisel=0)
        lo.parent = o
    return o


def _pieza_hueso(rig, hueso):
    """malla principal pegada a un hueso del rig (la mas grande), ej. el torso."""
    cands = [c for c in rig.children_recursive if c.type == 'MESH' and c.parent_type == 'BONE' and c.parent_bone == hueso
             and not c.get("ct_accesorio")]                     # sin bandas u otros accesorios que ya le pusimos
    if not cands:
        return None
    def vol(c):
        d = c.dimensions
        return d.x * d.y * d.z
    return max(cands, key=vol)


def banda_presidencial(rig, col, colores=("#1f8a4c", "#f4f4f4", "#d12b2b"), nombre=None):
    """banda de PRESIDENTE MUNICIPAL: tres franjas que cruzan el pecho del hombro derecho a la cadera izquierda
    (adelante y atras, y por encima del hombro) con una roseta dorada en la cintura. Se pega al hueso UpperTorso con la
    MISMA relacion que la pieza del torso (asi va pegada al pecho en cualquier pose). Solo cubre el UpperTorso: si bajara
    a la cadera, al inclinarse se despegaria. Hacerla con el rig en reposo (sin pose). Devuelve el objeto."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Banda"
    up, lo = _pieza_hueso(rig, "UpperTorso"), _pieza_hueso(rig, "LowerTorso")
    bpy.context.view_layer.update()
    # medir en los ejes DEL RIG (no del mundo): si el rig esta girado en ese cuadro, la banda saldria chueca
    M = rig.matrix_world.copy(); Mi = M.inverted()
    pts = [Mi @ (p_.matrix_world @ Vector(c)) for p_ in (up, lo) if p_ for c in p_.bound_box]
    x0, x1 = min(v.x for v in pts), max(v.x for v in pts)
    y0, y1 = min(v.y for v in pts), max(v.y for v in pts)
    Wt0 = up.matrix_world.copy()
    zu = [Mi @ (up.matrix_world @ Vector(c)) for c in up.bound_box]
    z1 = max(v.z for v in zu)
    z0 = min(v.z for v in zu)                                  # solo el UpperTorso (no la cadera)
    ancho = x1 - x0
    bw = 0.075 * ancho                                         # ancho de cada franja
    p = P(nombre, col)
    p.M = M                                                    # se arma en los ejes del rig y se pasa al mundo
    ms = [mat("CT_Banda_" + c.lstrip("#"), c, 0.55) for c in colores]
    A = Vector((x0 + 0.2 * ancho, 0, z1 - 0.02))             # hombro derecho (el personaje mira a -Y: su derecha es -X)
    B = Vector((x1 - 0.02 * ancho, 0, z0 + 0.12 * (z1 - z0)))  # cintura izquierda
    d = B - A; L = d.length
    ang = -math.degrees(math.atan2(d.z, d.x))
    nrm = Vector((-d.z, 0, d.x)) / L
    for y in (y0 - 0.012, y1 + 0.012):
        for k, m in enumerate(ms):
            c = (A + B) / 2 + nrm * (k - 1) * bw
            p.caja((c.x, y, c.z), (L + 0.1, 0.02, bw), m, rot=('Y', ang))
    for k, m in enumerate(ms):                                 # por encima del hombro, de adelante hacia atras
        p.caja((A.x + (k - 1) * bw * 1.05, (y0 + y1) / 2, z1 + 0.01), (bw, (y1 - y0) + 0.05, 0.02), m)
        p.caja((x1 + 0.012, (y0 + y1) / 2, B.z + (k - 1) * bw * 1.05), (0.02, (y1 - y0) + 0.05, bw), m)
    oro = mat("CT_Oro_Roseta", "#e2b23a", 0.3)
    R = Vector((B.x - 0.08 * ancho, y0 - 0.03, B.z))
    p.cono((R.x, R.y + 0.02, R.z), 0.13 * ancho, 0.13 * ancho, 0.03, oro, segs=18, rot=('X', 90))
    p.cono((R.x, R.y - 0.005, R.z), 0.07 * ancho, 0.07 * ancho, 0.03, ms[0], segs=14, rot=('X', 90))
    for s, m in ((-1, ms[0]), (1, ms[2])):
        p.caja((R.x + s * 0.05 * ancho, R.y + 0.01, R.z - 0.2 * ancho), (0.06 * ancho, 0.015, 0.25 * ancho), m, rot=('Y', s * 15))
    o = _acabado(p.fin(), bisel=0)
    o["ct_accesorio"] = True
    W = o.matrix_world.copy()
    # misma relacion que la pieza del torso: no depende de la matriz del hueso (que puede no estar al dia en reposo)
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = "UpperTorso"
    o.matrix_parent_inverse = up.matrix_parent_inverse.copy()
    o.matrix_basis = up.matrix_basis @ Wt0.inverted() @ W
    return o


# ----------------------------------------------------------------- vestuario (EP007): que cada NPC parezca quien es
# Pedido del usuario (2026-11-09): "un panadero debe verse como panadero". Todo se mide en los ejes del rig EN REPOSO
# y se pega al hueso con la misma relacion que su pieza del cuerpo (como banda_presidencial): llamar ANTES de posar.
# Atajos por papel: vestir_panadero, vestir_tendero, vestir_vecina.
_TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "texturas")


def _pieza_cuerpo(rig, hueso):
    """la pieza DEL CUERPO de ese hueso (<Nombre>_<Hueso>), no el accesorio mas grande: el pelo largo de una chica
    (pegado a UpperTorso) o un peinado alto pueden ser mas grandes que el torso o la cabeza."""
    o = bpy.data.objects.get(rig.name.replace("_Rig", "") + "_" + hueso)
    if o is not None and o.parent_bone == hueso and len(o.data.vertices) >= 20:
        return o
    return _cabeza_y_pelo(rig)[0] if hueso == "Head" else _pieza_hueso(rig, hueso)


def _caja_hueso(rig, hueso):
    """pieza del cuerpo del hueso y su caja (min, max) en los ejes del rig."""
    bpy.context.view_layer.update()
    pz = _pieza_cuerpo(rig, hueso)
    Mi = rig.matrix_world.inverted()
    pts = [Mi @ (pz.matrix_world @ Vector(c)) for c in pz.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return pz, mn, mx


def _pegar_hueso(o, rig, hueso):
    """pega o (armado en coordenadas del mundo) al hueso, con la misma relacion que la pieza del cuerpo de ese hueso."""
    pz = _pieza_cuerpo(rig, hueso)
    bpy.context.view_layer.update()
    W, Wt0 = o.matrix_world.copy(), pz.matrix_world.copy()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = hueso
    o.matrix_parent_inverse = pz.matrix_parent_inverse.copy()
    o.matrix_basis = pz.matrix_basis @ Wt0.inverted() @ W
    o["ct_accesorio"] = True
    return o


def _frente_cabeza(mn, mx, x):
    """y de la cara a la altura x (la cabeza R15 clasica es casi un cilindro: el frente se curva hacia los lados)."""
    cx, cy, r = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mx.x - mn.x) / 2
    return cy - math.sqrt(max(r * r - (x - cx) ** 2, 0.0))


def _frente_torso(rig, cx, ancho, z0, z1):
    """lo mas adelantado (y minima, en ejes del rig) del torso Y de la ropa en capas (malla con Armature, ej. sudadera),
    en la franja central; asi el mandil queda encima de la ropa. El pelo y los monos no cuentan."""
    bpy.context.view_layer.update()
    Mi = rig.matrix_world.inverted()
    objs = [o for o in (_pieza_cuerpo(rig, "UpperTorso"), _pieza_cuerpo(rig, "LowerTorso")) if o]
    objs += [c for c in rig.children_recursive if c.type == 'MESH' and not c.get("ct_accesorio")
             and (c.parent_type == 'OBJECT' and any(m.type == 'ARMATURE' for m in c.modifiers))]
    ys = []
    for o in objs:
        M = Mi @ o.matrix_world
        for v in o.data.vertices:
            p = M @ v.co
            if abs(p.x - cx) < 0.3 * ancho and z0 < p.z < z1:
                ys.append(p.y)
    return min(ys) if ys else -0.6


def _mat_tela(nombre, color="#ffffff", png=None, tile=0.6, relieve=0.2, rough=0.9):
    """tela con grano fino (y estampado PNG opcional de Herramientas/blender/texturas). Usa las coordenadas del objeto:
    el estampado se ve derecho en el frente (plano XZ), sin UV."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs["Roughness"].default_value = rough
    h = color.lstrip("#")
    c = tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if png:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value = (math.radians(-90), 0, 0)    # u = x, v = z (el frente)
        mp.inputs["Scale"].default_value = (1 / tile,) * 3
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(png if os.path.isabs(png) else os.path.join(_TEX, png), check_existing=True)
        nt.links.new(mp.outputs["Vector"], im.inputs["Vector"]); nt.links.new(im.outputs["Color"], bs.inputs["Base Color"])
    else:
        bs.inputs["Base Color"].default_value = (*c, 1)
    m.diffuse_color = (*c, 1)
    if relieve:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 90.0; nz.inputs["Detail"].default_value = 3.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = relieve; bp.inputs["Distance"].default_value = 0.005
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _oscuro(color, f=0.72):
    h = color.lstrip("#")
    return "#" + "".join(f"{max(0, min(255, int(int(h[i:i + 2], 16) * f))):02x}" for i in (0, 2, 4))


def ocultar_pelo(rig):
    """esconde el pelo/sombrero de fabrica (accesorios pegados a la cabeza) para ponerle otro gorro."""
    for c in rig.children_recursive:
        if c.type == 'MESH' and c.parent_bone == "Head" and "_Acc_" in c.name and not c.get("ct_accesorio"):
            c.hide_render = True; c.hide_viewport = True


def gorro_chef(rig, col, nombre=None, color="#f7f7f2", quitar_pelo=True, alto=1.0):
    """GORRO DE CHEF (toque): banda alta con pliegues y copa inflada con bultos, pegado a la cabeza. Por defecto
    esconde el pelo de fabrica (si no, se sale por la banda)."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_GorroChef"
    _, mn, mx = _caja_hueso(rig, "Head")
    cx, cy, w, h = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.x - mn.x, mx.z - mn.z
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    bl = mat("CT_Chef_" + color.lstrip("#"), color, 0.85)
    rb, z0, hb = 0.54 * w, mx.z - 0.24 * h, 0.36 * h * alto
    p.cono((cx, cy, z0), rb, rb * 1.05, hb, bl, segs=28)
    for i in range(16):                                            # pliegues de la banda
        a = 2 * math.pi * i / 16
        p.cono((cx + rb * 1.02 * math.cos(a), cy + rb * 1.02 * math.sin(a), z0 + 0.03), 0.035, 0.042, hb - 0.03, bl, segs=6)
    zc = z0 + hb + 0.12 * h
    p.esfera((cx, cy, zc), 0.62 * w, bl, esc=(1, 1, 0.55), segs=22)            # copa inflada (mas ancha que la banda)
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        p.esfera((cx + 0.36 * w * math.cos(a), cy + 0.36 * w * math.sin(a), zc + 0.08 * h), 0.27 * w, bl, esc=(1, 1, 0.8), segs=12)
    p.esfera((cx, cy, zc + 0.2 * h), 0.32 * w, bl, esc=(1, 1, 0.7), segs=14)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015)
    _pegar_hueso(o, rig, "Head")
    if quitar_pelo:
        ocultar_pelo(rig)
    return o


def lentes(rig, col, nombre=None, color="#3b2a1a", alto=0.58, radio=0.14, sep=0.21):
    """LENTES redondos (armazon, puente y patitas hasta las orejas). alto = altura de los ojos en la cabeza (0 = barbilla)."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Lentes"
    _, mn, mx = _caja_hueso(rig, "Head")
    cx, cy, w, h = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mx.x - mn.x, mx.z - mn.z
    k = w / 1.2
    z, yf = mn.z + alto * h, cy - w / 2 - 0.03
    m = mat("CT_Lentes_" + color.lstrip("#"), color, 0.4)
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    for s in (-1, 1):
        p.anillo((cx + s * sep * k, yf, z), radio * k * 0.8, radio * k, 0.035, m, segs=24, eje='Y')
    p.caja((cx, yf, z + 0.02), (2 * (sep - radio) * k + 0.04, 0.035, 0.035), m)            # puente
    for s in (-1, 1):                                                                          # patitas
        xa, ya = cx + s * (sep + radio) * k, yf
        xs, ys = cx + s * (w / 2 + 0.02), cy - 0.25 * k
        for (x0, y0), (x1, y1) in (((xa, ya), (xs, ys)), ((xs, ys), (xs, cy + 0.1 * k))):
            L = math.hypot(x1 - x0, y1 - y0)
            p.caja(((x0 + x1) / 2, (y0 + y1) / 2, z + 0.03), (L + 0.03, 0.03, 0.035), m,
                   rot=('Z', math.degrees(math.atan2(y1 - y0, x1 - x0))))
    o = _acabado(p.fin(), bisel=0)
    return _pegar_hueso(o, rig, "Head")


def cachetes(rig, col, nombre=None, color="#f08a8a", alto=0.42):
    """cachetes rosados (discos planitos en la cara), para personajes bonachones."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Cachetes"
    _, mn, mx = _caja_hueso(rig, "Head")
    cx, w, h = (mn.x + mx.x) / 2, mx.x - mn.x, mx.z - mn.z
    m = mat("CT_Cachete_" + color.lstrip("#"), color, 0.9)
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    for s in (-1, 1):
        x = cx + s * 0.31 * w
        p.esfera((x, _frente_cabeza(mn, mx, x) + 0.005, mn.z + alto * h), 0.085 * w, m, esc=(1.2, 0.25, 0.8), segs=12)
    o = _acabado(p.fin(), bisel=0)
    return _pegar_hueso(o, rig, "Head")


def chaqueta_chef(rig, col, nombre=None, color="#f7f7f2", grosor=0.03, botones="#ddd6c6", relieve=0.04, solapa=True):
    """FILIPINA (chaqueta de chef) blanca: una funda un poco mas grande de cada pieza del torso y los brazos (las manos
    quedan igual), pegada a su hueso con la misma relacion que la pieza (se mueve igual en cualquier pose), dos filas
    de botones y la orilla de la solapa cruzada en el pecho. Tela casi lisa (con mucho relieve el pecho se veia
    "rarito", manchado, en acercamientos: EP007). Devuelve la lista de objetos."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Filipina"
    bl = _mat_tela("CT_Filipina_%s_r%02d" % (color.lstrip("#"), round(relieve * 100)), color, relieve=relieve)
    hechos = []
    for hueso in ("UpperTorso", "LowerTorso", "LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm"):
        pz = _pieza_cuerpo(rig, hueso)
        if not pz or len(pz.data.vertices) < 20:                   # piezas vacias (algunos brazos de ropa en capas)
            continue
        me = pz.data.copy(); me.name = f"{nombre}_{hueso}"
        mn = Vector((min(v.co.x for v in me.vertices), min(v.co.y for v in me.vertices), min(v.co.z for v in me.vertices)))
        mx = Vector((max(v.co.x for v in me.vertices), max(v.co.y for v in me.vertices), max(v.co.z for v in me.vertices)))
        c, d, sw = (mn + mx) / 2, mx - mn, pz.matrix_world.to_scale()
        s = [(d[i] + 2 * grosor / max(sw[i], 1e-4)) / max(d[i], 1e-4) for i in range(3)]
        for v in me.vertices:
            v.co = Vector((c.x + (v.co.x - c.x) * s[0], c.y + (v.co.y - c.y) * s[1], c.z + (v.co.z - c.z) * s[2]))
        me.materials.clear(); me.materials.append(bl)
        o = bpy.data.objects.new(me.name, me); col.objects.link(o)
        o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = hueso
        o.matrix_parent_inverse = pz.matrix_parent_inverse.copy(); o.matrix_basis = pz.matrix_basis.copy()
        o["ct_accesorio"] = True
        hechos.append(o)
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    cx, W = (um.x + uM.x) / 2, uM.x - um.x
    yf = _frente_torso(rig, cx, W, um.z, uM.z) - grosor - 0.012
    bm = mat("CT_Boton_" + botones.lstrip("#"), botones, 0.45)
    p = P(nombre + "_Botones", col); p.M = rig.matrix_world.copy()
    for f in (0.66, 0.46, 0.26):
        for sx in (-1, 1):
            p.esfera((cx + sx * 0.17 * W, yf, um.z + f * (uM.z - um.z)), 0.05, bm, esc=(1, 0.5, 1), segs=10)
    if solapa:                                                   # orilla de la solapa cruzada (de chef), apenas marcada
        so = mat("CT_SolapaFilipina", "#e6e3da", 0.8)
        p.caja((cx + 0.05 * W, yf + 0.006, (um.z + uM.z) / 2 - 0.04), (0.025, 0.012, (uM.z - um.z) * 0.78), so)
    hechos.append(_pegar_hueso(_acabado(p.fin(), bisel=0), rig, "UpperTorso"))
    return hechos


def panuelo_cuello(rig, col, nombre=None, color="#d12b2b", encima=0.04, baja=0.0, plano=False):
    """PANUELO al cuello: triangulo que cuelga en el pecho, nudo y tira por arriba (de panadero o vaquero).
    baja = cuanto mas abajo del borde del torso (la boca de las caras clasicas esta MUY abajo en la cabeza: si el
    panuelo queda en el borde, en tomas desde abajo tapa la sonrisa; pedido del usuario EP007). plano = nudo plano y
    triangulo pegado al pecho (sin bola que sobresale)."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Panuelo"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    cx, W = (um.x + uM.x) / 2, uM.x - um.x
    yf = _frente_torso(rig, cx, W, um.z, uM.z) - encima
    m = _mat_tela("CT_Panuelo_" + color.lstrip("#"), color, relieve=0.15)
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    zt = uM.z - baja
    if plano:
        p.placa_xz([(cx - 0.17 * W, zt - 0.06), (cx + 0.17 * W, zt - 0.06), (cx, zt - 0.4)], yf - 0.015, 0.02, m)
        p.caja((cx, yf - 0.01, zt - 0.04), (0.42 * W, 0.03, 0.07), m)
        p.caja((cx, yf - 0.03, zt - 0.075), (0.11, 0.03, 0.09), m)                      # nudo plano
    else:
        p.placa_xz([(cx - 0.21 * W, zt - 0.04), (cx + 0.21 * W, zt - 0.04), (cx, zt - 0.36)], yf - 0.03, 0.03, m)
        p.caja((cx, yf - 0.015, zt - 0.035), (0.44 * W, 0.04, 0.09), m)
        p.esfera((cx, yf - 0.05, zt - 0.08), 0.085, m, esc=(1.25, 0.75, 0.9), segs=12)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return _pegar_hueso(o, rig, "UpperTorso")


def _falda_curva(q, cx, cy, rx, ry, zt, largo, tela, abre=82, vuelo=0.07, redondo=0.3, filas=8, cols=40, pliegues=0.035,
                 tela_orilla=None, rx1=None, ry1=None):
    """falda de mandil que RODEA la cadera (arco de 2*abre grados por delante, elipse rx-ry alrededor del centro del
    torso), se abre un poco hacia abajo (vuelo), PLIEGUES suaves de tela que crecen hacia abajo y la orilla de abajo es
    REDONDA (mas corta a los lados). tela_orilla = color de la ultima franja (ribete). En q (P)."""
    vs = []
    for i in range(filas + 1):
        t = i / filas
        fila = []
        for j in range(cols + 1):
            u = -1 + 2 * j / cols
            a = math.radians(abre) * u                              # 0 = al frente (-Y)
            z = zt - t * largo * (1 - redondo * u * u)
            k = 1 + vuelo * t + pliegues * t * math.sin(7 * a)            # pliegues: ondas suaves, mas hacia abajo
            w = min(1.0, t / 0.4)                                          # de la cintura (rx, ry) a la cadera (rx1, ry1)
            rxt = rx + ((rx1 if rx1 else rx) - rx) * w
            ryt = ry + ((ry1 if ry1 else ry) - ry) * w
            fila.append(q.bm.verts.new(q.M @ Vector((cx + rxt * k * math.sin(a), cy - ryt * k * math.cos(a), z))))
        vs.append(fila)
    for i in range(filas):
        for j in range(cols):
            f = q.bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))   # normal hacia afuera
            f.material_index = q._i(tela_orilla if (tela_orilla and i == filas - 1) else tela); f.smooth = True
    return vs


def mandil_curvo(rig, col, nombre=None, color="#c98b4a", largo=0.95, encima=0.045, harina=True, abre=82):
    """MANDIL de cintura para abajo que se ADAPTA AL CUERPO (pedido del usuario EP007: el plano y cuadrado se veia raro):
    cinta que da la vuelta a la cintura con monito atras y falda curva que rodea la cadera, con vuelo y orilla redonda.
    Pegado a LowerTorso. Devuelve la falda."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Mandil"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    _, lm, lM = _caja_hueso(rig, "LowerTorso")
    cx, cy = (lm.x + lM.x) / 2, (lm.y + lM.y) / 2
    zt = um.z + 0.05
    # medir el CUERPO de verdad (los torsos de ropa se adelgazan en la cintura: con el ancho maximo quedaba como cubeta)
    Mi = rig.matrix_world.inverted()
    pts = []
    for h in ("UpperTorso", "LowerTorso", "LeftUpperLeg", "RightUpperLeg"):
        pz = _pieza_cuerpo(rig, h)
        if pz:
            M = Mi @ pz.matrix_world
            pts += [M @ v.co for v in pz.data.vertices]

    def radios(z0, z1):
        sel = [p_ for p_ in pts if z0 < p_.z < z1] or pts
        return max(abs(p_.x - cx) for p_ in sel) + encima, cy - min(p_.y for p_ in sel) + encima
    rx, ry = radios(zt - 0.15, zt + 0.1)                          # cintura (encima de la filipina)
    rx1, ry1 = radios(zt - largo * 0.55, zt - largo * 0.3)        # cadera y muslos
    tela = _mat_tela("CT_MandilCurvo_" + color.lstrip("#"), color, relieve=0.1)
    cinta = _mat_tela("CT_MandilCinta_" + _oscuro(color).lstrip("#"), _oscuro(color), relieve=0.1)
    q = P(nombre + "_Falda", col); q.M = rig.matrix_world.copy()
    vs = _falda_curva(q, cx, cy, rx, ry, zt - 0.03, largo, tela, abre=abre, tela_orilla=cinta, rx1=max(rx, rx1), ry1=max(ry, ry1))
    n = 36                                                        # cinta: anillo completo a la cintura
    ri = [q.bm.verts.new(q.M @ Vector((cx + (rx + 0.008) * math.sin(2 * math.pi * k / n), cy - (ry + 0.008) * math.cos(2 * math.pi * k / n),
                                        zt + dz))) for dz in (0.03, -0.03) for k in range(n)]   # cinta delgada (no aro)
    for k in range(n):
        j = (k + 1) % n
        f = q.bm.faces.new((ri[k], ri[n + k], ri[n + j], ri[j])); f.material_index = q._i(cinta); f.smooth = True
    yb = cy + ry + 0.04                                           # monito atras
    for s in (-1, 1):
        q.esfera((cx + s * 0.08, yb, zt), 0.07, cinta, esc=(1.3, 0.5, 0.8), segs=10)
        q.caja((cx + s * 0.05, yb - 0.01, zt - 0.13), (0.05, 0.02, 0.22), cinta, rot=('Y', s * 12))
    if harina:                                                    # manchitas de harina en el frente de la tela
        rnd = __import__("random").Random(7)
        blanco = mat("CT_Harina", "#fbf8f0", 0.95)
        for _ in range(7):
            u, t = rnd.uniform(-0.45, 0.45), rnd.uniform(0.2, 0.75)
            a, k = math.radians(abre) * u, 1 + 0.07 * t + 0.035 * t * math.sin(7 * math.radians(abre) * u)
            w = min(1.0, t / 0.4)
            rxt, ryt = rx + (max(rx, rx1) - rx) * w, ry + (max(ry, ry1) - ry) * w
            x, y = cx + (rxt * k + 0.012) * math.sin(a), cy - (ryt * k + 0.012) * math.cos(a)
            q.esfera((x, y, zt - 0.03 - t * largo), rnd.uniform(0.03, 0.07), blanco,
                     esc=(rnd.uniform(1.0, 1.7), 0.15, rnd.uniform(0.6, 1.0)), segs=8)
    o = q.fin()
    so = o.modifiers.new("Grosor", 'SOLIDIFY'); so.thickness = 0.018; so.offset = -1.0
    contorno(o, 0.01)
    return _pegar_hueso(o, rig, "LowerTorso")


def mandil(rig, col, nombre=None, color="#c98b4a", png=None, tile=0.6, peto=True, arriba=0.19, ancho=0.62,
           largo=0.9, bolsillo=True, lapiz=False, harina=False, encima=0.025, olanes=None):
    """MANDIL de tela: peto en el pecho (UpperTorso, con tirantes y cinta a la cintura con monito atras) y falda que
    baja a medio muslo (LowerTorso). peto=False -> solo de la cintura para abajo (panadero, mesero). png = estampado
    (texturas/tela_*.png). bolsillo y lapiz (asomando del bolsillo); harina = manchitas blancas; olanes = color del
    holan ondulado de la orilla de abajo y de arriba del peto (ej. "#ffffff"). Queda ENCIMA de la ropa en capas.
    Devuelve (peto o None, falda)."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Mandil"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    _, lm, lM = _caja_hueso(rig, "LowerTorso")
    cx, W = (um.x + uM.x) / 2, uM.x - um.x
    yf = _frente_torso(rig, cx, W, lm.z, uM.z) - encima
    tela = _mat_tela("CT_Mandil_" + (os.path.splitext(png)[0] if png else color.lstrip("#")), color, png, tile)
    cinta = _mat_tela("CT_MandilCinta_" + _oscuro(color).lstrip("#"), _oscuro(color), relieve=0.15)
    blanco = mat("CT_Harina", "#fbf8f0", 0.95)
    a = ancho * W
    zc = um.z + 0.05                                            # cintura (abajo del UpperTorso)
    rnd = __import__("random").Random(7)

    def manchas(q, x0, x1, z0, z1, n, y):
        for _ in range(n):
            q.esfera((rnd.uniform(x0, x1), y, rnd.uniform(z0, z1)), rnd.uniform(0.03, 0.075), blanco,
                     esc=(rnd.uniform(1.0, 1.8), 0.15, rnd.uniform(0.6, 1.1)), segs=8)

    p = P(nombre + "_Peto", col); p.M = rig.matrix_world.copy()
    if peto:
        zt = uM.z - arriba * (uM.z - um.z)
        p.placa_xz([(cx - a / 2, um.z), (cx + a / 2, um.z), (cx + a / 2 * 0.9, zt), (cx - a / 2 * 0.9, zt)], yf - 0.03, 0.03, tela)
        for s in (-1, 1):                                      # tirantes: de las esquinas del peto al cuello y por el hombro
            xa, za, xb, zb = cx + s * a / 2 * 0.82, zt - 0.02, cx + s * a * 0.3, uM.z + 0.01
            L = math.hypot(xb - xa, zb - za)
            p.caja(((xa + xb) / 2, yf - 0.025, (za + zb) / 2), (L + 0.04, 0.025, 0.06), cinta,
                   rot=('Y', -math.degrees(math.atan2(zb - za, xb - xa))))
            p.caja((xb, (yf + uM.y) / 2, uM.z + 0.012), (0.06, (uM.y - yf) + 0.04, 0.025), cinta)
        if harina:
            manchas(p, cx - a / 2 * 0.8, cx + a / 2 * 0.8, um.z + 0.1, zt - 0.1, 5, yf - 0.034)
        if olanes:
            ho = _mat_tela("CT_Holan_" + olanes.lstrip("#"), olanes, relieve=0.2)
            k = max(4, int(a * 0.9 / 0.085))
            for i in range(k):                                  # holan arriba del peto
                p.esfera((cx - a / 2 * 0.9 + (i + 0.5) * a * 0.9 / k, yf - 0.035, zt + 0.015), 0.05, ho, esc=(1, 0.35, 0.7), segs=8)
    else:
        p.caja((cx, yf - 0.035, zc), (W * 0.96, 0.03, 0.08), cinta)            # cinta de enfrente
    for s in (-1, 1):                                           # cinta por los lados y atras, con monito
        p.caja((cx + s * (W / 2 + 0.012), (yf + uM.y) / 2, zc), (0.025, uM.y - yf + 0.03, 0.075), cinta)
    p.caja((cx, uM.y + 0.012, zc), (W + 0.05, 0.025, 0.075), cinta)
    for s in (-1, 1):
        p.esfera((cx + s * 0.08, uM.y + 0.04, zc), 0.07, cinta, esc=(1.3, 0.5, 0.8), segs=10)
        p.caja((cx + s * 0.05, uM.y + 0.03, zc - 0.13), (0.05, 0.02, 0.22), cinta, rot=('Y', s * 12))
    po = _pegar_hueso(_acabado(p.fin(), bisel=0), rig, "UpperTorso")

    q = P(nombre + "_Falda", col); q.M = rig.matrix_world.copy()
    zt2 = zc + (0.0 if peto else -0.02)
    zb2 = zt2 - largo
    aw, bw = a * 1.05, a * 1.22
    q.placa_xz([(cx - bw / 2, zb2), (cx + bw / 2, zb2), (cx + aw / 2, zt2), (cx - aw / 2, zt2)], yf - 0.04, 0.03, tela)
    for i in range(1, 4):                                       # pliegues suaves de la tela
        x = cx - bw / 2 + i * bw / 4
        q.caja((x, yf - 0.045, (zt2 + zb2) / 2 - 0.05), (0.02, 0.012, largo * 0.75), tela)
    if bolsillo:
        bx, bz = cx + 0.16 * W, zt2 - 0.42 * largo
        q.caja((bx, yf - 0.08, bz), (0.3 * W, 0.02, 0.22 * largo), cinta)
        if lapiz:                                              # asoma del bolsillo, un poco chueco
            amar, gom = mat("CT_Lapiz", "#f2c230", 0.6), mat("CT_Goma", "#f08aa0", 0.8)
            lx, lz = bx - 0.06 * W, bz + 0.11 * largo - 0.08
            q.cono((lx, yf - 0.056, lz), 0.03, 0.03, 0.36, amar, segs=6, rot=('Y', -8))
            q.cono((lx - 0.05, yf - 0.056, lz + 0.355), 0.03, 0.03, 0.07, gom, segs=6, rot=('Y', -8))
    if harina:
        manchas(q, cx - bw / 2 * 0.8, cx + bw / 2 * 0.8, zb2 + 0.1, zt2 - 0.08, 7, yf - 0.044)
    if olanes:                                                  # holan ondulado en la orilla de abajo
        ho = _mat_tela("CT_Holan_" + olanes.lstrip("#"), olanes, relieve=0.2)
        k = max(5, int(bw / 0.09))
        for i in range(k):
            q.esfera((cx - bw / 2 + (i + 0.5) * bw / k, yf - 0.045, zb2 - 0.01), 0.065, ho, esc=(1, 0.4, 0.75), segs=10)
    fa = _pegar_hueso(_acabado(q.fin(), bisel=0), rig, "LowerTorso")
    return (po if peto else None), fa


def vestir_panadero(rig, col):
    """PANADERO: filipina blanca con botones, panuelo rojo, mandil cafe de la cintura para abajo con harina,
    gorro de chef, bigote de manubrio y cachetes rosados."""
    chaqueta_chef(rig, col)
    mandil_curvo(rig, col, color="#c98b4a", largo=0.95)                       # curvo, con pliegues y orilla redonda (EP007)
    panuelo_cuello(rig, col, encima=0.06, baja=0.14, plano=True)              # abajo de la boca, nudo plano (EP007)
    gorro_chef(rig, col)
    bigote(rig, col, color="#3a2414", alto=0.5, ancho=0.66, grosor=1.15)      # bigote() de una pieza (EP006)
    cachetes(rig, col)


def vestir_tendero(rig, col):
    """TENDERO amable: mandil verde con peto, bolsillo y lapiz, lentes redondos y bigote chico."""
    mandil(rig, col, color="#2f7d4a", peto=True, bolsillo=True, lapiz=True)
    lentes(rig, col, alto=0.64)                                 # los ojos de la cara clasica quedan a ~0,64
    bigote(rig, col, color="#8a6a2e", alto=0.5, ancho=0.44, grosor=0.8)


def _piel_de_manos(rig):
    """color de piel (sRGB 0-1) de las manos, leido de su textura por UV: mediana de los pixeles opacos mas claros
    (sin unas ni sombras). None si las manos no tienen textura."""
    import statistics
    for lado in ("LeftHand", "RightHand"):
        o = _pieza_cuerpo(rig, lado)
        if o is None or not o.data.uv_layers:
            continue
        im = next((n.image for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes
                   if n.type == 'TEX_IMAGE' and n.image), None)
        if im is None:
            continue
        W, H = im.size
        px = im.pixels[:]
        uv = o.data.uv_layers.active.data
        cs = []
        for lp in uv:
            u, v = lp.uv
            i = (int((v % 1) * (H - 1)) * W + int((u % 1) * (W - 1))) * 4
            if px[i + 3] > 0.5:
                cs.append(px[i:i + 3])
        if len(cs) > 20:
            cs.sort(key=sum)
            cs = cs[len(cs) // 3:]
            return tuple(statistics.median(c[k] for c in cs) for k in range(3))
    return None


def igualar_piel(rig, color=None):
    """CABEZA BRONCEADA Y PIERNAS CLARAS (EP007, la vecina): en las cabezas tipo calcomania (la cara es una imagen con
    transparencia), la piel de la cabeza sale del color de la pieza que trae el .mtl de Roblox (Kd), y las manos y las
    piernas traen su piel PINTADA en la textura de la ropa. Causa: armar_rig_r15_auto pasaba el Kd (que Roblox ya da en
    lineal) otra vez a lineal; ya se corrigio para rigs nuevos, pero los rigs viejos siguen asi. Esto pone el color de fondo de la
    cabeza igual a la piel de las manos (o a 'color', hex o sRGB 0-1). Ojos y boca no cambian. Solo en este archivo
    (no toca el .blend del personaje). Devuelve el color usado o None si la cabeza no es calcomania."""
    if isinstance(color, str):
        h = color.lstrip("#"); color = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    piel = color or _piel_de_manos(rig)
    cab = _pieza_cuerpo(rig, "Head")
    if piel is None or cab is None:
        return None
    hecho = None
    for m in cab.data.materials:
        if not (m and m.use_nodes):
            continue
        for n in m.node_tree.nodes:                            # Mix(A = color de la pieza, B = cara, factor = alfa)
            if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[6].is_linked and n.inputs[0].is_linked:
                n.inputs[6].default_value = (*[lin(c) for c in piel], 1)
                hecho = piel
    return hecho


def vestir_vecina(rig, col):
    """VECINA: delantal CORTO y ancho de tela estampada (corazones) con olanes blancos y bolsillo, y la piel de la
    cabeza igual a la del cuerpo (igualar_piel). Para que se lea como "la vecina que tiende la ropa", darle ademas
    canasta_ropa() y cargar_canasta()."""
    igualar_piel(rig)
    mandil(rig, col, color="#f6d6cf", png="tela_corazones_coral.png", peto=True, arriba=0.37, ancho=1.1, bolsillo=True,
           largo=0.55, olanes="#ffffff")                    # ancho: su torso es delgado y el pelo tapa los lados


def canasta_ropa(nombre, col, tam=1.0, pinzas=True):
    """CANASTA DE MIMBRE redonda (franjas de dos tonos, orilla gruesa y dos asas a los lados) llena de ropa doblada de
    colores, una manga que cuelga por enfrente y pinzas de colores en la orilla. Origen en la base; frente -Y.
    Ancho ~1,45 * tam (con las asas), alto ~0,95 * tam."""
    p = P(nombre, col)
    m1, m2 = _mat_tela("CT_Mimbre1", "#cf9a5c", relieve=0.5), _mat_tela("CT_Mimbre2", "#a8743f", relieve=0.5)
    r0, r1, H = 0.5, 0.62, 0.55
    n = 8
    for i in range(n):                                          # franjas tejidas
        za, zb = H * i / n, H * (i + 1) / n
        ra, rb = r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n
        p.cono((0, 0, za), ra, rb, zb - za, m1 if i % 2 == 0 else m2, segs=28)
    p.anillo((0, 0, H), r1 - 0.06, r1 + 0.05, 0.08, m2, segs=28, eje='Z')       # orilla
    for s in (-1, 1):                                           # asas a los lados
        _arco(p, (s * (r1 + 0.03), 0, H - 0.1), 0.11, m2, grosor=0.05, k=8,
              desde=-90 if s > 0 else 90, hasta=90 if s > 0 else 270)
    telas = [("#3d7fd9", (-0.15, 0.05, 0.02), 0.44, (1, 0.85, 0.32)), ("#f2c230", (0.2, -0.08, 0.1), 0.38, (1, 0.8, 0.33)),
             ("#fbfbf6", (-0.05, -0.12, 0.2), 0.32, (1.1, 0.8, 0.3)), ("#f08aa0", (0.12, 0.16, 0.19), 0.3, (1, 0.9, 0.35)),
             ("#5bbf6a", (-0.22, 0.12, 0.26), 0.22, (1, 0.9, 0.4))]
    for c, (x, y, dz), r, esc in telas:                        # la ropa asoma bien por arriba de la orilla
        p.esfera((x, y, H + dz + 0.07), r, _mat_tela("CT_Ropa_" + c.lstrip("#"), c, relieve=0.3), esc=esc, segs=16)
    manga = _mat_tela("CT_Ropa_7fc8ff", "#7fc8ff", relieve=0.3)       # manga azul clarito que cuelga por enfrente
    p.caja((0.24, -r1 + 0.1, H + 0.08), (0.17, 0.3, 0.07), manga)
    p.caja((0.24, -r1 - 0.04, H - 0.1), (0.17, 0.06, 0.36), manga)
    if pinzas:                                                  # pinzas chiquitas en la orilla (de lado, no tapan)
        for ang, c in ((-150, "#e23b3b"), (-25, "#3d7fd9"), (25, "#f2c230"), (155, "#5bbf6a")):
            a = math.radians(ang)
            pm = mat("CT_Pinza_" + c.lstrip("#"), c, 0.4)
            for dr in (-0.03, 0.03):                            # las dos tapitas de la pinza, abrazando la orilla
                rr = r1 + dr
                p.caja((rr * math.cos(a), rr * math.sin(a), H + 0.03), (0.026, 0.045, 0.13), pm, rot=('Z', ang + 90))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015)
    o.scale = (tam,) * 3
    return o


def cargar_canasta(rig, canasta, adelante=30, codo=48, adentro=9):
    """pone al personaje CARGANDO la canasta frente a la cintura con las manos en las asas (gira hombros y codos, sin
    llaves), ajusta el tamano de la canasta a la distancia entre las manos y la pega al UpperTorso. Si el rig tiene los
    brazos al reves (X+ = atras, rigs sobre el Blocky Rig), lo nota midiendo la mano y voltea el signo.
    Para animar: poner llaves despues de llamarla."""
    pb = rig.pose.bones
    bpy.context.view_layer.update()
    mano0 = (rig.matrix_world @ pb["RightHand"].head).y

    def posar(sg):
        for lado, sz in (("Right", 1), ("Left", -1)):
            ua, la = pb[lado + "UpperArm"], pb[lado + "LowerArm"]
            ua.rotation_mode = la.rotation_mode = 'XYZ'
            ua.rotation_euler = (math.radians(sg * adelante), 0, math.radians(sz * adentro))
            la.rotation_euler = (math.radians(sg * codo), 0, 0)
        bpy.context.view_layer.update()

    posar(1)
    if (rig.matrix_world @ pb["RightHand"].head).y > mano0:     # la mano se fue para atras: ejes al reves
        posar(-1)
    mr, ml = rig.matrix_world @ pb["RightHand"].head, rig.matrix_world @ pb["LeftHand"].head
    medio = (mr + ml) / 2
    s = max(0.7, min(1.25, abs(mr.x - ml.x) / 2 / 0.65))      # asas (radio 0,65) en las manos
    canasta.scale = (s,) * 3
    canasta.location = (medio.x, medio.y - 0.1 * s, medio.z - 0.2 - 0.45 * s)   # agarre ~0,2 abajo de la muneca
    canasta.rotation_euler = rig.matrix_world.to_euler()
    bpy.context.view_layer.update()
    return _pegar_hueso(canasta, rig, "UpperTorso")


# ----------------------------------------------------------------- objetos de EP007 ("Todos tienen poder menos yo")
def _mat_vidrio(nombre="CT_Vidrio_Claro", color="#dff3f7", alfa=0.32):
    """vidrio de caricatura: claro, casi transparente y brillante. Transparencia BLENDED (lisa): con DITHERED se veia
    granuloso a 16 muestras (prueba EP007)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = mat(nombre, color, 0.05)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    # orillas mas visibles que el centro (como el vidrio de verdad): alfa segun el angulo (Layer Weight > Facing)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = alfa * 0.4; mr.inputs["To Max"].default_value = min(1.0, alfa * 2.8)
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], bs.inputs["Alpha"])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True                  # con BLENDED, sin la cara de atras se ordena mejor
    return m


def _mat_halo(color, fuerza=2.5, alfa=0.3):
    """luz que llena el frasco: transparente y brillante (sin bloom en Eevee, el halo hace de resplandor)."""
    nombre = "CT_Halo_" + color.lstrip("#")
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = mat(nombre, color, 0.5, emit=fuerza)
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs["Alpha"].default_value = alfa
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True
    return m


def _tubo_var(p, pts, radios, m, segs=10, aplanar=1.0):
    """tubo liso que sigue los puntos 'pts' con un radio por punto (puntas cerradas). aplanar < 1 lo aplasta en Y local."""
    bm = p.bm
    k = p._i(m)
    V = [Vector(q) for q in pts]
    anillos = []
    for i, c in enumerate(V):
        tg = (V[min(i + 1, len(V) - 1)] - V[max(i - 1, 0)]).normalized()
        ref = Vector((0, 1, 0)) if abs(tg.y) < 0.9 else Vector((1, 0, 0))
        a1 = tg.cross(ref).normalized(); a2 = tg.cross(a1).normalized()
        anillos.append([bm.verts.new(p.M @ (c + a1 * math.cos(2 * math.pi * j / segs) * radios[i]
                                            + a2 * math.sin(2 * math.pi * j / segs) * radios[i] * aplanar)) for j in range(segs)])
    for A, B in zip(anillos, anillos[1:]):
        for j in range(segs):
            bm.faces.new((A[j], A[(j + 1) % segs], B[(j + 1) % segs], B[j])).material_index = k
    for i, sg in ((0, -1), (len(V) - 1, 1)):
        tg = (V[i] - V[i - sg]).normalized() if len(V) > 1 else Vector((0, 0, 1))
        pt = bm.verts.new(p.M @ (V[i] + tg * radios[i] * 0.8))
        A = anillos[i]
        for j in range(segs):
            bm.faces.new((A[j], A[(j + 1) % segs], pt) if sg > 0 else (A[(j + 1) % segs], A[j], pt)).material_index = k
    return p


def _texto3d(nombre, col, texto, tam, color="#2b2b2b", extruir=0.0, borde=None, fuente="arialbd.ttf"):
    """letras 3D centradas (curva de texto) en el plano XZ mirando a -Y. borde = color del contorno (copia detras)."""
    def una(nom, off, c):
        cu = bpy.data.curves.new(nom, 'FONT')
        cu.body = texto; cu.size = tam; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.extrude = extruir; cu.offset = off
        f = os.path.join(r"C:\Windows\Fonts", fuente)
        if os.path.exists(f):
            cu.font = bpy.data.fonts.load(f, check_existing=True)
        cu.materials.append(mat("CT_Tinta_" + c.lstrip("#"), c, 0.6))
        o = bpy.data.objects.new(nom, cu); col.objects.link(o)
        o.rotation_euler = (math.radians(90), 0, 0)
        return o
    t = una(nombre, 0.0, color)
    if borde:
        b = una(nombre + "_Borde", tam * 0.07, borde)
        b.parent = t; b.matrix_parent_inverse = t.matrix_world.inverted() @ t.matrix_world
        b.rotation_euler = (0, 0, 0); b.location = (0, 0, -max(extruir, 0.01) - 0.01)   # detras (en ejes del texto)
    return t


def frasco(nombre, col, contenido=None, brillo=6.0, etiqueta=None, color_etiqueta="#f3e6c4", tapa="#b07a4a",
           polvo=False, alto=0.55, tam=1.0, tela=None):
    """FRASCO de conserva (cuerpo redondo con hombros, rosca y tapa): vacio (contenido=None) o con un PODER adentro
    (contenido = color): nube de luz con nucleo claro, halo que llena el frasco y chispitas. El vidrio se ve mas en las
    orillas. tela = color de una tela amarrada con cordon sobre la tapa (por defecto en los que tienen poder).
    etiqueta = texto en una etiqueta de papel con orilla (None = sin etiqueta, "" = en blanco). polvo=True: frasco viejo
    (vidrio opaco, polvo y telarana). Origen en la base; frente -Y. Alto ~0,66 * tam. El contenido es un hijo
    (<nombre>_Poder) sin contorno, para que no se vea una raya negra dentro del vidrio."""
    p = P(nombre, col)
    vid = _mat_vidrio("CT_Vidrio_Viejo", "#b9b2a0", 0.7) if polvo else _mat_vidrio()
    tp = mat("CT_Tapa_" + tapa.lstrip("#"), tapa, 0.45)
    brillo_v = mat("CT_Brillo_Vidrio", "#ffffff", 0.2, emit=2.0)
    r, H, n = 0.16, alto, 20

    def circ(rr):
        return [(rr * math.cos(2 * math.pi * i / n), rr * math.sin(2 * math.pi * i / n)) for i in range(n)]
    perfil = [(0.0, r * 0.86), (0.025, r * 0.97), (0.07, r), (H * 0.64, r), (H * 0.72, r * 0.94), (H * 0.78, r * 0.82),
              (H * 0.8, r * 0.77), (H * 0.88, r * 0.77)]
    p.loft([(z, circ(rr)) for z, rr in perfil], vid, tapa_abajo=True, tapa_arriba=False)
    for z in (H * 0.825, H * 0.855):                                              # rosca
        p.anillo((0, 0, z), r * 0.75, r * 0.81, 0.014, vid, segs=n, eje='Z')
    p.cono((0, 0, H * 0.87), r * 0.84, r * 0.84, 0.075, tp, segs=n)              # tapa
    p.cono((0, 0, H * 0.87 + 0.075), r * 0.84, r * 0.72, 0.02, tp, segs=n)
    det = P(nombre + "_Detalles", col)                                            # sin contorno (reflejos, telarana)
    for a, alto_b, z, gr in ((-122, H * 0.4, H * 0.38, 0.016), (-108, H * 0.13, H * 0.6, 0.012)):   # reflejos curvos
        for k in range(3):
            aa = math.radians(a + k * 4)
            det.caja((r * 1.006 * math.cos(aa), r * 1.006 * math.sin(aa), z), (gr, 0.004, alto_b * (1 - 0.12 * abs(k - 1))),
                     brillo_v, rot=('Z', a + k * 4 + 90))
    if tela is None and contenido and not polvo:
        tela = "#d9c39b"
    if tela:
        tm = _mat_tela("CT_TelaFrasco_" + tela.lstrip("#"), tela, relieve=0.4)
        cord = mat("CT_Cordon", "#b8322a", 0.7)
        p.esfera((0, 0, H * 0.94), r * 0.98, tm, esc=(1, 1, 0.32), segs=n)
        p.cono((0, 0, H * 0.8), r * 1.0, r * 0.88, H * 0.15, tm, segs=n)
        p.anillo((0, 0, H * 0.84), r * 0.87, r * 0.95, 0.03, cord, segs=n, eje='Z')
        for s in (-1, 1):                                                         # monito al frente
            p.esfera((s * 0.026, -r * 0.95, H * 0.84), 0.021, cord, esc=(1.4, 0.6, 0.9), segs=8)
            p.caja((s * 0.016, -r * 0.94, H * 0.8), (0.013, 0.01, 0.06), cord, rot=('Y', s * 18))
    if etiqueta is not None:
        pap = mat("CT_Etiqueta_" + color_etiqueta.lstrip("#"), color_etiqueta, 0.85, emit=0.3)   # se lee de noche
        ori = mat("CT_EtiquetaOrilla", "#8a6a40", 0.8)
        p.caja((0, -r - 0.004, H * 0.4), (r * 1.42, 0.012, H * 0.25), ori)
        p.caja((0, -r - 0.010, H * 0.4), (r * 1.3, 0.012, H * 0.21), pap)
    if polvo:
        gris = mat("CT_Polvo", "#d8d2c4", 0.95)
        rnd = __import__("random").Random(3)
        for _ in range(11):
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0, r * 0.7)
            p.esfera((rr * math.cos(a), rr * math.sin(a), H * 0.87 + 0.1), rnd.uniform(0.025, 0.05), gris, esc=(1.4, 1.4, 0.4), segs=8)
        telar = mat("CT_Telarana", "#f4f2ec", 0.9)
        for k, (x, z, ang, L) in enumerate(((0.12, 0.62, 35, 0.32), (0.15, 0.5, -25, 0.28), (0.1, 0.42, 70, 0.22))):
            det.caja((x, -0.06, H * z + 0.1), (0.005, 0.005, L), telar, rot=('Y', ang))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    do = det.fin(); do.parent = o; do.visible_shadow = False
    if contenido:
        q = P(nombre + "_Poder", col)
        luz = mat("CT_Poder_" + contenido.lstrip("#"), contenido, 0.3, emit=brillo)
        h = contenido.lstrip("#")
        claro = "#" + "".join(f"{int(int(h[i:i + 2], 16) * 0.45 + 255 * 0.55):02x}" for i in (0, 2, 4))
        nuc = mat("CT_PoderNucleo_" + claro.lstrip("#"), claro, 0.3, emit=brillo * 1.3)
        for (x, y, z, rr, ez) in ((0, 0, 0.36, 0.5, 1.25), (0.26, -0.08, 0.47, 0.34, 1.0), (-0.25, 0.08, 0.3, 0.36, 1.0),
                                  (0.02, 0.16, 0.22, 0.3, 1.0), (-0.1, -0.14, 0.52, 0.26, 1.0)):
            q.esfera((x * r, y * r, z * H), rr * r, luz, esc=(1, 1, ez), segs=12)
        q.esfera((0, -0.08 * r, 0.38 * H), 0.24 * r, nuc, segs=10)
        q.esfera((0, 0, 0.4 * H), 0.9 * r, _mat_halo(contenido, fuerza=brillo * 0.45), esc=(1, 1, 1.45), segs=16)
        chis = mat("CT_Chispa", "#ffffff", 0.2, emit=8.0)
        rnd = __import__("random").Random(len(nombre))
        for _ in range(6):
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0.2, 0.7) * r
            q.ico((rr * math.cos(a), rr * math.sin(a), rnd.uniform(0.15, 0.7) * H), rnd.uniform(0.012, 0.02), chis, sub=1)
        po = q.fin()
        for pl in po.data.polygons:
            pl.use_smooth = True
        po.parent = o; po.visible_shadow = False
    if etiqueta:
        t = _texto3d(nombre + "_Texto", col, etiqueta, 0.05, "#3a2a20")
        t.parent = o; t.location = (0, -r - 0.018, H * 0.4)
    o.scale = (tam,) * 3
    return o


def frasco_especial(nombre, col, color="#ffd84a", etiqueta="SIKELPA", polvo=True, rayos=True, tam=1.0):
    """EL FRASCO DEL PROTAGONISTA, distinto a todos: frasco ANTIGUO de boticario (panzon, cuello delgado, tapon de
    vidrio redondo, cinta y aros DORADOS, sello de cera roja), poder mas brillante (nucleo blanco, halo grande,
    chispas y una estrellita), RAYOS de luz que se escapan por el polvo y una ETIQUETA COLGANTE con cordon y el nombre.
    Origen en la base; frente -Y. Alto ~1,0 * tam."""
    p = P(nombre, col)
    vid = _mat_vidrio("CT_Vidrio_Antiguo", "#e8dcc0", 0.42 if polvo else 0.3)
    oro, oro2 = mat("CT_Oro_Frasco", "#e8b53a", 0.25), mat("CT_Oro_Frasco2", "#b8861f", 0.3)
    cera = mat("CT_Cera", "#b3261e", 0.5)
    n = 24

    def circ(rr):
        return [(rr * math.cos(2 * math.pi * i / n), rr * math.sin(2 * math.pi * i / n)) for i in range(n)]
    perfil = [(0.0, 0.17), (0.03, 0.21), (0.1, 0.25), (0.28, 0.27), (0.45, 0.25), (0.57, 0.19), (0.65, 0.11), (0.68, 0.09),
              (0.8, 0.09), (0.83, 0.115), (0.86, 0.115)]
    p.loft([(z, circ(rr)) for z, rr in perfil], vid, tapa_abajo=True, tapa_arriba=False)
    p.anillo((0, 0, 0.015), 0.17, 0.215, 0.04, oro2, segs=n, eje='Z')                  # aro dorado de la base
    p.anillo((0, 0, 0.74), 0.088, 0.12, 0.07, oro, segs=n, eje='Z')                   # cinta dorada del cuello
    p.esfera((0, 0, 0.95), 0.12, vid, segs=16)                                         # tapon de vidrio
    p.cono((0, 0, 0.84), 0.07, 0.085, 0.06, vid, segs=16)
    p.esfera((0, -0.115, 0.74), 0.05, cera, esc=(1.1, 0.5, 1.1), segs=12)              # sello de cera
    det = P(nombre + "_Detalles", col)
    bv = mat("CT_Brillo_Vidrio", "#ffffff", 0.2, emit=2.0)
    for a, alto_b, z, gr in ((-125, 0.3, 0.3, 0.02), (-110, 0.1, 0.5, 0.014)):
        for k in range(3):
            aa = math.radians(a + k * 4); rr = 0.272 if z < 0.45 else 0.24
            det.caja((rr * math.cos(aa), rr * math.sin(aa), z), (gr, 0.004, alto_b * (1 - 0.12 * abs(k - 1))), bv, rot=('Z', a + k * 4 + 90))
    if polvo:
        gris = mat("CT_Polvo", "#d8d2c4", 0.95)
        rnd = __import__("random").Random(5)
        for _ in range(16):                                                           # polvo en los hombros
            a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0.12, 0.24)
            p.esfera((rr * math.cos(a), rr * math.sin(a), 0.56 + (0.24 - rr) * 0.6), rnd.uniform(0.03, 0.06), gris, esc=(1.5, 1.5, 0.35), segs=8)
        telar = mat("CT_Telarana", "#f4f2ec", 0.9)
        for x, z, ang, L in ((0.2, 0.75, 40, 0.5), (0.24, 0.6, -20, 0.42), (0.15, 0.9, 75, 0.3), (-0.22, 0.7, -50, 0.36)):
            det.caja((x, 0.04, z), (0.005, 0.005, L), telar, rot=('Y', ang))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01)
    do = det.fin(); do.parent = o; do.visible_shadow = False
    # el poder: mas brillante que los demas
    q = P(nombre + "_Poder", col)
    luz = mat("CT_PoderEspecial_" + color.lstrip("#"), color, 0.3, emit=9.0)
    blanco = mat("CT_PoderNucleoEspecial", "#fffbe6", 0.3, emit=12.0)
    for (x, y, z, rr) in ((0, 0, 0.3, 0.16), (0.08, -0.04, 0.38, 0.1), (-0.08, 0.03, 0.24, 0.11), (0.02, 0.07, 0.18, 0.09)):
        q.esfera((x, y, z), rr, luz, segs=14)
    q.esfera((0, -0.03, 0.3), 0.075, blanco, segs=12)
    q.esfera((0, 0, 0.3), 0.235, _mat_halo(color, 4.0, 0.35), segs=18)
    chis = mat("CT_Chispa", "#ffffff", 0.2, emit=8.0)
    rnd = __import__("random").Random(9)
    for _ in range(10):
        a = rnd.uniform(0, 2 * math.pi); rr = rnd.uniform(0.05, 0.2)
        q.ico((rr * math.cos(a), rr * math.sin(a), rnd.uniform(0.1, 0.5)), rnd.uniform(0.012, 0.022), chis, sub=1)
    for k in range(4):                                                                 # estrellita de 4 puntas
        q.caja((0.05, -0.12, 0.42), (0.11 if k % 2 == 0 else 0.018, 0.006, 0.018 if k % 2 == 0 else 0.11), chis)
    po = q.fin(); po.parent = o; po.visible_shadow = False
    if rayos:                                                                          # rayos que se escapan
        rr_ = P(nombre + "_Rayos", col)
        nombre_m = "CT_RayoFrasco_" + color.lstrip("#")
        rm = bpy.data.materials.get(nombre_m)
        if rm is None:                                                             # rayo suave y transparente
            rm = mat(nombre_m, color, 0.5, emit=1.6)
            bs = next(nn for nn in rm.node_tree.nodes if nn.type == 'BSDF_PRINCIPLED')
            bs.inputs["Alpha"].default_value = 0.1
            try:
                rm.surface_render_method = 'BLENDED'
            except Exception:
                rm.blend_method = 'BLEND'
        for k, (az, el, L) in enumerate(((-100, 15, 0.8), (-60, 35, 0.65), (-140, 40, 0.6), (-20, 5, 0.5), (-170, 10, 0.55), (150, 25, 0.45))):
            a, e = math.radians(az), math.radians(el)
            d = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
            rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            res = bmesh.ops.create_cone(rr_.bm, cap_ends=True, segments=10, radius1=0.015, radius2=0.065, depth=L,
                                        matrix=Matrix.Translation((0, 0, 0.3)) @ rot @ Matrix.Translation((0, 0, L / 2 + 0.22)))
            rr_._marcar(res, rm)
        ro = rr_.fin(); ro.parent = o; ro.visible_shadow = False
    # etiqueta colgante con cordon y el nombre
    tg = P(nombre + "_Etiqueta", col)
    pap = mat("CT_EtiquetaColgante", "#f6e7c1", 0.85, emit=0.35)
    cord = mat("CT_Cordon", "#b8322a", 0.7)
    _tubo_var(tg, [(0.1, -0.06, 0.74), (0.2, -0.17, 0.66), (0.24, -0.27, 0.56)], [0.008] * 3, cord, segs=6)
    tg.caja((0.25, -0.29, 0.43), (0.36, 0.012, 0.24), pap, rot=('Y', -8))
    tg.caja((0.25, -0.283, 0.43), (0.39, 0.008, 0.27), mat("CT_EtiquetaOrilla", "#8a6a40", 0.8), rot=('Y', -8))
    to = _acabado(tg.fin(), bisel=0); to.parent = o; contorno(to, 0.006)
    t = _texto3d(nombre + "_Texto", col, etiqueta, 0.075, "#3a2a20", fuente="ariblk.ttf")
    t.parent = o; t.location = (0.25, -0.302, 0.43); t.rotation_euler = (math.radians(90), math.radians(-8), 0)
    o.scale = (tam,) * 3
    return o


def contenedor_basura(nombre, col, color="#3f9a4a", tapa="#1d1e21", abiertas=(0.0, 0.0), basura=True, olor=None,
                      texto="BASURA", tam=1.0):
    """CONTENEDOR DE BASURA como el de la referencia del usuario (2026-11-10): cuerpo verde MAS ANCHO ARRIBA (frente y
    lados inclinados, atras recto), hueco por dentro, refuerzos verticales en el frente, fundas trapecio a los lados
    (para el camion), orilla gruesa arriba, rueditas con horquilla y DOS TAPAS NEGRAS con nervaduras, cada una la mitad
    de arriba, con bisagra atras. La BASURA VA ADENTRO (bolsas, caja, cascara) por debajo de la orilla.
    abiertas = grados de cada tapa (0 = cerrada; 120 = bien abierta hacia atras, para que alguien caiga adentro).
    olor (None = solo si hay una tapa abierta): rayitas verdes. Frente a -Y; origen al centro, en el piso.
    Medidas: 5,2 de largo (X) arriba, 3,1 de fondo arriba, 3,4 de alto * tam. Devuelve el cuerpo; las tapas son hijas
    (<nombre>_Tapa_0 izquierda, _Tapa_1 derecha; giran en su X local: negativo = abrir)."""
    Z0, Z1, g = 0.55, 3.25, 0.09                     # fondo (arriba de las ruedas), orilla, grueso de lamina
    xb, xt = 2.35, 2.6                               # medio largo abajo / arriba
    yb_atras, yb_frente, yt_frente = 1.3, -1.25, -1.8  # atras recto; el frente se inclina hacia afuera
    p = P(nombre, col)
    lam = _mat_tela("CT_Lamina_" + color.lstrip("#"), color, relieve=0.35, rough=0.5)
    lam2 = mat("CT_Lamina2_" + _oscuro(color, 0.82).lstrip("#"), _oscuro(color, 0.82), 0.45)
    neg, gris = mat("CT_NegroMate", "#1c1c1e", 0.7), mat("CT_RinGris", "#9a9ca3", 0.35)
    mugre = mat("CT_Mugre", "#3a3226", 0.95)

    def rect(x, y0, y1, ch=0.12):
        """rectangulo con esquinas achaflanadas (8 puntos), en el orden de un anillo."""
        return [(-x + ch, y0), (x - ch, y0), (x, y0 + ch), (x, y1 - ch), (x - ch, y1), (-x + ch, y1), (-x, y1 - ch), (-x, y0 + ch)]
    # casco hueco y cerrado: fuera abajo -> fuera arriba -> dentro arriba -> dentro abajo (normales correctas)
    p.loft([(Z0, rect(xb, yb_frente, yb_atras)), (Z1, rect(xt, yt_frente, yb_atras)),
            (Z1, rect(xt - g, yt_frente + g, yb_atras - g)), (Z0 + g, rect(xb - g, yb_frente + g, yb_atras - g))],
           lam, tapa_abajo=True, tapa_arriba=True)
    af = math.degrees(math.atan2(yb_frente - yt_frente, Z1 - Z0))            # inclinacion del frente
    al = math.degrees(math.atan2(xt - xb, Z1 - Z0))                          # inclinacion de los lados
    Lf = math.hypot(Z1 - Z0, yb_frente - yt_frente)

    def frente_y(z):
        return yb_frente + (yt_frente - yb_frente) * (z - Z0) / (Z1 - Z0)
    for i in range(7):                                                        # refuerzos verticales del frente
        x = -1.95 + i * 0.65
        zc = (Z0 + 0.15 + Z1 - 0.45) / 2
        p.caja((x, frente_y(zc) - 0.06, zc), (0.36, 0.12, Lf - 0.6), lam2, rot=('X', af))
    for s in (-1, 1):                                                         # orilla gruesa de arriba
        p.caja((s * (xt + 0.05), (yt_frente + yb_atras) / 2, Z1 - 0.06), (0.16, yb_atras - yt_frente + 0.2, 0.2), lam2)
    p.caja((0, yb_atras + 0.05, Z1 - 0.06), (2 * xt + 0.2, 0.16, 0.2), lam2)
    p.caja((0, yt_frente - 0.05, Z1 - 0.06), (2 * xt + 0.2, 0.16, 0.2), lam2)
    for s in (-1, 1):                                                         # lados: refuerzo y funda trapecio
        xl = lambda z: xb + (xt - xb) * (z - Z0) / (Z1 - Z0)
        for y in (-0.95, 0.95):
            p.caja((s * (xl(1.9) + 0.04), y, 1.9), (0.1, 0.22, Z1 - Z0 - 0.4), lam2, rot=('Y', -s * al))
        zf = 2.0
        q = [(-1.0, zf - 0.45), (1.0, zf - 0.45), (1.15, zf + 0.45), (-1.15, zf + 0.45)]
        Mi = p.M
        p.M = Matrix.Rotation(math.radians(90), 4, 'Z')                       # funda: perfil en YZ, sale hacia afuera
        x_ext = xl(zf) + 0.42
        p.placa_xz(q, -x_ext if s > 0 else x_ext - 0.42, 0.42, lam)
        p.M = Mi
        for yy in (-1.08, 1.08):                                              # bocas de la funda (negras)
            p.caja((s * (xl(zf) + 0.22), yy, zf), (0.3, 0.02, 0.62), neg)
    for x in (-xb + 0.35, xb - 0.35):                                         # rueditas con horquilla
        for y in (yb_frente + 0.35, yb_atras - 0.35):
            p.caja((x, y, Z0 - 0.05), (0.42, 0.42, 0.06), gris)
            for dx in (-0.12, 0.12):
                p.caja((x + dx, y, Z0 - 0.22), (0.04, 0.22, 0.3), gris)
            p.cono((x - 0.08, y, 0.22), 0.21, 0.21, 0.16, neg, segs=16, rot=('Y', 90))
            p.cono((x - 0.1, y, 0.22), 0.09, 0.09, 0.2, gris, segs=12, rot=('Y', 90))
    rnd = __import__("random").Random(11)
    for k in range(8):                                                        # chorreadas suaves bajo la orilla
        x = rnd.uniform(-2.2, 2.2); L = rnd.uniform(0.25, 0.6)
        if abs(((x + 1.95) / 0.65) - round((x + 1.95) / 0.65)) < 0.35:
            continue                                                          # no sobre los refuerzos
        zc = Z1 - 0.2 - L / 2
        p.caja((x, frente_y(zc) - 0.012, zc), (0.045, 0.015, L), mugre, rot=('X', af))
    abierto = [a > 15 for a in abiertas]
    if basura:                                                                # adentro, debajo de la orilla
        bol, bol2 = mat("CT_BolsaBasura", "#202024", 0.25), mat("CT_BolsaBasura2", "#3a3d44", 0.3)
        tope = Z1 - 0.25
        for k, (x, y, r) in enumerate(((-1.6, 0.4, 0.62), (-0.7, -0.3, 0.66), (0.2, 0.5, 0.6), (1.1, -0.4, 0.64),
                                       (1.8, 0.45, 0.55), (-1.9, -0.6, 0.5), (0.6, -0.9, 0.48))):
            z = tope - r * 0.8
            m = bol if k % 3 else bol2
            p.esfera((x, y, z), r, m, esc=(1, 0.9, 0.8), segs=14)
            p.cono((x, y, z + r * 0.72), 0.1, 0.04, 0.2, m, segs=8)            # nudo
        p.caja((-0.15, 0.1, tope - 0.25), (0.85, 0.65, 0.5), mat("CT_Carton", "#c49a62", 0.85), rot=('Z', 20))
        pla = mat("CT_Platano", "#f2d03b", 0.6)
        for k in range(3):                                                    # cascara encima de las bolsas
            p.esfera((1.0 + 0.12 * k, -0.4, tope + 0.02 - 0.08 * k), 0.07, pla, esc=(0.6, 0.6, 1.8), segs=8)
        p.ico((-1.1, 0.7, tope - 0.05), 0.16, mat("CT_PapelBola", "#efe9dc", 0.9), sub=1)
    cuerpo = _acabado(p.fin(), bisel=0); contorno(cuerpo, 0.015)
    if texto:                                                                 # letrero blanco sobre los refuerzos
        t = _texto3d(nombre + "_Texto", col, texto, 0.5, "#f4f1e6", extruir=0.01, fuente="ariblk.ttf")
        t.parent = cuerpo; zt_ = 2.3; t.location = (0, frente_y(zt_) - 0.2, zt_)
        t.rotation_euler = (math.radians(90 - af), 0, 0)
    tp = mat("CT_TapaContenedor_" + tapa.lstrip("#"), tapa, 0.4)
    tp2 = mat("CT_TapaContenedor2_" + _oscuro(tapa, 1.6).lstrip("#"), "#2c2e33", 0.45)
    prof = yb_atras - yt_frente + 0.22                                        # fondo de la tapa (con ceja)
    for k, s in enumerate((-1, 1)):                                           # dos tapas negras
        q = P(f"{nombre}_Tapa_{k}", col)
        ancho = xt + 0.08
        q.caja((0, -prof / 2, 0.06), (ancho, prof, 0.12), tp)                 # en ejes de la bisagra (atras arriba)
        for j in range(5):                                                    # nervaduras de adelante hacia atras
            q.caja((-ancho / 2 + 0.3 + j * (ancho - 0.6) / 4, -prof / 2 - 0.1, 0.16), (0.14, prof - 0.5, 0.08), tp2)
        q.caja((0, -0.35, 0.17), (ancho - 0.2, 0.3, 0.1), tp2)                 # escalon junto a la bisagra
        q.caja((0, -prof + 0.03, -0.04), (ancho, 0.08, 0.2), tp)              # ceja de enfrente
        for x in (-ancho / 2 + 0.35, ancho / 2 - 0.35):                       # bisagras
            q.cono((x - 0.15, 0.04, 0.02), 0.07, 0.07, 0.3, gris, segs=10, rot=('Y', 90))
        tap = _acabado(q.fin(), bisel=0); contorno(tap, 0.012)
        tap.parent = cuerpo; tap.location = (s * (xt + 0.08) / 2, yb_atras + 0.12, Z1 + 0.06)
        tap.rotation_euler = (math.radians(-abiertas[k]), 0, 0)
    if olor is None:
        olor = any(abierto)
    if olor:                                                                  # rayitas de mal olor (del lado abierto)
        ol = mat("CT_Olor", "#9fd06a", 0.6, emit=0.6)
        q = P(nombre + "_Olor", col)
        xs = [x for x in ((-1.6, -0.6) if abierto[0] else ()) + ((0.6, 1.6) if abierto[1] else ())] or [-0.6, 0.6]
        for k, x in enumerate(xs):
            pts = [(x + 0.16 * math.sin(i * 1.3 + k), -0.2, Z1 + 0.3 + i * 0.3) for i in range(6)]
            _tubo_var(q, pts, [0.03] * 6, ol, segs=6)
        oo = q.fin(); oo.parent = cuerpo; oo.visible_shadow = False
    cuerpo.scale = (tam,) * 3
    return cuerpo


def estante_frascos(nombre, col, ancho=4.0, alto=4.2, filas=4, colores=("#ff5a5a", "#ffd84a", "#5ad1ff", "#9f6bff",
                    "#6be37a", "#ff8ad8", "#ff9f40"), brillo=6.0, vacios=False, semilla=1, tam_frasco=1.3):
    """ESTANTE de madera lleno de frascos (con poderes de colores que brillan, o vacios). Los frascos son copias que
    comparten malla (ligero aunque sean cientos). Origen al centro de la base; los frascos miran a -Y.
    Devuelve el objeto del estante (los frascos son sus hijos)."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    mad, mad2 = mat("CT_Madera_Estante", "#8a5a32", 0.75), mat("CT_Madera_Estante2", "#6e4426", 0.8)
    prof = 0.6
    for i in range(filas + 1):
        z = 0.15 + i * (alto - 0.3) / filas
        p.caja((0, 0, z), (ancho, prof, 0.08), mad)
    for x in (-ancho / 2, ancho / 2):
        p.caja((x, 0, alto / 2), (0.1, prof, alto), mad2)
    p.caja((0, prof / 2 - 0.03, alto / 2), (ancho, 0.05, alto), mad2)                       # fondo
    est = _acabado(p.fin(), bisel=0.01)
    modelos = {}

    def modelo(c):
        if c not in modelos:
            modelos[c] = frasco(f"{nombre}_Modelo_{len(modelos)}", col, contenido=None if vacios else c,
                                brillo=brillo, etiqueta="", tam=1.0)
            for ob in [modelos[c]] + list(modelos[c].children):
                ob.hide_render = ob.hide_viewport = True
        return modelos[c]

    paso = 0.42 * tam_frasco
    n = int((ancho - 0.3) / paso)
    for i in range(filas):
        z = 0.15 + i * (alto - 0.3) / filas + 0.04
        for k in range(n):
            if rnd.random() < 0.08:
                continue                                         # algun hueco: que no se vea de fabrica
            c = rnd.choice(colores)
            m = modelo(c)
            f = bpy.data.objects.new(f"{nombre}_Frasco_{i}_{k}", m.data); col.objects.link(f)
            f.parent = est
            f.location = (-ancho / 2 + 0.2 + paso / 2 + k * paso + rnd.uniform(-0.03, 0.03), rnd.uniform(-0.08, 0.04), z)
            f.rotation_euler = (0, 0, math.radians(rnd.uniform(-20, 20)))
            f.scale = (tam_frasco * rnd.uniform(0.9, 1.05),) * 3
            for md in m.modifiers:                               # el contorno tambien
                nm = f.modifiers.new(md.name, md.type)
                for a in ("thickness", "offset", "use_flip_normals", "material_offset"):
                    if hasattr(md, a):
                        setattr(nm, a, getattr(md, a))
            for ch in m.children:                                # el poder de adentro (hijo sin contorno)
                c2 = bpy.data.objects.new(f.name + "_" + ch.name.rsplit("_", 1)[-1], ch.data); col.objects.link(c2)
                c2.parent = f; c2.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
                c2.matrix_basis = ch.matrix_basis.copy(); c2.visible_shadow = ch.visible_shadow
    return est


def bote_basura(nombre, col, color="#6f8f5e", tapa=True, basura=True, tam=1.0):
    """BOTE DE BASURA de lamina: cilindro con aros, dos asas y tapa con agarradera (tapa=False: sin tapa y con basura
    asomando: cascara de platano, papel hecho bola y una lata). Origen en la base. Alto ~1,1 * tam (tam 2,2: le cabe un
    personaje de cabeza)."""
    p = P(nombre, col)
    lam, lam2 = mat("CT_Bote_" + color.lstrip("#"), color, 0.4), mat("CT_Bote2_" + _oscuro(color).lstrip("#"), _oscuro(color), 0.45)
    H, r0, r1 = 1.1, 0.42, 0.5
    p.cono((0, 0, 0), r0, r1, H, lam, segs=24)
    for z in (0.15, 0.55, 0.95):
        rz = r0 + (r1 - r0) * z / H
        p.anillo((0, 0, z), rz - 0.01, rz + 0.025, 0.05, lam2, segs=24, eje='Z')
    for s in (-1, 1):
        _arco(p, (s * (r1 + 0.02), 0, H - 0.2), 0.09, lam2, grosor=0.035, k=6,
              desde=-90 if s > 0 else 90, hasta=90 if s > 0 else 270)
    if tapa:
        p.esfera((0, 0, H), r1 + 0.03, lam, esc=(1, 1, 0.22), segs=24)
        _arco(p, (0, 0, H + 0.12), 0.1, lam2, grosor=0.035, k=6)
    elif basura:
        pla, pla2 = mat("CT_Platano", "#f2d03b", 0.6), mat("CT_Platano2", "#b58b2a", 0.7)
        for k, a in enumerate((0, 120, 240)):                  # cascara de platano colgando de la orilla
            aa = math.radians(a)
            p.esfera((0.18 + 0.12 * math.cos(aa), -0.1 + 0.12 * math.sin(aa), H + 0.02 - 0.08 * k), 0.08, pla, esc=(0.6, 0.6, 2.0), segs=8)
        p.esfera((0.18, -0.1, H + 0.12), 0.05, pla2, segs=6)
        p.ico((-0.15, 0.1, H + 0.02), 0.17, mat("CT_PapelBola", "#efe9dc", 0.9), sub=1)
        p.cono((0.05, 0.22, H - 0.12), 0.08, 0.08, 0.24, mat("CT_Lata", "#d9433a", 0.3), segs=12, rot=('Y', 25))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def tendedero(nombre, col, largo=12.0, alto=5.6, prendas=True, semilla=2):
    """TENDEDERO: dos postes en T, cuerda con su comba y ropa de colores colgada con pinzas (playeras, calcetines,
    toallas). A lo largo de X; origen al centro, en el piso. Devuelve el objeto."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    pos, cue = mat("CT_PosteTendedero", "#7a7f86", 0.4), mat("CT_Cuerda", "#efe6d2", 0.9)
    for s in (-1, 1):
        x = s * largo / 2
        p.cono((x, 0, 0), 0.09, 0.08, alto, pos, segs=8)
        p.caja((x, 0, alto - 0.1), (0.1, 1.2, 0.1), pos)
    def comba(x, y):
        t = (x + largo / 2) / largo
        return alto - 0.15 - 0.45 * 4 * t * (1 - t)
    for y in (-0.45, 0.45):                                     # dos cuerdas
        segs = 12
        for i in range(segs):
            x0, x1 = -largo / 2 + largo * i / segs, -largo / 2 + largo * (i + 1) / segs
            z0, z1 = comba(x0, y), comba(x1, y)
            L = math.hypot(x1 - x0, z1 - z0)
            p.caja(((x0 + x1) / 2, y, (z0 + z1) / 2), (L + 0.02, 0.035, 0.035), cue, rot=('Y', -math.degrees(math.atan2(z1 - z0, x1 - x0))))
    if prendas:
        colores = ("#e23b3b", "#3d7fd9", "#f2c230", "#5bbf6a", "#ff8ad8", "#ffffff", "#9f6bff")
        x = -largo / 2 + 0.9
        while x < largo / 2 - 0.9:
            c = rnd.choice(colores)
            m = _mat_tela("CT_Prenda_" + c.lstrip("#"), c, relieve=0.3)
            y = -0.45
            z = comba(x, y)
            tipo = rnd.choice(("playera", "playera", "calcetin", "toalla"))
            if tipo == "playera":
                p.caja((x, y, z - 0.6), (0.9, 0.04, 1.1), m)
                p.caja((x, y, z - 0.25), (1.4, 0.04, 0.4), m)                    # mangas
                w = 1.4
            elif tipo == "calcetin":
                p.caja((x, y, z - 0.35), (0.22, 0.04, 0.7), m)
                p.caja((x + 0.12, y, z - 0.68), (0.4, 0.04, 0.2), m)
                w = 0.5
            else:
                p.caja((x, y, z - 0.75), (1.0, 0.04, 1.5), m)
                for k in range(3):
                    p.caja((x, y - 0.025, z - 0.3 - 0.4 * k), (1.0, 0.01, 0.06), mat("CT_Raya_Toalla", "#ffffff", 0.9))
                w = 1.0
            for dx in (-w / 2 + 0.1, w / 2 - 0.1):                              # pinzas
                cp = rnd.choice(("e23b3b", "3d7fd9", "f2c230"))
                p.caja((x + dx, y, z + 0.02), (0.06, 0.09, 0.22), mat("CT_Pinza_" + cp, "#" + cp, 0.4))
            x += w + rnd.uniform(0.25, 0.5)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return o


def chile(nombre, col, color="#d9271f", tam=1.0):
    """CHILE de caricatura: cuerpo curvo que se adelgaza a la punta y rabito verde. Origen en el rabito; largo ~0,5."""
    p = P(nombre, col)
    m, v = mat("CT_Chile_" + color.lstrip("#"), color, 0.3), mat("CT_RabitoChile", "#3f8f3a", 0.6)
    n = 9
    pts = [(0.07 * math.sin(i / (n - 1) * 2.4), 0, -0.05 - 0.45 * i / (n - 1)) for i in range(n)]
    _tubo_var(p, pts, [0.08 * (1 - 0.85 * (i / (n - 1)) ** 1.3) + 0.008 for i in range(n)], m, segs=12)
    p.cono((0, 0, -0.06), 0.055, 0.02, 0.1, v, segs=8)
    o = p.fin()
    for pl in o.data.polygons:
        pl.use_smooth = True
    o.modifiers.new("Liso", 'SUBSURF').levels = 1
    contorno(o, 0.008); o.scale = (tam,) * 3
    return o


def bolsa_chiles(nombre, col, tam=1.0):
    """BOLSA DE PAPEL abierta con chiles rojos y verdes asomando. Origen en la base; alto ~0,8 * tam."""
    p = P(nombre, col)
    pap = mat("CT_BolsaPapel", "#c79a63", 0.85)
    p.caja((0, 0, 0.3), (0.5, 0.32, 0.6), pap)
    p.caja((0, -0.17, 0.62), (0.5, 0.02, 0.06), mat("CT_BolsaDoblez", "#a87f4e", 0.85))
    rojo, verde, rab = mat("CT_Chile_d9271f", "#d9271f", 0.3), mat("CT_Chile_3fae3a", "#3fae3a", 0.3), mat("CT_RabitoChile", "#3f8f3a", 0.6)
    for k, (x, y, ang, m) in enumerate(((-0.12, 0.0, -20, rojo), (0.0, 0.05, 5, verde), (0.12, -0.02, 25, rojo), (0.06, 0.08, -10, rojo))):
        a = math.radians(ang)
        pts = [(x + math.sin(a) * 0.32 * t - 0.03 * math.sin(t * 3), y, 0.5 + math.cos(a) * 0.32 * t) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        pts.reverse()                                            # de la punta (abajo, dentro de la bolsa) al rabito
        _tubo_var(p, pts, [0.065, 0.06, 0.05, 0.035, 0.015][::-1], m, segs=10)
        p.cono((x + math.sin(a) * 0.33, y, 0.5 + math.cos(a) * 0.33), 0.035, 0.015, 0.07, rab, segs=6)
    o = p.fin()
    for pl in o.data.polygons:
        pl.use_smooth = True
    contorno(o, 0.01); o.scale = (tam,) * 3
    return o


def linterna_mano(nombre, col, color="#2f6fd6", rayo=None, largo_rayo=6.0, tam=1.0):
    """LINTERNA DE MANO apuntando a -Y (cuerpo de color, cabeza ancha y foco que brilla). rayo: None, "luz" (cono de luz
    amarilla transparente) o "laser" (rayo rojo delgado y brillante). Origen en el mango (para la mano). Largo ~0,7."""
    p = P(nombre, col)
    cu, ne = mat("CT_Linterna_" + color.lstrip("#"), color, 0.35), mat("CT_Negro", "#151515", 0.4)
    foco = mat("CT_FocoLinterna", "#fff6c8", 0.2, emit=6.0)
    p.cono((0, 0.25, 0), 0.075, 0.075, 0.5, cu, segs=14, rot=('X', 90))           # cuerpo de y=0,25 a y=-0,25
    p.cono((0, -0.25, 0), 0.08, 0.13, 0.16, cu, segs=14, rot=('X', 90))           # cabeza
    p.cono((0, -0.41, 0), 0.115, 0.115, 0.02, foco, segs=14, rot=('X', 90))
    p.caja((0, 0.0, 0.08), (0.06, 0.12, 0.03), ne)                                  # boton
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01)
    if rayo:
        q = P(nombre + "_Rayo", col)
        if rayo == "laser":
            rm = mat("CT_Laser", "#ff2a2a", 0.2, emit=12.0)
            q.cono((0, -0.42, 0), 0.035, 0.035, largo_rayo, rm, segs=10, rot=('X', 90))
            rg = _mat_vidrio("CT_LaserHalo", "#ff6a6a", 0.25)
            q.cono((0, -0.42, 0), 0.09, 0.09, largo_rayo, rg, segs=10, rot=('X', 90))
        else:
            lm = _mat_vidrio("CT_RayoLuz", "#fff2a8", 0.22)
            bs = next(n for n in lm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            bs.inputs["Emission Color"].default_value = (1, 0.92, 0.6, 1); bs.inputs["Emission Strength"].default_value = 2.0
            q.cono((0, -0.42, 0), 0.12, 0.12 + largo_rayo * 0.22, largo_rayo, lm, segs=20, rot=('X', 90))
        r = q.fin(); r.parent = o
        r.visible_shadow = False
    o.scale = (tam,) * 3
    return o


def manta(nombre, col, texto="PRUEBA DE HÉROES", color="#d12b2b", color_texto="#ffd84a", ancho=12.0, alto=2.4, cuerdas=1.5):
    """MANTA de tela con letras (de pie, mirando a -Y): tela con orilla, letras amarillas con contorno oscuro y cuerdas
    en las esquinas que suben 'cuerdas' unidades (para amarrarla a postes o columnas). Origen al centro de la tela."""
    p = P(nombre, col)
    tel = _mat_tela("CT_Manta_" + color.lstrip("#"), color, relieve=0.25)
    ori = _mat_tela("CT_MantaOrilla_" + _oscuro(color).lstrip("#"), _oscuro(color), relieve=0.25)
    p.caja((0, 0, 0), (ancho, 0.06, alto), tel)
    for z in (-alto / 2, alto / 2):
        p.caja((0, -0.01, z), (ancho + 0.05, 0.08, 0.16), ori)
    cue = mat("CT_Cuerda", "#efe6d2", 0.9)
    for s in (-1, 1):
        p.caja((s * (ancho / 2 - 0.1), 0, alto / 2 + cuerdas / 2), (0.05, 0.05, cuerdas), cue)
    o = _acabado(p.fin(), bisel=0)
    t = _texto3d(nombre + "_Texto", col, texto, alto * 0.42, color_texto, extruir=0.03, borde="#2b1a12", fuente="ariblk.ttf")
    t.parent = o; t.matrix_parent_inverse = o.matrix_world.inverted(); t.location = (0, -0.06, -alto * 0.05)
    while t.dimensions.x > ancho * 0.92 and t.data.size > 0.2:                       # que quepa en la tela
        t.data.size *= 0.92; bpy.context.view_layer.update()
    return o


def escalera_mano(nombre, col, alto=8.0, ancho=1.1, color="#b07a4a"):
    """ESCALERA de mano de madera (largueros y peldanos) de pie, frente -Y. Origen al centro de la base."""
    p = P(nombre, col)
    m = mat("CT_Escalera_" + color.lstrip("#"), color, 0.7)
    for s in (-1, 1):
        p.caja((s * ancho / 2, 0, alto / 2), (0.12, 0.12, alto), m)
    n = int(alto / 0.55)
    for i in range(1, n + 1):
        p.caja((0, 0, i * alto / (n + 1)), (ancho, 0.08, 0.08), m)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.012)
    return o


def pizarron(nombre, col, lineas=("LISTA DE PRECIOS",), ancho=3.6, alto=2.4, color="#24352b", tinta="#f4f1e6"):
    """PIZARRON de gis con marco de madera, letras de gis (Comic) y repisita con gises. De pie, mirando a -Y.
    Origen al centro de la base del marco. La primera linea es el titulo (mas grande)."""
    p = P(nombre, col)
    tab, mad = mat("CT_Pizarron_" + color.lstrip("#"), color, 0.95), mat("CT_MarcoPizarron", "#8a5a32", 0.7)
    p.caja((0, 0, alto / 2), (ancho, 0.06, alto), tab)
    for z in (0, alto):
        p.caja((0, -0.02, z), (ancho + 0.2, 0.12, 0.14), mad)
    for x in (-ancho / 2, ancho / 2):
        p.caja((x, -0.02, alto / 2), (0.14, 0.12, alto + 0.14), mad)
    p.caja((0, -0.12, 0.02), (ancho * 0.6, 0.18, 0.05), mad)                       # repisita
    for k, c in enumerate(("#ffffff", "#ffd84a", "#ff8ad8")):
        p.cono((-0.3 + k * 0.25, -0.12, 0.06), 0.025, 0.025, 0.16, mat("CT_Gis_" + c.lstrip("#"), c, 0.9), segs=6, rot=('Y', 90))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    fuente = "comicbd.ttf" if os.path.exists(r"C:\Windows\Fonts\comicbd.ttf") else "arialbd.ttf"
    _lineas_en_tablero(o, nombre, col, lineas, ancho, alto, 0, tinta, fuente, emit=0.35, y=-0.04)
    return o


def _texto_en_caja(t, ancho_max, alto_max):
    """ajusta el tamano del texto para que quepa COMPLETO en ancho_max x alto_max (crece o se achica): nunca se sale
    del marco. Las medidas del objeto de texto son locales (X = ancho, Y = alto), giren como giren."""
    bpy.context.view_layer.update()
    for _ in range(3):
        d = t.dimensions
        if d.x < 1e-6 or d.y < 1e-6:
            return t
        f = min(ancho_max / d.x, alto_max / d.y)
        t.data.size *= f
        bpy.context.view_layer.update()
    return t


def _lineas_en_tablero(o, nombre, col, lineas, ancho, alto, z0, tinta, fuente, emit=0.0, y=-0.05, titulo=1.35):
    """reparte las lineas en el tablero (de z0 a z0+alto) con margen: cada una lo mas GRANDE posible sin salirse
    (la primera, 'titulo' veces mas alta). Devuelve las letras."""
    mx, mz = 0.08 * ancho, 0.12 * alto
    aw, ah = ancho - 2 * mx, alto - 2 * mz
    pesos = [titulo if i == 0 and len(lineas) > 1 else 1.0 for i in range(len(lineas))]
    total = sum(pesos)
    zc = z0 + alto - mz
    letras = []
    for i, (txt, w) in enumerate(zip(lineas, pesos)):
        h = ah * w / total
        t = _texto3d(f"{nombre}_Linea{i}", col, txt, h, tinta, fuente=fuente)
        if emit:
            t.data.materials[0] = mat("CT_Letra_" + tinta.lstrip("#") + "_e", tinta, 0.9, emit=emit)
        t.parent = o
        t.location = (0, y, zc - h / 2)
        _texto_en_caja(t, aw, h * 0.82)
        zc -= h
        letras.append(t)
    return letras


def letrero_colgante(nombre, col, lineas=("SOLO FRASCOS", "VACÍOS"), ancho=5.0, alto=1.7, color="#f2d06b",
                     tinta="#3a2416", orilla="#7a4e2c", cadenas=0.8):
    """LETRERO COLGANTE de tienda: tabla pintada con orilla de madera, letras GRANDES (Arial Black) que llenan la
    tabla sin salirse, y dos cadenas que suben 'cadenas' unidades. Mira a -Y. ORIGEN ARRIBA (en el techo): la tabla
    cuelga hacia abajo. Para que se lea en 9:16 debe ocupar al menos ~1/3 del ancho del cuadro en su toma."""
    p = P(nombre, col)
    tab, ori = mat("CT_Letrero_" + color.lstrip("#"), color, 0.6), mat("CT_LetreroOrilla_" + orilla.lstrip("#"), orilla, 0.7)
    met = mat("CT_Cadena", "#5a5a60", 0.35)
    zt = -cadenas
    p.caja((0, 0, zt - alto / 2), (ancho, 0.1, alto), tab)
    for z in (zt, zt - alto):
        p.caja((0, -0.02, z), (ancho + 0.16, 0.16, 0.14), ori)
    for x in (-ancho / 2, ancho / 2):
        p.caja((x, -0.02, zt - alto / 2), (0.14, 0.16, alto + 0.14), ori)
    for s in (-1, 1):                                                                 # cadenas (eslabones)
        x = s * (ancho / 2 - 0.4)
        k = max(2, int(cadenas / 0.16))
        for j in range(k):
            p.anillo((x, 0, -(j + 0.5) * cadenas / k), 0.035, 0.06, 0.03, met, segs=8, eje='Y' if j % 2 == 0 else 'Z')
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    _lineas_en_tablero(o, nombre, col, lineas, ancho, alto, zt - alto, tinta, "ariblk.ttf", emit=0.15, y=-0.08, titulo=1.0)
    return o


def caja_madera(nombre, col, tam=1.0, color="#a8784a"):
    """CAJA de madera de tablitas (como de fruta). Cubo de ~1 * tam, origen en la base."""
    p = P(nombre, col)
    m, m2 = mat("CT_Caja_" + color.lstrip("#"), color, 0.8), mat("CT_Caja2_" + _oscuro(color).lstrip("#"), _oscuro(color), 0.8)
    p.caja((0, 0, 0.04), (1, 1, 0.08), m2)
    for s in (-1, 1):
        for z in (0.2, 0.5, 0.8):
            p.caja((0, s * 0.48, z), (1, 0.05, 0.2), m)
            p.caja((s * 0.48, 0, z), (0.05, 1, 0.2), m)
    for x in (-0.47, 0.47):
        for y in (-0.47, 0.47):
            p.caja((x, y, 0.5), (0.08, 0.08, 1.0), m2)
    o = _acabado(p.fin(), bisel=0.008); contorno(o, 0.01); o.scale = (tam,) * 3
    return o


def bolsa_dinero(nombre, col, tam=1.0):
    """COSTAL DE DINERO de caricatura: bolsa gordita amarrada arriba con el signo $ al frente. Origen en la base."""
    p = P(nombre, col)
    m, cu = _mat_tela("CT_Costal", "#c9a46a", relieve=0.5), mat("CT_CordonCostal", "#7a5a30", 0.8)
    p.esfera((0, 0, 0.42), 0.42, m, esc=(1, 1, 0.95), segs=16)
    p.cono((0, 0, 0.72), 0.16, 0.12, 0.14, m, segs=12)
    p.esfera((0, 0, 0.92), 0.18, m, esc=(1.2, 1.2, 0.6), segs=12)
    p.anillo((0, 0, 0.8), 0.12, 0.17, 0.05, cu, segs=14, eje='Z')
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    t = _texto3d(nombre + "_Signo", col, "$", 0.42, "#2f7d4a", extruir=0.02, fuente="ariblk.ttf")
    t.parent = o; t.location = (0, -0.41, 0.42)
    o.scale = (tam,) * 3
    return o


def libro_abierto(nombre, col, tam=1.0, color="#7a2e2e"):
    """LIBRETA de cuentas abierta (pastas de color, hojas crema con renglones). Acostada; origen en el centro."""
    p = P(nombre, col)
    pas, hoja, ren = mat("CT_Pasta_" + color.lstrip("#"), color, 0.7), mat("CT_Hoja", "#f5ecd2", 0.9), mat("CT_Renglon", "#6d7fa8", 0.8)
    for s in (-1, 1):
        p.caja((s * 0.32, 0, 0.02), (0.64, 0.86, 0.03), pas, rot=('Y', -s * 6))
        p.caja((s * 0.3, 0, 0.055), (0.58, 0.8, 0.04), hoja, rot=('Y', -s * 6))
        for k in range(7):
            p.caja((s * 0.3, -0.3 + k * 0.1, 0.08 + 0.003), (0.48, 0.012, 0.004), ren, rot=('Y', -s * 6))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008); o.scale = (tam,) * 3
    return o


def atrapa_poderes(nombre, col, tam=1.0, poder=None):
    """ATRAPAPODERES (la maquina del villano): frasco grande de vidrio sobre una base de laton con manometro, una
    manguera que sale de la tapa y una boquilla de embudo para 'aspirar' el poder. poder = color si ya tiene uno
    adentro. Origen en la base; la boquilla apunta a -Y. Alto ~1,3 * tam."""
    p = P(nombre, col)
    lat, lat2 = mat("CT_Laton", "#c99a3c", 0.3), mat("CT_Laton2", "#8a6422", 0.35)
    gom, vid = mat("CT_Manguera", "#3a3a40", 0.6), _mat_vidrio()
    p.cono((0, 0, 0), 0.45, 0.4, 0.22, lat2, segs=20)
    p.cono((0, 0, 0.22), 0.36, 0.36, 0.06, lat, segs=20)
    p.cono((0, 0, 0.28), 0.32, 0.32, 0.7, vid, segs=20)                            # frasco grande
    p.cono((0, 0, 0.98), 0.35, 0.3, 0.12, lat, segs=20)                            # tapa
    p.cono((0, 0, 1.1), 0.07, 0.07, 0.12, lat2, segs=10)
    p.cono((0.36, -0.2, 0.08), 0.1, 0.1, 0.05, lat, segs=14, rot=('X', 90))        # manometro
    p.cono((0.36, -0.25, 0.08), 0.085, 0.085, 0.01, mat("CT_Esfera", "#f4f1e6", 0.6), segs=14, rot=('X', 90))
    pts = [(0, 0, 1.2), (0, 0, 1.38), (0, -0.25, 1.48), (0, -0.6, 1.35), (0, -0.82, 1.05), (0, -0.95, 0.75)]
    _tubo_var(p, pts, [0.05] * len(pts), gom, segs=10)                             # manguera
    p.cono((0, -0.95, 0.75), 0.05, 0.2, 0.32, lat, segs=16, rot=('X', 160))        # boquilla de embudo
    for z in (0.45, 0.8):                                                          # aros del frasco
        p.anillo((0, 0, z), 0.32, 0.345, 0.04, lat, segs=20, eje='Z')
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    if poder:
        q = P(nombre + "_Poder", col)
        q.esfera((0, 0, 0.6), 0.24, mat("CT_Poder_" + poder.lstrip("#"), poder, 0.3, emit=6.0), esc=(1, 1, 1.3), segs=14)
        q.esfera((0, 0, 0.62), 0.29, _mat_halo(poder, 2.5), esc=(1, 1, 1.3), segs=14)
        po = q.fin(); po.parent = o; po.visible_shadow = False
    o.scale = (tam,) * 3
    return o


def telarana(nombre, col, tam=1.0):
    """TELARANA de esquina (rayos y vueltas delgadas, blanca). Plana en XZ, para pegar en una esquina. Origen en la
    punta (la esquina); se abre hacia +X y -Z. ~1 * tam."""
    p = P(nombre, col)
    m = mat("CT_Telarana", "#f4f2ec", 0.9)
    rayos = [math.radians(a) for a in (-90, -72, -54, -36, -18, 0)]
    for a in rayos:
        p.caja((0.5 * math.cos(a), 0, 0.5 * math.sin(a)), (1.0, 0.008, 0.008), m, rot=('Y', -math.degrees(a)))
    for rr in (0.3, 0.55, 0.8):
        for a0, a1 in zip(rayos, rayos[1:]):
            x0, z0, x1, z1 = rr * math.cos(a0), rr * math.sin(a0), rr * math.cos(a1), rr * math.sin(a1)
            L = math.hypot(x1 - x0, z1 - z0)
            p.caja(((x0 + x1) / 2 * 0.97, 0, (z0 + z1) / 2 * 0.97), (L, 0.006, 0.006), m,
                   rot=('Y', -math.degrees(math.atan2(z1 - z0, x1 - x0))))
    o = p.fin(); o.scale = (tam,) * 3; o.visible_shadow = False
    return o


def veleta(nombre, col, tam=1.0):
    """VELETA de techo: poste, flecha y un gallito de lamina. Origen en la base. Alto ~1,6 * tam."""
    p = P(nombre, col)
    m, m2 = mat("CT_Veleta", "#2e2e33", 0.4), mat("CT_VeletaGallo", "#3a3a40", 0.4)
    p.cono((0, 0, 0), 0.04, 0.03, 1.4, m, segs=8)
    p.caja((0, 0, 1.0), (0.9, 0.03, 0.03), m)
    p.cono((0.45, 0, 1.0), 0.07, 0.0, 0.15, m, segs=4, rot=('Y', 90))
    p.caja((-0.45, 0, 1.0), (0.04, 0.2, 0.14), m)
    p.esfera((0, 0, 1.5), 0.16, m2, esc=(1.4, 0.2, 1), segs=10)                    # gallito (cuerpo)
    p.esfera((0.18, 0, 1.64), 0.07, m2, esc=(1, 0.2, 1), segs=8)
    p.cono((-0.22, 0, 1.52), 0.1, 0.02, 0.22, m2, segs=4, rot=('Y', -60))           # cola
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01); o.scale = (tam,) * 3
    return o


def mostrador(nombre, col, largo=8.0, alto=2.6, prof=1.5, madera="#7a4e2c", vitrina=True):
    """MOSTRADOR de tienda antigua (largo en X; el lado del cliente mira a -Y): mueble de madera con tableros
    enmarcados, cubierta que sobresale y, si vitrina, una seccion de vidrio al frente con repisa adentro (para
    mostrar cosas). Origen al centro de la base. Devuelve el objeto (el vidrio es parte del objeto)."""
    p = P(nombre, col)
    m, m2 = mat("CT_Mostrador_" + madera.lstrip("#"), madera, 0.6), mat("CT_Mostrador2_" + _oscuro(madera).lstrip("#"), _oscuro(madera), 0.65)
    cub = mat("CT_CubiertaMostrador", "#5a3a20", 0.35)
    vid = _mat_vidrio()
    p.caja((0, 0, alto / 2 - 0.05), (largo, prof, alto - 0.1), m)                     # cuerpo
    p.caja((0, -0.08, alto + 0.0), (largo + 0.25, prof + 0.3, 0.14), cub)             # cubierta
    p.caja((0, -prof / 2 + 0.05, 0.12), (largo + 0.05, 0.12, 0.24), m2)               # zoclo
    n = max(2, int(largo / 1.6))
    zt = alto * (0.45 if vitrina else 0.85)
    for i in range(n):                                                                # tableros enmarcados
        x = -largo / 2 + (i + 0.5) * largo / n
        w = largo / n - 0.35
        z0, z1 = 0.4, zt - 0.15
        p.caja((x, -prof / 2 - 0.02, (z0 + z1) / 2), (w, 0.04, z1 - z0), m2)
        p.caja((x, -prof / 2 - 0.035, (z0 + z1) / 2), (w - 0.25, 0.03, z1 - z0 - 0.25), m)
    if vitrina:                                                                       # vitrina al frente arriba
        p.caja((0, -prof / 2 - 0.01, (zt + alto) / 2 - 0.05), (largo - 0.2, 0.06, alto - zt - 0.15), vid)
        p.caja((0, -prof / 2 + 0.1, zt), (largo - 0.2, 0.4, 0.06), m2)                # repisa adentro
        for i in range(n + 1):                                                        # marcos verticales
            p.caja((-largo / 2 + 0.1 + i * (largo - 0.2) / n, -prof / 2 - 0.02, (zt + alto) / 2 - 0.05),
                   (0.1, 0.08, alto - zt - 0.1), m2)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.012)
    return o


def caja_registradora(nombre, col, tam=1.0):
    """CAJA REGISTRADORA antigua de laton: cuerpo con teclas redondas en escalones, letrerito arriba con "$", cajon
    abajo y manivela al lado. Origen en la base; el frente (teclas) mira a -Y. ~0,9 x 0,8 x 1,0 * tam."""
    p = P(nombre, col)
    lat, lat2 = mat("CT_Laton", "#c99a3c", 0.3), mat("CT_Laton2", "#8a6422", 0.35)
    tec, neg = mat("CT_TeclaCaja", "#f4f1e6", 0.5), mat("CT_Negro", "#151515", 0.4)
    p.caja((0, 0, 0.12), (0.95, 0.8, 0.24), lat2)                                     # cajon
    p.caja((0, -0.405, 0.12), (0.3, 0.02, 0.06), lat)
    p.caja((0, 0.08, 0.5), (0.9, 0.62, 0.52), lat)                                    # cuerpo
    for f in range(3):                                                                # teclas en escalones
        z = 0.32 + f * 0.13; y = -0.25 + f * 0.09
        p.caja((0, y + 0.02, z - 0.04), (0.84, 0.16, 0.08), lat2)
        for k in range(5):
            p.cono((-0.32 + k * 0.16, y, z), 0.05, 0.05, 0.05, tec, segs=10)
            p.cono((-0.32 + k * 0.16, y, z + 0.05), 0.05, 0.045, 0.01, neg, segs=10)
    p.caja((0, 0.22, 0.92), (0.6, 0.12, 0.3), lat)                                    # letrerito
    p.caja((0, 0.155, 0.92), (0.46, 0.02, 0.2), mat("CT_PapelCaja", "#f4f1e6", 0.6))
    p.cono((0.5, 0.1, 0.5), 0.05, 0.05, 0.18, lat2, segs=8, rot=('Y', 90))            # manivela
    p.caja((0.62, 0.1, 0.42), (0.04, 0.04, 0.2), lat2)
    p.esfera((0.62, 0.1, 0.3), 0.05, neg, segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01)
    t = _texto3d(nombre + "_Signo", col, "$", 0.18, "#2f7d4a", fuente="ariblk.ttf")
    t.parent = o; t.location = (0, 0.14, 0.92)
    o.scale = (tam,) * 3
    return o


def campanita(nombre, col, tam=1.0):
    """CAMPANITA de mostrador (domo dorado con boton sobre base negra). Origen en la base. ~0,3 * tam."""
    p = P(nombre, col)
    oro, neg = mat("CT_Oro_Campana", "#e2b23a", 0.2), mat("CT_Negro", "#151515", 0.4)
    p.cono((0, 0, 0), 0.16, 0.16, 0.04, neg, segs=16)
    p.esfera((0, 0, 0.05), 0.13, oro, esc=(1, 1, 0.75), segs=16)
    abajo = [v for v in p.bm.verts if v.co.z < 0.049]
    p.cono((0, 0, 0.14), 0.015, 0.015, 0.05, oro, segs=8)
    p.esfera((0, 0, 0.2), 0.03, oro, segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.006); o.scale = (tam,) * 3
    return o


def barril(nombre, col, tam=1.0, madera="#9a6a3c"):
    """BARRIL de madera con duelas y dos aros de metal. Origen en la base; alto ~1,2 * tam."""
    p = P(nombre, col)
    m, m2, aro = mat("CT_Barril_" + madera.lstrip("#"), madera, 0.75), mat("CT_Barril2", _oscuro(madera), 0.8), mat("CT_AroBarril", "#4a4a50", 0.4)
    secc = [(0.0, 0.42), (0.3, 0.5), (0.6, 0.53), (0.9, 0.5), (1.2, 0.42)]
    n = 16
    p.loft([(z, [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]) for z, r in secc], m)
    for i in range(n):                                                                # rayas entre duelas
        a = 2 * math.pi * (i + 0.5) / n
        p.caja((0.515 * math.cos(a), 0.515 * math.sin(a), 0.6), (0.02, 0.02, 1.1), m2, rot=('Z', math.degrees(a)))
    for z, r in ((0.22, 0.49), (0.98, 0.49)):
        p.anillo((0, 0, z), r - 0.01, r + 0.035, 0.07, aro, segs=n, eje='Z')
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def _globos(p, puntos, colores, r=0.55, semilla=1):
    """globos brillantes (gota con nudito y reflejo) en los puntos dados (centro de cada globo)."""
    rnd = __import__("random").Random(semilla)
    brillo = mat("CT_BrilloGlobo", "#ffffff", 0.2, emit=1.5)
    for i, c in enumerate(puntos):
        col_ = colores[i % len(colores)]
        m = mat("CT_Globo_" + col_.lstrip("#"), col_, 0.25)
        rr = r * rnd.uniform(0.9, 1.1)
        x, y, z = c
        p.esfera((x, y, z), rr, m, esc=(1, 1, 1.18), segs=14)
        p.cono((x, y, z - rr * 1.2), 0.06, 0.1, 0.12, m, segs=8)
        p.esfera((x - rr * 0.35, y - rr * 0.75, z + rr * 0.4), rr * 0.18, brillo, esc=(1, 0.4, 1.4), segs=8)


def racimo_globos(nombre, col, colores=("#ff3d7f", "#ffd84a", "#3da5ff", "#6fd36f", "#b46bff"), n=7, alto=5.0, semilla=1):
    """RACIMO de globos amarrado a una pesita: hilos que suben y globos de colores arriba. Origen en el piso."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    hilo = mat("CT_HiloGlobo", "#f4f1e6", 0.8)
    p.cono((0, 0, 0), 0.18, 0.14, 0.25, mat("CT_Pesita", "#e2b23a", 0.3), segs=10)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.3, 0.3)
        rr = 0.55 + 0.4 * (i % 2)
        c = (rr * math.cos(a), rr * math.sin(a), alto - 0.4 * (i % 3) + rnd.uniform(-0.2, 0.2))
        pts.append(c)
        _tubo_var(p, [(0, 0, 0.25), (c[0] * 0.5, c[1] * 0.5, alto * 0.55), (c[0], c[1], c[2] - 0.75)], [0.012] * 3, hilo, segs=4)
    _globos(p, pts, colores, r=0.55, semilla=semilla)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return o


def arco_globos(nombre, col, ancho=14.0, alto=9.0, colores=("#ff3d7f", "#ffd84a", "#3da5ff", "#ffffff", "#b46bff"), semilla=2):
    """ARCO de globos (medio ovalo de globos de colores, dos o tres por paso). En el plano XZ; origen al centro del
    piso; los pies del arco en x = +-ancho/2."""
    p = P(nombre, col)
    pts = []
    n = int(math.pi * (ancho / 2 + alto) / 2 / 0.75)
    for i in range(n + 1):
        t = math.pi * i / n
        x, z = -math.cos(t) * ancho / 2, math.sin(t) * alto
        for k, (dy, dz) in enumerate(((0.0, 0.0), (0.45, 0.35), (-0.45, 0.35))):
            pts.append((x + 0.2 * k, dy, z + dz + 0.4))
    _globos(p, pts, colores, r=0.5, semilla=semilla)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return o


def gradas(nombre, col, largo=12.0, filas=4, color="#3d7fd9", madera="#c99a63"):
    """GRADAS para publico: escalones de madera con asientos (tablones) sobre estructura de color y barandal atras.
    El publico mira a -Y; largo en X; origen al centro del frente, en el piso. Fondo ~1,1 por fila; alto 0,9 por fila."""
    p = P(nombre, col)
    est, tab = mat("CT_Gradas_" + color.lstrip("#"), color, 0.4), mat("CT_TablonGradas", madera, 0.7)
    for i in range(filas):
        y, z = 0.55 + i * 1.1, 0.45 + i * 0.9
        p.caja((0, y, z / 2), (largo, 1.1, z), est)                                   # escalon
        p.caja((0, y - 0.1, z + 0.08), (largo, 0.6, 0.12), tab)                       # asiento
        p.caja((0, y - 0.48, z - 0.2), (largo, 0.06, 0.3), tab)                       # tabla de frente
    yb, zb = filas * 1.1 + 0.1, filas * 0.9 + 0.45
    for x in [(-largo / 2) + k * largo / 6 for k in range(7)]:                        # barandal
        p.caja((x, yb, zb + 0.5), (0.08, 0.08, 1.2), est)
    p.caja((0, yb, zb + 1.1), (largo, 0.1, 0.1), est)
    p.caja((0, yb, zb + 0.6), (largo, 0.06, 0.06), est)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.012)
    return o


def podio_ganadores(nombre, col, colores=("#e2b23a", "#c9ccd3", "#c9874a"), tam=1.0):
    """PODIO DE GANADORES: tres bloques (1 al centro y mas alto, 2 a la izquierda, 3 a la derecha) con su numero y
    una franja de color (oro, plata, bronce). Frente -Y; origen al centro de la base."""
    p = P(nombre, col)
    bl = mat("CT_PodioBlanco", "#f4f1e6", 0.5)
    datos = [(0.0, 1.5, "1", colores[0]), (-1.6, 1.0, "2", colores[1]), (1.6, 0.7, "3", colores[2])]
    for x, h, _, c in datos:
        p.caja((x, 0, h / 2), (1.5, 1.4, h), bl)
        p.caja((x, -0.71, h - 0.18), (1.5, 0.04, 0.22), mat("CT_Franja_" + c.lstrip("#"), c, 0.3))
    o = _acabado(p.fin(), bisel=0.02); contorno(o, 0.012)
    for x, h, num, c in datos:
        t = _texto3d(f"{nombre}_N{num}", col, num, 0.6, c, extruir=0.04, borde="#2b1a12", fuente="ariblk.ttf")
        t.parent = o; t.location = (x, -0.72, h * 0.45)
    o.scale = (tam,) * 3
    return o


def mesa_jueces(nombre, col, largo=6.0, mantel="#c0262f", n=3):
    """MESA DE JUECES: mesa larga con mantel rojo de orilla dorada que cae al frente, letreritos "JUEZ", vasos de agua
    y microfonitos. Los jueces se sientan del lado +Y (miran a -Y). Origen al centro de la base."""
    p = P(nombre, col)
    tm, oro = _mat_tela("CT_Mantel_" + mantel.lstrip("#"), mantel, relieve=0.3), mat("CT_OrillaOro", "#e2b23a", 0.3)
    p.caja((0, 0, 1.5), (largo, 1.6, 0.12), tm)                                       # cubierta
    p.caja((0, -0.8, 0.8), (largo, 0.05, 1.45), tm)                                   # faldon al frente
    for s in (-1, 1):
        p.caja((s * largo / 2, 0, 0.8), (0.05, 1.6, 1.45), tm)
    p.caja((0, -0.83, 0.2), (largo + 0.02, 0.03, 0.12), oro)
    p.caja((0, -0.83, 1.4), (largo + 0.02, 0.03, 0.08), oro)
    car, vas = mat("CT_Tarjeta", "#f4f1e6", 0.7, emit=0.2), _mat_vidrio()
    neg = mat("CT_Negro", "#151515", 0.4)
    for i in range(n):
        x = -largo / 2 + (i + 0.5) * largo / n
        p.caja((x, -0.55, 1.75), (0.9, 0.04, 0.4), car, rot=('X', -12))               # letrerito
        p.cono((x + 0.6, -0.3, 1.56), 0.08, 0.1, 0.25, vas, segs=10)                  # vaso
        p.cono((x - 0.5, -0.2, 1.56), 0.06, 0.05, 0.05, neg, segs=8)                  # microfono de mesa
        _tubo_var(p, [(x - 0.5, -0.2, 1.6), (x - 0.5, -0.35, 1.85), (x - 0.45, -0.5, 1.95)], [0.015] * 3, neg, segs=5)
        p.esfera((x - 0.45, -0.52, 1.98), 0.05, neg, segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    for i in range(n):
        x = -largo / 2 + (i + 0.5) * largo / n
        t = _texto3d(f"{nombre}_Juez{i}", col, "JUEZ", 0.16, "#2b1a12", fuente="ariblk.ttf")
        t.parent = o; t.location = (x, -0.6, 1.75); t.rotation_euler = (math.radians(78), 0, 0)
    return o


def cuna(nombre, col, color="#f4f1e6", cobija="#9fd0f5", largo=3.4, ancho=2.0, alto=2.4):
    """CUNA de bebe: patas redondeadas, barrotes en los cuatro lados, cabecera con arco, colchon, almohada y cobija
    acolchada que cae por un lado. Largo en X; origen al centro de la base. Altura del colchon ~1,0."""
    p = P(nombre, col)
    m, m2 = mat("CT_Cuna_" + color.lstrip("#"), color, 0.5), mat("CT_Cuna2_" + _oscuro(color, 0.85).lstrip("#"), _oscuro(color, 0.85), 0.5)
    zc = 0.95                                                                          # arriba del colchon
    for x in (-largo / 2, largo / 2):
        for y in (-ancho / 2, ancho / 2):
            p.cono((x, y, 0), 0.1, 0.09, alto, m, segs=12)
            p.esfera((x, y, alto + 0.05), 0.13, m, segs=12)
    for z in (0.7, alto - 0.08):                                                      # largueros
        for y in (-ancho / 2, ancho / 2):
            p.caja((0, y, z), (largo, 0.1, 0.1), m)
        for x in (-largo / 2, largo / 2):
            p.caja((x, 0, z), (0.1, ancho, 0.1), m)
    for i in range(1, 13):                                                            # barrotes largos
        x = -largo / 2 + i * largo / 13
        for y in (-ancho / 2, ancho / 2):
            p.cono((x, y, 0.7), 0.035, 0.035, alto - 0.78, m2, segs=6)
    for i in range(1, 7):
        y = -ancho / 2 + i * ancho / 7
        for x in (-largo / 2, largo / 2):
            p.cono((x, y, 0.7), 0.035, 0.035, alto - 0.78, m2, segs=6)
    for s in (-1, 1):                                                                 # cabecera con arco
        _arco(p, (s * largo / 2, 0, alto - 0.1), ancho / 2, m, grosor=0.06, k=10)
    p.caja((0, 0, 0.82), (largo - 0.1, ancho - 0.1, 0.24), mat("CT_Colchon", "#fbfbf6", 0.8))
    cm = _mat_tela("CT_CobijaCuna_" + cobija.lstrip("#"), cobija, relieve=0.5)
    p.esfera((-largo / 2 + 0.55, 0, zc + 0.08), 0.42, mat("CT_AlmohadaCuna", "#ffffff", 0.8), esc=(0.8, 1.6, 0.4), segs=14)
    p.caja((0.4, 0, zc + 0.06), (largo - 1.0, ancho - 0.2, 0.12), cm)                  # cobija
    p.caja((0.4, -ancho / 2 - 0.05, zc - 0.25), (largo - 1.2, 0.06, 0.65), cm, rot=('X', 6))   # cae por un lado
    for k in range(4):
        p.esfera((-0.4 + k * 0.55, -ancho / 2 + 0.3, zc + 0.13), 0.06, mat("CT_EstrellaCobija", "#ffd84a", 0.6), esc=(1, 1, 0.4), segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return o


def movil_cuna(nombre, col, colores=("#ffd84a", "#ff8ad8", "#7fc8ff", "#9fe0a0")):
    """MOVIL de cuna: brazo curvo y aro del que cuelgan estrellas, una luna y nubecitas con hilos. Origen en la base del
    brazo (se pega a la orilla de la cuna); cuelga hacia +X. Alto ~2,2."""
    p = P(nombre, col)
    m = mat("CT_MovilBrazo", "#f4f1e6", 0.5)
    hilo = mat("CT_HiloGlobo", "#f4f1e6", 0.8)
    _tubo_var(p, [(0, 0, 0), (0, 0, 1.6), (0.3, 0, 2.1), (0.9, 0, 2.2)], [0.04] * 4, m, segs=8)
    p.anillo((0.9, 0, 2.1), 0.45, 0.5, 0.04, m, segs=20, eje='Z')
    for k in range(5):
        a = 2 * math.pi * k / 5
        x, y = 0.9 + 0.48 * math.cos(a), 0.48 * math.sin(a)
        L = 0.4 + 0.15 * (k % 2)
        p.caja((x, y, 2.1 - L / 2), (0.01, 0.01, L), hilo)
        c = colores[k % len(colores)]
        cm = mat("CT_Movil_" + c.lstrip("#"), c, 0.5, emit=0.2)
        z = 2.1 - L - 0.12
        if k % 3 == 0:                                                                # estrella
            pts = []
            for j in range(10):
                rr = 0.16 if j % 2 == 0 else 0.07
                aa = math.pi / 2 + j * math.pi / 5
                pts.append((x + rr * math.cos(aa), z + rr * math.sin(aa)))
            p.placa_xz(pts, y - 0.025, 0.05, cm)
        elif k % 3 == 1:                                                              # luna
            p.esfera((x, y, z), 0.14, cm, esc=(0.45, 0.3, 1), segs=10)
        else:                                                                         # nubecita
            for dx in (-0.08, 0.0, 0.08):
                p.esfera((x + dx, y, z + (0.03 if dx == 0 else 0)), 0.08, mat("CT_Nube", "#ffffff", 0.7), esc=(1, 0.5, 0.8), segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    return o


def mecedora(nombre, col, color="#a8784a", cojin="#f2a5c4"):
    """MECEDORA de madera con patines curvos, respaldo de barrotes y cojin. Frente -Y; origen al centro de la base."""
    p = P(nombre, col)
    m, cm = mat("CT_Mecedora_" + color.lstrip("#"), color, 0.6), _mat_tela("CT_CojinMece_" + cojin.lstrip("#"), cojin, relieve=0.4)
    for s in (-1, 1):
        x = s * 0.75
        pts = [(x, -1.0 + i * 0.25, 0.08 + 0.09 * ((i - 4) / 4) ** 2 * 2) for i in range(9)]
        _tubo_var(p, pts, [0.07] * 9, m, segs=8)                                     # patin curvo
        for y in (-0.55, 0.5):
            p.cono((x, y, 0.1), 0.06, 0.05, 1.2, m, segs=8)                            # patas
        p.cono((x, 0.55, 1.25), 0.06, 0.05, 1.7, m, segs=8)                            # postes del respaldo
        p.caja((x, -0.05, 1.75), (0.1, 1.1, 0.08), m)                                  # brazo
    p.caja((0, 0, 1.3), (1.6, 1.25, 0.14), m)                                          # asiento
    p.caja((0, -0.05, 1.42), (1.4, 1.1, 0.14), cm)                                     # cojin
    for k in range(5):
        p.cono((-0.5 + k * 0.25, 0.55, 1.35), 0.035, 0.035, 1.4, m, segs=6)            # barrotes
    p.caja((0, 0.55, 2.85), (1.65, 0.12, 0.25), m)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012)
    return o


def chupon(rig, col, nombre=None, color="#7fc8ff", alto=0.33):
    """CHUPON de bebe en la boca (escudo de color, botoncito y argolla), pegado a la cabeza."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Chupon"
    _, mn, mx = _caja_hueso(rig, "Head")
    cx, w, h = (mn.x + mx.x) / 2, mx.x - mn.x, mx.z - mn.z
    k = w / 1.2
    z = mn.z + alto * h
    y = _frente_cabeza(mn, mx, cx) - 0.05 * k
    p = P(nombre, col)
    p.M = rig.matrix_world.copy()
    esc = mat("CT_Chupon_" + color.lstrip("#"), color, 0.3)
    p.esfera((cx, y, z), 0.15 * k, esc, esc=(1.35, 0.25, 1), segs=16)
    p.esfera((cx, y - 0.05 * k, z), 0.055 * k, mat("CT_ChuponBoton", "#ffffff", 0.4), segs=10)
    p.anillo((cx, y - 0.1 * k, z - 0.04 * k), 0.06 * k, 0.085 * k, 0.025 * k, esc, segs=14, eje='Y')
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.006)
    return _pegar_hueso(o, rig, "Head")


def panal(rig, col, nombre=None, color="#ffffff"):
    """PANAL de bebe: calzon esponjado alrededor de la cadera con dos pestanas al frente, pegado a LowerTorso."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Panal"
    _, lm, lM = _caja_hueso(rig, "LowerTorso")
    cx, cy = (lm.x + lM.x) / 2, (lm.y + lM.y) / 2
    W, D = lM.x - lm.x, lM.y - lm.y
    p = P(nombre, col)
    p.M = rig.matrix_world.copy()
    m = _mat_tela("CT_Panal_" + color.lstrip("#"), color, relieve=0.35)
    p.esfera((cx, cy, lm.z + (lM.z - lm.z) * 0.35), 0.58 * W, m, esc=(1, D / W * 1.25, 0.75), segs=18)
    for s in (-1, 1):
        p.caja((cx + s * 0.32 * W, lm.y - 0.04, lm.z + (lM.z - lm.z) * 0.62), (0.22 * W, 0.04, 0.18 * W), mat("CT_PestanaPanal", "#9fd0f5", 0.5))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    return _pegar_hueso(o, rig, "LowerTorso")


def chorro_luz(nombre, col, desde, hasta, color="#ffd84a", grosor=0.18, curva=0.8):
    """CHORRO DE LUZ curvo (para "le robo su poder"): tubo brillante y transparente que va de 'desde' a 'hasta' (puntos
    del mundo) con un arco hacia arriba, nucleo claro y chispitas. Devuelve el objeto (sin contorno ni sombra)."""
    a, b = Vector(desde), Vector(hasta)
    pts = []
    for i in range(9):
        t = i / 8
        q = a.lerp(b, t) + Vector((0, 0, curva * 4 * t * (1 - t)))
        pts.append(tuple(q))
    p = P(nombre, col)
    _tubo_var(p, pts, [grosor * (1.0 - 0.45 * i / 8) for i in range(9)], _mat_halo(color, 4.0, 0.4), segs=12)
    _tubo_var(p, pts, [grosor * 0.35 * (1.0 - 0.4 * i / 8) for i in range(9)],
              mat("CT_ChorroNucleo", "#fffbe6", 0.3, emit=10.0), segs=8)
    chis = mat("CT_Chispa", "#ffffff", 0.2, emit=8.0)
    rnd = __import__("random").Random(4)
    for i in range(12):
        t = rnd.random()
        q = a.lerp(b, t) + Vector((0, 0, curva * 4 * t * (1 - t))) + Vector((rnd.uniform(-1, 1) * grosor * 1.6,
                                                                                rnd.uniform(-1, 1) * grosor * 1.6,
                                                                                rnd.uniform(-1, 1) * grosor * 1.6))
        p.ico(tuple(q), rnd.uniform(0.02, 0.045), chis, sub=1)
    o = p.fin(); o.visible_shadow = False
    for pl in o.data.polygons:
        pl.use_smooth = True
    return o


def fondo_noche(nombre, col, ancho=12.0, alto=8.0, luna=True):
    """FONDO de noche para ver por una ventana: cielo azul oscuro, luna grande que brilla y estrellitas. De pie en el
    plano XZ mirando a -Y; origen al centro."""
    p = P(nombre, col)
    p.caja((0, 0, 0), (ancho, 0.05, alto), mat("CT_CieloNoche", "#14204a", 0.9, emit=0.6))
    if luna:
        p.cono((ancho * 0.22, -0.05, alto * 0.18), alto * 0.14, alto * 0.14, 0.04, mat("CT_Luna", "#fff4c8", 0.5, emit=3.0), segs=32, rot=('X', 90))
    rnd = __import__("random").Random(8)
    est = mat("CT_EstrellaCielo", "#ffffff", 0.5, emit=4.0)
    for _ in range(60):
        r = rnd.uniform(0.03, 0.08)
        p.ico((rnd.uniform(-ancho / 2, ancho / 2), -0.06, rnd.uniform(-alto / 2, alto / 2)), r, est, sub=1)
    o = p.fin(); o.visible_shadow = False
    return o


def babero(rig, col, nombre=None, color="#ffffff", orilla="#7fc8ff", estrella="#ffd84a"):
    """BABERO de bebe al frente del pecho (redondito, con orilla de color y una estrellita), pegado a UpperTorso."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Babero"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    cx, W, H = (um.x + uM.x) / 2, uM.x - um.x, uM.z - um.z
    yf = _frente_torso(rig, cx, W, um.z, uM.z) - 0.02
    p = P(nombre, col)
    p.M = rig.matrix_world.copy()
    zc = uM.z - H * 0.36
    p.esfera((cx, yf - 0.01, zc), W * 0.36, mat("CT_BaberoOrilla_" + orilla.lstrip("#"), orilla, 0.6), esc=(1, 0.08, 0.95), segs=20)
    p.esfera((cx, yf - 0.03, zc), W * 0.31, _mat_tela("CT_Babero_" + color.lstrip("#"), color, relieve=0.3), esc=(1, 0.08, 0.95), segs=20)
    pts = []
    for j in range(10):
        rr = W * (0.11 if j % 2 == 0 else 0.045)
        a = math.pi / 2 + j * math.pi / 5
        pts.append((cx + rr * math.cos(a), zc - W * 0.02 + rr * math.sin(a)))
    p.placa_xz(pts, yf - 0.07, 0.02, mat("CT_BaberoEstrella_" + estrella.lstrip("#"), estrella, 0.5))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    return _pegar_hueso(o, rig, "UpperTorso")


def destellos(nombre, col, puntos, tam=0.25, colores=("#ffffff", "#fff3a0", "#ffd84a"), fuerza=8.0):
    """DESTELLOS de caricatura: estrellitas de 4 puntas (como el brillo de los dibujos) en los puntos dados, mirando a -Y.
    Se entienden mejor que puntitos: "esto brilla". Devuelve un objeto sin sombra."""
    p = P(nombre, col)
    for i, c in enumerate(puntos):
        cc = colores[i % len(colores)]
        m = mat("CT_Destello_" + cc.lstrip("#"), cc, 0.3, emit=fuerza)
        s = tam * (0.6 + 0.4 * ((i * 7) % 5) / 4)
        x, y, z = c
        pts = []
        for j in range(8):
            rr = s if j % 2 == 0 else s * 0.22
            a = j * math.pi / 4
            pts.append((x + rr * math.cos(a), z + rr * math.sin(a)))
        p.placa_xz(pts, y, 0.01, m)
    o = p.fin(); o.visible_shadow = False
    return o


def rayos_brillo(nombre, col, n=12, largo=2.4, ancho=0.35, color="#ffd84a", alfa=0.35, fuerza=3.0, hueco=0.6):
    """RAYOS DE BRILLO de caricatura (como sol): triangulos de luz que salen del centro hacia afuera en el plano XZ,
    transparentes y brillantes, con un hueco en medio (para que no tapen lo que esta adelante). Ponerlos DETRAS del
    personaje. Origen al centro."""
    nombre_m = "CT_RayoBrillo_" + color.lstrip("#")
    m = bpy.data.materials.get(nombre_m)
    if m is None:
        m = mat(nombre_m, color, 0.5, emit=fuerza)
        bs = next(nn for nn in m.node_tree.nodes if nn.type == 'BSDF_PRINCIPLED')
        bs.inputs["Alpha"].default_value = alfa
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            m.blend_method = 'BLEND'
    p = P(nombre, col)
    for i in range(n):
        a = 2 * math.pi * i / n + 0.13
        L = largo * (1.0 if i % 2 == 0 else 0.7)
        d = (math.cos(a), math.sin(a)); t = (-d[1], d[0])
        pts = [(hueco * d[0] + t[0] * ancho * 0.25, hueco * d[1] + t[1] * ancho * 0.25),
               (L * d[0] + t[0] * ancho, L * d[1] + t[1] * ancho),
               (L * d[0] - t[0] * ancho, L * d[1] - t[1] * ancho),
               (hueco * d[0] - t[0] * ancho * 0.25, hueco * d[1] - t[1] * ancho * 0.25)]
        p.placa_xz(pts, 0, 0.01, m)
    o = p.fin(); o.visible_shadow = False
    return o


# ----------------------------------------------------------------- panaderia (EP007)
def _pan_mats(quemado):
    if quemado:
        return mat("CT_PanQuemado", "#2a1d16", 0.8), mat("CT_PanQuemado2", "#14100d", 0.9)
    return mat("CT_PanDorado", "#d9954a", 0.6), mat("CT_PanDorado2", "#b06a2a", 0.65)


def concha(p, c, tam=1.0, cubierta="#f6efe0", quemado=False):
    """agrega a P una CONCHA (pan dulce mexicano): bollo dorado con costra de azucar en cuadritos. c = centro de la base."""
    x, y, z = c
    base, _ = _pan_mats(quemado)
    top = mat("CT_CostraConcha_" + cubierta.lstrip("#"), "#3a2a20" if quemado else cubierta, 0.7)
    raya = mat("CT_RayaConcha", "#1a1410" if quemado else "#c9a477", 0.7)
    r = 0.38 * tam
    p.esfera((x, y, z + r * 0.35), r, base, esc=(1, 1, 0.62), segs=16)
    p.esfera((x, y, z + r * 0.48), r * 0.92, top, esc=(1, 1, 0.5), segs=16)
    for s in (-1, 1):                                                                 # cuadritos de la costra
        for k in range(-2, 3):
            L = r * 1.5 * math.sqrt(max(0.05, 1 - (k / 3.2) ** 2))
            ang = math.radians(45 * s)
            ox, oy = -math.sin(ang) * k * r * 0.32, math.cos(ang) * k * r * 0.32
            p.caja((x + ox, y + oy, z + r * 0.93), (L, 0.025 * tam, 0.02 * tam), raya, rot=('Z', 45 * s))
    return p


def bolillo(p, c, tam=1.0, quemado=False, ang=0.0):
    """agrega a P un BOLILLO: pan alargado dorado con su rajita encima. c = centro de la base."""
    x, y, z = c
    base, b2 = _pan_mats(quemado)
    a = math.radians(ang)
    L, r = 0.5 * tam, 0.2 * tam
    pts = [(x + math.cos(a) * L * t, y + math.sin(a) * L * t, z + r * 0.85 + 0.04 * (1 - t * t) * tam) for t in (-1, -0.6, 0, 0.6, 1)]
    _tubo_var(p, pts, [r * 0.35, r * 0.85, r, r * 0.85, r * 0.35], base, segs=12, aplanar=0.85)
    p.caja((x, y, z + r * 1.72), (L * 1.1, 0.04 * tam, 0.025 * tam), b2, rot=('Z', ang))
    return p


def cuernito(p, c, tam=1.0, quemado=False, ang=0.0):
    """agrega a P un CUERNITO (media luna): curvo, grueso al centro y delgado en las puntas, con gajos."""
    x, y, z = c
    base, b2 = _pan_mats(quemado)
    a0 = math.radians(ang)
    pts, rr = [], []
    for i in range(9):
        t = -1 + 2 * i / 8
        aa = a0 + t * 1.1
        pts.append((x + math.cos(aa) * 0.38 * tam, y + math.sin(aa) * 0.38 * tam, z + 0.13 * tam))
        rr.append(0.15 * tam * (1 - 0.75 * t * t) + 0.02 * tam)
    _tubo_var(p, pts, rr, base, segs=10)
    for i in (2, 4, 6):                                                               # gajos
        q = pts[i]
        p.anillo(q, rr[i] * 0.96, rr[i] * 1.04, 0.025 * tam, b2, segs=12, eje='Z')
    return p


def charola_panes(nombre, col, ancho=2.4, fondo=1.2, tipo="mixto", quemados=False, semilla=1):
    """CHAROLA de lamina con panes en filas (tipo: concha, bolillo, cuernito o mixto). quemados=True: todos negros (para
    "se le quemaron los panes"). Origen al centro de la charola, abajo."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    lam = mat("CT_Charola", "#9a9ca3", 0.35)
    p.caja((0, 0, 0.03), (ancho, fondo, 0.06), lam)
    for x in (-ancho / 2, ancho / 2):
        p.caja((x, 0, 0.07), (0.04, fondo, 0.1), lam)
    for y in (-fondo / 2, fondo / 2):
        p.caja((0, y, 0.07), (ancho, 0.04, 0.1), lam)
    tipos = ("concha", "bolillo", "cuernito")
    nx, ny = max(1, int(ancho / 0.8)), max(1, int(fondo / 0.6))
    for i in range(nx):
        for j in range(ny):
            t = tipo if tipo != "mixto" else tipos[(i + j) % 3]
            c = (-ancho / 2 + (i + 0.5) * ancho / nx, -fondo / 2 + (j + 0.5) * fondo / ny, 0.06)
            if t == "concha":
                concha(p, c, tam=0.85, cubierta=rnd.choice(("#f6efe0", "#f6c1d6", "#6b4a33")), quemado=quemados)
            elif t == "bolillo":
                bolillo(p, c, tam=0.8, quemado=quemados, ang=rnd.uniform(-15, 15))
            else:
                cuernito(p, c, tam=0.8, quemado=quemados, ang=rnd.uniform(-30, 30) + 90)
    o = p.fin()
    for pl in o.data.polygons:
        pl.use_smooth = True
    contorno(o, 0.01)
    return o


def anaquel_panes(nombre, col, ancho=2.8, alto=5.0, niveles=5, semilla=3):
    """ANAQUEL de metal con charolas de pan en cada nivel (mixto). Frente -Y; origen al centro de la base."""
    p = P(nombre, col)
    met = mat("CT_Anaquel", "#b8bcc4", 0.35)
    for x in (-ancho / 2, ancho / 2):
        for y in (-0.6, 0.6):
            p.caja((x, y, alto / 2), (0.08, 0.08, alto), met)
    for k in range(niveles):
        z = 0.35 + k * (alto - 0.5) / (niveles - 1)
        for y in (-0.6, 0.6):
            p.caja((0, y, z), (ancho, 0.06, 0.06), met)
    ra = _acabado(p.fin(), bisel=0); contorno(ra, 0.01)
    for k in range(niveles):
        z = 0.35 + k * (alto - 0.5) / (niveles - 1)
        ch = charola_panes(f"{nombre}_Charola_{k}", col, ancho=ancho - 0.2, fondo=1.15, semilla=semilla + k)
        ch.parent = ra; ch.location = (0, 0, z + 0.03)
    return ra


def horno_lena(nombre, col, ancho=4.4, fuego=True):
    """HORNO DE LENA de ladrillo (textura de ladrillos): base cuadrada, cupula, boca en arco al frente (-Y) con fuego
    que brilla y lenos, y chimenea. Origen al centro de la base. Alto ~4,6."""
    p = P(nombre, col)
    lad = bpy.data.materials.get("CT_Ladrillo")
    if lad is None:
        lad = bpy.data.materials.new("CT_Ladrillo"); lad.use_nodes = True
        nt = lad.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        tc, br = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Color1"].default_value = (0.55, 0.18, 0.09, 1); br.inputs["Color2"].default_value = (0.65, 0.25, 0.12, 1)
        br.inputs["Mortar"].default_value = (0.85, 0.78, 0.66, 1); br.inputs["Scale"].default_value = 2.2
        br.inputs["Mortar Size"].default_value = 0.025
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = 0.85
    neg = mat("CT_BocaHorno", "#140c08", 0.9)
    r = ancho / 2
    p.caja((0, 0, 0.8), (ancho, ancho, 1.6), lad)                                       # base
    p.esfera((0, 0, 1.6), r * 0.95, lad, esc=(1, 1, 0.85), segs=24)                     # cupula
    bm_abajo = [v for v in p.bm.verts if v.co.z < 1.59 and v.co.z > 1.0 and v.co.length < r * 1.2]
    _arco(p, (0, -r * 0.92, 1.7), 0.75, lad, grosor=0.16, k=10)                          # arco de la boca
    p.caja((0, -r * 0.93, 2.1), (1.4, 0.1, 1.0), neg)                                    # boca oscura
    p.esfera((0, -r * 0.93, 2.55), 0.7, neg, esc=(1, 0.12, 0.6), segs=14)
    p.caja((0, -r * 1.02, 1.62), (1.9, 0.5, 0.12), lad)                                  # repisa de la boca
    p.cono((r * 0.4, r * 0.3, 3.0), 0.32, 0.28, 2.6, mat("CT_Chimenea", "#4a4a50", 0.4), segs=12)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015)
    if fuego:                                                                         # fuego y lenos adentro
        q = P(nombre + "_Fuego", col)
        len_ = mat("CT_Leno", "#5a3a20", 0.8)
        for k in range(3):
            q.cono((-0.35 + k * 0.35, -r * 0.8, 1.78), 0.09, 0.09, 0.9, len_, segs=8, rot=('Y', 90))
        for k, (dx, h, c) in enumerate(((-0.25, 0.6, "#ff5a1f"), (0.1, 0.8, "#ff8a1f"), (0.3, 0.5, "#ffc93a"), (0.0, 0.45, "#fff0a0"))):
            q.cono((dx, -r * 0.82, 1.8), 0.18 - 0.02 * k, 0.0, h, mat("CT_Llama_" + c.lstrip("#"), c, 0.3, emit=6.0), segs=8)
        fo = q.fin(); fo.parent = o; fo.visible_shadow = False
        ld = bpy.data.lights.new(nombre + "_Luz", 'POINT'); ld.energy = 260; ld.color = (1.0, 0.55, 0.2); ld.shadow_soft_size = 0.4
        lo = bpy.data.objects.new(nombre + "_Luz", ld); col.objects.link(lo); lo.parent = o; lo.location = (0, -r * 1.2, 2.1)
    return o


def costal_harina(nombre, col, tam=1.0):
    """COSTAL DE HARINA de manta con la palabra HARINA y un poco de harina regada. Origen en la base."""
    p = P(nombre, col)
    m = _mat_tela("CT_CostalHarina", "#efe6d2", relieve=0.5)
    p.caja((0, 0, 0.55), (0.9, 0.55, 1.1), m)
    p.esfera((0, 0, 1.1), 0.46, m, esc=(1, 0.62, 0.35), segs=14)
    p.esfera((0, 0, 0.05), 0.5, m, esc=(1, 0.65, 0.15), segs=14)
    blanco = mat("CT_Harina", "#fbf8f0", 0.95)
    for k in range(5):
        p.esfera((-0.5 + k * 0.25, -0.5, 0.01), 0.12, blanco, esc=(1.4, 1, 0.12), segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01)
    t = _texto3d(nombre + "_Texto", col, "HARINA", 0.16, "#3a6fb0", fuente="ariblk.ttf")
    t.parent = o; t.location = (0, -0.29, 0.65)
    o.scale = (tam,) * 3
    return o


def mesa_panadero(nombre, col, largo=4.0, fondo=1.8):
    """MESA DE TRABAJO de panadero: tablon con harina regada, una bola de masa y un rodillo. Origen al centro de la base;
    alto ~1,9."""
    p = P(nombre, col)
    mad, mad2 = mat("CT_MesaPan", "#c99a63", 0.7), mat("CT_MesaPan2", "#8a5a32", 0.75)
    p.caja((0, 0, 1.8), (largo, fondo, 0.16), mad)
    for x in (-largo / 2 + 0.2, largo / 2 - 0.2):
        for y in (-fondo / 2 + 0.2, fondo / 2 - 0.2):
            p.caja((x, y, 0.9), (0.16, 0.16, 1.8), mad2)
    p.caja((0, 0, 0.5), (largo - 0.4, fondo - 0.4, 0.08), mad2)                         # repisa de abajo
    blanco = mat("CT_Harina", "#fbf8f0", 0.95)
    rnd = __import__("random").Random(6)
    for _ in range(9):
        p.esfera((rnd.uniform(-largo / 2 + 0.3, largo / 2 - 0.3), rnd.uniform(-fondo / 2 + 0.2, fondo / 2 - 0.2), 1.89),
                 rnd.uniform(0.1, 0.25), blanco, esc=(1.5, 1, 0.08), segs=10)
    p.esfera((-0.6, 0.1, 2.05), 0.35, mat("CT_Masa", "#f2dfb8", 0.8), esc=(1.2, 1, 0.6), segs=16)
    p.cono((0.9, -0.1, 2.0), 0.11, 0.11, 1.2, mad, segs=12, rot=('Y', 90))              # rodillo
    for s in (-1, 1):
        p.cono((0.9 + s * 0.6 + (0 if s > 0 else -0.25), -0.1, 2.0), 0.05, 0.05, 0.25, mad2, segs=8, rot=('Y', 90))
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.012)
    return o


# ----------------------------------------------------------------- galletas, rayos X y efectos (EP007)
def galleta(p, c, tam=1.0, ang=0.0):
    """agrega a P una GALLETA con chispas de chocolate, de pie y mirando a -Y (para la mano o un plato)."""
    x, y, z = c
    m, ch = mat("CT_Galleta", "#d9a25a", 0.7), mat("CT_Chispa_Choco", "#4a2a18", 0.6)
    r = 0.3 * tam
    p.cono((x, y + 0.03 * tam, z), r, r, 0.07 * tam, m, segs=18, rot=('X', 90))
    rnd = __import__("random").Random(int(x * 10 + z * 7) % 97)
    for _ in range(6):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, r * 0.75)
        p.esfera((x + rr * math.cos(a), y - 0.05 * tam, z + rr * math.sin(a)), 0.04 * tam, ch, esc=(1, 0.5, 1), segs=6)
    return p


def frasco_galletas(nombre, col, tam=1.0, llenas=True):
    """FRASCO DE GALLETAS de vidrio panzon con tapa de bolita y etiqueta "GALLETAS"; galletas apiladas adentro.
    Origen en la base; frente -Y. Alto ~1,2 * tam."""
    p = P(nombre, col)
    vid, tp = _mat_vidrio(), mat("CT_TapaGalletas", "#e85d75", 0.5)
    n = 20
    perfil = [(0.0, 0.3), (0.05, 0.38), (0.5, 0.42), (0.85, 0.38), (0.92, 0.3)]
    p.loft([(z, [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]) for z, r in perfil], vid,
           tapa_abajo=True, tapa_arriba=False)
    p.cono((0, 0, 0.92), 0.33, 0.33, 0.08, tp, segs=n)
    p.esfera((0, 0, 1.06), 0.3, tp, esc=(1, 1, 0.35), segs=n)
    p.esfera((0, 0, 1.2), 0.08, tp, segs=10)
    p.caja((0, -0.425, 0.5), (0.52, 0.02, 0.22), mat("CT_EtiquetaGalletas", "#fff3d6", 0.8, emit=0.25))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.01)
    if llenas:
        q = P(nombre + "_Galletas", col)
        m = mat("CT_Galleta", "#d9a25a", 0.7)
        for k in range(7):                                                          # galletas acostadas, apiladas
            a = k * 1.3
            q.cono((0.12 * math.cos(a), 0.12 * math.sin(a), 0.06 + k * 0.11), 0.26, 0.26, 0.07, m, segs=16, rot=('X', 8 * math.sin(a)))
        go = q.fin(); go.parent = o
    t = _texto3d(nombre + "_Texto", col, "GALLETAS", 0.09, "#7a2e1a", fuente="ariblk.ttf")
    t.parent = o; t.location = (0, -0.44, 0.5)
    o.scale = (tam,) * 3
    return o


def _mat_aura(color, fuerza=2.5):
    """material de AURA: transparente en el centro y brillante en la orilla (como un contorno de luz)."""
    nombre = "CT_Aura_" + color.lstrip("#")
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = mat(nombre, color, 0.5, emit=fuerza)
    nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 0.55
    nt.links.new(lw.outputs["Facing"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], bs.inputs["Alpha"])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True
    return m


def aura_poder(rig, col, color="#5ad1ff", nombre=None, chispas=True):
    """AURA DE PODER alrededor del personaje: capsula de luz que brilla en la ORILLA (el centro es transparente: no tapa
    la cara) y destellos que suben. Pegada al rig (se mueve con el). Mide al personaje. Devuelve el objeto del aura."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Aura"
    bpy.context.view_layer.update()
    Mi = rig.matrix_world.inverted()
    ps = [Mi @ (o.matrix_world @ Vector(b)) for o in rig.children_recursive if o.type == 'MESH' and not o.hide_render
          for b in o.bound_box]
    mn = Vector((min(q.x for q in ps), min(q.y for q in ps), min(q.z for q in ps)))
    mx = Vector((max(q.x for q in ps), max(q.y for q in ps), max(q.z for q in ps)))
    c = (mn + mx) / 2; d = mx - mn
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    p.esfera(tuple(c), 0.5, _mat_aura(color), esc=(d.x * 1.35, max(d.y, d.x * 0.6) * 1.35, d.z * 1.15), segs=24)
    o = p.fin(); o.visible_shadow = False
    for pl in o.data.polygons:
        pl.use_smooth = True
    W = o.matrix_world.copy(); o.parent = rig; o.matrix_parent_inverse = rig.matrix_world.inverted() @ Matrix.Identity(4)
    o.matrix_world = W
    if chispas:
        rnd = __import__("random").Random(len(nombre))
        pts = [tuple(rig.matrix_world @ (c + Vector((rnd.uniform(-0.6, 0.6) * d.x, -0.55 * max(d.y, 0.6),
                                                     rnd.uniform(-0.45, 0.5) * d.z)))) for _ in range(8)]
        de = destellos(nombre + "_Destellos", col, pts, tam=0.16 * d.z / 5, colores=("#ffffff", color), fuerza=6.0)
        W = de.matrix_world.copy(); de.parent = rig; de.matrix_parent_inverse = rig.matrix_world.inverted(); de.matrix_world = W
    return o


def lucecita(nombre, col, color="#ff5a5a", tam=1.0, estela=1.6):
    """LUCECITA de poder (el "¡fiu!"): bolita brillante con nucleo blanco, halo y una ESTELA que se adelgaza hacia
    atras (+Y local: la lucecita viaja hacia -Y). Para que se vea volar de regreso a su dueno. Origen en la bolita."""
    p = P(nombre, col)
    p.esfera((0, 0, 0), 0.22, mat("CT_Poder_" + color.lstrip("#"), color, 0.3, emit=7.0), segs=14)
    p.esfera((0, -0.05, 0.03), 0.1, mat("CT_NucleoLucecita", "#ffffff", 0.3, emit=10.0), segs=10)
    p.esfera((0, 0, 0), 0.45, _mat_halo(color, 3.0, 0.25), segs=16)
    pts = [(0.06 * math.sin(i * 1.1), 0.25 + i * estela / 6, 0.05 * math.cos(i * 1.3)) for i in range(7)]
    _tubo_var(p, pts, [0.16 * (1 - i / 7) + 0.01 for i in range(7)], _mat_halo(color, 3.0, 0.35), segs=10)
    chis = mat("CT_Chispa", "#ffffff", 0.2, emit=8.0)
    for i in range(5):
        p.ico((0.18 * math.sin(i * 2.3), 0.4 + i * 0.3, 0.15 * math.cos(i * 1.7)), 0.03, chis, sub=1)
    o = p.fin(); o.visible_shadow = False
    for pl in o.data.polygons:
        pl.use_smooth = True
    o.scale = (tam,) * 3
    return o


def vidrios_rotos(nombre, col, n=18, radio=1.2, semilla=5):
    """VIDRIOS ROTOS de caricatura: triangulitos de vidrio (con orilla clara que brilla) regados en el piso alrededor,
    y unas chispas. Origen al centro, en el piso."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    vid, ori = _mat_vidrio("CT_VidrioRoto", "#cfefff", 0.5), mat("CT_OrillaVidrio", "#ffffff", 0.2, emit=1.5)
    for _ in range(n):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(0.15, radio)
        x, y = rr * math.cos(a), rr * math.sin(a)
        s = rnd.uniform(0.08, 0.2)
        r0 = rnd.uniform(0, 6.28)
        tri = [(x + s * math.cos(r0 + k * 2.1 + rnd.uniform(-0.3, 0.3)), y + s * math.sin(r0 + k * 2.1)) for k in range(3)]
        vs = [p.bm.verts.new(p.M @ Vector((tx, ty, 0.02 + rnd.uniform(0, 0.02)))) for tx, ty in tri]
        p.bm.faces.new(vs).material_index = p._i(vid)
        p.caja(((tri[0][0] + tri[1][0]) / 2, (tri[0][1] + tri[1][1]) / 2, 0.03), (s * 0.9, 0.01, 0.01), ori,
               rot=('Z', math.degrees(math.atan2(tri[1][1] - tri[0][1], tri[1][0] - tri[0][0]))))
    o = p.fin(); o.visible_shadow = False
    return o


def ventana_rayosx(nombre, col, radio=1.4, color="#7fe6ff"):
    """VENTANA DE RAYOS X en una pared (el poder de mama): circulo de luz celeste con orilla punteada y, adentro, la
    silueta brillante de alguien escondido (cabeza, cuerpo y una galleta en la mano). Mirando a -Y; origen al centro."""
    p = P(nombre, col)
    fondo = _mat_halo(color, 1.2, 0.35)
    p.cono((0, 0.01, 0), radio, radio, 0.02, fondo, segs=40, rot=('X', 90))
    ori = mat("CT_OrillaRayosX", "#e8fbff", 0.3, emit=4.0)
    for k in range(24):                                                               # orilla punteada
        a = 2 * math.pi * k / 24
        p.caja((radio * math.cos(a), -0.01, radio * math.sin(a)), (0.16, 0.02, 0.06), ori, rot=('Y', -math.degrees(a) + 90))
    sil = mat("CT_SiluetaRayosX", "#ffffff", 0.3, emit=3.0)
    p.cono((0, -0.02, 0.45), 0.32, 0.32, 0.02, sil, segs=20, rot=('X', 90))           # cabeza
    p.caja((0, -0.02, -0.25), (0.6, 0.02, 0.85), sil)                                  # cuerpo
    p.caja((0.42, -0.02, -0.05), (0.18, 0.02, 0.5), sil, rot=('Y', -35))               # brazo con galleta
    p.cono((0.62, -0.03, 0.18), 0.14, 0.14, 0.02, mat("CT_GalletaRayosX", "#ffd27a", 0.3, emit=3.0), segs=14, rot=('X', 90))
    o = p.fin(); o.visible_shadow = False
    return o


def marco_recuerdo(cam, col, nombre=None, distancia=0.5):
    """MARCO DE RECUERDO pegado a la camara: orilla de nubes blancas y vineta calida (texturas/marco_recuerdo.png)
    para las escenas del pasado. Se pone frente a la camara llenando el cuadro 9:16. Devuelve el plano."""
    nombre = nombre or cam.name + "_Recuerdo"
    png = os.path.join(_TEX, "marco_recuerdo.png")
    m = bpy.data.materials.get("CT_MarcoRecuerdo")
    if m is None:
        m = bpy.data.materials.new("CT_MarcoRecuerdo"); m.use_nodes = True
        nt = m.node_tree
        for n_ in list(nt.nodes):
            nt.nodes.remove(n_)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(png, check_existing=True)
        em, tr, mx = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(im.outputs["Color"], em.inputs["Color"])
        nt.links.new(im.outputs["Alpha"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            m.blend_method = 'BLEND'
    cd = cam.data
    h, w = 1.0, 9 / 16                                            # plano de alto 1; el tamano real lo da un driver
    me = bpy.data.meshes.new(nombre)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(); uv = me.uv_layers[0].data
    for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv[i].uv = (u, v)
    me.materials.append(m)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    o.parent = cam; o.location = (0, 0, -distancia); o.visible_shadow = False
    # llena SIEMPRE el cuadro aunque cambie el lente: alto = distancia * sensor / lente (en 9:16 el sensor va al alto).
    # Con sensor_fit VERTICAL (camaras de los episodios) el alto lo da sensor_height; con AUTO, sensor_width (EP007).
    sensor = "sensor_height" if cd.sensor_fit == 'VERTICAL' else "sensor_width"
    for i in (0, 1):
        fc = o.driver_add("scale", i); dv = fc.driver; dv.type = 'SCRIPTED'
        for nm, path in (("l", "lens"), ("s", sensor)):
            v = dv.variables.new(); v.name = nm; v.type = 'SINGLE_PROP'
            v.targets[0].id_type = 'CAMERA'; v.targets[0].id = cd; v.targets[0].data_path = path
        dv.expression = "%.4f * s / l * 1.03" % distancia
    return o


def letrero_espalda(rig, col, texto="NORMALITO", nombre=None, color="#fff6c8"):
    """LETRERO DE PAPEL pegado con cinta en la ESPALDA (la broma de la escuela): hoja crema con letras grandes que
    caben en el papel y dos tiras de cinta. Pegado a UpperTorso, del lado +Y (la espalda)."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_LetreroEspalda"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    cx, W, H = (um.x + uM.x) / 2, uM.x - um.x, uM.z - um.z
    yb = uM.y + 0.03
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    aw, ah = W * 0.86, H * 0.5
    zc = um.z + H * 0.55
    p.caja((cx, yb, zc), (aw, 0.02, ah), mat("CT_PapelEspalda_" + color.lstrip("#"), color, 0.8, emit=0.15), rot=('Y', 3))
    cin = _mat_vidrio("CT_Cinta", "#e8e2c8", 0.55)
    for s in (-1, 1):
        p.caja((cx + s * aw * 0.38, yb + 0.012, zc + ah * 0.48), (aw * 0.26, 0.012, ah * 0.14), cin, rot=('Y', s * 25))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    _pegar_hueso(o, rig, "UpperTorso")
    t = _texto3d(nombre + "_Texto", col, texto, ah * 0.4, "#c0262f", fuente="ariblk.ttf")
    t.parent = o; t.matrix_parent_inverse = o.matrix_world.inverted()
    t.matrix_world = rig.matrix_world @ Matrix.Translation((cx, yb + 0.02, zc)) @ Matrix.Rotation(math.radians(90), 4, 'X') \
        @ Matrix.Rotation(math.radians(180), 4, 'Y')                         # se lee desde atras (mirando a +Y)
    _texto_en_caja(t, aw * 0.88, ah * 0.7)
    return o


def lineas_velocidad(nombre, col, n=14, largo=3.5, radio=1.6, semilla=2):
    """LINEAS DE VELOCIDAD de caricatura (para volar): rayas blancas delgadas y algo transparentes alrededor de un
    eje que va hacia +Y local (detras de lo que se mueve hacia -Y). Origen al centro; ponerlas detras del personaje."""
    rnd = __import__("random").Random(semilla)
    m = _mat_halo("#ffffff", 1.5, 0.45)
    p = P(nombre, col)
    for _ in range(n):
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(radio * 0.5, radio)
        L = largo * rnd.uniform(0.5, 1.0)
        p.caja((rr * math.cos(a), L / 2 + rnd.uniform(0, 0.8), rr * math.sin(a)), (0.04, L, 0.04), m)
    o = p.fin(); o.visible_shadow = False
    return o


def ropa_tirada(nombre, col, semilla=4):
    """ROPA TIRADA en el piso (cuando la vecina se cae con todo y ropa): playeras, calcetin y toalla acostados, de
    colores, y unas pinzas. Origen al centro, en el piso."""
    rnd = __import__("random").Random(semilla)
    p = P(nombre, col)
    colores = ("#e23b3b", "#3d7fd9", "#f2c230", "#5bbf6a", "#ff8ad8", "#ffffff")
    for k in range(7):
        c = colores[k % len(colores)]
        m = _mat_tela("CT_Prenda_" + c.lstrip("#"), c, relieve=0.3)
        x, y, a = rnd.uniform(-2.0, 2.0), rnd.uniform(-1.2, 1.2), rnd.uniform(0, 180)
        if k % 3 == 0:
            p.caja((x, y, 0.03), (0.9, 1.1, 0.05), m, rot=('Z', a)); p.caja((x, y, 0.05), (1.4, 0.4, 0.05), m, rot=('Z', a))
        elif k % 3 == 1:
            p.caja((x, y, 0.03), (0.22, 0.7, 0.05), m, rot=('Z', a))
        else:
            p.caja((x, y, 0.03), (1.0, 1.5, 0.05), m, rot=('Z', a))
    for k in range(4):
        cp = ("#e23b3b", "#3d7fd9", "#f2c230")[k % 3]
        p.caja((rnd.uniform(-2, 2), rnd.uniform(-1.3, 1.3), 0.04), (0.06, 0.22, 0.06), mat("CT_Pinza_" + cp.lstrip("#"), cp, 0.4),
               rot=('Z', rnd.uniform(0, 180)))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.008)
    return o


def numero_concursante(rig, col, numero="7", nombre=None, color="#ffffff"):
    """NUMERO DE CONCURSANTE (dorsal) en el pecho: papel blanco con borde y el numero grande, pegado a UpperTorso."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Numero"
    _, um, uM = _caja_hueso(rig, "UpperTorso")
    cx, W, H = (um.x + uM.x) / 2, uM.x - um.x, uM.z - um.z
    yf = _frente_torso(rig, cx, W, um.z, uM.z) - 0.03
    p = P(nombre, col); p.M = rig.matrix_world.copy()
    aw, ah, zc = W * 0.6, H * 0.42, um.z + H * 0.5
    p.caja((cx, yf, zc), (aw + 0.06, 0.02, ah + 0.06), mat("CT_BordeNumero", "#d12b2b", 0.6))
    p.caja((cx, yf - 0.012, zc), (aw, 0.02, ah), mat("CT_PapelNumero_" + color.lstrip("#"), color, 0.7))
    o = _acabado(p.fin(), bisel=0)
    _pegar_hueso(o, rig, "UpperTorso")
    t = _texto3d(nombre + "_Texto", col, str(numero), ah * 0.7, "#1a1a1a", fuente="ariblk.ttf")
    t.parent = o; t.matrix_parent_inverse = o.matrix_world.inverted()
    t.matrix_world = rig.matrix_world @ Matrix.Translation((cx, yf - 0.03, zc)) @ Matrix.Rotation(math.radians(90), 4, 'X')
    _texto_en_caja(t, aw * 0.85, ah * 0.8)
    return o


def separar_helice(rig, col, nombre=None, disco=True):
    """SEPARA LA HELICE del gorro de Sikelpa (viene pegada en una sola malla, lecciones EP007) para que GIRE: busca de
    arriba hacia abajo el corte donde termina el palito/aspas (rebanadas con vertices junto al eje) y empieza la
    copa del gorro (un aro sin centro). La helice queda como objeto aparte <Nombre>_Helice, con su ORIGEN EN EL EJE,
    pegada al hueso Head; gira en su Z local. disco: hijo <Nombre>_HeliceDisco (disco transparente con rayitas de
    giro, escondido; lo prende girar_helice). Trabaja SOLO en el archivo del episodio (no toca el .blend del
    personaje). Si ya existe, la devuelve. Hacerlo con el rig en reposo."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Helice"
    if bpy.data.objects.get(nombre):
        return bpy.data.objects[nombre]
    bpy.context.view_layer.update()
    cab, pelos = _cabeza_y_pelo(rig)
    if not pelos:
        return None
    gorro = max(pelos, key=lambda o: len(o.data.vertices))
    Mi = rig.matrix_world.inverted()
    A = Mi @ gorro.matrix_world
    pts = [A @ v.co for v in gorro.data.vertices]
    zmax = max(q.z for q in pts)
    arriba = [q for q in pts if q.z > zmax - 0.3]
    cx = sum(q.x for q in arriba) / len(arriba); cy = sum(q.y for q in arriba) / len(arriba)
    corte, paso, z, palito = None, 0.0125, zmax, False
    while z > zmax - 0.9:                         # 1) bajar hasta el palito (vertices junto al eje); 2) seguir hasta
        s = [q for q in pts if z - paso < q.z <= z]   # la copa del gorro (un aro sin centro): ahi va el corte
        if s:
            rmin = min(math.hypot(q.x - cx, q.y - cy) for q in s)
            if rmin < 0.08:
                palito = True
            elif palito and rmin > 0.25:
                corte = z
                break
        z -= paso
    if corte is None:
        return None
    piv = Vector((cx, cy, corte))
    me_h = gorro.data.copy(); me_h.name = nombre
    bm = bmesh.new(); bm.from_mesh(me_h)
    for v in bm.verts:
        v.co = (A @ v.co) - piv
    quitar = [f for f in bm.faces if any(v.co.z <= 0.002 for v in f.verts)]
    bmesh.ops.delete(bm, geom=quitar, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me_h); bm.free()
    if gorro.data.users > 1:
        gorro.data = gorro.data.copy()
    bm = bmesh.new(); bm.from_mesh(gorro.data)                               # quitarle la helice al gorro
    quitar = [f for f in bm.faces if all((A @ v.co).z > corte + 0.002 for v in f.verts)]
    bmesh.ops.delete(bm, geom=quitar, context='FACES')
    bm.to_mesh(gorro.data); bm.free()
    # eje propio (vacio) pegado a la cabeza con los ejes del rig: asi la helice gira sobre SU eje (Z local), no sobre
    # los ejes del hueso (si se pega directo al hueso, rotation_euler.z gira chueco)
    eje = bpy.data.objects.new(nombre + "_Eje", None); col.objects.link(eje); eje.empty_display_size = 0.3
    eje.matrix_world = rig.matrix_world @ Matrix.Translation(piv)
    _pegar_hueso(eje, rig, "Head")
    o = bpy.data.objects.new(nombre, me_h); col.objects.link(o)
    o.parent = eje; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = Matrix.Identity(4)
    o["ct_accesorio"] = True
    if disco:
        rmax = max(math.hypot(v.co.x, v.co.y) for v in me_h.vertices)
        zc = sum(v.co.z for v in me_h.vertices) / len(me_h.vertices)
        q = P(nombre + "Disco", col)
        dm = _mat_halo("#ffffff", 1.0, 0.28)
        q.cono((0, 0, zc - 0.01), rmax * 1.05, rmax * 1.05, 0.02, dm, segs=32)
        rm = mat("CT_RayitaGiro", "#ffffff", 0.3, emit=2.0)
        for k in range(3):                                                    # rayitas de giro (arcos)
            a0 = k * 2 * math.pi / 3
            for j in range(6):
                a = a0 + j * 0.12
                rr = rmax * 1.12
                q.caja((rr * math.cos(a), rr * math.sin(a), zc), (0.03, 0.12, 0.02), rm, rot=('Z', math.degrees(a)))
        do = q.fin(); do.parent = o; do.visible_shadow = False
        do.hide_render = True; do.hide_viewport = True
    return o


def girar_helice(helice, f0, f1, vueltas_seg=5.0, fps=30, disco=True):
    """pone a GIRAR la helice de f0 a f1 (llaves LINEALES en su rotacion Z) y prende el disco de giro en ese tramo."""
    rz0 = helice.rotation_euler.z
    helice.rotation_euler.z = rz0; helice.keyframe_insert("rotation_euler", index=2, frame=f0)
    helice.rotation_euler.z = rz0 + 2 * math.pi * vueltas_seg * (f1 - f0) / fps
    helice.keyframe_insert("rotation_euler", index=2, frame=f1)
    ad = helice.animation_data
    for fc in _curvas(helice):
        if fc.data_path == "rotation_euler":
            for k in fc.keyframe_points:
                if f0 <= k.co.x <= f1:
                    k.interpolation = 'LINEAR'
    d = bpy.data.objects.get(helice.name + "Disco")
    if disco and d:
        for f, v in ((f0 - 1, True), (f0, False), (f1, False), (f1 + 1, True)):
            d.hide_render = v; d.keyframe_insert("hide_render", frame=f)
        for fc in _curvas(d):
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'
    return helice


def _curvas(o):
    """las curvas de animacion de un objeto (Blender 5: acciones por capas)."""
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        return list(act.fcurves)
    except Exception:
        out = []
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    out += list(cb.fcurves)
        return out


def _pegar_como(o, pieza):
    """pega 'o' al mismo hueso que 'pieza' con la MISMA relacion (o se queda donde esta ahora). Lo marca como accesorio."""
    bpy.context.view_layer.update()
    W, Wp = o.matrix_world.copy(), pieza.matrix_world.copy()
    o.parent = pieza.parent; o.parent_type = pieza.parent_type; o.parent_bone = pieza.parent_bone
    o.matrix_parent_inverse = pieza.matrix_parent_inverse.copy()
    o.matrix_basis = pieza.matrix_basis @ Wp.inverted() @ W
    o["ct_accesorio"] = True


def _cabeza_y_pelo(rig):
    """(pieza de la cabeza, [cabello y accesorios de la cabeza]) del rig."""
    hijos = [c for c in rig.children_recursive if c.type == 'MESH' and c.parent_type == 'BONE' and c.parent_bone == "Head"
             and not c.get("ct_accesorio")]
    cab = bpy.data.objects.get(rig.name.replace("_Rig", "") + "_Head")
    if cab not in hijos:
        cab = next((c for c in hijos if c.name.endswith("_Head")), None) or _pieza_hueso(rig, "Head")
    return cab, [c for c in hijos if c is not cab]


def _vs_rig(o, Mi):
    dg = bpy.context.evaluated_depsgraph_get()
    oe = o.evaluated_get(dg)
    return [Mi @ (oe.matrix_world @ v.co) for v in oe.data.vertices]


def sombrero_copa(rig, col, color="#1b1b20", cinta=("#1f8a4c", "#f4f4f4", "#d12b2b"), alto=0.8, meter_pelo=True, nombre=None):
    """sombrero de copa (de presidente de caricatura) con cinta de tres franjas, pegado al hueso Head.
    Se mide en los ejes del rig (leccion 86). meter_pelo: el cabello que sale arriba del ala se mete dentro de la copa
    (copia la malla del cabello: el original no se toca). Hacerlo con el rig en reposo. Devuelve el objeto."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Sombrero"
    bpy.context.view_layer.update()
    M = rig.matrix_world.copy(); Mi = M.inverted()
    cab, pelos = _cabeza_y_pelo(rig)
    H = _vs_rig(cab, Mi)
    x0, x1 = min(v.x for v in H), max(v.x for v in H)
    y0, y1 = min(v.y for v in H), max(v.y for v in H)
    z0, z1 = min(v.z for v in H), max(v.z for v in H)
    cx, cy, w, hh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, z1 - z0
    r = 0.47 * w                                               # copa (abajo); arriba se abre un poco
    zb = z0 + 0.86 * hh                                        # el sombrero entra un poquito en la cabeza
    hc = alto * hh
    abre = 0.07

    def r_en(z):
        return r * (1 + abre * max(0.0, min(1.0, (z - zb) / hc)))

    if meter_pelo:
        for pe in pelos:
            orig = bpy.data.meshes.get(pe.get("ct_pelo_original", ""))
            if orig is not None:
                pe.data = orig
            pe["ct_pelo_original"] = pe.data.name
            pe.data = pe.data.copy()
            Mo = pe.matrix_world.copy(); A = Mi @ Mo; Ai = A.inverted()
            for v in pe.data.vertices:
                q = A @ v.co
                if q.z <= zb - 0.01:
                    continue
                d = Vector((q.x - cx, q.y - cy)); lim = 0.93 * r_en(q.z)
                if d.length > lim:
                    d = d.normalized() * lim
                q = Vector((cx + d.x, cy + d.y, min(q.z, zb + hc - 0.04)))
                v.co = Ai @ q
            pe.data.update()
    p = P(nombre, col)
    p.M = M
    neg = mat("CT_Sombrero_" + color.lstrip("#"), color, 0.45)
    ms = [mat("CT_Banda_" + c.lstrip("#"), c, 0.55) for c in cinta]
    rb = r * 1.6                                               # ala
    p.cono((cx, cy, zb - 0.03), rb, rb * 0.96, 0.055, neg, segs=32)
    p.cono((cx, cy, zb), r, r * (1 + abre), hc, neg, segs=32)
    bh = 0.05 * hh                                             # cinta: roja abajo, blanca, verde arriba
    for k, m in enumerate(reversed(ms)):
        z = zb + 0.025 + k * bh
        p.cono((cx, cy, z), r_en(z) + 0.012, r_en(z + bh) + 0.012, bh, m, segs=32)
    o = _acabado(p.fin(), angulo=40, bisel=0.008)
    _pegar_como(o, cab)
    return o


def bigote(rig, col, color="#3a2414", alto=0.50, ancho=0.62, grosor=0.9, nombre=None):
    """bigote de caricatura de UNA pieza lisa (no bolitas): un tubo curvo, gordito al centro, que se adelgaza y sube
    en las puntas, pegado a la curva de la cara y suavizado (subdivision). Va al hueso Head. alto = altura en la
    cabeza (0 = barbilla, 1 = coronilla; 0,5 = bajo los ojos y la boca asoma por debajo), ancho = fraccion del ancho de
    la cabeza. Se mide en los ejes del rig. Hacerlo con el rig en reposo. Devuelve el objeto."""
    nombre = nombre or rig.name.replace("_Rig", "") + "_Bigote"
    bpy.context.view_layer.update()
    M = rig.matrix_world.copy(); Mi = M.inverted()
    cab, _ = _cabeza_y_pelo(rig)
    H = _vs_rig(cab, Mi)
    x0, x1 = min(v.x for v in H), max(v.x for v in H)
    y0 = min(v.y for v in H)
    z0, z1 = min(v.z for v in H), max(v.z for v in H)
    cx, w, hh = (x0 + x1) / 2, x1 - x0, z1 - z0
    zm = z0 + alto * hh
    franja = [v for v in H if abs(v.z - zm) < 0.12 * hh]

    def frente(x):                                            # y de la cara a esa x (el personaje mira a -Y)
        cerca = [v.y for v in franja if abs(v.x - x) < 0.07 * w]
        return min(cerca) if cerca else y0

    mitad = ancho * w / 2
    rmax = 0.07 * w * grosor
    N, K = 41, 14                                             # puntos a lo largo y alrededor
    centros, radios = [], []
    for i in range(N):
        s = -1 + 2 * i / (N - 1)                              # -1 punta derecha ... 0 centro ... 1 punta izquierda
        a = abs(s)
        x = cx + s * mitad
        z = zm - 0.05 * w * math.sin(math.pi * 0.85 * a) + 0.10 * w * a ** 4 + 0.012 * w * (1 - a) ** 6
        r = rmax * (1 - 0.72 * a ** 1.6)                     # gordito al centro, delgadito en las puntas
        centros.append(Vector((x, 0, z))); radios.append(r)
    for i, c in enumerate(centros):
        c.y = frente(c.x) - radios[i] * 0.3
    bm = bmesh.new()
    anillos = []
    for i, c in enumerate(centros):
        tg = (centros[min(i + 1, N - 1)] - centros[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)); up = (up - tg * up.dot(tg)).normalized()
        fr = tg.cross(up).normalized()                        # hacia la cara / hacia afuera
        r = radios[i]
        anillos.append([bm.verts.new(M @ (c + up * math.sin(2 * math.pi * k / K) * r * 0.78
                                             + fr * math.cos(2 * math.pi * k / K) * r * 0.5)) for k in range(K)])
    for i in range(N - 1):
        A, B = anillos[i], anillos[i + 1]
        for k in range(K):
            bm.faces.new((A[k], A[(k + 1) % K], B[(k + 1) % K], B[k]))
    for i, sig in ((0, -1), (N - 1, 1)):                      # puntas cerradas y redondas
        tg = (centros[i] - centros[i - sig]).normalized()
        punta = bm.verts.new(M @ (centros[i] + tg * radios[i] * 0.9))
        A = anillos[i]
        for k in range(K):
            bm.faces.new((A[k], A[(k + 1) % K], punta) if sig > 0 else (A[(k + 1) % K], A[k], punta))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    me.materials.append(mat("CT_Bigote_" + color.lstrip("#"), color, 0.8))
    for pl in me.polygons:
        pl.use_smooth = True
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    sub = o.modifiers.new("Liso", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    _pegar_como(o, cab)
    return o
