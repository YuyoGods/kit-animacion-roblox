# PUENTE STORYBOARD -> BLENDER: arma en el .blend del episodio lo que se aprobo en el navegador: las camaras con sus
# marcadores, los personajes (lugar, caminatas, poses, caras, saltos y miradas, una llave por fotograma como EP002) y
# los objetos como figuras sencillas en su lugar y momento. Despues el script del episodio solo pule y agrega detalle.
#
# 1) Desde un script de animacion del episodio (lo normal):
#      import sys; sys.path.insert(0, r"<kit>/Herramientas/storyboard"); import sb_blender as sbb
#      sb = sbb.leer()                       # lee <episodio>/storyboard/storyboard.json y los fotogramas de cada toma
#      sbb.armar_todo(sb, tomas=[1, 2], reemplazar=True)      # o por partes: crear_camaras / poner_personajes / poner_objetos
#      sbb.camara_en(sb, 3, 120)             # -> (lugar, mira, fov, giro) de la toma 3 en el fotograma 120
# 2) En el Blender abierto (con el .blend del episodio y los personajes ya anexados como <Modelo>_Rig):
#      py Herramientas/blender/bl.py Herramientas/storyboard/sb_blender.py
#    Arma lo que falte: nunca reemplaza camaras, personajes con animacion ni objetos que ya existan.
# 3) Sin ventana, sobre una COPIA:  blender.exe -b copia.blend --python sb_blender.py -- [storyboard.json] [--reemplazar] [--solo-camaras] [--guardar]
# Lo que NO hace (lo pone el script del episodio): dia/noche y luces, monstruos oscuros, manos exactas, objetos bonitos.
#
# Tiempos: si el episodio tiene audio/tomas_voz.json (voz aprobada) se usan sus fotogramas; si no, se estiman igual que
# en el navegador (web/tiempos.js). Solo toca la coleccion CR_Camaras (camaras CR_Cam_S#_<lugar>) y marcadores CR_S#_<lugar>.
import bpy, os, re, sys, json, math, unicodedata
from mathutils import Vector, Matrix

FPS = 30


def _raiz():
    try:
        d = os.path.dirname(os.path.abspath(__file__))
    except NameError:                                 # enviado con bl.py: se busca desde el .blend abierto
        d = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
    while not os.path.exists(os.path.join(d, "Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            raise SystemExit("No encuentro la carpeta del kit (Herramientas/config.py)")
        d = os.path.dirname(d)
    return d


RAIZ = _raiz()
CACHE = os.path.join(RAIZ, "Herramientas", "storyboard", "cache", "personajes")


# ------------------------------------------------------------------ tiempos (igual que web/tiempos.js)
def norm(p):
    p = unicodedata.normalize("NFD", p)
    p = "".join(c for c in p if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]", "", p)


def silabas(p):
    s = re.sub(r"y$", "i", norm(p))
    grupos = re.findall(r"[aeiou]+", s)
    if not grupos:
        return 1
    return max(1, sum(1 + len(re.findall(r"[aeo]{2}", g)) for g in grupos))


def palabras(texto):
    return [w for w in (texto or "").split() if norm(w)]


def estimar(sb):
    ritmo, respiro = sb.get("ritmo", 7.2), sb.get("respiro", 0.35)
    tomas, t = [], 0.0
    for tm in sb["tomas"]:
        pal, tt = [], t + 0.05
        for w in palabras(tm.get("texto")):
            d = silabas(w) / ritmo
            pal.append({"w": w, "t0": tt, "t1": tt + d})
            tt += d
            if re.search(r"[,;:][\"”»]?$", w):
                tt += 0.12
            elif re.search(r"[.!?…][\"”»]?$", w):
                tt += 0.08
        dur = max(tm.get("dur", 0), tt - t + respiro, tm.get("min", 0.8))
        tomas.append({"t0": t, "t1": t + dur, "palabras": pal})
        t += dur
    return tomas


def desde_voz(sb, tv):
    fps = tv.get("fps", FPS)
    por_toma = {}
    for p in tv.get("palabras", []):
        por_toma.setdefault(p["toma"], []).append({"w": p.get("texto", p["w"]), "t0": p["t0"], "t1": p["t1"]})
    tomas = []
    for i, tm in enumerate(sb["tomas"]):
        v = tv["tomas"][i]
        tomas.append({"t0": (v["f_ini"] - 1) / fps, "t1": v["f_fin"] / fps, "palabras": por_toma.get(v["n"], []),
                      "f_ini": v["f_ini"], "f_fin": v["f_fin"]})
    return tomas


def tiempo_en(ti, ref, desfase=0.0):
    dur = ti["t1"] - ti["t0"]
    if ref is None or ref == "inicio":
        t = 0.0
    elif isinstance(ref, (int, float)):
        t = dur + ref if ref < 0 else float(ref)
    elif ref == "fin":
        t = dur
    else:
        w, _, cual = str(ref).partition("#")
        obj, k, t = norm(w), 0, None
        for p in ti["palabras"]:
            if norm(p["w"]) == obj or (len(obj) > 3 and norm(p["w"]).startswith(obj)):
                k += 1
                if k == (int(cual) if cual else 1):
                    t = p["t0"] - ti["t0"]
                    break
        if t is None:
            print("  aviso: no encuentro la palabra '%s'" % ref)
            t = 0.0
    return min(max(t + (desfase or 0.0), 0.0), dur)


# ------------------------------------------------------------------ leer el storyboard
def leer(ruta=None):
    """ruta: storyboard.json; sin ruta, el de la carpeta del .blend abierto (Episodios/EP###/storyboard/)."""
    if ruta is None:
        ruta = os.path.join(os.path.dirname(bpy.data.filepath), "storyboard", "storyboard.json")
    sb = json.load(open(ruta, encoding="utf-8"))
    ep = os.path.dirname(os.path.dirname(os.path.abspath(ruta)))
    tv = os.path.join(ep, sb.get("tiempos_voz") or os.path.join("audio", "tomas_voz.json"))
    tomas = None
    if os.path.exists(tv):
        datos = json.load(open(tv, encoding="utf-8"))
        if len(datos.get("tomas", [])) == len(sb["tomas"]):
            tomas = desde_voz(sb, datos)
            print("Tiempos: de la voz (%s)" % os.path.relpath(tv, RAIZ))
        else:
            print("Aviso: la voz tiene %d lineas y el storyboard %d tomas: se estiman los tiempos"
                  % (len(datos.get("tomas", [])), len(sb["tomas"])))
    if tomas is None:
        tomas = estimar(sb)
        print("Tiempos: estimados (sin voz)")
    for ti in tomas:
        ti.setdefault("f_ini", int(round(ti["t0"] * FPS)) + 1)
        ti.setdefault("f_fin", int(round(ti["t1"] * FPS)))
    sb["_tiempos"] = tomas
    sb["_ruta"] = ruta
    return sb


# ------------------------------------------------------------------ personajes (para camaras que miran a alguien)
_altos = {}


def alto_de(sb, aid):
    spec = sb.get("reparto", {}).get(aid, {})
    modelo = spec.get("modelo", aid)
    if modelo not in _altos:
        meta = os.path.join(CACHE, modelo + ".json")
        _altos[modelo] = json.load(open(meta, encoding="utf-8")).get("altura", 5.0) if os.path.exists(meta) else 5.0
    return _altos[modelo] * spec.get("escala", 1.0)


PISO_RE = re.compile(r"Piso|Suelo|Banqueta|Asfalto|Cancha|Pasto|Camino|Colina|Tierra|Acera|Calle|Carretera|Explanada|Alfombra|Tapete|Escal", re.I)
NO_PISO_RE = re.compile(r"Techo|Faja|Dibujo|Linea|Logo|Pino|Arbol|Copa|Tronco|Farol|Jardinera", re.I)
_cache_piso = {}


def es_piso(o):
    for x in (o, o.parent):
        if x is None:
            continue
        if NO_PISO_RE.search(x.name):
            return False
        if PISO_RE.search(x.name):
            return True
    return False


def piso(x, y, z_sug=0.4):
    """z del PISO REAL (igual que web/escena.js): ignora mesas, sillas, cajas y objetos; nadie se sube a un mueble."""
    clave = (round(x, 2), round(y, 2), None if z_sug is None else round(z_sug, 1))
    if clave in _cache_piso:
        return _cache_piso[clave]
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    desde = 600.0 if z_sug is None else z_sug + 3.2
    lejos = 1200.0 if z_sug is None else 60.0
    o = Vector((x, y, desde))
    golpes = []
    for _ in range(16):                               # todos los golpes hacia abajo, del mas alto al mas bajo
        hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, o, Vector((0, 0, -1)), distance=lejos - (desde - o.z))
        if not hit:
            break
        golpes.append((loc.z, ob))
        o = Vector((x, y, loc.z - 0.01))
    z = 0.0 if z_sug is None else z_sug
    pisos = [g for g in golpes if g[1] is not None and es_piso(g[1])]
    if pisos:
        z = pisos[0][0]
    elif golpes:
        cerca = golpes if z_sug is None else [g for g in golpes if abs(g[0] - z_sug) < 1.6]
        z = (cerca or golpes)[-1][0]
    _cache_piso[clave] = z
    return z


def pos_actor(sb, n, aid, tl):
    """(x, y, z) del personaje en la toma n a los tl segundos (con su caminata, si tiene)."""
    tm, ti = sb["tomas"][n - 1], sb["_tiempos"][n - 1]
    spec = tm.get("actores", {}).get(aid)
    if not spec:
        return None
    p0 = spec.get("pos", [0, 0])
    x, y = p0[0], p0[1]
    c = spec.get("camina")
    if c:
        pts = [p0[:2]] + [p[:2] for p in (c.get("ruta") or ([c["a"]] if c.get("a") else []))]
        segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
        L = sum(segs)
        if L > 0:
            tipo = c.get("tipo") or ("correr" if c.get("vel", 0) > 8 else "caminar")
            vel = c.get("vel") or (11.5 if tipo == "correr" else 5.0)
            t0 = tiempo_en(ti, c.get("en", 0), c.get("desfase"))
            t1 = tiempo_en(ti, c["hasta"], c.get("desfase_hasta")) if "hasta" in c else t0 + L / vel
            u = 1.0 if t1 <= t0 else min(max((tl - t0) / (t1 - t0), 0.0), 1.0)
            d, acc, i = u * L, 0.0, 0
            while i < len(segs) - 1 and acc + segs[i] < d:
                acc += segs[i]
                i += 1
            f = 0.0 if segs[i] == 0 else min(max((d - acc) / segs[i], 0.0), 1.0)
            x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
            y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
    if "z" in spec:
        z = spec["z"]
    else:
        z = piso(x, y, None if spec.get("piso") == "alto" else (p0[2] if len(p0) > 2 else 0.4))
    return Vector((x, y, z))


def actores_de(sb, n):
    """{id: {"pos": Vector, "spec": {...}}} de la toma n (al inicio de la toma)."""
    tm = sb["tomas"][n - 1]
    return {aid: {"pos": pos_actor(sb, n, aid, 0.0), "spec": spec} for aid, spec in tm.get("actores", {}).items()}


# ------------------------------------------------------------------ camara (igual que calcCamara en web/app.js)
def _suave(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


CURVAS = {"suave": _suave, "lineal": lambda u: u, "rapido": lambda u: 1 - (1 - u) ** 2.4,
          "lento": lambda u: u ** 2.2, "corte": lambda u: 0.0 if u < 1 else 1.0}


def _ruido(t, s):
    return math.sin(t * 7.3 + s) * 0.5 + math.sin(t * 13.1 + s * 2.1) * 0.3 + math.sin(t * 23.7 + s * 3.7) * 0.2


_RIGS = {}                                            # personajes ya horneados (los usa la camara para mirarlos bien)


def _estado(aid, f):
    R = _RIGS.get(aid)
    e = R.estados.get(f) if R else None
    return (R, e) if e and not e["fuera"] else (None, None)


def rot_actor(sb, n, aid, tl, f):
    """hacia donde mira el cuerpo (grados, 0 = -Y)"""
    R, e = _estado(aid, f)
    if e:
        return e["rot"]
    spec = sb["tomas"][n - 1].get("actores", {}).get(aid, {})
    rot = spec.get("rot", 0.0)
    m = spec.get("mira_a")
    p = pos_actor(sb, n, aid, tl)
    if isinstance(m, (list, tuple)) and p is not None:
        rot = rot_hacia(p.x, p.y, m[0], m[1])
    return rot


def _punto(sb, n, ref, tl, f=None):
    if isinstance(ref, (list, tuple)):
        return Vector((ref[0], ref[1], ref[2] if len(ref) > 2 else 0.0))
    if isinstance(ref, str) and ref.startswith("actor:"):
        partes = ref.split(":")
        aid, parte = partes[1], (partes[2] if len(partes) > 2 else "pecho")
        R, e = _estado(aid, f) if f is not None else (None, None)
        if R is not None:
            if parte in ("der", "izq"):
                return R.mano(f, parte)
            if parte in ("cabeza", "cara", "tope", "boca"):
                return R.cabeza(f, parte)
            return e["pos"] + Vector((0, 0, R.alto * R.esc * 0.62))
        p = pos_actor(sb, n, aid, tl)
        if p is not None:
            k = {"cabeza": 0.86, "cara": 0.86, "tope": 1.0, "boca": 0.8}.get(parte, 0.62)
            return p + Vector((0, 0, alto_de(sb, aid) * k))
    if isinstance(ref, dict) and ref.get("de"):
        R, e = _estado(ref["de"], f) if f is not None else (None, None)
        p = e["pos"] if e else pos_actor(sb, n, ref["de"], tl)
        if p is not None:
            off = ref.get("off", [0, 0, 0])
            return p + Vector(off)
    return Vector((0, 0, 5))


def fov_de_lente(mm):
    return math.degrees(2 * math.atan(18 / mm))


def tercio(cara, pos, fov, tope=None):
    """la cara en el tercio superior (y que no se corte el gorro): igual que web/app.js"""
    tg = math.tan(math.radians(fov) / 2)
    d = (cara - pos).length
    mira = cara + Vector((0, 0, -d * tg / 3))
    if tope is not None:
        dt = (tope - pos).length
        ndc = (tope.z - mira.z) / (dt * tg)
        if ndc > 0.9:
            mira.z += (ndc - 0.9) * dt * tg
    return mira


def _encuadre(sb, n, c, fov, tl, f):
    """"encuadre": "cara" | "medio" | "entero" (igual que web/app.js)"""
    aid = c.get("actor")
    if not aid or aid not in sb["tomas"][n - 1].get("actores", {}):
        return None
    R, e = _estado(aid, f)
    suelo = e["pos"].copy() if e else pos_actor(sb, n, aid, tl)
    alto = alto_de(sb, aid)
    cab = (R.L["Head"] * R.esc) if R else alto * 0.21
    tipo = c["encuadre"]
    H = max(cab * 2.7, alto * 0.42) if tipo == "cara" else alto * 0.75 if tipo == "medio" else alto * 1.45
    tg = math.tan(math.radians(fov) / 2)
    d = (H / 2) / tg * c.get("distancia", 1.0)
    cara = _punto(sb, n, "actor:%s:cara" % aid, tl, f)
    tope = _punto(sb, n, "actor:%s:tope" % aid, tl, f)
    yaw = math.radians(rot_actor(sb, n, aid, tl, f) + c.get("angulo", 0))
    frente = Vector((math.sin(yaw), -math.cos(yaw), 0))
    h = (suelo.z + alto * 0.55 if tipo == "entero" else cara.z - alto * 0.1 if tipo == "medio" else cara.z) + c.get("altura", 0)
    for _ in range(8):
        pos = Vector((suelo.x, suelo.y, h)) + frente * d
        mira = suelo + Vector((0, 0, alto * 0.5)) if tipo == "entero" else tercio(cara, pos, fov)
        if tipo == "entero" or (tope.z - mira.z) / ((tope - pos).length * tg) <= 0.9:
            break
        d *= 1.08
    return pos, mira


def camara_en(sb, n, f):
    """(lugar, mira, fov vertical en grados, giro en grados) de la toma n en el fotograma f."""
    tm, ti = sb["tomas"][n - 1], sb["_tiempos"][n - 1]
    tl = (f - ti["f_ini"]) / FPS
    cam = tm.get("camara", {})
    claves = cam.get("claves")
    if not claves:
        if cam.get("pos") or cam.get("mira") or cam.get("encuadre"):
            claves = [{"t": 0, "pos": cam.get("pos"), "mira": cam.get("mira"), "fov": cam.get("fov"), "lente": cam.get("lente"),
                       "giro": cam.get("giro", 0), "encuadre": cam.get("encuadre"), "actor": cam.get("actor"), "angulo": cam.get("angulo", 0)}]
        else:
            ids = list(tm.get("actores", {}))
            claves = [{"t": 0, "encuadre": "medio", "actor": ids[0], "fov": 50}] if ids else [{"t": 0, "pos": [0, -20, 10], "mira": [0, 0, 4]}]
    ant = {"pos": Vector((0, -20, 10)), "mira": Vector((0, 0, 4)), "fov": 50.0, "giro": 0.0}
    ks = []
    for c in claves:
        fov = c.get("fov") if c.get("fov") is not None else (fov_de_lente(c["lente"]) if c.get("lente") else ant["fov"])
        en = _encuadre(sb, n, c, fov, tl, f) if c.get("encuadre") else None
        if en:
            pos, mira = en
        else:
            pos = _punto(sb, n, c["pos"], tl, f) if c.get("pos") is not None else ant["pos"].copy()
            mira = _punto(sb, n, c["mira"], tl, f) if c.get("mira") is not None else ant["mira"].copy()
            m = c.get("mira")
            if isinstance(m, str) and re.search(r":(cabeza|cara)$", m) and c.get("tercio") is True:
                aid = m.split(":")[1]
                mira = tercio(mira, pos, fov, _punto(sb, n, "actor:%s:tope" % aid, tl, f))
        k = {"pos": pos, "mira": mira, "fov": fov, "giro": c.get("giro", ant["giro"]), "curva": c.get("curva"),
             "_t": tiempo_en(ti, c.get("en", c.get("t", 0)), c.get("desfase"))}
        ks.append(k)
        ant = k
    ks.sort(key=lambda k: k["_t"])
    i = 0
    while i < len(ks) - 1 and tl >= ks[i + 1]["_t"]:
        i += 1
    a, b = ks[i], ks[min(i + 1, len(ks) - 1)]
    u = 1.0 if b is a or b["_t"] <= a["_t"] else min(max((tl - a["_t"]) / (b["_t"] - a["_t"]), 0.0), 1.0)
    e = CURVAS.get(b["curva"] or cam.get("curva") or "suave", _suave)(u)
    pos = a["pos"].lerp(b["pos"], e)
    mira = a["mira"].lerp(b["mira"], e)
    # "vivo": true (igual que el navegador): si la toma no se mueve, acercamiento lento de 5 % y temblor chico
    quieta = all((k["pos"] - ks[0]["pos"]).length < 0.02 and (k["mira"] - ks[0]["mira"]).length < 0.02
                 and abs(k["fov"] - ks[0]["fov"]) < 0.1 for k in ks)
    vivo = quieta and cam.get("vivo") is True
    if vivo:
        pos = pos.lerp(mira, 0.05 * _suave(tl / max(ti["t1"] - ti["t0"], 0.1)))
    amp = cam.get("temblor", 0.012 if vivo else 0)
    if amp:                                           # mismo temblor que el navegador (pasado a ejes de Blender)
        hz = cam.get("temblor_hz", 1)
        r = [_ruido(tl * hz, s) for s in (1, 2, 3, 4, 5)]
        pos += Vector((r[0], -r[2], r[1])) * amp
        mira += Vector((r[3], 0, r[4])) * amp * 0.4
    return pos, mira, a["fov"] + (b["fov"] - a["fov"]) * e, a["giro"] + (b["giro"] - a["giro"]) * e


# ------------------------------------------------------------------ crear camaras y marcadores
def _slug(t):
    t = norm(t or "")
    return (t[:16] or "toma").capitalize()


def _num(nombre, pref):
    m = re.match(pref + r"(\d+)", nombre)
    return int(m.group(1)) if m else None


def crear_camaras(sb, tomas=None, reemplazar=False, ajustar_rango=True):
    sc = bpy.context.scene
    tomas = tomas or list(range(1, len(sb["tomas"]) + 1))
    CC = bpy.data.collections.get("CR_Camaras")
    if CC is None:
        CC = bpy.data.collections.new("CR_Camaras")
        sc.collection.children.link(CC)
    existentes = {_num(o.name, "CR_Cam_S"): o for o in CC.objects if _num(o.name, "CR_Cam_S") is not None}
    hechas, saltadas = [], []
    for n in tomas:
        if n in existentes:
            if not reemplazar:
                saltadas.append(n)
                continue
            bpy.data.objects.remove(existentes[n])
            for m in list(sc.timeline_markers):
                if _num(m.name, "CR_S") == n:
                    sc.timeline_markers.remove(m)
        tm, ti = sb["tomas"][n - 1], sb["_tiempos"][n - 1]
        nombre = "CR_Cam_S%d_%s" % (n, _slug(tm.get("lugar")))
        cd = bpy.data.cameras.new(nombre)
        cd.sensor_fit = 'VERTICAL'
        cd.clip_start, cd.clip_end = 0.1, 5000
        cam = bpy.data.objects.new(nombre, cd)
        CC.objects.link(cam)
        cam["storyboard"] = n
        prev = None
        for f in range(ti["f_ini"], ti["f_fin"] + 1):
            loc, mira, fov, giro = camara_en(sb, n, f)
            cam.location = loc
            q = (mira - loc).to_track_quat('-Z', 'Y') @ Matrix.Rotation(math.radians(giro), 3, 'Z').to_quaternion()
            eu = q.to_euler('XYZ', prev) if prev else q.to_euler('XYZ')
            cam.rotation_euler = eu
            prev = eu.copy()
            cd.angle_y = math.radians(fov)
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_euler", frame=f)
            cd.keyframe_insert("lens", frame=f)
        mk = sc.timeline_markers.new("CR_S%d_%s" % (n, _slug(tm.get("lugar"))), frame=ti["f_ini"])
        mk.camera = cam
        hechas.append(n)
    if ajustar_rango and hechas:
        sc.frame_start = 1
        sc.frame_end = max(sc.frame_end, sb["_tiempos"][-1]["f_fin"])
        sc.render.fps = FPS
    print("Camaras creadas: %s" % (hechas or "ninguna"))
    if saltadas:
        print("Ya existian (no se tocaron): tomas %s. Para reemplazarlas: crear_camaras(sb, reemplazar=True)" % saltadas)
    return hechas


# ================================================================== PERSONAJES (igual que evaluarActor en web/app.js)
# Mismas poses (web/poses.json), mismos ciclos de caminar/correr, mismas caras, saltos y miradas que el navegador.
# Se hornea una llave por fotograma como en los scripts de EP002: lugar y giro en el objeto <Modelo>_Rig, rotaciones
# XYZ en los huesos, la cadera en HumanoidRootPart, IK apagado y "cara" del rig. Fuera de sus tomas, bajo el piso.
from mathutils import Quaternion
import bmesh

POSES_FIJAS = json.load(open(os.path.join(RAIZ, "Herramientas", "storyboard", "web", "poses.json"), encoding="utf-8"))
POSES_FIJAS.pop("_nota", None)
CICLOS = {
    "caminar": dict(muslo=26, rodilla=38, brazos=26, antebrazo=14, frente=16, torso=3, torsion=7, cadera=1.5, rebote=0.05, largo=3.0, vel=5.0),
    "correr": dict(muslo=40, rodilla=62, brazos=72, antebrazo=80, frente=16, torso=16, torsion=13, cadera=4.5, rebote=0.24, largo=4.6, vel=11.5),
}
CARAS_BASE = {"molesto": 1, "sorpresa": 2, "picaro": 3, "confundido": 4, "risa": 5, "triste": 6, "asustado": 7, "muy feliz": 8,
              "feliz": 8, "nervioso": 9, "preocupado": 10, "incredulo": 11, "bostezo": 12, "indignado": 13, "asombro": 14,
              "sonrisa": 15, "concentrado": 18, "gritando": 19, "decidido": 20, "angustiado": 17}
HUESOS = ["HumanoidRootPart", "LowerTorso", "UpperTorso", "Head", "RightUpperArm", "RightLowerArm", "RightHand",
          "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperLeg", "RightLowerLeg", "RightFoot",
          "LeftUpperLeg", "LeftLowerLeg", "LeftFoot"]
PARQUEO = Vector((0.0, 0.0, -500.0))
EX, EZ, EMY = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))   # ejes del personaje: lado, arriba, frente


def _q(eje, grados):
    return Quaternion(eje, math.radians(grados))


# Lo que un cuerpo puede hacer, en angulos "de persona" [adelante/doblar, afuera/voltear, giro/ladear]. Ninguna pose ni
# mezcla se pasa de aqui: nada de brazos que dan la vuelta completa ni rodillas al reves (igual en web/escena.js).
LIMITES = {
    "UpperArm": ((-60, 180), (-80, 178), (-90, 90)),
    "LowerArm": ((0, 150), (-60, 60), (0, 0)),
    "Hand": ((-75, 75), (-45, 45), (0, 0)),
    "UpperLeg": ((-50, 125), (-25, 60), (-45, 45)),
    "LowerLeg": ((0, 150), (0, 0), (0, 0)),
    "Foot": ((-45, 55), (0, 0), (0, 0)),
    "Head": ((-45, 50), (-80, 80), (-35, 35)),
    "Torso": ((-35, 60), (-50, 50), (-35, 35)),
}


def limitar(hueso, v):
    t = hueso.replace("Right", "").replace("Left", "")
    t = "Torso" if "Torso" in t else t
    lim = LIMITES.get(t)
    v = (list(v) + [0, 0, 0])[:3]
    if not lim:
        return v
    return [min(max(x, lo), hi) for x, (lo, hi) in zip(v, lim)]


def giro_de(hueso, v):
    """angulos 'de persona' -> giro en el espacio del rig (mismo que giroDe de web/escena.js)"""
    a, b, c = limitar(hueso, v)
    lado = -1 if hueso.startswith("Right") else 1
    if "UpperArm" in hueso or "UpperLeg" in hueso:
        return _q(EX, -a) @ _q(EMY, lado * b) @ _q(EZ, lado * c)
    if "LowerArm" in hueso or hueso.endswith("Hand"):
        return _q(EX, -a) @ _q(EZ, lado * b)
    if "LowerLeg" in hueso:
        return _q(EX, a)
    if hueso.endswith("Foot"):
        return _q(EX, -a)
    if hueso == "Head":
        return _q(EZ, b) @ _q(EX, a) @ _q(EMY, -c)
    return _q(EZ, c) @ _q(EMY, -b) @ _q(EX, a)


def pose_de(p, t):
    if not p:
        return POSES_FIJAS["parado"]
    if isinstance(p, dict):
        return p
    if p == "saludar":
        return {"RightUpperArm": [20, 150], "RightLowerArm": [25 + 25 * math.sin(t * 9)], "LeftUpperArm": [0, 4], "Head": [0, -8]}
    if p == "temblando":
        return {"RightUpperArm": [40, 0], "LeftUpperArm": [40, 0], "RightLowerArm": [125], "LeftLowerArm": [125],
                "UpperTorso": [-6 + math.sin(t * 40) * 1.5, math.sin(t * 33) * 2], "Head": [-4, math.sin(t * 29) * 3]}
    if p == "respirar":
        return {"RightUpperArm": [0, 4 + math.sin(t * 2) * 1.5], "LeftUpperArm": [0, 4 + math.sin(t * 2) * 1.5],
                "UpperTorso": [math.sin(t * 2) * 1.2]}
    if p not in POSES_FIJAS:
        print("  aviso: pose desconocida '%s'" % p)
    return POSES_FIJAS.get(p, POSES_FIJAS["parado"])


def mezclar(a, b, k):
    if k <= 0:
        return a
    if k >= 1:
        return b
    r = {}
    for n in set(a) | set(b):
        if n.startswith("_"):
            r[n] = a.get(n) if k < 0.5 else b.get(n)
            continue
        va, vb = list(a.get(n, [])) + [0, 0, 0], list(b.get(n, [])) + [0, 0, 0]
        r[n] = [va[i] * (1 - k) + vb[i] * k for i in range(3)]
    return r


def sumar(a, extra):
    r = dict(a)
    for n, v in extra.items():
        base = list(r.get(n, [])) + [0, 0, 0]
        v = list(v) + [0, 0, 0]
        r[n] = [base[i] + v[i] for i in range(3)]
    return r


def ciclo(tipo, fase, largo_pierna):
    c = CICLOS.get(tipo, CICLOS["caminar"])
    s, co = math.sin(fase), math.cos(fase)
    br_d, br_i = -c["brazos"] * s, c["brazos"] * s
    pose = {
        "RightUpperLeg": [c["muslo"] * s, 2], "LeftUpperLeg": [-c["muslo"] * s, 2],
        "RightLowerLeg": [5 + c["rodilla"] * max(0, co) ** 2], "LeftLowerLeg": [5 + c["rodilla"] * max(0, -co) ** 2],
        "RightFoot": [max(0, -c["muslo"] * s) * 0.3], "LeftFoot": [max(0, c["muslo"] * s) * 0.3],
        "RightUpperArm": [br_d, 6], "LeftUpperArm": [br_i, 6],
        "RightLowerArm": [c["antebrazo"] + c["frente"] * max(0, br_d / c["brazos"])],
        "LeftLowerArm": [c["antebrazo"] + c["frente"] * max(0, br_i / c["brazos"])],
        "UpperTorso": [c["torso"], 0, c["torsion"] * s], "LowerTorso": [0, 0, -c["cadera"] * s],
        "Head": [-c["torso"] * 0.5, -c["torsion"] * s * 0.6],
    }
    baja = -largo_pierna * (1 - math.cos(math.radians(c["muslo"]) * s))
    return pose, baja + c["rebote"] * (0.5 + 0.5 * math.cos(2 * fase))


def rot_hacia(x, y, tx, ty):
    dx, dy = tx - x, ty - y
    if abs(dx) + abs(dy) < 1e-6:
        return 0.0
    return math.degrees(math.atan2(dx, -dy))


def camino(spec, tl, ti, p0):
    c = spec.get("camina")
    if not c:
        return None
    pts = [p0[:2]] + [p[:2] for p in (c.get("ruta") or ([c["a"]] if c.get("a") else []))]
    if len(pts) < 2:
        return None
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    L = sum(segs)
    tipo = c.get("tipo") or ("correr" if c.get("vel", 0) > 8 else "caminar")
    vel = c.get("vel") or CICLOS[tipo]["vel"]
    t0 = tiempo_en(ti, c.get("en", 0), c.get("desfase"))
    t1 = tiempo_en(ti, c["hasta"], c.get("desfase_hasta")) if "hasta" in c else t0 + L / vel
    u = 1.0 if t1 <= t0 else min(max((tl - t0) / (t1 - t0), 0.0), 1.0)
    d, acc, i = u * L, 0.0, 0
    while i < len(segs) - 1 and acc + segs[i] < d:
        acc += segs[i]
        i += 1
    f = 0.0 if segs[i] == 0 else min(max((d - acc) / segs[i], 0.0), 1.0)
    peso = min(1.0, (tl - t0) / 0.2, (t1 - tl) / 0.2) if t0 < tl < t1 else 0.0
    return {"x": pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, "y": pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f,
            "rot": rot_hacia(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]), "peso": peso,
            "fase": 2 * math.pi * d / CICLOS[tipo]["largo"], "tipo": tipo, "llego": tl >= t1}


class Rig:
    """un personaje del reparto en el .blend: rig, huesos en reposo y como ponerle una pose"""

    def __init__(self, sb, aid):
        rep = sb.get("reparto", {}).get(aid, {})
        self.aid, self.rep = aid, rep
        self.rig = bpy.data.objects.get(rep.get("rig") or rep.get("modelo", aid) + "_Rig")
        if self.rig is None:
            return
        bs = self.rig.data.bones
        self.W = {b.name: b.matrix_local.to_quaternion() for b in bs}
        self.Winv = {k: q.inverted() for k, q in self.W.items()}
        self.rel = {b.name: (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local.copy() for b in bs}
        self.par = {b.name: b.parent.name if b.parent else None for b in bs}
        self.L = {b.name: b.length for b in bs}
        self.cadera = bs["HumanoidRootPart"].head_local.z if "HumanoidRootPart" in bs else 2.0
        self.esc = float(rep.get("escala", 1.0))
        self.alto = alto_de(sb, aid) / self.esc
        self.caras = dict(CARAS_BASE, **{k.lower(): v for k, v in rep.get("caras", {}).items()})
        self.estados = {}

    def basis(self, pose, sube, inclina):
        B = {}
        for h in HUESOS:
            if h not in self.W:
                continue
            if h == "HumanoidRootPart":
                inc = (list(inclina or []) + [0, 0, 0])[:3]
                R = _q(EZ, inc[2]) @ _q(EMY, -inc[1]) @ _q(EX, inc[0])
            elif h in pose:
                R = giro_de(h, pose[h])
            else:
                B[h] = Quaternion()
                continue
            B[h] = self.Winv[h] @ R @ self.W[h]
        loc = self.Winv["HumanoidRootPart"] @ Vector((0, 0, sube / self.esc)) if "HumanoidRootPart" in self.W else Vector()
        return B, loc

    def fk(self, B, loc):
        M = {}

        def m(b):
            if b in M:
                return M[b]
            q = B.get(b, Quaternion())
            bas = q.to_matrix().to_4x4()
            if b == "HumanoidRootPart":
                bas = Matrix.Translation(loc) @ bas
            p = self.par[b]
            M[b] = (m(p) if p else Matrix.Identity(4)) @ self.rel[b] @ bas
            return M[b]
        for b in self.rel:
            m(b)
        return M

    def mundo(self, f):
        """matriz del rig en el mundo y matrices de los huesos en ese fotograma (o None si no sale)"""
        e = self.estados.get(f)
        if e is None or e["fuera"]:
            return None
        mw = Matrix.Translation(e["pos"]) @ Matrix.Rotation(math.radians(e["rot"]), 4, 'Z') @ Matrix.Scale(self.esc, 4)
        return mw, self.fk(e["B"], e["loc"])

    def mano(self, f, lado):
        r = self.mundo(f)
        if r is None:
            return None
        mw, M = r
        b = ("Right" if lado == "der" else "Left") + "Hand"
        return mw @ M[b] @ Vector((0, self.L[b] * 0.75, 0))

    def cabeza(self, f, parte="cara"):
        """centro de la cabeza ("cara"/"cabeza"), punta del gorro ("tope") o boca, desde el hueso Head"""
        r = self.mundo(f)
        if r is None:
            return None
        mw, M = r
        L = self.L["Head"]
        if parte == "tope":
            return mw @ M["Head"] @ Vector((0, L * 1.25, 0))
        if parte == "boca":
            frente = self.Winv["Head"] @ EMY
            return mw @ M["Head"] @ (Vector((0, L * 0.28, 0)) + frente * (L * 0.55))
        return mw @ M["Head"] @ Vector((0, L * 0.5, 0))

    def arriba(self, f):
        e = self.estados.get(f)
        return None if e is None or e["fuera"] else e["pos"] + Vector((0, 0, (self.alto + 0.4) * self.esc))


def _bump(u):
    return 0.0 if u <= 0 or u >= 1 else math.sin(math.pi * u)


def estado_actor(sb, n, R, spec, tl, f):
    """lo mismo que evaluarActor (web/app.js): lugar, giro, pose, cara y cadera del personaje en ese momento"""
    ti = sb["_tiempos"][n - 1]
    acc = []
    for ac in spec.get("acciones", []):              # "muerde": true -> pose "morder" 0,25 s antes y regresa (igual que el navegador)
        t = tiempo_en(ti, ac.get("en", ac.get("t", 0)), ac.get("desfase"))
        acc.append({**ac, "_t": t})
        if ac.get("muerde") and not ac.get("pose"):
            acc += [{"_t": max(0.0, t - 0.25), "pose": "morder", "_antes": True}, {"_t": t + 0.35, "pose": "_volver"}]
    acc.sort(key=lambda a: a["_t"])
    prev = cur = antes = spec.get("pose", "parado")
    tc, cara, mira, t_mira = -1e9, spec.get("cara"), spec.get("mira"), -1e9
    for ac in acc:
        if ac["_t"] > tl:
            break
        if ac.get("pose"):
            nueva = antes if ac["pose"] == "_volver" else ac["pose"]
            if ac.get("_antes"):
                antes = cur
            prev, cur, tc = cur, nueva, ac["_t"]
        if "cara" in ac:
            cara = ac["cara"]
        if "mira" in ac:
            mira, t_mira = ac["mira"], ac["_t"]
    pose = mezclar(pose_de(prev, tl), pose_de(cur, tl), _suave((tl - tc) / spec.get("mezcla", 0.25)))
    sube = sum(ac["salto"] * R.esc * _bump((tl - ac["_t"]) / ac.get("salto_dur", 0.45)) for ac in acc if ac.get("salto"))
    p0 = spec.get("pos", [0, 0])
    x, y = p0[0], p0[1]
    cam_pos = None

    def xy_de(ref):
        nonlocal cam_pos
        if isinstance(ref, (list, tuple)):
            return ref[0], ref[1]
        if ref == "camara":
            cam_pos = cam_pos or camara_en(sb, n, f)[0]
            return cam_pos.x, cam_pos.y
        p = pos_actor(sb, n, ref, tl)
        return (p.x, p.y) if p is not None else None

    rot = spec.get("rot", 0.0)
    if spec.get("mira_a"):
        o = xy_de(spec["mira_a"])
        if o:
            rot = rot_hacia(x, y, *o)
    mov = camino(spec, tl, ti, p0)
    if mov:
        x, y = mov["x"], mov["y"]
        if not mov["llego"] or (not spec.get("mira_a") and "rot" not in spec):
            rot = mov["rot"]
        elif spec.get("mira_a"):
            o = xy_de(spec["mira_a"])
            if o:
                rot = rot_hacia(x, y, *o)
        if mov["peso"] > 0:
            cp, cs = ciclo(mov["tipo"], mov["fase"], R.cadera)
            pose = mezclar(pose, cp, mov["peso"])
            sube += cs * R.esc * mov["peso"]
    if "z" in spec:
        z = spec["z"]
    else:
        z = piso(x, y, None if spec.get("piso") == "alto" else (p0[2] if len(p0) > 2 else 0.4))
    if pose.get("_sentado"):
        sube += spec.get("asiento", z + 1.3) - z + 0.45 * R.esc - R.cadera * R.esc
    if pose.get("_baja"):
        sube -= pose["_baja"] * R.cadera * R.esc
    if mira:                                          # la cabeza voltea a lo que mira (y un poco el torso)
        if mira == "camara":
            obj = cam_pos or camara_en(sb, n, f)[0]
        elif isinstance(mira, (list, tuple)):
            obj = Vector((mira[0], mira[1], mira[2] if len(mira) > 2 else 5.0))
        else:
            ida = mira.split(":")[1] if mira.startswith("actor:") else mira
            p = pos_actor(sb, n, ida, tl)
            obj = p + Vector((0, 0, alto_de(sb, ida) * 0.86)) if p is not None else None
        if obj is not None:
            d = obj - Vector((x, y, z + R.alto * 0.86 * R.esc))
            d.rotate(Matrix.Rotation(-math.radians(rot), 3, 'Z'))
            voltear = max(-75.0, min(75.0, math.degrees(math.atan2(d.x, -d.y))))
            abajo = max(-35.0, min(35.0, math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y)))))
            k = _suave((tl - t_mira) / 0.3)
            pose = sumar(pose, {"Head": [abajo * 0.8 * k, voltear * 0.75 * k], "UpperTorso": [0, 0, voltear * 0.25 * k]})
    return {"pos": Vector((x, y, z)), "rot": rot, "pose": pose, "sube": sube, "inclina": spec.get("inclina"), "cara": cara}


def _llaves_fuera(o, fa, fb):
    """borra las llaves de o (y de sus huesos) entre fa y fb"""
    ad = o.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    curvas = []
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        curvas = list(act.fcurves)
    else:                                             # acciones por capas (Blender 4.4+)
        for capa in getattr(act, "layers", []):
            for tira in capa.strips:
                for cb in tira.channelbags:
                    curvas += list(cb.fcurves)
    for fc in curvas:
        for k in [k for k in fc.keyframe_points if fa - 0.5 <= k.co.x <= fb + 0.5][::-1]:
            fc.keyframe_points.remove(k)


def _rangos(sb, tomas):
    return [(sb["_tiempos"][n - 1]["f_ini"], sb["_tiempos"][n - 1]["f_fin"]) for n in tomas]


def poner_personajes(sb, tomas=None, reemplazar=False):
    """hornea a cada personaje del reparto en las tomas pedidas. Devuelve {id: Rig} (lo usan los objetos)."""
    tomas = tomas or list(range(1, len(sb["tomas"]) + 1))
    rigs = {}
    for aid in sb.get("reparto", {}):
        R = Rig(sb, aid)
        if R.rig is None:
            print("  aviso: no hay rig para '%s' (%s_Rig) en este .blend: se salta" % (aid, R.rep.get("modelo", aid)))
            continue
        ad = R.rig.animation_data
        if ad and ad.action and not reemplazar:
            print("  %s ya tiene animacion: no se toca (usa reemplazar=True para rehacer estas tomas)" % R.rig.name)
            continue
        rigs[aid] = R
    if not rigs:
        return rigs
    _RIGS.update(rigs)
    # 1) medir todo con los personajes apartados (asi los rayos del piso no chocan con ellos)
    guardado = {aid: (R.rig.location.copy(), R.rig.animation_data.action if R.rig.animation_data else None) for aid, R in rigs.items()}
    for R in rigs.values():
        if R.rig.animation_data:
            R.rig.animation_data.action = None
        R.rig.location = PARQUEO
    bpy.context.view_layer.update()
    for n in tomas:
        tm, ti = sb["tomas"][n - 1], sb["_tiempos"][n - 1]
        for aid, R in rigs.items():
            spec = tm.get("actores", {}).get(aid)
            for f in range(ti["f_ini"], ti["f_fin"] + 1):
                if not spec:
                    R.estados[f] = {"fuera": True}
                    continue
                e = estado_actor(sb, n, R, spec, (f - ti["f_ini"]) / FPS, f)
                e["B"], e["loc"] = R.basis(e["pose"], e["sube"], e["inclina"])
                e["fuera"] = False
                R.estados[f] = e
    for aid, R in rigs.items():
        loc, act = guardado[aid]
        R.rig.location = loc
        if act is not None:
            R.rig.animation_data.action = act
    # 2) hornear (una llave por fotograma, solo en el tramo de las tomas)
    for aid, R in rigs.items():
        rig = R.rig
        for fa, fb in _rangos(sb, tomas):
            _llaves_fuera(rig, fa, fb)
        rig.rotation_mode = 'XYZ'
        if abs(rig.scale.x - R.esc) > 1e-6:
            rig.scale = (R.esc, R.esc, R.esc)
        pbs = rig.pose.bones
        for h in HUESOS:
            if h in pbs:
                pbs[h].rotation_mode = 'XYZ'
        prev_e, prev_yaw, cara_prev = {}, None, None
        for f in sorted(R.estados):
            e = R.estados[f]
            if e["fuera"]:
                rig.location = PARQUEO
                rig.keyframe_insert("location", frame=f)
                continue
            for k in ("IK_Piernas", "IK_Brazos"):
                if k in rig.keys():
                    rig[k] = 0.0
                    rig.keyframe_insert('["%s"]' % k, frame=f)
            yaw = math.radians(e["rot"])
            if prev_yaw is not None:
                while yaw - prev_yaw > math.pi:
                    yaw -= 2 * math.pi
                while yaw - prev_yaw < -math.pi:
                    yaw += 2 * math.pi
            prev_yaw = yaw
            rig.location = e["pos"]
            rig.rotation_euler = (0, 0, yaw)
            rig.keyframe_insert("location", frame=f)
            rig.keyframe_insert("rotation_euler", index=2, frame=f)
            for h, q in e["B"].items():
                eu = q.to_euler('XYZ', prev_e[h]) if h in prev_e else q.to_euler('XYZ')
                prev_e[h] = eu.copy()
                pbs[h].rotation_euler = eu
                pbs[h].keyframe_insert("rotation_euler", frame=f, group=h)
            if "HumanoidRootPart" in pbs:
                pbs["HumanoidRootPart"].location = e["loc"]
                pbs["HumanoidRootPart"].keyframe_insert("location", frame=f, group="HumanoidRootPart")
            if "cara" in rig.keys():
                c = e["cara"]
                num = c if isinstance(c, int) else R.caras.get(str(c).lower()) if c else None
                if num is None:
                    num = cara_prev if cara_prev is not None else int(rig.get("cara", 15))
                if num != cara_prev:
                    if cara_prev is not None:
                        rig["cara"] = cara_prev
                        rig.keyframe_insert('["cara"]', frame=f - 1)
                    rig["cara"] = int(num)
                    rig.keyframe_insert('["cara"]', frame=f)
                    cara_prev = num
        print("  %s: %d fotogramas horneados" % (rig.name, len(R.estados)))
    return rigs


# ================================================================== OBJETOS (marcadores de lugar)
# En Blender salen como figuras sencillas de su color, en el lugar y momento del storyboard (la mano, la cabeza...).
# El objeto bonito de verdad (helado, burbuja...) lo hace despues el script del episodio en ese mismo lugar.
_FORMAS = {"burbuja": ("esfera", 1.0, "#ffffff"), "helado": ("cono", 0.6, "#ff86ae"), "globo": ("esfera", 0.7, "#ff4f7b"),
           "pastel": ("cilindro", 1.0, "#f6d6e8"), "pan": ("esfera", 0.5, "#d49a52"), "nube": ("esfera", 1.2, "#9aa4b2"),
           "campana": ("cono", 1.2, "#d9a520"), "puf": ("esfera", 0.8, "#ffffff")}


def _hex(c):
    c = c.lstrip("#")
    return [((int(c[i:i + 2], 16) / 255) ** 2.2) for i in (0, 2, 4)] + [1.0]


def _malla(nombre, forma, r):
    me = bpy.data.meshes.new(nombre)
    bm = bmesh.new()
    if forma == "esfera":
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    elif forma == "cono":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.01, radius2=r, depth=r * 2.4,
                              matrix=Matrix.Translation((0, 0, r * 1.2)))
    elif forma == "cilindro":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=r * 0.8,
                              matrix=Matrix.Translation((0, 0, r * 0.4)))
    else:
        bmesh.ops.create_cube(bm, size=r * 2, matrix=Matrix.Translation((0, 0, r)))
    bm.to_mesh(me)
    bm.free()
    return me


def poner_objetos(sb, rigs, tomas=None, reemplazar=False):
    sc = bpy.context.scene
    tomas = tomas or list(range(1, len(sb["tomas"]) + 1))
    col = bpy.data.collections.get("SB_Objetos")
    if col is None:
        col = bpy.data.collections.new("SB_Objetos")
        sc.collection.children.link(col)
    hechos = 0
    for n in tomas:
        tm, ti = sb["tomas"][n - 1], sb["_tiempos"][n - 1]
        for i, sp in enumerate(tm.get("objetos", [])):
            tipo = sp.get("tipo", "caja")
            nombre = "SB_T%d_%s_%d" % (n, tipo, i + 1)
            viejo = bpy.data.objects.get(nombre)
            if viejo is not None:
                if not reemplazar:
                    continue
                bpy.data.objects.remove(viejo)
            forma, r, color = _FORMAS.get(tipo, ("caja", 0.5, "#c9a26b"))
            o = bpy.data.objects.new(nombre, _malla(nombre, forma, r))
            col.objects.link(o)
            m = bpy.data.materials.new(nombre)
            m.diffuse_color = _hex(sp.get("color", color))
            m.use_nodes = True
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = _hex(sp.get("color", color))
            o.data.materials.append(m)
            o["storyboard"] = {"toma": n, "tipo": tipo}
            t_in = tiempo_en(ti, sp.get("en", 0), sp.get("desfase"))
            dur = ti["t1"] - ti["t0"]
            t_out = tiempo_en(ti, sp["hasta"], sp.get("desfase_hasta")) if "hasta" in sp else (t_in + 0.35 if tipo == "puf" else dur + 1)
            esc0 = sp.get("escala", 0.55 if tipo == "burbuja" else 1.0)
            for f in range(ti["f_ini"] - 1, ti["f_fin"] + 2):
                tl = (f - ti["f_ini"]) / FPS
                p = None
                if ti["f_ini"] <= f <= ti["f_fin"] and t_in <= tl < t_out:
                    if sp.get("mano"):
                        R = rigs.get(sp["mano"][0])
                        lado = sp["mano"][1] if len(sp["mano"]) > 1 else "der"
                        if R:
                            p = (R.mano(f, "der") + R.mano(f, "izq")) / 2 if lado == "ambas" and R.mano(f, "der") else R.mano(f, lado)
                    elif sp.get("de") or sp.get("sobre"):
                        R = rigs.get(sp.get("de") or sp.get("sobre"))
                        a = R.arriba(f) if R else None
                        if a is not None and sp.get("de"):
                            cpos, cmira, _, _ = camara_en(sb, n, f)
                            der = (cmira - cpos).cross(Vector((0, 0, 1))).normalized()
                            p = a + der * sp.get("lado", 1) * 1.3 * R.esc + Vector((0, 0, 0.5 * R.esc))
                        elif a is not None:
                            p = a + Vector((0, 0, sp.get("alto", 0.6)))
                    if p is None:
                        q = list(sp.get("pos", [0, 0, 0])) + [0, 0, 0]
                        p = Vector(q[:3])
                        if sp.get("piso"):
                            p.z = piso(q[0], q[1], q[2] or 0.4) + sp.get("altura", 0)
                    if sp.get("off"):
                        p = p + Vector((list(sp["off"]) + [0, 0, 0])[:3])
                    if sp.get("sube"):
                        p.z += sp["sube"] * (tl - t_in)
                    td = tl - t_in
                    s = esc0
                    if sp.get("pop") or tipo == "burbuja":
                        u = min(max(td / 0.28, 0.0), 1.0)
                        s *= (u / 0.6) * 1.22 if u < 0.6 else 1.22 - 0.22 * ((u - 0.6) / 0.4)
                    if tipo == "puf":
                        s *= 0.5 + 1.0 * min(max(td / 0.35, 0.0), 1.0)
                    o.location, o.scale = p, (max(s, 1e-4),) * 3
                else:
                    o.location, o.scale = PARQUEO, (0.0, 0.0, 0.0)
                o.keyframe_insert("location", frame=f)
                o.keyframe_insert("scale", frame=f)
            hechos += 1
    print("Objetos (marcadores de lugar) creados: %d" % hechos)


def armar_todo(sb=None, tomas=None, reemplazar=False):
    """camaras + personajes + objetos del storyboard, de una vez"""
    sb = sb or leer()
    rigs = poner_personajes(sb, tomas=tomas, reemplazar=reemplazar)   # primero ellos: asi la camara los mira donde estan
    crear_camaras(sb, tomas=tomas, reemplazar=reemplazar)
    poner_objetos(sb, rigs, tomas=tomas, reemplazar=reemplazar)
    return rigs


if __name__ in ("__main__", "builtins"):              # "builtins" = enviado con bl.py al Blender abierto
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ruta = next((a for a in args if a.endswith(".json")), None)
    sb = leer(ruta)
    if "--solo-camaras" in args:
        crear_camaras(sb, reemplazar="--reemplazar" in args)
    else:
        armar_todo(sb, reemplazar="--reemplazar" in args)
    if "--guardar" in args and bpy.data.filepath:
        bpy.ops.wm.save_mainfile()
        print("Guardado:", bpy.data.filepath)
