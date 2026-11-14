# Arma el video: la voz completa de corrido (las tomas ya siguen a la voz, ver tomas_desde_voz.py) + pocos efectos
# debajo de la voz, cada uno justo cuando pasa algo en la escena + subtitulos automaticos (subtitulos_estilo.py)
# + la musica de fondo del canal de principio a fin (mi_config.json -> musica_fondo; Herramientas/audio/musica_fondo.py) -> MP4.
# PLANTILLA: copiar a EP###/scripts/armar_video.py y editar AMBIENTES, EFECTOS y CLAVE para el episodio.
# Uso: py Episodios/EP###_Titulo/scripts/armar_video.py EP###_Titulo [preview|final] [--solo-audio]
# Lee:  audio/tomas_voz.json + la voz (audio/voz.wav si se recorto con recortar_pausas.py, si no audio/narracion.mp3)
#       renders/<modo>/fotogramas/c_0001.png ...
# Deja: renders/<modo>/EP###_Titulo_<modo>.mp4  (+ subtitulos.ass, mezcla_final.wav, tiempos_finales.json en audio/)
# (La version vieja de esta plantilla, con la voz acomodada frase por frase, quedo en EP001/scripts/armar_video.py.)
import re, json, os, subprocess, sys, unicodedata
import numpy as np


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            sys.exit("No encuentro Herramientas/config.py")
        d = os.path.dirname(d)
    return d


sys.path.insert(0, os.path.join(_raiz(), "Herramientas"))
sys.path.insert(0, os.path.join(_raiz(), "Herramientas", "audio"))
from config import SFX, episodio  # noqa: E402
import musica_fondo  # noqa: E402

# ======================= EDITAR POR EPISODIO =======================
# Sonido de fondo en bucle, muy bajito (toma_desde, toma_hasta, categoria, numero, volumen_dB)
AMBIENTES = [
    # (1, 4, "wind", 2, -30),            # exterior de dia
    # (5, 5, "night_ambience", 3, -21),  # noche
]
# Golpes: (cuando, categoria, numero, volumen_dB[, corte]). cuando = segundos, "palabra:pum" (cae con esa palabra de la
# voz; "palabra:pum:2" = la segunda vez que la dice) o "toma:3" (al empezar la toma 3). Pocos y con sentido.
# REGLA (pedido del usuario 2026-11-11, "muy importante"): cada efecto suena SOLO mientras pasa su accion en pantalla.
# Muchos clips de la libreria duran 5-6 s (typing, tick, reverse_swell, sub_drop): se cortan solos (con fade corto) al
# terminar la toma donde empiezan, y el 5o dato los acorta mas: segundos (0.6) o "hasta:palabra:una".
# Los sonidos que salen de la animacion (ej. el tecleo de una burbuja) van en audio/efectos_animacion.json:
# [{"tipo": "tecleo", "f0": cuadro_primera_letra, "f1": cuadro_ultima_letra + 3}] -> suenan solo en ese tramo.
TECLEO = ("typing", -16)
EFECTOS = [
    # ("palabra:pum", "pop", 5, -3),
    # ("toma:6", "whoosh", 2, -16),
]
CLAVE = set()        # palabras que van en amarillo en los subtitulos, ej. {"monstruo", "pum"}
CALLAR = set()       # palabras que la voz dice pero que mejor hace el EFECTO (onomatopeyas que ElevenLabs lee
                     # en ingles, ej. {"dong"}): se silencian en la voz y no salen en subtitulos
SIN_SUBS = {"suscribete"}   # se dicen pero NO van en subtitulos (el boton SUSCRIBETE ya lo dice; salian encimados, EP016 y EP018)
ESTILO_SUBS = "custerk"   # "custerk" (1 palabra en MAYUSCULAS con pop, como Custerk), "custerk_viejo" o "clasico"
# ===================================================================

SOLO_AUDIO = "--solo-audio" in sys.argv[1:]      # solo la mezcla (voz + efectos + musica) para escucharla, sin video
_args = [a for a in sys.argv[1:] if a not in ("preview", "final", "--solo-audio")]
if not _args:
    sys.exit("Uso: py armar_video.py EP###_Titulo [preview|final]")
EP = _args[0]
MODE = "final" if "final" in sys.argv[1:] else "preview"
ROOT = episodio(EP)
AUD = os.path.join(ROOT, "audio")
FRAMES = os.path.join(ROOT, "renders", MODE, "fotogramas")
OUT_MP4 = os.path.join(ROOT, "renders", MODE, "%s_%s.mp4" % (EP, MODE))
if not SOLO_AUDIO and not os.path.exists(os.path.join(FRAMES, "c_0001.png")):
    import limpiar_episodio      # episodio ya limpio: los PNG quedaron en fotogramas/fotogramas.mp4 -> sacarlos
    limpiar_episodio.restaurar(FRAMES)
if not SFX or not os.path.isdir(SFX):
    sys.exit("Falta la carpeta de efectos: poner la ruta en \"sfx\" de mi_config.json")
SR = 48000
VOZ = json.load(open(os.path.join(AUD, "tomas_voz.json"), encoding="utf-8"))
FPS = VOZ["fps"]
DUR = VOZ["frames"] / FPS
N = int(DUR * SR) + SR
TOMA = {t["n"]: ((t["f_ini"] - 1) / FPS, t["f_fin"] / FPS) for t in VOZ["tomas"]}


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


def cuando(c):
    if isinstance(c, (int, float)):
        return float(c)
    tipo, valor, *resto = c.split(":")
    if tipo == "toma":
        return TOMA[int(valor)][0]
    hits = [p for p in VOZ["palabras"] if p["w"] == norm(valor)]
    if not hits:
        sys.exit("La voz no dice la palabra: " + valor)
    return hits[int(resto[0]) - 1 if resto else 0]["t0"]


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def sfx(cat, n):
    return load(os.path.join(SFX, cat, "sfx.%s.%02d.ogg" % (cat, n)))


def db(x):
    return 10 ** (x / 20.0)


def place(track, clip, t, gain_db=0.0, fade_in=0.0, fade_out=0.0):
    c = clip * db(gain_db)
    if fade_in:                                            # curvas suaves (seno): sin clic ni golpe al entrar/salir
        n = min(len(c), int(fade_in * SR)); c[:n] *= np.sin(np.linspace(0, np.pi / 2, n))
    if fade_out:
        n = min(len(c), int(fade_out * SR)); c[-n:] *= np.cos(np.linspace(0, np.pi / 2, n))
    i = int(t * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(c))
    track[i:j] += c[:j - i]


# ================= VOZ: completa y de corrido =================
voz = np.zeros(N, np.float32)
archivo_voz = os.path.join(AUD, VOZ.get("audio", "narracion.mp3"))
place(voz, load(archivo_voz), VOZ["voz_inicio"], 0.0, fade_in=0.005, fade_out=0.05)
for p in VOZ["palabras"]:                                  # CALLAR: quitar esa palabra de la voz (el efecto la "dice")
    if p["w"] in CALLAR:
        i0, i1 = int((p["t0"] - 0.02) * SR), int((p["t1"] + 0.06) * SR)
        r = min(240, (i1 - i0) // 4)
        voz[i0:i0 + r] *= np.linspace(1, 0, r); voz[i0 + r:i1 - r] = 0; voz[i1 - r:i1] *= np.linspace(0, 1, r)

# ================= EFECTOS =================
fx = np.zeros(N, np.float32)
for t0, t1, cat, n, g in AMBIENTES:
    a, b = TOMA[t0][0], TOMA[t1][1]
    c = sfx(cat, n); m = int((b - a) * SR)
    place(fx, np.tile(c, int(np.ceil(m / len(c))) + 1)[:m].copy(), a, g, fade_in=0.4, fade_out=0.5)
def fin_de_toma(t):
    for n_, (a_, b_) in TOMA.items():
        if a_ - 1e-6 <= t < b_:
            return b_
    return DUR


for e in EFECTOS:
    c, cat, n, g = e[:4]
    t = cuando(c)
    fin = fin_de_toma(t)                                   # nunca pasa del corte de su toma
    if len(e) > 4:
        fin = min(fin, cuando(e[4][6:]) if isinstance(e[4], str) and e[4].startswith("hasta:") else t + float(e[4]))
    entero = sfx(cat, n)
    clip = entero[:max(1, int((fin - t) * SR))].copy()
    largo = len(clip) / SR
    # DESVANECIDO al final (pedido del usuario 2026-11-11): si el efecto se recorto (por el corte de la toma o su 5o dato)
    # se apaga suave en su ultimo tramo (0,15-0,6 s) y termina ANTES del corte: no se oye "cortado" al cambiar de escena.
    recortado = len(clip) < len(entero)
    fo = min(0.6, max(0.15, largo * 0.4)) if recortado else min(0.25, max(0.04, largo * 0.15))
    place(fx, clip, t, g, fade_in=0.01, fade_out=min(fo, largo * 0.7))
    print("  efecto %-14s %6.2f -> %6.2f s" % (cat, t, t + len(clip) / SR))
_ev = os.path.join(AUD, "efectos_animacion.json")
for k, e in enumerate(json.load(open(_ev, encoding="utf-8")) if os.path.exists(_ev) else []):
    if e["tipo"] == "tecleo":                              # tecleo: solo mientras salen las letras de esa burbuja
        t0, t1 = (e["f0"] - 1) / FPS, (e["f1"] - 1) / FPS
        clip = sfx(TECLEO[0], 1 + k % 2)[:max(1, int((t1 - t0) * SR))].copy()
        place(fx, clip, t0, TECLEO[1], fade_in=0.01, fade_out=0.05)
        print("  efecto %-14s %6.2f -> %6.2f s (tecleo de %s)" % (TECLEO[0], t0, t1, e.get("burbuja", "")))

# ================= MEZCLA =================
env = np.convolve(np.abs(voz), np.ones(2400) / 2400, mode="same")
duck = np.clip(1.0 - env * 6.0, 0.55, 1.0)                 # bajar efectos cuando habla la voz
mus = musica_fondo.pista(voz, DUR, SR, load)              # musica de fondo de principio a fin (mi_config.json), bajo la voz
mix = (voz * db(-1.0) + fx * duck + (mus if mus is not None else 0))[:int(DUR * SR)]
mix = mix / (np.max(np.abs(mix)) or 1) * 0.89
tmp = os.path.join(AUD, "mezcla_tmp.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", tmp], input=mix.astype(np.float32).tobytes(), check=True)
final_wav = os.path.join(AUD, "mezcla_final.wav")
# loudnorm en 2 pasadas y YA EN ESTEREO (medir y luego aplicar lineal). En una pasada, o midiendo en mono (3 dB mas
# bajo: pedia tanta ganancia que se pasaba del pico y loudnorm se rendia), quedaba en -15,3 LUFS (EP006) y no en -14.
_med = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                      capture_output=True, text=True).stderr
_m = json.loads(_med[_med.rindex("{"):_med.rindex("}") + 1])
_ln = ("aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
       % (_m["input_i"], _m["input_tp"], _m["input_lra"], _m["input_thresh"], _m["target_offset"]))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", _ln, "-ar", str(SR), "-ac", "2", final_wav], check=True)
os.remove(tmp)
if SOLO_AUDIO:
    escuchar = os.path.join(AUD, "mezcla_escuchar.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", final_wav, "-c:a", "libmp3lame", "-b:a", "192k", escuchar], check=True)
    print("MEZCLA LISTA (sin video):", escuchar)
    sys.exit(0)

# ================= SUBTITULOS (Herramientas/audio/subtitulos_estilo.py) =================
# "custerk" (desde 2026-11-12, copia de sus subtitulos del 10-12 nov): UNA palabra EN MAYUSCULAS, Montserrat Black,
# relleno con degradado suave, contorno negro y sombra 3D, entrada pop con rebote (48 -> 120 -> 100 %), a 69 % de la
# altura; CLAVE y numeros en dorado. "custerk_viejo" (hasta el 9-nov) y "clasico" (el nuestro de antes) siguen disponibles.
import subtitulos_estilo  # noqa: E402
texto_ass, events = subtitulos_estilo.armar(VOZ["palabras"], DUR, clave=CLAVE, callar=CALLAR | SIN_SUBS, estilo=ESTILO_SUBS)
open(os.path.join(AUD, "subtitulos.ass"), "w", encoding="utf-8").write(texto_ass)
json.dump({"subtitulos": events}, open(os.path.join(AUD, "tiempos_finales.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ================= VIDEO =================
os.chdir(AUD)          # ruta corta para el filtro de subtitulos
cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "c_%04d.png"),
       "-i", final_wav, "-vf", "scale=1080:1920:flags=lanczos," + subtitulos_estilo.filtro("subtitulos.ass", AUD, ESTILO_SUBS),
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", OUT_MP4]
subprocess.run(cmd, check=True)
print("listo ->", OUT_MP4, "| duracion %.2f s | %d subtitulos" % (DUR, len(events)))
