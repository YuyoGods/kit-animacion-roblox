# La voz manda el ritmo: calcula las tomas del episodio a partir de la voz ya lista (y aprobada por el usuario).
# Cada linea de narracion.txt = una toma. La toma empieza justo con su primera palabra (corte en la palabra) y
# termina donde empieza la siguiente; la ultima se sostiene un poco al final.
#   py Herramientas/audio/tomas_desde_voz.py EP###_Titulo [--inicio 0.05] [--cola 0.6]
# Usa, en este orden:
#   1) audio/voz_palabras.json  (voz recortada con recortar_pausas.py; sirve tambien para voces propias via Whisper)
#   2) audio/narracion_tiempos.json  (voz de ElevenLabs sin recortar)
# Deja: audio/tomas_voz.json -> {"fps", "frames", "voz_inicio", "audio", "tomas": [...], "palabras": [...]}
#   (los scripts de animacion leen las tomas de ahi; "palabras" sirve para sincronizar golpes, ej. "pum")
import difflib, json, math, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FPS, episodio  # noqa: E402

args = list(sys.argv[1:])


def opcion(nombre, defecto):
    if nombre in args:
        i = args.index(nombre); v = float(args[i + 1]); del args[i:i + 2]; return v
    return defecto


INICIO = opcion("--inicio", 0.05)      # segundo del video donde empieza la voz
COLA = opcion("--cola", 0.6)           # segundos que se sostiene la ultima toma despues de la ultima palabra
if not args:
    sys.exit("Uso: py tomas_desde_voz.py EP###_Nombre [--inicio 0.05] [--cola 0.6]")
EP = episodio(args[0])
AUD = os.path.join(EP, "audio")
lineas = [l.strip() for l in open(os.path.join(EP, "narracion.txt"), encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


def cuadro(t):                  # segundo -> fotograma (el fotograma 1 es el segundo 0)
    return int(math.floor(t * FPS + 1e-6)) + 1


# ---- palabras de la voz con su tiempo
vp_path = os.path.join(AUD, "voz_palabras.json")
if os.path.exists(vp_path):
    vp = json.load(open(vp_path, encoding="utf-8"))
    pal = [dict(p, w=norm(p["texto"])) for p in vp["palabras"]]
    audio = "voz.wav"
else:
    al = json.load(open(os.path.join(AUD, "narracion_tiempos.json"), encoding="utf-8"))
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    pal, i = [], 0
    while i < len(ch):
        if ch[i].isspace():
            i += 1; continue
        j = i
        while j < len(ch) and not ch[j].isspace():
            j += 1
        letras = [k for k in range(i, j) if ch[k].isalnum()]
        if letras:
            pal.append({"texto": "".join(ch[i:j]), "w": norm("".join(ch[i:j])), "t0": st[letras[0]], "t1": en[letras[-1]]})
        i = j
    audio = "narracion.mp3"

# ---- emparejar las palabras del guion con las que se oyen (tolera palabras mal entendidas)
guion = [(k, norm(w), w) for k, l in enumerate(lineas) for w in l.split() if norm(w)]


def emparejar():
    sm = difflib.SequenceMatcher(a=[w for _, w, _ in guion], b=[p["w"] for p in pal], autojunk=False)
    m = {}
    for bl in sm.get_matching_blocks():
        for d in range(bl.size):
            m[bl.a + d] = bl.b + d
    return m


mapa = emparejar()
# ---- onomatopeyas que Whisper no escribe (¡Miau!, ¡Pum!): si una palabra del guion no se oyo, pero en su hueco la
#      revision de recortar_pausas encontro un "sonido de mas", esa palabra ES ese sonido (asi los golpes y el
#      subtitulo caen en su momento).
if os.path.exists(vp_path):
    sonidos = []
    for pr in (vp.get("revision") or {}).get("problemas", []):
        if pr.get("tipo") == "sonido de mas" and pr.get("t") is not None:
            m_ = re.search(r"([0-9.]+) s", pr.get("detalle", ""))
            sonidos.append((float(pr["t"]), float(m_.group(1)) if m_ else 0.3))
    nuevos = []
    for gi, (k, w, crudo) in enumerate(guion):
        if gi in mapa:
            continue
        ant = max([g for g in mapa if g < gi], default=None); sig = min([g for g in mapa if g > gi], default=None)
        lo = pal[mapa[ant]]["t1"] if ant is not None else 0.0
        hi = pal[mapa[sig]]["t0"] if sig is not None else 1e9
        hay = [sn for sn in sonidos if lo - 0.05 <= sn[0] <= hi + 0.05]
        if hay:
            sonidos.remove(hay[0])
            nuevos.append({"texto": crudo, "w": w, "t0": hay[0][0], "t1": hay[0][0] + hay[0][1]})
            print("Palabra sin texto en Whisper (onomatopeya): %s -> el sonido de %.2f s" % (crudo, hay[0][0]))
    if nuevos:
        pal = sorted(pal + nuevos, key=lambda p: p["t0"])
        mapa = emparejar()
ini_linea, fin_linea = {}, {}
for gi, (k, _, _) in enumerate(guion):
    if gi in mapa:
        ini_linea.setdefault(k, mapa[gi]); fin_linea[k] = mapa[gi]
faltan = [k for k in range(len(lineas)) if k not in ini_linea]
for k in faltan:                # linea sin pareja: se reparte entre sus vecinas
    ant = max([j for j in ini_linea if j < k], default=None); sig = min([j for j in ini_linea if j > k], default=None)
    if ant is not None and sig is not None:
        ini_linea[k] = (fin_linea[ant] + ini_linea[sig] + 1) // 2; fin_linea[k] = ini_linea[k]
    else:
        sys.exit("No encuentro en la voz la linea: " + lineas[k])
if faltan:
    print("Aviso: lineas que no se oyen claro en la voz (revisar):", [lineas[k][:40] for k in faltan])
tomas = []
for k, l in enumerate(lineas):
    t0 = pal[ini_linea[k]]["t0"] + INICIO
    tomas.append({"n": k + 1, "texto": l, "voz_ini": round(t0, 3), "voz_fin": round(pal[fin_linea[k]]["t1"] + INICIO, 3),
                  "f_ini": 1 if k == 0 else cuadro(t0)})
for k, tm in enumerate(tomas):
    tm["f_fin"] = tomas[k + 1]["f_ini"] - 1 if k + 1 < len(tomas) else cuadro(tm["voz_fin"] + COLA)
    tm["seg"] = round((tm["f_fin"] - tm["f_ini"] + 1) / FPS, 2)
palabras = []
for j, p in enumerate(pal):
    toma = next((t["n"] for t in reversed(tomas) if ini_linea[t["n"] - 1] <= j), 1)
    palabras.append({"w": p["w"], "texto": p["texto"], "t0": round(p["t0"] + INICIO, 3), "t1": round(p["t1"] + INICIO, 3),
                     "f": cuadro(p["t0"] + INICIO), "toma": toma})
salida = {"fps": FPS, "frames": tomas[-1]["f_fin"], "voz_inicio": INICIO, "audio": audio, "tomas": tomas, "palabras": palabras}
json.dump(salida, open(os.path.join(AUD, "tomas_voz.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
huecos = [q["t0"] - p["t1"] for p, q in zip(pal, pal[1:])]
print("Tomas desde la voz (%s): %d tomas, %.2f s, %d fotogramas | pausa mas larga %.2f s" % (audio, len(tomas), salida["frames"] / FPS, salida["frames"], max(huecos) if huecos else 0))
for tm in tomas:
    print("  %2d  f %4d-%4d  %4.2f s  %s" % (tm["n"], tm["f_ini"], tm["f_fin"], tm["seg"], tm["texto"]))
