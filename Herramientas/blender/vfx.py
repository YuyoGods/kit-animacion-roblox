# EFECTOS (VFX) CARICATURA para los momentos clave: rapidos (< 1 s), visibles y sin tapar la cara de quien habla.
# Todo se anima con llaves (no hay simulacion que hornear): sirve igual en vista previa y en el render final.
# Uso dentro de Blender (script de episodio):
#   import vfx
#   vfx.migas("Migas_T03", col, (x, y, z), f0)                 # al romper la galleta: migajas que saltan y caen
#   vfx.migas_mordida("Migas_T05", col, borde, f_mordida, f_mastica)  # al MORDER: migas que caen de la boca (2 tandas)
#   vfx.fuego_caricatura("Fuego_T09", col, (x, y, z), f0, f1, ancho, alto, camara)  # muro de llamas planas (+ humo_negro)
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


def corazones(nombre, col, pos, f0, n=5, color="#ff4f8b", tam=1.0, ancho=1.6, camara=None, semilla=7, relleno=False):
    """corazones de LINEA DELGADA (con brillo) que salen con un pop, suben meciendose y se desvanecen (~1 s).
    Se ven bien sin tapar: grosor fino, nucleo blanco y halo de color. relleno=True agrega un relleno suave."""
    rnd = random.Random(semilla)
    raiz = _raiz(nombre, col, pos)
    m = _mat("VFX_Corazon_" + color.lstrip("#"), color, 8.0, 0.3)
    nucleo = _mat("VFX_Corazon_Nucleo", "#ffffff", 4.0, 0.3)
    for i in range(n):
        s = rnd.uniform(0.32, 0.5) * tam
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
