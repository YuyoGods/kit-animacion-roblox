# Quita de la VOZ ya aprobada las onomatopeyas que dice el narrador (¡clic!, ¡ting!, ¡kikiriki!...) SIN gastar
# creditos: corta ese pedazo del audio y deja un hueco cortito donde suena el EFECTO de verdad (lo pone armar_video).
# Cada palabra quitada queda como MARCA en audio/voz_palabras.json ("sfx": true): tomas_desde_voz.py la pasa a
# tomas_voz.json, asi palabra(n, "clic") y "palabra:clic" en armar_video siguen cayendo en su momento, sin subtitulo.
#   py Herramientas/audio/quitar_onomatopeyas.py EP###_Titulo [--palabras clic,ting,...] [--probar]
#   despues:  py Herramientas/audio/tomas_desde_voz.py EP###_Titulo
# Lee audio/voz.wav + audio/voz_palabras.json (de recortar_pausas.py). Respalda voz.wav, voz_palabras.json y
# narracion.txt en Respaldos/<EP>/antes_onomatopeyas/ y quita las onomatopeyas de narracion.txt.
# (Si se vuelve a correr recortar_pausas.py, regresan: correr este script otra vez.)
import argparse, json, os, re, shutil, subprocess, sys, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import episodio  # noqa: E402

# hueco que queda (s) donde iba la onomatopeya: lo que dura su efecto de sonido (corto: la voz manda el ritmo)
HUECO = {"clic": 0.30, "click": 0.30, "ting": 0.28, "clinc": 0.28, "clink": 0.28, "pum": 0.30, "pop": 0.28, "plic": 0.30,
         "clac": 0.40, "kikiriki": 0.30, "miau": 0.45, "guau": 0.40, "boing": 0.40, "zas": 0.28, "crac": 0.30, "bum": 0.35,
         "toc": 0.25, "ring": 0.40, "splash": 0.35, "chas": 0.28, "fiu": 0.30, "brrr": 0.40, "achu": 0.40, "muac": 0.30}
EXTRA = 0.15          # por cada onomatopeya mas seguida (¡Ting! ¡Ting! ¡Ting!)
COLA = 0.06           # cola que se deja despues de la palabra anterior (para que no se corte su final)
XF = 0.012            # fundido en cada corte (s)

ap = argparse.ArgumentParser()
ap.add_argument("ep")
ap.add_argument("--palabras", help="onomatopeyas a quitar separadas por coma (por defecto: la lista HUECO)")
ap.add_argument("--probar", action="store_true", help="solo mostrar que quitaria")
a = ap.parse_args()
EP = episodio(a.ep)
AUD = os.path.join(EP, "audio")
ONO = set(a.palabras.split(",")) if a.palabras else set(HUECO)


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


vp_path = os.path.join(AUD, "voz_palabras.json")
vp = json.load(open(vp_path, encoding="utf-8"))
pal = vp["palabras"]
for p in pal:
    p.setdefault("w", norm(p["texto"]))
# ---- tramos de onomatopeyas seguidas (que no esten ya quitadas)
tramos, i = [], 0
while i < len(pal):
    if pal[i]["w"] in ONO and not pal[i].get("sfx"):
        j = i
        while j + 1 < len(pal) and pal[j + 1]["w"] in ONO and not pal[j + 1].get("sfx"):
            j += 1
        tramos.append((i, j)); i = j + 1
    else:
        i += 1
if not tramos:
    sys.exit("No hay onomatopeyas que quitar (%s)" % ", ".join(sorted(ONO)))

sr = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate",
                         "-of", "csv=p=0", os.path.join(AUD, "voz.wav")], capture_output=True, text=True).stdout.strip())
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(AUD, "voz.wav"), "-f", "f32le", "-ac", "1", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32).copy()
dur = len(x) / sr
cortes = []                                           # (t0, t1, marcas[(w, texto, t_relativo_al_corte)])
for i, j in tramos:
    prev = pal[i - 1] if i > 0 else None
    sig = pal[j + 1] if j + 1 < len(pal) else None
    n = j - i + 1
    hueco = max(HUECO.get(pal[k]["w"], 0.3) for k in range(i, j + 1)) + EXTRA * (n - 1)
    c0 = (prev["t1"] + COLA) if prev else max(0.0, pal[i]["t0"] - 0.02)
    c0 = min(c0, pal[i]["t0"] - 0.01)
    fin_ono = pal[j]["t1"] + 0.05
    if sig:
        c1 = max(sig["t0"] - (hueco - (c0 - (prev["t1"] if prev else c0))), fin_ono)
        c1 = min(c1, sig["t0"] - 0.03)
    else:
        c1 = min(dur, fin_ono + 0.1)
    queda = (c0 - (prev["t1"] if prev else c0)) + ((sig["t0"] - c1) if sig else 0)
    pad = max(0.0, hueco - queda) if sig else 0.0          # silencio que se agrega (lo cubre el efecto)
    marcas = [(pal[k]["w"], pal[k]["texto"], 0.02 + (hueco - 0.08) * (k - i) / max(1, n)) for k in range(i, j + 1)]
    cortes.append((c0, c1, marcas, pad))
    print("quita %-28s  %.2f-%.2f s (%.2f s)  hueco que queda %.2f s  | antes: %s  despues: %s"
          % (" ".join(pal[k]["texto"] for k in range(i, j + 1)), c0, c1, c1 - c0, queda + pad,
             prev["texto"] if prev else "-", sig["texto"] if sig else "-"))
total = sum(c1 - c0 - pad for c0, c1, _, pad in cortes)
print("en total: %d onomatopeyas, la voz queda %.2f s mas corta (%.2f -> %.2f s)" % (sum(len(c[2]) for c in cortes), total, dur, dur - total))
if a.probar:
    sys.exit(0)

# ---- respaldo (carpeta personal Respaldos/)
raiz = os.path.abspath(os.path.join(EP, "..", ".."))
resp = os.path.join(raiz, "Respaldos", os.path.basename(EP).split("_")[0], "antes_onomatopeyas")
os.makedirs(resp, exist_ok=True)
for f in (os.path.join(AUD, "voz.wav"), vp_path, os.path.join(EP, "narracion.txt")):
    dst = os.path.join(resp, os.path.basename(f))
    if not os.path.exists(dst):
        shutil.copy2(f, dst)
print("respaldo ->", resp)

# ---- cortar el audio con fundidos cortos
partes, t_prev, nx = [], 0.0, int(XF * sr)
for c0, c1, _, pad in cortes:
    partes.append(x[int(t_prev * sr):int(c0 * sr)].copy())
    if pad > 0:
        partes.append(np.zeros(int(pad * sr) + nx, np.float32))
    t_prev = c1
partes.append(x[int(t_prev * sr):].copy())
y = partes[0]
for p in partes[1:]:
    if len(y) > nx and len(p) > nx:
        f = np.linspace(0, 1, nx, dtype=np.float32)
        y = np.concatenate([y[:-nx], y[-nx:] * (1 - f) + p[:nx] * f, p[nx:]])
    else:
        y = np.concatenate([y, p])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", os.path.join(AUD, "voz.wav")],
               input=y.astype(np.float32).tobytes(), check=True)


def nuevo_t(t):
    """tiempo en la voz nueva: se resta lo cortado antes (y el traslape de cada fundido)."""
    d, n = 0.0, 0
    for c0, c1, _, pad in cortes:
        if t >= c1:
            d += c1 - c0 - pad; n += 2 if pad > 0 else 1
        elif t > c0:
            t = c0
            break
    return t - d - XF * n


quitar = {k for i, j in tramos for k in range(i, j + 1)}
nuevas = []
for k, p in enumerate(pal):
    if k in quitar:
        continue
    q = dict(p); q["t0"] = round(nuevo_t(p["t0"]), 3); q["t1"] = round(nuevo_t(p["t1"]), 3)
    nuevas.append(q)
for c0, c1, marcas, _ in cortes:
    base = nuevo_t(c0)
    for w, texto, dt in marcas:
        nuevas.append({"texto": texto, "w": w, "t0": round(base + dt, 3), "t1": round(base + dt + 0.05, 3), "sfx": True})
nuevas.sort(key=lambda p: p["t0"])
vp["palabras"] = nuevas
vp["duracion"] = round(len(y) / sr, 3)
vp["onomatopeyas_quitadas"] = vp.get("onomatopeyas_quitadas", []) + [m[1] for c in cortes for m in c[2]]
json.dump(vp, open(vp_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- el guion: quitar esas palabras de narracion.txt (las lineas con # se quedan igual)
nar = os.path.join(EP, "narracion.txt")
out = []
for l in open(nar, encoding="utf-8").read().split("\n"):
    if l.strip() and not l.lstrip().startswith("#"):
        toks = [t for t in l.split(" ") if not (norm(t) in ONO)]
        l = re.sub(r"\s+", " ", " ".join(toks)).strip()
    out.append(l)
open(nar, "w", encoding="utf-8").write("\n".join(out))
print("listo: voz.wav %.2f s, voz_palabras.json con %d marcas de efecto, narracion.txt sin onomatopeyas"
      % (len(y) / sr, sum(len(c[2]) for c in cortes)))
print("ahora: py Herramientas/audio/tomas_desde_voz.py", os.path.basename(EP))
