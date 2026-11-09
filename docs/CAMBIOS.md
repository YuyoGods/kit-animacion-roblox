# Cambios del kit

> Una entrada por cada actualización que se sube al repositorio (lo más nuevo arriba).
> Si una actualización renombra o mueve archivos compartidos, avisarlo aquí.

## v0.5.0 — 2026-11-09 — Planear antes de animar (y nada tieso)
**Cómo trabaja Claude un episodio ahora** (`CLAUDE.md`, skill `nuevo-episodio`, `docs/01_PIPELINE.md`). Es lo aprendido en EP004 y EP005 y en el entrenamiento con 172 videos:
1. **Guion desde el título** con la estructura medida (`docs/08_HISTORIAS.md`):
   - «En este pueblo, …» con la regla completa a los ~4 s.
   - Frases de 6–7 palabras, ~2:05 de duración.
   - El «suscríbete» amarrado a la regla.
   - Checklist para niños de 5 a 9 años.
2. **Plano de construcción antes de la voz** (`Episodios/_PLANTILLA_EPISODIO/PLANO.md`):
   - Contiene lugares, personajes, objetos, efectos, letreros y la tabla de tomas.
   - Primero se revisa el **catálogo** de lo que ya existe (`docs/10_CATALOGO.md`). Es personal: lo crea `instalar.py` en cada PC con `Herramientas/catalogo.py`.
   - Se construye solo lo que falta y se muestran fotos.
3. **Receta simple** (`docs/09_RECETA_SIMPLE.md` + `Herramientas/blender/tomas_simples.py`):
   - 5 tipos de toma, cámara fija o con acercamiento lento, una frase = una toma.
   - La energía son los **cortes**: 37–42 por minuto y un corte en los primeros 3 s.
4. **Nada tieso** (regla de oro 14):
   - `Herramientas/blender/vida_suave.py` suma respiración, cabeza, peso, brazos y un gesto en la palabra clave. Viene activado por defecto en `tomas_simples`.
   - `actuar.py` sirve para actuar toma por toma.
5. **Revisión antes de renderizar** (regla de oro 13, checklist «Calidad de cada toma» en `docs/05`):
   - `revisar_encuadre.py`, `revisar_ojos.py`, `revisar_agarre.py`, `revisar_objetos.py`, `revisar_pies.py` y `detectar_superficies.py`.
   - Después, un **borrador MP4 con voz** (cuadros salteados, baja calidad) y hojas por toma para revisar cada fotograma. Al final, la vista previa.
- **Lecciones 37–79** en `docs/02_LECCIONES.md`. Algunas: espejo de verdad, cobija que tapa sin atravesar, beso que sí se note, cámara pegada detrás de alguien, simple ≠ congelado y onomatopeyas que Whisper no escribe.

**Entrenamiento** (`Analizador/Estilos/`):
- **Custerk** (76 videos) y **Gelo** (96 videos), los dos con confiabilidad alta: fórmula, notas y `COMPARACION.md`.
- Ellos casi no mueven la cámara: la energía son los cortes. Lo único que va con más vistas en los dos creadores es **cortar en los primeros 3 s**.

**Para construir escenas**:
- `muebles_cartoon.py` (nuevo): camas con cobija de tela, tocador con foquitos, espejo de cuerpo completo, repisas, peluches, cocina, sala y comedor, entre otros.
- `Herramientas/texturas_tela.py` (nuevo): telas y papel tapiz con estampado propio (estrellas, corazones y gatitas kawaii **originales**, sin personajes con dueño).
- `objetos_cartoon.py`: mochila que se abre, carta, gorra, candado, camita y platito de gato, tenedor, peluche, pastel, globo, billete y galleta de la fortuna.
- `vfx.py`: cambio de cuerpo (almas de luz), sonrojo, líneas de impacto, fuego y humo de caricatura, y un gato con vida que come con tenedor.
- Caras:
  - `caras_atlas.py`: cabezas dinámicas.
  - `caras_npc.py`: reemplaza la cara clásica « : ) ».
  - `bocas_hablar.py`: lip-sync sencillo.
  - `mirada_lateral.py`: ojos hacia un lado.
- Carteles con detalle de caricatura: `carteles.py`.
- Para estudiar videos: `fotogramas_ref.py` y `comparar_videos.py`.

**Voz**:
- `tomas_desde_voz.py`: las onomatopeyas que Whisper no escribe (como «¡Miau!») toman el tiempo de su sonido, así los golpes y el subtítulo caen en su momento.

- **El storyboard del navegador se quitó del kit**: dejaba a los personajes tiesos (EP004). Solo queda su **motor de poses**, `Herramientas/storyboard/sb_blender.py` + `web/poses.json` (ángulos «de persona» → huesos, ciclos de caminar y correr, piso real). Lo usan `vida_suave`, `actuar` y `tomas_simples`.
- `recortar_pausas.py` ahora **escucha** la voz: mide la energía y solo quita silencio real (nunca un pedazo de palabra), deja un **respiro corto** entre líneas (0,3–0,4 s; 0,41–0,55 s después de "…") y al final la oye con Whisper y avisa si alguna palabra no se oye completa. También guarda `audio/voz_escuchar.mp3` para oírla.
- Arreglado: los tiempos de las palabras se atrasaban hasta 0,18 s al final de la voz (golpes y subtítulos caían tarde). Si ya recortaste una voz con la v0.4.1, vuelve a correr `recortar_pausas.py` y `tomas_desde_voz.py`.
- `voz_elevenlabs.py --linea N` (o `--linea 24-26` si la voz dice esas líneas pegadas): rehace solo esa parte (gasta solo sus créditos) y la pega en la voz con la misma voz, ajustes y el volumen de las líneas vecinas; `--simular` lo prueba sin gastar y `--reusar` vuelve a pegar la línea ya pedida sin pagar otra vez. La voz anterior se guarda sola en `Respaldos/`.
- `revisar_voz.py` (nuevo, lo corre solo el recorte): revisa la voz como una persona con Whisper y medidas, y marca con su segundo palabras de más o poco claras, sonidos inventados, líneas atropelladas o fuera de volumen.
- `recortar_pausas.py` empareja el volumen de las líneas (ElevenLabs a veces susurra una) y pega el inicio de cada palabra a donde de verdad empieza el sonido (cortes de toma más exactos).
- Subtítulos sin comillas ni signos (. , ! ¡ ? ¿) en la plantilla `armar_video.py`.
- `cielo.py` (nuevo): cielo decorativo para cualquier mapa, de día azul con nubes y un sol blanco con brillo suave, de noche con estrellas. Solo lo ve la cámara (la luz del mapa no cambia) y pasa solo a noche cuando el mapa se oscurece. Ver `docs/04_ESCENARIOS.md`.
- `voz_elevenlabs.py --agregar`: genera solo las líneas nuevas del final (ej. el bloque 2) y las pega a la voz ya aprobada, sin rehacerla. Al rehacer una voz completa usa la misma voz del episodio.
- Regla nueva: no usar "..." en la narración para ElevenLabs (se come finales, mete sonidos o junta palabras); usar coma o punto. `recortar_pausas.py` también mete el respiro donde la voz junta dos líneas pero baja casi a silencio.
- **Exportar personajes de Roblox Studio en lote** (`Herramientas/roblox/`, nuevo): Claude aísla cada personaje, lo exporta a `.obj` con el menú de Studio y crea su `partes.json` (nombres reales de las piezas). Guía: `Herramientas/roblox/LEEME.md`.
- `armar_rig_r15_auto.py`: la **ropa en capas** (chamarras, mangas, calentadores) ahora se deforma con los huesos; lee `partes.json` (reconoce niñas, cuerpos angostos y piezas que faltan); 3er dato opcional `voltear` / `no_voltear` cuando la detección de giro falla.
- **Trabajo por toma**: `rehacer_tramo.py EP### --toma 12` (o `12-14`) rehace solo esa toma (cámara) y vuelve a mezclar el sonido; `--tomas` lista las tomas con sus segundos.
- `objetos_cartoon.galleta_fortuna()`: galleta de la fortuna cerrada o abierta (dos mitades y el papelito con el texto que quieras).
- `extras_npc.py` (nuevo): gente de fondo con poses (atender, sentados platicando, fila, comprar, saludar) y `platica(a, b, f0, f1)`: dos personajes platicando con movimiento natural (se turnan, asienten, gesticulan, respiran).
- `vfx.py` (nuevo): efectos rápidos que no tapan la cara: `migas`, `brillitos` (con hueco para no tapar un texto), `corazones` de línea delgada, `confeti` y `abrir_galleta` (la galleta se parte con ¡crac!, migas y brillitos).
- `fotos_escenario.py`: `"props"` por vista (por ejemplo prender las luces del parque) y la noche ahora oscurece el fondo correcto (el cielo decorativo pasa a estrellas).
- Arreglado: `hoja_contacto.py` y `fotos_escenario.py` guardaban las fotos en `C:\Episodios\…` si se les daba una carpeta relativa (Blender toma esas rutas desde la raíz del disco); ahora usan la ruta completa.

## v0.4.1 — 2026-11-06 — Voz de corrido
- `recortar_pausas.py` deja pausas de máximo 0,15 s entre palabras y 0,25 s después de "…": la voz se oye hablando de corrido, a velocidad normal.

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
