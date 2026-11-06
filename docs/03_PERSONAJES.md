# 03 — Personajes y rigs

Carpetas por nivel (ver `01_Personajes/LEEME.md`): `1_Protagonista/` (A) · `2_Secundarios/` (B) · `3_Pueblo_NPC/` (C).

## Receta: "ya subí a <Nombre>, ponle su rig"
Hacerlo directo, sin explicaciones largas (ya está probado con Crista). Pasos:
1. **Revisar la carpeta** `01_Personajes/<nivel>/<Nombre>/`: `.obj` + `.mtl` + `.png` (y `Accesorios/` si vienen aparte). Si falta la textura o el `.obj`, decirlo en una línea.
2. **Listar los grupos del OBJ** en Blender de fondo (nombre, centro y tamaño de la caja de cada grupo, ya con `matrix_world` aplicado) y armar el mapa:
   - 15 piezas R15: la cabeza es la más alta; torso superior/inferior por altura; brazos a los lados (mano = la pieza más baja del brazo); piernas abajo (pie = la más baja).
   - *Right* = lado derecho del personaje = **−X** cuando mira a −Y.
   - Lo demás son **accesorios** → hueso más cercano: cabello/sombrero → `Head`; mochila/cuello/capa → `UpperTorso`; falda/cinturón → `LowerTorso`.
3. Copiar `04_Herramientas/blender/armar_rig_r15_plantilla.py` como `build_<nombre>_rig.py` en la carpeta del personaje; cambiar `Crista` por el nombre y llenar `PARTS` y `ACC`.
4. Ejecutar: `blender.exe -b --factory-startup --python build_<nombre>_rig.py` (≈1 min) → `<Nombre>_R15_Rig.blend` + `previews/` (frente, lado, espalda, pose de prueba).
5. **Revisar las fotos** (piezas en su lugar, nada flotando ni separado al doblar; materiales con la salida conectada, ver lección de caras negras). Corregir y repetir si hace falta.
6. **No borrar** lo que subió el usuario. Si ya existía un `<Nombre>_R15_Rig.blend`, moverlo a `99_Archivo/<Nombre>_rig_<fecha>.blend` antes de crear el nuevo.
7. Anotar en `MI_CANAL.md` (reparto: estado "rig listo", altura, rig) y responder corto: *"Listo: <Nombre> ya tiene rig → `<ruta>`"* + una foto de `previews/`.

## Caras (expresiones)
- Origen: `01_Personajes/<nivel>/<Nombre>/caras/` (prioridad) o `05_Recursos/Caras/` (`feliz.png`, `enojado.png`, `asombro.png`…; paquetes en `Caras/Paquete_*`).
- Método (como Sikelpa): un plano por expresión al frente de la cabeza, emparentado al hueso `Head`, material con transparencia; se cambia la cara con keyframes de visibilidad (`hide_render` + `hide_viewport`) en el fotograma de la emoción.
- Si la cara viene pintada en la textura del cuerpo (Crista), es fija: para hacerla intercambiable hay que tapar la cara de la textura y usar los planos.
- Elegir la emoción según el guion (ej. "¡y ya iba tarde!" → asombro/miedo). Si falta una emoción, buscar en los paquetes y preguntar.

## Quién sale y cuánto (reparto)
- Usar **siempre** el reparto de `MI_CANAL.md`. Nunca personajes al azar.
- Tiempo en cámara según nivel: **A** más tiempo y primeros planos; **B** cuando la historia lo pide (planos medios, algunos primeros planos); **C** de fondo. Excepción: el usuario pide enfocar a alguien en particular.
- **NPC con nombre** (siguen siendo nivel C, gente del pueblo): si la historia nombra a alguien que no está en el reparto (ej. "Valentina, la vecina", "Valeria, la panadera"):
  1. Buscar el nombre en `MI_CANAL.md` → *NPC con nombre*. Si ya existe, usar **el mismo modelo y colores**, sin preguntar.
  2. Si es nuevo: elegir de `3_Pueblo_NPC/` un modelo que encaje (edad, ropa) y que no tenga otro nombre; mostrar **una foto de frente** y preguntar: *"¿Quieres que esta sea Valentina?"*.
  3. Solo cuando el usuario confirme: registrarlo en la tabla (nombre, quién es, carpeta, colores, foto `previews/frente.png`, episodio). Desde ahí, Valentina es siempre ese modelo en todos los proyectos.
  4. Nunca registrar nombres de ejemplo ni inventados por Claude sin confirmación.
- **Subir de nivel**: si el usuario dice "esta es mi hermana, ponle rig y agrégala como secundaria", el personaje va a `2_Secundarios/<Nombre>/` (receta de rig) y se anota en el reparto con nivel B. Si ya era un NPC con nombre, mover su carpeta (no copiar ni borrar) y actualizar ambas tablas.

### Por qué este tipo de rig
Roblox mueve **piezas rígidas** unidas por articulaciones. De los Starter Rigs, el `blockyr15` es el único con esa lógica (los demás deforman una malla propia). Construimos un rig con **la misma estructura y nombres R15**, pero con las articulaciones medidas sobre el modelo real, así no se separan piezas al animar.

## Estructura del rig (Crista)
```
Root (piso) → HumanoidRootPart (cadera, mueve todo el cuerpo)
  └ LowerTorso → UpperTorso → Head
                 ├ RightUpperArm → RightLowerArm → RightHand   (igual Left)
                 └ RightUpperLeg → RightLowerLeg → RightFoot   (cuelgan de LowerTorso)
Controles IK (cubos/esferas): IK_Pie.R/L, Polo_Rodilla.R/L, IK_Mano.R/L, Polo_Codo.R/L
Propiedades del objeto Crista_Rig: IK_Piernas (1 = pies fijos), IK_Brazos (0 = FK)
```
Las piezas del cuerpo y los accesorios están **emparentadas al hueso** (rígidas, como Roblox).

## Ejes de rotación (rig propio, medido)
| Hueso | X+ | Y | Z+ |
|---|---|---|---|
| Brazos (Upper/Lower) | hacia **adelante** | giro sobre su eje | derecho: **hacia adentro** · izquierdo: **hacia afuera** |
| Piernas (Upper) | hacia **adelante** | — | lateral |
| LowerLeg (rodilla) | **negativo = doblar** (espinilla atrás) | — | — |
| Pie | punta **arriba** | — | — |
| UpperTorso | inclina **adelante** | **torcer** (twist) | inclina de lado |
| Cabeza | mira **abajo** | **voltear** izquierda/derecha (signo: calcular `HEAD_LEFT`) | ladear |
| HumanoidRootPart | — | balanceo lateral (roll) | giro de cadera; **location.z** sube/baja el cuerpo |

> Los rigs hechos sobre el Starter `Blocky Rig` (ej. Sikelpa) tienen ejes distintos: X+ de brazos/piernas = **hacia atrás**. Medir antes de animar.

## Ciclos de movimiento (FK) — parámetros que funcionaron
`fase` avanza `2π · velocidad / longitud_ciclo / 30` por fotograma.

| Parámetro | Caminar | Correr |
|---|---|---|
| Velocidad (unid/s) | 4,5–5,5 | 11–12 |
| Longitud de ciclo | 3,0 | 4,6 |
| Muslo ±A | 26° | 40° |
| Rodilla K (al pasar) | 38° | 62° |
| Brazos ±B | 26° | 72° |
| Antebrazo | 14° (+16 al frente) | 80° (+16) |
| Inclinación torso | 3° | 16° |
| Torsión torso / cadera | 7° / 1,5° | 13° / 4,5° |
| Rebote cadera | 0,05 | 0,24 + balanceo lateral 0,07 |

Bajada de cadera para que el pie no flote: `−L·(1 − cos(A·sin(fase)))`, con L = largo de pierna (Crista 1,67).
Pisadas (para sonido): cuando la fase cruza `π/2 + k·π`.

## Poses guardadas (Crista, en grados)
- **Amarrarse la agujeta** (rodilla izquierda al piso, pie derecho adelante): HRP z −0,76 · RightUpperLeg (86,0,4) · RightLowerLeg −86 · RightFoot 13 · LeftUpperLeg (−12,0,−3) · LeftLowerLeg −78 · UpperTorso 34 · Head 30 · RightUpperArm (35,0,35) · RightLowerArm 10 · LeftUpperArm (30,0,−60) · LeftLowerArm 10. Movimiento de amarrar: ±12° antebrazos y ±15° manos a 2,3 Hz, alternados.
- **Tocar la puerta** (brazo derecho): RightUpperArm (82,0,12) · RightLowerArm 62 − 22·golpe · RightHand −18. Golpes como pulsos gaussianos (ancho 2,2 fotogramas).

## Personajes de cada usuario
La lista de personajes listos (archivo, altura, rig, notas) va en `MI_CANAL.md`. Las poses de arriba se midieron con el rig de la plantilla (altura ≈4,4); en personajes más altos o bajos, escalar la bajada de cadera (`HRP z`) proporcionalmente.
