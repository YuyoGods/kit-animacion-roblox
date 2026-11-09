# VIDA SUAVE: que ningun personaje se quede TIESO (pedido del usuario 2026-11-09: "no lo quiero tieso... la historia no
# se entiende si la animacion es estatica"). Se SUMA encima de la pose que el personaje ya tiene en cada fotograma
# (storyboard, tomas_simples, poses del episodio...), asi que sirve con cualquier forma de animar:
#   - siempre: respira, se mece un poco, la cabeza mira y se mueve sola, cambia el peso de pie (si esta parado) y los
#     brazos se mecen un poquito (solo si no sostienen nada).
#   - GESTOS amarrados a una palabra (o fotograma): asentir, negar, contar, habla, mano_pecho, risa, susto, encoge,
#     agitar, triste, mirar, manos_cabeza, oler, comer, arriba, orgullo, tocar_pelo, sorpresa.
# Lento (<= 2 Hz) y de pocos grados: los valores que el usuario aprobo en EP004 (memoria "movimientos suaves").
# Medido: Custerk y Gelo solo dejan casi quietas el 31-45 % de sus tomas; en el resto los personajes se mueven poquito.
#
# Uso dentro de Blender (despues de poner las poses y las camaras):
#   import vida_suave as vs
#   vs.hornear(rig, fa, fb, gestos=[(f0, "mano_pecho", 30), (f1, "asentir", None)])   # dur None = hasta fb
#   vs.hornear_todos(fa, fb, gestos={"Sikelpa_Rig": [...]})                            # todos los rigs en cuadro
#   vs.gesto_en_palabra(tomas_voz, toma, palabra)  -> fotograma donde empieza esa palabra
# Ejemplo completo: Episodios/EP005_No_Te_Sientes_En_Su_Lugar/scripts/animar_ep005.py (tabla GESTOS).
import math, os, sys
import bpy
from mathutils import Quaternion, Euler

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for _d in ("Herramientas/storyboard", "Herramientas/blender"):
    _p = os.path.join(_RAIZ, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
import sb_blender as sbb  # noqa: E402  (angulos "de persona" -> giro de cada hueso, con limites del cuerpo)

HUESOS_VIDA = ("UpperTorso", "LowerTorso", "Head", "RightUpperArm", "LeftUpperArm", "RightLowerArm", "LeftLowerArm")
T2 = 2 * math.pi


def _suave(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _env(k, dur, ataque=6, salida=8):
    if k < 0 or k > dur:
        return 0.0
    e = _suave(k / max(1, ataque))
    if dur - k < salida:
        e *= _suave((dur - k) / max(1, salida))
    return e


# gesto -> funcion (k = cuadro desde que empieza, dur = cuadros) que da angulos "de persona" A SUMAR
GESTOS = {
    "asentir": lambda k, d: {"Head": [7 * math.sin(T2 * k / 18) * _env(k, d, 4, 6)]},
    "contar": lambda k, d: {"Head": [6 * math.sin(math.pi * min(1, k / max(1, d))) * _env(k, d, 2, 4)]},
    "negar": lambda k, d: {"Head": [0, 11 * math.sin(T2 * k / 20) * _env(k, d, 4, 8)]},
    "habla": lambda k, d: {"Head": [2.6 * math.sin(T2 * k / 26) * _env(k, d, 6, 8), 2.2 * math.sin(T2 * k / 41) * _env(k, d, 6, 8),
                                    1.5 * math.sin(T2 * k / 33) * _env(k, d, 6, 8)]},
    "mano_pecho": lambda k, d: {"RightUpperArm": [38 * _env(k, d, 8, 10), -32 * _env(k, d, 8, 10)], "RightLowerArm": [80 * _env(k, d, 8, 10)],
                                "Head": [5 * _env(k, d, 8, 10), 0, 7 * _env(k, d, 8, 10)]},
    "risa": lambda k, d: {"UpperTorso": [3 * math.sin(T2 * k / 16) * _env(k, d, 4, 10)],
                          "Head": [(-6 + 2 * math.sin(T2 * k / 16)) * _env(k, d, 4, 10)]},
    "susto": lambda k, d: {h: [v * _env(k, d, 4, 8) * (1 + 0.15 * math.sin(T2 * k / 10) * math.exp(-k / 8)) for v in vals]
                           for h, vals in {"UpperTorso": [-8], "Head": [-7], "RightUpperArm": [24, 22], "LeftUpperArm": [24, 22],
                                           "RightLowerArm": [45], "LeftLowerArm": [45]}.items()},
    "encoge": lambda k, d: {"Head": [10 * _env(k, d, 10, 10), 0, 5 * _env(k, d, 10, 10)], "UpperTorso": [5 * _env(k, d, 10, 10)]},
    "agitar": lambda k, d: {"RightLowerArm": [20 * math.sin(T2 * k / 18) * _env(k, d, 4, 6)]},
    "triste": lambda k, d: {"Head": [14 * _env(k, d, 18, 10)], "UpperTorso": [6 * _env(k, d, 18, 10)]},
    "mirar": lambda k, d: {"Head": [0, 24 * math.sin(T2 * k / 64) * _env(k, d, 10, 10)]},
    "manos_cabeza": lambda k, d: {"RightUpperArm": [148 * _env(k, d, 6, 8), 30 * _env(k, d, 6, 8)], "LeftUpperArm": [148 * _env(k, d, 6, 8), 30 * _env(k, d, 6, 8)],
                                  "RightLowerArm": [105 * _env(k, d, 6, 8)], "LeftLowerArm": [105 * _env(k, d, 6, 8)], "Head": [-4 * _env(k, d, 6, 8)]},
    "oler": lambda k, d: {"Head": [-14 * _env(k, d, 14, 8)]},
    "comer": lambda k, d: {"Head": [9 * (0.5 - 0.5 * math.cos(T2 * k / 14)) * _env(k, d, 3, 3)]},
    "arriba": lambda k, d: {"Head": [-62 * _env(k, d, 4, 4)]},
    "orgullo": lambda k, d: {"Head": [-9 * _env(k, d, 8, 8), 0, 6 * _env(k, d, 8, 8)], "UpperTorso": [-4 * _env(k, d, 8, 8)]},
    # EP005: se toca el pelo (mano derecha a la cabeza) y sorpresa que NO avienta las manos a la camara
    "tocar_pelo": lambda k, d: {"RightUpperArm": [100 * _env(k, d, 8, 8), 48 * _env(k, d, 8, 8)], "RightLowerArm": [112 * _env(k, d, 8, 8)],
                                "Head": [-4 * _env(k, d, 8, 8), 0, -6 * _env(k, d, 8, 8)]},
    "sorpresa": lambda k, d: {h: [v * _env(k, d, 3, 8) * (1 + 0.12 * math.sin(T2 * k / 9) * math.exp(-k / 7)) for v in vals]
                              for h, vals in {"UpperTorso": [-9], "Head": [-8, 0, 5], "RightUpperArm": [6, 20], "LeftUpperArm": [6, 20],
                                              "RightLowerArm": [22], "LeftLowerArm": [22]}.items()},
}


def _s(t, hz, fase):
    return math.sin(T2 * hz * t + fase)


def _curva(rig, path, i):
    ad = rig.animation_data
    if not (ad and ad.action):
        return None
    for lay in ad.action.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                fc = cb.fcurves.find(path, index=i)
                if fc:
                    return fc
    return None


def _pose_base(rig, h, f):
    """rotacion del hueso en ese fotograma segun sus llaves (o la actual si no tiene)"""
    pb = rig.pose.bones[h]
    vals = []
    for i in range(3):
        fc = _curva(rig, 'pose.bones["%s"].rotation_euler' % h, i)
        vals.append(fc.evaluate(f) if fc else pb.rotation_euler[i])
    return Euler(vals, 'XYZ').to_quaternion()


def _fuera(rig, f):
    fc = _curva(rig, "location", 2)
    return fc is not None and fc.evaluate(f) < -100


def hornear(rig, fa, fb, gestos=(), semilla=None, paso=1, forzar=False):
    """suma vida suave + gestos a lo que el rig ya tiene en fa..fb (una llave por fotograma en 7 huesos).
    No la suma dos veces al mismo tramo (se encimaria): marca el tramo en el rig; forzar=True la vuelve a sumar (usar
    solo si antes se rehicieron las poses de ese tramo, como hace tomas_simples.armar)."""
    if rig is None:
        return 0
    marca = "%d-%d" % (fa, fb)
    hechos = list(rig.get("vida_hecha", []))
    if marca in hechos and not forzar:
        print("vida_suave: %s ya tiene vida en %s (usa forzar=True si rehiciste las poses)" % (rig.name, marca))
        return 0
    rig["vida_hecha"] = [m for m in hechos if m != marca] + [marca]
    W = {b.name: b.matrix_local.to_quaternion() for b in rig.data.bones}
    Winv = {k: q.inverted() for k, q in W.items()}
    pbs = rig.pose.bones
    sem = semilla if semilla is not None else sum(ord(c) for c in rig.name)
    fz = [((sem * (i + 3)) % 628) / 100.0 for i in range(10)]
    n = 0
    prev = {}
    for f in range(fa, fb + 1, paso):
        if _fuera(rig, f):
            continue
        base = {h: _pose_base(rig, h, f) for h in HUESOS_VIDA if h in pbs}
        sentado = "RightUpperLeg" in pbs and _pose_base(rig, "RightUpperLeg", f).angle > math.radians(50)
        libres = all(base[h].angle < math.radians(30) for h in ("RightUpperArm", "LeftUpperArm") if h in base) and \
            all(base[h].angle < math.radians(40) for h in ("RightLowerArm", "LeftLowerArm") if h in base)
        t = f / 30.0
        off = {"UpperTorso": [1.4 * _s(t, 0.32, fz[0]), 0.8 * _s(t, 0.09, fz[1]), 0],
               "Head": [1.8 * _s(t, 0.17, fz[2]), 3.2 * _s(t, 0.11, fz[3]) + 1.4 * _s(t, 0.23, fz[4]), 1.2 * _s(t, 0.13, fz[5])]}
        if not sentado:
            off["LowerTorso"] = [0, 0, 1.1 * _s(t, 0.12, fz[6])]
        if libres:
            off["RightUpperArm"] = [1.6 * _s(t, 0.21, fz[7]), 1.0 * _s(t, 0.15, fz[8])]
            off["LeftUpperArm"] = [1.6 * _s(t, 0.19, fz[9]), 1.0 * _s(t, 0.17, fz[1])]
        for g in gestos:
            g0, tipo, dur = g[0], g[1], (g[2] if len(g) > 2 and g[2] else fb - g[0])
            if g0 <= f <= g0 + dur and tipo in GESTOS:
                off = sbb.sumar(off, GESTOS[tipo](f - g0, dur))
        for h, ang in off.items():
            if h not in base:
                continue
            q_off = Winv[h] @ sbb.giro_de(h, ang) @ W[h]
            q = q_off @ base[h]
            e = q.to_euler('XYZ', prev[h]) if h in prev else q.to_euler('XYZ')
            prev[h] = e.copy()
            pbs[h].rotation_mode = 'XYZ'
            pbs[h].rotation_euler = e
            pbs[h].keyframe_insert("rotation_euler", frame=f, group=h)
            n += 1
    return n


def hornear_todos(fa, fb, gestos=None, rigs=None, forzar=False):
    """vida suave a todos los rigs (o los dados) en fa..fb. gestos = {nombre_del_rig: [(f0, tipo, dur), ...]}"""
    gestos = gestos or {}
    rigs = rigs or [o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.endswith("_Rig") and not o.hide_render]
    total = 0
    for r in rigs:
        total += hornear(r, fa, fb, gestos.get(r.name, ()), forzar=forzar)
    print("vida_suave: %d llaves en %d personajes (%d-%d)" % (total, len(rigs), fa, fb))
    return total


def gesto_en_palabra(tomas_voz, toma, palabra, k=0):
    """fotograma donde empieza 'palabra' (minusculas, sin acentos ni signos) en la toma (de audio/tomas_voz.json)"""
    hits = [p["f"] for p in tomas_voz["palabras"] if p["toma"] == toma and p["w"] == palabra]
    return hits[min(k, len(hits) - 1)] if hits else None
