# 07 — Análisis de referencias (patrones de cámara de otros creadores)

## Objetivo
Los creadores exitosos de historias animadas de Roblox **repiten un patrón de cámara** en casi todas sus tomas: cada cuánto cortan, cuándo hacen zoom, qué tipo de plano usan y cómo enfocan. Ese patrón es gran parte del "enganche".
Meta: **medir** esos patrones fotograma por fotograma y convertirlos en **recetas de cámara** que nuestros episodios usen automáticamente.

> Se analiza para aprender el **estilo de edición y cámara**, no para copiar historias, personajes ni escenas. Nuestros videos son propios.

## Qué medir (ficha de estilo)
| # | Aspecto | Qué anotar |
|---|---|---|
| 1 | **Ritmo de cortes** | duración de cada toma; promedio, mediana, mín/máx; cortes por minuto |
| 2 | **Tipo de plano** | general / medio / primer plano / detalle / dron / POV; en qué orden se alternan |
| 3 | **Movimiento dentro de la toma** | fija, acercamiento (zoom in), alejamiento, paneo, seguimiento, órbita, temblor; velocidad (% de escala por segundo) |
| 4 | **Zoom** | cada cuántos segundos/tomas, cuánto (110 %, 130 %), duración, si es de cámara o "golpe" de edición |
| 5 | **Transiciones** | corte seco, objeto que tapa, barrido rápido, flash, zoom; cuándo se usan (cambio de lugar/tiempo) |
| 6 | **Encuadre** | dónde queda el personaje (centro/tercios), altura de cámara, hacia dónde mira |
| 7 | **Sincronía con la voz** | ¿corta en cada frase? ¿en palabras clave? ¿cambia la expresión del personaje? |
| 8 | **Subtítulos** | palabras por bloque, posición, tamaño, colores, animación |
| 9 | **Sonido** | efectos por minuto, tipos, música |
| 10 | **Gancho** | qué pasa en los primeros 3 segundos |

## Método (herramientas)
1. **Cortes**: detección de cambios de escena con FFmpeg (`select='gt(scene,0.3)',showinfo`) → tiempos de corte → duraciones. Confirmar con hojas de contacto.
2. **Fotogramas**: 1 cada 0,5 s + hoja de contacto por toma (inicio/mitad/fin) → Claude clasifica tipo de plano, encuadre y transiciones viendo las imágenes.
3. **Zoom, paneo y temblor**: comparar fotogramas seguidos (flujo óptico / transformación entre fotogramas) → escala y desplazamiento por fotograma → detecta acercamientos, alejamientos, paneos y la amplitud/frecuencia del temblor. *Requiere instalar `opencv-python` (pedir permiso antes).*
4. **Narración**: transcripción con tiempos por palabra → comparar cortes con frases y palabras clave.
5. **Resumen**: tabla de tomas + estadísticas + reglas en lenguaje simple.

## Uso (herramienta lista)
```
py -X utf8 04_Herramientas/analisis/analizar_referencia.py "RUTA\video.mp4" --creador NombreDelCreador
```
Opciones: `--nombre ref_03` (nombre de la carpeta), `--umbral 22` (más bajo = detecta más cortes; por defecto 27), `--sin-voz` (no transcribir).
Instalado: OpenCV 5 (zoom/paneo/temblor por fotograma), PySceneDetect 0.7 (cortes), faster-whisper 1.2 con modelo **large-v3-turbo** (transcripción en español con tiempos por palabra, en la PC, gratis), matplotlib (gráficas). Tarda ~20–40 s por cada 30 s de video.

Qué entrega por video:
- **`ficha.md`**: resumen (tomas, cortes por minuto, duración media/mediana, tipos de toma, zoom medio, ritmo de narración, % de cortes que caen en una palabra) + tabla toma por toma con su texto.
- **`hojas/`**: hojas de contacto (inicio/mitad/fin de cada toma con sus datos) → Claude las revisa para anotar tipo de plano, encuadre y transiciones.
- **`grafica.png`**: duración de cada toma, zoom acumulado y temblor a lo largo del video.
- **`datos.json`**: todo en datos para la receta de cámara.
- Además actualiza **`00_Referencias/<Creador>/ficha_estilo.md`** con el promedio de todos los videos de ese creador.

Probado con EP001 (`00_Referencias/_Prueba_EP001/`): midió bien los acercamientos de la toma frontal (+20 %), el temblor fuerte de la cámara de frente al correr (13,5–17,3 s), el ritmo de narración (3 palabras/s) y que el 83 % de los cortes caen en una palabra. Limitación: a veces junta dos tomas cuando el cambio es suave (bajar `--umbral`).

## Resultado por referencia
```
00_Referencias/<Creador_o_Serie>/
├── videos/            ← MP4 originales del usuario
├── fotogramas/        ← hojas de contacto
├── datos.json         ← cada toma: inicio, duración, tipo, movimiento, zoom, transición
└── ficha_estilo.md    ← estadísticas + reglas ("toma media 1,6 s; zoom in cada 2 tomas al 115 %…")
```

## Cómo se usa después
Las reglas de la ficha alimentan una **receta de cámara** (`04_Herramientas/`) que, a partir de la tabla de tomas del guion, genera las cámaras del episodio con ese ritmo (duraciones, tipos de plano, zooms, transiciones). Después se revisa con `revisar_camaras.py` como siempre.

## Primeras observaciones (videos analizados el 2026-11-05)
Tres videos de un mismo creador ("NO ENTRES AL BÚNKER", "NO TE CASES CON ELLA", "APUNTE MAL"), formato 9:16 a 30 fps, 1–2 min:
- **Cortes muy rápidos**: en "Búnker" 41 cortes en 115 s → **≈ 2,8 s por toma** (rango ≈ 1,1–6 s).
- **Subtítulos de una palabra** en el centro-bajo, algunas palabras clave en rojo/amarillo.
- Mucho **primer plano de cara** con cambios de expresión en cada frase emocional; planos generales cortos para ubicar el lugar.
- Escenarios muy coloridos con iluminación fuerte de color (rojo de alarma, verde, azul neón).
- Narrador en primera persona contando la historia de corrido; cada frase tiene su imagen.
*(Pendiente: medir zooms y movimientos con el método completo.)*
