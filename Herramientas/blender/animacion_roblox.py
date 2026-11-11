# ANIMACIONES DE ROBLOX STUDIO -> rigs R15 del kit (2026-11-10, primera: el paso de Yamal).
# La animacion se saca de Studio con Herramientas/roblox/sacar_animacion.luau (un .json con las curvas de cada
# articulacion) y aqui se hornea al rig: un keyframe por fotograma, con los mismos nombres de huesos que Roblox.
#
# Desde la terminal (hace un .blend NUEVO; no toca el rig original):
#   blender -b "<rig>.blend" --python Herramientas/blender/animacion_roblox.py -- <anim.json> <salida.blend> [repeticiones] [--empacar]
#     --empacar: mete las texturas dentro del .blend (para mandarselo a otra persona).
# Desde otro script:
#   import animacion_roblox as ar
#   ar.aplicar(rig, ar.cargar("Personajes/Animaciones/Paso_Yamal.json"), inicio=1, repeticiones=2)
#
# Como funciona: en Roblox cada articulacion es un Motor6D con Part1 = Part0 * C0 * Transform * C1^-1. Las curvas dan
# Transform (posicion + giro Euler en orden XYZ = Rx*Ry*Rz) en los ejes de la pieza padre (+X derecha, +Y arriba, +Z
# atras). En los rigs R15 C0/C1 no tienen giro, asi que ese giro es el del hueso respecto a su padre: se pasa a los
# ejes de la armadura del kit (mira a -Y, su derecha es -X) y luego a los ejes de cada hueso.
import bpy, bisect, json, math, os, sys
from mathutils import Matrix, Vector, Euler

# ejes de una pieza de Roblox -> ejes de la armadura del kit
M = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))


def cargar(ruta):
    d = json.load(open(ruta, encoding="utf-8"))
    esc = float(d.get("escala", 1000))
    T = [[t / 1000.0 for t in ts] for ts in d["T"]]          # tiempos en milisegundos
    canales = {}
    for nombre, e in d["J"].items():
        c = {}
        for k in ("p", "r"):
            c[k] = [None if not ch else (T[ch[0] - 1], [v / esc for v in ch[1]]) for ch in e.get(k, [0, 0, 0])]
        c["orden"] = e.get("orden", "XYZ")
        canales[nombre] = c
    return {"nombre": d.get("nombre") or os.path.splitext(os.path.basename(ruta))[0], "dur": float(d["dur"]),
            "loop": bool(d.get("loop", False)), "J": canales}


def _valor(ch, t):
    if ch is None:
        return 0.0
    ts, vs = ch
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = bisect.bisect_right(ts, t) - 1
    a = (t - ts[i]) / (ts[i + 1] - ts[i])
    return vs[i] + (vs[i + 1] - vs[i]) * a


def giro_roblox(x, y, z, orden="XYZ"):
    """matriz de giro como CFrame.fromEulerAngles(x, y, z, orden) de Roblox (XYZ = Rx*Ry*Rz)."""
    return Euler((x, y, z), orden[::-1]).to_matrix()     # Blender aplica en el orden escrito: 'ZYX' = Rx*Ry*Rz


def transform(c, t):
    """(giro 3x3, posicion) de la articulacion en el tiempo t, en ejes de Roblox."""
    r = [_valor(ch, t) for ch in c["r"]]
    p = Vector([_valor(ch, t) for ch in c["p"]])
    return giro_roblox(*r, c["orden"]), p


def aplicar(rig, anim, inicio=1, repeticiones=1, fps=None, nombre_accion=None, posiciones=True):
    """hornea la animacion en el rig desde el fotograma 'inicio'. Apaga el IK de piernas y brazos (la animacion es FK).
    Devuelve el ultimo fotograma."""
    sc = bpy.context.scene
    fps = fps or sc.render.fps / sc.render.fps_base
    pbs, bones = rig.pose.bones, rig.data.bones
    huesos = [n for n in anim["J"] if n in pbs]
    faltan = [n for n in anim["J"] if n not in pbs]
    if faltan:
        print("AVISO: el rig no tiene estos huesos (se ignoran):", faltan)
    rig.animation_data_create()
    if nombre_accion:
        act = bpy.data.actions.new(nombre_accion)
        act.use_fake_user = True                       # se puede anexar a otro rig desde este .blend
        rig.animation_data.action = act
    prefs = bpy.context.preferences.edit
    interp_antes = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = 'LINEAR'
    B = {n: bones[n].matrix_local.to_3x3() for n in huesos}
    for n in huesos:
        pbs[n].rotation_mode = 'XYZ'
    for k in ("IK_Piernas", "IK_Brazos"):
        if k in rig.keys():
            rig[k] = 0.0
            rig.keyframe_insert('["%s"]' % k, frame=inicio)
    total = int(round(anim["dur"] * fps * repeticiones))
    prev = {}
    for i in range(total + 1):
        t = i / fps
        if anim["loop"] or repeticiones > 1:
            t = t % anim["dur"] if i < total else anim["dur"]
        f = inicio + i
        for n in huesos:
            c = anim["J"][n]
            R, p = transform(c, t)
            Bn = B[n]
            Q = Bn.transposed() @ (M @ R @ M.transposed()) @ Bn
            eu = Q.to_euler('XYZ', prev[n]) if n in prev else Q.to_euler('XYZ')
            prev[n] = eu.copy()
            pb = pbs[n]
            pb.rotation_euler = eu
            pb.keyframe_insert("rotation_euler", frame=f, group=n)
            if posiciones and not bones[n].use_connect and any(c["p"]):
                pb.location = Bn.transposed() @ (M @ p)
                pb.keyframe_insert("location", frame=f, group=n)
    prefs.keyframe_new_interpolation_type = interp_antes
    print("animacion %s: %d huesos, fotogramas %d-%d (%d vueltas)" % (anim["nombre"], len(huesos), inicio, inicio + total, repeticiones))
    return inicio + total


def aplicar_motor6d(rig, anim, inicio=1, repeticiones=1, fps=None, nombre_accion=None):
    """como aplicar(), pero para rigs hechos con rig_motor6d.py (ciervo, monstruos: 2026-11-11). Ahi cada hueso tiene
    EXACTAMENTE los ejes de su articulacion de Roblox (Part0 * C0), asi que el Transform de Roblox se pone tal cual:
    giro + posicion en studs, sin convertir ejes. Devuelve el ultimo fotograma."""
    sc = bpy.context.scene
    fps = fps or sc.render.fps / sc.render.fps_base
    pbs = rig.pose.bones
    huesos = [n for n in anim["J"] if n in pbs]
    faltan = [n for n in anim["J"] if n not in pbs]
    if faltan:
        print("AVISO: el rig no tiene estos huesos (se ignoran):", faltan)
    rig.animation_data_create()
    if nombre_accion:
        act = bpy.data.actions.new(nombre_accion)
        act.use_fake_user = True
        rig.animation_data.action = act
    prefs = bpy.context.preferences.edit
    interp_antes = prefs.keyframe_new_interpolation_type
    prefs.keyframe_new_interpolation_type = 'LINEAR'
    for n in huesos:
        pbs[n].rotation_mode = 'XYZ'
    total = int(round(anim["dur"] * fps * repeticiones))
    prev = {}
    for i in range(total + 1):
        t = i / fps
        if anim["loop"] or repeticiones > 1:
            t = t % anim["dur"] if i < total else anim["dur"]
        f = inicio + i
        for n in huesos:
            R, p = transform(anim["J"][n], t)
            eu = R.to_euler('XYZ', prev[n]) if n in prev else R.to_euler('XYZ')
            prev[n] = eu.copy()
            pb = pbs[n]
            pb.rotation_euler = eu
            pb.location = p
            pb.keyframe_insert("rotation_euler", frame=f, group=n)
            pb.keyframe_insert("location", frame=f, group=n)
    prefs.keyframe_new_interpolation_type = interp_antes
    print("animacion %s (motor6d): %d huesos, fotogramas %d-%d" % (anim["nombre"], len(huesos), inicio, inicio + total))
    return inicio + total


def _autoprueba():
    # mismo giro que dio Studio para RightUpperArm en t=0 (EulerRotationCurve:GetRotationAtTime)
    R = giro_roblox(1.686, 0.427, -0.610)
    esperado = ((0.746, 0.521, 0.414), (0.403, 0.141, -0.904), (-0.530, 0.841, -0.105))
    err = max(abs(R[i][j] - esperado[i][j]) for i in range(3) for j in range(3))
    assert err < 0.003, "orden de giro distinto al de Roblox (error %.4f)" % err


_autoprueba()

if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    empacar = "--empacar" in a
    a = [x for x in a if not x.startswith("--")]
    ruta, salida = os.path.abspath(a[0]), os.path.abspath(a[1])
    rep = int(a[2]) if len(a) > 2 else 1
    if os.path.exists(salida):
        sys.exit("YA EXISTE (no se sobrescribe): " + salida)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and "UpperTorso" in o.pose.bones)
    anim = cargar(ruta)
    sc = bpy.context.scene
    sc.render.fps, sc.render.fps_base = 30, 1.0
    fin = aplicar(rig, anim, inicio=1, repeticiones=rep, nombre_accion=anim["nombre"])
    sc.frame_start, sc.frame_end = 1, fin
    sc.frame_set(1)
    if empacar:
        bpy.ops.file.pack_all()
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=salida, copy=True)
    print("GUARDADO", salida, "rig", rig.name, "accion", anim["nombre"], "fotogramas 1-%d" % fin)
