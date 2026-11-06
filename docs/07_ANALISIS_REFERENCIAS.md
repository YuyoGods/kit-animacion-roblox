# 07 — Analizador de videos y fórmulas de estilo

Objetivo: copiar **la fórmula** de los creadores que funcionan (ritmo, planos, cámara, efectos, subtítulos, sonido e historia) y aplicarla a nuestras animaciones ("hazlo al estilo de ClusterK"). Guía para personas: `Analizador/LEEME.md`.

## Flujo de "entrenamiento" (cada vez que el usuario sube videos)
1. Videos en `Analizador/Videos_para_analizar/<Creador>/`.
2. `py -X utf8 Analizador/motor/analizar.py` → analiza solo lo nuevo (registro en `Resultados/registro.json`) y regenera `Estilos/<Creador>.json`, `<Creador>_formula.md` y `COMPARACION.md`.
   - Correrlo en segundo plano si son muchos videos (≈2–3× la duración del video con GPU). Un video que falla no detiene a los demás.
3. **Revisión de Claude** por cada video nuevo (lo que la máquina no mide bien):
   - Leer `para_claude.md` y mirar `hojas/hoja_*.jpg` y `efectos/efecto_*.jpg`.
   - Escribir `notas_claude.md` en la carpeta del video: gancho, estructura con segundos, misterio/retención, personajes, patrones de cámara, efectos reales (hojas, humo, líneas de velocidad, emojis…), subtítulos exactos, sonido, 5 reglas.
   - Pasar a `Estilos/<Creador>_notas.md` las reglas que **se repiten en 2+ videos** (no copiar texto ni guiones de los creadores: solo patrones).
4. Contarle al usuario lo nuevo que se aprendió (3–5 líneas) y cuántos videos lleva cada creador.

## Usar una fórmula al animar
- Leer `Estilos/<Creador>.json` (números) y `<Creador>_notas.md` (reglas).
- Guion: duración típica, gancho en los primeros segundos, giros por minuto, final con misterio según las notas.
- Tabla de tomas: duraciones según `ritmo` (mediana y rango, más rápido donde la fórmula lo indique), mezcla de `planos_pct`, movimientos de `camara_pct`, temblor (`camara.temblor_*`), golpes de zoom por minuto, transiciones.
- Subtítulos: `subtitulos` (modo, palabras, altura, tamaño, color, resaltado, mayúsculas, pop) → parámetros de `armar_video.py`.
- Sonido: LUFS, golpes de sonido por minuto, música sí/no.
- Comparar el resultado: analizar nuestra vista previa con `--creador Nosotros` y ver `COMPARACION.md`.

## Qué mide cada dato (y qué tan confiable es)
| Dato | Cómo | Confiable |
|---|---|---|
| Cortes | PySceneDetect (umbral 22) + verificación: salto aislado ≥ 2× los cuadros vecinos o ≥ 42 | Alta (EP001: 11/11, 0 falsos). Cortes escondidos tras un objeto que tapa pueden no verse (es su intención) |
| Transiciones | brillo (fundido/destello), prueba de mezcla A+B (disolvencia), movimiento + desenfoque (barrido), zoom final | Media |
| Cámara | alineación ORB+RANSAC entre cuadros: zoom, paneo, giro; temblor = residuo de alta frecuencia (umbral 2,5) | Media-alta; con mucho movimiento del personaje la cámara que lo sigue sale como "acercamiento/alejamiento" |
| Tipo de plano | Grounding DINO: alto de la cara (≥40 % primerísimo, ≥22 % primer plano, ≥11 % medio) y del cuerpo (≥85 % medio, ≥40 % entero) | Media-alta |
| Ambiente, hora, lugar | CLIP sin entrenar | Baja-media (orientativo) |
| Efectos | destellos, negro/blanco, partículas (muchos puntos que se mueven aparte de la cámara), sacudida de impacto, imagen congelada, cambio de color, cámara lenta | **Candidatos**: Claude los confirma mirando `efectos/`. Las "partículas" dan muchos falsos con dron/paralaje y gigantes caminando (visto en ClusterK/Gelo): no usarlas como regla |
| Subtítulos | EasyOCR a 6 muestras/s + fotograma a fotograma en los primeros 12 (inicio exacto y pop) | Alta en posición/tamaño/colores; el texto leído puede tener errores (se usa la voz para contar palabras) |
| Voz | Whisper large-v3-turbo (GPU) con tiempo por palabra; descarta frases inventadas en silencios | Alta |
| Sonido | LUFS (FFmpeg ebur128), golpes fuera de la voz (librosa), fondo armónico ⇒ música probable | Media |
| Historia | palabras clave de giro, preguntas, final, llamados a la acción | Baja: lo importante lo escribe Claude en las notas |

## Lecciones del analizador
- Los subtítulos quemados no se mueven entre cuadros y engañan la verificación de cortes por alineación: por eso se usa el salto aislado.
- Whisper inventa "¡Suscríbete al canal!" en silencios finales: se descarta por logprob bajo + velocidad imposible (> 5,5 palabras/s).
- El cielo o el fondo se cuelan en el color del subtítulo: el relleno se mide solo en pixeles claros pegados al contorno oscuro.
- Primera carga de modelos: ~1 min (después quedan en caché en `%USERPROFILE%\.cache`).
