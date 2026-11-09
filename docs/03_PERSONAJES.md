# 03 — Personajes y rigs

Carpetas por nivel (ver `Personajes/LEEME.md`): `Protagonista/` (A) · `Secundarios/` (B) · `Pueblo_NPC/` (C).

## Receta: "ya subí a <Nombre>, ponle su rig"
Hacerlo directo, sin explicaciones largas (ya está probado con Crista). Pasos:
1. **Revisar la carpeta** `Personajes/<nivel>/<Nombre>/`: `.obj` + `.mtl` + `.png` (y `Accesorios/` si vienen aparte). Si falta la textura o el `.obj`, decirlo en una línea.
2. **Listar los grupos del OBJ** en Blender de fondo (nombre, centro y tamaño de la caja de cada grupo, ya con `matrix_world` aplicado) y armar el mapa:
   - 15 piezas R15: la cabeza es la más alta; torso superior/inferior por altura; brazos a los lados (mano = la pieza más baja del brazo); piernas abajo (pie = la más baja).
   - *Right* = lado derecho del personaje = **−X** cuando mira a −Y.
   - Lo demás son **accesorios** → hueso más cercano: cabello/sombrero → `Head`; mochila/cuello/capa → `UpperTorso`; falda/cinturón → `LowerTorso`.
3. **Automático (recomendado)**: `blender.exe -b --factory-startup --python Herramientas/blender/armar_rig_r15_auto.py -- "<carpeta del personaje>" <Nombre> [voltear|no_voltear]` (≈5 s). Importa todos los `.obj` de la carpeta (y su subcarpeta de accesorios), **centra** el modelo, lo **voltea** si mira a +Y, reconoce las 15 piezas y pega los accesorios. Revisar en la salida el mapa que imprime.
   - **Con `partes.json`** (lo crea `Herramientas/roblox/partes_json.py` desde Studio): usa los nombres reales de cada pieza, sabe si hay que voltearlo y crea piezas **ocultas** para las que no vinieron en el OBJ (invisibles o tapadas por ropa en capas). Sin él, adivina por posición (falla con cuerpos angostos como niñas, o si falta una pieza).
   - Si el giro sale mal (la foto `frente` muestra la espalda), repetir con `voltear` o `no_voltear`. Exportado desde Studio con el personaje mirando a −Z → `voltear`.
   - **Accesorios**: cada vértice se compara con la pieza del cuerpo más cercana. ≥ 85 % junto a una pieza → rígido a ese hueso (zapatos, mochila, sombrero). Ropa en capas de Roblox (WrapLayer: chamarras, mangas, calentadores) que cubre varias piezas → **se deforma** con los huesos (modificador Armature, colección `Acc_Ropa_*`). Cabello, sombreros y caras → `Head`; cuello, hombro, frente y espalda → `UpperTorso`; cintura → `LowerTorso` (según el tipo de accesorio de Studio o, si es "Unknown", si llega a la mitad de arriba de la cabeza).
   - **Muchos personajes desde Roblox Studio** (exportar, nombrar carpetas y riguear todos): guía en `Herramientas/roblox/LEEME.md`.
   - Manual (si el automático falla): copiar `armar_rig_r15_plantilla.py` como `build_<nombre>_rig.py`, cambiar `Crista` por el nombre y llenar `PARTS` y `ACC`.
4. Resultado: `<Nombre>_R15_Rig.blend` + `previews/` (frente, lado, espalda, pose de prueba).
5. **Revisar las fotos** (piezas en su lugar, nada flotando ni separado al doblar; materiales con la salida conectada, ver lección de caras negras). Corregir y repetir si hace falta.
6. **No borrar** lo que subió el usuario. Si ya existía un `<Nombre>_R15_Rig.blend`, moverlo a `Respaldos/<Nombre>_rig_<fecha>.blend` antes de crear el nuevo.
7. Anotar en `MI_CANAL.md` (reparto: estado "rig listo", altura, rig) y responder corto: *"Listo: <Nombre> ya tiene rig → `<ruta>`"* + una foto de `previews/`.

## Caras (expresiones)
- **Método recomendado (cabeza clásica, ej. Lila y Coco): cara en la textura**, sin planos encima. `Herramientas/blender/caras_textura.py` le da a la cabeza un material propio: piel + la cara elegida, pintada de frente sobre toda la cara de la cabeza (tamaño aprobado por el usuario; `zona="frente"` la hace más chica), y borra la cara de fábrica. La sonrisa de siempre (15) está reducida a su tamaño original. La cara se elige con la propiedad **`cara`** del rig (número de `Caras/Emociones/_secuencia/caras.json`: 1 molesto · 2 sorpresa · 3 pícaro · 4 confundido · 5 risa · 6 triste · 7 asustado · 8 muy feliz · 9 nervioso · 10 preocupado · 11 incrédulo · 12 bostezo · 13 indignado · 14 asombro · 15 sonrisa de siempre) y se anima con keyframes (cambio seco: valor viejo en f−1, nuevo en f).
- Para agregar emociones: poner el PNG (fondo transparente) en `Caras/Emociones/` y regenerar la secuencia (`cara_####.png`, 1024 px) con su número en `caras.json`.
- **Excepciones (no se cambia la cara)**: cabezas con cara de máscara, dinámicas o dibujadas (ej. Crista "la payasita", Raul y Ajolota del mantenedor; el personaje de Yuyo con máscara gigante). Se respetan tal cual, salvo que su dueño pida cambiarlas; sus emociones se cuentan con poses, efectos (burbujas, gotas de sudor, nubes, destellos) y sonido. Anotar en `MI_CANAL.md` qué personajes son excepción.
- Cada personaje que sí cambia: elegir su cara en **cada toma** según la emoción del momento (tabla `CARAS` en el script de animación) y regresar a su cara de siempre cuando pasa la emoción.
- Origen: `Personajes/<nivel>/<Nombre>/caras/` (prioridad) o `Caras/` (`feliz.png`, `enojado.png`, `asombro.png`…; paquetes en `Caras/Paquete_*`).
- Método (como Sikelpa): un plano por expresión al frente de la cabeza, emparentado al hueso `Head`, material con transparencia; se cambia la cara con keyframes de visibilidad (`hide_render` + `hide_viewport`) en el fotograma de la emoción.
- Si la cara viene pintada en la textura del cuerpo (Crista), es fija: para hacerla intercambiable hay que tapar la cara de la textura y usar los planos.
- Elegir la emoción según el guion (ej. "¡y ya iba tarde!" → asombro/miedo). Si falta una emoción, buscar en los paquetes y preguntar.

## Quién sale y cuánto (reparto)
- Usar **siempre** el reparto de `MI_CANAL.md`. Nunca personajes al azar.
- Tiempo en cámara según nivel: **A** más tiempo y primeros planos; **B** cuando la historia lo pide (planos medios, algunos primeros planos); **C** de fondo. Excepción: el usuario pide enfocar a alguien en particular.
- **NPC con nombre** (siguen siendo nivel C, gente del pueblo): si la historia nombra a alguien que no está en el reparto (ej. "Valentina, la vecina", "Valeria, la panadera"):
  1. Buscar el nombre en `MI_CANAL.md` → *NPC con nombre*. Si ya existe, usar **el mismo modelo y colores**, sin preguntar.
  2. Si es nuevo: elegir de `Pueblo_NPC/` un modelo que encaje (edad, ropa) y que no tenga otro nombre; mostrar **una foto de frente** y preguntar: *"¿Quieres que esta sea Valentina?"*.
  3. Solo cuando el usuario confirme: registrarlo en la tabla (nombre, quién es, carpeta, colores, foto `previews/frente.png`, episodio). Desde ahí, Valentina es siempre ese modelo en todos los proyectos.
  4. Nunca registrar nombres de ejemplo ni inventados por Claude sin confirmación.
- **Subir de nivel**: si el usuario dice "esta es mi hermana, ponle rig y agrégala como secundaria", el personaje va a `Secundarios/<Nombre>/` (receta de rig) y se anota en el reparto con nivel B. Si ya era un NPC con nombre, mover su carpeta (no copiar ni borrar) y actualizar ambas tablas.

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

## Poses guardadas (en grados)
- **Sentado en el sillón** (Coco/Lila, EP002): UpperLeg X 86 · LowerLeg X −70 · Foot X −10 · UpperTorso X −5; HRP z = (asiento + 0,45) − (piso + altura de cadera). Manos en los muslos: UpperArm (16,0,±8) · LowerArm 58.
- **Acostado → se sienta en la cama**: HRP X de −90 a 0 mientras UpperLeg X va de 0 a 90 (las piernas no se mueven); origen del rig = cobija + 0,62 − altura del HRP.
- **Manos en las sienes / mano en la barbilla / secreto al oído**: calcularlas con `resolver_mano` (ver `Episodios/EP002_Lo_Que_Piensas/scripts/animar_bloque1.py`).

### Crista
- **Amarrarse la agujeta** (rodilla izquierda al piso, pie derecho adelante): HRP z −0,76 · RightUpperLeg (86,0,4) · RightLowerLeg −86 · RightFoot 13 · LeftUpperLeg (−12,0,−3) · LeftLowerLeg −78 · UpperTorso 34 · Head 30 · RightUpperArm (35,0,35) · RightLowerArm 10 · LeftUpperArm (30,0,−60) · LeftLowerArm 10. Movimiento de amarrar: ±12° antebrazos y ±15° manos a 2,3 Hz, alternados.
- **Tocar la puerta** (brazo derecho): RightUpperArm (82,0,12) · RightLowerArm 62 − 22·golpe · RightHand −18. Golpes como pulsos gaussianos (ancho 2,2 fotogramas).

## Personajes de cada usuario
La lista de personajes listos (archivo, altura, rig, notas) va en `MI_CANAL.md`. Las poses de arriba se midieron con el rig de la plantilla (altura ≈4,4); en personajes más altos o bajos, escalar la bajada de cadera (`HRP z`) proporcionalmente.
