# Cambios del kit

> Una entrada por cada actualización que se sube al repositorio (lo más nuevo arriba).
> Si una actualización renombra o mueve archivos compartidos, avisarlo aquí.

## v0.4.0 — 2026-11-06 — La voz manda el ritmo
**Reglas nuevas para Shorts** (CLAUDE.md, reglas de oro 9–12; skill `nuevo-episodio` actualizada):
- **Cada escena lleva voz** (no quedan partes calladas): el video dura lo que la voz, aunque el guion sea corto. Una línea de `narracion.txt` = una toma (1,5–2,5 s, corte en cada idea).
- **Voz primero**, con la voz de cada quien (su ElevenLabs o una voz ya hecha), a **velocidad normal** y con emoción. El usuario la escucha y la aprueba antes de animar.
- **Recortar pausas sin que se note**: `Herramientas/audio/recortar_pausas.py` (también para voces propias, con Whisper).
- **Las tomas salen de la voz**: `Herramientas/audio/tomas_desde_voz.py` → `audio/tomas_voz.json` (los golpes ¡pum!/¡pop! caen en su palabra).
- **Efectos que coinciden con la escena** (nueva plantilla `Herramientas/audio/armar_video.py`: voz de corrido, `"palabra:pum"`, subtítulos automáticos de 1–2 palabras).
- **Caras por emoción cambiando la textura** de la cabeza (`Herramientas/blender/caras_textura.py` + `Herramientas/armar_secuencia_caras.py` para armar tus caras), nunca planos encima. Excepciones: caras de máscara, dinámicas o dibujadas (se anotan en `MI_CANAL.md`).
- **Render en paralelo** (`Herramientas/render_paralelo.py`): 2 Blender a la vez ≈ 1,6× más rápido. Claude pregunta antes.

**Herramientas y guías nuevas**
- **Rig automático** (`armar_rig_r15_auto.py`): centra, voltea, reconoce las 15 piezas R15 y pega accesorios; arregla cabezas dinámicas sin cara. La skill `poner-rig` ya lo usa.
- **Interiores para el Pueblo** (scripts en `Escenarios/Pueblo/scripts/`: `interiores.py`, `presidencia_interior.py`, `util_interiores.py`): 2 casas anchas con sala, comedor, cocina, escalera y cuartos; presidencia con vestíbulo, despacho del alcalde, cabildo, secretaría y torre del reloj. Se aplican sobre una **copia** del mapa (ver `docs/04_ESCENARIOS.md`).
- `objetos_cartoon.py` (burbujas de pensamiento, humo "¡pop!", nube que llueve, pan, elefante, sombrero, escoba, gato con cabeza que voltea, paraguas, linterna, cuaderno, monstruo desde un personaje) y `fotos_escenario.py`.
- Revisión: `hoja_contacto.py` + `componer_hoja.py` (hoja con todas las tomas) y `revisar_camaras.py` con varios personajes por toma (propiedad `sujeto`) y por tramos.
- `voz_elevenlabs.py --voz ID`: probar otra voz sin cambiar la del canal.
- Guía `docs/08_HISTORIAS.md`: historias con misterio, giro que no se adivine y narración con voz en cada escena.
- La plantilla vieja de `armar_video.py` (voz acomodada frase por frase) queda solo en EP001.

## v0.3.1 — 2026-11-06 — Segundo entrenamiento
- **ClusterK y Gelo con 5 videos cada uno** (confiabilidad media). Fórmulas, notas y `COMPARACION.md` actualizadas.
- ClusterK: tipos de giro (narrador engañado con montaje de pistas, golpe final), retos por rondas con cameo famoso, finales abiertos para parte 2.
- Gelo: alcalde villano que se aprovecha de la regla (5 de 5), monstruo incomprendido, "suscríbete" pegado al tema, protagonista a color contra el pueblo gris, carteles en la escena.

## v0.3.0 — 2026-11-06 — Skills y primer entrenamiento
- **Skills del kit** (`.claude/skills/`): `instalar-kit`, `poner-rig`, `analizar-videos`, `nuevo-episodio`, `rehacer-tramo`, `actualizar-kit`. Claude las usa solo al abrir la carpeta del kit.
- **Primer entrenamiento** (`Analizador/Estilos/`): fórmulas y notas de **ClusterK** y **Gelo** (3 videos cada uno, confiabilidad baja: se irán afinando) + `COMPARACION.md`.
- Analizador: subtítulos de una palabra bien contados; detector de partículas sin la franja de subtítulos ni el paralaje de zooms.
- README: instalación fácil con un prompt para Claude.

## v0.2.0 — 2026-11-06 — Carpetas claras, Analizador y rehacer tramos
- **Carpetas sin números**, más fáciles de entender: `Personajes/` (`Protagonista`, `Secundarios`, `Pueblo_NPC`, `Plantillas_Rigs`), `Caras/`, `Escenarios/`, `Episodios/`, `Analizador/`, `Herramientas/`, `Respaldos/`.
  Si tenías la v0.1.0 con cosas tuyas: mueve los videos de `00_Referencias` → `Analizador/Videos_para_analizar/<Creador>/`, `01_Personajes/1_Protagonista` → `Personajes/Protagonista` (igual secundarios, NPC y rigs), `05_Recursos/Caras` → `Caras`, `02_Escenarios` → `Escenarios`, `03_Episodios` → `Episodios`, `99_Archivo` → `Respaldos` (o pídeselo a Claude).
- **Analizador de videos v2** (`Analizador/`): cortes verificados, cámara, tipo de plano medido (cara/cuerpo), subtítulos por OCR, voz por GPU, sonido, historia, efectos candidatos, reporte HTML y fórmula por creador (`Analizador/Estilos/`). Reemplaza a `Herramientas/analisis/analizar_referencia.py`.
- **Rehacer solo un tramo** (`Herramientas/rehacer_tramo.py`): respalda, renderiza solo del segundo X al Y y vuelve a armar el video; `--deshacer` regresa la versión anterior.
- Personajes por nivel (protagonista, secundarios, NPC) con receta de rig, NPC con nombre confirmados por el usuario y caras por emoción.
- Mapas: el `Pueblo/` original no se modifica; copias y mapas nuevos van en su propia carpeta de `Escenarios/`. Los episodios anexan solo los personajes que salen.

## v0.1.0 — 2026-11-06 — Primera versión
- Escenario por defecto **Pueblo** (`Escenarios/Pueblo/`): calle con casas y cortinas animables, faroles, plaza con fuente, presidencia con reloj y podio, 4 tiendas, escuela con 2 salones y cancha, estanque, colinas. Incluye los scripts que lo construyen.
- Plantilla de episodio (`Episodios/_PLANTILLA_EPISODIO/`): guion con tabla de tomas, narración y checklist.
- Herramientas (`Herramientas/`): conexión a Blender (`bl.py`), revisión de cámaras, solver de poses de brazos, plantilla de rig R15, voz con ElevenLabs, armado de video (voz + efectos + subtítulos), análisis de videos de referencia.
- Guías en `docs/`: pipeline, 28 lecciones, personajes, escenarios, cámaras, audio y análisis de referencias.
- Archivos personales separados (`MI_CANAL.md`, `MI_BITACORA.md`, `mi_config.json`, personajes, episodios, referencias): las actualizaciones nunca los tocan.
- `instalar.py` + `requirements.txt` para preparar una PC nueva.
