# Analizador de videos

Estudia videos de otros creadores **toma por toma y fotograma por fotograma** y saca su **fórmula**: ritmo de cortes, tipos de plano, movimientos de cámara, temblor, zooms, transiciones, efectos, subtítulos, voz, sonido y estructura de la historia. Esa fórmula la usa Claude para animar "al estilo de…".

## 1. Sube los videos
```
Analizador/Videos_para_analizar/
├── ClusterK/     ← aquí los videos de ClusterK
├── Gelo/         ← aquí los videos de Gelo
└── <OtroCreador>/  (crea una carpeta con su nombre)
```
- Formatos: `.mp4`, `.mov`, `.mkv`, `.webm`. El nombre del archivo puede ser cualquiera (con acentos o emojis está bien).
- Entre más variados, mejor: **mínimo 5 por creador** para una fórmula confiable, **15 o más** para una muy buena.

## 2. Pídele a Claude: **"Analiza los videos nuevos"**
Claude corre:
```
py -X utf8 Analizador/motor/analizar.py
```
Solo analiza lo **nuevo** (lo ya analizado se salta). Un video de 2 minutos tarda unos 3–5 minutos con la tarjeta de video.

Después Claude hace la **revisión cualitativa** (lo que la máquina no puede medir sola): mira las hojas de contacto y los efectos, lee la historia y escribe sus notas.

## 3. Qué sale
| Dónde | Qué es |
|---|---|
| `Resultados/<Creador>/<video>/reporte.html` | Reporte visual: línea de tiempo con miniaturas, gráficas, tomas, subtítulos, efectos, narración |
| `Resultados/<Creador>/<video>/hojas/` | Hojas de contacto: inicio, mitad y fin de cada toma con sus datos |
| `Resultados/<Creador>/<video>/efectos/` | Momentos con posible efecto (destellos, partículas, sacudidas, cambios de color) |
| `Resultados/<Creador>/<video>/notas_claude.md` | Lo que Claude vio al revisarlo (historia, efectos reales, patrones) |
| `Estilos/<Creador>_formula.md` | **La fórmula del creador** en palabras (se actualiza sola con cada video nuevo) |
| `Estilos/<Creador>.json` | La misma fórmula en números (la leen los scripts de animación) |
| `Estilos/<Creador>_notas.md` | Reglas que Claude va aprendiendo al revisar (se va completando, nunca se borra) |
| `Estilos/COMPARACION.md` | Todos los creadores lado a lado (y `Nosotros`, para ver qué tanto nos parecemos) |

## Cómo "aprende"
No es una red neuronal que se re-entrena: cada video nuevo **suma datos medidos** a la fórmula (más videos = números más confiables) y Claude **suma reglas** a las notas al revisarlo. Las dos cosas juntas son el "modelo entrenado" de cada creador, y se pueden compartir en el repositorio (los videos y los resultados con imágenes no, porque son de sus creadores).

## Qué mide (motores)
- **Cortes y transiciones**: PySceneDetect + verificación propia (corte directo, fundido, destello, disolvencia, barrido, zoom).
- **Cámara**: alineación entre cuadros (OpenCV): acercamiento, alejamiento, golpe de zoom, paneo, giro, temblor (fuerza y frecuencia).
- **Tipo de plano**: tamaño de la cara y del cuerpo detectados (Grounding DINO) + CLIP para plano aéreo, ambiente, hora y lugar.
- **Subtítulos**: OCR (EasyOCR): palabras por subtítulo, posición, tamaño, color, palabra resaltada, mayúsculas, contorno, animación de entrada y sincronía con la voz.
- **Voz**: Whisper large-v3-turbo con tiempo de cada palabra (filtra frases inventadas en silencios).
- **Sonido**: volumen (LUFS), golpes de sonido, fondo/música, ritmo (BPM).
- **Historia**: gancho, preguntas, giros, final, llamados a la acción.

Calibrado con nuestro EP001: detecta sus 11 tomas exactas, el temblor solo en la toma corriendo y el estilo de subtítulos correcto.
