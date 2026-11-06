---
name: rehacer-tramo
description: Corrige solo una parte del video sin volver a renderizar todo. Usar cuando el usuario diga "del segundo X al Y no me gustó", "cambia esa parte", "rehaz esa toma", "regresa la versión anterior".
---

# Rehacer solo un tramo

1. Identificar los segundos (o la toma) y qué quiere cambiar. Si no está claro, mostrar una foto de ese momento y preguntar.
2. Hacer el cambio **solo en ese tramo** del `.blend` del episodio (animación, cámara, objetos) y guardarlo.
   - Si el cambio alarga o acorta el tramo, avisar: eso mueve todo lo que sigue y hay que re-renderizar desde ese punto (y reacomodar voz/subtítulos).
3. Revisar cámaras del tramo (`revisar_camaras.py`) y una foto de inicio/mitad/fin.
4. `py Herramientas/rehacer_tramo.py EP###_Titulo DESDE HASTA` (vista previa) o con `--final`. Respalda los fotogramas viejos en `Respaldos/`, renderiza solo ese tramo y vuelve a armar el MP4.
5. Mostrar el resultado. Si no le gusta: `py Herramientas/rehacer_tramo.py EP###_Titulo --deshacer` regresa la versión anterior.
