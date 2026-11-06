# Prepara el kit en esta PC. Se puede correr las veces que quieras: NUNCA sobrescribe tus archivos.
#   py instalar.py              -> revisa todo y crea lo que falte (mi_config.json, MI_CANAL.md, MI_BITACORA.md)
#   py instalar.py --paquetes   -> ademas instala los paquetes de Python de requirements.txt
import glob, importlib.util, json, os, shutil, socket, subprocess, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
OK, FALTA, AVISO = "[ok]   ", "[falta]", "[aviso]"
pendientes = []


def ruta(*p):
    return os.path.join(RAIZ, *p)


def crear_si_no_existe(destino, origen=None, texto=None):
    d = ruta(destino)
    if os.path.exists(d):
        print(OK, destino, "ya existe (no se toca)")
        return False
    if origen:
        shutil.copyfile(ruta(origen), d)
    else:
        open(d, "w", encoding="utf-8").write(texto)
    print(OK, destino, "creado")
    return True


print("== Kit de Animacion Roblox: revision ==\n")

# 1) Python
v = sys.version_info
if v >= (3, 11):
    print(OK, "Python %d.%d" % (v.major, v.minor))
else:
    print(FALTA, "Python 3.11 o mas nuevo (tienes %d.%d)" % (v.major, v.minor))
    pendientes.append("Instalar Python 3.11+ desde python.org")

# 2) Paquetes
PAQ = {"numpy": "numpy", "cv2": "opencv-python", "scenedetect": "scenedetect",
       "faster_whisper": "faster-whisper", "matplotlib": "matplotlib"}
faltan = [pip for mod, pip in PAQ.items() if importlib.util.find_spec(mod) is None]
if faltan and "--paquetes" in sys.argv:
    print("Instalando:", ", ".join(faltan))
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", ruta("requirements.txt")], check=False)
    faltan = [pip for mod, pip in PAQ.items() if importlib.util.find_spec(mod) is None]
if faltan:
    print(FALTA, "paquetes de Python:", ", ".join(faltan))
    pendientes.append("Instalar paquetes: py instalar.py --paquetes")
else:
    print(OK, "paquetes de Python (numpy, OpenCV, PySceneDetect, faster-whisper, matplotlib)")

# 3) FFmpeg con subtitulos (libass)
ff = shutil.which("ffmpeg")
if not ff:
    print(FALTA, "FFmpeg no esta en el PATH")
    pendientes.append("Instalar FFmpeg (winget install Gyan.FFmpeg) y abrir una terminal nueva")
else:
    filtros = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    if " ass " in filtros or " subtitles " in filtros:
        print(OK, "FFmpeg con subtitulos")
    else:
        print(AVISO, "FFmpeg sin libass: no podra quemar subtitulos")
        pendientes.append("Instalar una version completa de FFmpeg (winget install Gyan.FFmpeg)")

# 4) Blender
cfg_path = ruta("mi_config.json")
cfg = json.load(open(ruta("mi_config.ejemplo.json"), encoding="utf-8"))
if os.path.exists(cfg_path):
    cfg.update(json.load(open(cfg_path, encoding="utf-8")))
blender = cfg.get("blender", "")
if not os.path.exists(blender):
    candidatos = []
    for base in [os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")]:
        candidatos += glob.glob(os.path.join(base, "Blender Foundation", "Blender *", "blender.exe"))
        candidatos += glob.glob(os.path.join(base, "Steam", "steamapps", "common", "Blender", "blender.exe"))
    for letra in "CDEFG":
        candidatos += glob.glob(letra + r":\SteamLibrary\steamapps\common\Blender\blender.exe")
    if candidatos:
        blender = sorted(candidatos)[-1]
if os.path.exists(blender):
    print(OK, "Blender:", blender)
else:
    print(FALTA, "Blender 5.2 (no lo encontre)")
    pendientes.append("Instalar Blender 5.2 o poner su ruta en mi_config.json -> \"blender\"")

# 5) Archivos personales (solo si no existen)
print()
if not os.path.exists(cfg_path):
    cfg["blender"] = blender if os.path.exists(blender) else cfg["blender"]
    json.dump(cfg, open(cfg_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(OK, "mi_config.json creado")
else:
    print(OK, "mi_config.json ya existe (no se toca)")
crear_si_no_existe("MI_CANAL.md", origen="MI_CANAL.ejemplo.md")
crear_si_no_existe("MI_BITACORA.md", texto="# Mi bitacora (personal)\n\nUna entrada por sesion de trabajo (lo mas nuevo arriba).\n")
for c in ["00_Referencias", "01_Personajes/1_Protagonista", "01_Personajes/2_Secundarios", "01_Personajes/3_Pueblo_NPC",
          "01_Personajes/_Plantillas_Rigs", "02_Escenarios", "03_Episodios", "05_Recursos/Caras", "99_Archivo"]:
    os.makedirs(ruta(c), exist_ok=True)

# 6) Opcionales
print()
if not cfg.get("sfx") or not os.path.isdir(cfg.get("sfx", "")):
    print(AVISO, "sin carpeta de efectos de sonido (mi_config.json -> \"sfx\"); opcional")
else:
    print(OK, "efectos de sonido:", cfg["sfx"])
clave = os.environ.get("ELEVENLABS_API_KEY")
if not clave and sys.platform == "win32":
    try:
        import winreg
        clave = winreg.QueryValueEx(winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment"), "ELEVENLABS_API_KEY")[0]
    except OSError:
        clave = None
print(OK if clave else AVISO, "ElevenLabs:", "clave configurada" if clave else "sin clave (opcional; ver README)")
if not cfg.get("voz_narrador"):
    print(AVISO, "sin voz de narrador (mi_config.json -> \"voz_narrador\"); opcional")
try:
    socket.create_connection(("localhost", int(cfg.get("blender_mcp_puerto", 9876))), timeout=1).close()
    print(OK, "Blender abierto con BlenderMCP conectado")
except OSError:
    print(AVISO, "BlenderMCP no responde (abre Blender y presiona Connect en la pestana BlenderMCP; ver README)")
if os.listdir(ruta("01_Personajes", "1_Protagonista")) in ([], ["LEEME.md"]):
    pendientes.append("Poner tu protagonista en 01_Personajes/1_Protagonista/<Nombre>/ y pedirle a Claude su rig")

print("\n== Pendientes ==" if pendientes else "\n== Todo listo ==")
for p in pendientes:
    print(" -", p)
