# Roblox Studio → personajes del kit (exportar muchos de una vez)

Para cuando el usuario pone varios personajes en un lugar de Roblox Studio y pide "expórtalos y ponles rig".
Claude lo hace solo con el MCP de Roblox Studio + estos archivos (probado con 24 personajes el 2026-11-07).

| Archivo | Qué hace |
|---|---|
| `studio_personajes.luau` | Se pega una vez con `execute_luau`. `_G.CL_isolate("Nombre")` deja solo ese personaje en el Workspace (lo demás va a ServerStorage), `_G.CL_restore()` regresa todo, `_G.CL_datos()` da la posición de cada pieza y los accesorios en el orden del OBJ. Reversible: no borra ni guarda el lugar. |
| `exportar_obj.ps1` | Abre **Archivo › Exportar como .obj**, pega la ruta en el diálogo de Windows y guarda. No sobrescribe. |
| `sacar_animacion.luau` | `_G.CL_sacarAnim(modelo, nombre[, clip])` saca una animación a JSON (con `clip` = una de las guardadas en `RBX_ANIMSAVES`; también acepta un `KeyframeSequence`). |
| `partes_json.py` | Escribe `partes.json` en la carpeta del personaje: nombre real de cada grupo del OBJ, piezas que no vinieron y qué accesorios son ropa en capas. `armar_rig_r15_auto.py` lo usa solo. |

## Pasos
1. `list_roblox_studios` → elegir el lugar. Ver los personajes y en qué grupo van (A/B/C) según lo que diga el usuario o su imagen.
2. Pegar `studio_personajes.luau` con `execute_luau` (Edit).
   - **Si alguno es R6** (piezas `Torso`, `Left Arm`… sin codos ni rodillas): hacerle una copia R15 con
     `_G.CL_r6a15(modeloR6, "Nombre_R15", plantillaR15)` (plantilla = un R15 blocky del lugar) y exportar la copia.
     Lleva su ropa, colores, cara y accesorios. Borrar las copias al terminar. Probado con 5 personajes el 2026-11-10.
3. Por cada personaje: `_G.CL_isolate("Nombre")` y luego
   `powershell -STA -File Herramientas\roblox\exportar_obj.ps1 -Ruta "<kit>\Personajes\<nivel>\<Carpeta>\<Carpeta>.obj"`.
   Un personaje a la vez (aislar → exportar), nunca en paralelo.
4. **`_G.CL_restore()` al terminar** (y confirmar que no quedó `ServerStorage._TEMP_EXPORT_CLAUDE`).
5. `_G.CL_datos()` → guardar el JSON en un archivo → `py Herramientas/roblox/partes_json.py datos.json "NombreStudio=Personajes/<nivel>/<Carpeta>" ...`
6. Rig: `blender.exe -b --factory-startup --python Herramientas/blender/armar_rig_r15_auto.py -- "<carpeta>" <Carpeta>` (lee `partes.json`, ya sabe que debe voltearlo).

## Animaciones de Studio → Blender (2026-11-10, primera: el paso de Yamal)
1. En Studio, importar la animación al personaje con el Animation Editor (pegar el ID): crea un `CurveAnimation`
   dentro del personaje. También sirve un `KeyframeSequence` en `AnimSaves` o un objeto `Animation` con su ID.
2. Pegar `sacar_animacion.luau` con `execute_luau` y correr `_G.CL_sacarAnim(workspace.<Personaje>, "<Nombre>")`.
   Guardar el JSON en `Personajes/Animaciones/<Nombre>.json` (revisar que el número de keyframes coincida).
3. `blender -b <rig>.blend --python Herramientas/blender/animacion_roblox.py -- <Nombre>.json <salida>.blend [vueltas] [--empacar]`.
   Hornea un keyframe por fotograma (30 fps), apaga el IK y deja la acción `<Nombre>` lista para anexar a otros rigs.
   Desde un script de episodio: `animacion_roblox.aplicar(rig, animacion_roblox.cargar(json), inicio=f)`.
- Comprobado contra Studio en 2 poses (0,5 s y 2,5 s): mismas posiciones de brazos, cabeza y cadera.
- En modo edición, cambiar `Motor6D.Transform` **no mueve** las piezas: para comparar se hace una copia anclada y se
  calcula cada pieza con `Part1 = Part0 * C0 * Transform * C1⁻¹`.
- Roblox: giro Euler `XYZ` = `CFrame.fromEulerAngles` = Rx·Ry·Rz (en Blender, `Euler(..., 'ZYX')`).
- Las animaciones publicadas por otras personas no se pueden bajar (Roblox las bloquea). Las del juego que el usuario puso en
  su lugar (objetos `Animation` con su ID) sí bajaron con `KeyframeSequenceProvider` (EP012: el ataque del ciervo).

## R6 sin plantilla R15 en el lugar (2026-11-11, EP012: 4 niños y el encapuchado)
1. `_G.CL_r6a15(modeloR6, "Nombre", nil, offset, tipos)`: con `nil` crea el R15 con `CreateHumanoidModelFromDescription`,
   toma el tamaño del R6 (niños de torso 1,2) y vuelve Accessory también las piezas de sus Models (capa, máscara).
2. Exportar **dos veces** con `-Espera 5` (la primera a una carpeta temporal): Studio arma la textura de la ropa y la cara
   después de la primera exportación. El `.mtl` debe tener la textura del cuerpo (916×568) en las 15 piezas.
3. Rig normal (`armar_rig_r15_auto.py`) y luego la cara: la cabeza R15 nueva pinta mal las calcomanías, así que en Blender
   se cambia por una cabeza clásica con la cara del kit: `caras_textura.preparar(rig, cara=N, cabeza_clasica=<malla Calvo_Head>)`
   (ver `Episodios/EP012_.../scripts/caras_ep012.py`). Para **conservar su cara de Roblox**: exportar una copia con la cabeza R6
   (ahí la cara sale limpia en la textura del cuerpo) y darle a la cabeza clásica el material del cuerpo con esa textura
   (`scripts/cara_original_encapuchado.py`).

## Modelos con esqueleto propio: ciervo, monstruos, animales (2026-11-11)
1. `_G.CL_juntas(workspace.<Modelo>)` → `juntas.json` en la carpeta del personaje (piezas, Motor6D con C0/C1, soldaduras).
2. Aislar (`CL_isolate` ya acepta modelos sin Humanoid, herramientas y escenarios) y exportar el `.obj` en la misma carpeta.
3. Animaciones guardadas → `<carpeta>/animaciones/<Nombre>.json` (`CL_sacarAnim(modelo, "Nombre", "Walk Ciervo")`).
4. `blender -b --factory-startup --python Herramientas/blender/rig_motor6d.py -- "<carpeta>" <Nombre>` → `<Nombre>_Rig.blend`
   con un hueso por articulación y las animaciones como acciones. Desde un episodio:
   `animacion_roblox.aplicar_motor6d(rig, animacion_roblox.cargar(json), inicio=f, repeticiones=n)`.

## Por qué así (lo aprendido)
- **"Exportar como .obj" exporta TODO el lugar**, no la selección (en esta versión no hay "Exportar selección" en los menús). Por eso se aísla cada personaje.
- **Orden del OBJ** = orden inverso de `GetDescendants()` del modelo, sin las piezas invisibles. Los nombres de grupo (`Crush1…Crush15`, `Handle1…`) no dicen qué pieza es; el número cambia en cada avatar.
- **Coordenadas del OBJ = coordenadas del mundo de Studio** (Blender: x, −z, y). Por eso las piezas se empatan por posición. Si el personaje se movió después de exportarlo, `partes_json.py` resta el centro.
- Un personaje que en Studio mira a **−Z** sale en Blender mirando a **+Y** → hay que voltearlo. Si mira a **+Z** no se voltea
  (`partes.json` dice `no_voltear`). Hasta el 2026-11-10 el armador leía mal ese `no_voltear` y los dejaba de espaldas: ya corregido.
- **R6 → R15**: el rig del kit necesita las 15 piezas R15. Las camisas y pantalones clásicos se ven igual en el cuerpo R15 blocky;
  solo se pierde el `CharacterMesh` del R6 (forma de torso de paquete viejo). Los `Hat` viejos sí salen en el OBJ: `CL_datos` ya los cuenta. La detección automática por los pies falla con botas, faldas o mangas anchas (pasó con Miku).
- A veces **faltan piezas**: invisibles en Studio (pierna de palo) o tapadas por ropa en capas (antebrazos bajo unos calentadores). El rig les pone una pieza oculta para medir la articulación.
