# Arma el video final: voz acomodada a cada toma + efectos suaves + subtitulos cortos (1 linea).
# Uso: py armar_video.py EP###_Nombre [preview|final]
# Es una PLANTILLA (ejemplo de EP001): copiarla a EP###/scripts/ y editar LINES, NEW_START, efectos y CHUNKS.
# Lee:  EP###/audio/(narracion.mp3, narracion_tiempos.json, eventos.json)
#       EP###/renders/<modo>/fotogramas/c_0001.png ...
# Deja: EP###/renders/<modo>/EP###_<modo>.mp4  (+ subtitulos.ass y mezcla_final.wav en audio/)
import json, os, subprocess, sys, unicodedata
import numpy as np


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "04_Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            sys.exit("No encuentro 04_Herramientas/config.py")
        d = os.path.dirname(d)
    return d


sys.path.insert(0, os.path.join(_raiz(), "04_Herramientas"))
from config import SFX, episodio  # noqa: E402

_args = [a for a in sys.argv[1:] if a not in ("preview", "final")]
if not _args:
    sys.exit("Uso: py armar_video.py EP###_Nombre [preview|final]")
EP = _args[0]
MODE = "final" if "final" in sys.argv[1:] else "preview"
ROOT = episodio(EP)
AUD = os.path.join(ROOT, "audio")
FRAMES = os.path.join(ROOT, "renders", MODE, "fotogramas")
OUT_MP4 = os.path.join(ROOT, "renders", MODE, "%s_%s.mp4" % (EP, MODE))
if not SFX or not os.path.isdir(SFX):
    sys.exit("Falta la carpeta de efectos: poner la ruta en \"sfx\" de mi_config.json")
SR = 48000
EV = json.load(open(os.path.join(AUD, "eventos.json")))
DUR = EV["frames"] / EV["fps"]
N = int(DUR * SR) + SR


def load(path):
    """decodifica cualquier audio a float32 mono 48 kHz con ffmpeg"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def db(x):
    return 10 ** (x / 20.0)


def place(track, clip, t, gain_db=0.0, fade_in=0.0, fade_out=0.0):
    c = clip * db(gain_db)
    if fade_in:
        n = min(len(c), int(fade_in * SR)); c[:n] *= np.linspace(0, 1, n)
    if fade_out:
        n = min(len(c), int(fade_out * SR)); c[-n:] *= np.linspace(1, 0, n)
    i = int(t * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(c))
    track[i:j] += c[:j - i]


# ================= VOZ: cada frase en su toma =================
al = json.load(open(os.path.join(AUD, "narracion_tiempos.json"), encoding="utf-8"))
chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
text = "".join(chars)
LINES = ["Esta es Crista, y hoy era el día más importante de su vida.", "El alcalde la había elegido para algo muy especial.",
         "Pero justo antes de llegar...", "se le desató la agujeta... ¡y ya iba tarde!", "Faltaban dos minutos.",
         "Crista corrió como nunca por todo el pueblo.", "Pasó la fuente, la plaza...", "y por fin llegó.",
         "Subió las escaleras con el corazón a mil.", "Tocó la puerta tres veces...", "pero lo que había detrás... nadie se lo esperaba."]
NEW_START = [0.20, 3.95, 7.10, 8.97, 12.11, 14.30, 17.45, 19.80, 22.30, 25.05, 26.95]
voz_src = load(os.path.join(AUD, "narracion.mp3"))
voz = np.zeros(N, np.float32)
spans, pos = [], 0
for l in LINES:
    a = text.find(l[:12], pos); b = a + len(l) - 1; pos = b
    spans.append((a, b))
offsets = []
for k, (a, b) in enumerate(spans):
    t0, t1 = st[a], en[b]
    nxt = st[spans[k + 1][0]] if k + 1 < len(spans) else t1 + 0.4
    s0, s1 = max(0.0, t0 - 0.04), min(nxt - 0.02, t1 + 0.18)
    seg = voz_src[int(s0 * SR):int(s1 * SR)].copy()
    place(voz, seg, NEW_START[k] - (t0 - s0), 0.0, fade_in=0.01, fade_out=0.04)
    offsets.append(NEW_START[k] - t0)

# ================= EFECTOS (pocos, con sentido) =================
fx = np.zeros(N, np.float32)
amb = load(os.path.join(SFX, "wind", "sfx.wind.02.ogg"))
amb = np.tile(amb, int(np.ceil(N / len(amb))))[:N]
fx += amb * db(-27)                                              # ambiente: viento suave de pueblo
steps = [load(os.path.join(SFX, "footstep", "sfx.footstep.0%d.ogg" % i)) for i in (7, 8, 9)]
for i, p in enumerate(EV["pasos"]):                              # pasos sincronizados con cada pisada
    place(fx, steps[i % 3], p["t"], -17 if p["tipo"] == "correr" else -21)
place(fx, load(os.path.join(SFX, "swish", "sfx.swish.02.ogg")), EV["agacharse"] + 0.1, -16)          # ropa al agacharse
place(fx, load(os.path.join(SFX, "reverse_swell", "sfx.reverse_swell.02.ogg")), EV["corte_poste"] - 0.84, -11)
place(fx, load(os.path.join(SFX, "swish", "sfx.swish.06.ogg")), EV["corte_poste"] - 0.05, -6)          # whoosh del poste
gav = [load(os.path.join(SFX, "gavel", "sfx.gavel.0%d.ogg" % i)) for i in (1, 2, 3)]
for i, t in enumerate(EV["golpes"]):                             # tres toques en la puerta
    place(fx, gav[i], t, -7)
drone = load(os.path.join(SFX, "tension_drone", "sfx.tension_drone.02.ogg"))
place(fx, drone[:int(4.2 * SR)], 26.6, -22, fade_in=1.5, fade_out=0.6)   # tension del final
place(fx, load(os.path.join(SFX, "sub_drop", "sfx.sub_drop.01.ogg")), 29.35, -14, fade_out=0.8)

# ================= MEZCLA =================
mix = voz * db(-1.0) + fx
# bajar efectos cuando habla la voz (ducking suave)
env = np.convolve(np.abs(voz), np.ones(2400) / 2400, mode="same")
duck = np.clip(1.0 - env * 6.0, 0.55, 1.0)
mix = voz * db(-1.0) + fx * duck
mix = mix[:int(DUR * SR)]
peak = np.max(np.abs(mix)) or 1
mix = mix / peak * 0.89
tmp = os.path.join(AUD, "mezcla_tmp.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", tmp], input=mix.astype(np.float32).tobytes(), check=True)
final_wav = os.path.join(AUD, "mezcla_final.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "2", final_wav], check=True)
os.remove(tmp)

# ================= SUBTITULOS (1 a 3 palabras, 1 linea) =================
CHUNKS = ["Esta es Crista", "y hoy era", "el día más", "importante", "de su vida",
          "El alcalde", "la había elegido", "para algo", "muy especial",
          "Pero justo", "antes de llegar",
          "se le desató", "la agujeta", "¡y ya", "iba tarde!",
          "Faltaban", "dos minutos",
          "Crista corrió", "como nunca", "por todo", "el pueblo",
          "Pasó la fuente", "la plaza",
          "y por fin", "llegó",
          "Subió", "las escaleras", "con el corazón", "a mil",
          "Tocó la puerta", "tres veces",
          "pero lo que", "había detrás", "nadie se lo", "esperaba"]
HILITE = {"crista", "importante", "alcalde", "agujeta", "tarde", "minutos", "corrió", "llegó", "escaleras", "puerta", "esperaba", "especial"}


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


# palabras con su tiempo (ya movido a su toma)
words = []
i = 0
line_of = []
for k, (a, b) in enumerate(spans):
    for idx in range(a, b + 1):
        line_of.append((idx, k))
lk = dict(line_of)
while i < len(text):
    if text[i].isspace():
        i += 1; continue
    j = i
    while j < len(text) and not text[j].isspace():
        j += 1
    w = text[i:j]
    if norm(w) and i in lk:
        off = offsets[lk[i]]
        words.append((norm(w), st[i] + off, en[j - 1] + off))
    i = j
events = []
wi = 0
for c in CHUNKS:
    ws = [norm(x) for x in c.split() if norm(x)]
    t0 = words[wi][1]; t1 = words[wi + len(ws) - 1][2]
    assert [w[0] for w in words[wi:wi + len(ws)]] == ws, (c, words[wi:wi + len(ws)])
    events.append([t0 - 0.03, t1, c])
    wi += len(ws)
for k in range(len(events)):
    nxt = events[k + 1][0] if k + 1 < len(events) else DUR
    events[k][1] = min(nxt, max(events[k][1] + 0.3, events[k][1]))
    if nxt - events[k][1] < 0.35:
        events[k][1] = nxt


def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def styled(c):
    out = []
    for w in c.split():
        clean = w.strip("¡!.,")
        if norm(clean) in HILITE:
            out.append("{\\c&H2AD8FF&}" + w + "{\\c&HFFFFFF&}")
        else:
            out.append(w)
    return " ".join(out)


ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       "Style: Sub,Arial Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,3,2,50,50,400,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for t0, t1, c in events:
    ass.append("Dialogue: 0,%s,%s,Sub,,0,0,0,,{\\fscx118\\fscy118\\t(0,90,\\fscx100\\fscy100)}%s" % (ts(t0), ts(t1), styled(c)))
open(os.path.join(AUD, "subtitulos.ass"), "w", encoding="utf-8").write("\n".join(ass) + "\n")
json.dump({"voz_inicio_frases": NEW_START, "subtitulos": events}, open(os.path.join(AUD, "tiempos_finales.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ================= VIDEO =================
os.chdir(AUD)          # ruta corta para el filtro de subtitulos
cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(EV["fps"]), "-i", os.path.join(FRAMES, "c_%04d.png"),
       "-i", final_wav, "-vf", "scale=1080:1920:flags=lanczos,subtitles=subtitulos.ass",
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(EV["fps"]),
       "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", OUT_MP4]
subprocess.run(cmd, check=True)
print("listo ->", OUT_MP4, "| duracion", round(DUR, 2), "s | subtitulos:", len(events), "| pasos:", len(EV["pasos"]))
