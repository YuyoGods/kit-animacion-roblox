# 06 — Voz, subtítulos, efectos y mezcla

## Voz (ElevenLabs)
- Script: `py Herramientas/audio/voz_elevenlabs.py EP###_Titulo` → lee `EP###/narracion.txt`, guarda en `EP###/audio/`. La voz sale de `mi_config.json` → `voz_narrador`.
- Clave: variable de entorno de usuario `ELEVENLABS_API_KEY` (el script la lee de Windows; nunca se imprime). Para crearla (la pone el usuario):
  `[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", "CLAVE", "User")`
- Voz: la de `MI_CANAL.md` / `mi_config.json`. Modelo `eleven_multilingual_v2`, stability 0,4 · similarity 0,75 · style 0,3 · speaker boost.
- Endpoint con tiempos: `/v1/text-to-speech/{voz}/with-timestamps` → MP3 + tiempo de cada letra (`narracion_tiempos.json`).
- Escribir con "..." para pausas y "¡!" para emoción. Generar todo el texto en una sola llamada (suena continuo).
- **Confirmar con el usuario antes de gastar créditos.**

## Acomodar la voz al video
- Medir inicio/fin de cada frase (tiempos por letra) y compararlo con el inicio de su toma.
- Mover cada frase (`NEW_START` en `armar_video.py`) para que la acción coincida (ej. "tocó la puerta" con los golpes).
- Si la última frase no cabe, **alargar la última toma** (sostener el primer plano).

## Subtítulos (ASS quemado con FFmpeg/libass)
- 1–3 palabras por subtítulo, **una sola línea**, sin puntos ni comas finales.
- Posición: abajo al centro, `MarginV 400` sobre 1920 (≈79 % de la altura, como YouTube; no tan abajo para no chocar con la interfaz de Shorts).
- Estilo: Arial Black 92, blanco, contorno negro 8, sombra 3; palabras clave en amarillo (`HILITE`); entrada con "pop" (118 % → 100 % en 90 ms).
- Tiempos: cada subtítulo aparece 0,03 s antes de su primera palabra y dura hasta el siguiente.

## Efectos (pocos y con sentido)
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
