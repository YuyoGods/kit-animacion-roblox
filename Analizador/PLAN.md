# Plan: de "analizar creadores" a "animar con su fórmula"

Meta: que al pedir *"hazme una historia de 2 min al estilo de ClusterK"* salga un video con su ritmo, sus tomas, sus efectos, sus subtítulos y su forma de contar la historia, y que cualquier parte se pueda corregir sin rehacer todo.

## Fase 1 — Analizador (✅ hecho, 2026-11-06)
- Analizador v2 con GPU: cortes verificados, cámara, tipo de plano medido, subtítulos (OCR), voz (Whisper), sonido, historia, efectos candidatos, reporte HTML, fórmula por creador y comparación.
- Calibrado con EP001 (11/11 tomas, temblor y subtítulos correctos).
- `Herramientas/rehacer_tramo.py`: rehacer solo del segundo X al Y (con respaldo y deshacer).

## Fase 2 — Entrenar con ClusterK y Gelo (lo que sigue)
**Tú:**
1. Sube **10–20 videos por creador** a `Analizador/Videos_para_analizar/ClusterK/` y `.../Gelo/`. Variados: los más vistos, los más nuevos, distintos temas y duraciones.
2. *(Opcional, muy útil)* En cada carpeta crea `vistas.txt` con una línea por video: `nombre del archivo ; vistas`. Con eso hago que los videos más virales pesen más en la fórmula (lo activo cuando lleguen los videos).
3. Videos tutoriales (cómo trabajan otras herramientas o creadores): ponlos en `Analizador/Videos_para_analizar/_Tutoriales/`. El analizador los transcribe y saca hojas de contacto (las carpetas que empiezan con `_` no cuentan como estilo) para tomar ideas.
4. Dime **"Analiza los videos nuevos"**.

**Claude:**
- Corre el analizador, revisa cada video (hojas, efectos, historia) y escribe notas y reglas.
- Revisa a mano 3–5 videos para **calibrar** los detectores con su estilo (como se hizo con EP001).
- Entrega: `ClusterK_formula.md`, `Gelo_formula.md`, notas y `COMPARACION.md` + resumen de "qué hace diferente a cada uno".

## Fase 3 — De la fórmula a la tabla de tomas
- `plan_tomas.py`: guion + fórmula → tabla de tomas automática (duración de cada toma, tipo de plano, movimiento de cámara, temblor, golpes de zoom, transiciones, dónde va cada frase).
- Biblioteca de **cámaras listas** en Blender: dron, frontal con temblor, órbita 360, acercamiento lento, golpe de zoom, paneo látigo, primer plano de reacción, objeto que tapa (transición).
- Medir el resultado: analizar nuestra vista previa como `Nosotros` y comparar con el creador (porcentaje de parecido).

## Fase 4 — Efectos low poly / caricatura
Biblioteca en Blender, sencillos y estilo Roblox (no realistas), con un comando cada uno:
hojas que caen, viento (líneas), humo en bolitas, polvo al correr, chispas/estrellas de impacto, líneas de velocidad, lluvia, nieve, confeti, emotes (!, ?, gotas de sudor, corazones, calavera), destello de pantalla.
Primero se hacen por código (sin depender de nadie); opcional: sprites CC0 (Kenney) para ir más rápido.

## Fase 5 — Subtítulos y audio con estilo
- Subtítulos parametrizados por la fórmula: palabra por palabra o grupos, color, palabra resaltada que avanza (karaoke), mayúsculas, pop, posición.
- Separar `armar_video.py` en motor fijo + datos del episodio.
- Efectos de sonido por tipo (whoosh, golpe, pop, tensión) según lo que usa cada creador; música libre opcional.

## Fase 6 — Historias de 2 minutos
- Plantilla de guion con la estructura medida: gancho (0–3 s) → planteamiento → escalada → giro(s) → final con misterio que se resuelve al último.
- Banco de ganchos y giros que funcionan (patrones, no copias).

## Fase 7 — Personajes que crea Claude
- Animales y criaturas estilo Roblox (gato, búho, oso…) hechos por código, con rig simple y caras intercambiables.
- Caras por emoción aplicadas automáticamente según el guion.

## Recomendaciones extra (propuestas de Claude)
1. **Puntaje de parecido**: cada vista previa nuestra se analiza y se compara con el estilo elegido (ritmo, planos, subtítulos, audio) → sabemos qué falta antes de publicar.
2. **Pesar por vistas**: la fórmula da más peso a los videos más virales (con `vistas.txt`).
3. **Separar voz / música / efectos** (Demucs) y **reconocer el tipo de efecto de sonido** (whoosh, boom, pop) para copiar su diseño de sonido.
4. **Miniaturas y títulos**: analizar también las miniaturas y títulos de los videos más vistos (colores, caras, texto) para que el video empiece a ganar desde el clic.
5. **Retención propia**: cuando publiques, anotar la retención de YouTube Studio de cada video nuestro y cruzarla con lo medido → aprender de nuestros propios datos.
6. **Render por tomas**: renderizar cada toma en su carpeta para que cambiar una toma no toque las demás, y versiones de vista previa (v1, v2…) para comparar.
