# EFECTOS (VFX) CARICATURA para los momentos clave: rapidos (< 1 s), visibles y sin tapar la cara de quien habla.
# Todo se anima con llaves (no hay simulacion que hornear): sirve igual en vista previa y en el render final.
# Uso dentro de Blender (script de episodio):
#   import vfx
#   vfx.migas("Migas_T03", col, (x, y, z), f0)                 # al romper la galleta: migajas que saltan y caen
#   vfx.migas_mordida("Migas_T05", col, borde, f_mordida, f_mastica)  # al MORDER: migas que caen de la boca (2 tandas)
#   vfx.fuego_caricatura("Fuego_T09", col, (x, y, z), f0, f1, ancho, alto, camara)  # muro de llamas planas (+ humo_negro)
#   vfx.fuego_vivo("Fuego_T04", col, (x, y, z), f0, f1, tam)   # fuego con volumen que SI parece fuego (de cerca, en manos)
#   vfx.brillitos("Brillo_T03", col, (x, y, z), f0)            # destellos de 4 puntas que aparecen y se apagan
#   vfx.corazones("Cora_T40", col, (x, y, z), f0, n=5)         # corazones de linea delgada que suben (romance)
#   vfx.confeti("Confeti_T44", col, (x, y, z), f0)             # papelitos de colores que caen girando
# Cada funcion devuelve un vacio padre (se puede mover o emparentar a una mano). Los que miran a camara usan la camara
# activa de la escena (o la que se pase en camara=). Duracion corta para que no estorbe el encuadre.
# Reglas: pocos y con sentido; nunca delante de la cara de quien esta en foco mas de un instante (ver docs/05).
import bpy, bmesh, math, random
from mathutils import Vector
T2 = 2 * math.pi


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(h):
    h = h.lstrip("#")
    return tuple(_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


def _mat(nombre, color, emit=0.0, rough=0.6):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        sal = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); nt.links.new(bs.outputs["BSDF"], sal.inputs["Surface"])
    c = _rgb(color)
    bs.inputs["Base Color"].default_value = (*c, 1); bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = (*c, 1); bs.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*c, 1)
    return m


def _raiz(nombre, col, pos):
    r = bpy.data.objects.new(nombre, None); col.objects.link(r)
    r.location = pos; r.empty_display_size = 0.3
    return r


def _mirar_camara(o, camara):
    cam = camara or bpy.context.scene.camera
    if cam:
        c = o.constraints.new('TRACK_TO'); c.target = cam; c.track_axis = 'TRACK_Z'; c.up_axis = 'UP_Y'


def _visible(o, f_on, f_off):
    """aparece en f_on y desaparece en f_off (sin mezclas raras)."""
    for f, v in ((f_on - 1, True), (f_on, False), (f_off, False), (f_off + 1, True)):
        o.hide_render = v; o.hide_viewport = v
        o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)


def _constante(o):
    ad = o.animation_data
    ac = ad.action if ad else None
    for fc in (getattr(ac, "fcurves", None) or []):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'


# ------------------------------------------------------------------ migas
def migas(nombre, col, pos, f0, n=16, color="#d9a256", tam=1.0, piso=None, semilla=3):
    """migajas de galleta: saltan hacia los lados y arriba, giran, caen con gravedad y se apagan (~0,8 s).
    piso: z donde rebotan/se quedan (por defecto 3 unidades abajo)."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    m = _mat("VFX_Miga", color, 0.0, 0.8)
    m2 = _mat("VFX_Miga_Clara", "#efc27e", 0.0, 0.8)
    z_piso = (piso if piso is not None else pos[2] - 3.0) - pos[2]
    g = -38.0 * tam
    for i in range(n):
        me = bpy.data.meshes.new("%s_%02d" % (nombre, i))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        for v in bm.verts:                                   # pedacito irregular
            v.co.x *= rnd.uniform(0.6, 1.3); v.co.y *= rnd.uniform(0.5, 1.1); v.co.z *= rnd.uniform(0.4, 0.9)
        bm.to_mesh(me); bm.free()
        me.materials.append(m if i % 3 else m2)
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = raiz
        s0 = rnd.uniform(0.035, 0.085) * tam
        ang = rnd.uniform(0, 2 * math.pi)
        v = Vector((math.cos(ang) * rnd.uniform(2.0, 4.5), math.sin(ang) * rnd.uniform(0.6, 2.2) - 0.8,
                    rnd.uniform(3.0, 6.5))) * tam
        rot_v = Vector((rnd.uniform(-14, 14), rnd.uniform(-14, 14), rnd.uniform(-14, 14)))
        vida = rnd.randint(20, 28)
        fps = bpy.context.scene.render.fps or 30
        for k in range(0, vida + 1, 2):
            t = k / fps
            p = Vector((v.x * t, v.y * t, v.z * t + 0.5 * g * t * t))
            if p.z < z_piso:
                p.z = z_piso
            o.location = p; o.rotation_euler = tuple(rot_v * t)
            o.scale = [s0 * (1.0 if k < vida - 6 else max(0.0, (vida - k) / 6))] * 3
            o.keyframe_insert("location", frame=f0 + k); o.keyframe_insert("rotation_euler", frame=f0 + k)
            o.keyframe_insert("scale", frame=f0 + k)
        _visible(o, f0, f0 + vida); _constante(o)
    return raiz


def migas_mordida(nombre, col, punto, f_mordida, f_mastica=None, n=60, n_mastica=30, tam=1.0, color="#e3a75a",
                  hacia=(0, -1, 0), semilla=5):
    """MORDER algo que suelta migas (galleta, pan, empanada): migas que CAEN del borde mordido (poco hacia los lados),
    una tanda al morder y otra chiquita en la primera masticada (cuenta "mordio y mastica").
    Sistema de particulas (instancias de una miga): probado en la prueba C (2026-11-08): mismo costo de render que
    las migas con llaves y da IGUAL al renderizar por tramos (render_paralelo / rehacer_tramo), sin hornear.
    punto: borde mordido en el mundo en f_mordida (la cara en ese cuadro: que las migas no suban a los ojos).
    hacia: hacia donde salen (afuera de la boca, normalmente hacia la camara-abajo)."""
    rnd = random.Random(semilla)
    me = bpy.data.meshes.new(nombre + "_Proto")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts:
        v.co.x *= rnd.uniform(0.6, 1.3); v.co.y *= rnd.uniform(0.5, 1.1); v.co.z *= rnd.uniform(0.4, 0.9)
    bm.to_mesh(me); bm.free()
    me.materials.append(_mat("VFX_Miga_Mordida", color, 0.0, 0.8))
    proto = bpy.data.objects.new(nombre + "_Proto", me); col.objects.link(proto)
    proto.location = (0, 0, -500)                      # la miga modelo, fuera de cuadro
    tandas = [(nombre + "_Mordida", f_mordida - 1, f_mordida + 2, n)]
    if f_mastica:
        tandas.append((nombre + "_Mastica", f_mastica - 1, f_mastica + 2, n_mastica))
    raiz = _raiz(nombre, col, punto)
    d = Vector(hacia).normalized()
    for nom, f0, f1, k in tandas:
        mg = bpy.data.meshes.new(nom); bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=0.08 * tam)
        bm.to_mesh(mg); bm.free()
        em = bpy.data.objects.new(nom, mg); col.objects.link(em)
        em.parent = raiz
        em.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()     # la normal del emisor = "hacia"
        ps = em.modifiers.new("Particulas", 'PARTICLE_SYSTEM').particle_system
        st = ps.settings
        st.count = k; st.frame_start = f0; st.frame_end = f1; st.lifetime = 22; st.lifetime_random = 0.3
        st.emit_from = 'FACE'; st.normal_factor = 0.9 * tam; st.factor_random = 1.3 * tam
        st.render_type = 'OBJECT'; st.instance_object = proto
        st.particle_size = 0.045 * tam; st.size_random = 0.6
        st.use_rotations = True; st.rotation_mode = 'NONE'; st.rotation_factor_random = 1.0
        st.angular_velocity_mode = 'RAND'; st.angular_velocity_factor = 6.0
        st.effector_weights.gravity = 3.0
        em.show_instancer_for_render = False; em.show_instancer_for_viewport = False
        ps.seed = semilla
    return raiz


# ------------------------------------------------------------------ fuego y humo de caricatura
def _carta_llama(nombre, col, ancho, alto, dientes, semilla, material):
    rnd = random.Random(semilla)
    me = bpy.data.meshes.new(nombre); bm = bmesh.new()
    pts = [(-ancho / 2, 0.0)]
    for i in range(dientes):
        x0 = -ancho / 2 + ancho * i / dientes
        x1 = -ancho / 2 + ancho * (i + 1) / dientes
        pico = alto * rnd.uniform(0.62, 1.0)
        valle = alto * rnd.uniform(0.28, 0.45)
        xm = (x0 + x1) / 2 + rnd.uniform(-0.15, 0.15) * (x1 - x0)
        if i > 0:
            pts.append((x0, valle))
        pts.append((xm, pico))
    pts.append((ancho / 2, alto * 0.3)); pts.append((ancho / 2, 0.0))
    vs = [bm.verts.new((x, 0, z)) for x, z in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    me.materials.append(material)
    return o


def fuego_caricatura(nombre, col, pos, f0, f1, ancho=3.0, alto=2.6, camara=None, semilla=1, borde=True):
    """FUEGO de caricatura (como Custerk): muro de llamas planas en 3 capas (rojo, naranja, amarillo) x 3 dibujos que se
    turnan cada 4 cuadros (~8 por segundo) y miran a la camara. Sin simulacion: mismo costo que sin fuego (prueba E,
    2026-11-08: 0,149 vs 0,153 s/cuadro con humo y luz). Funciona mejor GRANDE y DETRAS del personaje (en 9:16 no cabe
    al lado) y con fondo que contraste (contra paredes naranjas se pierde)."""
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.location = pos
    if camara:
        c = raiz.constraints.new('LOCKED_TRACK'); c.target = camara
        c.track_axis = 'TRACK_NEGATIVE_Y'; c.lock_axis = 'LOCK_Z'
    capas = (("#e8361a", 1.00, 1.00, 0.00, 0.9), ("#ff8a1c", 0.80, 0.76, -0.04, 1.0), ("#ffd23a", 0.52, 0.50, -0.08, 1.1))
    if borde:       # capa de atras rojo oscuro un poco mas grande: hace de contorno y separa el fuego de fondos claros
        capas = (("#7a1208", 1.10, 1.08, 0.04, 0.35),) + capas
    rnd = random.Random(semilla)
    for k, (colr, sa, sh, dy, emi) in enumerate(capas):
        m = _mat("VFX_Llama_%d" % k, colr, emi, 0.9)
        for d in range(3):
            o = _carta_llama("%s_c%d_d%d" % (nombre, k, d), col, ancho * sa, alto * sh, max(4, round(ancho * sa / 0.45)) - k,
                              semilla * 31 + k * 7 + d, m)        # ~1 diente cada 0,45 (con 6 fijos un fuego grande se veia en bloques)
            o.parent = raiz; o.location = (rnd.uniform(-0.08, 0.08), dy, 0)
            for f in range(f0 - 1, f1 + 2):
                vis = ((f - f0) // 4) % 3 == d and f0 <= f <= f1          # cambia de dibujo cada 4 cuadros (~8/s)
                o.hide_render = not vis; o.hide_viewport = not vis
                o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
            # un respiro de tamano (crece y baja poquito)
            for f in range(f0, f1 + 1, 3):
                s = 1.0 + 0.06 * math.sin(f * 0.9 + k * 2 + d)
                o.scale = (1, 1, s); o.keyframe_insert("scale", frame=f)
    return raiz


def humo_negro(nombre, col, pos, ancho, f0, f1, cada=4, vida=36, semilla=3):
    """humo negro de caricatura que sube y crece desde arriba del fuego (bolas suaves, sin simulacion)."""
    rnd = random.Random(semilla)
    m = _mat("VFX_Humo_Negro", "#33333a", 0.0, 1.0)
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz); raiz.location = pos
    i = 0
    for fn in range(f0, f1, cada):
        me = bpy.data.meshes.new("%s_%02d" % (nombre, i)); bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            v.co *= rnd.uniform(0.85, 1.1)
        bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(m)
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = raiz
        x0 = rnd.uniform(-ancho / 2, ancho / 2)
        for k in range(0, vida + 1, 2):
            t = k / vida
            o.location = (x0 + 0.6 * math.sin(t * 3 + i), rnd.uniform(-0.1, 0.1), 0.3 + 4.5 * t)
            s = (0.35 + 1.1 * t) * (1.0 if t < 0.75 else max(0.0, (1 - t) / 0.25))
            o.scale = (s, s, s * 0.85)
            o.keyframe_insert("location", frame=fn + k); o.keyframe_insert("scale", frame=fn + k)
        for f, h in ((fn - 1, True), (fn, False), (fn + vida, False), (fn + vida + 1, True)):
            o.hide_render = h; o.hide_viewport = h
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
        i += 1
    return raiz



# ------------------------------------------------------------------ lineas de impacto
def lineas_impacto(nombre, col, pos, f0, n=10, radio=1.0, largo=1.6, color="#ffffff", camara=None, semilla=9, dur=5):
    """"¡PUM!" de caricatura (como Custerk TYDW2fNQYYU 45,2 s): rayas gruesas que salen del punto del golpe, miran a la
    camara, aparecen en f0 (el cuadro del contacto), crecen hacia afuera y se van en ~dur cuadros. Dejan un hueco en el
    centro (radio) para no tapar lo que golpea."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    _mirar_camara(raiz, camara)
    m = _mat("VFX_Impacto", color, 2.0, 0.5)
    for i in range(n):
        an = 2 * math.pi * i / n + rnd.uniform(-0.18, 0.18)
        l = largo * rnd.uniform(0.7, 1.15)
        w = 0.10 * largo * rnd.uniform(0.8, 1.2)
        me = bpy.data.meshes.new("%s_%02d" % (nombre, i)); bm = bmesh.new()
        d = Vector((math.cos(an), math.sin(an), 0)); nrm = Vector((-d.y, d.x, 0))
        a0 = d * radio
        vs = [bm.verts.new(a0 + nrm * w * 0.5), bm.verts.new(a0 - nrm * w * 0.5), bm.verts.new(a0 + d * l)]
        bm.faces.new(vs); bm.to_mesh(me); bm.free()
        me.materials.append(m)
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = raiz
        for k, (s, desp) in enumerate(((0.45, 0.0), (1.0, 0.25), (0.55, 0.55), (0.0, 0.8))):   # sale y se encoge (no flota)
            f = f0 + int(round(k * dur / 3))
            o.scale = (s, s, s); o.location = d * desp * radio
            o.keyframe_insert("scale", frame=f); o.keyframe_insert("location", frame=f)
        _visible(o, f0, f0 + dur); _constante(o)
    return raiz


# ------------------------------------------------------------------ brillitos
def _estrella(nombre, r=1.0, puntas=4, agudo=0.28):
    me = bpy.data.meshes.new(nombre)
    vs = [(0, 0, 0)]
    for i in range(puntas * 2):
        a = math.pi / 2 + math.pi * i / puntas
        rr = r if i % 2 == 0 else r * agudo
        vs.append((rr * math.cos(a), rr * math.sin(a), 0))
    fs = [(0, i, i % (puntas * 2) + 1) for i in range(1, puntas * 2 + 1)]
    me.from_pydata(vs, [], fs)
    return me


def brillitos(nombre, col, pos, f0, n=8, color="#fff3b0", radio=1.2, tam=1.0, camara=None, semilla=5, hueco=0.0):
    """destellos de 4 puntas alrededor de pos: aparecen con un pop, giran un poco y se apagan (8-14 cuadros cada uno).
    hueco: radio del centro que se deja libre (para no tapar un texto o una cara)."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    m = _mat("VFX_Brillo_" + color.lstrip("#"), color, 6.0, 0.3)
    for i in range(n):
        o = bpy.data.objects.new("%s_%02d" % (nombre, i), _estrella("%s_%02d" % (nombre, i))); col.objects.link(o)
        o.data.materials.append(m); o.parent = raiz
        a = rnd.uniform(0, 2 * math.pi); r = hueco + rnd.uniform(0.35, 1.0) * (radio - hueco) if hueco else rnd.uniform(0.35, 1.0) * radio
        o.location = (math.cos(a) * r, rnd.uniform(-0.2, 0.2), math.sin(a) * r * 0.8)
        _mirar_camara(o, camara)
        fi = f0 + rnd.randint(0, 9); dur = rnd.randint(8, 14); s = rnd.uniform(0.12, 0.26) * tam
        for k, esc in ((0, 0.0), (3, 1.15), (dur * 0.6, 0.85), (dur, 0.0)):
            o.scale = (s * esc, s * esc, s * esc); o.keyframe_insert("scale", frame=fi + int(k))
        o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", frame=fi)
        o.rotation_euler = (0, 0, math.radians(rnd.choice((-1, 1)) * 45)); o.keyframe_insert("rotation_euler", frame=fi + dur)
        _visible(o, fi, fi + dur); _constante(o)
    return raiz


# ------------------------------------------------------------------ corazones
def _curva_corazon(nombre, tam, grosor):
    cu = bpy.data.curves.new(nombre, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    N = 48
    pts = []
    for i in range(N):
        t = 2 * math.pi * i / N
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x / 17 * tam, y / 17 * tam, 0))
    sp.points.add(len(pts) - 1)
    for p, (x, y, z) in zip(sp.points, pts):
        p.co = (x, y, z, 1)
    sp.use_cyclic_u = True
    cu.bevel_depth = grosor; cu.bevel_resolution = 2
    return cu


def _contorno_corazon(n_arco=22):
    """CORAZON DE TODA LA VIDA (como el emoji): dos lobulos redondos y la punta abajo, con lineas rectas de los lobulos
    a la punta. Medidas: ~2 de ancho, ~1,9 de alto, centrado."""
    r, a, b, punta = 0.52, 0.44, 0.28, -0.98
    T = (0.0, punta)
    C = (-a, b)
    dx, dy = C[0] - T[0], C[1] - T[1]
    L = math.hypot(dx, dy)
    th = math.atan2(dy, dx) + math.asin(r / L)              # tangente por fuera del lobulo izquierdo
    lt = math.sqrt(L * L - r * r)
    P = (T[0] + lt * math.cos(th), T[1] + lt * math.sin(th))
    D = (0.0, b + math.sqrt(max(0.0, r * r - a * a)))       # la "V" de arriba, entre los dos lobulos
    psi_p = math.atan2(P[1] - C[1], P[0] - C[0])
    psi_d = math.atan2(D[1] - C[1], D[0] - C[0])
    if psi_p < psi_d:
        psi_p += 2 * math.pi
    izq = [(C[0] + r * math.cos(psi_p + (psi_d - psi_p) * k / n_arco), C[1] + r * math.sin(psi_p + (psi_d - psi_p) * k / n_arco))
           for k in range(n_arco + 1)]
    der = [(-x, y) for (x, y) in reversed(izq)]
    pts = [T] + izq + der[1:]
    cy = (max(y for _, y in pts) + min(y for _, y in pts)) / 2
    return [(x, y - cy) for x, y in pts]


def _mat_corazon(nombre, color, emit, rough):
    """material del corazon: color lleno (sin transparencia) que se DESVANECE solo al final, con la propiedad "alfa" de
    cada objeto (1 = lleno)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = _mat(nombre, color, emit, rough)
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'OBJECT'; at.attribute_name = "alfa"
    nt.links.new(at.outputs["Fac"], bs.inputs["Alpha"])
    m.surface_render_method = 'DITHERED'
    return m


def _corazon_solido(nombre, col, color, borde="#b0124f"):
    """corazon LLENO de forma clasica: rosa por dentro, sin hueco, con un poquito de grosor y orilla redondeada, orilla
    rosa oscuro detras y un brillito blanco en el lobulo izquierdo. Mira a +Z (se gira a la camara)."""
    contorno = _contorno_corazon()

    def curva(nom, esc, mat_, extr, bisel):
        cu = bpy.data.curves.new(nom, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
        cu.extrude = extr; cu.bevel_depth = bisel; cu.bevel_resolution = 3
        sp = cu.splines.new('POLY'); sp.points.add(len(contorno) - 1)
        for pt, (x, y) in zip(sp.points, contorno):
            pt.co = (x * esc, y * esc, 0, 1)
        sp.use_cyclic_u = True
        cu.materials.append(mat_)
        o = bpy.data.objects.new(nom, cu); col.objects.link(o)
        return o
    o = curva(nombre, 1.0, _mat_corazon("VFX_CorazonLleno_" + color.lstrip("#"), color, 0.45, 0.35), 0.05, 0.05)
    b = curva(nombre + "_Orilla", 1.1, _mat_corazon("VFX_CorazonOrilla_" + borde.lstrip("#"), borde, 0.2, 0.5), 0.03, 0.03)
    b.parent = o; b.location = (0, -0.01, -0.07)
    me = bpy.data.meshes.new(nombre + "_Brillo"); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=6, radius=1.0); bm.to_mesh(me); bm.free()
    me.materials.append(_mat_corazon("VFX_CorazonBrillo", "#ffffff", 1.2, 0.3))
    br = bpy.data.objects.new(me.name, me); col.objects.link(br); br.parent = o
    br.location = (-0.48, 0.38, 0.1); br.scale = (0.17, 0.09, 0.03); br.rotation_euler = (0, 0, 0.75)
    for x in (o, b, br):
        x.visible_shadow = False
        x["alfa"] = 1.0
    return o


def _alfa(o, valor, f):
    for x in [o] + list(o.children):
        x["alfa"] = valor
        x.keyframe_insert('["alfa"]', frame=f)


def corazones_emisor(nombre, col, f0, f1, objetivo=None, hueso=None, offset=(0.0, 0.0, 0.0), pos=None, cada=6,
                     tam=1.0, alto=3.2, ancho=1.0, vida=40, color="#ff3d7f", camara=None, semilla=7, detras=1.5):
    """CORAZONES QUE NACEN DEL PERSONAJE (como en los juegos; pedido del usuario 2026-11-11): de f0 a f1 sale uno cada
    'cada' cuadros desde el emisor (el hueso 'hueso' del rig 'objetivo', o el objeto 'objetivo', o el punto 'pos'),
    con un saltito al nacer, sube meciendose 'alto' unidades, late un poco y se DESVANECE arriba. Siguen naciendo de
    donde este el personaje en ese momento. offset = (x, y, z) del mundo desde el emisor.
    detras: los corazones nacen esa distancia DETRAS del personaje (del lado contrario a la camara) y suben por los
    lados y por arriba de su cabeza: nunca le tapan la cara (pedido del usuario 2026-11-11). 0 = enfrente, como antes."""
    rnd = random.Random(semilla)
    sc = bpy.context.scene
    f_antes = sc.frame_current
    cam = camara or sc.camera
    derecha = cam.matrix_world.to_3x3() @ Vector((1, 0, 0)) if cam else Vector((1, 0, 0))
    derecha.z = 0
    derecha = derecha.normalized() if derecha.length > 1e-6 else Vector((1, 0, 0))
    raiz = _raiz(nombre, col, (0, 0, 0))
    i = 0
    for t0 in range(f0, max(f0 + 1, f1), cada):
        if objetivo is not None:
            sc.frame_set(t0)
            if hueso:
                Mw = objetivo.matrix_world @ objetivo.pose.bones[hueso].matrix
            else:
                Mw = objetivo.matrix_world
            p0 = Mw.translation + Vector(offset)
        else:
            p0 = Vector(pos) + Vector(offset)
        if detras and cam is not None:
            atras = p0 - cam.matrix_world.translation
            atras.z = 0
            if atras.length > 1e-6:
                p0 = p0 + atras.normalized() * detras
        o = _corazon_solido("%s_%02d" % (nombre, i), col, color); i += 1
        o.parent = raiz
        _mirar_camara(o, cam)
        s = tam * rnd.uniform(0.7, 1.05)
        # se abren a un lado y al otro (alternando): no tapan la cara del personaje
        lado = (1 if i % 2 else -1) * rnd.uniform(0.55, 1.0) * ancho
        fase = rnd.uniform(0, 2 * math.pi)
        for k in range(0, vida + 1, 2):
            t = k / vida
            sube = alto * (1 - (1 - t) ** 1.6)                          # sale rapido y se frena arriba
            mece = 0.28 * tam * math.sin(fase + t * 7.0) * min(1.0, t * 3)
            o.location = p0 + derecha * (lado * t ** 0.6 + mece) + Vector((0, 0, sube))
            if t < 0.1:
                e = 1.25 * t / 0.1                                      # nace con un saltito
            elif t < 0.18:
                e = 1.25 - 0.25 * (t - 0.1) / 0.08
            else:
                e = 1.0 - 0.3 * max(0.0, t - 0.8) / 0.2                # se achica un poquito solo al final
            e *= 1.0 + 0.07 * math.sin(t * 22)                          # late
            o.scale = (s * e, s * e, s * e)
            o.keyframe_insert("location", frame=t0 + k); o.keyframe_insert("scale", frame=t0 + k)
        _alfa(o, 1.0, t0 + int(vida * 0.82)); _alfa(o, 0.0, t0 + vida)     # llenos casi todo el viaje
        _visible(o, t0, t0 + vida); _constante(o)
        for ch in o.children:
            _visible(ch, t0, t0 + vida); _constante(ch)
    sc.frame_set(f_antes)
    return raiz


def corazones(nombre, col, pos, f0, n=5, color="#ff4f8b", tam=1.0, ancho=1.6, camara=None, semilla=7, relleno=False,
              estilo="solido"):
    """corazones que salen con un pop, suben meciendose, laten y se desvanecen (~1 s).
    estilo "solido" (por defecto desde 2026-11-11): corazones de forma CLASICA y LLENOS, rosas por dentro, sin hueco
    (pedido del usuario), que se desvanecen al final. Para que NAZCAN DEL PERSONAJE una y otra vez: corazones_emisor. estilo "linea": el de antes (linea delgada con brillo; relleno=True le pone un
    relleno suave)."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    m = _mat("VFX_Corazon_" + color.lstrip("#"), color, 8.0, 0.3)
    nucleo = _mat("VFX_Corazon_Nucleo", "#ffffff", 4.0, 0.3)
    for i in range(n):
        s = rnd.uniform(0.32, 0.5) * tam
        if estilo == "solido":
            o = _corazon_solido("%s_%02d" % (nombre, i), col, color); o.parent = raiz
            _mirar_camara(o, camara)
            x0 = rnd.uniform(-ancho / 2, ancho / 2)
            fi = f0 + rnd.randint(0, 10); dur = rnd.randint(26, 34)
            fase = rnd.uniform(0, 2 * math.pi)
            for k in range(0, dur + 1, 3):
                t = k / dur
                o.location = (x0 + 0.25 * math.sin(fase + t * 5), 0, 1.8 * t)
                esc = min(1.0, t / 0.18) * (1.0 if t < 0.7 else max(0.0, (1 - t) / 0.3))
                esc *= 1.0 + 0.12 * math.sin(t * 18)
                o.scale = (s * esc, s * esc, s * esc)
                o.keyframe_insert("location", frame=fi + k); o.keyframe_insert("scale", frame=fi + k)
            _alfa(o, 1.0, fi + int(dur * 0.82)); _alfa(o, 0.0, fi + dur)
            _visible(o, fi, fi + dur); _constante(o)
            for ch in o.children:
                _visible(ch, fi, fi + dur); _constante(ch)
            continue
        cu = _curva_corazon("%s_%02d" % (nombre, i), 1.0, 0.045)
        cu.materials.append(m)
        o = bpy.data.objects.new(cu.name, cu); col.objects.link(o); o.parent = raiz
        lin = _curva_corazon(cu.name + "_Nucleo", 1.0, 0.018); lin.materials.append(nucleo)   # linea blanca adentro: resalta
        on = bpy.data.objects.new(lin.name, lin); col.objects.link(on); on.parent = o; on.location = (0, 0, 0.03)
        if relleno:
            me = bpy.data.meshes.new(cu.name + "_Relleno")
            bm = bmesh.new()
            N = 32
            vs = [bm.verts.new((16 * math.sin(2 * math.pi * k / N) ** 3 / 17, (13 * math.cos(2 * math.pi * k / N) - 5 * math.cos(4 * math.pi * k / N)
                                - 2 * math.cos(6 * math.pi * k / N) - math.cos(8 * math.pi * k / N)) / 17, -0.02)) for k in range(N)]
            bm.faces.new(vs); bm.to_mesh(me); bm.free()
            me.materials.append(_mat("VFX_Corazon_Relleno", color, 1.5, 0.5))
            orl = bpy.data.objects.new(me.name, me); col.objects.link(orl); orl.parent = o
        _mirar_camara(o, camara)
        x0 = rnd.uniform(-ancho / 2, ancho / 2)
        fi = f0 + rnd.randint(0, 10); dur = rnd.randint(26, 34)
        fase = rnd.uniform(0, 2 * math.pi)
        for k in range(0, dur + 1, 3):
            t = k / dur
            o.location = (x0 + 0.25 * math.sin(fase + t * 5), 0, 1.8 * t)
            esc = min(1.0, t / 0.18) * (1.0 if t < 0.7 else max(0.0, (1 - t) / 0.3))
            esc *= 1.0 + 0.12 * math.sin(t * 18)                              # late un poquito
            o.scale = (s * esc, s * esc, s * esc)
            o.keyframe_insert("location", frame=fi + k); o.keyframe_insert("scale", frame=fi + k)
        _visible(o, fi, fi + dur); _constante(o)
    return raiz


# ------------------------------------------------------------------ confeti
def confeti(nombre, col, pos, f0, n=40, area=(6, 3), alto=6.0, duracion=60, semilla=11,
            colores=("#ff4f5e", "#ffd23a", "#3a8dff", "#5ccf5c", "#ff7ac0", "#ffffff")):
    """papelitos de colores que caen desde 'alto' arriba de pos, girando y meciendose."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    mats = [_mat("VFX_Confeti_" + c.lstrip("#"), c, 0.8, 0.5) for c in colores]
    for i in range(n):
        me = bpy.data.meshes.new("%s_%02d" % (nombre, i))
        w, h = rnd.uniform(0.12, 0.2), rnd.uniform(0.06, 0.1)
        me.from_pydata([(-w, -h, 0), (w, -h, 0), (w, h, 0), (-w, h, 0)], [], [(0, 1, 2, 3)])
        me.materials.append(mats[i % len(mats)])
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = raiz
        x0, y0 = rnd.uniform(-area[0] / 2, area[0] / 2), rnd.uniform(-area[1] / 2, area[1] / 2)
        fi = f0 + rnd.randint(0, 12); vz = rnd.uniform(2.2, 3.4); fase = rnd.uniform(0, 6.3)
        giro = Vector((rnd.uniform(4, 9), rnd.uniform(4, 9), rnd.uniform(-3, 3)))
        fps = bpy.context.scene.render.fps or 30
        for k in range(0, duracion + 1, 3):
            t = k / fps
            o.location = (x0 + 0.35 * math.sin(fase + t * 4), y0 + 0.2 * math.cos(fase + t * 3), alto - vz * t)
            o.rotation_euler = tuple(giro * t)
            o.keyframe_insert("location", frame=fi + k); o.keyframe_insert("rotation_euler", frame=fi + k)
        _visible(o, fi, fi + duracion); _constante(o)
    return raiz


# ------------------------------------------------------------------ abrir la galleta (animacion + efectos)
def abrir_galleta(galleta_abierta, f0, col, camara=None, tam=1.0):
    """anima una galleta hecha con objetos_cartoon.galleta_fortuna(abierta=True): las dos mitades empiezan juntas y
    se separan con un ¡crac! en f0 (con un pequeno rebote), el papelito se estira, y salen migas y brillitos."""
    izq = bpy.data.objects.get(galleta_abierta.name + "_Izq")
    der = bpy.data.objects.get(galleta_abierta.name + "_Der")
    pap = bpy.data.objects.get(galleta_abierta.name + "_Papel")
    for h, lado in ((izq, -1), (der, 1)):
        if not h:
            continue
        x1, rz1 = h.location.x, h.rotation_euler.z
        for f, x, rz in ((f0 - 6, lado * 0.32, 0.0), (f0, lado * 0.34, 0.0), (f0 + 4, x1 * 1.12, rz1 * 1.2), (f0 + 9, x1, rz1)):
            h.location.x = x; h.rotation_euler.z = rz
            h.keyframe_insert("location", index=0, frame=f); h.keyframe_insert("rotation_euler", index=2, frame=f)
    if pap:
        for f, sx in ((f0 - 6, 0.25), (f0, 0.25), (f0 + 5, 1.06), (f0 + 9, 1.0)):
            pap.scale = (sx, 1, 1); pap.keyframe_insert("scale", frame=f)
    bpy.context.view_layer.update()
    w = galleta_abierta.matrix_world.translation.copy()
    s = galleta_abierta.matrix_world.to_scale().x
    migas(galleta_abierta.name + "_Migas", col, (w.x, w.y - 0.1, w.z + 0.4 * s), f0, n=18, tam=0.75 * s * tam)
    brillitos(galleta_abierta.name + "_Brillo", col, (w.x, w.y - 0.1, w.z + 0.45 * s), f0 + 2, n=7, radio=2.0 * s, tam=s,
              camara=camara, hueco=1.35 * s)                 # alrededor del papelito, sin tapar el texto


# ------------------------------------------------------------------ sonrojo (verguenza)
def _textura_sonrojo():
    """mejilla rosa difuminada con rayitas /// (PNG con transparencia, se hace una vez)."""
    import os
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vfx_texturas", "sonrojo.png")
    if not os.path.exists(ruta):
        raise FileNotFoundError("Falta %s: correr py Herramientas/blender/vfx_texturas/hacer_texturas.py" % ruta)
    return ruta


def sonrojo(nombre, col, cabeza, f0, f1, tam=1.0):
    """mejillas rosas con /// pegadas a la cara (siguen a la cabeza). cabeza = objeto malla de la cabeza del personaje
    (ej. "Crush_Head", "Sikelpa_Head"). Aparecen en f0 y se van en f1, en seco (sin animacion)."""
    me = cabeza.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    ancho, alto = max(xs) - min(xs), max(zs) - min(zs)
    cx, zf = (max(xs) + min(xs)) / 2, min(zs) + 0.27 * alto        # en las mejillas, sin tocar los ojos
    frente = min(ys) - 0.012
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz)
    raiz.parent = cabeza; raiz.matrix_parent_inverse.identity(); raiz.location = (0, 0, 0)
    m = bpy.data.materials.get("VFX_Sonrojo")
    if m is None:
        m = bpy.data.materials.new("VFX_Sonrojo"); m.use_nodes = True
        nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(_textura_sonrojo(), check_existing=True)
        tx.extension = 'CLIP'
        nt.links.new(tx.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.0
        nt.links.new(tx.outputs["Alpha"], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    w, h = 0.33 * ancho * tam, 0.19 * ancho * tam
    for lado in (-1, 1):
        x = cx + lado * 0.27 * ancho
        mm = bpy.data.meshes.new("%s_%d" % (nombre, lado))
        mm.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
        uvl = mm.uv_layers.new(); [setattr(uvl.data[i], "uv", uv) for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)])]
        if lado > 0:                                          # en espejo, como mejillas de verdad
            for i, uv in enumerate([(1, 0), (0, 0), (0, 1), (1, 1)]):
                uvl.data[i].uv = uv
        mm.materials.append(m)
        o = bpy.data.objects.new(mm.name, mm); col.objects.link(o); o.parent = raiz
        o.location = (x, frente - 0.004 * abs(x - cx), zf)
        o.rotation_euler = (0, 0, math.radians(-lado * 16))   # sigue la curva de la cara
        o.visible_shadow = False
    # aparece y se va EN SECO (como una expresion de la cara): nada de crecer ni moverse (pedido del usuario: con la
    # animacion de llegada se veia bajar de la nada y caerse al irse)
    for o in raiz.children:
        for f, oculto in ((f0 - 1, True), (f0, False), (f1, True)):
            if f < 0:
                continue
            o.hide_render = oculto; o.hide_viewport = oculto
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
    return raiz


# ------------------------------------------------------------------ cambio de cuerpo (EP005: "si te sientas en el lugar de otro")
def cambio_cuerpo(nombre, col, cabeza_a, cabeza_b, f0, dur=18, colores=("#7fd4ff", "#ff8fc8"), alto=1.4, camara=None, tam=1.0):
    """dos ALMAS de luz salen de las cabezas, cruzan en arco (una por arriba, otra por abajo) y entran en la cabeza del
    otro, con estela de puntitos; al llegar, chispas en las dos cabezas. cabeza_a/b = puntos del mundo; f0 = cuando salen."""
    A, B = Vector(cabeza_a) + Vector((0, 0, 0.6)), Vector(cabeza_b) + Vector((0, 0, 0.6))
    raiz = _raiz(nombre, col, (0, 0, 0))
    for k, (p0, p1, c, signo) in enumerate(((A, B, colores[0], 1), (B, A, colores[1], -1))):
        m = _mat("VFX_Alma2_" + c.lstrip("#"), c, 2.6, 0.3)          # color que se vea (no blanco quemado)
        lado = (p1 - p0).cross(Vector((0, 0, 1)))
        lado = lado.normalized() * 0.35 * signo if lado.length > 1e-4 else Vector()
        for j in range(9):                                   # la bola y su estela (8 puntitos que la siguen)
            r = (0.34 if j == 0 else 0.22 * (1 - j / 9)) * tam
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=r)
            o = bpy.context.object; o.name = "%s_%d_%d" % (nombre, k, j)
            for cc in o.users_collection:
                cc.objects.unlink(o)
            col.objects.link(o); o.parent = raiz; o.data.materials.append(m)
            for pl in o.data.polygons:
                pl.use_smooth = True
            retraso = j * 1.5
            for fr in range(f0, f0 + dur + 8):
                u = (fr - f0 - retraso) / dur
                if u < 0:
                    u = 0.0
                u = min(1.0, u)
                e = u * u * (3 - 2 * u)
                pos = p0.lerp(p1, e) + Vector((0, 0, alto * signo * 0.5 + alto * 0.5)) * math.sin(math.pi * e) + lado * math.sin(math.pi * e)
                esc = (1.0 if 0 < u < 1 else 0.0) * (1 - 0.08 * j)
                o.location = pos; o.keyframe_insert("location", frame=fr)
                o.scale = (esc,) * 3; o.keyframe_insert("scale", frame=fr)
            _visible(o, f0, f0 + dur + 8); _constante(o)
    brillitos(nombre + "_LlegaA", col, tuple(B), f0 + dur - 2, n=8, color=colores[0], radio=1.0, camara=camara, tam=tam)
    brillitos(nombre + "_LlegaB", col, tuple(A), f0 + dur - 2, n=8, color=colores[1], radio=1.0, camara=camara, tam=tam, semilla=8)
    brillitos(nombre + "_Sale", col, tuple((A + B) / 2 + Vector((0, 0, 0.8))), f0, n=6, color="#fff3b0", radio=1.4, camara=camara, tam=tam, semilla=11)
    return raiz


# ------------------------------------------------------------------ props con vida (gato de objetos_cartoon con cabeza_aparte=True)
def vida_gato(gato, fa, fb, mirar=None, inclina=0.0, parpadeos=True, semilla=3):
    """el gato RESPIRA (el cuerpo se infla un poquito), mueve la cabeza (mira a 'mirar' = punto del mundo, con un
    vaiven lento) y PARPADEA cada 1,5-3 s. Usa los hijos <gato>_Cabeza y <gato>_Ojos (oc.gato(..., cabeza_aparte=True)).
    inclina: grados que ladea la cabeza (curiosidad). Una llave por cuadro en fa..fb."""
    import random
    from mathutils import Vector as _V
    rnd = random.Random(semilla)
    cab = next((c for c in gato.children if c.name.endswith("_Cabeza")), None)
    ojos = next((c for c in cab.children if c.name.endswith("_Ojos")), None) if cab else None
    esc0 = gato.scale.copy()
    parp = []
    f = fa + rnd.randint(10, 30)
    while f < fb:
        parp.append(f)
        f += rnd.randint(45, 90)
    for fr in range(fa, fb + 1):
        t = fr / 30.0
        r = 1.0 + 0.025 * math.sin(T2 * 0.45 * t + semilla)
        gato.scale = (esc0.x, esc0.y, esc0.z * r); gato.keyframe_insert("scale", frame=fr)
        if cab:
            giro = 0.0
            if mirar is not None:
                bpy.context.scene.frame_set(fr)
                p = gato.matrix_world.inverted() @ _V(mirar)
                giro = max(-1.0, min(1.0, math.atan2(-p.x, -p.y)))     # el frente del gato es -Y
            cab.rotation_euler = (math.radians(4 * math.sin(T2 * 0.21 * t)), 0,
                                  giro + math.radians(9 * math.sin(T2 * 0.13 * t + 1.0) + inclina * 0.0))
            cab.rotation_euler.y = math.radians(inclina)
            cab.keyframe_insert("rotation_euler", frame=fr)
        if ojos:
            cierra = any(0 <= fr - p0 <= 3 for p0 in parp)
            ojos.scale = (1, 1, 0.12 if cierra else 1.0); ojos.keyframe_insert("scale", frame=fr)
    return gato


def comer_con_tenedor(tenedor, cabeza, f0, f1, mordidas=2, comida=None, col=None, migas_en=None):
    """el TENEDOR (hijo del gato) sube a la boca y baja 'mordidas' veces entre f0 y f1; la cabeza se inclina al morder;
    la comida se achica en cada mordida y caen migas. Llaves por cuadro."""
    base_l, base_r = tenedor.location.copy(), tenedor.rotation_euler.copy()
    boca_l = base_l + Vector((-0.24, -0.12, 0.28))
    cab_r = cabeza.rotation_euler.copy() if cabeza else None
    ciclo = max(12, (f1 - f0) // max(1, mordidas))
    esc_com = comida.scale.copy() if comida else None
    for fr in range(f0, f1 + 1):
        k = (fr - f0) % ciclo
        n = (fr - f0) // ciclo
        u = math.sin(math.pi * min(1.0, k / (ciclo * 0.6))) if n < mordidas else 0.0
        tenedor.location = base_l.lerp(boca_l, u)
        tenedor.rotation_euler = (base_r.x + math.radians(-35) * u, base_r.y + math.radians(18) * u, base_r.z)
        tenedor.keyframe_insert("location", frame=fr); tenedor.keyframe_insert("rotation_euler", frame=fr)
        if cabeza:
            cabeza.rotation_euler.x = math.radians(10) * u + math.radians(3 * math.sin(T2 * fr / 14))   # mastica
            cabeza.keyframe_insert("rotation_euler", index=0, frame=fr)
        if comida is not None:
            s_ = 1.0 - 0.28 * min(n + (1 if k > ciclo * 0.5 else 0), mordidas)
            comida.scale = esc_com * max(0.3, s_); comida.keyframe_insert("scale", frame=fr)
        if migas_en and col and n < mordidas and k == int(ciclo * 0.5):
            migas("EP5_MigasGato_%d" % n, col, tuple(migas_en), fr, n=10, tam=0.55, piso=migas_en[2] - 0.9, semilla=n + 4)


# ------------------------------------------------------------------ EP006: chapoteo, lagrimas y agua dorada
def chapoteo(nombre, col, pos, f0, n=26, tam=1.0, color="#d9f3ff", radio=1.0, semilla=13):
    """CHAPOTEO de caricatura (cuando algo cae, se hunde o sale del agua): gotas que saltan en corona hacia arriba y
    afuera, caen con gravedad hasta el agua y se apagan, mas un aro que se abre en la superficie (~0,8 s).
    pos = punto en la superficie del agua (las gotas no bajan de ahi)."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    m = _mat("VFX_Gota", color, 0.5, 0.15)
    fps = bpy.context.scene.render.fps or 30
    g = -34.0 * tam
    for i in range(n):
        me = bpy.data.meshes.new("%s_%02d" % (nombre, i))
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(me); bm.free()
        for pl in me.polygons:
            pl.use_smooth = True
        me.materials.append(m)
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); o.parent = raiz
        a = 2 * math.pi * i / n + rnd.uniform(-0.25, 0.25)
        r0 = radio * rnd.uniform(0.25, 0.9) * tam
        vr, vz = rnd.uniform(1.4, 3.4) * tam, rnd.uniform(5.0, 9.5) * tam
        s0 = rnd.uniform(0.07, 0.15) * tam
        vida = int(2 * vz / -g * fps) + 1
        for k in range(0, vida + 2, 2):
            t = k / fps
            z = vz * t + 0.5 * g * t * t
            o.location = (math.cos(a) * (r0 + vr * t), math.sin(a) * (r0 + vr * t), max(0.0, z))
            o.scale = (s0, s0, s0 * (1.6 if k < vida * 0.4 else 1.0)) if z > 0 or k == 0 else (0.0, 0.0, 0.0)
            o.keyframe_insert("location", frame=f0 + k); o.keyframe_insert("scale", frame=f0 + k)
        _visible(o, f0, f0 + vida + 2); _constante(o)
    # aro en la superficie
    me = bpy.data.meshes.new(nombre + "_Aro")
    bm = bmesh.new()
    seg = 32
    vi = [bm.verts.new((0.8 * math.cos(2 * math.pi * k / seg), 0.8 * math.sin(2 * math.pi * k / seg), 0)) for k in range(seg)]
    vo = [bm.verts.new((1.0 * math.cos(2 * math.pi * k / seg), 1.0 * math.sin(2 * math.pi * k / seg), 0)) for k in range(seg)]
    for k in range(seg):
        j = (k + 1) % seg
        bm.faces.new((vi[k], vo[k], vo[j], vi[j]))
    bm.to_mesh(me); bm.free()
    me.materials.append(_mat("VFX_Aro_Agua", "#ffffff", 0.6, 0.2))
    aro = bpy.data.objects.new(me.name, me); col.objects.link(aro); aro.parent = raiz; aro.location = (0, 0, 0.03)
    for k, s in ((0, 0.4), (8, 1.6), (16, 2.6), (22, 3.0)):
        aro.scale = (s * radio * tam, s * radio * tam, 1)
        aro.keyframe_insert("scale", frame=f0 + k)
    _visible(aro, f0, f0 + 22); _constante(aro)
    return raiz


def lagrimas(nombre, col, cabeza, f0, f1, cada=9, tam=1.0, color="#7fd0ff"):
    """LAGRIMAS que salen de los dos ojos, bajan por la cara y caen (siguen a la cabeza). cabeza = malla de la cabeza
    del personaje (ej. "Alex2641590_Head"). Una gota por ojo cada 'cada' cuadros entre f0 y f1."""
    me = cabeza.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    ancho, alto = max(xs) - min(xs), max(zs) - min(zs)
    cx, frente = (max(xs) + min(xs)) / 2, min(ys) - 0.015
    z_ojo, z_barba = min(zs) + 0.5 * alto, min(zs) + 0.1 * alto
    raiz = bpy.data.objects.new(nombre, None); col.objects.link(raiz)
    raiz.parent = cabeza; raiz.matrix_parent_inverse.identity(); raiz.location = (0, 0, 0)
    m = _mat("VFX_Lagrima", color, 0.8, 0.1)
    s = 0.055 * ancho * tam
    i = 0
    for t0 in range(f0, max(f0 + 1, f1 - 14), cada):
        for lado in (-1, 1):
            mm = bpy.data.meshes.new("%s_%02d" % (nombre, i)); i += 1
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
            for v in bm.verts:                                     # gota: punta arriba
                if v.co.z > 0:
                    v.co.x *= (1 - v.co.z * 0.7); v.co.y *= (1 - v.co.z * 0.7); v.co.z *= 1.5
            bm.to_mesh(mm); bm.free(); mm.materials.append(m)
            o = bpy.data.objects.new(mm.name, mm); col.objects.link(o); o.parent = raiz
            o.visible_shadow = False
            x = cx + lado * 0.22 * ancho
            for k, (zz, dy, sc_) in ((0, (z_ojo, 0.0, 0.6)), (10, (z_barba, 0.0, 1.0)), (16, (z_barba - 0.35 * alto, -0.1 * ancho, 0.0))):
                o.location = (x + lado * 0.03 * ancho * k / 16, frente + dy, zz)
                o.scale = (s * sc_, s * sc_ * 0.6, s * sc_)
                o.keyframe_insert("location", frame=t0 + k); o.keyframe_insert("scale", frame=t0 + k)
            _visible(o, t0, t0 + 16); _constante(o)
    return raiz


def dorar_materiales(nombres, tramos, color="#ffbf2e", fuerza=1.3, rampa=6, cuanto=0.55):
    """AGUA DORADA (o cualquier material): en cada tramo [(f0, f1), ...] el material se vuelve dorado y brillante, con
    subida y bajada de 'rampa' cuadros. Mete una mezcla con emision dorada en cada material (solo en el archivo
    abierto: el mapa no cambia). Se puede volver a llamar: rehace las llaves."""
    hechos = []
    for nm in nombres:
        m = bpy.data.materials.get(nm)
        if not m or not m.use_nodes:
            continue
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        mx = nt.nodes.get("VFX_Dorado_Mix")
        if mx is None:
            src = out.inputs["Surface"].links[0].from_socket
            em = nt.nodes.new("ShaderNodeEmission"); em.name = "VFX_Dorado_Em"
            em.inputs["Color"].default_value = (*_rgb(color), 1); em.inputs["Strength"].default_value = fuerza
            mx = nt.nodes.new("ShaderNodeMixShader"); mx.name = "VFX_Dorado_Mix"
            nt.links.new(src, mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
        fac = mx.inputs[0]
        ad = nt.animation_data
        if ad and ad.action:                                   # Blender 5: las curvas viven en capas/tiras/channelbags
            for lay in ad.action.layers:
                for st in lay.strips:
                    for cb in st.channelbags:
                        for fc in [c for c in cb.fcurves if "VFX_Dorado_Mix" in c.data_path]:
                            cb.fcurves.remove(fc)
        fac.default_value = 0.0; fac.keyframe_insert("default_value", frame=0)
        for f0, f1 in tramos:
            for f, v in ((f0 - rampa, 0.0), (f0, cuanto), (f1, cuanto), (f1 + rampa, 0.0)):
                fac.default_value = v; fac.keyframe_insert("default_value", frame=f)
        hechos.append(nm)
    return hechos


# ------------------------------------------------------------------ fuego "de verdad" (EP007: "que el fuego SI parezca fuego")
def _mat_fuego(nombre="VFX_FuegoVivo_v2", fuerza=1.4):
    """(con Standard un brillo > ~1,5 lo quema a blanco: el naranja y el rojo se pierden)
    llama con volumen: color por ALTURA (blanco-amarillo abajo -> naranja -> rojo arriba) movido por un ruido que SUBE
    con el tiempo (driver de frame), orilla y punta transparentes (se deshace), sin sombra. La malla mide 1 de alto en
    su Z local (el tamano lo da la escala del objeto)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        N.remove(n)
    out = N.new("ShaderNodeOutputMaterial")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (2.2, 2.2, 1.3)
    fc = mp.inputs["Location"].driver_add("default_value", 2)
    fc.driver.type = 'SCRIPTED'; fc.driver.expression = "-frame * 0.07"         # el ruido sube: la llama "corre" hacia arriba
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.6; nz.inputs["Detail"].default_value = 3.0
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    sx = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sx.inputs["Vector"])
    m1 = N.new("ShaderNodeMath"); m1.operation = 'SUBTRACT'; m1.inputs[1].default_value = 0.5
    L.new(nz.outputs["Fac"], m1.inputs[0])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY_ADD'; m2.inputs[1].default_value = 0.55
    L.new(m1.outputs[0], m2.inputs[0]); L.new(sx.outputs["Z"], m2.inputs[2])           # altura + ruido
    ramp = N.new("ShaderNodeValToRGB"); L.new(m2.outputs[0], ramp.inputs["Fac"])
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (1.0, 0.93, 0.62, 1)
    el[1].position, el[1].color = 0.97, (0.3, 0.02, 0.0, 1)
    for p_, c_ in ((0.12, (1.0, 0.76, 0.16, 1)), (0.3, (1.0, 0.42, 0.03, 1)), (0.55, (0.9, 0.15, 0.01, 1)), (0.82, (0.55, 0.05, 0.0, 1))):
        e = el.new(p_); e.color = c_
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = fuerza
    L.new(ramp.outputs["Color"], em.inputs["Color"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    a1 = N.new("ShaderNodeMath"); a1.operation = 'SUBTRACT'; a1.inputs[0].default_value = 1.0
    L.new(lw.outputs["Facing"], a1.inputs[1])                                           # 1 en el centro, 0 en la orilla
    a2 = N.new("ShaderNodeMath"); a2.operation = 'SUBTRACT'; a2.inputs[0].default_value = 1.08
    L.new(m2.outputs[0], a2.inputs[1])                                                  # se deshace hacia la punta
    a3 = N.new("ShaderNodeMath"); a3.operation = 'MULTIPLY'; L.new(a1.outputs[0], a3.inputs[0]); L.new(a2.outputs[0], a3.inputs[1])
    a4 = N.new("ShaderNodeMath"); a4.operation = 'MULTIPLY'; a4.inputs[1].default_value = 2.6; a4.use_clamp = True
    L.new(a3.outputs[0], a4.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); L.new(a4.outputs[0], mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True
    m.diffuse_color = (1.0, 0.5, 0.05, 1)
    return m


def _lengua_fuego(nombre, col, semilla, mat):
    """una LENGUA de fuego: gota que se adelgaza hasta una punta curva (1 de alto, origen en la base)."""
    rnd = random.Random(semilla)
    me = bpy.data.meshes.new(nombre); bm = bmesh.new()
    seg, an = 14, 14
    ph, amp = rnd.uniform(0, T2), rnd.uniform(0.04, 0.09)
    anillos = []
    for i in range(1, seg):
        t = i / seg
        r = 0.5 * (t / 0.2) ** 0.55 if t < 0.2 else 0.5 * ((1 - t) / 0.8) ** 1.25
        cx = amp * math.sin(t * 5.5 + ph) * t * 1.6                                     # la punta se curva
        cy = amp * 0.6 * math.cos(t * 4.0 + ph) * t
        anillos.append([bm.verts.new((cx + r * math.cos(T2 * k / an), cy + r * math.sin(T2 * k / an), t)) for k in range(an)])
    abajo, arriba = bm.verts.new((0, 0, 0)), bm.verts.new((anillos[-1][0].co.x * 0.6, 0, 1.0))
    for k in range(an):
        j = (k + 1) % an
        bm.faces.new((abajo, anillos[0][j], anillos[0][k]))
        bm.faces.new((anillos[-1][k], anillos[-1][j], arriba))
        for a, b in zip(anillos[:-1], anillos[1:]):
            bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.normal_update(); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o); o.visible_shadow = False
    return o


def fuego_vivo(nombre, col, pos, f0, f1, tam=1.0, semilla=1, chispas=True, luz=True, fuerza=1.4):
    """FUEGO que si parece fuego (pedido del usuario EP007): 5 lenguas de llama con volumen que crecen, bajan y se
    mecen (llaves cada 2 cuadros), color por altura con ruido que sube, nucleo claro, resplandor, CHISPAS que suben y
    una luz naranja que parpadea. Sin simulacion. Alto ~1,5 * tam. Devuelve el vacio raiz (origen en la base: se puede
    pegar a una mano con ep7.en_mano). Visible de f0 a f1."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    mat = _mat_fuego(fuerza=fuerza)
    lenguas = [(0.0, 0.0, 1.0, 0.62), (0.16, 0.06, 0.78, 0.46), (-0.16, -0.04, 0.82, 0.48), (0.05, -0.15, 0.66, 0.4),
               (-0.06, 0.15, 0.7, 0.42)]
    hechos = []
    for i, (dx, dy, h, w) in enumerate(lenguas):
        o = _lengua_fuego("%s_L%d" % (nombre, i), col, semilla * 13 + i, mat)
        o.parent = raiz; o.location = (dx * tam, dy * tam, 0)
        hechos.append((o, h * 1.5 * tam, w * tam, rnd.uniform(0, T2)))
    nuc = _lengua_fuego(nombre + "_Nucleo", col, semilla * 13 + 9, _mat_fuego("VFX_FuegoNucleo_v2", fuerza * 1.5))
    nuc.parent = raiz; hechos.append((nuc, 0.55 * tam, 0.34 * tam, rnd.uniform(0, T2)))
    for f in range(f0, f1 + 1, 2):                    # crece, baja y se mece (nunca igual: senos con fases distintas)
        t = f / 30.0
        for o, h, w, ph in hechos:
            n1 = math.sin(t * 9.1 + ph) * 0.5 + math.sin(t * 15.3 + ph * 1.7) * 0.3 + math.sin(t * 23.7 + ph * 0.6) * 0.2
            o.scale = (w * (1 - 0.07 * n1), w * (1 - 0.07 * n1), h * (1 + 0.2 * n1))
            o.rotation_euler = (math.radians(7 * math.sin(t * 5.3 + ph)), math.radians(8 * math.sin(t * 4.1 + ph * 1.3)), 0)
            o.keyframe_insert("scale", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    # resplandor suave en la base (no tapa: transparente en la orilla)
    gm = bpy.data.materials.get("VFX_FuegoResplandor_v2")
    if gm is None:
        gm = bpy.data.materials.new("VFX_FuegoResplandor_v2"); gm.use_nodes = True
        nt = gm.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1.0, 0.42, 0.05, 1); em.inputs["Strength"].default_value = 1.0
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.6
        a = nt.nodes.new("ShaderNodeMath"); a.operation = 'SUBTRACT'; a.inputs[0].default_value = 1.0
        nt.links.new(lw.outputs["Facing"], a.inputs[1])
        b = nt.nodes.new("ShaderNodeMath"); b.operation = 'POWER'; b.inputs[1].default_value = 2.5; nt.links.new(a.outputs[0], b.inputs[0])
        c = nt.nodes.new("ShaderNodeMath"); c.operation = 'MULTIPLY'; c.inputs[1].default_value = 0.4; nt.links.new(b.outputs[0], c.inputs[0])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(c.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs["Surface"])
        try:
            gm.surface_render_method = 'BLENDED'
        except Exception:
            gm.blend_method = 'BLEND'
        gm.use_backface_culling = True
    me = bpy.data.meshes.new(nombre + "_Resplandor"); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.55 * tam)
    bm.to_mesh(me); bm.free(); me.materials.append(gm)
    for p in me.polygons:
        p.use_smooth = True
    g = bpy.data.objects.new(nombre + "_Resplandor", me); col.objects.link(g); g.parent = raiz
    g.location = (0, 0, 0.45 * tam); g.scale = (1.0, 1.0, 1.25); g.visible_shadow = False
    if chispas:                                       # chispas que suben, se van de lado y se apagan
        cm = _mat("VFX_Chispa_Fuego", "#ffc04a", 9.0, 0.3)
        for k in range(9):
            me = bpy.data.meshes.new("%s_Chispa%d" % (nombre, k)); bm = bmesh.new()
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.035 * tam); bm.to_mesh(me); bm.free(); me.materials.append(cm)
            ch = bpy.data.objects.new(me.name, me); col.objects.link(ch); ch.parent = raiz; ch.visible_shadow = False
            dur = rnd.randint(16, 26); f = f0 + rnd.randint(0, dur)
            while f < f1:
                x0, y0 = rnd.uniform(-0.25, 0.25) * tam, rnd.uniform(-0.25, 0.25) * tam
                ch.location = (x0, y0, 0.3 * tam); ch.scale = (0.01,) * 3
                ch.keyframe_insert("location", frame=f); ch.keyframe_insert("scale", frame=f)
                ch.scale = (1.0,) * 3; ch.keyframe_insert("scale", frame=f + 2)
                ch.location = (x0 + rnd.uniform(-0.5, 0.5) * tam, y0 + rnd.uniform(-0.3, 0.3) * tam, rnd.uniform(1.7, 2.4) * tam)
                ch.scale = (0.01,) * 3
                ch.keyframe_insert("location", frame=f + dur); ch.keyframe_insert("scale", frame=f + dur)
                f += dur + 1
    if luz:                                           # luz naranja que parpadea
        ld = bpy.data.lights.new(nombre + "_Luz", 'POINT'); ld.color = (1.0, 0.52, 0.16); ld.shadow_soft_size = 0.3 * tam
        lo = bpy.data.objects.new(nombre + "_Luz", ld); col.objects.link(lo); lo.parent = raiz; lo.location = (0, 0, 0.7 * tam)
        for f in range(f0, f1 + 1, 2):
            t = f / 30.0
            ld.energy = 110 * tam * (0.85 + 0.15 * math.sin(t * 17 + semilla) + 0.1 * math.sin(t * 29))
            ld.keyframe_insert("energy", frame=f)
    for o in [raiz] + list(raiz.children_recursive):
        _visible(o, f0, f1)
        _constante(o)
    return raiz
