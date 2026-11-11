# Música de fondo (PERSONAL)

Aquí va la canción de fondo del canal. Git no sube esta carpeta (solo este LEEME), porque la música puede tener licencia.

- Ruta en `mi_config.json` → `"musica_fondo"` (puede ser relativa a la raíz del kit, por ejemplo `Musica/Song Animations.mp3`).
- `"musica_fondo_db"`: cuántos dB queda la música por debajo de la voz (por defecto −16; más negativo = más bajita).
- `armar_video.py` la pone de principio a fin del video. Si la canción es más larga, se recorta al final con una salida suave de 1,5 s, para que no quede pantalla negra. Si es más corta, se repite. Mientras habla el narrador baja un poco más (unos 4 dB) y sube en los respiros.
- Si `"musica_fondo"` está vacío, el video sale sin música.
