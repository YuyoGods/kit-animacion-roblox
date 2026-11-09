# Roblox Studio → personajes del kit (exportar muchos de una vez)

Para cuando el usuario pone varios personajes en un lugar de Roblox Studio y pide "expórtalos y ponles rig".
Claude lo hace solo con el MCP de Roblox Studio + estos archivos (probado con 24 personajes el 2026-11-07).

| Archivo | Qué hace |
|---|---|
| `studio_personajes.luau` | Se pega una vez con `execute_luau`. `_G.CL_isolate("Nombre")` deja solo ese personaje en el Workspace (lo demás va a ServerStorage), `_G.CL_restore()` regresa todo, `_G.CL_datos()` da la posición de cada pieza y los accesorios en el orden del OBJ. Reversible: no borra ni guarda el lugar. |
| `exportar_obj.ps1` | Abre **Archivo › Exportar como .obj**, pega la ruta en el diálogo de Windows y guarda. No sobrescribe. |
| `partes_json.py` | Escribe `partes.json` en la carpeta del personaje: nombre real de cada grupo del OBJ, piezas que no vinieron y qué accesorios son ropa en capas. `armar_rig_r15_auto.py` lo usa solo. |

## Pasos
1. `list_roblox_studios` → elegir el lugar. Ver los personajes y en qué grupo van (A/B/C) según lo que diga el usuario o su imagen.
2. Pegar `studio_personajes.luau` con `execute_luau` (Edit).
3. Por cada personaje: `_G.CL_isolate("Nombre")` y luego
   `powershell -STA -File Herramientas\roblox\exportar_obj.ps1 -Ruta "<kit>\Personajes\<nivel>\<Carpeta>\<Carpeta>.obj"`.
   Un personaje a la vez (aislar → exportar), nunca en paralelo.
4. **`_G.CL_restore()` al terminar** (y confirmar que no quedó `ServerStorage._TEMP_EXPORT_CLAUDE`).
5. `_G.CL_datos()` → guardar el JSON en un archivo → `py Herramientas/roblox/partes_json.py datos.json "NombreStudio=Personajes/<nivel>/<Carpeta>" ...`
6. Rig: `blender.exe -b --factory-startup --python Herramientas/blender/armar_rig_r15_auto.py -- "<carpeta>" <Carpeta>` (lee `partes.json`, ya sabe que debe voltearlo).

## Por qué así (lo aprendido)
- **"Exportar como .obj" exporta TODO el lugar**, no la selección (en esta versión no hay "Exportar selección" en los menús). Por eso se aísla cada personaje.
- **Orden del OBJ** = orden inverso de `GetDescendants()` del modelo, sin las piezas invisibles. Los nombres de grupo (`Crush1…Crush15`, `Handle1…`) no dicen qué pieza es; el número cambia en cada avatar.
- **Coordenadas del OBJ = coordenadas del mundo de Studio** (Blender: x, −z, y). Por eso las piezas se empatan por posición. Si el personaje se movió después de exportarlo, `partes_json.py` resta el centro.
- Un personaje que en Studio mira a **−Z** sale en Blender mirando a **+Y** → hay que voltearlo. La detección automática por los pies falla con botas, faldas o mangas anchas (pasó con Miku).
- A veces **faltan piezas**: invisibles en Studio (pierna de palo) o tapadas por ropa en capas (antebrazos bajo unos calentadores). El rig les pone una pieza oculta para medir la articulación.
