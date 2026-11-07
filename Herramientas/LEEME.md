# Herramientas

Todas leen rutas de `config.py` (y las de cada PC de `mi_config.json`). Comandos desde la raíz del kit.

| Script | Para qué | Cómo se usa |
|---|---|---|
| `config.py` | Rutas y valores centrales | `from config import *` |
| `blender/bl.py` | Enviar un script al Blender abierto (addon BlenderMCP) | `py Herramientas/blender/bl.py mi_script.py` |
| `blender/revisar_camaras.py` | Revisa cada fotograma: obstrucciones, objetos cercanos tapando, personaje fuera de cuadro. Cada cámara dice a quién sigue con su propiedad `sujeto` (`"Coco_Rig,Lila_Rig"`, `"Gato"`; vacío = no revisar) y rangos tapados a propósito con `excepto` | `blender.exe -b episodio.blend --python Herramientas/blender/revisar_camaras.py` (o con `bl.py` en el Blender abierto) |
| `audio/recortar_pausas.py` | Quita los silencios largos de la voz sin que se note el corte (voz de ElevenLabs o voz propia con `--audio`, tiempos con Whisper) → `audio/voz.wav` + `voz_palabras.json` | `py Herramientas/audio/recortar_pausas.py EP###_Titulo [--audio su_voz.mp3]` |
| `armar_secuencia_caras.py` | Arma la secuencia de caras (`Caras/Emociones/_secuencia/`) desde tus PNG para las caras por emoción | `py Herramientas/armar_secuencia_caras.py [--sonrisa textura.png]` |
| `render_paralelo.py` | Renderiza con 2 (o 3) Blender a la vez, cada uno un pedazo seguido de fotogramas (≈1,6× más rápido con una tarjeta) | `py Herramientas/render_paralelo.py EP###_Titulo preview` |
| `audio/tomas_desde_voz.py` | La voz manda el ritmo: de `narracion.txt` (una línea = una toma) y los tiempos de ElevenLabs calcula cada toma (corte en su primera palabra) y el fotograma de cada palabra → `audio/tomas_voz.json` | `py Herramientas/audio/tomas_desde_voz.py EP###_Titulo` |
| `blender/caras_textura.py` | Caras intercambiables en la textura de la cabeza (sin planos encima): propiedad `cara` del rig con la emoción (números en `Caras/Emociones/_secuencia/caras.json`) | dentro de Blender: `import caras_textura as ct; ct.preparar(rig, cara=15); ct.poner(rig, 7, frame)` |
| `blender/hoja_contacto.py` + `componer_hoja.py` | Hoja de contacto: fotos de inicio/mitad/fin de cada toma (marcadores con cámara) en una sola imagen con etiquetas | `blender.exe -b episodio.blend --python Herramientas/blender/hoja_contacto.py -- carpeta 22 8 [toma_desde toma_hasta]` y luego `py Herramientas/componer_hoja.py carpeta hoja.jpg` |
| `blender/armar_rig_r15_auto.py` | **Rig R15 automático**: centra, voltea, reconoce las 15 piezas y los accesorios (probado con Ajolota, Coco, Lila, Raul) | `blender.exe -b --factory-startup --python armar_rig_r15_auto.py -- "<carpeta>" Nombre` |
| `blender/armar_rig_r15_plantilla.py` | Plantilla para armar el rig R15 de un personaje exportado de Roblox | Ver receta en `docs/03_PERSONAJES.md` |
| `blender/resolver_pose_brazos.py` | Busca ángulos de brazos para que las manos lleguen a un punto (y pies planos) | `blender.exe -b --factory-startup --python resolver_pose_brazos.py -- RIG.blend NombreRig` (editar `BODY` y objetivo) |
| `blender/limpiar_escenario.py` | Guarda solo el escenario de un `.blend` de episodio | `blender.exe -b EP.blend --python limpiar_escenario.py -- salida.blend` |
| `blender/fotos_escenario.py` | Fotos de revisión de un escenario desde cámaras temporales (día/noche), sin tocar el .blend | `blender.exe -b escena.blend --python fotos_escenario.py -- vistas.json carpeta` |
| `blender/objetos_cartoon.py` | Objetos y efectos caricatura: burbuja de pensamiento, humo "¡pop!", nube que llueve, pan, elefante, sombrero de bruja, escoba, gato, paraguas, cuaderno, linterna, lonchera; **monstruo desde un personaje** (`monstruo_desde`) | `import objetos_cartoon as oc` dentro de Blender |
| `rehacer_tramo.py` | Rehace solo un tramo del video (ej. 10–15 s): respalda los fotogramas viejos, renderiza ese tramo y vuelve a armar el MP4 | `py Herramientas/rehacer_tramo.py EP###_Titulo 10 15 [--final]` · `--deshacer` regresa el respaldo |
| `audio/voz_elevenlabs.py` | Narración con tiempos por letra (**gasta créditos**) | `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo` (lee `EP###/narracion.txt`) |
| `audio/armar_video.py` | Voz por toma + efectos + subtítulos + MP4 (plantilla con el ejemplo de EP001) | Copiar a `EP###/scripts/`, editar `LINES`, `NEW_START`, efectos y `CHUNKS` → `py armar_video.py EP###_Titulo preview` o `final` |
