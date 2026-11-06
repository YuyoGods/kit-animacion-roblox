---
name: analizar-videos
description: Analiza los videos de otros creadores que el usuario subió a Analizador/Videos_para_analizar/<Creador>/ y actualiza la fórmula de estilo de cada creador. Usar cuando diga "analiza los videos nuevos", "ya subí videos de X", "entrena el analizador", "qué hace diferente a X".
---

# Analizar videos y actualizar fórmulas

1. Ver qué hay nuevo en `Analizador/Videos_para_analizar/*/` (nombre, duración). Un creador = una carpeta.
2. Correr en **segundo plano**: `py -X utf8 Analizador/motor/analizar.py` (solo analiza lo nuevo; ≈1,5× la duración del video con GPU). Avisar al usuario y seguir cuando termine.
3. Por cada video nuevo, **revisión de Claude** (ver `docs/07_ANALISIS_REFERENCIAS.md`): leer `para_claude.md`, mirar `hojas/` y `efectos/`, escribir `notas_claude.md` en `Analizador/Resultados/<Creador>/<video>/`.
4. Pasar a `Analizador/Estilos/<Creador>_notas.md` las reglas que se repiten en 2+ videos (patrones, nunca copiar guiones).
5. Responder corto: cuántos videos lleva cada creador, confiabilidad y 3–5 cosas nuevas aprendidas. Detalle: `Analizador/Estilos/<Creador>_formula.md` y `COMPARACION.md`.

Los videos y resultados son personales (no se suben). Las fórmulas sí se comparten.
