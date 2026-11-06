# Herramientas

Todas leen rutas de `config.py` (y las de cada PC de `mi_config.json`). Comandos desde la raíz del kit.

| Script | Para qué | Cómo se usa |
|---|---|---|
| `config.py` | Rutas y valores centrales | `from config import *` |
| `blender/bl.py` | Enviar un script al Blender abierto (addon BlenderMCP) | `py Herramientas/blender/bl.py mi_script.py` |
| `blender/revisar_camaras.py` | Revisa cada fotograma: obstrucciones, objetos cercanos tapando, personaje fuera de cuadro | `py Herramientas/blender/bl.py Herramientas/blender/revisar_camaras.py` (ajustar `RIG_NOMBRE` y `EXCEPT`) |
| `blender/armar_rig_r15_plantilla.py` | Plantilla para armar el rig R15 de un personaje exportado de Roblox | Ver receta en `docs/03_PERSONAJES.md` |
| `blender/resolver_pose_brazos.py` | Busca ángulos de brazos para que las manos lleguen a un punto (y pies planos) | `blender.exe -b --factory-startup --python resolver_pose_brazos.py -- RIG.blend NombreRig` (editar `BODY` y objetivo) |
| `blender/limpiar_escenario.py` | Guarda solo el escenario de un `.blend` de episodio | `blender.exe -b EP.blend --python limpiar_escenario.py -- salida.blend` |
| `rehacer_tramo.py` | Rehace solo un tramo del video (ej. 10–15 s): respalda los fotogramas viejos, renderiza ese tramo y vuelve a armar el MP4 | `py Herramientas/rehacer_tramo.py EP###_Titulo 10 15 [--final]` · `--deshacer` regresa el respaldo |
| `audio/voz_elevenlabs.py` | Narración con tiempos por letra (**gasta créditos**) | `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo` (lee `EP###/narracion.txt`) |
| `audio/armar_video.py` | Voz por toma + efectos + subtítulos + MP4 (plantilla con el ejemplo de EP001) | Copiar a `EP###/scripts/`, editar `LINES`, `NEW_START`, efectos y `CHUNKS` → `py armar_video.py EP###_Titulo preview` o `final` |
