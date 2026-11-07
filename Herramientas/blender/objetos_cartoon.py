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
    """borde negro de caricatura (casco invertido)."""
    negro = mat("CT_Contorno", "#111111", 0.9, cull=True)
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
