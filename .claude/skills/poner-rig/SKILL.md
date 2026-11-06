---
name: poner-rig
description: Arma el rig R15 (huesos para animar) de un personaje exportado de Roblox Studio que el usuario subió a Personajes/Protagonista, Secundarios o Pueblo_NPC. Usar cuando diga "ya subí a X, ponle su rig", "riguea a mi personaje", "esta es mi hermana, agrégala como secundaria".
---

# Poner rig a un personaje

Seguir **directo y sin explicaciones largas** la *Receta* de `docs/03_PERSONAJES.md`:

1. Ubicar la carpeta: `Personajes/<Protagonista|Secundarios|Pueblo_NPC>/<Nombre>/` (familia, amigos, autoridades → `Secundarios`). Revisar que estén `.obj` + `.mtl` + `.png`.
2. Listar los grupos del OBJ en Blender de fondo (centro y tamaño de cada grupo con `matrix_world` aplicado) y armar el mapa `PARTS` (15 piezas R15; *Right* = −X mirando a −Y) y `ACC` (accesorios → hueso más cercano).
3. Copiar `Herramientas/blender/armar_rig_r15_plantilla.py` como `build_<nombre>_rig.py` en la carpeta del personaje, cambiar el nombre y los mapas, ejecutar con `blender -b --factory-startup --python build_<nombre>_rig.py`.
4. Revisar las fotos de `previews/` (nada separado, nada flotando, materiales conectados). Corregir si hace falta.
5. **No borrar** lo que subió el usuario. Si ya había un `<Nombre>_R15_Rig.blend`, moverlo a `Respaldos/` antes.
6. Anotar en `MI_CANAL.md` (reparto y detalle) y responder: *"Listo: <Nombre> ya tiene rig → `<ruta>`"* + una foto.
