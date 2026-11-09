# MUEBLES Y DECORACION DE CUARTOS (estilo Roblox, low poly) para vestir interiores en cualquier episodio.
# Uso dentro de Blender:  import muebles_cartoon as mc ; mc.tocador_espejo("Tocador", coleccion) ...
# Convenciones (iguales a objetos_cartoon):
#   - muebles de piso:   origen en la base; los que van contra la pared tienen el origen en el centro de su parte
#                        de ATRAS (se ponen con location = punto de la pared) y el frente mira a -Y.
#   - cosas de pared:    (cuadro, repisa, cortina, fotos, banderines, foquitos_linea) origen en la pared, frente a -Y.
#   - para girar hacia el cuarto: pared con normal +X -> rot z 90 ; -X -> -90 ; +Y -> 180 ; -Y -> 0  (ver en_pared()).
# Tamanos pensados para personajes de ~5 unidades de alto (cama ~4 x 6, escritorio ~2,6 de alto).
# Hecho para EP005 (2026-11-08): cuarto de chica (tocador con espejo y foquitos, cama con dosel, cortinas, tapete,
# cuadros, repisas, peluches) y cuarto de ninos (cuadros de cohete y ajolote, banderines, estrellas, juguetes).
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
from objetos_cartoon import P, mat, contorno, _acabado

BLANCO = "#fbf6f2"
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "texturas")
PISO = Matrix.Rotation(math.radians(-90), 4, 'X')     # figura plana acostada en el piso (grosor hacia arriba, su 'arriba' mira a +Y)


def emite(nombre, color, fuerza=3.0):
    """material que brilla (focos, estrellas). Con vista Standard se ve blanco-calido sin quemar alrededor."""
    return mat(nombre, color, 0.5, emit=fuerza)


def recolorear(o, mapa):
    """cambia materiales de UN objeto del mapa solo en este archivo (ranura a nivel de objeto); mapa = {nombre_material
    original: material nuevo}. Repetible (si la ranura ya es del objeto, no la toca)."""
    for s in o.material_slots:
        if s.link == 'OBJECT' or not s.material:
            continue
        nuevo = mapa.get(s.material.name)
        if nuevo:
            s.link = 'OBJECT'; s.material = nuevo
    return o


def en_pared(o, punto, normal, alto=None):
    """pone un objeto (frente a -Y) pegado a la pared en 'punto', mirando hacia 'normal' ('+x','-x','+y','-y')."""
    rot = {"+x": 90, "-x": -90, "+y": 180, "-y": 0}[normal]
    o.location = (punto[0], punto[1], alto if alto is not None else punto[2])
    o.rotation_euler = (0, 0, math.radians(rot))
    return o


# ------------------------------------------------------------------ figuras planas (para cuadros y cojines)
def pts_corazon(r=0.5, k=32):
    """contorno de corazon en (x, z); ancho ~2r, alto ~1,8r, centrado."""
    pts = []
    for i in range(k):
        t = 2 * math.pi * i / k
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * r / 16, (z + 2.5) * r / 16))
    return pts


def pts_estrella(r=0.5, ri=0.45, puntas=5):
    return [((r if i % 2 == 0 else r * ri) * math.sin(math.pi * i / puntas),
             (r if i % 2 == 0 else r * ri) * math.cos(math.pi * i / puntas)) for i in range(2 * puntas)]


def pts_circulo(r=0.5, k=20, cx=0.0, cz=0.0, esc=(1, 1)):
    return [(cx + r * esc[0] * math.cos(2 * math.pi * i / k), cz + r * esc[1] * math.sin(2 * math.pi * i / k)) for i in range(k)]


def pts_medio_aro(r1, r2, k=16):
    """medio aro (arcoiris): arco de afuera y regreso por el de adentro."""
    afuera = [(r2 * math.cos(math.pi * i / k), r2 * math.sin(math.pi * i / k)) for i in range(k + 1)]
    adentro = [(r1 * math.cos(math.pi * i / k), r1 * math.sin(math.pi * i / k)) for i in range(k, -1, -1)]
    return afuera + adentro


def prisma(p, pts, grosor, m, M=None):
    """agrega a P una figura plana (puntos x,z) con grosor hacia el frente (-Y). M = matriz extra (posicion/giro)."""
    M = p.M @ (M if M is not None else Matrix.Identity(4))
    bm = p.bm
    vs = [bm.verts.new(M @ Vector((x, 0, z))) for x, z in pts]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=M.to_3x3() @ Vector((0, -grosor, 0)), verts=nv)
    i = p._i(m)
    for ff in {f} | {ff for v in nv for ff in v.link_faces}:
        ff.material_index = i
    return p


def _T(x, y, z):
    return Matrix.Translation((x, y, z))


def _rejilla(p, filas, m, cerrar=False):
    """malla de tela: 'filas' = lista de filas (cada una lista de Vector). Une fila con fila en cuadros."""
    bm = p.bm
    vv = [[bm.verts.new(v) for v in fila] for fila in filas]
    i = p._i(m)
    for a, b in zip(vv, vv[1:]):
        n = len(a)
        for j in range(n - (0 if cerrar else 1)):
            k = (j + 1) % n
            f = bm.faces.new((a[j], a[k], b[k], b[j]))
            f.material_index = i
    return p


def _suave(o):
    for pl in o.data.polygons:
        pl.use_smooth = True
    return o


# ------------------------------------------------------------------ muebles
def tocador_espejo(nombre, col, color="#f6a5c8", tam=1.0, focos="#fff1c9"):
    """tocador de chica: mesa blanca con cajones rosas, espejo REDONDO de caricatura (azul claro con dos rayitas de
    brillo, se lee "espejo" sin reflejos) y marco con FOQUITOS que brillan; perfumes y un joyero encima.
    Origen: base, centro de atras (va contra la pared). Ancho 3,4 * tam; mesa 2,5 de alto; centro del espejo a 4,3
    (a la altura de la cara de un personaje de pie). Hijo de referencia: <nombre>_Espejo (vacio en el centro del espejo,
    para poner la camara "desde el espejo")."""
    p = P(nombre, col)
    W, D, H = 3.4, 1.3, 2.5
    bl, ro = mat("CT_Mueble_Blanco", BLANCO, 0.45), mat("CT_Mueble_" + color.lstrip("#"), color, 0.5)
    oro, esp = mat("CT_Oro_Perilla", "#e2b23a", 0.3), mat("CT_Espejo_Caricatura", "#a9d8f0", 0.12)
    brillo, foco = mat("CT_Brillo_Espejo", "#ffffff", 0.2, emit=0.6), emite("CT_Foco_" + focos.lstrip("#"), focos, 3.0)
    p.caja((0, -D / 2, H - 0.08), (W + 0.1, D + 0.08, 0.16), bl)                 # cubierta
    for x in (-W / 2 + 0.55, W / 2 - 0.55):                                      # dos columnas de cajones
        p.caja((x, -D / 2, (H - 0.16) / 2), (1.1, D - 0.04, H - 0.16), ro)
        for z in (0.55, 1.25, 1.95):
            p.caja((x, -D - 0.005, z + 0.33), (0.98, 0.03, 0.04), bl)
            p.esfera((x, -D - 0.05, z), 0.07, oro, segs=8)
    p.caja((0, -D / 2, H - 0.42), (W - 2.2, D - 0.04, 0.5), ro)                 # cajon del centro
    p.esfera((0, -D - 0.05, H - 0.42), 0.07, oro, segs=8)
    zc, R = 4.3, 1.12                                                            # espejo redondo
    p.caja((0, -0.1, H + 0.45), (0.5, 0.16, 0.9), bl)                             # soporte
    p.cono((0, -0.02, zc), R + 0.26, R + 0.26, 0.14, bl, segs=32, rot=('X', 90))
    p.cono((0, -0.15, zc), R, R, 0.04, esp, segs=32, rot=('X', 90))
    for dx, lg in ((-0.3, 1.1), (0.12, 0.6)):                                    # rayitas de brillo
        p.caja((dx, -0.2, zc + 0.15), (0.09, 0.012, lg), brillo, rot=('Y', -35))
    for i in range(12):                                                          # foquitos del marco
        a = 2 * math.pi * i / 12
        p.esfera((math.cos(a) * (R + 0.13), -0.2, zc + math.sin(a) * (R + 0.13)), 0.085, foco, segs=8)
    # cositas encima: dos perfumes, un joyero
    vid, tapa = mat("CT_Perfume", "#f59ac1", 0.15), mat("CT_Oro_Perilla", "#e2b23a", 0.3)
    for x, h in ((-1.25, 0.34), (-0.95, 0.26)):
        p.cono((x, -0.75, H), 0.11, 0.11, h, vid, segs=10)
        p.cono((x, -0.75, H + h), 0.05, 0.05, 0.08, tapa, segs=8)
    p.caja((1.15, -0.75, H + 0.13), (0.5, 0.34, 0.26), mat("CT_Joyero", "#b48ae8", 0.5))
    p.caja((1.15, -0.75, H + 0.29), (0.54, 0.38, 0.06), bl)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.02); o.scale = (tam,) * 3
    e = bpy.data.objects.new(nombre + "_Espejo", None); col.objects.link(e)
    e.parent = o; e.location = (0, -0.2, zc); e.empty_display_size = 0.3
    return o


def banquito(nombre, col, color="#f6a5c8", tam=1.0):
    """banquito redondo afelpado con patas blancas. Origen en la base. Alto ~1,6 * tam."""
    p = P(nombre, col)
    bl, ro = mat("CT_Mueble_Blanco", BLANCO, 0.45), mat("CT_Felpa_" + color.lstrip("#"), color, 1.0)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        p.cono((0.36 * math.cos(a), 0.36 * math.sin(a), 0), 0.05, 0.06, 1.2, bl, segs=8)
    p.cono((0, 0, 1.15), 0.62, 0.62, 0.18, bl, segs=24)
    p.esfera((0, 0, 1.38), 0.62, ro, esc=(1, 1, 0.42), segs=20)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def buro(nombre, col, color=BLANCO, color2="#f6a5c8", tam=1.0):
    """buro (mesita de noche) con dos cajones de color. Origen: base, centro de atras. 1,4 x 1,2 x 1,9."""
    p = P(nombre, col)
    c, c2, oro = mat("CT_Mueble_" + color.lstrip("#"), color, 0.45), mat("CT_Mueble_" + color2.lstrip("#"), color2, 0.5), mat("CT_Oro_Perilla", "#e2b23a", 0.3)
    p.caja((0, -0.6, 0.95), (1.4, 1.2, 1.9), c)
    for z in (0.5, 1.3):
        p.caja((0, -1.2, z), (1.18, 0.04, 0.62), c2)
        p.esfera((0, -1.25, z), 0.07, oro, segs=8)
    o = _acabado(p.fin(), bisel=0.012); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def lampara_buro(nombre, col, color="#f6a5c8", tam=1.0, luz=0.0, color_luz=(1.0, 0.85, 0.65)):
    """lamparita de buro: base redonda, palito y pantalla de color con el foco que brilla abajo. Origen en la base.
    Alto ~1,25 * tam. luz > 0 agrega una luz de punto (W) hija, para escenas de noche."""
    p = P(nombre, col)
    c, bl, foco = mat("CT_Pantalla_" + color.lstrip("#"), color, 0.7), mat("CT_Mueble_Blanco", BLANCO, 0.45), emite("CT_Foco_fff1c9", "#fff1c9", 3.0)
    p.esfera((0, 0, 0.14), 0.24, bl, esc=(1, 1, 0.6), segs=14)
    p.cono((0, 0, 0.2), 0.04, 0.04, 0.55, bl, segs=8)
    p.esfera((0, 0, 0.72), 0.14, foco, segs=10)
    p.cono((0, 0, 0.62), 0.42, 0.26, 0.55, c, segs=20)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    if luz:
        ld = bpy.data.lights.new(nombre + "_Luz", 'POINT'); ld.energy = luz; ld.color = color_luz; ld.shadow_soft_size = 0.3
        lo = bpy.data.objects.new(nombre + "_Luz", ld); col.objects.link(lo); lo.parent = o; lo.location = (0, 0, 0.7)
    return o


def lampara_colgante(nombre, col, color="#f6a5c8", tam=1.0):
    """lampara de techo colgante (cable + campana de color + foco). Origen ARRIBA (pegado al techo); cuelga hacia -Z
    ~1,3 * tam. Sustituye los discos blancos del mapa que se queman en cuadro."""
    p = P(nombre, col)
    c, neg, foco = mat("CT_Pantalla_" + color.lstrip("#"), color, 0.6), mat("CT_Negro", "#151515", 0.5), emite("CT_Foco_Colgante", "#fff1c9", 1.2)
    p.cono((0, 0, -0.12), 0.25, 0.25, 0.12, c, segs=16)
    p.cono((0, 0, -0.75), 0.025, 0.025, 0.65, neg, segs=6)
    p.esfera((0, 0, -1.05), 0.6, c, esc=(1, 1, 0.55), segs=20)
    abajo = [v for v in p.bm.verts if v.co.z < -1.05 - 0.001]
    bmesh.ops.delete(p.bm, geom=abajo, context='VERTS')
    p.esfera((0, 0, -0.93), 0.17, foco, segs=10)                                # foco escondido dentro de la campana
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def tapete_redondo(nombre, col, r=3.2, color="#f8c8dc", color2=BLANCO, tam=1.0):
    """tapete redondo afelpado de dos colores (aros) con orilla de bolitas. Origen en el centro, en el piso."""
    p = P(nombre, col)
    c, c2 = mat("CT_Felpa_" + color.lstrip("#"), color, 1.0), mat("CT_Felpa_" + color2.lstrip("#"), color2, 1.0)
    p.cono((0, 0, 0), r, r, 0.05, c, segs=40)
    p.cono((0, 0, 0.05), r * 0.72, r * 0.72, 0.012, c2, segs=40)
    p.cono((0, 0, 0.062), r * 0.5, r * 0.5, 0.012, c, segs=40)
    n = max(18, int(r * 11))
    for i in range(n):
        a = 2 * math.pi * i / n
        p.esfera((r * math.cos(a), r * math.sin(a), 0.04), 0.11, c2, esc=(1, 1, 0.5), segs=6)
    o = _acabado(p.fin(), bisel=0); o.scale = (tam,) * 3
    return o


def tapete_corazon(nombre, col, r=1.2, color="#ff8fb8", tam=1.0):
    """tapetito en forma de corazon (acostado en el piso). Origen en el centro."""
    p = P(nombre, col)
    prisma(p, pts_corazon(r), 0.05, mat("CT_Felpa_" + color.lstrip("#"), color, 1.0), M=PISO)
    o = _acabado(p.fin(), bisel=0.02); o.scale = (tam,) * 3
    return o


def cojin(nombre, col, color="#ffffff", w=1.0, h=0.75, grosor=0.32, tam=1.0, corazon=False):
    """cojin acolchado de pie (frente -Y). corazon=True -> cojin en forma de corazon. Origen en la base."""
    p = P(nombre, col)
    m = mat("CT_Cojin_" + color.lstrip("#"), color, 0.95)
    if corazon:
        prisma(p, [(x, z + h * 0.6) for x, z in pts_corazon(w / 2)], grosor, m, M=_T(0, grosor / 2, 0))
    else:
        p.caja((0, 0, h / 2), (w, grosor, h), m)
    o = _acabado(p.fin(), angulo=30, bisel=min(0.12, grosor * 0.4)); o.modifiers["Bisel"].segments = 3
    contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def puff_pera(nombre, col, color="#f6a5c8", tam=1.0):
    """puff tipo pera (bean bag) para sentarse en el piso. Origen en la base. ~1,6 de ancho."""
    p = P(nombre, col)
    m = mat("CT_Felpa_" + color.lstrip("#"), color, 1.0)
    p.esfera((0, 0, 0.45), 0.85, m, esc=(1, 1, 0.55), segs=20)
    p.esfera((0, 0.25, 0.85), 0.6, m, esc=(1, 0.8, 0.7), segs=16)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


def peluche_ajolote(nombre, col, color="#ff9cc4", tam=1.0):
    """peluche de ajolote rosa (cabezon, branquias de colores, ojitos y sonrisa). Origen en la base; mira a -Y. ~0,9."""
    p = P(nombre, col)
    c, osc, neg = mat("CT_Ajolote_" + color.lstrip("#"), color, 0.95), mat("CT_Ajolote_Branquia", "#ff5f9e", 0.9), mat("CT_Negro", "#151515", 0.5)
    p.esfera((0, 0.05, 0.25), 0.3, c, esc=(1, 1.3, 0.8), segs=14)
    p.esfera((0, -0.05, 0.62), 0.36, c, esc=(1.25, 1, 0.9), segs=16)
    for s in (-1, 1):
        for k, (dz, ang) in enumerate(((0.2, 35), (0.02, 0), (-0.14, -30))):
            p.esfera((s * 0.5, 0.0, 0.66 + dz), 0.07, osc, esc=(2.2, 0.8, 0.8), segs=8)
        p.esfera((s * 0.16, -0.36, 0.7), 0.045, neg, segs=8)
        p.esfera((s * 0.22, 0.0, 0.05), 0.09, c, segs=8)
    p.caja((0, -0.38, 0.55), (0.16, 0.02, 0.025), neg)
    p.esfera((0, 0.42, 0.2), 0.12, c, esc=(0.5, 1.6, 0.8), segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.018); o.scale = (tam,) * 3
    return o


def pelota(nombre, col, r=0.4, color="#d9433a", color2=BLANCO, tam=1.0):
    """pelota de dos colores (franja). Origen en la base."""
    p = P(nombre, col)
    p.esfera((0, 0, r), r, mat("CT_Pelota_" + color.lstrip("#"), color, 0.4), segs=16)
    p.cono((0, 0, r - r * 0.18), r * 1.01, r * 1.01, r * 0.36, mat("CT_Pelota_" + color2.lstrip("#"), color2, 0.4), segs=24)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def cochecito(nombre, col, color="#2f6fd6", tam=1.0):
    """carrito de juguete (cuerpo, cabina, ventanas, 4 llantas). Origen en la base; el frente mira a -Y. ~0,9 de largo."""
    p = P(nombre, col)
    c, neg, vid = mat("CT_Carrito_" + color.lstrip("#"), color, 0.4), mat("CT_Negro", "#151515", 0.5), mat("CT_Ventana_Juguete", "#bfe6ff", 0.2)
    p.caja((0, 0, 0.2), (0.5, 0.9, 0.18), c)
    p.caja((0, 0.06, 0.37), (0.42, 0.46, 0.18), c)
    p.caja((0, -0.17, 0.37), (0.36, 0.02, 0.13), vid)
    for x in (-0.26, 0.26):
        for y in (-0.28, 0.28):
            p.cono((x - 0.04 * (1 if x < 0 else -1), y, 0.12), 0.12, 0.12, 0.1, neg, segs=12, rot=('Y', 90))
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def libros(nombre, col, n=5, colores=("#e85d75", "#7fb8e0", "#f2c230", "#9b7fe0", "#5cc28a"), tam=1.0):
    """fila de libros de pie, de alturas distintas. Origen en la base, centro de la fila (a lo largo de X)."""
    p = P(nombre, col)
    bl = mat("CT_Hojas_Libro", "#fff8e8", 0.8)
    x = -n * 0.09
    for i in range(n):
        h = 0.55 + 0.12 * ((i * 7) % 3)
        g = 0.14 + 0.04 * (i % 2)
        p.caja((x + g / 2, 0, h / 2), (g, 0.42, h), mat("CT_Libro_" + colores[i % len(colores)].lstrip("#"), colores[i % len(colores)], 0.6))
        p.caja((x + g / 2, -0.012, h / 2), (g * 0.7, 0.4, h * 0.92), bl)
        x += g + 0.015
    o = _acabado(p.fin(), bisel=0.006); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def macetita(nombre, col, color="#f6a5c8", tam=1.0):
    """macetita con planta redonda. Origen en la base. Alto ~0,7."""
    p = P(nombre, col)
    p.cono((0, 0, 0), 0.16, 0.22, 0.3, mat("CT_Maceta_" + color.lstrip("#"), color, 0.6), segs=12)
    v = mat("CT_Hoja_Planta", "#4caf6a", 0.8)
    for dx, dz, r in ((0, 0.45, 0.2), (-0.13, 0.38, 0.14), (0.13, 0.4, 0.15)):
        p.esfera((dx, 0, dz), r, v, segs=10)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


# ------------------------------------------------------------------ cosas de pared
def cuadro(nombre, col, dibujo="corazon", w=1.4, h=1.8, fondo="#ffffff", marco="#fbf6f2", tam=1.0):
    """cuadro / poster de pared con dibujo en relieve: corazon, arcoiris, estrella, cohete, ajolote, luna.
    Origen en el centro de la parte de atras (pegado a la pared); el frente mira a -Y."""
    p = P(nombre, col)
    mm, mf = mat("CT_Marco_" + marco.lstrip("#"), marco, 0.5), mat("CT_Fondo_" + fondo.lstrip("#"), fondo, 0.8)
    p.caja((0, -0.04, 0), (w + 0.16, 0.08, h + 0.16), mm)
    p.caja((0, -0.085, 0), (w, 0.02, h), mf)
    y0 = -0.095
    M = lambda x=0.0, z=0.0, s=1.0: _T(x, y0, z) @ Matrix.Diagonal((s, s, s, 1))
    if dibujo == "corazon":
        prisma(p, pts_corazon(w * 0.32), 0.05, mat("CT_Dib_Corazon", "#ff4f8b", 0.6), M(0, -h * 0.05))
        prisma(p, pts_corazon(w * 0.13), 0.06, mat("CT_Dib_Corazon2", "#ffd1e3", 0.6), M(-w * 0.3, h * 0.3))
    elif dibujo == "arcoiris":
        cols = ("#ff5a5a", "#ff9f40", "#ffd84a", "#6fd36f", "#5aa7ff")
        r = w * 0.44
        for i, c in enumerate(cols):
            prisma(p, pts_medio_aro(r - (i + 1) * w * 0.055, r - i * w * 0.055), 0.04 + 0.004 * i, mat("CT_Arco_" + c.lstrip("#"), c, 0.6), M(0, -h * 0.12))
        nb = mat("CT_Nube", "#ffffff", 0.8)
        for s in (-1, 1):
            for dx, r2 in ((0, 0.13), (0.12, 0.1), (-0.12, 0.1)):
                prisma(p, pts_circulo(r2 * w, 14), 0.07, nb, M(s * w * 0.33 + dx * w, -h * 0.15))
    elif dibujo == "estrella":
        prisma(p, pts_estrella(w * 0.36), 0.05, mat("CT_Dib_Estrella", "#ffd84a", 0.5), M(0, 0))
    elif dibujo == "luna":
        lun = mat("CT_Dib_Luna", "#ffe9a0", 0.5)
        prisma(p, pts_circulo(w * 0.3, 24), 0.05, lun, M(0, h * 0.05))
        prisma(p, pts_circulo(w * 0.26, 24), 0.06, mf, M(w * 0.14, h * 0.13))
        for x, z in ((-0.3, -0.3), (0.3, -0.25), (0.25, 0.35)):
            prisma(p, pts_estrella(w * 0.06), 0.05, lun, M(x * w, z * h))
    elif dibujo == "cohete":
        bl, rojo, az = mat("CT_Dib_Blanco", "#f4f4f4", 0.6), mat("CT_Dib_Rojo", "#d9433a", 0.8), mat("CT_Dib_Azul", "#2f6fd6", 0.8)
        nar = mat("CT_Dib_Naranja", "#ff9f40", 0.6)
        s = w / 1.4
        prisma(p, [(-0.2 * s, -0.35 * s), (0.2 * s, -0.35 * s), (0.2 * s, 0.3 * s), (-0.2 * s, 0.3 * s)], 0.05, bl, M())
        prisma(p, [(-0.2 * s, 0.3 * s), (0.2 * s, 0.3 * s), (0, 0.62 * s)], 0.05, rojo, M())
        for sg in (-1, 1):
            prisma(p, [(sg * 0.2 * s, -0.35 * s), (sg * 0.42 * s, -0.5 * s), (sg * 0.2 * s, -0.05 * s)], 0.05, rojo, M())
        prisma(p, pts_circulo(0.11 * s, 16), 0.07, az, M(0, 0.08 * s))
        prisma(p, [(-0.14 * s, -0.36 * s), (0.14 * s, -0.36 * s), (0, -0.66 * s)], 0.05, nar, M())
        for x, z in ((-0.45, 0.6), (0.4, 0.45), (-0.35, -0.2), (0.45, -0.55)):
            prisma(p, pts_estrella(0.06 * s), 0.05, mat("CT_Dib_Amarillo", "#f2c230", 0.8), M(x * s, z * s))
    elif dibujo == "ajolote":
        c, osc, neg = mat("CT_Ajolote_ff9cc4", "#ff9cc4", 0.8), mat("CT_Ajolote_Branquia", "#ff5f9e", 0.9), mat("CT_Negro", "#151515", 0.5)
        s = w / 1.4
        for sg in (-1, 1):
            for dz, a in ((0.2, 30), (0.0, 0), (-0.2, -30)):
                prisma(p, pts_circulo(0.12 * s, 12, esc=(1.8, 0.6)), 0.04, osc,
                       M(sg * 0.42 * s, dz * s) @ Matrix.Rotation(math.radians(a * sg), 4, 'Y'))
        prisma(p, pts_circulo(0.38 * s, 24, esc=(1.15, 0.95)), 0.05, c, M(0, 0))
        for sg in (-1, 1):
            prisma(p, pts_circulo(0.05 * s, 10), 0.07, neg, M(sg * 0.15 * s, 0.08 * s))
            prisma(p, pts_circulo(0.06 * s, 10), 0.06, mat("CT_Dib_Cachete", "#ff6fa5", 0.8), M(sg * 0.24 * s, -0.06 * s))
        prisma(p, pts_medio_aro(0.07 * s, 0.1 * s, 10), 0.07, neg, M(0, -0.05 * s) @ Matrix.Rotation(math.pi, 4, 'Y'))
    elif dibujo == "paisaje":
        s = w / 1.4
        prisma(p, pts_circulo(0.16 * s, 18), 0.04, mat("CT_Dib_Sol", "#ffd84a", 0.5), M(0.3 * s, 0.35 * h / 1.8 * 1.0))
        for (x, a, c) in ((-0.3, 0.75, "#5f8f6a"), (0.15, 0.95, "#4f7fa8"), (0.45, 0.6, "#6faa6a")):
            prisma(p, [(x * w - a * w * 0.45, -0.3 * h), (x * w + a * w * 0.45, -0.3 * h), (x * w, -0.3 * h + a * h * 0.55)], 0.05, mat("CT_Dib_Monte_" + c.lstrip("#"), c, 0.7), M())
            prisma(p, [(x * w - a * w * 0.12, -0.3 * h + a * h * 0.4), (x * w + a * w * 0.12, -0.3 * h + a * h * 0.4), (x * w, -0.3 * h + a * h * 0.55)], 0.06, mat("CT_Dib_Nieve", "#ffffff", 0.6), M())
        prisma(p, [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, -0.28 * h), (-w / 2, -0.28 * h)], 0.055, mat("CT_Dib_Pasto", "#7cc46a", 0.7), M())
    elif dibujo == "gatita":
        _cara_gatita(p, w * 0.36, lambda x, z, dy=0.0: M(x, z - h * 0.06) @ _T(0, -dy, 0), 0.04)
        for x, z in ((-0.36, 0.36), (0.36, 0.34)):
            prisma(p, pts_corazon(w * 0.07), 0.05, mat("CT_Dib_Corazon", "#ff4f8b", 0.6), M(x * w, z * h))
    o = _acabado(p.fin(), bisel=0.008); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def _cara_gatita(p, r, M, g, cara="#ffffff", rosa="#ff9cc4"):
    """carita de gatita kawaii ORIGINAL (orejas, ojos de punto, naricita, boca :3, cachetes, bigotes) hecha con figuras
    planas. M(x, z, dy) = matriz de cada pieza (dy = cuanto mas al frente). g = grosor de la cabeza."""
    mc, mr = mat("CT_Gatita_Cara_" + cara.lstrip("#"), cara, 0.8), mat("CT_Gatita_Rosa_" + rosa.lstrip("#"), rosa, 0.8)
    neg, nar = mat("CT_Negro", "#151515", 0.5), mat("CT_Gatita_Nariz", "#ff6f9e", 0.5)
    for s in (-1, 1):
        prisma(p, [(s * 0.95 * r, 0.12 * r), (s * 0.8 * r, 1.02 * r), (s * 0.18 * r, 0.6 * r)], g * 0.8, mc, M(0, 0))
        prisma(p, [(s * 0.8 * r, 0.3 * r), (s * 0.74 * r, 0.82 * r), (s * 0.38 * r, 0.58 * r)], g * 0.9, mr, M(0, 0))
    prisma(p, pts_circulo(r, 32, esc=(1, 0.74)), g, mc, M(0, 0))
    for s in (-1, 1):
        prisma(p, pts_circulo(0.09 * r, 12, esc=(1, 1.15)), g + 0.02, neg, M(s * 0.42 * r, 0.02 * r))
        prisma(p, pts_circulo(0.14 * r, 14, esc=(1, 0.6)), g + 0.012, mr, M(s * 0.62 * r, -0.25 * r))
        for k in (-1, 1):
            prisma(p, [(0, -0.012 * r), (0.36 * r, -0.012 * r + k * 0.06 * r), (0.36 * r, 0.012 * r + k * 0.06 * r), (0, 0.012 * r)],
                   g + 0.012, neg, M(s * 0.8 * r if s > 0 else -0.8 * r - 0.36 * r, (-0.08 + k * 0.08) * r))
    prisma(p, pts_circulo(0.07 * r, 12, esc=(1.2, 0.8)), g + 0.02, nar, M(0, -0.14 * r))
    for s in (-1, 1):
        prisma(p, pts_medio_aro(0.06 * r, 0.09 * r, 8), g + 0.02, neg,
               M(s * 0.075 * r, -0.21 * r) @ Matrix.Rotation(math.pi, 4, 'Y'))


def repisa(nombre, col, ancho=2.8, color=BLANCO, tam=1.0):
    """repisa flotante. Origen en la pared, a la altura de la CARA DE ARRIBA de la tabla (lo que va encima se pone a
    z = 0 local). Fondo 0,6."""
    p = P(nombre, col)
    m = mat("CT_Mueble_" + color.lstrip("#"), color, 0.45)
    p.caja((0, -0.3, -0.06), (ancho, 0.6, 0.12), m)
    for x in (-ancho * 0.35, ancho * 0.35):
        p.caja((x, -0.04, -0.3), (0.06, 0.08, 0.4), m)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def cortina(nombre, col, ancho=1.0, alto=4.4, color="#f7b6cf", lado=1, recogida=0.55, pliegues=4, tam=1.0):
    """una hoja de cortina con pliegues, recogida con un lazo a media altura hacia su orilla de afuera.
    Origen ARRIBA en la orilla de afuera (lado=+1: la orilla de afuera queda en +X y la tela va hacia -X; lado=-1 al
    reves). Cuelga hacia -Z; frente -Y. Poner un par por ventana (lado -1 a la izquierda, +1 a la derecha)."""
    p = P(nombre, col)
    m = mat("CT_Tela_" + color.lstrip("#"), color, 0.95)
    filas, nf, nc = [], 22, 4 * pliegues
    for i in range(nf + 1):
        s = i / nf
        if s < recogida:
            w = 1.0 - 0.62 * (s / recogida) ** 1.6
        else:
            w = 0.38 + 0.4 * ((s - recogida) / (1 - recogida)) ** 0.8
        fila = []
        for j in range(nc + 1):
            u = j / nc
            amp = 0.07 + 0.12 * (1 - w)
            y = -amp * (0.5 + 0.5 * math.sin(2 * math.pi * pliegues * u + 0.5)) - 0.08
            fila.append(Vector((-lado * u * ancho * w, y, -s * alto)))
        filas.append(fila)
    _rejilla(p, filas, m)
    lazo = mat("CT_Lazo_" + color.lstrip("#"), "#ffffff", 0.6)
    p.caja((-lado * ancho * 0.19, -0.16, -recogida * alto), (ancho * 0.42, 0.06, 0.12), lazo)
    o = _suave(p.fin())
    o.scale = (tam,) * 3
    return o


def barra_cortina(nombre, col, ancho=5.0, color=BLANCO, tam=1.0):
    """barra para cortinas con bolitas en las puntas. Origen en el centro, en la pared; frente -Y."""
    p = P(nombre, col)
    m = mat("CT_Mueble_" + color.lstrip("#"), color, 0.4)
    p.cono((-ancho / 2, -0.18, 0), 0.045, 0.045, ancho, m, segs=8, rot=('Y', 90))
    for x in (-ancho / 2 - 0.05, ancho / 2 + 0.05):
        p.esfera((x, -0.18, 0), 0.1, m, segs=10)
        p.caja((x * 0.97, -0.09, 0), (0.06, 0.18, 0.06), m)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def _cuelga(a, b, caida, k):
    """puntos de una cuerda que cuelga de a a b (parabola), k tramos."""
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / k) - Vector((0, 0, caida * 4 * (i / k) * (1 - i / k))) for i in range(k + 1)]


def foquitos(nombre, col, puntos, cada=0.38, caida=0.25, colores=("#fff1c9",), fuerza=1.8, r=0.065, cable="#2f4a2f"):
    """serie de FOQUITOS que cuelga entre los puntos dados (coordenadas del mundo, o locales si luego se emparenta).
    'colores' se van alternando (calido, rosa...). Devuelve un solo objeto (cable + focos)."""
    p = P(nombre, col)
    mc = mat("CT_Cable_" + cable.lstrip("#"), cable, 0.6)
    focos = [emite("CT_Foco_" + c.lstrip("#"), c, fuerza) for c in colores]
    n = 0
    for a, b in zip(puntos, puntos[1:]):
        L = (Vector(b) - Vector(a)).length
        k = max(2, int(L / cada))
        pts = _cuelga(a, b, caida * min(1.0, L / 2.5), k)
        for q0, q1 in zip(pts, pts[1:]):
            d = q1 - q0
            if d.length < 1e-4:
                continue
            rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
            res = bmesh.ops.create_cone(p.bm, cap_ends=False, segments=5, radius1=0.012, radius2=0.012, depth=d.length,
                                        matrix=Matrix.Translation(q0) @ rot @ Matrix.Translation((0, 0, d.length / 2)))
            p._marcar(res, mc)
        for q in pts[1:]:
            p.esfera(tuple(q - Vector((0, 0, r * 0.9))), r, focos[n % len(focos)], esc=(1, 1, 1.3), segs=8)
            n += 1
    o = _suave(p.fin())
    return o


def foquitos_linea(nombre, col, largo=3.0, caida=0.35, colores=("#fff1c9",), fuerza=1.8, tramos=3):
    """foquitos en guirnalda sobre una pared: va de x=-largo/2 a +largo/2 (local), con 'tramos' columpios."""
    xs = [(-largo / 2 + largo * i / tramos, -0.06, 0) for i in range(tramos + 1)]
    return foquitos(nombre, col, xs, caida=caida, colores=colores, fuerza=fuerza)


def fotos_cuerda(nombre, col, largo=3.0, n=5, caida=0.28, colores=("#ff8fb8", "#7fc8ff", "#ffd84a", "#9fe0a0", "#c7a2ff"), tam=1.0):
    """cordel con fotos tipo polaroid y pinzas (decoracion de pared). Local: de x=-largo/2 a +largo/2; frente -Y."""
    p = P(nombre, col)
    cuerda, bl, pin = mat("CT_Cuerda", "#d8c3a0", 0.8), mat("CT_Polaroid", "#ffffff", 0.7), mat("CT_Pinza", "#c49a6c", 0.6)
    pts = _cuelga((-largo / 2, -0.05, 0), (largo / 2, -0.05, 0), caida, 24)
    for q0, q1 in zip(pts, pts[1:]):
        d = q1 - q0
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        res = bmesh.ops.create_cone(p.bm, cap_ends=False, segments=5, radius1=0.015, radius2=0.015, depth=d.length,
                                    matrix=Matrix.Translation(q0) @ rot @ Matrix.Translation((0, 0, d.length / 2)))
        p._marcar(res, cuerda)
    for i in range(n):
        t = (i + 0.5) / n
        q = pts[int(t * 24)]
        ang = (i % 2 - 0.5) * 8
        R = Matrix.Translation(q) @ Matrix.Rotation(math.radians(ang), 4, 'Y')
        p.M = R
        p.caja((0, -0.02, -0.36), (0.46, 0.02, 0.56), bl)
        p.caja((0, -0.035, -0.31), (0.38, 0.012, 0.36), mat("CT_Foto_" + colores[i % len(colores)].lstrip("#"), colores[i % len(colores)], 0.6))
        p.caja((0, -0.05, -0.04), (0.06, 0.04, 0.16), pin)
        p.M = Matrix.Identity(4)
    o = _acabado(p.fin(), bisel=0); o.scale = (tam,) * 3
    return o


def banderines(nombre, col, largo=4.0, n=9, caida=0.35, colores=("#ff5a5a", "#ffd84a", "#5aa7ff", "#6fd36f", "#ff9fd0"), tam=1.0):
    """guirnalda de banderitas triangulares (cuarto de ninos). Local: x=-largo/2 a +largo/2; frente -Y."""
    p = P(nombre, col)
    cuerda = mat("CT_Cuerda", "#d8c3a0", 0.8)
    pts = _cuelga((-largo / 2, -0.05, 0), (largo / 2, -0.05, 0), caida, n * 2)
    for q0, q1 in zip(pts, pts[1:]):
        d = q1 - q0
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        res = bmesh.ops.create_cone(p.bm, cap_ends=False, segments=5, radius1=0.015, radius2=0.015, depth=d.length,
                                    matrix=Matrix.Translation(q0) @ rot @ Matrix.Translation((0, 0, d.length / 2)))
        p._marcar(res, cuerda)
    w = largo / n * 0.8
    for i in range(n):
        q = pts[2 * i + 1]
        c = colores[i % len(colores)]
        prisma(p, [(-w / 2, 0), (w / 2, 0), (0, -w * 1.1)], 0.02, mat("CT_Bandera_" + c.lstrip("#"), c, 0.8), _T(q.x, q.y - 0.01, q.z))
    o = _acabado(p.fin(), bisel=0); o.scale = (tam,) * 3
    return o


def estrellas_techo(nombre, col, ancho=6.0, fondo=4.0, n=14, color="#fff3a0", fuerza=1.6, semilla=4):
    """estrellitas que brillan pegadas al techo (cuarto de noche). Origen en el techo (centro del area); miran abajo."""
    import random
    rnd = random.Random(semilla)
    p = P(nombre, col)
    m = emite("CT_Estrella_Techo_" + color.lstrip("#"), color, fuerza)
    for i in range(n):
        x, y = rnd.uniform(-ancho / 2, ancho / 2), rnd.uniform(-fondo / 2, fondo / 2)
        r = rnd.uniform(0.12, 0.24)
        prisma(p, pts_estrella(r), 0.02, m, _T(x, y, -0.01) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(rnd.uniform(0, 1.2), 4, 'Y'))
    o = p.fin()
    return o


def corona_dosel(nombre, col, ancho_cama=4.2, alto=6.2, color="#fbd3e4", color_corona=BLANCO, focos=("#fff1c9", "#ffc2dc"), tam=1.0):
    """DOSEL de princesa sobre la cabecera: corona blanca en la pared y dos cortinas de tela rosa clara que bajan
    hasta las esquinas de la cama, con foquitos en la orilla. Origen: en la pared, al centro de la cama, en el piso.
    Frente -Y (hacia los pies de la cama). Devuelve la corona; tela y foquitos quedan como hijos."""
    pc = P(nombre, col)
    bl = mat("CT_Mueble_" + color_corona.lstrip("#"), color_corona, 0.45)
    oro = mat("CT_Oro_Perilla", "#e2b23a", 0.3)
    R = 0.8
    pc.cono((0, 0, alto - 0.05), R, R, 0.12, bl, segs=24)
    medio = [v for v in pc.bm.verts if v.co.y > 0.001]
    bmesh.ops.delete(pc.bm, geom=medio, context='VERTS')
    for i in range(9):                                                           # orilla de bolitas
        a = math.pi + math.pi * i / 8
        pc.esfera((R * math.cos(a), R * math.sin(a), alto - 0.08), 0.1, bl, segs=8)
    pc.esfera((0, -R * 0.55, alto + 0.17), 0.12, oro, segs=10)                    # remate dorado
    corona = _acabado(pc.fin(), bisel=0); contorno(corona, 0.015)
    # tela: dos hojas que salen de la corona y bajan a las esquinas de la cabecera
    pt = P(nombre + "_Tela", col)
    tela = mat("CT_Tela_" + color.lstrip("#"), color, 0.95)
    lados_focos = []
    for s in (-1, 1):
        c0 = Vector((s * 0.35, -0.45, alto - 0.12))
        c1 = Vector((s * (ancho_cama / 2 + 0.25), -0.75, alto * 0.5))
        c2 = Vector((s * (ancho_cama / 2 + 0.55), -0.95, 0.12))
        filas, borde = [], []
        nf = 26
        for i in range(nf + 1):
            t = i / nf
            if t < 0.5:
                u = t / 0.5; cen = c0.lerp(c1, u) + Vector((0, 0, 0.35 * math.sin(math.pi * u)))
                ancho = 1.1 - 0.75 * u ** 1.3
            else:
                u = (t - 0.5) / 0.5; cen = c1.lerp(c2, u)
                ancho = 0.35 + 0.85 * u ** 0.9
            fila = []
            for j in range(13):
                v = j / 12 - 0.5
                fold = 0.08 * math.sin(2 * math.pi * 3 * (j / 12)) * (1.4 - ancho)
                fila.append(cen + Vector((v * ancho, fold - 0.02, 0)))
            filas.append(fila)
            borde.append(cen + Vector((s * ancho / 2, -0.12, 0)))
        _rejilla(pt, filas, tela)
        lados_focos.append(borde[::3])
    tela_o = _suave(pt.fin())
    tela_o.parent = corona
    # lazos donde se recoge la tela
    pl = P(nombre + "_Lazos", col)
    lazo = mat("CT_Lazo_Rosa", "#ff8fb8", 0.6)
    for s in (-1, 1):
        q = Vector((s * (ancho_cama / 2 + 0.25), -0.8, alto * 0.5))
        pl.esfera(tuple(q), 0.13, lazo, segs=8)
        for d in (-1, 1):
            pl.esfera(tuple(q + Vector((d * 0.2, -0.02, 0.05))), 0.13, lazo, esc=(1.4, 0.5, 0.8), segs=8)
    lazos = _acabado(pl.fin(), bisel=0); contorno(lazos, 0.012); lazos.parent = corona
    # foquitos por la orilla de cada tela + uno de lado a lado por la corona
    fq = foquitos(nombre + "_Foquitos", col, [tuple(v) for v in lados_focos[0]], cada=0.3, caida=0.12, colores=focos)
    fq.parent = corona
    fq2 = foquitos(nombre + "_Foquitos2", col, [tuple(v) for v in lados_focos[1]], cada=0.3, caida=0.12, colores=focos)
    fq2.parent = corona
    corona.scale = (tam,) * 3
    return corona


# ------------------------------------------------------------------ gatita (diseno propio)
def peluche_gatita(nombre, col, color="#ffffff", rosa="#ff9cc4", collar="#ff4f8b", tam=1.0):
    """peluche de gatita kawaii ORIGINAL sentada (cabezona, orejas rosas, cachetes, collar con cascabel dorado).
    Origen en la base; mira a -Y. Alto ~1 * tam (tam 2 = gatita gigante de rincon)."""
    p = P(nombre, col)
    c, r = mat("CT_Gatita_Felpa_" + color.lstrip("#"), color, 0.95), mat("CT_Gatita_Rosa_" + rosa.lstrip("#"), rosa, 0.8)
    neg, nar = mat("CT_Negro", "#151515", 0.5), mat("CT_Gatita_Nariz", "#ff6f9e", 0.5)
    co, oro = mat("CT_Collar_" + collar.lstrip("#"), collar, 0.6), mat("CT_Oro_Perilla", "#e2b23a", 0.3)
    p.esfera((0, 0.02, 0.27), 0.27, c, esc=(1, 0.9, 1.0), segs=14)                   # cuerpo
    p.esfera((0, 0, 0.66), 0.32, c, esc=(1.2, 0.95, 0.85), segs=18)                  # cabeza
    for s in (-1, 1):
        p.cono((s * 0.22, 0.02, 0.84), 0.13, 0.01, 0.24, c, segs=4, rot=('Y', -s * 22))    # orejas
        p.cono((s * 0.22, -0.035, 0.85), 0.08, 0.01, 0.17, r, segs=4, rot=('Y', -s * 22))
        p.esfera((s * 0.13, -0.27, 0.69), 0.04, neg, esc=(1, 0.6, 1.2), segs=8)          # ojos
        p.esfera((s * 0.24, -0.24, 0.6), 0.06, r, esc=(1, 0.4, 0.7), segs=8)            # cachetes
        p.esfera((s * 0.16, -0.17, 0.06), 0.09, c, esc=(1, 1.2, 0.8), segs=8)           # patitas
        p.esfera((s * 0.24, -0.1, 0.32), 0.08, c, esc=(1, 1, 1.5), segs=8)              # bracitos
    p.esfera((0, -0.29, 0.62), 0.03, nar, esc=(1.3, 0.6, 1), segs=8)
    p.cono((0, 0, 0.44), 0.23, 0.23, 0.05, co, segs=16)                              # collar + cascabel
    p.esfera((0, -0.24, 0.42), 0.05, oro, segs=8)
    p.esfera((0.05, 0.3, 0.12), 0.06, c, esc=(1, 3.0, 1), segs=8)                    # colita
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.018); o.scale = (tam,) * 3
    return o


def tapete_gatita(nombre, col, r=2.4, cara="#ffffff", rosa="#ff9cc4", tam=1.0):
    """tapete con forma de carita de gatita, acostado en el piso (las orejas apuntan a +Y). Origen en el centro."""
    p = P(nombre, col)
    _cara_gatita(p, r, lambda x, z: PISO @ _T(x, 0, z), 0.05, cara, rosa)
    o = _acabado(p.fin(), bisel=0.01); o.scale = (tam,) * 3
    return o


# ------------------------------------------------------------------ materiales con textura (un poco de realismo)
def _sock(lista, ident):
    return next(s for s in lista if s.identifier == ident)


def _rgb(h):
    from objetos_cartoon import lin
    h = h.lstrip("#")
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1,)


def material_tela(nombre, png=None, color="#ffffff", tile=2.0, acolchado=0.0, relieve=0.18, rough=0.92):
    """tela con estampado (PNG de Herramientas/blender/texturas, se repite cada 'tile' unidades en UV), grano fino
    y, si acolchado > 0, costuras de rombos (cobija acolchada). Pensado para UV en unidades (cama() las pone asi)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs["Roughness"].default_value = rough
    uv = nt.nodes.new("ShaderNodeTexCoord")
    if png:
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        im = nt.nodes.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(png if os.path.isabs(png) else os.path.join(TEX, png), check_existing=True)
        nt.links.new(mp.outputs["Vector"], im.inputs["Vector"]); nt.links.new(im.outputs["Color"], bs.inputs["Base Color"])
    else:
        bs.inputs["Base Color"].default_value = _rgb(color); m.diffuse_color = _rgb(color)
    normal = None
    if relieve:
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0; nz.inputs["Detail"].default_value = 3.0
        nt.links.new(uv.outputs["UV"], nz.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = relieve; bp.inputs["Distance"].default_value = 0.01
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); normal = bp
    if acolchado:
        alturas = []
        for ang in (45, -45):
            mp2 = nt.nodes.new("ShaderNodeMapping"); mp2.inputs["Rotation"].default_value = (0, 0, math.radians(ang))
            nt.links.new(uv.outputs["UV"], mp2.inputs["Vector"])
            wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.wave_profile = 'SIN'
            wv.inputs["Scale"].default_value = 0.55
            nt.links.new(mp2.outputs["Vector"], wv.inputs["Vector"]); alturas.append(wv)
        mn = nt.nodes.new("ShaderNodeMath"); mn.operation = 'MINIMUM'
        nt.links.new(alturas[0].outputs["Fac"], mn.inputs[0]); nt.links.new(alturas[1].outputs["Fac"], mn.inputs[1])
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 0.35
        nt.links.new(mn.outputs[0], pw.inputs[0])
        bq = nt.nodes.new("ShaderNodeBump"); bq.inputs["Strength"].default_value = acolchado; bq.inputs["Distance"].default_value = 0.05
        nt.links.new(pw.outputs[0], bq.inputs["Height"])
        if normal:
            nt.links.new(normal.outputs["Normal"], bq.inputs["Normal"])
        normal = bq
    if normal:
        nt.links.new(normal.outputs["Normal"], bs.inputs["Normal"])
    return m


def pintar_pared_por_altura(m, z_corte, arriba, acento=None, franja=None, abajo2=None, franjas=(), clave="pintada_por_altura"):
    """cambia SOLO en este archivo el color de una pared del mapa a partir de cierta altura (piso de arriba), sin
    tocar la geometria ni el mapa original. arriba = "#hex". abajo2 = (z_hasta, "#hex") pinta otro color entre
    z_corte y z_hasta (medio muro). franja = (z0, z1, "#hex"). acento = dict(eje='y'|'x', mayor=bool, valor=coordenada,
    png=..., tile=3.0, color=...) -> papel tapiz con estampado en esa pared (u = la otra coordenada).
    franjas = [(z0, z1, "#hex"), ...] (lambrin, cenefa). arriba=None no pinta arriba. 'clave' permite varias pasadas."""
    if m.get(clave):
        return m
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    base_in = bs.inputs["Base Color"]
    if base_in.links:
        actual = base_in.links[0].from_socket
    else:
        rgbn = nt.nodes.new("ShaderNodeRGB"); rgbn.outputs[0].default_value = tuple(base_in.default_value); actual = rgbn.outputs[0]
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])

    def mezcla(cond_socket, a_socket, b_color=None, b_socket=None):
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
        nt.links.new(cond_socket, _sock(mx.inputs, "Factor_Float"))
        nt.links.new(a_socket, _sock(mx.inputs, "A_Color"))
        if b_socket is not None:
            nt.links.new(b_socket, _sock(mx.inputs, "B_Color"))
        else:
            _sock(mx.inputs, "B_Color").default_value = _rgb(b_color)
        return _sock(mx.outputs, "Result_Color")

    def compara(sock, valor, menor=False):
        c = nt.nodes.new("ShaderNodeMath"); c.operation = 'LESS_THAN' if menor else 'GREATER_THAN'
        nt.links.new(sock, c.inputs[0]); c.inputs[1].default_value = valor
        return c.outputs[0]

    def y_logico(a, b):
        c = nt.nodes.new("ShaderNodeMath"); c.operation = 'MULTIPLY'
        nt.links.new(a, c.inputs[0]); nt.links.new(b, c.inputs[1])
        return c.outputs[0]

    arriba_z = compara(sep.outputs["Z"], z_corte)
    sal = mezcla(arriba_z, actual, arriba) if arriba else actual
    for z0, z1, cf in franjas:
        sal = mezcla(y_logico(compara(sep.outputs["Z"], z0), compara(sep.outputs["Z"], z1, menor=True)), sal, cf)
    if abajo2:
        sal = mezcla(y_logico(arriba_z, compara(sep.outputs["Z"], abajo2[0], menor=True)), sal, abajo2[1])
    if franja:
        sal = mezcla(y_logico(compara(sep.outputs["Z"], franja[0]), compara(sep.outputs["Z"], franja[1], menor=True)), sal, franja[2])
    if acento:
        eje = acento["eje"].upper()
        cond = y_logico(arriba_z, compara(sep.outputs[eje], acento["valor"], menor=not acento.get("mayor", True)))
        if acento.get("png"):
            u = sep.outputs["X" if eje == "Y" else "Y"]
            cmb = nt.nodes.new("ShaderNodeCombineXYZ")
            for k, s in (("X", u), ("Y", sep.outputs["Z"])):
                dv = nt.nodes.new("ShaderNodeMath"); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = acento.get("tile", 3.0)
                nt.links.new(s, dv.inputs[0]); nt.links.new(dv.outputs[0], cmb.inputs[k])
            im = nt.nodes.new("ShaderNodeTexImage")
            png = acento["png"]
            im.image = bpy.data.images.load(png if os.path.isabs(png) else os.path.join(TEX, png), check_existing=True)
            nt.links.new(cmb.outputs[0], im.inputs["Vector"])
            sal = mezcla(cond, sal, b_socket=im.outputs["Color"])
        else:
            sal = mezcla(cond, sal, acento["color"])
    nt.links.new(sal, base_in)
    m[clave] = True
    return m


def piso_tablas(m, color1="#e9c6a0", color2="#dfb98f", junta="#b48a64", largo=4.0, ancho=0.8):
    """convierte un material de piso en duela de madera (tablas con junta y relieve leve), en coordenadas del mundo."""
    if m.get("duela"):
        return m
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Color1"].default_value = _rgb(color1); br.inputs["Color2"].default_value = _rgb(color2)
    br.inputs["Mortar"].default_value = _rgb(junta)
    br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.025; br.inputs["Mortar Smooth"].default_value = 0.2
    br.inputs["Brick Width"].default_value = largo; br.inputs["Row Height"].default_value = ancho
    br.offset = 0.5; br.squash_frequency = 1
    nt.links.new(geo.outputs["Position"], br.inputs["Vector"])
    for l in list(bs.inputs["Base Color"].links):
        nt.links.remove(l)
    nt.links.new(br.outputs["Color"], bs.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.02
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1]); nt.links.new(inv.outputs[0], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.55
    m.diffuse_color = _rgb(color1)
    m["duela"] = True
    return m


# ------------------------------------------------------------------ cama con cobija de verdad
def _sabana(nombre, col, m, ancho, y_cabeza, y_pie, z_top, caida=0.85, rc=0.16, paso=0.09, cabeza_cae=False,
            arrugas=0.02, esponja=0.04, semilla=0.0):
    """cobija que CUBRE un colchon (rectangulo ancho x [y_pie, y_cabeza] a la altura z_top) y CAE por los lados y el
    pie con orilla redondeada, pliegues y arruguitas. UV = coordenadas planas de la tela (unidades) -> el estampado no
    se estira. Devuelve el objeto (con grosor y suavizado)."""
    a = ancho / 2
    x0, x1 = -a - caida, a + caida
    y0, y1 = y_pie - caida, (y_cabeza + caida if cabeza_cae else y_cabeza)
    nx, ny = int((x1 - x0) / paso) + 1, int((y1 - y0) / paso) + 1
    me = bpy.data.meshes.new(nombre)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid, uvs = [], []
    ym, yl = (y_pie + y_cabeza) / 2, max(0.01, (y_cabeza - y_pie) / 2)
    for j in range(ny + 1):
        sy = y0 + (y1 - y0) * j / ny
        fila, fu = [], []
        for i in range(nx + 1):
            sx = x0 + (x1 - x0) * i / nx
            cx, cy = max(-a, min(a, sx)), max(y_pie, min(y_cabeza, sy))
            dx, dy = sx - cx, sy - cy
            d = math.hypot(dx, dy)
            arr = arrugas * math.sin(sx * 3.1 + sy * 1.7 + semilla) * math.sin(sy * 2.3 - sx * 0.7)
            bulto = esponja * max(0.0, 1 - (abs(cx) / a) ** 4) * max(0.0, 1 - ((cy - ym) / yl) ** 6)
            if d < 1e-6:
                v = Vector((sx, sy, z_top + arr + bulto))
            else:
                n = Vector((dx / d, dy / d, 0))
                lim = rc * math.pi / 2
                if d <= lim:
                    th = d / rc
                    h, z = rc * math.sin(th), z_top - rc * (1 - math.cos(th))
                else:
                    cae = d - lim
                    h, z = rc + 0.06 * cae, z_top - rc - cae
                tcoord = cy if abs(n.x) > abs(n.y) else cx
                pl = 0.06 * min(1.0, max(0.0, d - lim) / 0.4) * math.sin(tcoord * 5.2 + semilla)
                v = Vector((cx, cy, z + bulto * 0.0)) + n * (h + pl)
            fila.append(bm.verts.new(v)); fu.append((sx, sy))
        grid.append(fila); uvs.append(fu)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for lp, (jj, ii) in zip(f.loops, ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i))):
                lp[uvl].uv = uvs[jj][ii]
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    for pl in me.polygons:
        pl.use_smooth = True
    centro = min(me.polygons, key=lambda pl: (pl.center.x) ** 2 + (pl.center.y - ym) ** 2)
    if centro.normal.z < 0:
        me.flip_normals()
    so = o.modifiers.new("Grosor", 'SOLIDIFY'); so.thickness = 0.035; so.offset = -1.0
    return o


def cama(nombre, col, ancho=4.2, largo=5.8, estilo="gatita", cobija="tela_estrellas_rosa.png", tile=2.2,
         color_cabecera="#f6a5c8", color_madera=BLANCO, funda=None, pie=None, color_doblez="#ffffff", doblez=None, tam=1.0):
    """CAMA con cobija de verdad: cabecera (estilo 'gatita' = acolchada con orejitas de gato y botones; 'simple' =
    de madera con arco), base con patitas, colchon, COBIJA de tela con estampado que cae por los lados con pliegues,
    doblez de sabana a la cabeza, almohadas esponjadas (funda = PNG opcional) y pie de cama (pie = PNG opcional).
    Origen: base, centro de la CABECERA (va contra la pared); la cama se extiende hacia -Y.
    Colchon a ~1,45 de alto (un personaje acostado va a z ~1,5). Devuelve la base; lo demas son hijos."""
    p = P(nombre, col)
    mad, cab = mat("CT_Mueble_" + color_madera.lstrip("#"), color_madera, 0.45), mat("CT_Cabecera_" + color_cabecera.lstrip("#"), color_cabecera, 0.85)
    W, L = ancho, largo
    for x in (-W / 2 + 0.2, W / 2 - 0.2):                                          # patitas
        for y in (-0.3, -L + 0.2):
            p.cono((x, y, 0), 0.09, 0.07, 0.28, mad, segs=8)
    p.caja((0, -L / 2, 0.55), (W + 0.1, L - 0.1, 0.55), mad)                     # base
    a = W / 2 + 0.1
    if estilo == "gatita":
        arco = [((-a + 0.95) + (2 * a - 1.9) * i / 10, 3.25 + 0.22 * math.sin(math.pi * i / 10)) for i in range(11)]
        pts = [(-a, 0.28), (a, 0.28), (a, 3.05), (a - 0.22, 3.95)] + arco[::-1] + [(-a + 0.22, 3.95), (-a, 3.05)]
        prisma(p, pts, 0.32, cab)
        rosa_osc = mat("CT_Cabecera_Oreja", "#ff7fae", 0.85)
        for s in (-1, 1):
            prisma(p, [(s * (a - 0.32), 3.2), (s * (a - 0.3), 3.68), (s * (a - 0.78), 3.3)], 0.36, rosa_osc)
        bt = mat("CT_Boton_Cabecera", "#ffd1e3", 0.6)
        for k in range(3):
            n = 5 if k % 2 == 0 else 4
            for i in range(n):
                x = (-W / 2 + 0.5) + (W - 1.0) * (i + (0.5 if k % 2 else 0)) / 4
                p.esfera((x, -0.34, 1.95 + 0.5 * k), 0.06, bt, segs=6)
    else:
        arco = [(-a + 2 * a * i / 12, 2.9 + 0.35 * math.sin(math.pi * i / 12)) for i in range(13)]
        prisma(p, [(-a, 0.28)] + arco + [(a, 0.28)], 0.22, cab)
        for x in (-a, a):
            p.cono((x, -0.11, 0.28), 0.13, 0.13, 2.75, cab, segs=10)
            p.esfera((x, -0.11, 3.08), 0.16, cab, segs=10)
    p.caja((0, -L + 0.05, 0.75), (W + 0.1, 0.18, 0.95), mad if estilo == "gatita" else cab)   # piecera
    base = _acabado(p.fin(), bisel=0.03); contorno(base, 0.02)
    # colchon
    pc = P(nombre + "_Colchon", col)
    pc.caja((0, -L / 2 - 0.12, 1.13), (W - 0.12, L - 0.42, 0.56), mat("CT_Colchon", "#f4f1ec", 0.8))
    colchon = _acabado(pc.fin(), bisel=0.08); colchon.modifiers["Bisel"].segments = 3; colchon.parent = base
    z_top = 1.42
    am = (W - 0.12) / 2 + 0.03
    y_cab, y_pie = -1.5, -L + 0.08
    # cobija
    if cobija:
        mcob = material_tela("CT_Cobija_" + os.path.splitext(os.path.basename(cobija))[0], cobija, tile=tile, acolchado=0.35)
    else:
        mcob = material_tela("CT_Cobija_Lisa_" + color_cabecera.lstrip("#"), None, color_cabecera, acolchado=0.35)
    cob = _sabana(nombre + "_Cobija", col, mcob, 2 * am, y_cab, y_pie, z_top, caida=0.82, semilla=len(nombre))
    cob.parent = base
    # doblez de la sabana a la cabeza
    if doblez:
        mdob = material_tela("CT_Sabana_" + os.path.splitext(os.path.basename(doblez))[0], doblez, tile=1.2, relieve=0.12)
    else:
        mdob = material_tela("CT_Sabana_" + color_doblez.lstrip("#"), None, color_doblez, relieve=0.12)
    dob = _sabana(nombre + "_Doblez", col, mdob, 2 * am + 0.06, y_cab, y_cab - 0.7, z_top + 0.075, caida=0.42, rc=0.19,
                  arrugas=0.012, esponja=0.0)
    dob.parent = base
    # pie de cama (otra tela)
    if pie:
        mpie = material_tela("CT_PieCama_" + os.path.splitext(os.path.basename(pie))[0], pie, tile=1.6, relieve=0.15)
        pc2 = _sabana(nombre + "_PieCama", col, mpie, 2 * am + 0.07, y_pie + 1.1, y_pie, z_top + 0.1, caida=0.6, rc=0.2,
                      arrugas=0.012, esponja=0.0)
        pc2.parent = base
    # almohadas
    if funda:
        mfun = material_tela("CT_Funda_" + os.path.splitext(os.path.basename(funda))[0], funda, tile=1.0, relieve=0.1)
    else:
        mfun = material_tela("CT_Funda_Blanca", None, "#ffffff", relieve=0.1)
    lados = (-1, 1) if W > 3.0 else (0,)
    for s in lados:
        pa = P(nombre + "_Almohada" + {-1: "I", 1: "D", 0: ""}[s], col)
        wa = (W - 0.55) / 2 if s else W - 0.7
        pa.caja((0, 0, 0), (wa, 0.95, 0.42), mfun)
        alm = pa.fin()
        uvl = alm.data.uv_layers.new(name="UVMap")
        for lp in alm.data.loops:
            co = alm.data.vertices[lp.vertex_index].co
            uvl.data[lp.index].uv = (co.x, co.z + co.y)
        bev = alm.modifiers.new("Bisel", 'BEVEL'); bev.width = 0.13; bev.segments = 2
        sub = alm.modifiers.new("Esponja", 'SUBSURF'); sub.levels = 2; sub.render_levels = 2
        for pl in alm.data.polygons:
            pl.use_smooth = True
        alm.parent = base
        alm.location = (s * (W - 0.55) / 4 if s else 0, -0.85, z_top + 0.3)
        alm.rotation_euler = (math.radians(-18), 0, 0)
    base.scale = (tam,) * 3
    return base


def candado_corazon(nombre, col, color="#ff4f8b", tam=1.0):
    """candado con cuerpo de CORAZON (rosa fuerte), ojo de la llave y arco gris. Para "nuestras sillas" (EP005).
    Origen en la base; el frente mira a -Y. Alto ~0,85 * tam."""
    from objetos_cartoon import _arco
    p = P(nombre, col)
    c, gris, neg = mat("CT_Candado_Corazon_" + color.lstrip("#"), color, 0.35), mat("CT_Metal", "#9aa3ad", 0.3), mat("CT_Negro", "#151515", 0.5)
    prisma(p, [(x, z + 0.3) for x, z in pts_corazon(0.3)], 0.2, c, _T(0, 0.1, 0))
    p.esfera((0, -0.115, 0.33), 0.045, neg, segs=8)
    p.caja((0, -0.115, 0.26), (0.03, 0.012, 0.09), neg)
    for x in (-0.15, 0.15):
        p.cono((x, 0, 0.5), 0.032, 0.032, 0.08, gris, segs=8)
    _arco(p, (0, 0, 0.58), 0.15, gris, grosor=0.032)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.02); o.scale = (tam,) * 3
    return o


# ------------------------------------------------------------------ planta baja: cocina, comedor y sala (EP005, 2026-11-08)
def _uv_caja(o, escala=1.0):
    """UV por caras (proyeccion de caja en unidades): la tela o el azulejo no se estiran."""
    me = o.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for pl in me.polygons:
        n = pl.normal
        a = max(range(3), key=lambda i: abs(n[i]))
        u, v = {0: (1, 2), 1: (0, 2), 2: (0, 1)}[a]
        for li in pl.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (co[u] * escala, co[v] * escala)
    return o


def _esponjar(o, bisel=0.12, sub=1):
    """orillas redondas y suaves (cojines, sofa)."""
    b = o.modifiers.new("Bisel", 'BEVEL'); b.width = bisel; b.segments = 2
    if sub:
        s = o.modifiers.new("Esponja", 'SUBSURF'); s.levels = sub; s.render_levels = sub
    for pl in o.data.polygons:
        pl.use_smooth = True
    return o


def _tubo(p, pts, r, m, segs=8, cerrar=False):
    """tubo que une puntos (patas inclinadas, llaves de agua, asas)."""
    pts = [Vector(q) for q in pts]
    if cerrar:
        pts.append(pts[0])
    for a, b in zip(pts, pts[1:]):
        d = b - a
        L = d.length
        if L < 1e-5:
            continue
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        res = bmesh.ops.create_cone(p.bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=L,
                                    matrix=p.M @ Matrix.Translation(a) @ rot @ Matrix.Translation((0, 0, L / 2)))
        p._marcar(res, m)
    return p


def _hijo(padre, o, loc, rotz=0.0):
    o.parent = padre; o.location = loc; o.rotation_euler = (0, 0, math.radians(rotz))
    return o


def material_azulejo(nombre, color="#eef7f5", junta="#c3d3d0", ancho=0.6, alto=0.3, desfase=0.5, plano="xz"):
    """azulejo brillante tipo metro (ladrillo chico con junta) en coordenadas del objeto (plano xz = pared de frente)."""
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre); m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[plano[0].upper()], cmb.inputs["X"]); nt.links.new(sep.outputs[plano[1].upper()], cmb.inputs["Y"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    c1 = _rgb(color); c2 = tuple(min(1.0, v * 0.93) for v in c1[:3]) + (1,)
    br.inputs["Color1"].default_value = c1; br.inputs["Color2"].default_value = c2; br.inputs["Mortar"].default_value = _rgb(junta)
    br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.018; br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Brick Width"].default_value = ancho; br.inputs["Row Height"].default_value = alto
    br.offset = desfase; br.squash_frequency = 1
    nt.links.new(cmb.outputs[0], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], bs.inputs["Base Color"])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(br.outputs["Fac"], inv.inputs[1])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.02
    nt.links.new(inv.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.22
    m.diffuse_color = c1
    return m


def frutero(nombre, col, color=BLANCO, tam=1.0):
    """frutero con manzanas, naranjas y platanos. Origen en la base. Ancho ~0,9."""
    p = P(nombre, col)
    p.esfera((0, 0, 0.24), 0.45, mat("CT_Frutero_" + color.lstrip("#"), color, 0.3), esc=(1, 1, 0.5), segs=18)
    arriba = [v for v in p.bm.verts if v.co.z > 0.24 + 0.001]
    bmesh.ops.delete(p.bm, geom=arriba, context='VERTS')
    p.cono((0, 0, 0), 0.18, 0.15, 0.04, mat("CT_Frutero_" + color.lstrip("#"), color, 0.3), segs=14)
    roja, nar, ama, ver = mat("CT_Manzana", "#d9333a", 0.35), mat("CT_Naranja", "#ff9a2e", 0.5), mat("CT_Platano", "#f6d34a", 0.5), mat("CT_Rabito", "#4a8f3a", 0.6)
    for (x, y, z), m in (((-0.15, -0.08, 0.32), roja), ((0.14, -0.12, 0.31), nar), ((0.0, 0.14, 0.33), roja), ((0.2, 0.12, 0.34), nar), ((-0.18, 0.15, 0.36), roja)):
        p.esfera((x, y, z), 0.14, m, segs=10)
        p.cono((x, y, z + 0.12), 0.012, 0.012, 0.07, ver, segs=5)
    for k in range(3):
        p.M = Matrix.Translation((-0.02 + 0.06 * k, -0.02, 0.46)) @ Matrix.Rotation(math.radians(-25 + 18 * k), 4, 'Z') @ Matrix.Rotation(math.radians(70), 4, 'Y')
        p.esfera((0, 0, 0), 0.06, ama, esc=(1, 1, 4.2), segs=8)
    p.M = Matrix.Identity(4)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def tetera(nombre, col, color="#e85d75", tam=1.0):
    """tetera de caricatura (cuerpo redondo, pico, asa, tapa). Origen en la base; el pico mira a +X."""
    p = P(nombre, col)
    c, neg = mat("CT_Tetera_" + color.lstrip("#"), color, 0.3), mat("CT_Negro", "#151515", 0.5)
    p.esfera((0, 0, 0.26), 0.3, c, esc=(1, 1, 0.85), segs=16)
    p.cono((0, 0, 0.48), 0.16, 0.1, 0.06, c, segs=12)
    p.esfera((0, 0, 0.57), 0.05, neg, segs=8)
    p.cono((0.24, 0, 0.2), 0.07, 0.035, 0.32, c, segs=8, rot=('Y', 55))
    _tubo(p, [(-0.24, 0, 0.42), (-0.36, 0, 0.5), (-0.42, 0, 0.36), (-0.36, 0, 0.2), (-0.26, 0, 0.16)], 0.03, neg)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015); o.scale = (tam,) * 3
    return o


def frascos(nombre, col, colores=("#f2c230", "#d9433a", "#8a5a2b"), tam=1.0):
    """tres frascos de vidrio con contenido de colores y tapa de madera, en fila (a lo largo de X). Origen en la base."""
    p = P(nombre, col)
    vid, tapa = mat("CT_Vidrio_Frasco", "#dfeef2", 0.08), mat("CT_Tapa_Madera", "#b07a4a", 0.6)
    for i, (c, h) in enumerate(zip(colores, (0.5, 0.42, 0.36))):
        x = (i - 1) * 0.34
        p.cono((x, 0, 0), 0.14, 0.14, h, vid, segs=12)
        p.cono((x, 0, 0.02), 0.125, 0.125, h * 0.62, mat("CT_Contenido_" + c.lstrip("#"), c, 0.8), segs=12)
        p.cono((x, 0, h), 0.15, 0.15, 0.08, tapa, segs=12)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def florero(nombre, col, color="#7fb3dd", flores=("#ff6f91", "#ffd84a", "#ffffff", "#c7a2ff", "#ff9f40"), tam=1.0):
    """florero con 5 flores de colores y hojas. Origen en la base. Alto ~1,1."""
    p = P(nombre, col)
    v, tallo, cen = mat("CT_Florero_" + color.lstrip("#"), color, 0.3), mat("CT_Tallo", "#4caf6a", 0.7), mat("CT_Centro_Flor", "#f2c230", 0.6)
    p.esfera((0, 0, 0.22), 0.2, v, esc=(1, 1, 1.15), segs=14)
    p.cono((0, 0, 0.38), 0.1, 0.13, 0.18, v, segs=12)
    puntas = [(0, 0, 1.05), (0.25, 0.05, 0.92), (-0.24, 0.08, 0.9), (0.1, -0.22, 0.86), (-0.08, 0.22, 0.96)]
    for (x, y, z), c in zip(puntas, flores):
        _tubo(p, [(0, 0, 0.4), (x * 0.5, y * 0.5, z * 0.7), (x, y, z)], 0.018, tallo, segs=5)
        pet = mat("CT_Petalo_" + c.lstrip("#"), c, 0.7)
        for k in range(6):
            a = 2 * math.pi * k / 6
            p.esfera((x + 0.075 * math.cos(a), y + 0.075 * math.sin(a), z), 0.055, pet, esc=(1, 1, 0.5), segs=8)
        p.esfera((x, y, z + 0.015), 0.04, cen, segs=6)
    for a in (40, 200):
        p.esfera((0.12 * math.cos(math.radians(a)), 0.12 * math.sin(math.radians(a)), 0.62), 0.09, tallo, esc=(1.8, 0.5, 0.6), segs=8)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.012); o.scale = (tam,) * 3
    return o


def cocina_integral(nombre, col, largo=8.4, color="#9fd3c7", cubierta="#f1ede6", alacena=BLANCO, refri=1,
                    color_refri="#e8edf1", azulejo_color="#eef7f5", junta="#c3d3d0", tetera_color="#e85d75", cositas=True):
    """COCINA INTEGRAL contra la pared: gabinetes con puerta y cajon (estilo con marco) y manijas doradas, cubierta,
    TARJA con llave cuello de ganso, ESTUFA (parrillas, perillas, horno con ventana) y CAMPANA, alacenas, AZULEJO tipo
    metro entre la cubierta y las alacenas y REFRI de dos puertas (refri=+1 al final en +X, -1 en -X, 0 sin refri) con
    un dibujito pegado. cositas=True agrega tetera, frascos, tabla de picar y macetita.
    Origen: base, centro de atras (contra la pared); frente -Y. Cubierta a 2,74; alacenas 4,6-6,9; techo ~7,5."""
    p = P(nombre, col)
    L, D, H = largo, 1.5, 2.6
    mc_, cub = mat("CT_Cocina_" + color.lstrip("#"), color, 0.5), mat("CT_Cubierta_" + cubierta.lstrip("#"), cubierta, 0.25)
    al, met = mat("CT_Alacena_" + alacena.lstrip("#"), alacena, 0.45), mat("CT_Metal_Cocina", "#b9c2cb", 0.25)
    neg, zoc, man = mat("CT_Vidrio_Negro", "#1d1f24", 0.12), mat("CT_Zoclo_Cocina", "#3b3b40", 0.6), mat("CT_Manija_Dorada", "#d8b45a", 0.3)
    AR = 1.9 if refri else 0.0
    x0, x1 = -L / 2, L / 2
    if refri > 0:
        x1 -= AR + 0.08
    elif refri < 0:
        x0 += AR + 0.08
    lm = x1 - x0
    xc = (x0 + x1) / 2
    p.caja((xc, -D / 2 + 0.1, 0.13), (lm - 0.1, D - 0.2, 0.26), zoc)
    p.caja((xc, -D / 2, 0.26 + (H - 0.26) / 2), (lm, D, H - 0.26), mc_)
    p.caja((xc, -(D + 0.12) / 2, H + 0.07), (lm + 0.04, D + 0.12, 0.14), cub)
    n = max(3, round(lm / 1.25))
    w = lm / n
    ie = min(n - 1, int(n * 0.62))
    it = 1 if n > 3 else 0
    if it == ie:
        it = max(0, ie - 2)
    zA0, zA1, DA = 4.6, 6.9, 0.85
    for i in range(n):
        cx = x0 + w * (i + 0.5)
        if i == ie:                                                              # estufa con horno
            p.caja((cx, -D - 0.03, 1.15), (w - 0.12, 0.06, 1.6), met)
            p.caja((cx, -D - 0.065, 1.05), (w - 0.5, 0.02, 0.85), neg)
            _tubo(p, [(cx - (w - 0.45) / 2, -D - 0.2, 1.75), (cx + (w - 0.45) / 2, -D - 0.2, 1.75)], 0.035, met)
            for k in range(4):
                p.cono((cx - 0.42 + k * 0.28, -D - 0.06, 2.25), 0.07, 0.07, 0.08, neg, segs=10, rot=('X', 90))
            p.caja((cx, -D / 2 - 0.05, H + 0.15), (w - 0.15, D - 0.35, 0.02), neg)
            for dx in (-0.27, 0.27):
                for dy in (-0.25, 0.25):
                    p.cono((cx + dx, -D / 2 - 0.05 + dy, H + 0.16), 0.17, 0.17, 0.015, met, segs=16)
                    p.cono((cx + dx, -D / 2 - 0.05 + dy, H + 0.165), 0.08, 0.08, 0.02, neg, segs=12)
            p.cono((cx, -0.6, zA0 + 0.3), 0.85, 0.28, 0.9, met, segs=4, rot=('Z', 45))   # campana
            p.caja((cx, -0.32, (zA0 + 1.2 + 7.55) / 2), (0.55, 0.5, 7.55 - zA0 - 1.2), met)
            continue
        p.caja((cx, -D - 0.02, 2.2), (w - 0.1, 0.04, 0.5), mc_)                   # cajon
        p.caja((cx, -D - 0.065, 2.22), (0.5, 0.05, 0.06), man)
        p.caja((cx, -D - 0.02, 1.08), (w - 0.1, 0.04, 1.55), mc_)                 # puerta con marco claro
        for dx, dz, sx, sz in ((0, 1.78, w - 0.3, 0.07), (0, 0.38, w - 0.3, 0.07), (-(w - 0.3) / 2, 1.08, 0.07, 1.4), ((w - 0.3) / 2, 1.08, 0.07, 1.4)):
            p.caja((cx + dx, -D - 0.045, dz), (sx, 0.03, sz), al)
        p.caja((cx + w * 0.33, -D - 0.075, 1.4), (0.06, 0.05, 0.45), man)
        if i == it:                                                              # tarja con llave
            p.caja((cx, -D / 2 - 0.05, H + 0.145), (w - 0.2, D - 0.45, 0.02), met)
            p.caja((cx, -D / 2 - 0.05, H + 0.15), (w - 0.4, D - 0.65, 0.03), mat("CT_Tarja_Fondo", "#5f6871", 0.3))
            arco = [(cx, -0.25, H + 0.14), (cx, -0.25, H + 0.75)] + [(cx, -0.45 - 0.2 * math.cos(math.radians(a)), H + 0.75 + 0.2 * math.sin(math.radians(a))) for a in range(0, 181, 30)] + [(cx, -0.65, H + 0.55)]
            _tubo(p, arco, 0.04, met)
            p.cono((cx + 0.22, -0.25, H + 0.14), 0.05, 0.05, 0.22, met, segs=8)
        # alacena de arriba
        p.caja((cx, -DA / 2, (zA0 + zA1) / 2), (w, DA, zA1 - zA0), al)
        p.caja((cx, -DA - 0.02, (zA0 + zA1) / 2), (w - 0.1, 0.04, zA1 - zA0 - 0.1), al)
        for dx, dz, sx, sz in ((0, zA1 - 0.2, w - 0.3, 0.06), (0, zA0 + 0.2, w - 0.3, 0.06), (-(w - 0.3) / 2, (zA0 + zA1) / 2, 0.06, zA1 - zA0 - 0.4), ((w - 0.3) / 2, (zA0 + zA1) / 2, 0.06, zA1 - zA0 - 0.4)):
            p.caja((cx + dx, -DA - 0.045, dz), (sx, 0.03, sz), mc_)
        p.caja((cx + w * 0.33, -DA - 0.075, zA0 + 0.35), (0.06, 0.05, 0.4), man)
    # azulejo entre cubierta y alacenas
    p.caja((xc, -0.03, (H + 0.14 + zA0) / 2), (lm, 0.06, zA0 - H - 0.14), material_azulejo("CT_Azulejo_" + azulejo_color.lstrip("#"), azulejo_color, junta))
    # refri
    if refri:
        fx = (L / 2 - AR / 2) if refri > 0 else (-L / 2 + AR / 2)
        rf = mat("CT_Refri_" + color_refri.lstrip("#"), color_refri, 0.3)
        p.caja((fx, -0.85, 2.95), (AR, 1.7, 5.9), rf)
        p.caja((fx, -1.715, 4.15), (AR - 0.04, 0.03, 0.04), neg)
        s = -1 if refri > 0 else 1
        p.caja((fx + s * (AR / 2 - 0.22), -1.79, 4.95), (0.08, 0.1, 0.95), met)
        p.caja((fx + s * (AR / 2 - 0.22), -1.79, 3.2), (0.08, 0.1, 1.5), met)
        papel = mat("CT_Papel_Dibujo", "#fff8e8", 0.8)
        p.caja((fx - s * 0.25, -1.71, 2.9), (0.75, 0.012, 0.95), papel)
        prisma(p, pts_corazon(0.2), 0.012, mat("CT_Dib_Corazon", "#ff4f8b", 0.6), _T(fx - s * 0.25, -1.716, 2.95))
        for k, c in enumerate(("#ff5a5a", "#5aa7ff", "#ffd84a")):
            p.esfera((fx - s * 0.25 + (k - 1) * 0.42, -1.72, 3.42 + 0.04 * k), 0.07, mat("CT_Iman_" + c.lstrip("#"), c, 0.4), esc=(1, 0.5, 1), segs=8)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.02)
    if cositas:
        cxe = x0 + w * (ie + 0.5)
        _hijo(o, tetera(nombre + "_Tetera", col, color=tetera_color), (cxe + 0.27, -D / 2 + 0.2, H + 0.17), 20)
        _hijo(o, frascos(nombre + "_Frascos", col), (x0 + 0.65, -0.35, H + 0.14))
        cxt = x0 + w * (it + 1.5) if it + 1 < n and it + 1 != ie else x0 + w * 0.5
        pt = P(nombre + "_Tabla", col)
        pt.caja((0, 0, 0.03), (0.95, 0.6, 0.06), mat("CT_Tabla_Picar", "#c8935a", 0.7))
        pt.esfera((0.15, 0.05, 0.12), 0.1, mat("CT_Jitomate", "#e0402f", 0.4), segs=8)
        pt.esfera((-0.2, -0.05, 0.1), 0.07, mat("CT_Pepino", "#4caf6a", 0.6), esc=(2.2, 1, 1), segs=8)
        tb = _acabado(pt.fin(), bisel=0.01); contorno(tb, 0.012)
        _hijo(o, tb, (cxt, -0.8, H + 0.14), 8)
        _hijo(o, macetita(nombre + "_Hierbas", col, color="#d9774a"), (x1 - 0.45, -0.4, H + 0.14))
    return o


def isla_cocina(nombre, col, largo=4.0, ancho=1.7, alto=3.0, color="#9fd3c7", cubierta="#f1ede6", vuelo=0.5, fruta=True):
    """ISLA / barra de cocina. Del lado -Y tiene vuelo para sentarse (bancos) y tablitas verticales; del lado +Y,
    puertas. Origen en la base, al centro."""
    p = P(nombre, col)
    c, cub = mat("CT_Cocina_" + color.lstrip("#"), color, 0.5), mat("CT_Cubierta_" + cubierta.lstrip("#"), cubierta, 0.25)
    al, zoc, man = mat("CT_Alacena_" + BLANCO.lstrip("#"), BLANCO, 0.45), mat("CT_Zoclo_Cocina", "#3b3b40", 0.6), mat("CT_Manija_Dorada", "#d8b45a", 0.3)
    yb, fb = vuelo / 2, ancho - vuelo
    p.caja((0, yb, 0.13), (largo - 0.2, fb - 0.2, 0.26), zoc)
    p.caja((0, yb, 0.26 + (alto - 0.4) / 2), (largo, fb, alto - 0.4), c)
    p.caja((0, 0, alto - 0.07), (largo + 0.1, ancho, 0.14), cub)
    k = max(6, int(largo / 0.32))
    for i in range(k):
        p.caja((-largo / 2 + largo * (i + 0.5) / k, yb - fb / 2 - 0.015, 0.26 + (alto - 0.4) / 2), (largo / k - 0.05, 0.03, alto - 0.6), al)
    m = max(2, round(largo / 1.3))
    for i in range(m):
        cx = -largo / 2 + largo * (i + 0.5) / m
        p.caja((cx, yb + fb / 2 + 0.02, 1.3), (largo / m - 0.12, 0.04, 1.9), c)
        p.caja((cx + largo / m * 0.3, yb + fb / 2 + 0.06, 1.6), (0.06, 0.05, 0.45), man)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.02)
    if fruta:
        _hijo(o, frutero(nombre + "_Frutero", col), (largo * 0.18, 0.05, alto))
    return o


def taburete(nombre, col, color="#e85d75", alto=2.0, madera="#b07a4a"):
    """banco alto de barra: patas inclinadas, aro para los pies y cojin redondo. Origen en la base."""
    p = P(nombre, col)
    md, c = mat("CT_Madera_" + madera.lstrip("#"), madera, 0.55), mat("CT_Cojin_" + color.lstrip("#"), color, 0.9)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        _tubo(p, [(0.42 * math.cos(a), 0.42 * math.sin(a), 0), (0.27 * math.cos(a), 0.27 * math.sin(a), alto - 0.12)], 0.05, md)
    aro = [(0.36 * math.cos(2 * math.pi * k / 12), 0.36 * math.sin(2 * math.pi * k / 12), 0.65) for k in range(12)]
    _tubo(p, aro, 0.03, md, cerrar=True)
    p.cono((0, 0, alto - 0.14), 0.47, 0.47, 0.12, md, segs=20)
    p.esfera((0, 0, alto + 0.0), 0.47, c, esc=(1, 1, 0.3), segs=18)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.018)
    return o


def mesa_comedor(nombre, col, largo=4.4, ancho=2.8, alto=2.9, madera="#a8693f", mantel="mantel_cuadros_rojo.png",
                 platos=4, flores=True, color_florero="#7fb3dd"):
    """MESA DE COMEDOR (lo largo en Y) con patas torneadas, MANTEL DE TELA que cae por los 4 lados con pliegues,
    platos con vaso para 'platos' personas (2 por lado largo) y florero. Origen en la base, al centro."""
    p = P(nombre, col)
    m = mat("CT_Madera_" + madera.lstrip("#"), madera, 0.5)
    p.caja((0, 0, alto - 0.08), (ancho, largo, 0.16), m)
    p.caja((0, 0, alto - 0.3), (ancho - 0.3, largo - 0.3, 0.3), m)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (ancho / 2 - 0.25), sy * (largo / 2 - 0.25)
            p.cono((x, y, 0), 0.1, 0.13, alto - 0.3, m, segs=10)
            p.esfera((x, y, (alto - 0.3) * 0.55), 0.17, m, segs=10)
    o = _acabado(p.fin(), bisel=0.02); contorno(o, 0.02)
    z = alto + 0.005
    if mantel:
        mm = material_tela("CT_Mantel_" + os.path.splitext(os.path.basename(mantel))[0], mantel, tile=1.3, relieve=0.12)
        t = _sabana(nombre + "_Mantel", col, mm, ancho + 0.04, largo / 2 + 0.02, -largo / 2 - 0.02, z, caida=0.7, rc=0.05,
                    cabeza_cae=True, arrugas=0.004, esponja=0.0, semilla=1.3)
        t.parent = o
        z += 0.045
    if platos:
        pv = P(nombre + "_Vajilla", col)
        bl, vaso, serv = mat("CT_Plato", "#ffffff", 0.25), mat("CT_Vaso", "#cfe8f2", 0.08), mat("CT_Servilleta", "#ffd1e3", 0.9)
        for sx in (-1, 1):
            for sy in ((-1, 1) if platos >= 4 else (0,)):
                x, y = sx * (ancho / 2 - 0.5), sy * largo * 0.25
                pv.cono((x, y, z), 0.32, 0.4, 0.05, bl, segs=20)
                pv.cono((x, y, z + 0.05), 0.24, 0.24, 0.005, mat("CT_Plato_Centro", "#f1ede6", 0.3), segs=20)
                pv.cono((x - sx * 0.05, y + 0.52, z), 0.08, 0.1, 0.34, vaso, segs=10)
                pv.caja((x, y - 0.52, z + 0.01), (0.34, 0.2, 0.02), serv)
        vj = _acabado(pv.fin(), bisel=0); contorno(vj, 0.012); vj.parent = o
    if flores:
        _hijo(o, florero(nombre + "_Florero", col, color=color_florero), (0, 0, z))
    return o


def silla_comedor(nombre, col, madera="#a8693f", cojin="#e85d75", tela=None):
    """silla de comedor de madera (respaldo de barrotes) con cojin esponjado (tela = PNG opcional). Origen en la base;
    quien se sienta mira a -Y. Asiento a 1,75."""
    p = P(nombre, col)
    m = mat("CT_Madera_" + madera.lstrip("#"), madera, 0.5)
    S = 1.75
    p.caja((0, 0, S - 0.08), (1.5, 1.5, 0.14), m)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.cono((sx * 0.62, sy * 0.62, 0), 0.07, 0.08, S - 0.12, m, segs=8)
    for sx in (-1, 1):
        p.caja((sx * 0.62, 0.68, S + 1.05), (0.13, 0.13, 2.1), m)
    p.caja((0, 0.68, S + 2.0), (1.42, 0.15, 0.32), m)
    for k in (-0.3, 0.0, 0.3):
        p.caja((k, 0.68, S + 1.2), (0.12, 0.08, 1.4), m)
    o = _acabado(p.fin(), bisel=0.015); contorno(o, 0.018)
    pc = P(nombre + "_Cojin", col)
    mt = material_tela("CT_Cojin_" + os.path.splitext(os.path.basename(tela))[0], tela, tile=1.0, relieve=0.15) if tela else material_tela("CT_CojinLiso_" + cojin.lstrip("#"), None, cojin, relieve=0.15)
    pc.caja((0, -0.04, S + 0.08), (1.36, 1.32, 0.2), mt)
    c = _uv_caja(_esponjar(pc.fin(), 0.07, 1)); c.parent = o
    return o


def _pieza_tela(nombre, col, mt, centro, tam, bisel=0.14, rot_x=0.0):
    p = P(nombre, col)
    p.caja((0, 0, 0), tam, mt)
    o = _uv_caja(_esponjar(p.fin(), bisel, 1))
    o.location = centro; o.rotation_euler = (math.radians(rot_x), 0, 0)
    return o


def sofa(nombre, col, ancho=5.4, fondo=2.1, color="#8fa7e8", tela=None, cojines=("tela_gatitas_lila.png", "tela_corazones_coral.png"),
         patas="#6b4a2f"):
    """SOFA acolchado: base, brazos y respaldo redondeados y suaves, cojines de asiento y de respaldo separados, dos
    cojines decorativos con estampado y patitas de madera. Origen en la base, al centro; el frente (donde uno se
    sienta) mira a -Y. Asiento a ~1,75. Devuelve la base; lo demas son hijos."""
    mt = material_tela("CT_Sofa_" + (os.path.splitext(os.path.basename(tela))[0] if tela else color.lstrip("#")), tela, color, tile=1.6, relieve=0.25)
    A, F = ancho, fondo
    pb = P(nombre, col)
    pb.caja((0, 0, 0.95), (A, F, 0.75), mt)
    for s in (-1, 1):
        pb.caja((s * (A / 2 - 0.32), 0, 1.6), (0.64, F, 2.05), mt)
    pb.caja((0, F / 2 - 0.3, 2.2), (A - 1.2, 0.6, 2.5), mt)
    base = _uv_caja(_esponjar(pb.fin(), 0.16, 1))
    pp = P(nombre + "_Patas", col)
    mp = mat("CT_Madera_" + patas.lstrip("#"), patas, 0.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pp.cono((sx * (A / 2 - 0.3), sy * (F / 2 - 0.25), 0), 0.07, 0.1, 0.6, mp, segs=8)
    pt = _acabado(pp.fin(), bisel=0); pt.parent = base
    n = 2 if A < 4.6 else 3
    ws = (A - 1.28) / n
    for i in range(n):
        x = -(A - 1.28) / 2 + ws * (i + 0.5)
        _pieza_tela(nombre + "_Asiento%d" % i, col, mt, (x, -0.22, 1.55), (ws - 0.05, F - 0.62, 0.48)).parent = base
        _pieza_tela(nombre + "_Respaldo%d" % i, col, mt, (x, F / 2 - 0.78, 2.5), (ws - 0.07, 0.45, 1.3), rot_x=-12).parent = base
    for k, png in enumerate(cojines[:2]):
        s = -1 if k == 0 else 1
        mc2 = material_tela("CT_CojinSofa_" + os.path.splitext(os.path.basename(png))[0], png, tile=0.9, relieve=0.12)
        cj = _pieza_tela(nombre + "_Cojin%d" % k, col, mc2, (s * (A / 2 - 1.05), F / 2 - 1.12, 2.2), (0.95, 0.3, 0.95), bisel=0.12, rot_x=-14)
        cj.rotation_euler.z = math.radians(-s * 12)
        cj.parent = base
    return base


def mueble_tele(nombre, col, ancho=4.2, color=BLANCO, madera="#b07a4a"):
    """mueble bajo con 3 puertas de madera y TELE plana encima (apagada: azul oscuro con un reflejo), con macetita y
    libros. Origen: base, centro de atras (contra la pared); frente -Y."""
    p = P(nombre, col)
    c, md = mat("CT_Mueble_" + color.lstrip("#"), color, 0.45), mat("CT_Madera_" + madera.lstrip("#"), madera, 0.5)
    neg, pant = mat("CT_Tele_Marco", "#141418", 0.4), mat("CT_Tele_Pantalla", "#1d2a3c", 0.08)
    man = mat("CT_Manija_Dorada", "#d8b45a", 0.3)
    D, H = 1.1, 1.5
    p.caja((0, -D / 2, 0.15 + H / 2), (ancho, D, H), c)
    for sx in (-1, 1):
        for y in (-0.2, -D + 0.2):
            p.cono((sx * (ancho / 2 - 0.2), y, 0), 0.06, 0.06, 0.15, md, segs=8)
    for k in (-1, 0, 1):
        p.caja((k * ancho / 3, -D - 0.02, 0.15 + H / 2), (ancho / 3 - 0.1, 0.04, H - 0.2), md)
        p.caja((k * ancho / 3, -D - 0.06, 0.15 + H * 0.75), (0.45, 0.05, 0.06), man)
    p.caja((0, -D / 2, H + 0.19), (ancho + 0.06, D + 0.04, 0.08), md)
    tw, th, zt = 3.5, 2.05, H + 0.23
    p.caja((0, -0.5, zt + 0.03), (0.9, 0.5, 0.06), neg)
    p.caja((0, -0.5, zt + 0.3), (0.16, 0.1, 0.5), neg)
    zc = zt + 0.5 + th / 2
    p.caja((0, -0.5, zc), (tw, 0.1, th), neg)
    p.caja((0, -0.556, zc), (tw - 0.14, 0.012, th - 0.14), pant)
    p.caja((-tw * 0.22, -0.565, zc + th * 0.1), (0.07, 0.01, th * 0.6), mat("CT_Brillo_Espejo", "#ffffff", 0.2, emit=0.3), rot=('Y', -35))
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.02)
    _hijo(o, macetita(nombre + "_Maceta", col, color="#d9774a"), (ancho / 2 - 0.35, -0.5, H + 0.23))
    _hijo(o, libros(nombre + "_Libros", col, n=4), (-ancho / 2 + 0.5, -0.5, H + 0.23))
    return o


def mesa_centro(nombre, col, r=1.0, alto=1.2, madera="#b07a4a"):
    """mesita de centro redonda (3 patas y repisa) con libros y una taza. Origen en la base."""
    p = P(nombre, col)
    m = mat("CT_Madera_" + madera.lstrip("#"), madera, 0.5)
    p.cono((0, 0, alto - 0.12), r, r, 0.12, m, segs=28)
    p.cono((0, 0, 0.35), r * 0.75, r * 0.75, 0.08, m, segs=24)
    for k in range(3):
        a = 2 * math.pi * k / 3
        p.cono((r * 0.7 * math.cos(a), r * 0.7 * math.sin(a), 0), 0.07, 0.07, alto - 0.12, m, segs=8)
    p.caja((-0.3, 0.1, alto + 0.05), (0.8, 0.6, 0.1), mat("CT_Libro_e85d75", "#e85d75", 0.6))
    p.caja((-0.28, 0.08, alto + 0.15), (0.7, 0.5, 0.1), mat("CT_Libro_7fb8e0", "#7fb8e0", 0.6))
    taza = mat("CT_Taza", "#ffd84a", 0.3)
    p.cono((0.4, -0.25, alto), 0.11, 0.11, 0.24, taza, segs=12)
    _tubo(p, [(0.51, -0.25, alto + 0.19), (0.6, -0.25, alto + 0.16), (0.6, -0.25, alto + 0.07), (0.51, -0.25, alto + 0.05)], 0.022, taza)
    o = _acabado(p.fin(), bisel=0.01); contorno(o, 0.018)
    return o


def lampara_pie(nombre, col, color="#f3e6cf", alto=4.6, luz=0.0):
    """lampara de pie (base, poste, pantalla de tela; el foco brilla debajo). Origen en la base."""
    p = P(nombre, col)
    met, c = mat("CT_Metal_Lampara", "#3b3b40", 0.4), mat("CT_Pantalla_" + color.lstrip("#"), color, 0.8)
    p.cono((0, 0, 0), 0.38, 0.42, 0.08, met, segs=18)
    p.cono((0, 0, 0.08), 0.03, 0.03, alto - 0.6, met, segs=8)
    p.esfera((0, 0, alto - 0.55), 0.12, emite("CT_Foco_Colgante", "#fff1c9", 1.2), segs=10)
    p.cono((0, 0, alto - 0.75), 0.56, 0.4, 0.75, c, segs=22)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.018)
    if luz:
        ld = bpy.data.lights.new(nombre + "_Luz", 'POINT'); ld.energy = luz; ld.color = (1.0, 0.85, 0.65)
        lo = bpy.data.objects.new(nombre + "_Luz", ld); col.objects.link(lo); lo.parent = o; lo.location = (0, 0, alto - 0.5)
    return o


def planta_grande(nombre, col, maceta="#d9a07a", alto=3.0, semilla=2):
    """planta grande de interior en maceta (hojas anchas que salen hacia afuera, dos verdes). Origen en la base."""
    import random
    rnd = random.Random(semilla)
    p = P(nombre, col)
    mm, tierra = mat("CT_Maceta_" + maceta.lstrip("#"), maceta, 0.6), mat("CT_Tierra", "#4a3424", 0.9)
    v1, v2, tallo = mat("CT_Hoja_Grande1", "#3f9a55", 0.6), mat("CT_Hoja_Grande2", "#5cbf6a", 0.6), mat("CT_Tallo", "#4caf6a", 0.7)
    p.cono((0, 0, 0), 0.4, 0.55, 0.9, mm, segs=16)
    p.cono((0, 0, 0.85), 0.58, 0.58, 0.12, mm, segs=16)
    p.cono((0, 0, 0.9), 0.5, 0.5, 0.05, tierra, segs=16)
    k = 9
    for i in range(k):
        a = 2 * math.pi * i / k + rnd.uniform(-0.2, 0.2)
        h = 1.4 + (alto - 1.6) * rnd.uniform(0.2, 1.0)
        rr = rnd.uniform(0.35, 0.75)
        punta = Vector((rr * math.cos(a), rr * math.sin(a), h))
        _tubo(p, [(0, 0, 0.9), (punta.x * 0.4, punta.y * 0.4, (0.9 + h) / 2), tuple(punta)], 0.025, tallo, segs=5)
        p.M = Matrix.Translation(punta) @ Matrix.Rotation(a - math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.radians(-rnd.uniform(35, 65)), 4, 'X')
        p.esfera((0, 0, 0.45), 0.45, v1 if i % 2 else v2, esc=(0.75, 0.12, 1.0), segs=10)
        p.M = Matrix.Identity(4)
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015)
    return o


def reloj_pared(nombre, col, r=0.6, color="#e85d75"):
    """reloj de pared redondo (marco de color, numeros de rayita, manecillas). Origen en la pared, al centro; frente -Y."""
    p = P(nombre, col)
    mc_, bl, neg = mat("CT_Reloj_" + color.lstrip("#"), color, 0.4), mat("CT_Reloj_Cara", "#fffdf6", 0.5), mat("CT_Negro", "#151515", 0.5)
    p.cono((0, 0, 0), r + 0.1, r + 0.1, 0.14, mc_, segs=28, rot=('X', 90))
    p.cono((0, -0.14, 0), r, r, 0.01, bl, segs=28, rot=('X', 90))
    for k in range(12):
        a = 2 * math.pi * k / 12
        lg = 0.14 if k % 3 == 0 else 0.07
        p.M = Matrix.Translation((0, -0.16, 0)) @ Matrix.Rotation(-a, 4, 'Y')
        p.caja((0, 0, r - 0.1 - lg / 2), (0.04, 0.02, lg), neg)
        p.M = Matrix.Identity(4)
    for ang, lg, gr in ((-60, r * 0.5, 0.06), (60, r * 0.75, 0.04)):
        p.M = Matrix.Translation((0, -0.18, 0)) @ Matrix.Rotation(math.radians(ang), 4, 'Y')
        p.caja((0, 0, lg / 2), (gr, 0.02, lg), neg)
        p.M = Matrix.Identity(4)
    p.cono((0, -0.15, 0), 0.05, 0.05, 0.06, mc_, segs=10, rot=('X', 90))
    o = _acabado(p.fin(), bisel=0); contorno(o, 0.015)
    return o


def tapete_rect(nombre, col, largo=6.0, ancho=4.0, png="tapete_rombos_azul.png", tile=2.0, fleco="#f3e6cf"):
    """tapete rectangular de tela con estampado y fleco en los lados cortos. Lo largo en Y. Origen en el centro, en el piso."""
    p = P(nombre, col)
    p.caja((0, 0, 0.025), (ancho, largo, 0.05), material_tela("CT_Tapete_" + os.path.splitext(os.path.basename(png))[0], png, tile=tile, relieve=0.3))
    fl = mat("CT_Fleco_" + fleco.lstrip("#"), fleco, 0.9)
    k = int(ancho / 0.12)
    for s in (-1, 1):
        for i in range(k):
            p.caja((-ancho / 2 + ancho * (i + 0.5) / k, s * (largo / 2 + 0.12), 0.01), (0.04, 0.24, 0.02), fl)
    o = _uv_caja(p.fin())
    return o


def espejo_cuerpo(nombre, col, ancho=2.1, alto=5.0, color="#f6a5c8", focos="#fff1c9", base=0.35, tam=1.0):
    """espejo de CUERPO COMPLETO para la pared: marco redondeado de color con foquitos y vidrio. Origen: en la pared,
    abajo al centro; frente -Y. Hijo <nombre>_Vidrio = vacio en el centro del vidrio (para el reflejo real:
    animar_ep005.espejo_real). El vidrio mide ancho x alto (sin el marco)."""
    p = P(nombre, col)
    m, vid = mat("CT_Marco_" + color.lstrip("#"), color, 0.5), mat("CT_Espejo_Caricatura", "#a9d8f0", 0.12)
    foco = emite("CT_Foco_" + focos.lstrip("#"), focos, 3.0)
    zc = base + alto / 2
    g = 0.22
    p.caja((0, -0.06, zc), (ancho, 0.06, alto), vid)
    for x in (-(ancho + g) / 2, (ancho + g) / 2):
        p.caja((x, -0.09, zc), (g, 0.18, alto + 2 * g), m)
    for z in (base - g / 2, base + alto + g / 2):
        p.caja((0, -0.09, z), (ancho + 2 * g, 0.18, g), m)
    for i in range(9):
        z = base + alto * (i + 0.5) / 9
        for x in (-(ancho + g) / 2, (ancho + g) / 2):
            p.esfera((x, -0.2, z), 0.07, foco, segs=8)
    o = _acabado(p.fin(), bisel=0.02); contorno(o, 0.02); o.scale = (tam,) * 3
    e = bpy.data.objects.new(nombre + "_Vidrio", None); col.objects.link(e)
    e.parent = o; e.location = (0, -0.1, zc); e.empty_display_size = 0.3
    e["ancho"], e["alto"] = ancho, alto
    return o
