# 04 — Escenarios

## Pueblo (`Escenarios/Pueblo/Pueblo_set.blend`)
Escala: 1 unidad ≈ 1 stud de Roblox (personaje ≈ 4,5–5,6). Norte = **+Y**. Construido con los scripts de `Escenarios/Pueblo/scripts/` en este orden:
`build_pueblo.py` → `add_faroles.py` → `add_centro.py` → `mejoras_v3.py` → `mejoras_v4.py` → `colinas_anillo.py` → `escuela.py`.

### Mapa (coordenadas del mundo)
| Zona | Ubicación |
|---|---|
| Calle principal | carretera x ±8, y −30…264 · banquetas x ±8…±13 (altura 0,3) · asfalto altura 0,07 |
| Casas de la calle | x ±29,5 (frente hacia la calle), y = 0, 26, 52… 260 (11 por lado). Buzones en banqueta x ±11,9 (y casa+2,6) |
| Faroles de la calle | x ±8,9, y −13, 39, 91, 143, 195, 247 (foco 4200 W) |
| Tramo conector | y 264…332, casas anchas en y 286 y 312 (x ±29,5), faroles en (±8,9, 299) |
| Glorieta | cuadrada, eje a ±40 del centro (0, 380), calzada de 16 de ancho |
| Plaza | 64×64 centrada en (0, 380), piso 0,36 · fuente r 7,5 en el centro · 4 bancas a r 14,5 (diagonales) · carrito de nieves (−8,5, 358,5) |
| Tiendas | Panadería y Barbería (x −64), Abarrotes y Cafetería (x +64), y 354 y 391 |
| Calle norte | y = 420, x ±48…±300, banquetas y 407…412 y 428…433 |
| Presidencia | explanada y 433…455 (altura 0,3) con tarima y podio en (0, 442) · escalones y 453…458,6 (alturas 0,5/1,0/1,5) · pórtico con columnas en x ±4,6 / ±12 / ±19,5 / ±26,5, y 461,4 · **puerta** en (0, 465,6), porche a altura 1,5 · reloj en la torre (manecillas `Reloj_Horario`/`Reloj_Minutero`, girar en Y) |
| Escuela | vacío `Escuela` en (−188, 362), girada 180° (frente a la calle norte, fachada en y 388). Pasillo 16 de ancho con 68 lockers, 2 salones, 2.º piso decorativo, cancha al oeste. Ocultar `Escuela_Techo*` para ver adentro |
| Estanque | (−205, 150), r ≈ 36, con muelle |
| Colinas | anillo alrededor de (0, 250), de r 600 a 1600; más colinas al norte (y > 560) |

### Cosas animables ya preparadas
- **Cortinas** de cada casa/tienda: propiedad `cortinas` del objeto (0 abiertas, 1 cerradas).
- **Reloj** de la presidencia (rotación Y de las manecillas).

## Pueblo_v2 — interiores (en prueba, `Escenarios/Pueblo_v2/`)
Se construye sobre una copia del Pueblo con `Escenarios/Pueblo/scripts/interiores.py` y `presidencia_interior.py` (piezas comunes en `util_interiores.py`).
| Lugar | Dónde | Notas |
|---|---|---|
| Casa de Sikelpa y Ajolota | `CasaAncha_02` (29,5, 286), mira a la calle (−x) | Ancha y **alargada hacia atrás** (fachada igual). Interior 19,2 × 16,7: sala con tele, comedor, cocina con barra, escalera; arriba el cuarto de los hermanos (2 camas) |
| Casa de Lila | `CasaAncha_01` (−29,5, 286), frente a la de Sikelpa | Igual de grande; tonos morado/verde agua; cuarto con tocador y librero de "pociones" |
| Presidencia PB | vestíbulo z 1,5 | Piso de ajedrez, alfombra roja, escalera central (y 474–486), retratos, banderas, INFORMES, maqueta del pueblo, candil |
| Presidencia 2.º piso | z 10,8 | **Despacho del alcalde = ala derecha completa** (x 12–27, y 467–489); cabildo en el ala izquierda; secretaría al frente |
| Torre del reloj | z 22 | Engranes (`Pres_Engrane*`, girar en Y local), péndulo (`Pres_Pendulo`), campana; se ve la carátula por detrás |
- **Parque de la Fortuna** (`Escenarios/Pueblo_v2/scripts/parque_fortuna.py`, repetible; colección `Parque_Fortuna`): al este del centro, x 142–230, y 300–404, entrada por la calle norte en (186, 404). Como un parque real (por ahora la única atracción es la rueda): arco con letrero, taquillas y torniquetes, avenida con 4 puestos (Galletas de la fortuna, Algodones, Palomitas, Tiro al blanco) y guirnaldas, área de mesas con sombrillas (x ≈ 157–166, y 378–389), plaza redonda (centro (186, 352), r 21) con jardineras de flores, bancas largas (asiento z 1,68) y la fila con vallas frente al andén.
  - **Rueda de la fortuna**: centro (186, 326), eje a z ≈ 29,4, radio de pivotes 17; 10 cápsulas grandes (caben dos sentados con espacio, frente abierto para ver las caras) que miran al norte (+Y). Gira con el vacío `Rueda_Giro` (rotación Y, en radianes; las cápsulas se quedan derechas solas). `Rueda_Cabina_01` (rosa) es la de la pareja: con `Rueda_Giro` = 0 está arriba, piso z 35,6, centro (186, 330,3); propiedades `piso_z_local` y `asiento_z_local`. Andén a z 1,6 con escaleras al norte.
  - **Luces**: `Parque_Control["luces"]` (0,25 de día … 1 de noche) maneja los LED de arcoíris de los rayos, focos, letreros, la luz dentro de la cápsula 01 y las luces del parque.
- Gente de fondo: `Herramientas/blender/extras_npc.py` (anexa NPC y los deja atendiendo, sentados platicando, formados o comprando).
- Puertas: girar en Z `CasaAncha_0X_PuertaBisagra` y `Pres_PuertaIzq/Der_Bisagra` (≈1,6 rad = abierta).
- Coordenadas de las casas: **locales** de su vacío (frente hacia −Y; planta baja z 1,0; 2.º piso z 9,4).
- Fotos de revisión de cualquier escenario: `Herramientas/blender/fotos_escenario.py` (cámaras temporales, también de noche).

## Cielo decorativo (`Herramientas/blender/cielo.py`)
- **De día**: azul con degradado (más intenso arriba), nubes blancas esponjosas que avanzan despacito y un **sol blanco grande con brillo suave** (bloom pintado en el cielo: no se ve el borde del círculo y el cielo se despeja a su alrededor), del lado de donde viene la luz del Sol del mapa, a 26° sobre el horizonte. **De noche**: azul muy oscuro con estrellas.
- **Solo lo ve la cámara**: la luz y el brillo del mapa salen del `Background` de siempre, así que no cambian (medido en el Pueblo: diferencia promedio 0,26 de 765 en los píxeles del mapa). El sol no da rayos ni luz.
- **Cambia solo a noche**: cuando un episodio oscurece el color del `Background` (como la toma de la colina de EP002), el cielo pasa a estrellas sin hacer nada más.
- Ponerlo: `blender.exe -b mapa.blend --python Herramientas/blender/cielo.py -- --guardar` (o en el Blender abierto: `py Herramientas/blender/bl.py Herramientas/blender/cielo.py`). Se puede repetir: rehace solo sus nodos (`Cielo_…`). Ajustes desde un script: `cielo.poner(escena, nubes=0.55, estrellas=1.0, sol=True, sol_altura=26)`; quitarlo: `cielo.quitar(escena)`.
- Ya está puesto en `Pueblo_v2` (los episodios nuevos lo traen de una vez: solo cambian la historia y los personajes) y en EP002.
- **En los scripts de episodio** que hacen día/noche con keyframes: usar el `Background` que **no** empieza con `Cielo_` (el que ilumina) y **no** llamar `animation_data_clear()` del mundo (borraría los drivers del cielo): solo `w.node_tree.animation_data.action = None` antes de poner los keyframes.

## Cómo agregar un escenario nuevo
Crear `Escenarios/<Nombre>/` con `scripts/` (construcción repetible) y guardar un `<Nombre>_set.blend` limpio. Documentar aquí su mapa.
