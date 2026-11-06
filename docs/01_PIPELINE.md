# 01 — Pipeline de un episodio (checklist)

Marcar cada paso. No saltar la **revisión de cámaras** (paso 6).

## 0. Preparar
- [ ] Copiar `03_Episodios/_PLANTILLA_EPISODIO` → `03_Episodios/EP###_Titulo`.
- [ ] Llenar `GUION.md` (idea, historia, tabla de tomas).
- [ ] Referencias del usuario (videos MP4) → `00_Referencias/` o `referencias/` del episodio.
  - Para analizarlas: `ffmpeg -i video.mp4 -vf "fps=1/2,scale=180:320,tile=8x5" hoja.jpg` y detección de cortes con `select='gt(scene,0.3)',showinfo`.

## 1. Guion y tomas
- [ ] Historia corta estilo "historias de Roblox": gancho en los primeros 3 s → problema → acción → final con suspenso.
- [ ] Narración ≈ 2,5 palabras/s (30 s ≈ 70–80 palabras). Frases cortas, una por toma.
- [ ] Tabla de tomas: número, tipo (dron/frontal/lateral/giro/pegada/plano detalle), duración (2–4 s), acción, frase.
- [ ] El usuario aprueba el guion **antes** de animar.

## 2. Personajes
- [ ] ¿Existe en `01_Personajes/`? Si no: exportar desde Roblox Studio (OBJ del cuerpo + OBJ de accesorios con texturas) y armar rig (ver `03_PERSONAJES.md`).
- [ ] Probar el rig: pose de prueba renderizada de frente/lado/espalda.

## 3. Escenario
- [ ] Partir del `.blend` limpio del escenario o de su script.
- [ ] Todo cambio al escenario se hace con un script guardado en `02_Escenarios/<nombre>/scripts/` (se puede repetir).
- [ ] Anotar coordenadas nuevas en `04_ESCENARIOS.md`.

## 4. Montaje del episodio
- [ ] Abrir/crear el `.blend` del episodio en su carpeta. Traer personajes con `libraries.load` (colección del personaje).
- [ ] Fijar formato: 1080×1920, 30 fps, Eevee, Standard, shadow pool 1024.

## 5. Animación (script del episodio en `scripts/`)
- [ ] Trayectorias por segmento (camino con curva suave + velocidad) → posición/orientación del rig por fotograma.
- [ ] Altura del piso con **rayos** (escaleras, banquetas) + suavizado; no mezclar entre cortes.
- [ ] Ciclos de caminar/correr (ver parámetros en `03_PERSONAJES.md`) + poses especiales (calculadas con solver si hay manos/pies que deben tocar algo).
- [ ] Miradas de cabeza con claves suaves (voltear, mirar arriba/abajo).
- [ ] Cámaras: una por toma (`CR_Cam_S#_...`) + marcador `CR_S#_...` en el fotograma de inicio.
- [ ] Exportar eventos de sonido (pisadas, golpes, transiciones) a `audio/eventos.json`.

## 6. Revisión (OBLIGATORIA antes de cualquier render largo)
- [ ] `revisar_camaras.py`: rayos cámara→cabeza/pecho por fotograma + rejilla de "objeto cercano tapando". Resultado esperado: **0 obstrucciones** (salvo transiciones marcadas en `EXCEPT`).
- [ ] Fotos de inicio/mitad/fin de **cada toma** (22 % de resolución) en una hoja de contacto. Revisar: ¿se ve bien el personaje? ¿se entiende la acción? ¿algo raro en la pose?
- [ ] Corregir y repetir hasta que todo esté limpio.

## 7. Vista previa
- [ ] Guardar copia y renderizar en segundo plano: 50 %, 16 muestras, PNG → MP4.
- [ ] El usuario la revisa.

## 8. Voz, subtítulos y efectos
- [ ] Texto final en `EP###/narracion.txt` → `py 04_Herramientas/audio/voz_elevenlabs.py EP###_Titulo` → `audio/narracion.mp3` + tiempos por letra. Confirmar con el usuario antes de gastar créditos.
- [ ] Medir dónde cae cada frase vs. su toma; mover frases (`NEW_START`) para que coincidan con la acción; alargar la última toma si hace falta.
- [ ] Copiar `04_Herramientas/audio/armar_video.py` a `EP###/scripts/`, editar frases/efectos/subtítulos → `py armar_video.py EP###_Titulo preview` → voz + efectos + subtítulos sobre la vista previa. Revisar fotos con subtítulos y nivel de audio (≈ −14/−15 LUFS).

## 9. Render final
- [ ] Confirmar con el usuario (≈1 h por 30 s).
- [ ] Render 100 % en segundo plano → `renders/final/fotogramas/c_####.png`.
- [ ] `py armar_video.py EP###_Titulo final` → MP4 final en `renders/final/`.
- [ ] Anotar en `MI_BITACORA.md`. Publicar **solo** si el usuario lo pide.
