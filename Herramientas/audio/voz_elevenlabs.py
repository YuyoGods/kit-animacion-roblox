# Genera la narracion con ElevenLabs (con tiempos por letra para sincronizar subtitulos).
# Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt] [--voz ID_DE_VOZ] [--velocidad 1.06]
#   Lee el texto de EP###/narracion.txt (lineas con # se ignoran) y guarda en EP###/audio/:
#   narracion.mp3 + narracion_tiempos.json
#   --voz: probar otra voz sin cambiar "voz_narrador" de mi_config.json.
#   --velocidad: 0.7 a 1.2 (1.0 normal); 1.05-1.08 = ritmo de Shorts sin que suene acelerado.
# GASTA CREDITOS de ElevenLabs: confirmar con el usuario antes de correrlo.
# La clave se lee de la variable de entorno ELEVENLABS_API_KEY de Windows; nunca se imprime ni se guarda.
import base64, json, os, sys, urllib.error, urllib.request


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            sys.exit("No encuentro Herramientas/config.py")
        d = os.path.dirname(d)
    return d


sys.path.insert(0, os.path.join(_raiz(), "Herramientas"))
from config import VOZ_NARRADOR, MODELO_VOZ, episodio  # noqa: E402

_args = list(sys.argv[1:])
VOZ_ELEGIDA = None
VELOCIDAD = None
if "--velocidad" in _args:
    i = _args.index("--velocidad")
    VELOCIDAD = float(_args[i + 1])
    del _args[i:i + 2]
if "--voz" in _args:
    i = _args.index("--voz")
    VOZ_ELEGIDA = _args[i + 1] if i + 1 < len(_args) else None
    del _args[i:i + 2]
if not _args:
    sys.exit("Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt] [--voz ID_DE_VOZ]")
EP = episodio(_args[0])
TXT = _args[1] if len(_args) > 1 else os.path.join(EP, "narracion.txt")
if not os.path.exists(TXT):
    sys.exit("No existe el texto: " + TXT)
TEXT = " ".join(l.strip() for l in open(TXT, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#"))
if not TEXT:
    sys.exit("El texto esta vacio: " + TXT)
VOICE = VOZ_ELEGIDA or VOZ_NARRADOR
if not VOICE:
    sys.exit("Falta \"voz_narrador\" (id de la voz) en mi_config.json")
OUT = os.path.join(EP, "audio")
os.makedirs(OUT, exist_ok=True)


def api_key():
    v = os.environ.get("ELEVENLABS_API_KEY")
    if not v and sys.platform == "win32":
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            v, _ = winreg.QueryValueEx(k, "ELEVENLABS_API_KEY")
        except OSError:
            v = None
    if not v:
        sys.exit("Falta la variable de entorno ELEVENLABS_API_KEY (ver README)")
    return v.strip()


body = {
    "text": TEXT,
    "model_id": MODELO_VOZ,
    "voice_settings": {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True},
}
if VELOCIDAD:
    body["voice_settings"]["speed"] = max(0.7, min(1.2, VELOCIDAD))
url = "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % VOICE
req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                             headers={"xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print("ERROR HTTP", e.code, e.read().decode("utf-8", "replace")[:500])
    sys.exit(1)
audio = base64.b64decode(data["audio_base64"])
open(os.path.join(OUT, "narracion.mp3"), "wb").write(audio)
json.dump(data.get("alignment") or data.get("normalized_alignment"), open(os.path.join(OUT, "narracion_tiempos.json"), "w", encoding="utf-8"), ensure_ascii=False)
al = data.get("alignment") or {}
print("ok | audio:", len(audio), "bytes | caracteres:", len(TEXT), "| duracion aprox:", round(al.get("character_end_times_seconds", [0])[-1], 2), "s")
