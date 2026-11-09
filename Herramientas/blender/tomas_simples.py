# TOMAS SIMPLES (receta docs/09_RECETA_SIMPLE.md, estilo Custerk/Gelo): arma una escena a partir de una LISTA DE TOMAS:
# camaras fijas con acercamiento lento (que NADA tape la cara: prueba angulos con rayos), un corte por toma, cuerpos
# en su pose CON VIDA SUAVE (respiran, la cabeza se mueve; nunca congelados), caras por toma, gestos en su palabra y
# en los dialogos la boca + asentir suave. Probado en
# Analizador/Resultados/Entrenamiento_2026-11-08/prueba_simple (EP004 T13-16: 12 tomas en ~20 s de script).
#
# Uso dentro de Blender:
#   import tomas_simples as ts
#   ts.armar(fa, fb, personajes={"SK": "Sikelpa_Rig", "CR": "Crush_Rig"}, voz="audio/voz.wav",
#            bocas={"SK": "voz", "CR": [3, 2]},           # "voz" = bocas 21-25 segun el volumen; [abierta, cerrada] alterna
#            tomas=[(1226, "SK", "retrato", {"SK": 3}),             # (desde, foco, tipo, caras {quien: n | "bocas"})
#                   (1300, "SK", "habla", {"SK": "bocas"}),
#                   (1413, "CR", "hombro", {"SK": 4, "CR": 1}),     # sobre el hombro del OTRO: el foco sale de frente
#                   (1500, "Papel", "inserto", {})])                # objeto en primer plano (nombre del objeto)
# Tipos: "retrato" (plano medio), "habla" (primer plano + boca), "hombro" (dos personajes en 9:16), "inserto" (objeto),
#        "general" (a mano: pasar pos/mira en caras={"_pos": (x,y,z), "_mira": (x,y,z), "_ang": 50}).
# Borra antes lo que creo en ese rango (camaras CR_Cam_TS_*, marcadores CR_TS_*). No toca la voz ni otros rangos.
import math, os, sys
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _sc():
    return bpy.context.scene


def curvas(ob):
    r = []
    if ob.animation_data and ob.animation_data.action:
        for lay in ob.animation_data.action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    r += list(cb.fcurves)
    return r


def quieto(ob, f_src, fa, fb):
    """cuerpo QUIETO en la pose de f_src durante fa..fb (la cara aparte)"""
    for fc in curvas(ob):
        if fc.data_path == '["cara"]':
            continue
        v = fc.evaluate(f_src)
        kps = fc.keyframe_points
        for f in (fa, fb):
            if not any(abs(k.co.x - f) < 0.01 for k in kps):
                kps.insert(f, v)
        for k in kps:
            if fa <= k.co.x <= fb:
                k.co.y = v; k.handle_left.y = v; k.handle_right.y = v
        fc.update()


def caras(ob, lista, fa, fb):
    """llaves de cara CONSTANT [(f, n), ...] en fa..fb (borra las de ahi; respeta fb+1)"""
    if "cara" not in ob:
        return
    if not any(fc.data_path == '["cara"]' for fc in curvas(ob)):
        ob.keyframe_insert('["cara"]', frame=fa)
    for fc in curvas(ob):
        if fc.data_path != '["cara"]':
            continue
        despues = fc.evaluate(fb + 1)
        kps = fc.keyframe_points
        for i in reversed(range(len(kps))):
            if fa <= kps[i].co.x <= fb:
                kps.remove(kps[i])
        if not any(abs(k.co.x - (fb + 1)) < 0.01 for k in kps):
            kps.insert(fb + 1, despues)
        prev = None
        for f, n in lista:
            if n != prev:
                kps.insert(f, n); prev = n
        for k in kps:
            k.interpolation = 'CONSTANT'
        fc.update()


def cabeza(rig, f):
    _sc().frame_set(f)
    return rig.matrix_world @ rig.pose.bones["Head"].head


def frente(rig, f):
    _sc().frame_set(f)
    return (rig.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


def visible(pos, rig, f):
    """que parte de la cara se ve desde pos (rayos a 5 puntos; cuentan si pegan en el mismo personaje)"""
    sc = _sc(); sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    H = rig.matrix_world @ rig.pose.bones["Head"].head
    fr = (rig.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    lat = Vector((-fr.y, fr.x, 0))
    pts = [H + Vector((0, 0, 0.7)) + fr * 0.4 + lat * dx + Vector((0, 0, dz)) for dx, dz in ((0, 0), (0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3))]
    ok = 0
    for p in pts:
        d = p - Vector(pos)
        hit, loc, nrm, idx, ob, mat = sc.ray_cast(dg, Vector(pos), d.normalized(), distance=d.length + 0.3)
        if not hit or (ob is not None and (ob == rig or ob.parent == rig)):
            ok += 1
    return ok / len(pts)


def plano(rig, f, tipo, lado=0.0):
    """camara de frente al personaje, un poco abajo de los ojos; prueba angulos y se queda con el que ve la cara completa"""
    H = cabeza(rig, f); fr = frente(rig, f)
    mejor = None
    for extra in (0, 20, -20, 40, -40, 60, -60):
        g = math.radians(lado + extra)
        d = Vector((fr.x * math.cos(g) - fr.y * math.sin(g), fr.x * math.sin(g) + fr.y * math.cos(g), 0)).normalized()
        if tipo == "primer":
            cand = (H + d * 4.2 + Vector((0, 0, 0.45)), H + Vector((0, 0, 0.75)), 34)
        else:
            cand = (H + d * 6.4 + Vector((0, 0, 0.2)), H + Vector((0, 0, 0.35)), 40)
        v = visible(cand[0], rig, f)
        if mejor is None or v > mejor[0]:
            mejor = (v, cand)
        if v >= 0.99:
            break
    return mejor[1] + (mejor[0],)


def hombro(rig_foco, rig_otro, f):
    """sobre el hombro de rig_otro: rig_foco de frente (en 9:16 dos personajes separados no caben de lado)"""
    hs, hc = cabeza(rig_otro, f), cabeza(rig_foco, f)
    atras = hs - hc; atras.z = 0; atras.normalize()
    lat = Vector((-atras.y, atras.x, 0))
    ops = [hs + atras * 3.2 + lat * s * 1.7 + Vector((0, 0, 0.8)) for s in (1, -1)]
    return max(ops, key=lambda p: visible(p, rig_foco, f)), hc + Vector((0, 0, 0.45)), 38


def camara(col, nombre, f0, f1, pos, mira, ang, acercar=0.06):
    cd = bpy.data.cameras.new(nombre); cd.sensor_fit = 'VERTICAL'; cd.clip_start = 0.1; cd.clip_end = 2000
    c = bpy.data.objects.new(nombre, cd); col.objects.link(c)
    for f, u in ((f0, 0.0), (f1, 1.0)):                   # acercamiento lento y parejo: 2 llaves lineales
        p = Vector(pos).lerp(Vector(mira), acercar * u)
        c.location = p; c.rotation_euler = (Vector(mira) - p).to_track_quat('-Z', 'Y').to_euler()
        cd.angle_y = math.radians(ang)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
    for fc in curvas(c):
        for k in fc.keyframe_points:
            k.interpolation = 'LINEAR'
    return c


def bocas_de(modo, f0, f1, voz):
    """lista [(f, cara)] para que solo se mueva la boca: 'voz' = 21-25 segun volumen; [abierta, cerrada] = alterna cada 4"""
    if modo == "voz":
        import bocas_hablar
        bs = bocas_hablar.calcular(voz, (f0 - 1) / 30.0, f1 / 30.0)
        return [(f0 + k, bs[min(k, len(bs) - 1)]) for k in range(f1 - f0 + 1)]
    abierta, cerrada = modo
    return [(f, abierta if ((f - f0) // 4) % 2 == 0 else cerrada) for f in range(f0, f1 - 2)] + [(f1 - 2, cerrada)]


def armar(fa, fb, personajes, tomas, voz=None, bocas=None, coleccion="Tomas_Simples", vida=True, gestos=None):
    """vida=True (por defecto): al final suma VIDA SUAVE (vida_suave.py: respirar, cabeza, peso, brazos) a todos, para
    que NADIE quede tieso (pedido del usuario 2026-11-09). gestos = {clave: [(fotograma, tipo, cuadros|None), ...]}
    (tipos en vida_suave.GESTOS: asentir, negar, habla, mano_pecho, risa, susto, encoge, agitar, triste, mirar...)."""
    sc = _sc()
    rigs = {k: bpy.data.objects[v] for k, v in personajes.items()}
    bocas = bocas or {}
    for m in list(sc.timeline_markers):
        if fa <= m.frame <= fb:
            sc.timeline_markers.remove(m)
    for o in list(bpy.data.objects):
        if o.name.startswith("CR_Cam_TS_") and o.get("ts_rango") == "%d-%d" % (fa, fb):
            bpy.data.objects.remove(o, do_unlink=True)
    col = bpy.data.collections.get(coleccion) or bpy.data.collections.new(coleccion)
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    tramos = [(t[0], (tomas[i + 1][0] - 1) if i + 1 < len(tomas) else fb) + tuple(t[1:]) for i, t in enumerate(tomas)]
    hechas = []
    for i, (f0, f1, foco, tipo, cs) in enumerate(tramos):
        src = f0 + 3
        for r in rigs.values():
            quieto(r, src, f0, f1)
        if tipo == "general":
            pos, mira, ang = cs["_pos"], cs["_mira"], cs.get("_ang", 50)
        elif tipo == "inserto":
            ob = bpy.data.objects[foco]; sc.frame_set(src)
            P = ob.matrix_world.translation.copy()
            otro = next(iter(rigs.values()))
            d = (cabeza(otro, src) - P); d.z = 0
            d = -d.normalized() if d.length > 0.01 else Vector((0, -1, 0))
            pos, mira, ang = P + d * 2.2 + Vector((0, 0, 0.3)), P, 40
        elif tipo == "hombro":
            otro = next(r for k, r in rigs.items() if k != foco)
            pos, mira, ang = hombro(rigs[foco], otro, src)
        else:
            pos, mira, ang, vis = plano(rigs[foco], src, "primer" if tipo == "habla" else "medio", lado=(-18 if i % 2 else 18))
            if vis < 0.99 and len(rigs) > 1:              # otro personaje lo tapa: sobre el hombro de ese otro
                otro = min((r for k, r in rigs.items() if k != foco), key=lambda r: (cabeza(r, src) - cabeza(rigs[foco], src)).length)
                p2, m2, a2 = hombro(rigs[foco], otro, src)
                if visible(p2, rigs[foco], src) > vis:
                    pos, mira, ang = p2, m2, a2
                    tipo = tipo + "_hombro"
                else:
                    print("tomas_simples: aviso, la cara de %s se ve %d %% en f%d" % (rigs[foco].name, 100 * vis, src))
        c = camara(col, "CR_Cam_TS_%d_%02d_%s" % (fa, i + 1, tipo), f0, f1, pos, mira, ang)
        c["ts_rango"] = "%d-%d" % (fa, fb)
        c["sujeto"] = ",".join(r.name for k, r in rigs.items() if k == foco or tipo == "hombro") if foco in rigs else ""
        m = sc.timeline_markers.new("CR_TS_%02d_%s" % (i + 1, tipo), frame=f0); m.camera = c
        for k, r in rigs.items():
            v = cs.get(k)
            if v == "bocas":
                caras(r, bocas_de(bocas.get(k, "voz"), f0, f1, voz), f0, f1)
            elif v is not None:
                caras(r, [(f0, v)], f0, f1)
        hechas.append((f0, f1, foco, tipo, c.name))
    if vida:                                              # simple NO es congelado (docs/09_RECETA_SIMPLE.md)
        import vida_suave
        for k, r in rigs.items():
            vida_suave.hornear(r, fa, fb, (gestos or {}).get(k, ()), forzar=True)
    return hechas
