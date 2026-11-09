# 06 — Voz, subtítulos, efectos y mezcla

## Voz (ElevenLabs)
- Script: `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo` → lee `EP###/narracion.txt`, guarda en `EP###/audio/`. La voz sale de `mi_config.json` → `voz_narrador`.
- Clave: variable de entorno de usuario `ELEVENLABS_API_KEY` (el script la lee de Windows; nunca se imprime). Para crearla (la pone el usuario):
  `[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", "CLAVE", "User")`
- Voz: la de `MI_CANAL.md` / `mi_config.json`. Modelo `eleven_multilingual_v2`, stability 0,4 · similarity 0,75 · style 0,3 · speaker boost.
- Probar otra voz sin cambiar la del canal: `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo --voz ID_DE_LA_VOZ`.
- **Velocidad normal**: no acelerar la voz (con `--velocidad` el personaje pierde su esencia). Que suene con emoción.
- **Voz propia** (grabada o creada en otra cuenta/app): ponerla en `audio/` y usar `recortar_pausas.py EP### --audio su_voz.mp3` (saca los tiempos de cada palabra con Whisper).
- **Recortar pausas**: `py Herramientas/audio/recortar_pausas.py EP###` deja `audio/voz.wav` (y `voz_escuchar.mp3` para oírla) hablando de corrido **con un respiro corto**: hasta 0,2 s entre palabras, 0,3 s en comas, 0,3–0,4 s al final de cada línea o frase y 0,41–0,55 s después de "…" (nunca 1 s o más). **Mide la energía del audio**: solo quita silencio real, nunca un pedazo de palabra (lo comprueba antes de guardar), y alarga un poco los fines de frase demasiado pegados. Si la voz dice dos líneas sin silencio entre ellas, se quedan así. `--detalle` muestra cada pausa.
- **Volumen parejo** (solo, al recortar): si una línea suena mucho más suave o fuerte que las demás (ElevenLabs a veces susurra una), la acerca a ±2,5 dB del resto; los cambios caen en la pausa entre líneas. `--sin_nivelar` lo apaga.
- **Revisión de la voz** (`py Herramientas/audio/revisar_voz.py EP###`, la corre sola el recorte): la "oye" con Whisper, la compara con `narracion.txt` y la mide. Avisa con su segundo: palabra que no se oye, cortada o distinta; palabra o sonido **de más** (ej. un "¡oh!" inventado); palabra poco clara; línea atropellada o muy lenta; palabra estirada; volumen fuera de lugar; saturación. No marca diferencias de pura escritura de nombres ("Siquelpa" = "Sikelpa"). Deja `audio/revision_voz.json`. El usuario escucha esos segundos antes y después.
- Endpoint con tiempos: `/v1/text-to-speech/{voz}/with-timestamps` → MP3 + tiempo de cada letra (`narracion_tiempos.json`).
- Escribir con comas, puntos y dos puntos para las pausas y "¡!" para emoción. Generar todo el texto en una sola llamada (suena continuo).
- **No usar "..." con ElevenLabs**: a veces se come el final de la palabra, mete sonidos que no están en el guion o junta palabras (EP002: "calientito..." sonó "calientí"; "fuerzas..." metió un "¡oh!"; "escoba..." sonó "escóbatas"). Mejor coma o punto: el respiro y el suspenso los pone `recortar_pausas.py`.
- **Rehacer solo una línea** (una palabra que no se oye bien): corregir esa línea en `narracion.txt` y `py Herramientas/audio/voz_elevenlabs.py EP### --linea N` (si la voz dice esa línea pegada a la siguiente, se rehacen juntas: `--linea 24-26`) (misma voz y ajustes, con las líneas de antes y después como contexto para que suene igual; gasta solo los créditos de esa línea; la voz anterior queda en `Respaldos/`). La línea nueva se iguala al volumen de las líneas vecinas (pedida sola puede salir mucho más fuerte: en EP002, +9 dB). Probar sin gastar créditos: `--simular`; volver a pegar la línea ya pedida sin pagar otra vez: `--reusar`. Después, recortar otra vez.
- **Agregar un bloque nuevo sin rehacer la voz aprobada** (episodios largos, por bloques): poner las líneas nuevas al final de `narracion.txt` y `py Herramientas/audio/voz_elevenlabs.py EP### --agregar`. Genera solo las líneas nuevas (con las últimas como contexto y el mismo volumen) y las pega al final; lo pedido queda guardado en `Respaldos/.../agregadas.json` para volver a pegarlo sin pagar con `--respuesta`. Al rehacer una voz completa se usa la misma voz del episodio (`audio/narracion_info.json`).
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
- 1–2 palabras por subtítulo (automáticos desde los tiempos de cada palabra), **una sola línea**, **sin comillas ni signos** (. , ! ¡ ? ¿ : ;): `"no pienses…"` sale `no pienses`.
- Posición: abajo al centro, `MarginV 400` sobre 1920 (≈79 % de la altura, como YouTube; no tan abajo para no chocar con la interfaz de Shorts).
- Estilo: Arial Black 92, blanco, contorno negro 8, sombra 3; palabras clave en amarillo (`HILITE`); entrada con "pop" (118 % → 100 % en 90 ms).
- Tiempos: cada subtítulo aparece 0,03 s antes de su primera palabra y dura hasta el siguiente.

## Efectos (pocos y con sentido)
- **Que coincidan con lo que pasa**: cada golpe en el momento exacto de la acción (en `armar_video.py`: `("palabra:pum", "pop", 5, -3)` cae con la palabra; `"toma:6"` al empezar la toma 6). Si hay un respiro sin voz, lo llena un efecto acorde (cambio de emoción), nunca silencio.
- **Onomatopeyas que hace el efecto** ("¡Dong!"): ElevenLabs las lee como inglés. `CALLAR = {"dong"}` en `armar_video.py` las silencia en la voz y las quita de los subtítulos; mejor no escribirlas en `narracion.txt` (lección 68).
- **Ambiente**: poco y que coincida con la escena (ej. grillos bajitos de noche: `night_ambience`, −22 dB). El viento constante cansa: no ponerlo por defecto (cada canal anota sus gustos en `MI_CANAL.md`).
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

## Mezcla y exportación
- `armar_video.py preview|final`: voz + efectos (numpy) → `loudnorm I=-14` → subtítulos → H.264 `-preset slow -crf 17`, AAC 256k, `+faststart`.
- Verificar: `ffmpeg -i video.mp4 -af ebur128 -f null -` (≈ −14/−15 LUFS) y fotos con subtítulos.
