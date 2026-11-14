# 06 — Voz, subtítulos, efectos y mezcla

## Voz (ElevenLabs)
- Script: `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo` → lee `EP###/narracion.txt`, guarda en `EP###/audio/`. La voz sale de `mi_config.json` → `voz_narrador`.
- Clave: variable de entorno de usuario `ELEVENLABS_API_KEY` (el script la lee de Windows; nunca se imprime). Para crearla (la pone el usuario):
  `[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", "CLAVE", "User")`
- Voz: la de `MI_CANAL.md` / `mi_config.json`. Modelo **`eleven_v4`** (desde EP006; antes `eleven_multilingual_v2`), stability 0,4 · similarity 0,75 · style 0,3 · speaker boost.
- Probar otra voz sin cambiar la del canal: `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo --voz ID_DE_LA_VOZ`.
- **Velocidad normal**: no acelerar la voz (con `--velocidad` el personaje pierde su esencia). Que suene con emoción.
- **Voz propia** (grabada o creada en otra cuenta/app): ponerla en `audio/` y usar `recortar_pausas.py EP### --audio su_voz.mp3` (saca los tiempos de cada palabra con Whisper).
- **Recortar pausas**: `py Herramientas/audio/recortar_pausas.py EP###` deja `audio/voz.wav` (y `voz_escuchar.mp3` para oírla) hablando de corrido **con un respiro corto**: hasta 0,10 s entre palabras, 0,12 s en comas, ~0,14 s al final de cada línea o frase y 0,2 s después de "…": **el narrador siempre activo, sin huecos** (EP006: con 0,3–0,4 s entre líneas EP005 se sentía lento; el usuario eligió 0,14 s al comparar dos versiones). **Mide la energía del audio**: solo quita silencio real, nunca un pedazo de palabra (lo comprueba antes de guardar), y alarga un poco los fines de frase demasiado pegados. Si la voz dice dos líneas sin silencio entre ellas, se quedan así. `--detalle` muestra cada pausa.
- **Volumen parejo** (solo, al recortar): si una línea suena mucho más suave o fuerte que las demás (ElevenLabs a veces susurra una), la acerca a ±2,5 dB del resto; los cambios caen en la pausa entre líneas. `--sin_nivelar` lo apaga.
- **Revisión de la voz** (`py Herramientas/audio/revisar_voz.py EP###`, la corre sola el recorte): la "oye" con Whisper, la compara con `narracion.txt` y la mide. Avisa con su segundo: palabra que no se oye, cortada o distinta; palabra o sonido **de más** (ej. un "¡oh!" inventado); palabra poco clara; línea atropellada o muy lenta; palabra estirada; volumen fuera de lugar; saturación. No marca diferencias de pura escritura de nombres ("Siquelpa" = "Sikelpa"). Deja `audio/revision_voz.json`. El usuario escucha esos segundos antes y después.
- Endpoint con tiempos: `/v1/text-to-speech/{voz}/with-timestamps` → MP3 + tiempo de cada letra (`narracion_tiempos.json`).
- Escribir con comas, puntos y dos puntos para las pausas y "¡!" para emoción. Generar todo el texto en una sola llamada (suena continuo).
- **No usar "..." con ElevenLabs**: a veces se come el final de la palabra, mete sonidos que no están en el guion o junta palabras (EP002: "calientito..." sonó "calientí"; "fuerzas..." metió un "¡oh!"; "escoba..." sonó "escóbatas"). Mejor coma o punto: el respiro y el suspenso los pone `recortar_pausas.py`.
- **Rehacer solo una línea** (una palabra que no se oye bien): corregir esa línea en `narracion.txt` y `py Herramientas/audio/voz_elevenlabs.py EP### --linea N` (si la voz dice esa línea pegada a la siguiente, se rehacen juntas: `--linea 24-26`) (misma voz y ajustes, con las líneas de antes y después como contexto para que suene igual; gasta solo los créditos de esa línea; la voz anterior queda en `Respaldos/`). La línea nueva se iguala al volumen de las líneas vecinas (pedida sola puede salir mucho más fuerte: en EP002, +9 dB). Probar sin gastar créditos: `--simular`; volver a pegar la línea ya pedida sin pagar otra vez: `--reusar`. Después, recortar otra vez.
- **Agregar un bloque nuevo sin rehacer la voz aprobada** (episodios largos, por bloques): poner las líneas nuevas al final de `narracion.txt` y `py Herramientas/audio/voz_elevenlabs.py EP### --agregar`. Genera solo las líneas nuevas (con las últimas como contexto y el mismo volumen) y las pega al final; lo pedido queda guardado en `Respaldos/.../agregadas.json` para volver a pegarlo sin pagar con `--respuesta`. Al rehacer una voz completa se usa la misma voz del episodio (`audio/narracion_info.json`).
- **Agregar líneas al PRINCIPIO** (un gancho de adelanto, EP011): ponerlas arriba en `narracion.txt` y `voz_elevenlabs.py EP### --anteponer` (solo cobra esas líneas y las pega antes de la voz aprobada). Luego `recortar_pausas.py` y `tomas_desde_voz.py`: todas las tomas se recorren. Para no re-animar, `EP011/scripts/recorrer_tiempos_ep011.py VIEJO.json OFS` mueve todas las llaves y marcadores del `.blend` a los tiempos nuevos (lección 109).
- **Confirmar con el usuario antes de gastar créditos.**

## Acomodar la voz al video
- **Lo normal ahora es al revés: el video se acomoda a la voz** (`tomas_desde_voz.py`). La voz va completa y de corrido, sin huecos; lo de abajo solo sirve para videos animados antes de tener voz.
- Medir inicio/fin de cada frase (tiempos por letra) y compararlo con el inicio de su toma.
- Mover cada frase (`NEW_START` en `armar_video.py`) para que la acción coincida (ej. "tocó la puerta" con los golpes).
- Si la última frase no cabe, **alargar la última toma** (sostener el primer plano).
- Si una frase no cabe en su toma (EP002: la del pan), **partirla en pedazos donde la voz hace pausa** y acercarlos (dejar ≥ 0,1 s entre pedazos); recortar pausas dramáticas largas a ~0,3 s. No acelerar la voz.
- Si una palabra debe caer con un golpe visual ("¡pum!", "elefante"), mover el evento de la animación al tiempo de la palabra y rehacer solo esa toma con `rehacer_tramo.py`.
- `armar_video.py` imprime dónde se oye cada frase y avisa **SIN PAUSA** si dos frases quedan pegadas.

## Subtítulos (ASS quemado con FFmpeg/libass)
- **Estilo "custerk" (por defecto desde 2026-11-12, pedido del usuario)**: `Herramientas/audio/subtitulos_estilo.py`, lo usa la plantilla `armar_video.py` (`ESTILO_SUBS = "custerk"`). Copia medida cuadro a cuadro de los subtítulos NUEVOS de Custerk (estrenados en su Short más reciente, 12-nov; sus otros 22 videos del 9 al 12-nov siguen en minúsculas): **una palabra a la vez, EN MAYÚSCULAS**, letra **Montserrat Black** (la de CapCut; el script la encuentra sola en Roblox o CapCut y la pasa a FFmpeg con `fontsdir`; si no está, Arial Black), relleno con **degradado suave** (no es blanco puro: #FAFBFF arriba → #E9ECF5 abajo; las palabras clave y los números en dorado #FDE181 → #FEB527 → #FDA014; hecho con 6 capas recortadas porque ASS no tiene degradados), contorno negro 11 y **sombra 3D** hacia abajo (7 px), **entrada pop con rebote** (48 → 72 → 96 → 119 → 114 → 110 → 105 → 100 % por cuadro; Custerk: 48, 68, 93, 120, 113, 107, 102, 100), centrada a **≈69 % de la altura** (Custerk 69,2 %, dentro de la zona segura de Shorts). "CONTADOS" mide 575 px en reposo (Custerk ~580); las palabras largas se achican solas para caber en 770 px. Comparación: `Analizador/Resultados/CuadroACuadro/demo_subtitulos/`.
- `ESTILO_SUBS = "custerk_viejo"` = sus subtítulos hasta el 9-nov (minúsculas, entrada sutil 94 → 100 %, palabra clave en rojo). `ESTILO_SUBS = "clasico"` = el nuestro de antes: 1–2 palabras en minúsculas, ≈79 % de la altura, Arial Black 96, entrada 118 % → 100 % en 90 ms.
- Siempre **una sola línea** y **sin comillas ni signos** (. , ! ¡ ? ¿ : ;): `"no pienses…"` sale `NO` `PIENSES`.
- Tiempos: cada subtítulo aparece 0,03 s antes de su palabra y dura hasta el siguiente (los huecos cortos se llenan).
- Ojo con el encuadre: a 69 % el subtítulo cae sobre el pecho del personaje (como en Custerk). Si el objeto clave de una toma queda a esa altura, subirlo en el cuadro (o alejar un poco la cámara). Con FFmpeg a mano: `subtitles=subtitulos.ass:fontsdir=_fuentes` (corriendo desde la carpeta `audio/`; `subtitulos_estilo.filtro()` copia la letra ahí).

## Efectos (pocos y con sentido)
- **Que duren SOLO lo que dura su acción** (pedido del usuario 2026-11-11, "muy importante"): muchos clips de la librería duran 5–6 s (`typing`, `tick`, `reverse_swell`; `sub_drop` 4,7 s). Antes de usar uno, medir cuánto dura (`ffprobe`). `armar_video.py` corta cada efecto con un fade corto al terminar la toma donde empieza, y un 5.º dato lo acorta más: segundos (`0.6`) o `"hasta:palabra:una"`. Lo que depende de la animación, como el tecleo de una burbuja, va en `audio/efectos_animacion.json` (`{"tipo": "tecleo", "f0", "f1"}`) y suena solo mientras salen las letras. Nunca un sonido que siga después del corte.
- **Que coincidan con lo que pasa**: cada golpe en el momento exacto de la acción (en `armar_video.py`: `("palabra:pum", "pop", 5, -3)` cae con la palabra; `"toma:6"` al empezar la toma 6). Si hay un respiro sin voz, lo llena un efecto acorde (cambio de emoción), nunca silencio.
- **Onomatopeyas que hace el efecto** ("¡Dong!"): ElevenLabs las lee como inglés. `CALLAR = {"dong"}` en `armar_video.py` las silencia en la voz y las quita de los subtítulos; mejor no escribirlas en `narracion.txt` (lección 68).
- **Ambiente**: poco y que coincida con la escena (ej. grillos bajitos de noche: `night_ambience`, −22 dB). El viento constante cansa: no ponerlo por defecto (cada canal anota sus gustos en `MI_CANAL.md`).
- **Sonidos que cansaron al público** (canal del mantenedor, EP004–EP009): nada de viento (`wind`) de día, nada de aplausos ni multitud (`applause`, `cheer`: el festejo se ve en la animación y lo cubre la música) y nada de ladridos (`dog_bark`: se repetía mucho y no era agradable). Si un respiro necesita sonido, uno suave que coincida con la escena.
Biblioteca: la carpeta de `mi_config.json` → `sfx` (CC0, organizada por carpetas como Kenney/OpenGameArt). Los nombres de abajo son los del ejemplo EP001; con otra librería, cambiarlos en `armar_video.py`.
| Uso | Archivo | Nivel |
|---|---|---|
| Ambiente de pueblo | `wind/sfx.wind.02.ogg` (en bucle) | −27 dB |
| Pasos (sincronizados a `eventos.json`) | `footstep/sfx.footstep.07-09.ogg` (concreto) | −21 caminar / −17 correr |
| Ropa al agacharse | `swish/sfx.swish.02.ogg` | −16 dB |
| Transición poste | `reverse_swell.02` + `swish.06` | −11 / −6 dB |
| Golpes en puerta | `gavel/sfx.gavel.01-03.ogg` | −7 dB |
| Tensión final | `tension_drone.02` (4 s con fades) + `sub_drop.01` | −22 / −14 dB |
Ducking: los efectos bajan hasta 55 % mientras habla la voz.

## Música de fondo (de principio a fin)
- Canción en `mi_config.json` → `"musica_fondo"`. Puede ser una ruta relativa a la raíz, como `Musica/cancion.mp3`; la carpeta `Musica/` es personal y no se sube. `Herramientas/audio/musica_fondo.py` la pone desde el primer cuadro hasta el último:
  - si es más larga que el video, **se recorta al final del video** con una salida de 1,5 s, para que no quede pantalla negra con música;
  - si es más corta, se repite.
- **Volumen**: `"musica_fondo_db"` dB por debajo de la voz (por defecto −16, medido donde habla el narrador). Mientras habla baja unos 4 dB más y sube en los respiros: se oye de fondo y la voz manda. Más negativo = más bajita.
- Escuchar solo la mezcla, sin render: `py Episodios/EP###/scripts/armar_video.py EP### preview --solo-audio` → `audio/mezcla_escuchar.mp3`.
- Las copias viejas de `armar_video.py` en un episodio necesitan la llamada `mus = musica_fondo.pista(voz, DUR, SR, load)` antes de la mezcla (ver la plantilla).
- Promedios móviles de audio con suma acumulada, no con `np.convolve` de ventana grande: con 0,3 s a 48 kHz tardaba más de 5 minutos.

## Mezcla y exportación
- `armar_video.py preview|final`: voz + efectos + música de fondo (numpy) → `loudnorm I=-14` → subtítulos → H.264 `-preset slow -crf 17`, AAC 256k, `+faststart`.
- Verificar: `ffmpeg -i video.mp4 -af ebur128 -f null -` (≈ −14/−15 LUFS) y fotos con subtítulos.

## Palabra estirada sin gastar créditos (2026-11-11, EP012)
Si `recortar_pausas.py` avisa que una palabra viene **estirada** ("detrás" de 0,72 s), no hay que rehacer la línea:
`py -X utf8 Herramientas/audio/acortar_palabra.py EP### <t0> <t1> [factor]` comprime solo el tramo estirado (casi siempre
la vocal, se ve en la envolvente) con `atempo` (mismo tono), une las orillas con un cruce de 8 ms, recorre los tiempos de
las palabras de después y respalda lo anterior en `Respaldos/`. Luego `tomas_desde_voz.py`. Whisper siguió oyendo la
palabra completa (0,54 → 0,40 s).

