# ACORTAR UNA PALABRA ESTIRADA en la voz ya recortada, SIN gastar creditos (2026-11-11, EP012: "detras" de 0,72 s).
# Comprime solo el tramo estirado (casi siempre la vocal: "tráaaas") con atempo de ffmpeg (no cambia el tono), une las
# orillas con un cruce de 8 ms (sin clic), recorre los tiempos de las palabras que van despues y regenera
# voz_escuchar.mp3. Respalda antes en Respaldos/<EP>/voz_antes_de_acortar_<t0>/.
#   py -X utf8 Herramientas/audio/acortar_palabra.py EP###_Nombre <t0> <t1> [factor=2.5]
#   (t0-t1 en segundos de audio/voz.wav: el tramo estirado; verlo con la envolvente o el aviso de recortar_pausas.py)
# Despues: py Herramientas/audio/tomas_desde_voz.py EP###_Nombre
import json, os, shutil, subprocess, sys, tempfile, wave
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import RESPALDOS, episodio  # noqa: E402

if len(sys.argv) < 4:
    sys.exit(__doc__ or "uso: acortar_palabra.py EP t0 t1 [factor]")
EP = episodio(sys.argv[1])
T0, T1 = float(sys.argv[2]), float(sys.argv[3])
F = float(sys.argv[4]) if len(sys.argv) > 4 else 2.5
AUD = os.path.join(EP, "audio")
resp = os.path.join(RESPALDOS, os.path.basename(EP).split("_")[0], "voz_antes_de_acortar_%.2f" % T0)
os.makedirs(resp, exist_ok=True)
for n in ("voz.wav", "voz_palabras.json", "voz_escuchar.mp3", "tomas_voz.json"):
    if os.path.exists(os.path.join(AUD, n)):
        shutil.copy2(os.path.join(AUD, n), resp)
wf = wave.open(os.path.join(AUD, "voz.wav")); sr = wf.getframerate()
assert wf.getsampwidth() == 2 and wf.getnchannels() == 1, "se espera voz.wav mono de 16 bits (la de recortar_pausas)"
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32); wf.close()
i0, i1 = int(T0 * sr), int(T1 * sr)
tmp = tempfile.mkdtemp()
seg_in, seg_out = os.path.join(tmp, "in.wav"), os.path.join(tmp, "out.wav")
w = wave.open(seg_in, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(a[i0:i1].astype(np.int16).tobytes()); w.close()
filtros, f = [], F
while f > 2.0:                                         # atempo acepta hasta 2.0 por filtro
    filtros.append("atempo=2.0"); f /= 2.0
filtros.append("atempo=%.4f" % f)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", seg_in, "-filter:a", ",".join(filtros), "-ar", str(sr), "-ac", "1", seg_out], check=True)
wo = wave.open(seg_out); b = np.frombuffer(wo.readframes(wo.getnframes()), dtype=np.int16).astype(np.float32); wo.close()
xf = int(0.008 * sr)
A, C = a[:i0 + xf], a[i1 - xf:]
r = np.linspace(0, 1, xf)
B = b.copy()
B[:xf] = B[:xf] * r + A[-xf:] * (1 - r)
B[-xf:] = B[-xf:] * (1 - r) + C[:xf] * r
nuevo = np.concatenate([A[:-xf], B, C[xf:]])
delta = (len(a) - len(nuevo)) / sr
w = wave.open(os.path.join(AUD, "voz.wav"), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
w.writeframes(np.clip(nuevo, -32768, 32767).astype(np.int16).tobytes()); w.close()
vp_ruta = os.path.join(AUD, "voz_palabras.json")
if os.path.exists(vp_ruta):
    vp = json.load(open(vp_ruta, encoding="utf-8"))
    for p in vp["palabras"]:
        if p["t0"] >= T1 - 0.001:
            p["t0"] = round(p["t0"] - delta, 3); p["t1"] = round(p["t1"] - delta, 3)
        elif p["t1"] > T0:
            p["t1"] = round(max(p["t0"] + 0.1, p["t1"] - delta), 3)
    vp["duracion"] = round(len(nuevo) / sr, 3)
    vp.setdefault("acortados", []).append({"t0": T0, "t1": T1, "factor": F, "segundos_menos": round(delta, 3)})
    json.dump(vp, open(vp_ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(AUD, "voz.wav"), "-b:a", "192k", os.path.join(AUD, "voz_escuchar.mp3")], check=True)
print("listo: %.2f s -> %.2f s (%.3f s menos). Respaldo: %s" % (len(a) / sr, len(nuevo) / sr, delta, resp))
print("Ahora: py Herramientas/audio/tomas_desde_voz.py", os.path.basename(EP))
