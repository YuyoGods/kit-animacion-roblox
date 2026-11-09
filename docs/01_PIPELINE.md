# 01 — Pipeline de un episodio (checklist)

Marcar cada paso. No saltar la **revisión de cámaras** (paso 6).

## 0. Preparar
- [ ] Copiar `Episodios/_PLANTILLA_EPISODIO` → `Episodios/EP###_Titulo`.
- [ ] Llenar `GUION.md` (idea, historia, tabla de tomas).
- [ ] Referencias del usuario (videos MP4) → `Analizador/Videos_para_analizar/<Creador>/` (estilo) o `referencias/` del episodio (una toma concreta).
  - Para analizarlas: `ffmpeg -i video.mp4 -vf "fps=1/2,scale=180:320,tile=8x5" hoja.jpg` y detección de cortes con `select='gt(scene,0.3)',showinfo`.

## 1. Guion y tomas
- [ ] Historia corta estilo "historias de Roblox": gancho en los primeros 3 s → problema → acción → final con suspenso.
- [ ] **La voz manda el ritmo** (pedido del usuario, EP002): **cada escena lleva voz** (no quedan partes calladas; el video dura lo que la voz, aunque sea corto), frases cortas y concretas ("no pienses en un elefante rosa, porque… ¡pop!"). En `narracion.txt` **una línea = una toma** (tomas de ~1,5–2,5 s, corte en cada idea).
- [ ] **Sin storyboard** (decisión del usuario 2026-11-08: en EP004 dejó a los personajes tiesos; ya no viene en el kit). En su lugar, con el texto aprobado y **antes de la voz**, el **plano de construcción** (`PLANO.md` de la plantilla): lugares, personajes (caras y bocas que hacen falta), objetos (de `docs/10_CATALOGO.md` o nuevos, con referencia y un color que contraste), efectos, letreros y la **tabla de tomas** con el tipo de toma de `docs/09_RECETA_SIMPLE.md`. Construir lo que falta y mostrarle fotos al usuario; regenerar el catálogo (`py -X utf8 Herramientas/catalogo.py`) si se agregó algo.
- [ ] Orden nuevo: texto aprobado → plano de construcción → **voz primero** a velocidad normal, con la voz de cada quien (`voz_elevenlabs.py EP###`, confirmar créditos; o una voz ya hecha) → **el usuario la escucha y la aprueba** → `py Herramientas/audio/recortar_pausas.py EP### [--audio su_voz.mp3]` (quita silencios largos sin cortar la voz, deja un respiro corto entre líneas y la revisa con Whisper; si avisa que una palabra no se oye: corregir esa línea y `voz_elevenlabs.py EP### --linea N`) → `py Herramientas/audio/tomas_desde_voz.py EP###` (tomas y fotograma de cada palabra en `audio/tomas_voz.json`) → animar leyendo ese archivo (los golpes caen en su palabra).
- [ ] Tabla de tomas: número, tipo (dron/frontal/lateral/giro/pegada/plano detalle), acción y su línea de voz (la duración sale de la voz).
- [ ] El usuario aprueba el guion **antes** de animar.

## 2. Personajes
- [ ] ¿Existe en `Personajes/`? Si no: exportar desde Roblox Studio (OBJ del cuerpo + OBJ de accesorios con texturas) y armar rig (ver `03_PERSONAJES.md`).
- [ ] Probar el rig: pose de prueba renderizada de frente/lado/espalda.

## 3. Escenario
- [ ] Partir del `.blend` limpio del escenario o de su script.
- [ ] Todo cambio al escenario se hace con un script guardado en `Escenarios/<nombre>/scripts/` (se puede repetir).
- [ ] Anotar coordenadas nuevas en `04_ESCENARIOS.md`.

## 4. Montaje del episodio
- [ ] Abrir/crear el `.blend` del episodio en su carpeta. Traer personajes con `libraries.load` (colección del personaje).
- [ ] Fijar formato: 1080×1920, 30 fps, Eevee, Standard, shadow pool 1024.

## 5. Animación (script del episodio en `scripts/`)
- [ ] **Receta simple** (`docs/09_RECETA_SIMPLE.md`, `Herramientas/blender/tomas_simples.py`): cámara fija o con acercamiento lento sin que nada tape la cara, un corte por frase (~1–2 s; 37–42 cortes por minuto y 2–3 cortes en los primeros 3 s), cuerpos quietos, caras por toma; en los diálogos solo la boca.
- [ ] **Nada tieso** (regla de oro 14): vida suave (`Herramientas/blender/vida_suave.py`, por defecto en `tomas_simples.armar`) + un gesto en la palabra clave; actuar toma por toma (`actuar.py`) donde la línea lo pide. Lento y de pocos grados.
- [ ] Trayectorias por segmento (camino con curva suave + velocidad) → posición/orientación del rig por fotograma.
- [ ] Altura del piso con **rayos** (escaleras, banquetas) + suavizado; no mezclar entre cortes.
- [ ] Ciclos de caminar/correr (ver parámetros en `03_PERSONAJES.md`) + poses especiales (calculadas con solver si hay manos/pies que deben tocar algo).
- [ ] Miradas de cabeza con claves suaves (voltear, mirar arriba/abajo).
- [ ] Cámaras: una por toma (`CR_Cam_S#_...`) + marcador `CR_S#_...` en el fotograma de inicio.
- [ ] Exportar eventos de sonido (pisadas, golpes, transiciones) a `audio/eventos.json`.

## 6. Revisión (OBLIGATORIA antes de cualquier render largo)
- [ ] `revisar_camaras.py`: rayos cámara→cabeza/pecho por fotograma + rejilla de "objeto cercano tapando". Resultado esperado: **0 obstrucciones** (salvo transiciones marcadas en `EXCEPT`).
- [ ] `revisar_encuadre.py` (cabeza o gorro cortados, cara en el tercio de arriba), `revisar_objetos.py` (lo que dice la voz sale en cuadro, grande, sin tapar y se distingue), `revisar_pies.py` (pies que patinan), `revisar_ojos.py` (personajes con gorro/visera o cabello largo: ¿se ven los ojos en cada cuadro?), `revisar_agarre.py` (objetos en la mano: hueco, se mete, resbala) y `detectar_superficies.py` (caras al ras o duplicadas que parpadean). Añadidas el 2026-11-08 (lecciones 17, 56, 57).
- [ ] Fotos de inicio/mitad/fin de **cada toma** (22 % de resolución) en una hoja de contacto. Revisar: ¿se ve bien el personaje? ¿se entiende la acción? ¿algo raro en la pose?
- [ ] **Borrador MP4 con voz** (1 de cada 2 cuadros, 25 %, 4 muestras) + hojas por toma (inicio, 1/4, mitad, 3/4 y final con su texto) para revisar cada fotograma. El usuario lo ve antes de la vista previa.
- [ ] Corregir y repetir hasta que todo esté limpio.

## 7. Vista previa
- [ ] Preguntar si quiere **2 Blender en paralelo** (`py Herramientas/render_paralelo.py EP### preview`, ≈1,6× más rápido; si no, `--procesos 1`). Se renderiza en segundo plano desde el `.blend` guardado: 50 %, 16 muestras, PNG → MP4.
- [ ] El usuario la revisa.

## 8. Voz, subtítulos y efectos
- [ ] La voz ya está hecha y aprobada desde la sección 1 (voz primero); las tomas y las palabras salen de `audio/tomas_voz.json`. Los efectos van en su palabra (`"palabra:pum"`).
- [ ] Copiar `Herramientas/audio/armar_video.py` a `EP###/scripts/`, editar frases/efectos/subtítulos → `py armar_video.py EP###_Titulo preview` → voz + efectos + subtítulos sobre la vista previa. Revisar fotos con subtítulos y nivel de audio (≈ −14/−15 LUFS).

## Cambios en una parte del video
- [ ] Cambiar solo esa parte en el `.blend`, guardar → `py Herramientas/rehacer_tramo.py EP###_Titulo --toma N` (una toma = una cámara; `--tomas` las lista) o `DESDE HASTA` en segundos (respalda, renderiza solo eso y re-arma el MP4). `--deshacer` regresa la versión anterior.

## 9. Render final
- [ ] Confirmar con el usuario (≈1 h por 30 s).
- [ ] Render 100 % en segundo plano → `renders/final/fotogramas/c_####.png`.
- [ ] `py armar_video.py EP###_Titulo final` → MP4 final en `renders/final/`.
- [ ] Anotar en `MI_BITACORA.md`. Publicar **solo** si el usuario lo pide.
