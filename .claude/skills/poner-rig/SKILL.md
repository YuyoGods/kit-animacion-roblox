---
name: poner-rig
description: Arma el rig R15 (huesos para animar) de un personaje exportado de Roblox Studio que el usuario subió a Personajes/Protagonista, Secundarios o Pueblo_NPC. Usar cuando diga "ya subí a X, ponle su rig", "riguea a mi personaje", "esta es mi hermana, agrégala como secundaria".
---

# Poner rig a un personaje

Seguir **directo y sin explicaciones largas** la *Receta* de `docs/03_PERSONAJES.md`:

0. Si los personajes están en **Roblox Studio** y hay que exportarlos (uno o muchos): seguir `Herramientas/roblox/LEEME.md` (aislar, exportar, restaurar y crear `partes.json`); después el paso 3 para cada uno.
1. Ubicar la carpeta: `Personajes/<Protagonista|Secundarios|Pueblo_NPC>/<Nombre>/` (familia, amigos, autoridades → `Secundarios`). Revisar que estén `.obj` + `.mtl` + `.png`.
2. Si hay un rig anterior (`<Nombre>_R15_Rig.blend`), moverlo a `Respaldos/` antes de seguir.
3. Correr el rig automático: `blender -b --factory-startup --python Herramientas/blender/armar_rig_r15_auto.py -- "<carpeta>" <Nombre>` (centra, voltea si hace falta, reconoce piezas y accesorios). Revisar el mapa que imprime. Si falla, usar la plantilla manual (`armar_rig_r15_plantilla.py`).
4. Revisar las fotos de `previews/` (nada separado, nada flotando, materiales conectados). Corregir si hace falta.
   - **Examinar la piel** (pedido del usuario, 2026-11-09): `blender -b "<carpeta>/<Nombre>_R15_Rig.blend" --python Herramientas/blender/revisar_piel.py`. Debe decir **OK**: la cabeza y las manos tienen el mismo tono. Si dice `SE ARREGLA`, correrlo con `-- --arreglar`. Si dice `REVISAR`, el personaje trae tonos distintos de fábrica: avisarle al usuario con una foto y proponerle igualarlos (`objetos_cartoon.igualar_piel`).
5. **No borrar** lo que subió el usuario. Si ya había un `<Nombre>_R15_Rig.blend`, moverlo a `Respaldos/` antes.
6. Anotar en `MI_CANAL.md` (reparto y detalle) y responder: *"Listo: <Nombre> ya tiene rig → `<ruta>`"* + una foto.
