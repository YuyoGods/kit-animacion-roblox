# Utilidades comunes del analizador: rutas, ffmpeg, registro, textos.
import hashlib, json, os, re, subprocess, sys, unicodedata
import numpy as np

MOTOR = os.path.dirname(os.path.abspath(__file__))
ANALIZADOR = os.path.dirname(MOTOR)
VIDEOS = os.path.join(ANALIZADOR, "Videos_para_analizar")
RESULTADOS = os.path.join(ANALIZADOR, "Resultados")
ESTILOS = os.path.join(ANALIZADOR, "Estilos")
REGISTRO = os.path.join(RESULTADOS, "registro.json")
VERSION = 2
EXT_VIDEO = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")
FUENTE = r"C:\Windows\Fonts\arial.ttf"
FUENTE_N = r"C:\Windows\Fonts\arialbd.ttf"


def log(*a):
    print(*a, flush=True)


def slug(texto, largo=40):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")
    return (t or "video")[:largo]


def video_id(ruta):
    base = os.path.splitext(os.path.basename(ruta))[0]
    return slug(base) + "_" + hashlib.md5(base.encode("utf-8")).hexdigest()[:6]


def ffprobe(ruta):
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", ruta],
                       capture_output=True, text=True, encoding="utf-8")
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    num, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1").split("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    return {"ancho": int(v.get("width", 0)), "alto": int(v.get("height", 0)), "fps": round(fps, 3),
            "duracion": float(d.get("format", {}).get("duration", 0) or 0), "audio": a is not None,
            "codec": v.get("codec_name", "")}


def hacer_proxy(ruta, destino, fps_orig, max_lado=960):
    """copia liviana para analizar: lado mayor 960 px, maximo 30 fps, sin audio, nombre simple."""
    vf = "scale='if(gt(iw,ih),%d,-2)':'if(gt(iw,ih),-2,%d)'" % (max_lado, max_lado)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", ruta, "-vf", vf]
    if fps_orig > 31:
        cmd += ["-r", "30"]
    cmd += ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", destino]
    subprocess.run(cmd, check=True)


def leer_audio(ruta, sr=16000):
    """audio mono float32 (numpy) directo del video, sin archivos intermedios."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vn", "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                       capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".%d.tmp" % os.getpid()          # un temporal por proceso: varios motores a la vez no chocan
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=_np)
    os.replace(tmp, ruta)


def _np(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    raise TypeError(type(o))


def leer_json(ruta, defecto=None):
    if not os.path.exists(ruta):
        return defecto
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def mmss(t):
    t = max(0.0, float(t))
    return "%d:%04.1f" % (int(t // 60), t % 60)


def suav(x, n=9):
    x = np.asarray(x, dtype=float)
    if len(x) < n or n < 2:
        return x.copy()
    k = np.ones(n) / n
    pad = n // 2
    xp = np.pad(x, pad, mode="edge")
    return np.convolve(xp, k, mode="valid")[:len(x)]


def pct(a, q):
    a = np.asarray([v for v in a if v is not None], dtype=float)
    return float(np.percentile(a, q)) if len(a) else None


def r(x, n=2):
    return None if x is None else round(float(x), n)


def fuente(tam, negrita=False):
    from PIL import ImageFont
    for f in ([FUENTE_N] if negrita else []) + [FUENTE]:
        try:
            return ImageFont.truetype(f, tam)
        except OSError:
            pass
    return ImageFont.load_default()
