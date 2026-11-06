# Genera la narracion con ElevenLabs (con tiempos por letra para sincronizar subtitulos).
# Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt]
#   Lee el texto de EP###/narracion.txt (lineas con # se ignoran) y guarda en EP###/audio/:
#   narracion.mp3 + narracion_tiempos.json
# GASTA CREDITOS de ElevenLabs: confirmar con el usuario antes de correrlo.
# La clave se lee de la variable de entorno ELEVENLABS_API_KEY de Windows; nunca se imprime ni se guarda.
import base64, json, os, sys, urllib.error, urllib.request


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "04_Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            sys.exit("No encuentro 04_Herramientas/config.py")
        d = os.path.dirname(d)
    return d


sys.path.insert(0, os.path.join(_raiz(), "04_Herramientas"))
from config import VOZ_NARRADOR, MODELO_VOZ, episodio  # noqa: E402

if len(sys.argv) < 2:
    sys.exit("Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt]")
EP = episodio(sys.argv[1])
TXT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EP, "narracion.txt")
if not os.path.exists(TXT):
    sys.exit("No existe el texto: " + TXT)
TEXT = " ".join(l.strip() for l in open(TXT, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#"))
if not TEXT:
    sys.exit("El texto esta vacio: " + TXT)
VOICE = VOZ_NARRADOR
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
