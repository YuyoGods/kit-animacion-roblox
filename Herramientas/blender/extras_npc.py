# GENTE DE FONDO (NPC): anexa personajes con rig al .blend y los deja quietos en una pose que se entienda
# (atendiendo un puesto, sentados platicando, formados en la fila, comprando...). Para que el pueblo se vea vivo.
# Uso dentro de Blender (script de episodio o de prueba):
#   import extras_npc as ex
#   r = ex.anexar("regina145901")                                   # busca Personajes/*/<nombre>/<nombre>_R15_Rig.blend
#   ex.poner(r, (171.6, 380), rot=90, pose="atender")               # rot: grados, 0 = mira a -Y (como en Blender)
#   ex.poner(r2, (157, 376.4), rot=180, pose="platicar", asiento=1.14, gira=25)
# Poses: parado, atender, sentado, platicar (sentado o parado con la cabeza hacia su vecino y una mano arriba),
#        fila (parado, brazos cruzados), comprar (parado, un brazo al frente), saludar.
# Las piernas sentadas se doblan con FK (IK_Piernas = 0). Cada NPC se usa una sola vez por escena.
import bpy, math, os, glob
from mathutils import Vector

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def ruta_rig(nombre):
    for nivel in ("Pueblo_NPC", "Secundarios", "Protagonista"):
        r = os.path.join(RAIZ, "Personajes", nivel, nombre, nombre + "_R15_Rig.blend")
        if os.path.exists(r):
            return r
    hall = glob.glob(os.path.join(RAIZ, "Personajes", "*", "*", nombre + "_R15_Rig.blend"))
    return hall[0] if hall else None


def anexar(nombre, coleccion_destino=None):
    """trae la coleccion del personaje (NOMBRE en mayusculas) y devuelve su rig. Si ya estaba, devuelve el mismo."""
    rig = bpy.data.objects.get(nombre + "_Rig")
    if rig:
        return rig
    r = ruta_rig(nombre)
    if not r:
        raise FileNotFoundError("No encontre el rig de " + nombre)
    with bpy.data.libraries.load(r, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == nombre.upper()]
    c = dst.collections[0]
    (coleccion_destino or bpy.context.scene.collection).children.link(c)
    return bpy.data.objects[nombre + "_Rig"]


def _rot(pb, nombre, x=0.0, y=0.0, z=0.0):
    b = pb.get(nombre)
    if b:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))


def poner(rig, pos, rot=0.0, pose="parado", asiento=None, gira=0.0):
    """coloca al rig con los pies en pos (x, y[, z]) o, si se sienta, con la cadera sobre 'asiento' (z del asiento).
    gira: grados que voltea la cabeza (+ = a su izquierda) para platicar con el de al lado.
    Ejes de los huesos (medido): X = adelante/atras, Y = voltear (+ izquierda), Z = ladear."""
    rig["IK_Piernas"] = 0.0
    rig["IK_Brazos"] = 0.0
    pb = rig.pose.bones
    for b in pb:
        b.rotation_mode = 'XYZ'
        b.rotation_euler = (0, 0, 0); b.location = (0, 0, 0)
    sentado = pose in ("sentado",) or (pose == "platicar" and asiento is not None)
    if sentado:
        for s in ("Right", "Left"):
            _rot(pb, s + "UpperLeg", 90); _rot(pb, s + "LowerLeg", -90)
        _rot(pb, "RightUpperArm", 12); _rot(pb, "LeftUpperArm", 12)
        _rot(pb, "RightLowerArm", 25); _rot(pb, "LeftLowerArm", 25)
    if pose == "atender":
        _rot(pb, "RightUpperArm", 45); _rot(pb, "LeftUpperArm", 45)
        _rot(pb, "RightLowerArm", 30); _rot(pb, "LeftLowerArm", 30)
        _rot(pb, "UpperTorso", 6)
    elif pose == "fila":
        _rot(pb, "RightUpperArm", 35, 0, 25); _rot(pb, "LeftUpperArm", 35, 0, -25)
        _rot(pb, "RightLowerArm", 95); _rot(pb, "LeftLowerArm", 95)
    elif pose == "comprar":
        _rot(pb, "RightUpperArm", 70); _rot(pb, "RightLowerArm", 20)
    elif pose == "saludar":
        _rot(pb, "RightUpperArm", 0, 0, -150); _rot(pb, "RightLowerArm", 30)
    elif pose == "platicar":
        # las piernas se quedan como cuando uno se sienta normal; el torso y la cabeza voltean hacia el otro
        _rot(pb, "UpperTorso", 3, gira * 0.45, 0)                     # en estos rigs voltear = eje Y (+ = a su izquierda)
        _rot(pb, "LowerTorso", 0, gira * 0.15, 0)
        lado = "Left" if gira >= 0 else "Right"                       # la mano del lado del otro, a medio gesto
        _rot(pb, lado + "UpperArm", 25); _rot(pb, lado + "LowerArm", 55)
    if gira:
        _rot(pb, "Head", 0, gira * (0.55 if pose == "platicar" else 1.0), 0)
    rig["_gira"] = gira
    rig.rotation_euler = (0, 0, math.radians(rot))
    bpy.context.view_layer.update()
    if sentado:
        cadera = rig.matrix_world @ pb["LowerTorso"].head
        rig.location += Vector((pos[0], pos[1], asiento + 0.25)) - cadera
    else:
        rig.location = (pos[0], pos[1], pos[2] if len(pos) > 2 else 0.06)
    bpy.context.view_layer.update()
    return rig


def _llave(pb, nombre, f, dx=0.0, dy=0.0, dz=0.0, base=None):
    b = pb.get(nombre)
    if not b:
        return
    bx, by, bz = base[nombre]
    b.rotation_euler = (bx + math.radians(dx), by + math.radians(dy), bz + math.radians(dz))
    b.keyframe_insert("rotation_euler", frame=f)


def platica(a, b, f0, f1, turno=54, semilla=1):
    """anima a dos personajes (ya puestos con pose "platicar") platicando de f0 a f1 con movimiento natural:
    se turnan para hablar (el que habla mueve la mano y la cabeza; el que escucha asiente despacito), respiran y
    nunca se quedan tiesos. Llaves suaves cada ~0,4 s con variaciones (no se repite igual)."""
    import random
    rnd = random.Random(semilla)
    for rig in (a, b):
        if rig.animation_data and rig.animation_data.action:
            rig.animation_data.action = None
    huesos = ("Head", "UpperTorso", "LeftUpperArm", "LeftLowerArm", "RightUpperArm", "RightLowerArm", "LeftHand", "RightHand")
    bases = {r: {h: tuple(r.pose.bones[h].rotation_euler) for h in huesos if h in r.pose.bones} for r in (a, b)}
    habla = a
    f = f0
    while f <= f1:
        fin_turno = min(f1, f + turno + rnd.randint(-12, 14))
        for rig in (a, b):
            pb = rig.pose.bones
            gira = rig.get("_gira", 0.0)
            lado = "Left" if gira >= 0 else "Right"
            k = f
            while k <= fin_turno:
                t = (k - f0) / 30.0
                resp = 1.2 * math.sin(t * 2 * math.pi / 3.6 + (0 if rig is a else 1.3))        # respiracion
                if rig is habla:                                   # habla: gesto con la mano y la cabeza
                    _llave(pb, "Head", k, rnd.uniform(-5, 4), rnd.uniform(-7, 7), rnd.uniform(-4, 4), bases[rig])
                    _llave(pb, lado + "UpperArm", k, rnd.uniform(-8, 18), 0, rnd.uniform(-6, 6), bases[rig])
                    _llave(pb, lado + "LowerArm", k, rnd.uniform(-15, 25), 0, 0, bases[rig])
                    _llave(pb, lado + "Hand", k, rnd.uniform(-15, 15), 0, rnd.uniform(-10, 10), bases[rig])
                else:                                              # escucha: asiente despacio, casi quieto
                    _llave(pb, "Head", k, (6 if (k // 12) % 2 else -1) * rnd.uniform(0.4, 1.0), rnd.uniform(-2, 2), rnd.uniform(-2, 2), bases[rig])
                    _llave(pb, lado + "UpperArm", k, rnd.uniform(-2, 2), 0, 0, bases[rig])
                    _llave(pb, lado + "LowerArm", k, rnd.uniform(-3, 3), 0, 0, bases[rig])
                    _llave(pb, lado + "Hand", k, 0, 0, 0, bases[rig])
                _llave(pb, "UpperTorso", k, resp, 0, 0, bases[rig])
                k += rnd.randint(10, 15)
        habla = b if habla is a else a
        f = fin_turno + 1
    for rig in (a, b):                                             # curvas suaves (bezier con frenado natural)
        ac = rig.animation_data.action if rig.animation_data else None
        for fc in (getattr(ac, "fcurves", None) or []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'; kp.easing = 'AUTO'
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
