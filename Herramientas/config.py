# Configuracion central. Los scripts importan de aqui en vez de escribir rutas fijas:
#   import sys, os; sys.path.insert(0, RUTA_A_Herramientas); from config import *
# Las rutas propias de cada PC (Blender, efectos, voz) estan en mi_config.json (lo crea instalar.py).
import json, os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PERSONAJES = os.path.join(RAIZ, "Personajes")
ESCENARIOS = os.path.join(RAIZ, "Escenarios")
EPISODIOS = os.path.join(RAIZ, "Episodios")
HERRAMIENTAS = os.path.join(RAIZ, "Herramientas")
ANALIZADOR = os.path.join(RAIZ, "Analizador")
ESTILOS = os.path.join(ANALIZADOR, "Estilos")
RESPALDOS = os.path.join(RAIZ, "Respaldos")

_DEF = {
    "blender": r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    "blender_mcp_puerto": 9876,
    "sfx": "",
    "fuente_subtitulos": r"C:\Windows\Fonts\ariblk.ttf",
    "voz_narrador": "",
    "modelo_voz": "eleven_multilingual_v2",
}
_cfg_path = os.path.join(RAIZ, "mi_config.json")
CFG = dict(_DEF)
if os.path.exists(_cfg_path):
    CFG.update(json.load(open(_cfg_path, encoding="utf-8")))

BLENDER = CFG["blender"]
BLENDER_MCP_PUERTO = int(CFG["blender_mcp_puerto"])
SFX = CFG["sfx"]
FUENTE_SUBTITULOS = CFG["fuente_subtitulos"]
VOZ_NARRADOR = CFG["voz_narrador"]
MODELO_VOZ = CFG["modelo_voz"]
CARAS = os.path.join(RAIZ, "Caras")                      # PNG por emocion: feliz.png, enojado.png...

# formato estandar
ANCHO, ALTO, FPS = 1080, 1920, 30


def episodio(nombre):
    """ruta de la carpeta de un episodio, ej. episodio('EP001_Crista_Llega_Tarde')"""
    return os.path.join(EPISODIOS, nombre)
