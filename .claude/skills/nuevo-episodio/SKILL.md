---
name: nuevo-episodio
description: Produce un episodio (Short animado estilo Roblox) de principio a fin: guion, narración, voz, tomas desde la voz, escenario, personajes, animación, caras por emoción, revisión de cámaras, vista previa, subtítulos, efectos y render. Usar cuando el usuario pida "hazme un video/historia/episodio", "anima esta historia" o "al estilo de <Creador>".
---

# Nuevo episodio

Seguir `docs/01_PIPELINE.md` y las reglas de `CLAUDE.md` (sobre todo las reglas de oro 9–12). Resumen:

1. Leer `MI_CANAL.md` (reparto: protagonista A, secundarios B, NPC C; NPC con nombre; qué personajes NO cambian de cara) y, si pidió un estilo, `Analizador/Estilos/<Creador>.json` + `_notas.md`.
2. **Guion** siguiendo `docs/08_HISTORIAS.md` (bucle abierto, pistas reales escondidas, una pista falsa, giro que re-interpreta, último golpe). Copiar `Episodios/_PLANTILLA_EPISODIO` como `Episodios/EP###_Titulo/`.
3. **Narración con voz en cada escena** en `narracion.txt`: **una línea = una toma**, frases cortas y concretas, narrador en primera persona, onomatopeyas en la voz (¡pum!, ¡pop!). No hace falta que sea larga: el video dura lo que la voz. Mostrarla al usuario → **aprobación** antes de gastar créditos.
4. **Voz primero**, con la voz de cada quien y a **velocidad normal**: su voz de ElevenLabs (`py Herramientas/audio/voz_elevenlabs.py EP###_Titulo`, confirmar créditos) o una voz ya hecha que entregue. **El usuario la escucha y la aprueba.** Luego `py Herramientas/audio/recortar_pausas.py EP###_Titulo [--audio su_voz.mp3]` (quita silencios largos sin que se note) → `py Herramientas/audio/tomas_desde_voz.py EP###_Titulo` (tomas y fotograma de cada palabra en `audio/tomas_voz.json`).
5. **Escenario**: abrir el mapa de `Escenarios/<Mapa>/` (nunca modificar el original) y anexar solo los personajes que salen (ya con rig; caras por textura con `caras_textura.py` si el personaje no es excepción).
6. **Animación y cámaras por script** leyendo `tomas_voz.json`: cada toma dura lo que su línea, los golpes caen en su palabra, cada personaje cambia de cara según la emoción de la toma (las excepciones se expresan con poses, efectos y sonido).
7. **Revisión obligatoria**: `revisar_camaras.py` + hoja de contacto (`hoja_contacto.py` + `componer_hoja.py`); corregir antes de renderizar.
8. **Vista previa**: preguntar "¿Quieres que renderice con dos Blender en paralelo para que sea más rápido?" (`py Herramientas/render_paralelo.py EP###_Titulo preview`; si no, `--procesos 1`) → copiar `Herramientas/audio/armar_video.py` a `scripts/` y llenar AMBIENTES/EFECTOS para que **coincidan con lo que pasa** (golpes en su palabra) → el usuario aprueba. Si una parte no le gusta: skill `rehacer-tramo`.
9. **Render final** (confirmar si tarda > 15 min) con `render_paralelo.py ... final` → MP4 final. Publicar solo si el usuario lo pide.
10. Anotar en `MI_BITACORA.md`. Lecciones nuevas: `MI_LECCIONES.md` (rol usuario) o `docs/02_LECCIONES.md` (rol mantenedor).
