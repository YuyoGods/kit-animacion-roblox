# Recorta las pausas largas de la voz SIN que se note el corte, para que la animacion vaya continua (sin huecos).
# Solo quita silencio entre palabras (nunca corta una palabra) y une los pedazos con un fundido muy corto.
#   py Herramientas/audio/recortar_pausas.py EP###_Titulo [--audio voz.mp3] [--max 0.22] [--max_suspenso 0.4]
# Entrada:
#   - Voz de ElevenLabs (voz_elevenlabs.py): audio/narracion.mp3 + audio/narracion_tiempos.json (tiempos por letra).
#   - Voz propia (grabada o creada en otra app/cuenta): --audio <archivo>. Los tiempos de cada palabra se sacan
#     con Whisper (faster-whisper, la primera vez descarga el modelo).
# Salida: audio/voz.wav (voz recortada) + audio/voz_palabras.json (cada palabra con su tiempo en la voz recortada).
# Despues: py Herramientas/audio/tomas_desde_voz.py EP###_Titulo  (usa voz_palabras.json si existe).
# La velocidad de la voz NO se cambia (se oye natural); solo se acortan los silencios.
import argparse, json, os, subprocess, sys, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import episodio  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("ep")
ap.add_argument("--audio", help="voz propia (cualquier formato); si no, audio/narracion.mp3 de ElevenLabs")
ap.add_argument("--max", type=float, default=0.22, help="silencio maximo entre palabras (s)")
ap.add_argument("--max_suspenso", type=float, default=0.40, help="silencio maximo despues de '...' (s)")
ap.add_argument("--idioma", default="es")
a = ap.parse_args()
EP = episodio(a.ep)
AUD = os.path.join(EP, "audio")
SR = 48000
src = a.audio or os.path.join(AUD, "narracion.mp3")
if not os.path.exists(src):
    sys.exit("No encuentro la voz: " + src)


def cargar(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


voz = cargar(src)
palabras = []          # [{"texto", "t0", "t1"}] en la voz original; t1 = fin del ultimo sonido de la palabra
tiempos = os.path.join(AUD, "narracion_tiempos.json")
if not a.audio and os.path.exists(tiempos):
    fuente = "elevenlabs"
    al = json.load(open(tiempos, encoding="utf-8"))
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    i = 0
    while i < len(ch):
        if ch[i].isspace():
            i += 1; continue
        j = i
        while j < len(ch) and not ch[j].isspace():
            j += 1
        letras = [k for k in range(i, j) if ch[k].isalnum()]
        if letras:
            palabras.append({"texto": "".join(ch[i:j]), "t0": st[letras[0]], "t1": en[letras[-1]]})
        i = j
else:
    fuente = "whisper"
    try:
        import torch  # noqa: F401  (carga las librerias de CUDA que Whisper necesita para usar la tarjeta)
    except Exception:
        pass
    from faster_whisper import WhisperModel
    raw16 = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                           capture_output=True, check=True).stdout              # Whisper recibe el audio ya decodificado
    audio16 = np.frombuffer(raw16, dtype=np.float32).copy()
    for disp, tipo in (("cuda", "float16"), ("cpu", "int8")):                 # tarjeta de video; si falla, procesador
        try:
            modelo = WhisperModel("large-v3-turbo", device=disp, compute_type=tipo)
            segs, _ = modelo.transcribe(audio16, language=a.idioma, word_timestamps=True, vad_filter=False, beam_size=5)
            palabras = [{"texto": w.word.strip(), "t0": float(w.start), "t1": float(w.end)}
                        for s in segs for w in (s.words or []) if norm(w.word)]
            break
        except Exception as e:
            print("  Whisper en %s no funciono (%s); probando otra forma..." % (disp, str(e)[:70]))
            palabras = []
if not palabras:
    sys.exit("No encontre palabras en la voz")

# ---- tramos que se quedan (de un poco antes de cada palabra a un poco despues), quitando el silencio sobrante
PRE, POST, FUNDIDO = 0.03, 0.06, 0.012
dur = len(voz) / SR
cortes = []            # (inicio_quitar, fin_quitar) en segundos de la voz original
inicio = max(0.0, palabras[0]["t0"] - 0.05)
if inicio > 0.0:
    cortes.append((0.0, inicio))
for p, q in zip(palabras, palabras[1:]):
    hueco = q["t0"] - p["t1"]
    tope = a.max_suspenso if p["texto"].rstrip().endswith(("...", "…")) else a.max
    if hueco > tope:
        quitar = hueco - tope
        a0 = p["t1"] + POST + (hueco - POST - PRE - quitar) / 2.0     # quitar del centro del silencio
        cortes.append((a0, a0 + quitar))
fin = min(dur, palabras[-1]["t1"] + 0.35)
if fin < dur:
    cortes.append((fin, dur))


def nuevo_t(t):
    """tiempo en la voz original -> tiempo en la voz recortada"""
    menos = 0.0
    for c0, c1 in cortes:
        if t >= c1:
            menos += c1 - c0
        elif t > c0:
            menos += t - c0
    return t - menos


# ---- armar la voz recortada con fundidos cortos (inaudibles: el corte cae en silencio)
piezas, pos = [], 0.0
for c0, c1 in cortes + [(dur, dur)]:
    if c0 > pos:
        piezas.append(voz[int(pos * SR):int(c0 * SR)].copy())
    pos = max(pos, c1)
nf = int(FUNDIDO * SR)
salida = piezas[0] if piezas else voz
for pz in piezas[1:]:
    if len(salida) > nf and len(pz) > nf:
        w = np.linspace(0, 1, nf, dtype=np.float32)
        mezcla = salida[-nf:] * np.sqrt(1 - w) + pz[:nf] * np.sqrt(w)
        salida = np.concatenate([salida[:-nf], mezcla, pz[nf:]])
    else:
        salida = np.concatenate([salida, pz])
wav = os.path.join(AUD, "voz.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", wav],
               input=salida.astype(np.float32).tobytes(), check=True)
quitado = sum(c1 - c0 for c0, c1 in cortes)
for p in palabras:
    p["t0"], p["t1"] = round(nuevo_t(p["t0"]), 3), round(nuevo_t(p["t1"]), 3)
    p["w"] = norm(p["texto"])
json.dump({"fuente": fuente, "audio_original": os.path.basename(src), "duracion": round(len(salida) / SR, 3),
           "recortado_s": round(quitado, 3), "palabras": palabras},
          open(os.path.join(AUD, "voz_palabras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
huecos = [q["t0"] - p["t1"] for p, q in zip(palabras, palabras[1:])]
print("Voz recortada (%s): %.2f s -> %.2f s (se quitaron %.2f s de silencio) | %d palabras | pausa mas larga ahora %.2f s"
      % (fuente, dur, len(salida) / SR, quitado, len(palabras), max(huecos) if huecos else 0))
print("  ->", wav)
