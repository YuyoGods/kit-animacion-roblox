# ACTUACION: le da VIDA a los personajes despues de armar las tomas con sb_blender (pedido del usuario: con solo las
# poses del storyboard se veian tiesos; la meta es que actuen como en EP002 "Lo que piensas").
# Encima de la pose de cada fotograma (lugar, giro, pose base) suma:
#   - vida (siempre): respiran, cambian el peso de pie, la cabeza mira y se mueve sola, los brazos no se quedan quietos.
#   - gestos amarrados a una PALABRA de la voz: susto, sorpresa, festejo, salto, manos a la boca, rascarse, pensar,
#     asentir, negar, encogerse, senalar, aplaudir, reir, saludar, triste, nervioso, enamorado, flotar...
#     Con anticipacion y un poquito de rebote (no robotico). Los gestos de brazos REEMPLAZAN la pose base mientras duran
#     (los demas huesos se quedan como estaban); cabeceos y risas se SUMAN.
#   - habla: cuando un personaje dice su dialogo, cabeza y mano acompanan el volumen de la voz (voz.wav).
#   - golpes de camara (zoom de golpe + temblor) en los sustos y saltos.
# Uso (en el script del episodio, despues de rigs = sbb.armar_todo(...)):
#   import actuar
#   A = actuar.Actuacion(sb, rigs, voz_wav=".../audio/voz.wav")
#   A.gesto("coco", 3, "pum", "susto"); A.habla("crush", 14, "encanta"); A.flotar("lila", 4, subida=4.0)
#   A.hornear()                    # vuelve a poner las llaves de los huesos (todas las tomas)
#   A.golpes_camara()              # zoom/temblor en los golpes (despues de que existan las camaras)
import bpy, math, random, wave, zlib
import numpy as np
from mathutils import Vector
import sb_blender as sbb

FPS = 30


def smr(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def rebote(t):
    """0 -> 1 con un poquito de pasada (overshoot) antes de asentarse: se siente vivo, no robotico"""
    t = max(0.0, min(1.0, t))
    return smr(t) + 0.14 * math.sin(math.pi * t) ** 2 * t


def _h(x):
    """numero fijo para una semilla (el hash de Python cambia en cada corrida)"""
    return zlib.crc32(repr(x).encode())


# gesto: pose (angulos 'de persona' como el storyboard, lado derecho = Right...), salto (en alturas del personaje),
# a/h/r = fotogramas de llegada (termina JUSTO en la palabra), de quedarse y de regreso; osc = vaivenes que se suman.
GESTOS = {
    "susto":     dict(pose={"UpperTorso": [-12, 0, 0], "Head": [-10, 0, 0], "RightUpperArm": [45, 35], "LeftUpperArm": [45, 35],
                            "RightLowerArm": [85], "LeftLowerArm": [85]}, salto=0.05, a=5, h=14, r=14, osc="temblor"),
    "sorpresa":  dict(pose={"UpperTorso": [-7, 0, 0], "Head": [-8, 0, 0], "RightUpperArm": [18, 42], "LeftUpperArm": [18, 42],
                            "RightLowerArm": [35], "LeftLowerArm": [35]}, salto=0.03, a=6, h=16, r=14),
    "salto":     dict(pose={"RightUpperArm": [10, 155], "LeftUpperArm": [10, 155], "RightLowerArm": [15], "LeftLowerArm": [15]},
                      salto=0.14, a=5, h=8, r=12),
    "festejo":   dict(pose={"RightUpperArm": [10, 150], "LeftUpperArm": [10, 150], "RightLowerArm": [20], "LeftLowerArm": [20]},
                      a=6, h=40, r=10, osc="festejo"),
    "manos_boca": dict(pose={"RightUpperArm": [72, 16], "LeftUpperArm": [72, 16], "RightLowerArm": [135], "LeftLowerArm": [135],
                             "Head": [6, 0, 0], "UpperTorso": [6, 0, 0]}, a=5, h=20, r=10),
    "rascar":    dict(pose={"RightUpperArm": [30, 125], "RightLowerArm": [115], "Head": [4, 0, 9]}, a=6, h=24, r=10, osc="rascar"),
    "pensar":    dict(pose={"RightUpperArm": [55, 8], "RightLowerArm": [140], "LeftUpperArm": [35, 10], "LeftLowerArm": [95],
                            "Head": [-6, 0, 8]}, a=8, h=30, r=10),
    "asiente":   dict(pose={}, a=2, h=18, r=4, osc="asiente"),
    "niega":     dict(pose={}, a=2, h=20, r=4, osc="niega"),
    "encoge":    dict(pose={"RightUpperArm": [25, 32], "LeftUpperArm": [25, 32], "RightLowerArm": [85], "LeftLowerArm": [85],
                            "Head": [0, 0, 10]}, a=5, h=16, r=10),
    "senala":    dict(pose={"RightUpperArm": [88, 6], "RightLowerArm": [6], "UpperTorso": [4, 0, 0]}, a=5, h=20, r=10),
    "aplaude":   dict(pose={"RightUpperArm": [60, -6], "LeftUpperArm": [60, -6], "RightLowerArm": [85], "LeftLowerArm": [85]},
                      a=5, h=40, r=10, osc="aplaude"),
    "risa":      dict(pose={"Head": [-10, 0, 0], "RightUpperArm": [35, 10], "RightLowerArm": [110]}, a=4, h=24, r=10, osc="risa"),
    "saluda":    dict(pose={"RightUpperArm": [20, 150], "RightLowerArm": [25]}, a=6, h=40, r=10, osc="saluda"),
    "triste":    dict(pose={"UpperTorso": [14, 0, 0], "Head": [16, 0, 0], "RightUpperArm": [0, 2], "LeftUpperArm": [0, 2]},
                      a=10, h=60, r=12),
    "nervioso":  dict(pose={"RightUpperArm": [40, -4], "LeftUpperArm": [40, -4], "RightLowerArm": [100], "LeftLowerArm": [100],
                            "Head": [6, 0, 0]}, a=6, h=40, r=10, osc="nervioso"),
    "enamorado": dict(pose={"RightUpperArm": [45, -8], "LeftUpperArm": [45, -8], "RightLowerArm": [118], "LeftLowerArm": [118],
                            "Head": [-8, 0, 14]}, a=8, h=40, r=12, osc="enamorado"),
    "decidido":  dict(pose={"UpperTorso": [-4, 0, 0], "RightUpperArm": [30, 22], "RightLowerArm": [115], "Head": [-4, 0, 0]},
                      a=4, h=20, r=10, osc="puno"),
    "agacharse": dict(pose={"UpperTorso": [18, 0, 0], "Head": [10, 0, 0]}, a=8, h=30, r=10),
    "voltea":    dict(pose={}, a=4, h=30, r=8),           # kw ang: cuanto voltea la cabeza (+ a su derecha)
    "brinco":    dict(pose={}, salto=0.08, a=4, h=4, r=8),
    "temblor":   dict(pose={}, a=2, h=20, r=6, osc="temblor"),
}
BRAZOS = ("RightUpperArm", "LeftUpperArm", "RightLowerArm", "LeftLowerArm", "RightHand", "LeftHand")


def _rms_voz(ruta):
    w = wave.open(ruta); sr, ch = w.getframerate(), w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    paso = sr // FPS
    r = np.array([np.sqrt(np.mean(x[i:i + paso] ** 2)) for i in range(0, len(x) - paso, paso)])
    return r / (np.percentile(r, 95) or 1.0)


class Actuacion:
    def __init__(self, sb, rigs, voz_wav=None, semilla=7):
        self.sb, self.rigs = sb, rigs
        self.eventos = {aid: [] for aid in rigs}           # (f0, gesto, kw)
        self.hablas = {aid: [] for aid in rigs}            # (f0, f1, fuerza)
        self.flotes = {aid: [] for aid in rigs}            # (fa, fb, subida)
        self.sostiene = {aid: set() for aid in rigs}       # tomas donde sostiene algo (brazos quietos)
        self.sin_vida = set()
        self.golpes = []                                   # (toma, f0, fuerza)
        self.rms = _rms_voz(voz_wav) if voz_wav else None
        self.rnd = random.Random(semilla)
        self.suavidad = 0.45                           # 1 = sin filtro; mas bajo = mas suave (y un poquito mas lento)
        self.voz_suave = None
        if self.rms is not None:                       # volumen suavizado (~0.3 s): la cabeza no tiembla con cada silaba
            kk = np.ones(9) / 9.0
            self.voz_suave = np.clip(np.convolve(np.convolve(self.rms, kk, "same"), kk, "same"), 0, 1.2)

    # ------------------------------------------------------------------ lo que pide el script del episodio
    def f_palabra(self, n, palabra=None, desfase=0.0):
        ti = self.sb["_tiempos"][n - 1]
        if palabra is None:
            return ti["f_ini"]
        return ti["f_ini"] + int(round(sbb.tiempo_en(ti, palabra, desfase) * FPS))

    def gesto(self, aid, n, palabra, tipo, desfase=0.0, golpe=None, **kw):
        if aid not in self.rigs:
            return
        f0 = self.f_palabra(n, palabra, desfase)
        self.eventos[aid].append((f0, tipo, kw))
        if golpe or (golpe is None and tipo in ("susto", "salto")):
            self.golpes.append((n, f0, golpe or 1.0))

    def habla(self, aid, n, desde=None, hasta=None, fuerza=1.0):
        if aid not in self.rigs:
            return
        ti = self.sb["_tiempos"][n - 1]
        f0 = self.f_palabra(n, desde) if desde else ti["f_ini"]
        f1 = self.f_palabra(n, hasta) + 8 if hasta else ti["f_fin"]
        self.hablas[aid].append((f0, f1, fuerza))

    def flotar(self, aid, n, subida=3.0):
        if aid in self.rigs:
            ti = self.sb["_tiempos"][n - 1]
            self.flotes[aid].append((ti["f_ini"], ti["f_fin"], subida))

    def sostener(self, aid, *tomas):
        if aid in self.rigs:
            self.sostiene[aid].update(tomas)

    # ------------------------------------------------------------------ calculo por fotograma
    def _toma_de(self, f):
        for i, ti in enumerate(self.sb["_tiempos"]):
            if ti["f_ini"] <= f <= ti["f_fin"]:
                return i + 1
        return None

    def _env(self, f, f0, g):
        a, h, r = g["a"], g["h"], g["r"]
        if f < f0 - a or f > f0 + h + r:
            return 0.0
        if f < f0:
            return rebote((f - (f0 - a)) / float(a))
        if f <= f0 + h:
            return 1.0
        return 1.0 - smr((f - f0 - h) / float(r))

    def _osc(self, tipo, f, f0, k, P, R):
        t = (f - f0) / FPS
        s = math.sin
        if tipo == "temblor":
            sbb_sumar(P, {"UpperTorso": [0.5 * s(t * 24) * k, 0.4 * s(t * 19) * k], "Head": [0, 0.8 * s(t * 21) * k]})
        elif tipo == "festejo":
            sbb_sumar(P, {"RightLowerArm": [14 * s(t * 9) * k], "LeftLowerArm": [14 * s(t * 9 + 1.4) * k],
                          "RightUpperArm": [0, 6 * s(t * 9) * k], "LeftUpperArm": [0, 6 * s(t * 9 + 1.4) * k],
                          "Head": [-5 * k, 4 * s(t * 4.5) * k]})
            return 0.015 * max(0.0, s(t * 9)) * k
        elif tipo == "rascar":
            sbb_sumar(P, {"RightLowerArm": [0, 9 * s(t * 16) * k]})
        elif tipo == "asiente":
            sbb_sumar(P, {"Head": [7 * max(0.0, s(t * 10)) * k]})
        elif tipo == "niega":
            sbb_sumar(P, {"Head": [0, 10 * s(t * 11) * k]})
        elif tipo == "aplaude":
            sbb_sumar(P, {"RightUpperArm": [0, (10 + 10 * s(t * 15)) * k], "LeftUpperArm": [0, (10 + 10 * s(t * 15)) * k]})
        elif tipo == "risa":
            sbb_sumar(P, {"UpperTorso": [2.0 * s(t * 13) * k], "Head": [1.6 * s(t * 13 + 0.5) * k]})
            return 0.008 * abs(s(t * 13)) * k
        elif tipo == "saluda":
            sbb_sumar(P, {"RightLowerArm": [20 * s(t * 7) * k]})
        elif tipo == "nervioso":
            sbb_sumar(P, {"RightLowerArm": [4 * s(t * 11) * k], "LeftLowerArm": [4 * s(t * 11 + 2) * k], "Head": [0, 2.5 * s(t * 3) * k]})
        elif tipo == "enamorado":
            sbb_sumar(P, {"UpperTorso": [0, 2.5 * s(t * 2.2) * k], "Head": [0, 0, 3 * s(t * 2.2) * k]})
        elif tipo == "puno":
            sbb_sumar(P, {"RightLowerArm": [7 * max(0.0, s(t * 10)) * k]})
        return 0.0

    def _vida(self, aid, R, f, e, P, sentado, camina, quieto_brazos):
        t = f / FPS
        sd = (_h(aid) % 1000) / 100.0
        br = math.sin(2 * math.pi * t / 2.6 + sd)                         # respirar
        sbb_sumar(P, {"UpperTorso": [0.7 * br], "Head": [-0.3 * br]})
        sube = 0.005 * br * R.esc
        if not quieto_brazos:
            sbb_sumar(P, {"RightUpperArm": [1.5 * math.sin(t * 0.6 + sd), 0.8 * br], "LeftUpperArm": [1.5 * math.sin(t * 0.55 + sd + 2), 0.8 * br],
                          "RightLowerArm": [2.5 * math.sin(t * 0.7 + sd)], "LeftLowerArm": [2.5 * math.sin(t * 0.65 + sd + 1)]})
        if not sentado and not camina:                                     # cambia el peso de un pie al otro
            w = math.sin(2 * math.pi * t / 5.3 + sd * 1.7)
            sbb_sumar(P, {"LowerTorso": [0, 1.2 * w], "UpperTorso": [0, -0.9 * w], "Head": [0, 0, 0.7 * w]})
        # cabeza viva: deriva suave + miradas cortas cada tanto (no se queda fija como estatua)
        rnd = random.Random(_h((aid, f // 95)))
        objetivo = rnd.uniform(-5, 5) if rnd.random() < 0.5 else 0.0
        rnd2 = random.Random(_h((aid, f // 95 - 1)))
        antes = rnd2.uniform(-5, 5) if rnd2.random() < 0.5 else 0.0
        k = smr((f % 95) / 18.0)
        gira = antes + (objetivo - antes) * k
        sbb_sumar(P, {"Head": [1.0 * math.sin(t * 0.8 + sd), gira + 1.5 * math.sin(t * 0.45 + sd), 0.8 * math.sin(t * 0.6 + sd)]})
        return sube

    def hornear(self, tomas=None):
        tomas = set(tomas) if tomas else None
        for aid, R in self.rigs.items():
            rig = R.rig
            pbs = rig.pose.bones
            prev_e, prev_pos = {}, None
            suave, sube_s, toma_prev = {}, 0.0, None
            n_llaves = 0
            for f in sorted(R.estados):
                e = R.estados[f]
                if e.get("fuera"):
                    prev_pos = None
                    continue
                n = self._toma_de(f)
                if tomas and n not in tomas:
                    continue
                P = {k: list(v) if isinstance(v, (list, tuple)) else v for k, v in e["pose"].items()}
                sentado = bool(P.get("_sentado"))
                pos = e["pos"]
                camina = prev_pos is not None and (Vector(pos[:2]) - Vector(prev_pos[:2])).length * FPS > 0.6
                prev_pos = pos
                sube = e["sube"]
                if aid not in self.sin_vida:
                    sube += self._vida(aid, R, f, e, P, sentado, camina, n in self.sostiene[aid])
                for f0, tipo, kw in self.eventos[aid]:                    # gestos en su palabra
                    g = dict(GESTOS[tipo]); g.update({k: kw[k] for k in ("a", "h", "r") if k in kw})
                    k = self._env(f, f0, g)
                    if k <= 0:
                        continue
                    pose_g = dict(g["pose"]); pose_g.update(kw.get("pose", {}))
                    if pose_g:
                        objetivo = dict(P)
                        for b, v in pose_g.items():
                            if n in self.sostiene[aid] and b in BRAZOS:
                                continue                                   # si sostiene algo, los brazos no lo sueltan
                            objetivo[b] = list(v)
                        P = sbb.mezclar(P, objetivo, k) if k < 1 else objetivo
                    if tipo == "voltea":
                        sbb_sumar(P, {"Head": [0, kw.get("ang", 30) * k], "UpperTorso": [0, 0, kw.get("ang", 30) * 0.25 * k]})
                    if g.get("osc"):
                        sube += self._osc(g["osc"], f, f0, k, P, R) * R.esc
                    if g.get("salto") and not sentado:
                        u = (f - f0) / 12.0
                        if -0.25 < u < 0:
                            sube -= 0.6 * g["salto"] * R.alto * R.esc * math.sin(math.pi * (u + 0.25) / 0.25) * 0.5   # se agacha antes
                        elif 0 <= u <= 1:
                            sube += g["salto"] * R.alto * R.esc * math.sin(math.pi * u)
                for f0, f1, fuerza in self.hablas[aid]:                    # habla: quieto, solo la cabeza acompana suave
                    if f0 <= f <= f1 and self.voz_suave is not None:
                        k = smr((f - f0) / 8.0) * smr((f1 - f) / 10.0) * fuerza
                        v = float(self.voz_suave[min(max(f - 1, 0), len(self.voz_suave) - 1)])
                        sbb_sumar(P, {"Head": [2.2 * v * k + 0.8 * math.sin(f * 0.11) * k, 1.2 * math.sin(f * 0.07) * k, 1.0 * math.sin(f * 0.05) * k]})
                        if n not in self.sostiene[aid]:
                            sbb_sumar(P, {"RightUpperArm": [3 * v * k], "RightLowerArm": [5 * v * k]})
                for fa, fb, subida in self.flotes[aid]:                    # se lo lleva el globo
                    if fa <= f <= fb:
                        u = (f - fa) / float(max(1, fb - fa))
                        sube += subida * smr(u) * R.esc + 0.08 * math.sin(f * 0.15) * R.esc
                        sbb_sumar(P, {"RightUpperLeg": [18 + 14 * math.sin(f * 0.22)], "LeftUpperLeg": [18 - 14 * math.sin(f * 0.22 + 0.8)],
                                      "RightLowerLeg": [25 + 10 * math.sin(f * 0.22)], "LeftLowerLeg": [25 + 10 * math.sin(f * 0.22 + 0.8)]})
                if n != toma_prev:                                         # en el corte de toma no se suaviza (salto limpio)
                    suave, sube_s, toma_prev = {}, sube, n
                for b in list(P.keys()):                                   # filtro: todos los angulos se mueven suave, sin tirones
                    v = P[b]
                    if b.startswith("_") or not isinstance(v, list):
                        continue
                    if b in suave:
                        w = suave[b]
                        v = [w[i] + (v[i] - w[i]) * self.suavidad if i < len(w) else v[i] for i in range(len(v))]
                    suave[b] = list(v); P[b] = list(v)
                sube_s = sube_s + (sube - sube_s) * 0.6
                sube = sube_s
                B, loc = R.basis(P, sube, e["inclina"])
                for h, q in B.items():
                    eu = q.to_euler('XYZ', prev_e[h]) if h in prev_e else q.to_euler('XYZ')
                    prev_e[h] = eu.copy()
                    pbs[h].rotation_euler = eu
                    pbs[h].keyframe_insert("rotation_euler", frame=f, group=h)
                if "HumanoidRootPart" in pbs:
                    pbs["HumanoidRootPart"].location = loc
                    pbs["HumanoidRootPart"].keyframe_insert("location", frame=f, group="HumanoidRootPart")
                n_llaves += 1
            print("  actuacion %-9s %5d fotogramas, %d gestos, %d dialogos" % (aid, n_llaves, len(self.eventos[aid]), len(self.hablas[aid])))

    # ------------------------------------------------------------------ camara
    def golpes_camara(self):
        from bpy_extras import anim_utils
        hechos = 0
        for n, f0, fuerza in self.golpes:
            cam = next((c for c in bpy.data.objects if c.type == 'CAMERA' and c.name.startswith("CR_Cam_S%d_" % n)), None)
            if cam is None or not cam.animation_data or not cam.animation_data.action:
                continue
            ad = cam.animation_data
            cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
            if cb is None:
                continue
            loc = {i: cb.fcurves.find("location", index=i) for i in range(3)}
            cad = cam.data.animation_data
            lens_fc = None
            if cad and cad.action:
                cb2 = anim_utils.action_get_channelbag_for_slot(cad.action, cad.action_slot)
                lens_fc = cb2.fcurves.find("lens") if cb2 else None
            ti = self.sb["_tiempos"][n - 1]
            for f in range(f0, min(f0 + 14, ti["f_fin"]) + 1):
                d = (f - f0) / 14.0
                amp = fuerza * (1 - d) ** 2
                for i, fc in loc.items():
                    if fc is None:
                        continue
                    v = fc.evaluate(f) + 0.03 * amp * math.sin(f * (1.6 + i) + i)
                    fc.keyframe_points.insert(f, v, options={'FAST'})
                if lens_fc is not None:
                    lens_fc.keyframe_points.insert(f, lens_fc.evaluate(f) * (1 + 0.1 * amp), options={'FAST'})
            for fc in list(loc.values()) + [lens_fc]:
                if fc is not None:
                    fc.update()
            hechos += 1
        print("  golpes de camara:", hechos)


def sbb_sumar(P, extra):
    """suma angulos a la pose P (en su lugar)"""
    for b, v in extra.items():
        cur = list(P.get(b, [])) + [0, 0, 0]
        add = list(v) + [0, 0, 0]
        P[b] = [cur[i] + add[i] for i in range(3)]
