---
name: instalar-kit
description: Instala o revisa el Kit de Animación Roblox en esta PC (Python, paquetes, FFmpeg, Blender 5.2, addon BlenderMCP, GPU, archivos personales) y configura el canal del usuario. Usar la primera vez, cuando el usuario diga "instala el kit", "revisa la instalación", o cuando algo del kit no arranque.
---

# Instalar / revisar el kit

Responder en español, breve. Pedir permiso antes de **cada** descarga o instalación (decir qué es y de dónde viene). Nunca pedir claves en el chat.

1. **Revisión**: `py instalar.py` (desde la raíz del kit). Leer los `[falta]` y `[aviso]`.
2. **Lo que falte**, en este orden (con permiso):
   - Python 3.11+ → `winget install Python.Python.3.13`
   - Git → `winget install Git.Git` · FFmpeg → `winget install Gyan.FFmpeg` (abrir una terminal nueva después)
   - Paquetes → `py instalar.py --paquetes` (PyTorch con CUDA, EasyOCR, CLIP, Whisper, librosa…; varios minutos, ~4 GB)
   - Blender 5.2 → https://www.blender.org/download/ (lo instala el usuario; si no se detecta, su ruta va en `mi_config.json` → `"blender"`)
3. **BlenderMCP** (para que Claude controle el Blender abierto): con permiso, descargar `addon.py` de https://github.com/ahujasid/blender-mcp a una carpeta nueva. El usuario lo instala: Blender → Edit → Preferences → Add-ons → Install from Disk → activar; en la vista 3D tecla **N** → pestaña **BlenderMCP** → **Connect**. Probar con `py Herramientas/blender/bl.py` (responde la versión de Blender).
4. **Archivos personales**: `instalar.py` crea `mi_config.json`, `MI_CANAL.md` y `MI_BITACORA.md` si no existen (nunca los sobrescribe).
5. **Configurar el canal**: preguntar y llenar `MI_CANAL.md`: nombre del canal, protagonista, secundarios, rol `usuario`. Voz de ElevenLabs opcional: el usuario crea la variable de entorno él mismo (README → "Clave de ElevenLabs") y el id de la voz va en `mi_config.json`.
6. **Memoria**: guardar en la memoria del usuario que el kit vive en esta carpeta y que antes de cualquier animación hay que leer `CLAUDE.md` y `MI_CANAL.md`.
7. Volver a correr `py instalar.py` y decir qué quedó listo y el siguiente paso (normalmente: subir su protagonista a `Personajes/Protagonista/<Nombre>/` y pedir "ponle su rig").
