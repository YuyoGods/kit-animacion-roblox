# Analiza un video de referencia toma por toma y fotograma por fotograma.
#   py -X utf8 analizar_referencia.py "RUTA\video.mp4" --creador NombreCreador [--nombre ref_01] [--sin-voz]
# Resultado en 00_Referencias/<Creador>/<nombre>/:
#   video.mp4 (copia con nombre simple), datos.json, ficha.md, grafica.png, hojas/hoja_XX.jpg
# y actualiza 00_Referencias/<Creador>/ficha_estilo.md (resumen de todos sus videos).
import argparse, json, os, shutil, subprocess, sys, glob
import numpy as np
import cv2

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REFS = os.path.join(RAIZ, "00_Referencias")

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--creador", required=True)
ap.add_argument("--nombre", default=None)
ap.add_argument("--sin-voz", action="store_true", help="no transcribir la narracion")
ap.add_argument("--umbral", type=float, default=27.0, help="sensibilidad de cortes (menor = detecta mas cortes)")
args = ap.parse_args()

carpeta_creador = os.path.join(REFS, args.creador)
n_prev = len([d for d in glob.glob(os.path.join(carpeta_creador, "ref_*")) if os.path.isdir(d)])
nombre = args.nombre or "ref_%02d" % (n_prev + 1)
OUT = os.path.join(carpeta_creador, nombre)
os.makedirs(os.path.join(OUT, "hojas"), exist_ok=True)
VID = os.path.join(OUT, "video.mp4")
if os.path.abspath(args.video) != os.path.abspath(VID):
    shutil.copy(args.video, VID)            # nombre simple: OpenCV no abre rutas con emojis
origen = os.path.basename(args.video)
print("analizando:", origen, "->", OUT)

# ---------------- datos basicos ----------------
cap = cv2.VideoCapture(VID)
FPS = cap.get(cv2.CAP_PROP_FPS) or 30.0
NF = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
DUR = NF / FPS
print("  %dx%d, %.2f fps, %.1f s, %d fotogramas" % (W, H, FPS, DUR, NF))

# ---------------- cortes de camara ----------------
from scenedetect import detect, ContentDetector
escenas = detect(VID, ContentDetector(threshold=args.umbral, min_scene_len=int(FPS * 0.3)))
cortes = [0] + [s[0].get_frames() for s in escenas[1:]] if escenas else [0]
cortes = sorted(set(cortes)) + [NF]
print("  tomas detectadas:", len(cortes) - 1)

# ---------------- movimiento de camara por fotograma ----------------
SW = 360
SH = int(SW * H / W)
orb = cv2.ORB_create(1000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
escala = np.ones(NF); dx = np.zeros(NF); dy = np.zeros(NF); rot = np.zeros(NF); ok_m = np.zeros(NF, bool)
brillo = np.zeros(NF)
cortes_set = set(cortes)
cap = cv2.VideoCapture(VID)
prev_k = prev_d = None
for i in range(NF):
    okf, fr = cap.read()
    if not okf:
        break
    g = cv2.cvtColor(cv2.resize(fr, (SW, SH)), cv2.COLOR_BGR2GRAY)
    brillo[i] = g.mean()
    k, d = orb.detectAndCompute(g, None)
    if i in cortes_set or prev_d is None or d is None or len(k) < 25 or len(prev_k) < 25:
        prev_k, prev_d = k, d
        continue
    m = bf.match(prev_d, d)
    if len(m) >= 20:
        p1 = np.float32([prev_k[x.queryIdx].pt for x in m]); p2 = np.float32([k[x.trainIdx].pt for x in m])
        A, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if A is not None and inl is not None and inl.sum() >= 15:
            s = float(np.hypot(A[0, 0], A[1, 0]))
            # traslacion medida respecto al centro (no al origen) para separar zoom de paneo
            c = np.array([SW / 2, SH / 2])
            t = A[:, :2] @ c + A[:, 2] - c
            escala[i] = s; dx[i] = t[0] / SW; dy[i] = t[1] / SW
            rot[i] = np.degrees(np.arctan2(A[1, 0], A[0, 0])); ok_m[i] = True
    prev_k, prev_d = k, d
cap.release()


def suav(x, n=9):
    if len(x) < n:
        return x
    return np.convolve(x, np.ones(n) / n, mode="same")


# ---------------- estadisticas por toma ----------------
tomas = []
for ti in range(len(cortes) - 1):
    a, b = cortes[ti], cortes[ti + 1]
    if b - a < 2:
        continue
    seg = slice(a + 1, b)
    sc = escala[seg]; mx = dx[seg]; my = dy[seg]; okk = ok_m[seg]
    zoom_total = float(np.prod(sc)) - 1.0                       # +0.15 = acerco 15 %
    log_s = np.log(sc)
    zoom_rapido = float(np.max(np.abs(suav(log_s, 5))) * FPS) if len(log_s) else 0.0   # velocidad maxima (escala/s)
    pan_x = float(np.sum(mx)); pan_y = float(np.sum(my))
    res_x = mx - suav(mx, 9); res_y = my - suav(my, 9)
    temblor = float(np.sqrt(np.mean(res_x ** 2 + res_y ** 2))) * 100 if len(mx) else 0.0   # % del ancho por fotograma
    dur = (b - a) / FPS
    cobertura = float(okk.mean()) if len(okk) else 0.0
    if cobertura < 0.4:
        tipo = "indeterminado"
    elif zoom_rapido > 0.8 and abs(zoom_total) > 0.06 and dur < 1.2:
        tipo = "golpe de zoom"
    elif zoom_total > 0.03:
        tipo = "acercamiento"
    elif zoom_total < -0.03:
        tipo = "alejamiento"
    elif max(abs(pan_x), abs(pan_y)) > 0.12:
        tipo = "paneo / seguimiento"
    else:
        tipo = "fija"
    if temblor > 0.6 and tipo != "indeterminado":
        tipo += " + temblor"
    tomas.append({"n": len(tomas) + 1, "inicio": round(a / FPS, 3), "fin": round(b / FPS, 3), "duracion": round(dur, 3),
                  "zoom_total_pct": round(zoom_total * 100, 1), "zoom_vel_max": round(zoom_rapido, 3),
                  "paneo_x_pct": round(pan_x * 100, 1), "paneo_y_pct": round(pan_y * 100, 1),
                  "temblor_pct": round(temblor, 3), "medicion_ok_pct": round(cobertura * 100), "tipo": tipo})

# ---------------- voz (transcripcion con tiempos) ----------------
palabras = []
if not args.sin_voz:
    wav = os.path.join(OUT, "audio16k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VID, "-ac", "1", "-ar", "16000", wav], check=True)
    try:
        from faster_whisper import WhisperModel
        modelo = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
        audio = np.frombuffer(raw, dtype=np.float32)
        segs, info = modelo.transcribe(audio, language="es", word_timestamps=True, vad_filter=True)
        for sg in segs:
            for w in sg.words or []:
                palabras.append({"t0": round(w.start, 2), "t1": round(w.end, 2), "p": w.word.strip()})
        print("  palabras transcritas:", len(palabras))
    except Exception as e:
        print("  (sin transcripcion:", e, ")")
    if os.path.exists(wav):
        os.remove(wav)

# relacion cortes <-> voz
alineados = 0
if palabras:
    inicios = np.array([w["t0"] for w in palabras])
    for t in tomas[1:]:
        if np.min(np.abs(inicios - t["inicio"])) < 0.25:
            alineados += 1
# texto de cada toma
for t in tomas:
    t["texto"] = " ".join(w["p"] for w in palabras if t["inicio"] <= w["t0"] < t["fin"])

# ---------------- hojas de contacto (inicio / mitad / fin de cada toma) ----------------
TW = 200
TH = int(TW * H / W)
cap = cv2.VideoCapture(VID)


def frame_at(f):
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(NF - 1, f)))
    okf, fr = cap.read()
    return cv2.resize(fr, (TW, TH)) if okf else np.zeros((TH, TW, 3), np.uint8)


POR_HOJA = 6
for h0 in range(0, len(tomas), POR_HOJA):
    filas = []
    for t in tomas[h0:h0 + POR_HOJA]:
        a, b = int(t["inicio"] * FPS), int(t["fin"] * FPS)
        ims = [frame_at(a + 1), frame_at((a + b) // 2), frame_at(b - 2)]
        fila = np.hstack(ims)
        info_w = 360
        panel = np.full((TH, info_w, 3), 30, np.uint8)
        lineas = ["TOMA %d" % t["n"], "%.2f-%.2f s (%.2f s)" % (t["inicio"], t["fin"], t["duracion"]), t["tipo"],
                  "zoom %+.1f%%  paneo %.0f/%.0f%%" % (t["zoom_total_pct"], t["paneo_x_pct"], t["paneo_y_pct"]),
                  "temblor %.2f" % t["temblor_pct"]]
        txt = t.get("texto", "")
        while txt:
            lineas.append(txt[:30]); txt = txt[30:]
            if len(lineas) > 9:
                break
        for li, s in enumerate(lineas):
            cv2.putText(panel, s.encode("ascii", "replace").decode(), (10, 30 + li * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (80, 220, 255) if li == 0 else (235, 235, 235), 2 if li == 0 else 1, cv2.LINE_AA)
        filas.append(np.hstack([fila, panel]))
    cv2.imwrite(os.path.join(OUT, "hojas", "hoja_%02d.jpg" % (h0 // POR_HOJA + 1)), np.vstack(filas), [cv2.IMWRITE_JPEG_QUALITY, 85])
cap.release()

# ---------------- grafica ----------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tt = np.arange(NF) / FPS
    fig, ax = plt.subplots(3, 1, figsize=(14, 7), sharex=True)
    ax[0].bar([t["inicio"] for t in tomas], [t["duracion"] for t in tomas], width=[t["duracion"] * 0.95 for t in tomas], align="edge", color="#4a90d9")
    ax[0].set_ylabel("duracion toma (s)")
    z = np.cumprod(escala)
    for c in cortes:
        z[c:] = z[c:] / max(z[c - 1], 1e-6) if 0 < c < NF else z[c:]
    ax[1].plot(tt, (z - 1) * 100, color="#d9534f"); ax[1].set_ylabel("zoom acumulado %")
    ax[2].plot(tt, np.abs(dx - suav(dx)) * 100 + np.abs(dy - suav(dy)) * 100, color="#5cb85c", lw=0.7); ax[2].set_ylabel("temblor")
    ax[2].set_xlabel("segundos")
    for a_ in ax:
        for c in cortes[1:-1]:
            a_.axvline(c / FPS, color="#999", lw=0.5)
    if palabras:
        for w in palabras:
            ax[0].plot([w["t0"]], [0], "k|", ms=6)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "grafica.png"), dpi=90); plt.close(fig)
except Exception as e:
    print("  (sin grafica:", e, ")")

# ---------------- resumen ----------------
dur_t = np.array([t["duracion"] for t in tomas]) if tomas else np.array([0])
tipos = {}
for t in tomas:
    base = t["tipo"].replace(" + temblor", "")
    tipos[base] = tipos.get(base, 0) + 1
con_temblor = sum(1 for t in tomas if "temblor" in t["tipo"])
resumen = {
    "video": origen, "duracion_s": round(DUR, 2), "resolucion": "%dx%d" % (W, H), "fps": round(FPS, 2),
    "tomas": len(tomas), "cortes_por_minuto": round((len(tomas) - 1) / DUR * 60, 1),
    "toma_media_s": round(float(dur_t.mean()), 2), "toma_mediana_s": round(float(np.median(dur_t)), 2),
    "toma_min_s": round(float(dur_t.min()), 2), "toma_max_s": round(float(dur_t.max()), 2),
    "tipos": tipos, "tomas_con_temblor": con_temblor,
    "zoom_medio_en_acercamientos_pct": round(float(np.mean([t["zoom_total_pct"] for t in tomas if t["zoom_total_pct"] > 3] or [0])), 1),
    "palabras": len(palabras), "palabras_por_segundo": round(len(palabras) / DUR, 2) if palabras else None,
    "cortes_alineados_con_palabra_pct": round(100 * alineados / max(1, len(tomas) - 1)) if palabras else None,
}
json.dump({"resumen": resumen, "tomas": tomas, "palabras": palabras}, open(os.path.join(OUT, "datos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

L = ["# Análisis — %s" % origen, "", "| Dato | Valor |", "|---|---|"]
etiquetas = [("duracion_s", "Duración (s)"), ("tomas", "Tomas"), ("cortes_por_minuto", "Cortes por minuto"), ("toma_media_s", "Toma media (s)"),
             ("toma_mediana_s", "Toma mediana (s)"), ("toma_min_s", "Toma más corta (s)"), ("toma_max_s", "Toma más larga (s)"),
             ("tomas_con_temblor", "Tomas con temblor"), ("zoom_medio_en_acercamientos_pct", "Zoom medio en acercamientos (%)"),
             ("palabras_por_segundo", "Palabras por segundo"), ("cortes_alineados_con_palabra_pct", "Cortes que caen en una palabra (%)")]
for k, et in etiquetas:
    L.append("| %s | %s |" % (et, resumen[k]))
L += ["", "**Tipos de toma:** " + ", ".join("%s: %d" % kv for kv in sorted(tipos.items(), key=lambda kv: -kv[1])), "",
      "## Tomas", "", "| # | Inicio | Dur. | Tipo | Zoom % | Paneo x/y % | Temblor | Texto |", "|---|---|---|---|---|---|---|---|"]
for t in tomas:
    L.append("| %d | %.2f | %.2f | %s | %+.1f | %.0f / %.0f | %.2f | %s |" % (t["n"], t["inicio"], t["duracion"], t["tipo"], t["zoom_total_pct"],
                                                                     t["paneo_x_pct"], t["paneo_y_pct"], t["temblor_pct"], t.get("texto", "")))
L += ["", "Hojas de contacto: `hojas/` · Gráfica: `grafica.png`",
      "", "> Revisar las hojas para completar lo que la máquina no mide: tipo de plano (general/medio/primer plano), encuadre, transiciones especiales, subtítulos."]
open(os.path.join(OUT, "ficha.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------------- ficha de estilo del creador (todas sus referencias) ----------------
todos = []
for f in sorted(glob.glob(os.path.join(carpeta_creador, "*", "datos.json"))):
    todos.append(json.load(open(f, encoding="utf-8")))
if todos:
    durs = np.concatenate([[t["duracion"] for t in d["tomas"]] for d in todos])
    tipos_all = {}
    for d in todos:
        for k, v in d["resumen"]["tipos"].items():
            tipos_all[k] = tipos_all.get(k, 0) + v
    ntomas = sum(len(d["tomas"]) for d in todos)
    F = ["# Ficha de estilo — %s" % args.creador, "", "Basada en %d video(s) y %d tomas." % (len(todos), ntomas), "",
         "| Regla medida | Valor |", "|---|---|",
         "| Toma media | %.2f s |" % durs.mean(), "| Toma mediana | %.2f s |" % np.median(durs),
         "| 80 %% de las tomas duran entre | %.2f y %.2f s |" % (np.percentile(durs, 10), np.percentile(durs, 90)),
         "| Cortes por minuto (promedio) | %.1f |" % np.mean([d["resumen"]["cortes_por_minuto"] for d in todos])]
    pps = [d["resumen"]["palabras_por_segundo"] for d in todos if d["resumen"]["palabras_por_segundo"]]
    if pps:
        F.append("| Ritmo de narración | %.2f palabras/s |" % np.mean(pps))
    al = [d["resumen"]["cortes_alineados_con_palabra_pct"] for d in todos if d["resumen"]["cortes_alineados_con_palabra_pct"] is not None]
    if al:
        F.append("| Cortes que coinciden con una palabra | %.0f %% |" % np.mean(al))
    F += ["", "**Tipos de toma (todas):** " + ", ".join("%s %.0f %%" % (k, 100 * v / ntomas) for k, v in sorted(tipos_all.items(), key=lambda kv: -kv[1])),
          "", "## Videos analizados"] + ["- `%s` — %d tomas, toma media %.2f s" % (d["resumen"]["video"], d["resumen"]["tomas"], d["resumen"]["toma_media_s"]) for d in todos]
    F += ["", "## Reglas para nuestras cámaras (completar al revisar las hojas)", "- ..."]
    open(os.path.join(carpeta_creador, "ficha_estilo.md"), "w", encoding="utf-8").write("\n".join(F) + "\n")
print("LISTO:", resumen)
