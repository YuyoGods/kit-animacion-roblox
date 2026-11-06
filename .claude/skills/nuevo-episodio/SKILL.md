---
name: nuevo-episodio
description: Produce un episodio (Short animado estilo Roblox) de principio a fin: guion, tabla de tomas, escenario, personajes, animación, revisión de cámaras, vista previa, voz, subtítulos, efectos y render. Usar cuando el usuario pida "hazme un video/historia/episodio", "anima esta historia" o "al estilo de <Creador>".
---

# Nuevo episodio

Seguir `docs/01_PIPELINE.md` y las reglas de `CLAUDE.md`. Resumen:

1. Leer `MI_CANAL.md` (reparto: protagonista A, secundarios B, NPC C; NPC con nombre) y, si pidió un estilo, `Analizador/Estilos/<Creador>.json` + `_notas.md`.
2. Copiar `Episodios/_PLANTILLA_EPISODIO` como `Episodios/EP###_Titulo/`. Guion, narración y tabla de tomas en `GUION.md` → **aprobación del usuario** antes de animar.
3. Escenario: abrir el mapa de `Escenarios/<Mapa>/` (nunca modificar el original) y anexar solo los personajes que salen (ya con rig).
4. Animación y cámaras por script. **Revisión obligatoria**: `revisar_camaras.py` + fotos de inicio/mitad/fin de cada toma; corregir antes de renderizar.
5. Vista previa (50 %) en segundo plano → el usuario aprueba. Si una parte no le gusta: skill `rehacer-tramo`.
6. Voz (ElevenLabs, **confirmar créditos**) → subtítulos y efectos → `armar_video.py`.
7. Render final (confirmar si tarda > 15 min) → MP4 final. Publicar solo si el usuario lo pide.
8. Anotar en `MI_BITACORA.md`. Lecciones nuevas: `MI_LECCIONES.md` (rol usuario) o `docs/02_LECCIONES.md` (rol mantenedor).
