# Kit de Animación Roblox — Contexto del proyecto

> Leer este archivo completo antes de trabajar. Es el "cerebro" del proyecto: qué hacemos, cómo, dónde está cada cosa y qué errores ya resolvimos.
> Después leer **`MI_CANAL.md`** (configuración personal: protagonista, reparto con niveles A/B/C, voz, estado y pendientes del canal). Nunca elegir personajes al azar: usar el reparto. Si no existe, correr `py instalar.py` o crearlo a partir de `MI_CANAL.ejemplo.md` preguntando al usuario.
> Las rutas propias de cada PC (Blender, efectos, voz) están en **`mi_config.json`** y los scripts las leen con `Herramientas/config.py`. Nunca escribir rutas fijas de una PC en archivos compartidos.
> Proyecto en etapa temprana (inicio: noviembre 2026). Se mejora poco a poco: cuando algo falle o se aprenda algo nuevo, actualizar la documentación (ver sección 8 para saber dónde).

## 1. Qué es

Sistema para hacer **animaciones 3D estilo Roblox en Blender con Claude** (mediante scripts de Python), en formato **Short vertical 9:16**, para canales de YouTube.
- El usuario (dueño del canal) dirige: ideas, historia, personajes, aprobación de cada etapa.
- Claude construye: escenarios, rigs, animación, cámaras, revisión, voz (ElevenLabs), subtítulos, efectos y render.
- Cada video es un **episodio** dentro de `Episodios/`. Los personajes y escenarios se reutilizan entre episodios.
- Este sistema existe para **ahorrar horas** y no repetir errores.

### Hoja de ruta del kit
1. **Base** (hecho): el **Pueblo** como escenario por defecto + flujo completo probado con un episodio de 30 s.
2. **Biblioteca de personajes** (en curso): `Personajes/` por nivel — protagonista, secundarios y gente del pueblo. Todos con el mismo esqueleto R15, rig armado por Claude con una receta probada.
3. **Análisis de referencias**: medir fotograma por fotograma videos de creadores exitosos (ritmo de cortes, zooms, planos, transiciones) y convertirlo en **recetas de cámara** → `docs/07_ANALISIS_REFERENCIAS.md`. Las buenas tomas son el principal enganche.
4. **Plantilla de animación** reutilizable (trayectorias, ciclos, poses, cámaras por receta).
5. Nuevos escenarios e historias.

## 2. Reglas de trabajo (obligatorias)

- Responder en **español latinoamericano**, breve y directo; explicar solo lo necesario (el usuario está aprendiendo).
- **No publicar nada** (YouTube, GitHub, redes) ni hacer acciones irreversibles sin autorización explícita.
- Pedir confirmación antes de: gastar créditos (ElevenLabs), renders largos (> 15 min), borrar o sobrescribir archivos del usuario.
- **Nunca** pedir ni usar claves pegadas en el chat. Las claves van en variables de entorno de Windows (sección 5). Si el usuario pega una, no usarla y recomendarle revocarla.
- Mostrar avances con imágenes (fotogramas de prueba) antes de renderizar todo.

## 3. Estructura de carpetas

```
(raíz del kit)/
├── CLAUDE.md                  ← este archivo (compartido)
├── README.md                  ← instalación y uso para personas
├── instalar.py                ← revisa requisitos y crea los archivos personales
├── .claude/skills/            ← compartido: skills del kit (instalar-kit, poner-rig, analizar-videos, nuevo-episodio, rehacer-tramo, actualizar-kit)
├── MI_CANAL.md                ← PERSONAL: canal, reparto, voz, estado y pendientes
├── MI_BITACORA.md             ← PERSONAL: historial de sesiones de este usuario
├── mi_config.json             ← PERSONAL: rutas de esta PC
├── docs/
│   ├── 01_PIPELINE.md         ← paso a paso para producir un episodio (checklist)
│   ├── 02_LECCIONES.md        ← errores encontrados y su solución (LEER antes de animar)
│   ├── 03_PERSONAJES.md       ← rigs, ejes de huesos, poses y ciclos
│   ├── 04_ESCENARIOS.md       ← mapa y coordenadas del Pueblo (alturas de piso, objetos)
│   ├── 05_CAMARAS_Y_TOMAS.md  ← tipos de toma, transiciones, revisión de cámaras
│   ├── 06_AUDIO_VOZ_SUBS.md   ← ElevenLabs, subtítulos, efectos, mezcla
│   ├── 07_ANALISIS_REFERENCIAS.md ← cómo medir patrones de cámara de otros creadores
│   ├── 08_HISTORIAS.md        ← cómo escribir historias con misterio y giro que no se adivine
│   ├── 09_RECETA_SIMPLE.md    ← animar simple como Custerk/Gelo (tipos de toma, cámara, qué no animar)
│   ├── 10_CATALOGO.md         ← PERSONAL (lo crea `instalar.py` / `Herramientas/catalogo.py`): lo que ya existe en esta PC (objetos, efectos, gestos, caras, personajes, lugares)
│   ├── CAMBIOS.md             ← versiones del kit (qué trae cada actualización)
│   └── IDEAS.md               ← mejoras pendientes del kit
├── Personajes/                ← biblioteca de personajes (ver Personajes/LEEME.md)
│   ├── Protagonista/          ← PERSONAL: el personaje principal del canal (nivel A)
│   ├── Secundarios/           ← PERSONAL: familia, amigos, autoridades (nivel B)
│   ├── Pueblo_NPC/            ← PERSONAL: gente genérica de fondo (nivel C)
│   └── Plantillas_Rigs/       ← PERSONAL: Roblox Starter Rigs (no redistribuir)
├── Caras/                     ← PERSONAL: PNG por emoción (feliz.png, enojado.png…) + paquetes
├── Escenarios/                ← mapas, uno por carpeta
│   ├── Pueblo/                ← compartido: mapa original del kit (.blend + scripts). No se modifica
│   └── <OtroMapa>/            ← PERSONAL: copias modificadas (Pueblo_v2, Pueblo_Noche) o mapas nuevos (Medieval)
├── Episodios/
│   ├── _PLANTILLA_EPISODIO/   ← compartido: copiar para cada episodio nuevo
│   └── EP###_Titulo/          ← PERSONAL: .blend, guion, narración, audio, renders, scripts
├── Analizador/                ← estudia videos de otros creadores y saca su fórmula (ver Analizador/LEEME.md)
│   ├── Videos_para_analizar/<Creador>/  ← PERSONAL: los videos que sube el usuario
│   ├── Resultados/            ← PERSONAL: reportes, hojas de contacto, notas por video
│   ├── Estilos/               ← compartido: fórmula de cada creador (.json + _formula.md + _notas.md)
│   └── motor/                 ← compartido: el código del analizador
├── Herramientas/              ← compartido: scripts reutilizables + config.py
└── Respaldos/                 ← PERSONAL: versiones viejas y respaldos (nada se borra)
```

**PERSONAL** = está en `.gitignore`: git nunca lo sube ni lo toca al actualizar. En el repositorio esas carpetas vienen vacías, solo con un `LEEME.md` que dice qué va ahí.
Nombres: episodios `EP001_Titulo_Corto`, cámaras `CR_Cam_S#_Nombre`, marcadores `CR_S#_Nombre`.

### Mapas y episodios (Blender ligero)
- Cada mapa vive en su carpeta de `Escenarios/` con su `<Mapa>_set.blend` limpio (sin personajes ni cámaras de episodio).
- **Nunca modificar el original** (`Escenarios/Pueblo/`). Para cambiarlo: copiar la carpeta como `Escenarios/Pueblo_v2/` (o el nombre que diga el usuario) y trabajar ahí. Mapas nuevos (ej. `Medieval/`) se construyen con scripts guardados en su carpeta `scripts/`.
- **Episodio nuevo**: crear el `.blend` del episodio a partir del mapa elegido y **anexar (append)** solo los personajes que salen, desde sus `<Nombre>_R15_Rig.blend` ya rigueados. Así cada episodio carga solo lo necesario y cambiar de mapa no obliga a rehacer personajes.

### Personajes (detalle en `docs/03_PERSONAJES.md`)
- **"Ya subí a X, ponle su rig"** → seguir la *Receta* de `docs/03_PERSONAJES.md` directo y sin explicaciones largas; no borrar lo que subió el usuario; responder corto con la ruta del `.blend` y una foto.
- Usar siempre el reparto de `MI_CANAL.md`: nivel A más tiempo y primeros planos, B cuando la historia lo pide, C de fondo (salvo que el usuario pida enfocar a alguien).
- **NPC con nombre** (ej. "Valentina, la vecina"): reutilizar el modelo registrado en `MI_CANAL.md`; si es nuevo, proponer uno con foto de frente ("¿Quieres que esta sea Valentina?") y registrarlo solo cuando el usuario confirme.
- **"Esta es mi hermana, ponle rig"** → `Secundarios/<Nombre>/`, nivel B en el reparto (igual para cualquier personaje que el usuario quiera subir de nivel).
- Caras: `<personaje>/caras/` o `Caras/`; elegir la emoción según el guion.

## 4. Formato estándar del video

| Parámetro | Valor |
|---|---|
| Resolución | **1080×1920 (9:16)**, 30 fps |
| Duración típica | 25–35 s (Short) |
| Motor | Eevee (Blender 5.2), ray tracing on, shadow pool 1024 |
| Vista previa | 50 % resolución, 16 muestras (≈1 s/fotograma) |
| Final | 100 %, 32–64 muestras (≈4–6 s/fotograma → ~1 h por 30 s) |
| Color | View transform **Standard** (colores planos tipo Roblox), colores sRGB → lineal |
| Audio | voz −1 dB, efectos suaves, loudnorm −14 LUFS, AAC 256k |
| Subtítulos | 1–3 palabras, 1 línea, abajo al centro (≈79 % de altura), Arial Black 92, contorno negro, palabras clave en amarillo, sin comillas ni signos |
| Fotogramas | `EP###/renders/<preview|final>/fotogramas/c_0001.png …` (los lee `armar_video.py`) |

## 5. Herramientas

- **Blender 5.2**: ruta en `mi_config.json` → `"blender"`.
- **Conexión a Blender abierto**: addon BlenderMCP (puerto en `mi_config.json`, normalmente 9876). Enviar código con `py Herramientas/blender/bl.py script.py`. El código se ejecuta en el Blender del usuario: **no bloquearlo con renders largos**.
- **Renders largos**: guardar copia (`save_as_mainfile(copy=True)`) y renderizar en segundo plano con `blender.exe -b copia.blend -a`.
- **FFmpeg** (en PATH, con libass) y **Python 3.11+** con los paquetes de `requirements.txt` (numpy, OpenCV, PySceneDetect, faster-whisper, matplotlib). `py instalar.py` revisa todo.
- **Storyboard animado (Three.js)**: **ya no se usa para animar** (decisión del usuario, 2026-11-08: en EP004 dejó a los personajes tiesos). Las historias nuevas se animan toma por toma como EP002, con `Herramientas/blender/actuar.py` (vida, gestos en su palabra, diálogos, golpes de cámara). Del storyboard solo viene en el kit su **motor de poses** (`Herramientas/storyboard/sb_blender.py` + `web/poses.json`), que usan `vida_suave`, `actuar` y `tomas_simples`; el storyboard del navegador no se usa ni se distribuye.
- **Analizador de video**: `py -X utf8 Analizador/motor/analizar.py` (GPU: PyTorch CUDA, Whisper, EasyOCR, CLIP, Grounding DINO; la primera vez descarga ~3 GB de modelos). Guía: `docs/07_ANALISIS_REFERENCIAS.md`.
- **ElevenLabs** (opcional): clave en la variable de entorno de usuario `ELEVENLABS_API_KEY`; id de la voz en `mi_config.json` → `"voz_narrador"`.
- **Efectos de sonido**: carpeta en `mi_config.json` → `"sfx"` (librerías CC0, p. ej. Kenney).
- **Roblox Studio MCP** (opcional): para exportar personajes o assets.
- **GitHub**: solo el mantenedor del kit sube cambios, y solo cuando lo pide (ver sección 8).

## 6. Flujo de trabajo (resumen — detalle en `docs/01_PIPELINE.md`)

1. **Idea y guion** (usuario + Claude) → copiar `Episodios/_PLANTILLA_EPISODIO` como `EP###_Titulo` → `GUION.md` + `narracion.txt` (**una línea = una toma**, voz continua sin huecos) → el usuario aprueba el texto.
   - **Sin storyboard** (decisión del usuario 2026-11-08). Con el guion aprobado y antes de la voz: **plano de construcción** (`PLANO.md` de la plantilla: lugares, personajes, objetos —de `docs/10_CATALOGO.md` o nuevos—, efectos, letreros y tabla de tomas); construir lo que falta. Animar con la **receta simple** (`docs/09_RECETA_SIMPLE.md`, `Herramientas/blender/tomas_simples.py`) y mostrar un **borrador MP4 con voz** antes de la vista previa.
2. **Voz primero, y el usuario la escucha y la aprueba** antes de animar. Cada quien usa **su propia voz**: la de su cuenta de ElevenLabs (`voz_elevenlabs.py EP###`, confirmar créditos; velocidad normal, sin acelerar) o una voz ya hecha que entregue (`--audio`). Luego `py Herramientas/audio/recortar_pausas.py EP###` (quita silencios largos sin cortar la voz, deja un respiro corto entre líneas y la escucha con Whisper: si una palabra no se oye completa, se corrige esa línea y se rehace sola con `voz_elevenlabs.py EP### --linea N`, confirmando créditos) → `py Herramientas/audio/tomas_desde_voz.py EP###` (cada toma empieza en su línea; fotograma de cada palabra en `audio/tomas_voz.json`).
3. **Personajes**: si es nuevo, rig automático (`armar_rig_r15_auto.py`, ver `docs/03_PERSONAJES.md`) y caras por textura si se puede.
4. **Escenario**: partir de `Escenarios/...` (agregar cosas con scripts, nunca a mano sin registrar).
5. **Animación** con script por episodio que lee `tomas_voz.json` (los golpes caen en su palabra) + cámaras por toma + caras por emoción.
6. **Revisión obligatoria**: `revisar_camaras.py` (obstrucciones/fuera de cuadro) + `revisar_ojos.py` (visera/cabello tapando los ojos) + `revisar_encuadre.py` (cabeza o gorro cortados, cara en el tercio de arriba) + `revisar_agarre.py` (objetos en la mano) + `revisar_objetos.py` (los objetos que dice la voz salen en cuadro, grandes, sin tapar y se distinguen de lo de atrás) + `detectar_superficies.py` (caras al ras que parpadean) + hoja de contacto de cada toma. Corregir antes de renderizar.
7. **Vista previa** (50 %): **preguntar** si quiere renderizar con 2 Blender en paralelo (`py Herramientas/render_paralelo.py EP### preview`, más rápido pero usa más memoria de video) → `armar_video.py EP### preview` (voz de corrido, subtítulos automáticos de 1–2 palabras, efectos que coinciden con lo que pasa) → el usuario aprueba.
8. **Render final** (100 %, `render_paralelo.py EP### final`) → `armar_video.py EP### final` → el usuario revisa. Publicar solo si lo pide.
9. **Todo se trabaja por toma** (una línea = una toma = una cámara): animación, render y sonido. **¿No le gustó una parte?** ("la toma 12" o "del segundo 10 al 15 cámbiale…"): cambiar solo eso en el `.blend`, guardar y `py Herramientas/rehacer_tramo.py EP### --toma 12` (o `EP### 10 15`; `--tomas` las lista) para la vista previa, o con `--final`. Nunca re-renderizar todo por un cambio parcial. Si el cambio mueve tiempos (dura más o menos), avisar: eso sí obliga a re-renderizar desde ese punto.
10. **Estilo de un creador** ("al estilo de ClusterK"): leer `Analizador/Estilos/<Creador>.json` + `_notas.md` antes del guion y la tabla de tomas (ver `docs/07_ANALISIS_REFERENCIAS.md`).

## 7. Reglas de oro (lo más importante de `docs/02_LECCIONES.md`)

1. **Revisar cámaras antes de renderizar**: nada debe tapar al personaje (salvo transiciones a propósito) y el personaje debe estar en cuadro.
2. **Que se entienda a quién seguimos**: tomas de dron a media altura sobre la calle mirando al personaje, no encima de las casas.
3. **Poses sin articulaciones exageradas**: las piernas R15 blocky se enciman al doblar mucho la rodilla; calcular poses midiendo posiciones (solver), no a ojo.
4. **Inclinar el cuerpo desde `UpperTorso`**, no desde `LowerTorso` (las piernas cuelgan de él).
5. Los **marcadores con cámara** cambian la cámara activa al renderizar: para fotos de prueba con otra cámara, desvincularlos temporalmente.
6. Correr con **movimiento de cuerpo** (brazos, torso, cadera, cabeza) y cámara de frente con temblor de lado a lado.
7. Efectos de sonido **pocos y con sentido**; la voz siempre manda.
8. Guardar el `.blend` del episodio en su carpeta y anotar en `MI_BITACORA.md` lo que se hizo.
9. **Shorts cortos y rápidos: la voz manda el ritmo.** **Cada escena lleva voz**: no quedan partes calladas. No se trata de más palabras: el video dura lo que dura la voz (si el guion es corto, el video es corto) y cada toma tiene su frase (1,5–2,5 s, corte en cada idea, cámaras que cambian rápido). Frases concretas ("no pienses en un elefante rosa, porque… ¡pop!"). La voz va a **velocidad normal** (no acelerarla: pierde la esencia del personaje) y con emoción; las pausas largas se recortan sin que se note y queda un **respiro corto** entre líneas (0,3–0,5 s, nunca 1 s o más) (`recortar_pausas.py`, que también revisa que se oiga cada palabra). Los golpes (¡pum!, ¡pop!) caen justo en su palabra y si queda un respiro corto (cambio de emoción) lo cubre un efecto que coincide con la escena, nunca silencio. Primero la voz (aprobada por el usuario), después la animación.
10. **Caras por emoción cambiando la textura** de la cabeza (`caras_textura.py`), nunca con planos encima: cada personaje cambia de cara según lo que pasa en cada toma. **Excepciones**: personajes con cara de máscara, dinámica o dibujada (ej. Crista "la payasita", Raul y Ajolota del mantenedor; el personaje de Yuyo con su máscara gigante): su cara no se toca, salvo que su dueño lo pida; sus emociones se cuentan con poses, efectos y sonido.
11. **Renders en paralelo**: preguntar al usuario si quiere 2 Blender a la vez (`render_paralelo.py`): ≈ 1,6× más rápido en una sola tarjeta, pero usa más memoria de video.
12. **Efectos de sonido que coinciden con la escena**: cada golpe en el momento exacto de la acción (`"palabra:pum"` en `armar_video.py`), pocos y siempre debajo de la voz.
13. **Calidad de cada toma** (checklist en `docs/05_CAMARAS_Y_TOMAS.md`): comer y agarrar de verdad (objeto en la boca o en la palma, migas), caras encuadradas completas en el tercio superior, nada tapa a quien está en foco, cámara siempre viva con sentido, ambiente (polvo, brillitos, líneas de velocidad), cuerpo con sentido (atravesar un mueble está bien, subirse encima no), textos pegados a su objeto y legibles en 9:16.
14. **Simple no es congelado** (EP005, 2026-11-09): con poses fijas el usuario lo vio «tieso, cutre». Siempre **vida suave** (`Herramientas/blender/vida_suave.py`; por defecto en `tomas_simples.armar`): respirar, cabeza, peso, brazos + un gesto en la palabra clave + asentir al hablar. Lento y de pocos grados.

## 8. Actualizar el kit sin borrar nada del usuario

`MI_CANAL.md` indica el **rol** de este usuario: `mantenedor` (dueño del kit) o `usuario` (lo usa).

**Siempre:**
- Lo PERSONAL (sección 3) nunca se sube, se mueve ni se borra para "actualizar". Antes de un cambio que toque archivos del usuario, preguntar.
- No modificar los archivos compartidos para cosas de un solo canal: mapas propios o modificados → copiar el escenario a `Escenarios/<Nombre>/`; personajes → `Personajes/<nivel>/`; caras → `Caras/`; ideas, reparto y estado → `MI_CANAL.md`; historial → `MI_BITACORA.md`.
- Nunca usar `git reset --hard`, `git checkout -- .`, `git clean` ni `git push --force`.

**Si el rol es `usuario`** (recibe actualizaciones):
- Para actualizar: `git pull`. Si git avisa que hay cambios locales en archivos compartidos, **no forzar**: copiar esos archivos a `Respaldos/respaldo_<fecha>/`, explicarle al usuario y preguntar antes de seguir.
- Lecciones nuevas que aprenda → `MI_LECCIONES.md` (personal) y sugerir enviarlas al mantenedor.

**Si el rol es `mantenedor`:**
- Las lecciones y mejoras generales sí van a `docs/` y `Herramientas/`.
- **Subir al repositorio solo cuando el usuario lo diga** ("sube la actualización"). Antes: revisar `git status` (que no vaya nada personal, claves ni material con licencia), anotar la versión en `docs/CAMBIOS.md` y pedir confirmación.
- No renombrar ni mover archivos compartidos sin necesidad (rompe las copias de los demás); si es necesario, avisarlo en `docs/CAMBIOS.md`.
- **Antes de cada subida, probar como si fuera un amigo** (el repositorio es público): clonar en una carpeta temporal, correr `py instalar.py`, compilar todos los `.py`, correr el analizador vacío y confirmar que `git status` del clon queda limpio. Si algo falla, no se sube.
- **Subir el entrenamiento** (fórmulas de `Analizador/Estilos/`): solo `<Creador>.json`, `_formula.md`, `_notas.md` y `COMPARACION.md` (nunca `Nosotros*`, videos, resultados ni imágenes). Son archivos nuevos o que solo crecen, así que un `git pull` de los amigos no choca con nada suyo.

## 9. Estado

- Estado del canal, personajes listos y pendientes: **`MI_CANAL.md`**.
- Versión del kit y novedades: `docs/CAMBIOS.md`. Mejoras pendientes del kit: `docs/IDEAS.md`.
