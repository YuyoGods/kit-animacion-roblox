# ZONA SEGURA DE SHORTS (pedido del usuario 2026-11-11, EP010): en YouTube la parte de ABAJO del video la tapan el
# titulo, el canal y "suscribirse", a la DERECHA estan los botones (like, comentarios) y ARRIBA la barra. Lo importante
# (caras, burbujas, letreros, el objeto del que se habla) tiene que quedar CENTRADO dentro de la zona segura, con
# margen, ni muy abajo ni pegado arriba; si todo queda abajo y sobra cielo arriba, se avisa para subirlo.
# Mide en el cuadro (proyeccion de la camara) la cabeza de cada personaje visible (con lo que lleva encima) y la caja de
# cada objeto importante (burbujas, etc.), y devuelve los problemas.
#   import zona_segura as zs
#   zs.revisar(f, camara, rigs=["Sikelpa_Rig", ...], objetos=[burbuja, ...])  -> [(quien, problema), ...]
#   pos, mira = zs.encuadrar(puntos, direccion, elev=6, ang=50)   camara que deja esos puntos CENTRADOS en la zona
#   puntos = zs.puntos_cabeza(rig, f) + zs.puntos_objeto(burbuja, f)
#   zs.reencuadrar(camara, [f0, fm, f1], rigs)   corrige una camara YA HECHA (gira poquito y, si no caben, la aleja),
#                                                 el mismo cambio en todas sus llaves (EP011, 2026-11-11)
# Coordenadas: x de 0 (izquierda) a 1; y medido DESDE ARRIBA (0 = borde de arriba, 1 = borde de abajo).
import math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ZONA = {"x0": 0.06, "x1": 0.86, "y0": 0.12, "y1": 0.70}     # zona segura (y desde arriba)
SOBRA_ARRIBA = 0.42      # si lo mas alto de lo importante empieza mas abajo que esto, sobra espacio arriba
MIN_TAM = 0.035          # cabezas mas chicas que esto (alto en el cuadro) son de fondo: no se revisan


def _piezas_cabeza(rig):
    hijos = rig.children_recursive if hasattr(rig, "children_recursive") else rig.children
    return [o for o in hijos if o.type == 'MESH' and o.parent_bone == "Head" and not o.hide_render]


def _caja(objs, cam, paso=3):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    us, vs = [], []
    for o in objs:
        if o.hide_render or o.type not in ('MESH', 'FONT', 'CURVE'):
            continue
        oe = o.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        mw = oe.matrix_world
        for i in range(0, len(me.vertices), paso):
            p = world_to_camera_view(sc, cam, mw @ me.vertices[i].co)
            if p.z > 0:
                us.append(p.x); vs.append(1.0 - p.y)
        oe.to_mesh_clear()
    if not us:
        return None
    return min(us), max(us), min(vs), max(vs)


def _escala_mundo(o):
    s = o.matrix_world.to_scale()
    return min(abs(s.x), abs(s.y), abs(s.z))


def revisar(f, camara=None, rigs=(), objetos=(), zona=None):
    """problemas de encuadre en el cuadro f: [(quien, texto)]. objetos = raices (se miran todos sus hijos)."""
    z = dict(ZONA, **(zona or {}))
    sc = bpy.context.scene
    sc.frame_set(f)
    cam = camara or sc.camera
    probs, cajas = [], []
    for nombre in rigs:
        rg = bpy.data.objects.get(nombre)
        if not rg or rg.matrix_world.translation.z < -100:
            continue
        c = _caja(_piezas_cabeza(rg), cam)
        if not c or c[1] < 0 or c[0] > 1 or c[3] < 0 or c[2] > 1:
            continue
        if c[3] - c[2] < MIN_TAM:
            continue
        cajas.append((nombre.replace("_Rig", ""), c))
    for o in objetos:
        if o is None or o.hide_render or _escala_mundo(o) < 1e-3:
            continue
        hijos = [o] + [h for h in o.children_recursive if _escala_mundo(h) > 1e-3]
        c = _caja(hijos, cam, paso=1)
        if c:
            cajas.append((o.name, c))
    for quien, (x0, x1, y0, y1) in cajas:
        if y1 > z["y1"]:
            probs.append((quien, "muy abajo (llega a %d %% del alto; zona segura hasta %d %%)" % (100 * y1, 100 * z["y1"])))
        if y0 < z["y0"]:
            probs.append((quien, "muy arriba (empieza en %d %%; margen arriba %d %%)" % (100 * y0, 100 * z["y0"])))
        if x0 < z["x0"] or x1 > z["x1"]:
            probs.append((quien, "pegado a la orilla (x %d-%d %%; zona %d-%d %%)" % (100 * x0, 100 * x1, 100 * z["x0"], 100 * z["x1"])))
    if cajas and max(c[3] - c[2] for _, c in cajas) > 0.06:      # (en planos generales chiquitos no aplica)
        arriba = min(c[2] for _, c in cajas)
        if arriba > SOBRA_ARRIBA:
            probs.append(("toma", "todo esta abajo: sobra espacio arriba (lo mas alto empieza en %d %%)" % (100 * arriba)))
    return probs, cajas


# ------------------------------------------------------------------ ENCUADRAR: la camara se acomoda sola
def _puntos(objs, f, paso=4):
    sc = bpy.context.scene
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        if o.hide_render or o.type not in ('MESH', 'FONT', 'CURVE') or _escala_mundo(o) < 1e-3:
            continue
        oe = o.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        mw = oe.matrix_world
        pts += [mw @ me.vertices[i].co for i in range(0, len(me.vertices), paso)]
        oe.to_mesh_clear()
    return pts


def puntos_cabeza(rig, f):
    """puntos de la cabeza con todo lo que lleva encima (gorro, cabello, orejas) en el cuadro f."""
    return _puntos(_piezas_cabeza(rig), f)


def puntos_objeto(raiz, f):
    """puntos del objeto y de todos sus hijos visibles (una burbuja con sus letras, un letrero...) en el cuadro f."""
    return _puntos([raiz] + list(raiz.children_recursive), f, paso=2)


def encuadrar(puntos, direccion, elev=6.0, ang=50.0, centro=(0.46, 0.41), llenar=0.78, zona=None, d0=12.0):
    """posicion y punto de mira de una camara que ve 'puntos' desde 'direccion' (horizontal: del sujeto HACIA la
    camara), elevada 'elev' grados (negativo = desde abajo), con angulo vertical 'ang', de modo que la caja de los puntos
    quede centrada en 'centro' (x, y desde arriba) y ocupe 'llenar' de la zona segura en su lado mas justo."""
    z = dict(ZONA, **(zona or {}))
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("ZS_Tmp"); cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(ang)
    cam = bpy.data.objects.new("ZS_Tmp", cd); sc.collection.objects.link(cam)
    asp = sc.render.resolution_x / sc.render.resolution_y
    d = Vector((direccion[0], direccion[1], 0)).normalized()
    e = math.radians(elev)
    dirc = (d * math.cos(e) + Vector((0, 0, 1)) * math.sin(e)).normalized()
    M = sum(puntos, Vector()) / max(1, len(puntos))
    D = d0
    for _ in range(40):
        P = M + dirc * D
        cam.location = P
        cam.rotation_euler = (M - P).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        us, vs = [], []
        for p in puntos:
            q = world_to_camera_view(sc, cam, p)
            if q.z > 0:
                us.append(q.x); vs.append(1.0 - q.y)
        if len(us) < len(puntos) * 0.9:
            D *= 1.4
            continue
        bx0, bx1, by0, by1 = min(us), max(us), min(vs), max(vs)
        s = max((bx1 - bx0) / ((z["x1"] - z["x0"]) * llenar), (by1 - by0) / ((z["y1"] - z["y0"]) * llenar), 1e-3)
        ex, ey = (bx0 + bx1) / 2 - centro[0], (by0 + by1) / 2 - centro[1]
        R3 = cam.matrix_world.to_3x3()
        h = 2 * D * math.tan(math.radians(ang) / 2)
        M = M + (R3 @ Vector((1, 0, 0))) * (ex * h * asp) - (R3 @ Vector((0, 1, 0))) * (ey * h)
        D *= s ** 0.7
        if abs(ex) < 0.006 and abs(ey) < 0.006 and abs(s - 1) < 0.015:
            break
    P = M + dirc * D
    bpy.data.objects.remove(cam, do_unlink=True); bpy.data.cameras.remove(cd)
    return tuple(P), tuple(M)


# ------------------------------------------------------------------ REENCUADRAR: corregir una camara que ya existe
def _caja_union(cam, frames, rigs, objetos=()):
    """caja (x0, x1, y0, y1; y desde arriba) de las cabezas de 'rigs' que salen en cuadro en esos cuadros (y objetos)."""
    sc = bpy.context.scene
    cajas = []
    for f in frames:
        sc.frame_set(f)
        for nombre in rigs:
            rg = bpy.data.objects.get(nombre)
            if not rg or rg.matrix_world.translation.z < -100:
                continue
            c = _caja(_piezas_cabeza(rg), cam)
            if not c or c[1] < 0 or c[0] > 1 or c[3] < 0 or c[2] > 1 or c[3] - c[2] < MIN_TAM:
                continue
            cajas.append(c)
        for o in objetos:
            if o is not None and not o.hide_render:
                c = _caja([o] + list(o.children_recursive), cam, paso=1)
                if c:
                    cajas.append(c)
    if not cajas:
        return None
    return min(c[0] for c in cajas), max(c[1] for c in cajas), min(c[2] for c in cajas), max(c[3] for c in cajas)


def reencuadrar(cam, frames, rigs, objetos=(), centro=(0.46, 0.41), llenar=0.86, zona=None, vueltas=6, lente_max=78.0):
    """corrige una camara YA HECHA (con sus llaves) para que las caras de 'rigs' (y 'objetos') queden dentro de la zona
    segura en esos cuadros: la gira poquito (paneo/inclinacion, sin ladearla) hasta centrarlas y, si no caben, ABRE el
    lente (no se mueve: alejarla la metia en paredes, prueba EP011) hasta lente_max grados; solo lo que falte la aleja.
    El mismo cambio se aplica a todas sus llaves (conserva su movimiento). Devuelve (giro, inclina, alejar) o None."""
    z = dict(ZONA, **(zona or {}))
    sc = bpy.context.scene
    asp = sc.render.resolution_x / sc.render.resolution_y
    tv = math.tan(cam.data.angle_y / 2) if cam.data.sensor_fit == 'VERTICAL' else math.tan(cam.data.angle / 2) / asp
    th = tv * asp
    yaw_t = pitch_t = atras_t = 0.0
    caja = _caja_union(cam, frames, rigs, objetos)
    if caja is None:
        return None
    for _ in range(vueltas):
        caja = _caja_union(cam, frames, rigs, objetos)
        if caja is None:
            break
        x0, x1, y0, y1 = caja
        s = max((x1 - x0) / ((z["x1"] - z["x0"]) * llenar), (y1 - y0) / ((z["y1"] - z["y0"]) * llenar))
        ex, ey = (x0 + x1) / 2 - centro[0], (y0 + y1) / 2 - centro[1]
        dentro = x0 >= z["x0"] and x1 <= z["x1"] and y0 >= z["y0"] and y1 <= z["y1"]
        if dentro and abs(ex) < 0.04 and abs(ey) < 0.06:
            break
        yaw = -math.atan(ex * 2 * th)
        pitch = -math.atan(ey * 2 * tv)
        atras = 0.0
        if s > 1.0 and cam.data.sensor_fit == 'VERTICAL' and math.degrees(cam.data.angle_y) < lente_max - 0.5:
            nuevo = 2 * math.atan(math.tan(cam.data.angle_y / 2) * min(s, 1.6))     # no cabe: abrir el lente
            cam.data.angle_y = min(nuevo, math.radians(lente_max))
            tv = math.tan(cam.data.angle_y / 2); th = tv * asp
            s = 1.0
        if s > 1.0:                                      # ni con el lente: alejarla (distancia a lo que ve)
            sc.frame_set(frames[len(frames) // 2])
            pts = []
            for nombre in rigs:
                rg = bpy.data.objects.get(nombre)
                if rg and rg.matrix_world.translation.z > -100:
                    pts.append(rg.matrix_world @ rg.pose.bones["Head"].head)
            C = cam.matrix_world.translation
            D = min(((p - C).length for p in pts), default=8.0)
            atras = D * (s - 1.0) * 0.95
        _aplicar(cam, yaw, pitch, atras)
        yaw_t += yaw; pitch_t += pitch; atras_t += atras
    return (round(math.degrees(yaw_t), 1), round(math.degrees(pitch_t), 1), round(atras_t, 2))


def _aplicar(cam, yaw, pitch, atras):
    """gira la camara 'yaw' (eje Z del mundo) y 'pitch' (su eje X) y la mueve 'atras' a lo largo de su vista, en TODAS
    sus llaves (o en su posicion si no tiene)."""
    from mathutils import Matrix
    sc = bpy.context.scene
    ad = cam.animation_data
    frames = set()
    if ad and ad.action:
        try:
            curvas = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        except AttributeError:
            curvas = list(ad.action.fcurves)
        for fc in curvas:
            if fc.data_path in ("location", "rotation_euler"):
                frames |= {int(round(k.co.x)) for k in fc.keyframe_points}
    nuevos = []
    for f in sorted(frames) or [sc.frame_current]:
        sc.frame_set(f)
        W = cam.matrix_world.copy()
        P = W.translation.copy()
        R = W.to_3x3()
        R = Matrix.Rotation(yaw, 3, 'Z') @ R @ Matrix.Rotation(pitch, 3, 'X')
        P = P + (R @ Vector((0, 0, 1))) * atras
        nuevos.append((f, P, R))
    prev = None
    for f, P, R in nuevos:
        e = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ')
        cam.location = P; cam.rotation_euler = e; prev = e.copy()
        if frames:
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
