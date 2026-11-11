# 02 — Lecciones aprendidas (errores y soluciones)

Agregar aquí cada error nuevo con su solución. Formato: **Problema → Causa → Solución**.

## Cámaras y tomas
1. **Algo tapaba al personaje en el video** (columna, poste, tarima). → No se revisó cada fotograma. → Correr `revisar_camaras.py` (rayos + rejilla) y hojas de contacto por toma **antes** de renderizar.
2. **Dron encima de las casas, no se entendía a quién seguir.** → Cámara muy alta/lejos. → Dron a media altura sobre la calle, frente al personaje, bajando y retrocediendo mientras él se acerca.
3. **Cámaras demasiado pegadas** (solo se veían piernas/cabello). → Distancia < 4 unidades con lente normal. → Para cuerpo completo: 6–8 unidades, ángulo vertical 40–46°. Primeros planos de cara: 3–4,5 unidades, 28–34°.
4. **Render de prueba salió con otra cámara.** → Los marcadores con cámara cambian la cámara activa al renderizar. → Desvincular `marker.camera` temporalmente para fotos de depuración.
5. **Transición "algo tapa la cámara"**: colocar la cámara a 0,45 unidades detrás de un poste, en línea con el personaje (el poste llena el cuadro). La toma siguiente empieza tapada por el mismo tipo de objeto y la cámara se desliza para revelar.
6. **La cámara chocaba con el personaje al pasar corriendo.** → Cámara fija. → Que la cámara retroceda con él (más lento que el personaje) para acercarse sin chocar.
7. **Cámara que gira con el personaje se veía brusca.** → Usar la orientación promediada (±10 fotogramas) del personaje para colocar la cámara.

## Poses y rig
8. **Al inclinar el torso las piernas se iban hacia atrás.** → En R15 las piernas cuelgan de `LowerTorso`. → Inclinar con `UpperTorso` (y cabeza); dejar `LowerTorso` casi en 0.
9. **Rodillas "deformadas"** (bloques encimados). → Las piezas blocky R15 se traslapan ~0,4 en la rodilla. → Evitar flexiones de rodilla > 85°, preferir poses donde la parte encimada quede contra el piso o fuera de cámara.
10. **Las manos no llegaban al zapato.** → Ángulos puestos a ojo. → Usar `resolver_pose_brazos.py`: busca los ángulos de brazo que llevan la mano a un punto (error < 0,15).
11. **Controles de cortinas/IK no respondían.** → Los drivers creados por script a veces quedan marcados como inválidos y tienen keyframes. → Borrar keyframes del fcurve del driver y reasignar `driver.expression`.
12. **El importador OBJ dejó las piezas giradas** y la "subida" al piso se aplicó en el eje equivocado. → Aplicar `matrix_world` a la malla primero (`mesh.transform(...)`, luego `matrix_world = Identity`).
13. **Pose de prueba exagerada.** → No se conocían los ejes del rig. → Medir con un script (rotar 60° y ver a dónde se mueve la mano) y anotar los ejes en `03_PERSONAJES.md`.

## Materiales y render
14. **Colores lavados/grises.** → Blender espera colores lineales. → Convertir hex sRGB → lineal (`lin()` en los scripts).
15. **Caras nuevas salían negras.** → El material no estaba conectado a la salida (`BSDF → Material Output`). → Revisar enlaces al crear materiales por script.
16. **El vidrio no dejaba ver cortinas/interiores.** → Reflejo de cielo (IOR 1,5). → `IOR 1,05`, `Specular IOR Level 0,15`, `alpha 0,12`.
17. **Franjas o triángulos que parpadean** (z-fighting). → **Medido en Eevee 5.2 (2026-11-08, prueba B)**: la causa son caras **exactamente al ras** (separación 0: duplicadas, carteles pegados sin separar, dos cajas con la tapa al mismo nivel); con la cámara en movimiento se rompen en triángulos distintos cada cuadro, cerca o lejos. Separaciones de 0,01 m o más no fallaron ni a 150 m (de frente ni rasante); 0,001–0,003 m fallan a 100–150 m. Dos objetos idénticos en el mismo lugar no parpadean, pero se ve la copia equivocada. **Caso real**: el agua de la fuente del Pueblo (`Fuente_Agua1`) está al ras de su taza (`Fuente_Taza1`, z 6,56) → franjas diagonales que cambian cada cuadro en tomas cerca de la fuente (`Analizador/Resultados/Investigacion_2026-11-08/B_zfighting/hoja_fuente_cuadro_a_cuadro.jpg`); con el agua 1 cm más arriba queda lisa. → Antes de renderizar, correr `Herramientas/blender/detectar_superficies.py` (1–2 s). Arreglo que conserva la forma: borrar el duplicado; carteles/líneas/calcomanías separados 0,01–0,05; la caja de encima 0,01 más arriba. Subir `clip_start` a 0,5 solo ayuda con separaciones < 0,005 (no arregla el caso 0).
18. **"Buffer de sombras lleno"** en Eevee. → Muchas luces. → `eevee.shadow_pool_size = '1024'`.
19. **Cabello/accesorios con transparencia** → material en modo `DITHERED` y conectar `Alpha` de la textura.
20. **El techo de una casa/edificio tapaba el interior** en vistas aéreas → nombrar todo lo de arriba con un prefijo (`Escuela_Techo_*`) para ocultarlo de un golpe.

## Audio y edición
21. **Voz desfasada de la acción.** → Se puso el audio completo de corrido. → Pedir a ElevenLabs los tiempos por letra y mover cada frase al inicio de su toma (`NEW_START`); alargar la última toma si la última frase no cabe.
22. **Demasiados efectos.** → Preferencia del usuario: pocos y con sentido (ambiente suave, pasos, whoosh de transición, golpes, tensión final), y bajar efectos cuando habla la voz (ducking).

## Trabajo con Blender / Claude
23. **Blender bloqueado** durante renders. → Render dentro del Blender del usuario. → Guardar copia y renderizar con `blender.exe -b` en segundo plano.
24. **El usuario "ya no veía nada"**: había ocultado todas las colecciones (Ctrl+clic en el ojo) y apagado overlays. → `Alt+H`, encender ojos en el Outliner, `Shift+Alt+Z` para overlays. Encuadrar: `.` del teclado numérico (equivale a la F de Roblox Studio), vista frontal `1`.
25. **Scripts largos con rutas Windows** fallan dentro de heredocs de bash (escapes `\U`). → Escribir los scripts con la herramienta de archivos, no con heredoc.
26. **Claves de API pegadas en el chat** → no usarlas; pedir que se cambien y se guarden como variable de entorno.
27. **OpenCV/PySceneDetect no abren videos con emojis o acentos en el nombre** ("BÚNKER 😭.mp4"). → El analizador trabaja sobre una copia liviana con nombre simple (`proxy.mp4`) que crea con FFmpeg (que sí acepta esos nombres).
28. **Detección de cortes cuenta transiciones como cortes extra** (en EP001 detectó 13 en vez de 11 por el poste que tapa). → Confirmar cortes con hoja de contacto y ajustar el umbral (`ContentDetector(threshold=…)`).
29. **Personaje sin cara (cabeza dinámica de Roblox).** La piel viene transparente en la textura y Roblox la rellena con el color de la pieza (`Kd` del `.mtl`); si el alfa de la textura se conecta tal cual, la cabeza queda hueca. → En las 15 piezas del cuerpo: color = mezcla(Kd, textura, alfa de la textura) y alfa = 1 (ya lo hace `armar_rig_r15_auto.py`).
30. **Personajes en rosa (magenta) en una prueba.** → La copia del `.blend` estaba en otra carpeta y las texturas se guardan con ruta relativa. → Hacer las copias de prueba/render **en la misma carpeta** que el `.blend` del episodio.
31. **El calculador de brazos daba poses retorcidas** (brazo hacia atrás) cuando el objetivo estaba pegado al cuerpo (manos en los muslos, pan en el pecho). → El calculador solo busca la distancia más corta. → Usarlo para alcanzar cosas lejos del cuerpo (barbilla, sienes, atrapar); poses de descanso con ángulos directos.
32. **Un accesorio del episodio (sombrero) apareció flotando al repetir el guion de animación.** → En la segunda corrida el sombrero ya estaba pegado a la cabeza y el guion lo midió como parte de ella (la cabeza "creció"). → Al medir piezas de un personaje, ignorar los objetos del episodio (colección `EP#_Objetos`); los guiones deben dar el mismo resultado si se corren dos veces.
33. **Dos personajes mostraban la misma cara** aunque cada uno tenía otro número. → Compartían la misma imagen de secuencia (Eevee carga un solo cuadro por imagen). → Una secuencia propia por personaje (`<Nombre>_Caras`).
34. **La sonrisa de siempre salía enorme** (las emociones se veían bien). → Se sacó del rectángulo de la textura, que solo cubre la parte plana del frente, y se estiró a toda la cara. → Reducirla a ese tamaño dentro de la imagen; las emociones sí cubren toda la cara (tamaño que le gustó al usuario).
35. **La piel de la cara se veía gris** junto al cuello. → El material nuevo tenía más brillo especular (0,5) que el original (0,2). → Copiar rugosidad y brillo del material original.
36. **El video tenía huecos sin voz y tomas largas** (se pierde el gancho). → Se animó primero y la voz se acomodó después. → **Voz primero**: texto continuo (~3,8 palabras/s), una línea por toma, y `tomas_desde_voz.py` pone los cortes donde empieza cada línea.
37. **La voz recortada sonaba cortada ("pan calientí…") y muy acelerada.** → (1) ElevenLabs se comió el final de "calientito..." (los "..." pegados a la palabra le hacen apagar la voz); el recorte no fue. (2) El recorte viejo se guiaba solo por los tiempos de cada letra y dejaba 0,15 s entre líneas: sin respiro. → `recortar_pausas.py` mide la energía real (solo quita silencio), deja respiros cortos (0,3–0,55 s) y oye el resultado con Whisper para avisar si una palabra no se oye completa; esa línea se corrige y se rehace sola con `voz_elevenlabs.py --linea N` (la línea pedida sola salió +9 dB más fuerte: la herramienta la iguala al volumen de las líneas vecinas; aun así el usuario notó que sonaba distinta y prefirió rehacer toda la voz). En otra toma, "fuerzas..." metió un "¡oh!" y "escoba..." sonó "escóbatas": **no usar "..." con ElevenLabs**, solo comas y puntos.
38. **Golpes y subtítulos se atrasaban hasta 0,18 s al final del video** (5 fotogramas). → Cada fundido entre pedazos de voz acortaba el audio 12 ms y los tiempos de las palabras no lo descontaban. → Calcular los tiempos con lo que de verdad queda en el audio (ya lo hace `recortar_pausas.py`) y comprobarlo buscando cada palabra en el audio nuevo.
39. **Las fotos de la hoja de contacto aparecieron en `C:\Episodios\…`** (fuera del kit). → Blender guarda los renders con ruta relativa desde la raíz del disco, no desde la carpeta actual. → En los scripts de Blender, pasar las carpetas de salida a ruta completa (`os.path.abspath`).
40. **El cielo decorativo tiene drivers en el mundo** (cambio a noche y viento de las nubes). → Un script que limpiaba la animación del mundo con `animation_data_clear()` los habría borrado y el cielo se quedaría de día. → Solo quitar la acción (`animation_data.action = None`) y usar el `Background` que no empieza con `Cielo_`.
41. **"Archivo › Exportar como .obj" de Roblox Studio exportó el lugar completo** (los 25 personajes, el piso y el SpawnLocation en un OBJ de 66 MB), aunque había un personaje seleccionado. → En esta versión no hay "Exportar selección" en los menús. → Aislar cada personaje (`_G.CL_isolate` de `Herramientas/roblox/studio_personajes.luau`), exportar y restaurar al final.
42. **El rig de Miku salió de espaldas y con los lados cambiados**: la detección de giro por los pies falló con sus botas y mangas anchas. → Todos los personajes del lugar miraban a −Z en Studio, que en Blender es +Y. → Forzar el giro (`voltear`) o usar `partes.json`, que lo trae.
43. **Las mangas y chamarras de ropa en capas no seguían los brazos** (iban pegadas rígidas al torso). → Son una sola malla que cubre torso y brazos. → El rig ahora la deforma con los huesos según la pieza más cercana a cada vértice; el cabello largo sigue rígido a la cabeza.
44. **El rig automático no reconocía a niñas ni cuerpos angostos** (piernas "al centro") y fallaba si faltaban piezas (invisibles o tapadas por ropa en capas). → Los nombres del OBJ no dicen qué pieza es. → Empatar cada grupo con la posición de la pieza en Studio (`partes_json.py`) y crear piezas ocultas para las que faltan.
45. **Las cápsulas de la rueda se ladeaban y los pasajeros salían fuera de la cápsula** pasada media vuelta. → El driver que las mantiene derechas leía el giro con una variable TRANSFORMS (ROT_Y), que se confunde fuera de ±90°. → Leer la propiedad directa (`SINGLE_PROP` → `rotation_euler[1]`).
46. **Personajes de espaldas a la cámara** en tomas donde solo debían voltear la cabeza. → En el storyboard, `"mira"` hacia un lado o hacia atrás voltea TODO el cuerpo. → Para platicar, voltear solo cabeza y torso con la pose (`Head: [0, ±35]`); `b` positivo voltea hacia la DERECHA DE LA PANTALLA cuando el personaje mira a cámara, o sea hacia **su izquierda** (medido en la prueba A, 2026-11-08, con `giro_de`). En `UpperTorso` el giro es el **tercer** número (el segundo lo ladea). Y en una fila, nadie se pone entre la cámara y quien habla (la hermana tapaba a Sikelpa).
47. **Textos fuera de cuadro o tapando caras.** → Pegarlos a la cámara de su toma (tarjeta 2D a 2,2 m): letreros arriba, papelitos al centro y grandes, diálogos arriba con altura máxima; abajo quedan los subtítulos.
48. **Personajes tiesos con el storyboard** (EP004): cada toma era una pose fija con uno o dos cambios. → No usar el storyboard para animar; actuar toma por toma como EP002 (`Herramientas/blender/actuar.py`: respiran, cambian el peso, miran, caminan, gestos con anticipación y rebote amarrados a su palabra, cabeza y mano siguen la voz en los diálogos, golpes de cámara en los sustos).
49. **Las caras 21+ (bocas, caras nuevas) no salían**: la propiedad `cara` de los rigs viejos tiene tope 15 o 20 y Blender la recorta. → `rig.id_properties_ui("cara").update(max=40)` antes de usarlas.
50. **Voz equivocada**: `mi_config.json` tenía otra voz y el episodio salió con ella. → La voz del canal se anota en `MI_CANAL.md` y en `mi_config.json` → `voz_narrador` (revisarla antes de generar); `voz_elevenlabs.py` reusa la voz que ya tenga el episodio, así que para cambiarla hay que pasar `--voz`.
51. **Efectos de expresión con animación de llegada** (sonrojo ///): crecía desde el centro de la cabeza, parecía bajar de la nada y caerse al irse. → Las expresiones pegadas a la cara aparecen y se van en seco (`hide_render` con llaves), sin moverse.
52. **Objetos en la mano que flotan** al moverse los brazos. → Pegarlos al hueso de la mano (Child Of) o a un vacío en medio de las dos manos (`ancla_manos`), nunca a una posición fija.
53. **Carteles planos feos**. → `Herramientas/carteles.py`: papel con cinta, post-it, relojito, globo de diálogo, botón de suscribirse; contorno grueso, sombrita, el texto se achica solo para no salirse; aparecen con rebote en su palabra y se van con el corte.
54. **Cara clásica " : ) " de Roblox se ve antigua**. → `Herramientas/caras_npc.py` la borra de la textura y pone otra del `Paquete_Roblox_HD` + expresiones (risa, sorpresa) que salen de vez en cuando; solo a los que la traen por defecto (los de cara propia, como Mamá, no se tocan).
55. **Movimientos duros, "como ataque"** (EP004 borrador 2): la cabeza al hablar seguía el volumen de cada fotograma, la risa/temblor/nervios vibraban muy rápido y las miradas cambiaban de golpe. → En `actuar.py`: volumen suavizado (~0,3 s), al hablar casi quietos (solo la cabeza asiente poquito), vaivenes lentos y chiquitos, miradas cada ~3 s con giro lento y un filtro final que suaviza todos los ángulos dentro de cada toma. Regla: **suave y poquito**; quieto con vida, no todo el cuerpo moviéndose.
56. **La visera o el gorro tapan los ojos** cuando el personaje mira hacia abajo (prueba A, Sikelpa V3, 2026-11-08): cabeza baja 28° + cámara a la altura de los ojos → ojos tapados 41 de 90 cuadros, justo en la reacción. La visera de Sikelpa sale 0,40 por delante de los ojos: con la cabeza derecha tapa si la cámara está > ~16° por encima de los ojos, y cada grado que baja la cabeza le quita un grado a ese margen. → Cuando un personaje con visera mira algo abajo: **cámara un poco abajo de sus ojos** (con eso pasó a 90/90) y correr `Herramientas/blender/revisar_ojos.py` (dice en qué cuadros y con qué se tapan). *Propuesta pendiente de opinión del usuario:* llevar el objeto a la cara (mano al pecho, cabeza baja ~13°) en vez de la cara al objeto.
57. **Agarre**: un objeto en la mano se pega al hueso de la mano y se revisa con `Herramientas/blender/revisar_agarre.py` (hueco, cuánto se mete, si resbala cuadro a cuadro). Al animar un agarre, revisar **de perfil** el fotograma de contacto y reproducir ocho fotogramas alrededor para detectar deslizamiento.
58. **Orden de una reacción que se entiende sin audio** (prueba A): estímulo visible (brillo) → la cara cambia 3–4 cuadros después (los ojos primero) → cabeza → torso → mano (con un pequeño hundimiento antes de subir) → se sostiene ~0,6 s → nueva cara → levanta la vista. Los brillos de aviso deben medir ≥ 0,7 en la escena para leerse a 540×960.
59. **El borde negro de caricatura ensuciaba los objetos delgados** (prueba D, 2026-11-08): el casco invertido de `objetos_cartoon.contorno()` proyectaba sombra sobre la cara del objeto (galleta: más oscura y con grano, brillo 134 → 126). → El borde ahora es transparente para los rayos de sombra (nodo `SinSombra` en `CT_Contorno`) y la cara queda igual que sin borde (134). Con borde de 0,02–0,04 la galleta se separa mejor de la ropa del mismo tono. Comparación: `Analizador/Resultados/Investigacion_2026-11-08/C_migas/hoja_contorno_sombra.jpg`.
60. **La vista previa tardaba de más** (prueba de velocidad, 2026-11-08, EP004 f150–179 y f900–929, 540×960, abriendo el .blend sin guardar). Contra la vista previa normal (16 muestras), corrida al final porque la primera corrida de la noche carga el arranque y sale 10–17 % más lenta: **8 muestras** −27 % (PSNR 53,8 dB, igual a la vista); **sombras a media resolución** (`eevee.shadow_resolution_scale = 0.5`) −14 % (67,8 dB); **las dos juntas −36 %** (53,6 dB); 4 muestras −40 % (46 dB, solo cambian bordes finos); 1 muestra −52 % pero bordes dentados en letras y reloj (31,9 dB). **No sirven**: datos persistentes (+6 % de tiempo) ni JPG (no ahorra y deja artefactos). De noche (EP004 f3060–3074 y f3200–3214, feria con luces de colores): −35 % y PSNR medio 47,7 dB (peor cuadro 36,7: grano fino en el cabello transparente de Ajolota, no se nota a tamaño normal). → `render_paralelo.py EP### preview --rapida` usa 8 muestras + sombras a media resolución; en primeros planos con mucho cabello transparente revisar un cuadro de cerca. Con mucho movimiento (EP004 T4, globo de Lila): −33 %, PSNR 54,8 dB y el mismo parpadeo entre cuadros. *Propuesta pendiente de opinión del usuario:* usarla siempre para la vista previa que se publica.
61. **"Miré X" sin girar la cabeza** (prueba F, 2026-11-08; Custerk 5lSYLwGZSYE 13,75 s): primer plano con los ojos de la textura corridos hacia un lado y corte a lo que ve. `Herramientas/mirada_lateral.py CARA.png SALIDA --px 140` crea las variantes (con 80 px casi no se nota; con 140 se lee). Solo caras con ojos abiertos.
62. **Cambio de peso sin que los pies patinen** (prueba G, 2026-11-08): mover la cadera (`HumanoidRootPart`) de lado solo con **IK de piernas** (`IK_Piernas = 1`); en FK los dos pies se deslizan con la cadera. Valores suaves que se ven vivos: cadera ±0,10 de lado y −0,03, torso ladea 3° al lado contrario, transición de ~36 cuadros. Revisar con `Herramientas/blender/revisar_pies.py` (pie apoyado que resbala o se hunde).
63. **Fuego de caricatura que se lea** (pruebas E y E2, 2026-11-08; referencia Custerk f-4tJz5pmLk 85,5 s): `vfx.fuego_caricatura` (llamas planas en capas que cambian de dibujo ~8/s + capa de borde oscura) y `vfx.humo_negro`, sin simulación (mismo costo que sin fuego). Que se lea: **grande, encima del objeto que arde y un poco hacia la cámara** (con la raíz en el centro del carrito, el carrito y su sombrilla lo tapaban) y **detrás/arriba del personaje** (en 9:16 no cabe al lado); emisión ~1, no 3 (se vuelve mancha amarilla). Ejemplo en el Pueblo: `Analizador/Resultados/Investigacion_2026-11-08/E_fuego/E2_fuego_carrito_pueblo.mp4`.
64. **El gorro se cortaba en los primeros planos** sin que se notara en las fotos chicas (demo H, 2026-11-08): S2 −24 %, S4 −55 % al enderezarse, S5 −33 %. → Correr `Herramientas/blender/revisar_encuadre.py` por toma (mide con los vértices reales; la caja envolvente exagera por la hélice): cabeza y gorro completos y centro de la cara en el 55–80 % de la altura. Arreglo típico: lente un poco más abierta (40–44°) y mirar más abajo, no acercar la cámara.
65. **"¡PUM!" que se lea** (prueba I, 2026-11-08; referencia Custerk TYDW2fNQYYU 45,2 s): `vfx.lineas_impacto(nombre, col, punto, f_contacto, radio, largo, camara=cam)` = rayas blancas que salen del golpe en el cuadro del contacto, crecen 1 cuadro y se encogen hasta desaparecer (~4–5 cuadros; si duran 7 y no se encogen quedan como espinas flotando). Ponerlas **delante** del punto del golpe y con el objeto en cuadro (detrás de las piernas del personaje no se ven). Mismo costo de render que sin ellas. Con un golpe de cámara corto (≤ 8 cuadros) y el personaje que se agacha antes del contacto. Video: `Analizador/Resultados/Investigacion_2026-11-08/I_impacto/I_sin_vs_pum.mp4`.
66. **Accesorios de bloques más acabados sin costo** (prueba J, 2026-11-08, una variable por versión: `Analizador/Resultados/Investigacion_2026-11-08/J_bisel/hoja_bisel_v2.jpg`): el **sombreado suave** (con bordes duros > 35°: `set_sharp_from_angle`) quita las facetas de lo redondo (taza, galleta, moneda) sin redondear las cajas; el **bisel** 0,02–0,04 (2 segmentos) agrega una línea de luz en los bordes que dibuja la forma y se sigue viendo a tamaño celular. Con los dos se ve más terminado; mismo tiempo de render (0,89–0,93 s por foto).
67. **"Lo que se dice, se hace" y que se VEA** (EP004, comentarios del usuario a la vista previa, 2026-11-08). Cada cosa que dice la voz tiene que pasar en cuadro, grande y clara.
    - Problema en T3: "un billete en la cabeza" caía desde 9 m (casi siempre fuera de cuadro) y quedaba parado detrás del fleco.
    - Problema en T4: "un globo se la llevó tres calles", pero solo se veía a la niña subir en la plaza.
    - Arreglo (`EP004/scripts/pulir_t3_t4.py`):
      - "llover dinero" → lluvia de billetes a los lados de la cara. El cuadro mide ~2,4 m de ancho a la altura del personaje.
      - El billete cae desde ~3,5 m y queda encima del pelo, recargado hacia atrás para que el frente vea a la cámara, con líneas de impacto en "pum" y corte en "billete" a un plano un poco desde arriba.
      - "Se la llevó tres calles" → corte en "globo" a una toma aérea de frente a ella: cruza volando sobre la calle principal y abajo pasan tres filas de casas, con el globo completo en cuadro.
    - Al escribir la tabla de tomas, revisar cada verbo y cada número del guion ("tres calles", "cuarenta preguntas"): ¿se ve?
    - Para ponerle algo encima a la cabeza, el punto más alto de las piezas incluye los picos de atrás del pelo. Bajar ~0,3–0,4 m y comprobarlo con foto: si no, queda flotando.
68. **ElevenLabs lee en inglés las onomatopeyas** (EP004, 2026-11-08): "¡Dong!" sonó como palabra en inglés y además salió en los subtítulos; el usuario lo notó.
    - Whisper no lo detecta: transcribe "¿Don?" en español.
    - Arreglo sin gastar créditos: `CALLAR = {"dong"}` en `armar_video.py`. Silencia esa palabra en la voz (con fundido de 5 ms) y la quita de los subtítulos; el efecto de sonido (campana) la "dice".
    - En guiones nuevos: los sonidos que hace un efecto (dong, ring, bip) no se escriben en `narracion.txt`. Las onomatopeyas en español que sí se oyen bien ("¡pum!", "¡puf!", "¡clac!") pueden quedarse.
    - Para errores raros de la voz en una línea, rehacer solo esa línea con `voz_elevenlabs.py EP### --linea N` (gasta solo esa línea; confirmar créditos). No hace falta partir toda la narración en dos.
69. **Cambiar el orden de frases de la voz sin gastar créditos** (EP004, 2026-11-08): el usuario quiso empezar con "En este pueblo…" (la regla del mundo, para la retención).
    - Se cortan los bloques de la voz aprobada en cuadros de silencio, se cambian de lugar y se quita la palabra que sobra ("Y"), con fundidos de 8 ms.
    - Los dos bloques juntos deben durar lo mismo: lo que viene después no se mueve y no hay que volver a renderizarlo.
    - Con eso se reescribe `tomas_voz.json` (palabras, cuadros y tomas) y se mueven las llaves de animación de todas las acciones con la misma tabla de cuadros.
    - Scripts de ejemplo: `EP004/scripts/invertir_inicio_audio.py` y `invertir_inicio_blend.py`.
    - Para borrar cámaras por nombre, nunca usar un prefijo corto como `CR_Cam_S1`, porque también borra `CR_Cam_S10…S19`.
70. **Gestos de brazos sobre una pose que ya existe** (EP004 T44, aplauso).
    - Sumar un giro en ejes del rig solo sirve si el brazo cuelga: con los brazos abiertos, el giro solo los rota sobre sí mismos y las manos no se mueven.
    - Para aplaudir, señalar o agarrar: IK de dos huesos hacia un punto en el mundo (hombro → codo con polo abajo y afuera → mano). Se asigna `pose_bone.matrix` y se guarda la llave de `rotation_euler`, cuadro por cuadro.
    - Medir las manos (`RightHand.head`) antes de renderizar.
    - Si el que aplaude está detrás de otros, el aplauso va a la altura de la cara (debajo de la boca) y un poco hacia un lado; si no, no se ve.
71. **Grano (puntitos oscuros) en escenas de noche de la vista previa** (EP004, 2026-11-08; prueba en `Analizador/Resultados/Investigacion_2026-11-08/EP4_grano/`).
    - Causa: las sombras suaves de muchas luces (feria, foquitos) con 1 rayo de sombra por muestra. Se nota sobre superficies claras: caras blancas, cabinas, piel.
    - Subir las muestras casi no lo quita: con 64 todavía se ve.
    - `eevee.shadow_ray_count = 4` lo deja casi igual que 128 muestras: PSNR contra la referencia 36,5 → 42,1 dB (f2480) y 38,8 → 44,2 dB (f2850), con el mismo tiempo de render (36 s cada 30 cuadros con 1 o 4 rayos).
    - Filtrar el video después (nlmeans, hqdn3d) empeora la imagen contra la referencia.
    - `render_paralelo.py` y `rehacer_tramo.py` ya ponen `shadow_ray_count=4` en la vista previa y en el render final.
    - **De día también pasaba**: en interiores con luces y sombras suaves del sol salía grano en la piel y en la ropa clara. Con 4 rayos: salón f1500 42,6 → 47,9 dB, igual de rápido.
    - El vidrio y el pelo con transparencia "tramada" (`DITHERED`) **no** eran la causa: pasarlos a `BLENDED` o a borde recortado (alfa 0/1) no mejora nada medible (f190, f1500, f2160). No hace falta tocarlos.
72. **El objeto que dice la voz no se distinguía** (EP004 T20, "escondía un papelito en la mano", 2026-11-08). Tres errores juntos:
    - La cámara no lo encuadraba: solo se veía su cara.
    - Con la cámara nueva de frente, la amiga tapaba a la crush.
    - El papelito, pegado al hueso de la mano, quedaba de canto (una tira delgada) y blanco, igual que su guante.
    - Arreglo (`EP004/scripts/pulir_recreo.py` y `papelito_crema.py`): la cámara va por el lado libre. Mientras dura la frase, el papel deja la restricción de la mano (influencia 0) y queda de frente a la cámara, junto a la mano; en el siguiente corte vuelve a la mano. Además: material propio crema amarillento y 1,8 veces más grande.
    - `revisar_objetos.py` lo detecta: "se distingue" (cuánto cambia la foto con y sin el objeto dentro de su recuadro) pasó de 0,05 a 0,20.
    - Correrlo en cada toma con un objeto clave.
73. **El Analizador con 2 motores a la vez NO fue más rápido** (2026-11-08, RTX 5070 de 12 GB).
    - Con uno: la GPU se ve casi sin uso en algunos momentos, pero el motor ocupa ~5,5 GB de memoria de video.
    - Con dos: la memoria llegó a 11,6 de 12 GB y cada video tardó 2–3 veces su duración (con uno, 1–1,4 veces).
    - Se quedó la opción `--parte k/n --sin-formula` (el registro ya se relee antes de guardar y cada proceso usa su propio temporal), por si hay una tarjeta de 16 GB o más. Aquí: un solo motor.

### 74. Receta simple ≠ congelado (EP005, 2026-11-09)
- **Qué pasó**: con poses 100 % fijas, el usuario vio la animación «muy tiesa» y dijo que así no se entiende la historia. Ellos dejan casi quietas solo el 31–45 % de las tomas.
- **Solución**: siempre agregar **vida suave** (respirar, cabeza, peso, brazos), **un gesto en la palabra clave** y **asentir al hablar**. Lento y de pocos grados.
- **Dónde**: `docs/09_RECETA_SIMPLE.md` → «Simple NO es congelado».

### 75. Espejo de verdad en Eevee (EP005 tomas 23–24, 2026-11-09)
- **Qué pasó**: el usuario rechazó el espejo falso («un círculo con un cuadro rosa adentro»). La **sonda planar** de Eevee no refleja nada al renderizar en segundo plano (`blender -b`): salía negra o azul.
- **Solución (como en cine)**: una **cámara reflejada** (la cámara principal reflejada en el plano del vidrio) filma el cuarto cuadro por cuadro y esa imagen se pega en una placa encima del vidrio, con UV = dónde cae cada punto en esa cámara. La cámara reflejada debe mirar **derecho al espejo** (eje = normal) y encuadrarse con **desplazamiento de lente** (shift): así su corte cercano (`clip_start`) queda justo en el plano del vidrio. Si se inclina, se cuela lo que hay detrás de la pared (salió una escalera).
- Calcular las UV con la **resolución del reflejo** puesta (no la de 9:16), esconder la placa mientras se filma, y esconder en el reflejo los muebles pegados al espejo cuyo costado parte la imagen (ropero).
- Para que se vea su cara reflejada: ella a un lado del espejo y un poco volteada; la cámara **del otro lado**, donde la línea cámara → su reflejo pasa lejos de sus coletas y de los muebles. Espejo de cuerpo completo (2,4 × 5,7), no el redondito del tocador.
- **Dónde**: `animar_ep005.py` → `espejo_real()`; mueble: `muebles_cartoon.espejo_cuerpo()`.

### 76. Piezas Roblox: medir con sus CARAS, no con sus vértices (EP005 toma 21, 2026-11-09)
- **Qué pasó**: la cobija calculada sobre las piernas de la crush las dejaba salir: cada pieza R15 tiene muy pocos vértices (solo esquinas) y la cobija «no veía» el medio de la pierna.
- **Solución**: muestrear puntos sobre todos sus triángulos (cada ~0,12) antes de medir. Sirve para cualquier cosa que deba envolver o tocar el cuerpo (cobijas, apoyar en la cama, colisiones).
- La cobija que tapa a alguien acostado = **copia de la cobija de la cama con dos formas** (acostada / sentada) que cambian cuando se incorpora; la original se esconde en esas tomas.

### 77. Cámara pegada detrás de alguien = su cabeza tapa todo (EP005 tomas 27, 56, 2026-11-09)
- Para «entra a su cuarto» o «abre su mochila»: la cámara alta (casi en el techo) y **a un lado** de su camino, para que él quede en un tercio y lo importante (el cuarto, la hermana, la mochila) en el otro. Revisar con una foto antes de seguir: dos veces la cámara quedó metida en una coleta o en la pared.


### 78. Beso en la mejilla que SÍ se note (EP005 toma 25, 2026-11-09)
- Primera versión: la mamá parada al lado, mirando a la cámara. No se leía como beso, y su pelo tapaba a la chica.
- Lo que funcionó:
  - **Rotación:** quien da el beso mira a la mejilla de la otra persona y queda de 3/4 a la cámara, no de perfil (de perfil, su pelo largo le tapa la cara).
  - **Lado:** que llegue por el lado donde **su fleco cae hacia atrás**. Se prueban los dos lados con foto.
  - **Cabeza:** su cabeza va **al lado de la otra y un poco adelante, hacia la cámara**. Si queda atrás, el pelo grande de la otra le tapa la cara.
  - **Agacharse:** se agacha desde `UpperTorso` y la cabeza **compensa** lo que se inclina el torso (`Head x = -0,75 × inclinación`). Si no, su fleco cae sobre su cara.
  - **Tiempos:** se acerca en los 8 cuadros antes de «beso», se queda un momento y se endereza antes del primer plano.
- Medir con `matrix_world` de la cabeza (centro = mitad entre head y tail del hueso) y revisar cada cambio con fotos de 6 cuadros.

### 79. Whisper no escribe las onomatopeyas (EP005, voz propia, 2026-11-09)
- «¡Miau!» no salió como palabra. `recortar_pausas` lo marcó como «sonido de más» en su segundo, y el script de animación falló en `palabra(9, "miau")`.
- Ya se arregla solo: `tomas_desde_voz.py` le da a la palabra del guion que no se oyó el tiempo del «sonido de más» que cae en su hueco, y avisa en la consola.
- Antes de rearmar un episodio con voz nueva, comprobar que existan todas las palabras que usa el script (`palabra(n, "...")` y la tabla `GESTOS`).

### 80. La voz de EP005 se sentía lenta por los huecos, no por la voz (EP006, 2026-11-09)
- De 2:22, **34 s eran silencio**: `recortar_pausas` dejaba 0,3–0,4 s al final de cada línea y alargaba los respiros que ElevenLabs entregaba más cortos (71 huecos de 0,25 s o más = 26,5 s).
- Se compararon dos recortes de la misma voz (sin gastar créditos): A con 0,2 s entre líneas (2:18) y B con 0,14 s (2:13). **El usuario eligió B**: ahora es el valor por defecto (`--max 0.10 --coma 0.12 --respiro 0.14 --suspenso 0.2`).
- Para probar ritmos, recortar la misma voz con distintos valores y mandar las dos versiones: es gratis y el usuario decide con el oído.
- **Modelo `eleven_v4`** desde EP006: misma voz, más actuada; dice las frases con más calma, así que el video no se acorta tanto como los huecos. Costó ~981 créditos por 2.229 letras (menos de lo que marca el texto). No acepta el contexto de líneas vecinas: `voz_elevenlabs.py --linea N` reintenta sin él.

### 81. Los niños no se veían niños (EP006, 2026-11-09)
- Todos los rigs medían casi lo mismo (coronilla 4,4–5,45) y Sikelpa salía más alto que su mamá (5,10) y que el presidente (5,07).
- Ahora se escala cada personaje al anexarlo con `alturas.escalar(rig, "nino" | "adulto" | "nino_chico")`: adulto 5,1, niño 4,0 y niño chico 3,45 (se mide hasta la coronilla, sin gorros).
- Antes de escalar, revisar que el rig no tenga restricciones que apunten a otros objetos ni mallas sin padre: los 30 del kit están bien.
- Lo que usa distancias fijas se rompe con la escala: el paso al caminar (`alturas.fase_paso`) y las cámaras de `tomas_simples` (ya corregidas con la escala de cada rig).
- Al ver la foto, el usuario prefirió dejar a **Sikelpa con su tamaño original** (`"original"`): las excepciones de cada canal van en `MI_CANAL.md`, no en la regla general.

### 82. La camara daba una vuelta completa a mitad de la toma (EP006 T20, 2026-11-09)
- Pasaba con camaras que miran hacia -Y (al sur): una llave quedaba en 180 grados y la otra en -180, y Blender giraba por todo el circulo entre las dos (el personaje salia de cabeza a la mitad).
- Arreglado en `tomas_simples.camara` (y en `ep6.camara_toma`): cada llave usa `to_euler('XYZ', anterior)`, la rotacion compatible con la llave de antes.

### 83. Revision de EP006 toma por toma: lo que salio mal en el primer intento (2026-11-09)
- **Camara dentro de la cascada de la fuente** cuando el personaje mira a la fuente: la imagen sale lavada. La camara va entre la cascada (r 4,4) y la orilla (r 7,8), o el personaje voltea hacia el sur.
- **Postes y banderines tapando las tomas abiertas**: la camara va entre los postes y abajo de los banderines (z ~5).
- **Ninos escalados = camaras demasiado cerca**: `frente_rot` multiplica la distancia por la escala del personaje. Pedido del usuario: encuadre algo alejado. `cam_frente(lejos=True)`: al menos 6,8 y 25 % mas.
- **Las bocas de hablar del kit (21-25) son sonrisas**: en un dialogo triste ("Quiero que regrese mi hermana") se veia feliz. En dialogos tristes, cara fija triste (6) o llorando (31).
- **Objeto en la mano que tapa la cara** (caja, moneda, foto): bajar el brazo de la pose y usar `en_mano(..., arriba=-0.4)`.
- **Utileria del mapa en medio** (lampara de pie, lampara del escritorio): revisar la hoja de contacto y mover la camara o al personaje.

### 84. Luz de EP006 (2026-11-09)
- **La tarde se veia igual que el dia**: el color del mundo casi no se nota con el cielo nuevo. Ahora el sol se pone calido (1,0 · 0,72 · 0,45) y a 85 % en las tomas de tarde: se lee como atardecer dorado.
- **De noche, las caras que miran hacia la fuente quedan a contraluz**: luz calida del lado de la fuente ademas de la de la plaza; en interiores, una lampara puntual (despacho, cuarto).
- **Ventana de noche**: luz de luna azulada de afuera, suave (~320 W); con 900 W se lavaba la imagen.
- **Grano en las fotos de prueba de noche**: es el rayo de sombra unico. Revisar la luz siempre con `shadow_ray_count = 4` (como la vista previa real, leccion 71).

### 85. Correcciones del usuario al borrador de EP006 (2026-11-09)
- **El agua de la fuente de `Pueblo_v2` esta DEBAJO de la tapa de piedra de la pileta** (agua a 1,52-1,60; tapa a 1,76): lo que flota parecia apoyado en piedra y las monedas chapoteaban en roca. En EP006 se subio `Fuente_Agua` 0,28 solo en el archivo del episodio (`utileria.py`). Pendiente arreglarlo en el mapa (`docs/IDEAS.md`).
- **La puerta de la presidencia no tiene hoja** en `Pueblo_v2` (hueco oscuro y tableros flotando). En EP006 se puso una puerta cerrada en `utileria.py`.
- **Cascada que tapa**: lo que cae al agua debe caer entre la cascada (r 4,4) y la orilla (r 7,0); detras de la cascada no se ve.
- **Que se vea la moneda caer al agua**: de frente a quien la avienta, la moneda vuela hacia la camara y se sale del cuadro. Receta: de espaldas -> de frente (la avienta) -> corte rapido al agua desde la orilla con chapoteos (`inserto_agua`) + estela de destellos.
- **Mano en el hombro de otro**: no a ojo. Se calcula la pose del brazo que lleva la mano al punto (`mano_a`), y si queda lejos se acomoda al otro personaje a la distancia del brazo.
- **Peluche de un personaje**: usar la MISMA pieza de su modelo (copia de `Ajolota_Acc_Peluche_Espalda`), no uno generico de otro color.
- **La cara 15 se ve como la cara de fabrica**: para alegria usar 16 (feliz) u 8 (muy feliz).
- **Revision por segundos**: el usuario marca segundos del borrador; convertir a toma con `tomas_voz.json` (segundo x 30 = cuadro) y revisar esos cuadros del borrador antes de cambiar.

### 86. Accesorios pegados al cuerpo: medir en los ejes del rig, no del mundo (EP006, 2026-11-09)
- La banda presidencial salio cruzada sobre la boca: se armo midiendo el torso en ejes del MUNDO, pero en el cuadro guardado el rig estaba girado -122 grados (las llaves de giro van en el objeto del rig). Al pegarla al hueso conservo ese error en todas las tomas.
- Arreglo en `objetos_cartoon.banda_presidencial`: mide en los ejes del rig (`rig.matrix_world` invertida), arma con `P.M = rig.matrix_world`, se pega al hueso con la misma relacion que la pieza del torso y solo cubre el UpperTorso (si baja a la cadera se despega al inclinarse). Las piezas que ya le pusimos llevan `ct_accesorio` para que `_pieza_hueso` no las confunda con el torso.
- Para cualquier accesorio nuevo (mochila, collar, gafete): medir en ejes del rig y revisarlo con fotos de cerca en varias tomas (`scripts/foto_banda.py` de EP006 sirve de ejemplo).

### 87. Sombreros y bigotes en personajes (EP006, 2026-11-09)
- `objetos_cartoon.sombrero_copa(rig, col)` y `bigote(rig, col)`: se miden en ejes del rig y se pegan al hueso Head con la misma relacion que la cabeza. El sombrero mete dentro de la copa el cabello que sale arriba del ala (copia la malla del cabello; el original no se toca).
- **El bigote va de una sola pieza lisa** (tubo curvo con subdivision): hecho con bolitas el usuario dijo que parecia "bolita de chocolate". Altura 0,5 de la cabeza: bajo los ojos y la boca de la textura asoma por debajo (con 0,4 la boca quedaba ENCIMA del bigote).
- **Ala ancha + camara desde arriba + cabeza agachada = no se ve la cara**: en la toma 32 (llora con la foto) el ala le tapaba toda la cara. Camara mas baja (desde el pecho) y cabeza casi derecha; recordar que el gesto `triste` agacha 14 grados mas. Revisar con las camaras reales de cada toma (`fotos_cuadros.py`), no solo de frente.

### 88. Vestuario de NPC: medir la pieza DEL CUERPO, no el accesorio más grande (EP007, 2026-11-09)
- Para que cada NPC parezca quien es (pedido del usuario: "un panadero debe verse como panadero"), `objetos_cartoon` trae vestuario que se pega al hueso: `gorro_chef`, `chaqueta_chef` (filipina: funda un poco más grande de cada pieza del torso y los brazos), `panuelo_cuello`, `mandil` (con o sin peto, bolsillo, lápiz y harina), `lentes`, `cachetes` y los atajos `vestir_panadero`, `vestir_tendero` y `vestir_vecina`. El bigote es el `bigote()` de una pieza de EP006 (lección 87), con alto 0,5 para que la sonrisa asome abajo. Los ojos de la cara clásica quedan a ~0,64 de la altura de la cabeza (ahí van los `lentes`).
- Falla de la primera prueba: `_pieza_hueso` elige la malla MÁS GRANDE del hueso, y el pelo alto (cabeza) o el pelo largo de una chica (pegado a UpperTorso) son más grandes que la cabeza o el torso. El gorro de chef quedó flotando, los lentes en la frente y el delantal de la vecina a la altura de las rodillas.
- Arreglo: `_pieza_cuerpo(rig, hueso)` busca la pieza `<Nombre>_<Hueso>` y solo si no existe usa la más grande. El mandil se pone delante de la ropa en capas (mallas con Armature, ej. sudaderas), pero no del pelo.
- Ojo: `banda_presidencial` todavía usa `_pieza_hueso`. En una chica con pelo largo saldría mal; cambiarla a `_pieza_cuerpo` si se usa con ella.
- Siempre revisar con foto antes/después (frente y 3/4): `referencias/vestuario_npc.jpg` de EP007.
- **Cabeza bronceada y piernas claras** (la vecina): en las cabezas tipo calcomanía (la cara es una imagen casi toda transparente), la piel sale del color de la pieza que trae el `.mtl` de Roblox (`Kd`, mezclado por el alfa), mientras que las manos y las piernas traen su piel **pintada** en la textura de la ropa, a veces de otro tono. Arreglo: `objetos_cartoon.igualar_piel(rig)` lee la piel de las manos por UV y la pone de fondo en la cabeza (los ojos y la boca no cambian). Se aplica en el archivo del episodio; el `.blend` del personaje no se toca.
- **Para que se lea el papel, un objeto en las manos**: la vecina con delantal no se entendía (su pelo lo tapaba). Con `canasta_ropa` + `cargar_canasta` (hombros y codos, la canasta a la medida de las manos) se entiende de inmediato.
- **Causa de la cabeza bronceada** (medido en 20 NPC): `armar_rig_r15_auto.py` pasaba el `Kd` del `.mtl` a lineal, pero Roblox ya lo da en lineal. Pasarlo dos veces lo oscurece y lo vuelve naranja: por ejemplo, #eab892 (manos) queda en #d37c4a (cabeza). Ya está corregido para los rigs nuevos. Los rigs que ya existen (casi todos los NPC, Mamá, Raul, la crush, el mejor amigo y su amigo) siguen con la cabeza más oscura hasta que se les aplique `igualar_piel`.
- **Arreglado en todos los rigs existentes (2026-11-09)**: con `Herramientas/blender/revisar_piel.py -- --arreglar`, que regresa al `Kd` original los colores convertidos dos veces. Respaldo previo en `Respaldos/piel_antes_2026-11-09/`. **Cada rig nuevo se examina con `revisar_piel.py`** (paso de la receta en `docs/03_PERSONAJES.md` y de la skill `poner-rig`). Sikelpa sale `REVISAR` a propósito: su cabeza es blanca y sus manos rojas por diseño, así que no es piel.

### 88b. Gancho sin huecos: mostrar como desaparece, no el lugar vacio (EP006, 2026-11-10)
- En EP006 los segundos 3–6 ("¡Puf! Se lo traga el agua, y nunca vuelve") eran un puf y luego piso vacio: el usuario lo marco como el peor momento del gancho.
- Receta usada (toma 2): ¡puf! = chorro dorado a sus pies y la fuente lo JALA (vuela de espaldas en arco, manoteando, con estela de brillos; llaves en cada cuadro porque las del rig son CONSTANT) -> "se lo traga el agua" = corte desde atras y arriba, cae con chapoteo grande y se hunde -> "y nunca vuelve" = desde arriba, solo flota la moneda brillante con ondas y las ultimas burbujas.
- `arco()` esconde el objeto al llegar (y un cuadro antes de salir): si el objeto debe quedarse (flotar, quedar en el piso), poner las llaves a mano o usar `quedar`. Moneda acostada = rotacion X 0; con X 90 queda parada.
- Lista de lo que el usuario revisa en cada borrador: `docs/05_CAMARAS_Y_TOMAS.md`.

### 89. Letreros grandes y dentro de su marco; lo que se agrega combina con el edificio (EP007, 2026-11-10)
- **Letreros**: el de "SOLO FRASCOS VACÍOS" quedó diminuto sobre el mostrador y en 9:16 no se leía (el usuario lo notó). Regla: todo letrero que la historia necesita debe ocupar **al menos ~1/3 del ancho del cuadro** en su toma y **el texto nunca se sale de su marco**.
- Herramientas: `objetos_cartoon._texto_en_caja(t, ancho, alto)` ajusta el texto al ANCHO y al ALTO (antes solo al ancho). `_lineas_en_tablero` reparte las líneas con margen y cada una queda lo más grande posible. `letrero_colgante` (tabla con cadenas, Arial Black) y `pizarron` ya lo usan. Revisar siempre con una foto de la toma.
- **Lo que se agrega a un edificio usa SUS materiales**: el ático de tablones cafés sobre la tienda verde menta "no combinaba". Ahora usa `Tienda_Muro_ABARROTES` y `Casa_Borde` (molduras blancas, esquineros, friso, tablas del alero), con tejas y contraventanas de colores que van con el toldo.
- **Al reconstruir, borrar los materiales sin uso** (`bpy.data.materials` con `users == 0`): si no, el `.blend` se queda con los materiales viejos y las mejoras de `objetos_cartoon` (vidrio con orillas, etiquetas que se leen de noche) no aparecen.
- **Efectos que se entienden sin tapar** (bebé que brilla, EP007): un halo grande y anillos encima del bebé lo tapaban y "cambiaban" su aspecto (comentario del usuario). Funciona mejor así: `rayos_brillo` DETRÁS, un resplandor suave detrás y `destellos` de 4 puntas ALREDEDOR, nunca sobre la cara, más una luz del mismo color. Para "le roba el poder", un `chorro_luz` grueso y curvo con chispas. Los personajes de la escena **miran hacia lo que importa** (la cuna) y quedan de tres cuartos a la cámara: si la rotación queda al revés, se ven de espaldas.

### 90. Mundos enormes que no se acaban (EP008, mundo de globos, 2026-11-10)
- **El usuario quiere mundos GRANDES** (como la escalera infinita de Custerk): con 14 casas "se notaba que el mundo es pequeño". Receta probada en `Escenarios/Mundo_Globos/scripts/`:
  - **Casas héroe con detalle** solo cerca de donde va la cámara (porche, barandal, macetas, farol, letrero) y **miles de casas sencillas instanciadas** (vacíos con `instance_type='COLLECTION'`): 28 prototipos (2 niveles de detalle × 14 tamaños), 5.300 instancias, sin que Eevee se trabe.
  - **Color distinto por instancia** con `Object Info > Random` → rampa de colores CONSTANTE. Para que cada globo de un racimo (un solo objeto) sea de otro color: atributo por vértice `gid` + Random.
  - **Niebla de distancia en TODOS los materiales** (Camera Data > View Distance → Map Range → mezcla con una emisión del color del horizonte): lo lejano se funde con el cielo y el mundo "no se acaba".
  - La forma que cuenta la regla del mundo: una **montaña** de casas que sube y se angosta hasta la mansión (más globos = más arriba) + un mar de casas pobres hasta el horizonte.
- **La regla del mundo en números que se leen**: cada casa trae su letrero (placa negra, orilla dorada, globito rojo y el número en amarillo, Arial Black) sobre el techo; la del protagonista dice **1**. Las cuerdas se amarran **detrás** del letrero (el nudo va atrás y más alto) para que no lo crucen.
- **Sombras de cosas muy altas en Eevee**: la casa rica a 84 de altura NO daba sombra en la de Sikelpa (aunque un `ray_cast` decía que sí). Se arregla con `light.use_shadow_jitter = True` en el sol (y ángulo de 1,5°).
- **Nubes que no parezcan plástico**: metaballs gigantes (r 45–85, se funden; con r 10–20 parecían "bolitas" o piedras) + material mate con ruido de relieve, orilla clara y orillas que se desvanecen (alfa por *Facing*) + una **cáscara de humo volumétrico** (las mismas metaballs ×1,22 solo con volumen) + neblina volumétrica oscura que baja. La nube **no proyecta sombra** (`visible_shadow=False`) para que el piso de abajo tenga sol.
- **Si debajo hay una sorpresa, que no se vea por los huecos**: un **techo opaco** oscuro dentro de la nube (`MG_NubeTecho`, z −95). Cuando la nube se va hay que ocultarlo junto con la neblina.
- **Terreno lejano sencillo que tapaba el río y el lago**: la malla de horizonte no estaba cavada y quedó encima del agua. Dentro de la zona con detalle se hunde (−45).
- **Humo de chimenea**: con superficie parecía una cadena de cuentas negras; con **volumen + ruido** en bocanadas que crecen y se inclinan sí parece humo.
- **Whisper en esta PC**: `faster-whisper` falla con el video directo (`av`: `metadata_errors`) y en GPU (falta `cublas64_12.dll`). Funciona sacando el audio con ffmpeg (`-ac 1 -ar 16000 -f s16le`) y corriendo en CPU (`compute_type='int8'`).
- **Agua en Eevee**: con rugosidad 0,06 y capa brillante, los reflejos hacían "paredes" claras a los lados del lago; con 0,3 desaparecen. **Dos aguas a la misma altura parpadean** (el río entraba al lago): cortar la cinta del río donde entra. Para dar profundidad, malla en **anillos** con atributo `prof` (claro en la orilla, azul en el centro); en abanico el degradado se veía en gajos.
- **Pueblo de abajo, lo que pidió el usuario**: pocas flores sueltas (las casas sí con sus jardines), suelo con textura (pasto de 3 verdes, partes secas, puntitos, relieve, arena en las orillas con un atributo por vértice), matas de pasto, piedras y hongos, lago enorme con orilla irregular, playa e islita.
- **Personaje gordo** (Don Inflado): la forma del torso panzón del rig blocky de `Thumbnail.blend` (del usuario) quedó guardada como malla en `Personajes/Plantillas_Rigs/Panza_Gordo.blend`; se escala sobre el torso R15, se pega al hueso `UpperTorso` y se esconden `UpperTorso`/`LowerTorso` (quedan adentro). Prueba: `Episodios/EP008_Mi_Casa_Cuelga_De_Un_Globo/scripts/prueba_don_inflado.py`.

### 91. Encuadres en 9:16 y poderes que se entiendan (EP007, animación bloque 1, 2026-11-10)
- **Cabezas cortadas en casi todos los acercamientos**: se apuntaba la cámara al cuello y se medía solo lo ALTO. Las cabezas de Roblox son enormes (Sikelpa mide 6 de alto con el gorro y la hélice; la cabeza llena el ANCHO del cuadro). Se hizo `retrato()` en `animar_ep007.py`: mide cuello, punta y pies reales y además el ANCHO del cuerpo o de la cabeza (`medidas()`), y aleja la cámara hasta que quepan las dos cosas. Con `golpe=True` empieza más lejos y el golpe de zoom TERMINA en el encuadre bueno (antes acababa pegado a la cara).
- **`marco_recuerdo` no se veía**: el driver usaba `sensor_width`; las cámaras de los episodios usan `sensor_fit = VERTICAL` (manda `sensor_height`) y el plano quedaba 1,5× más grande que el cuadro. Arreglado en `objetos_cartoon.marco_recuerdo`.
- **Centro de la hélice**: incluir los hijos metía el disco de giro escondido (lejos) y la cámara del inserto apuntaba a la nada; medir solo la malla de la hélice.
- **Fuego que parezca fuego** (pedido del usuario: las llamas planas de `fuego_caricatura` de cerca parecen recortes de papel): nuevo `vfx.fuego_vivo` (lenguas de llama con volumen que crecen y se mecen, color por altura con ruido que sube, chispas, resplandor y luz que parpadea). Con view transform Standard un brillo de emisión > ~1,5 quema todo a blanco y se pierden el naranja y el rojo: emisión ~1,4. Se pega a la mano con `ep7.en_mano`.
- **Rayos X de mamá**: ojos que brillan se veían desalineados. Lo que pidió el usuario: la pared se vuelve TRANSPARENTE en un círculo donde está el escondido (booleano animado + vidrio celeste con líneas que corren + orilla punteada), y el escondido de cara a la pared para que se le vea la cara y la galleta.
- **Volar**: no estático ni con piernas tiesas. `flotar()` sube y baja de verdad (~0,3), las piernas van separadas y se mecen, el torso acompaña.
- **Lo que tapa**: postes de faroles (`FP_Poste`) frente a la cámara, el brazo de quien señala en primer plano, niños entre la cámara y el protagonista. Antes de dar por buena una toma, mirar qué hay entre la cámara y quien está en foco (rayo de prueba).
- **Mantas con texto**: si la manta grande tiene que verse completa, el texto chico de abajo queda pequeño; en la palabra clave se agrega un texto 3D grande que aparece de golpe ("¡3 DÍAS!") sin tapar el texto de la manta.
- **Espacio para quien trabaja entre muebles**: el panadero quedaba DENTRO del horno porque entre el horno y la mesa había 0,29 de espacio. Al construir un puesto de trabajo, dejar ≥ 1,4 libres entre lo de atrás y lo de adelante (medir con las cajas de los objetos) y probar con el personaje parado ahí. Cámara a la altura del pecho: desde arriba, la mesa parece que la tiene encima.

### 91b. Animar de noche sin la voz aprobada, gancho de caída y render por turnos (EP008, 2026-11-10)
- **Sin voz aprobada no se gastan créditos**: se hace una **voz temporal** con Windows (`System.Speech`, "Microsoft Sabina" es-MX, `Rate 3`, pausas de 120 ms; `scripts/voz_temporal.ps1`) → `recortar_pausas.py --audio voz_temporal_sabina.wav` → `tomas_desde_voz.py`. Sirve para animar con tiempos reales; cuando el usuario apruebe la voz del canal se rehacen esos dos pasos y se corre otra vez la animación (todo lee `tomas_voz.json`).
- Whisper con voz robótica a veces oye otra palabra ("boing" → "boeing"): en la animación y en los efectos usar un respaldo por toma (`pal(n, w, k, rel)` en `animar_ep008.py`, `en(w, k, toma, rel)` en `armar_video.py`) con el MISMO punto relativo, para que el golpe y el sonido caigan juntos.
- **Gancho "cae a la nube"**: globo que se infla de más y tiembla → ¡pop! (pedazos, destello de cómic chico para no tapar, líneas, brillitos) → el letrero 1 cambia a 0 rojo → la casa se queda colgada 8 cuadros → cae con gravedad de caricatura y gira → toma de dron que la sigue con un TRACK_TO a un vacío → corona de bocanadas + anillo de bocanadas (una dona plana se veía falsa) + neblina volumétrica que se levanta y se cierra.
- Si el personaje CAE en una toma, la cámara tiene que bajar con él (`sube=`); con cámara fija se sale del cuadro por abajo.
- **Dentro de una nube sólida no se puede filmar** (las metaballs tapan todo): se arma un **túnel de humo** aparte (esfera invertida con el material de la nube + niebla volumétrica oscura) lejos de todo, y las bocanadas que pasan no cruzan la línea cámara–personaje.
- Poses que tapan la cara: brazos al frente a la altura de los hombros ("agarrar" alto) tapan la cara en tomas de frente; agarrar más abajo (55–62°). Para acciones entre dos (dar, ayudar, abrazar) una cámara **de lado** perpendicular a la línea que los une (`dos()` en `animar_ep008.py`); sobre el hombro puede quedar dentro de un mueble (la taquilla).
- **Render por turnos** (`scripts/render_por_turnos.py`): tramos de 150 cuadros; antes de cada tramo revisa con `Get-CimInstance Win32_Process` si hay otro `blender.exe -b` de otra sesión y espera. Así dos sesiones no saturan la tarjeta al mismo tiempo.

### 92. Animar 67 tomas sin que nada tape: cámaras que se revisan solas (EP007, bloques 2-5, 2026-11-10)
- **`retrato()` prueba ángulos hasta que se vea la cara** (`ts.visible`: rayos a 5 puntos de la cara). En la primera pasada la mitad de los retratos chocaban: una pared detrás de la cámara, un niño, un poste (`FP_Poste`), el carrito de nieves, la casa vecina, la mesa de frascos. Ahora gira la cámara de 25 en 25 grados hasta ver ≥ 80 % de la cara y avisa si no lo logra. Para cámaras fijas, `camara_libre()` toma la primera de una lista que ve el punto sin nada en medio (el último 28 % no cuenta: la tapa abierta del contenedor está junto al punto).
- **Un rayo de prueba no ve lo transparente como transparente**: el cono de luz de la linterna (vidrio con brillo) es casi sólido en Standard y además engaña la revisión. En el acercamiento se cambia por un resplandor (luz fuerte + destellos en la cara).
- **Asomarse por una ventana**: el vidrio emisivo (5) salía blanco y no se veía quien se asoma. Vidrio con alfa 0,22 y emisión de noche 0,6: desde afuera sigue prendida y desde adentro se ve la cara. Quien se asoma va **de rodillas** con los brazos en la repisa (agachado, la cara quedaba arriba del vidrio) y a un lado de la cruz del marco.
- **Áticos con vigas más bajas que el personaje** (vigas a 5,2; Sikelpa mide 6): parado entre dos vigas y la cámara A LO LARGO de ellas (paralelas a la vista), si no una viga le cruza la cabeza.
- **Cámara dentro del set**: un personaje que mira hacia la pared de afuera deja la cámara de frente FUERA del cuarto. Voltearlo hacia adentro.
- **De cabeza en el contenedor** (`de_cabeza`): rig girado 180° en X con los pies 2,2 (a su escala) arriba de la orilla; la boca abierta se mide con rayos (`boca_bote`: lo más hondo adentro). La caída (`trayecto`, `voltea`) termina en esa misma altura.
- **Buffer de sombras lleno** (aviso de Eevee con muchas luces de adorno): `use_shadow = False` en las lucecitas decorativas (frascos, escritorio). No se nota y desaparece el aviso.
- **Objetos del set que se esconden en una toma** (la charola normal en los panes quemados, el frasco viejo cuando lo toma): `ocultar()` + `aplicar_ocultar()` (se ven por defecto) y `ver()` para los que van escondidos (charola quemada, letreros, auras). Cada bloque reescribe solo sus cuadros.
- **La hélice**: su disco de giro había quedado en el origen del mapa (padre mal puesto). `arreglar_disco_helice()` lo pega al eje a la altura de las aspas antes de `girar_helice`.
- **Movimiento suave en todo** (pedido del usuario): quien flota sube y baja y se desliza (`flotar(..., hasta=)`), aplausos cada 4 cuadros, el que barre se mece, las cámaras con acercamiento lento.
- **Lo que vio el usuario en la vista previa** (2 defectos que las fotos de 3 momentos no mostraron):
  - **Pantalla azul 1,7 s (toma 64)**: una cámara puesta a mano quedó DENTRO del marco de la puerta de la escuela (y 387,6; la puerta está en 387,8-388,3). Las cámaras a mano también pasan por `camara_libre` (un rayo que sale de adentro de una caja pega en su cara de salida y la descarta).
  - **Un tirante le tapaba el sombrero al señor (toma 41)**: su sombrero llega a 23,7 y los tirantes empiezan en 23,1, y la cámara estaba justo a la altura de los tirantes (la franja del más cercano cruzaba el cuadro). Igual que con Sikelpa: el personaje **entre dos tirantes** y la cámara **a lo largo** de ellos. Para encontrarlo: rayos en rejilla desde la cámara (qué objeto pega en cada parte del cuadro y a qué distancia).

### 93. Revisar el video renderizado, no solo la hoja de contacto (EP008, 2026-11-10)
- **Un cuadro por toma no basta**: la hoja de contacto de EP008 se veía bien, pero en el video la toma 35 salía amarilla y luego negra la mitad del tiempo. La cámara empezaba **dentro de la estatua dorada** y el acercamiento lento la sacaba a medio camino. Después del render: tira de 5 cuadros (inicio, ¼, mitad, ¾, final) de cada toma sospechosa.
- **`obj.copy()` comparte la animación**: la copia usa la MISMA acción que el original. Si después le pones llaves a la copia, también mueves y escondes al original (el parche de chicle de la toma 32 desaparecía). Justo después de copiar: `copia.animation_data_clear()`.
- **Filas con postes y cordón** (taquillas, alfombras): de lado los postes tapan a los personajes. Mejor sobre el hombro de quien da/recibe o desde arriba de los postes, y voltear al personaje hacia la cámara cuando lo avientan.
- **Re-render parcial**: borrar solo los PNG de las tomas corregidas y volver a correr `render_por_turnos.py` (renderiza lo que falta y vuelve a armar el video). Animar siempre desde el respaldo previo (`EP###_antes_animar.blend`) con semilla fija, así las tomas que no cambiaron quedan idénticas.

### 94. Rayos de luz, luces que queman y cámaras que se despejan solas (EP009, sol que se cobra, 2026-11-10)
- **Haces de luz (cilindros con emisión + transparencia BLENDED)**: en la primera revisión, 30 de 76 tomas salieron **amarillas de pantalla completa**. Si la cámara está dentro del haz (o muy cerca), ve la cara de adentro del cilindro y todo se pinta. Arreglo en `mat_rayo`: `use_backface_culling = True` (desde adentro no se ve) y **se desvanece cerca de la cámara** (Camera Data → View Distance, de 5 a 16): en los acercamientos se ve la cara iluminada y en las tomas abiertas, la columna de luz. Haces gruesos (circulos de sol de 3 de radio) con alfa ~0,3; los delgados (cadena de espejos), 0,5.
- **Luces puntuales: calcular antes de poner números**. Lo que llega es ≈ W / (4π·d²). Con 25.000 W a 6 m de la pared llegan ~55 (el sol del mapa es 3,4): la segunda mitad salió blanca, quemada. Para "prender" una casa bastan ~1.500 W a 6 m (≈3,3). Un reflector a 40 m puede llevar 40.000 W (≈2).
- **Visibilidad con UNA sola llave vale para todo el video**: `descubrir(d, frame)` ponía una sola llave en el cuadro del giro, así que Don Tapasol salió sin disfraz desde la toma 1. Siempre 2 llaves: el estado de antes en `frame - 1` y el nuevo en `frame`.
- **Cámaras que se despejan solas** (`ep9.despejar`, se usa en `camara_toma`): lanza un rayo desde lo que se ve hacia la cámara. Solo cuentan las caras de **entrada** (normal contra el rayo) a más de 1 m del sujeto (su propio cuerpo y accesorios no cuentan). Ignora rayos, burbujas, monedas y la sombrilla. Si algo tapa en el inicio o a la mitad de la toma, **gira la cámara** alrededor del sujeto (±18° … ±130°, también un poco más alto); si nada sirve, la acerca hasta antes del estorbo. Arregló 19 cámaras metidas en paredes o con Sikelpa de espaldas tapando. **La "mira" va enfrente del grupo**, no detrás de un personaje: si no, el sujeto mismo "tapa" y la cámara se acerca hasta quedar encima de él (pasó en la toma final).
- **Tomas gigantes**: `clip_end = 2000` cortaba la mitad de la sombrilla (8 km) vista desde arriba. Si la cámara está a más de 150 de lo que ve: `clip_start 0,5`, `clip_end 12000`.
- **Casas lejanas instanciadas**: dejar libre (sin instancias) donde van cámaras o escenas: la casa helada por dentro y la plaza frente a la mansión.
- **Al subir (dron) sobre la calle**: subir en vertical sobre la banqueta, no hacia atrás, porque atraviesa las casas de enfrente.

### 95. Correcciones del usuario a la vista previa: que todo se mueva junto y que la acción se lea (EP008, 2026-11-10)
- **Sin onomatopeyas en la voz** (preferencia del usuario): el narrador no dice ¡pop!, ¡boing! ni ¡fuuu!. El sonido lo pone un efecto justo al terminar la palabra (`fin_pal` en la animación, `fin()` en `armar_video.py`). Si una línea era solo onomatopeya, se cambia por una frase ("Y reventaron todos, uno tras otro.") para que la toma siga teniendo voz. **Pocos efectos**: quitar whoosh/swish que no acompañan algo que se vea. Si la librería no tiene el sonido (boing de resorte), se sintetiza con numpy en `audio/sfx_propios/` (categoría `"propio"`).
- **Lo que va encima de algo que se mueve, se mueve con eso**: si la casa baja, los personajes del porche bajan con ella cuadro por cuadro (`con_casa`), igual que el letrero y la cámara que los sigue. Si cae una casa con alguien adentro, el personaje se ancla al porche con la posición de la casa (`pos = casa + Rz @ lugar_local`) y la casa cae sin girar en X/Y para que no se despegue.
- **`obj.copy()` comparte la acción, otra vez**: el "0" del gancho se veía encimado sobre el "1" porque la copia tenía las mismas llaves de visibilidad. Toda copia lleva `animation_data_clear()` antes de animarla.
- **Recuerdos**: el aro blanco debe ser una orilla delgada (smoothstep 0,86–1,32, emisión 1,0); con 0,62–1,05 tapaba la acción. Que el recuerdo muestre la causa real ("se cayó" = su casa se quedó sin globos y cayó con él).
- **Acciones de manos (amarrar, jalar)**: una cuerda con un nudo de verdad (trébol abierto con bisel) que se "va formando" animando `bevel_factor_end`, más grande que la mano y un poco delante de ella. La cámara se aleja lo justo para que se vean las caras y el nudo.
- **Que se lea la acción**: lo que sale de un personaje (chicle, pelota) sale de su mano o boca y en su palabra, no al final de la toma. Si el blanco está detrás, se hace trampa de continuidad: en la toma 1 sale hacia la cámara y en la siguiente entra al blanco. Para "inflar", la cámara empieza en la cara soplando y se aleja hasta ver el globo crecer y desinflarse.
- **Revisar las copias de abrazos y personajes enfrentados**: `rot` 90/−90 los deja de espaldas si se invierten. Ponerlos frente a frente y un poco abiertos hacia la cámara (60/−60). El adulto se agacha y baja los brazos a la espalda del niño.
- **Cámara dentro de objetos dorados**: con el lente más abierto (54°) y más cerca se ve lo mismo sin meterse en la estatua de atrás. Una cuerda que cruza un letrero en una sola toma se esconde solo en esa toma (`ocultar_en`).
- **Humo quieto = metaball sin animar**: cada bolita sube por la columna, crece y se desvanece arriba, en ciclo (llaves en un periodo + modificador Cycles). Son pocas llaves y vale para todo el video.

### 96. Revisión de la vista previa de EP009: reutilizar el Pueblo, onomatopeyas fuera y la idea que se vea (2026-11-10)
- **Casas inventadas de cajas = "plasticoso"**: en un mapa nuevo, primero el catálogo. Se anexó una copia de `Casa_Base`, `Farol_Base` y `Escuela` del Pueblo (`bpy.data.libraries.load(..., link=False)`; el original no se toca) y se le agregó tinaco. Las del fondo: la MISMA casa unida en una sola malla (`unir()` en `construir_ciudad.py`), ventanas con luz cálida y niebla: con 8 500 copias se ve un mundo sin fin y sigue rápido. Las cercanas a la calle principal van completas.
- **El color de cada copia** está en propiedades del vacío que la instancia (`wall_color`, `roof_color`…; atributo `INSTANCER` en el material). Para "prender" una casa se anima esa propiedad (`e.keyframe_insert('["wall_color"]')`).
- **Piso negro**: era asfalto oscuro en 9 km a la sombra. Pasto con textura en todo el mundo + asfalto gris claro + banquetas de losa; nunca un piso de un solo color oscuro.
- **Niebla que se apaga por toma**: la niebla lee `sc["niebla"]` con un nodo Attribute tipo `VIEW_LAYER`; se anima a 0 en la toma desde arriba de la sombrilla.
- **Algo gigante visto de muy lejos** (la sombrilla de 8 km): cámara a 20 000 con `clip_start` 20 (con 0,1 la tela se perdía por precisión). Para que se lea "sombrilla": gajos de dos colores fuertes, orilla en ondas y una punta grande.
- **Onomatopeyas en la voz ya aprobada**: `quitar_onomatopeyas.py` las corta (sin créditos) y deja marcas `"sfx"` para que la animación y los efectos sigan cayendo en su momento; el subtítulo las salta.
- **Pensamientos**: la nube chiquita en la frente tapaba la cara y el objeto se salía. Ahora un corte "adentro del pensamiento" con orilla de nube pegada a la cámara (`ob.marco_pensamiento`).
- **Choques con la utilería**: la maquinita tapaba a los vecinos; el tendedero y las plantas estaban en el camino. La utilería va en la orilla de atrás de la banqueta y la gente al lado de la maquinita, nunca con la cabeza metida.

### 97. Piso que parpadea, rayos que velan y derretir de verdad (EP009, segunda revisión, 2026-11-10)
- **"El pasto y la calle se traspasan"** = parpadeo de profundidad (z-fighting): dos pisos a la misma altura (la placita del gancho y la banqueta, ambas en 0,4) o casi pegados vistos de lejos (asfalto 4 cm arriba del pasto). Arreglo: nada se encima a la misma altura, el pasto en −0,03, calles lejanas más gruesas (0,12) y cámaras normales con `clip_start` 0,3 (con 0,1 la precisión se acaba a ~250 m).
- **Utilería encima de otra cosa**: la maquinita de la calle estaba exactamente donde iba un poste de luz (x 24): el poste le partía el letrero. Antes de poner algo, revisar que no caiga en un poste, farol o árbol del mapa.
- **Rayo de luz que vela al personaje**: si alguien está dentro del círculo de sol, la columna del rayo lo tapa con un velo amarillo. El rayo de las ventanitas se vuelve transparente en sus últimos 7 m (`ob.rayo(..., suelo=7)`): se ve bajar del cielo y el personaje se ve limpio. Y la cámara nunca dentro de un rayo.
- **Polvito del rayo = copos gigantes** si pasa cerca de la cámara: el material de las motitas se borra a menos de 6–14 m de la cámara (`polvo_lejos`).
- **Derretir de verdad** (pedido: "que de verdad se haga agua"): no basta aplastar el rig. Agua con material propio (transparente, muy brillosa, ondas que se mueven con `frame`, orilla redondita), charco con lóbulos que crece **acostado en el techo** (malla doblada a las dos aguas y escala uniforme), chorritos que bajan por la pendiente y gotean del alero, nieve aguada a los pies, la bola de nieve con una forma "Derretir" (abajo se escurre con gotas gordas; la cara no se toca) y material mojado.
- **Composición en 9:16**: el cuadro mide solo ~29° de ancho con 50° de alto. Dos cosas lado a lado casi nunca caben; antes de poner la cámara, calcular el ángulo de cada cosa (o apilarlas en vertical: una cerca abajo, otra lejos arriba) y revisar en foto.
- **`keys(..., 'CONSTANT')` cambia TODA la curva**: la ayuda pone la interpolación a todas las llaves de esa propiedad, no solo a las nuevas. Si una toma posterior agrega llaves a la misma propiedad (la escala de Don Tapasol), revisar que no le quite lo suave a lo de antes.

### 98. Revisar cada fotograma antes de la vista previa: nadie atraviesa nada (EP009, 2026-11-10)
- Pedido del usuario: "que ninguna persona esté atravesando un objeto por una ventana… revisa cada fotograma". La hoja de 4 fotos por toma NO basta: se escaparon una vecina dentro del poste del farol, Sikelpa dentro del panel de su espejo, Don Tapasol dentro del caballete del techo, el palo de la sombrillita atravesándolo y gente encimada.
- **Revisión automática** (`Episodios/EP009_El_Sol_Cuesta_Mil_Pesos/scripts/revisar_ep009.py`): en 3–5 cuadros por toma, rayos de la cámara a cabeza y pecho de cada personaje en cuadro (TAPADO) y choque de mallas del cuerpo (sin pies) contra casas instanciadas, muebles, utilería y otros personajes con `BVHTree.overlap` (ATRAVIESA). Se descartan efectos (chispas, migas, monedas en el aire) y contactos que deben pasar (sentado, escalera, objeto en la mano).
- **Revisión a ojo**: hoja con un cuadro cada 10 fotogramas de la vista previa ya renderizada (no hace falta volver a renderizar para revisar).
- Reglas: personajes a ≥ 2,6 m (los brazos de Roblox abiertos miden casi 4); nadie dentro de la huella de un objeto grande (espejo de 9 m, rueda, poste, farol, maquinita, palo de sombrilla) — pararlos al lado calculando con la orientación del objeto (`junto_espejo`); si una acción se repite con llaves en un ciclo (`for f in range(...)`), que el ciclo termine en su toma (el abanicar de la 34 dejaba a Sikelpa de espaldas en la 35); una cámara dentro de un farol/objeto da un cuadro negro.

### 99. Vestir a un NPC: medir su cara primero y que la ropa tape las esquinas (EP012, Don Leño, 2026-11-10)
- Cada cara de Roblox tiene los ojos y la boca a distinta altura. En Mark los ojos están a **0,66–0,79** del alto de la cabeza y la boca a 0,22–0,41. Se adivinó "~0,45" y el gorro tapó los ojos; las puntas de la sonrisa parecían ojos rasgados. **Antes de ponerle gorro, cejas, bigote o barba**: foto ortográfica de frente solo de la cabeza (sin accesorios) y medir las filas oscuras. Así se acomoda: doblez del gorro arriba de las cejas, cejas justo arriba de los ojos, nariz entre ojos y boca, bigote arriba de la boca y barba abajo de la boca.
- **Ropa de esquinas redondas encima de piezas cuadradas** (botas, cañas, puños): una superelipse de medio ancho `a` deja la esquina cuadrada por fuera, y en las fotos se veía el pantalón por los lados. Hay que agrandarla `2^(1/e)` veces (con `e` = 10 casi no se nota lo redondo) y medir la pierna **que se ve** (todas sus piezas), no solo la del hueso.
- **Cambiar la camisa de fábrica** (p. ej. rosita → franela a cuadros): el material se cambia solo en las mallas de ese personaje (torso y mangas). La parte de arriba del `LowerTorso` todavía trae la camisa vieja (arriba del cinturón), así que se tapa con un faldón de la tela nueva. Como se pierden las bolsas y los botones de la textura, se agregan en 3D.
- Para que un personaje "no se vea básico": textura en todo (franela, lana, cuero, pelo con relieve), detalles chicos (botones, broches, agujetas, bolita del gorro) y foto de frente, de cara y de espalda contra la anterior (`antes_despues.jpg`).

### 100. Emparentar recién creado y escaleras en un cerro de escalones (EP010, isla, 2026-11-11)
- **Síntoma**: la mansión salió flotando detrás del cerro, corrida exactamente lo que medía la posición de su objeto padre.
- **Causa**: al crear un objeto con `location` y emparentarle piezas en el mismo script, `padre.matrix_world` todavía es la identidad (Blender no la recalcula hasta actualizar la escena), así que `matrix_parent_inverse = padre.matrix_world.inverted()` no compensa nada.
- **Solución**: usar `Matrix.Translation(padre.location).inverted()` (o llamar `bpy.context.view_layer.update()` antes de leer `matrix_world`).
- **Escaleras en un cerro de escalones**: si el terreno sube más rápido que la escalera, los escalones del cerro la tapan. Abrir un corte en el terreno donde va la escalera, con muros a los lados que llenen el corte.

### 101. Rayos de luz y cosas que brillan encima de un personaje (EP010, 2026-11-11)
- **Síntoma**: de cerca, un rayo de luz "casi transparente" (alfa 0,1 abajo) pintaba de blanco a Sikelpa y a su burbuja.
- **Causa**: en un material que mezcla Transparente con Emisión, la emisión **se suma** aunque el alfa sea bajo: con brillo 9 y alfa 0,1 todavía suma ≈ 1 (blanco). Además, la burbuja estaba DENTRO del rayo, y la cara de enfrente del cilindro le quedaba encima.
- **Solución**: brillo bajo (con View Transform Standard, 2–2,5 ya se ve blanco puro) y, con la cámara cerca (Camera Data → View Distance), el rayo empieza arriba de la burbuja (transparente desde el piso hasta ~9 de alto); de lejos llega hasta el piso. El círculo, el resplandor y las chispas en los pies dicen que la luz cae sobre él.
- **Textos que cambian (cuenta, porcentajes)**: un texto por valor, y se ve uno a la vez con escala 1/0 en saltos (CONSTANT). Si los cambios van a menos de 6 cuadros, no se le pone saltito: si no, la clave del saltito vuelve a mostrar el valor anterior y los números se enciman.

### 102. Modelos de Roblox Studio que no son R15 normales: ciervo, R6 sin plantilla y escenarios (EP012, 2026-11-11)
- **Esqueleto propio (ciervo de 30 piezas)**: no pasarlo por `armar_rig_r15_auto`. `_G.CL_juntas` + `rig_motor6d.py` arman cada hueso como su Motor6D. **El hueso va en `CFrame de la pieza Part0 * C0`**, no en "marco del hueso padre * C0": solo coinciden si el C1 del padre no tiene desplazamiento, y con ese error las patas y la cabeza quedaban corridas hasta 4,5 studs en las animaciones. Comprobado: la misma pose en Studio y en Blender difiere menos de 0,01 studs.
- **Copias R6 → R15 sin plantilla del lugar** (`CreateHumanoidModelFromDescription`): la cabeza R15 NUEVA de Roblox pinta mal la cara de calcomanía (bloques negros, la cara de lado). En Blender se cambia por una cabeza clásica y se pone la cara del kit (`caras_textura.preparar(..., cabeza_clasica=Calvo_Head)`): así además puede llorar o reír según la escena. **Si el personaje debe conservar SU cara de Roblox** (el encapuchado): exportar otra copia con la cabeza R6 (Part con SpecialMesh y su calcomanía), donde Studio sí pinta la cara limpia en la textura del cuerpo, y ponerle a la cabeza clásica el material del cuerpo con esa textura (misma distribución). `AssetService:CreateEditableImageAsync` no sirve: Studio no da permiso de leer calcomanías de otros.
- **La ropa clásica sale amarilla** si se exporta en cuanto se crea la copia: Studio arma la textura del cuerpo (camisa, pantalón, cara) DESPUÉS de la primera exportación. Exportar dos veces (la primera a una carpeta temporal) y revisar que el `.mtl` tenga la textura del cuerpo de 916×568.
- **Piezas de un Model (capa, máscara) vueltas Accessory sin Attachment**: el Humanoid las acomoda como sombrero ENCIMA de la cabeza (la capa salió en la cabeza, "Head 100 %"). Ponerles un Attachment que coincida con uno de la cabeza (`CL_r6a15` ya lo hace).
- **Texturas de Material de Roblox** (pasto, madera, roca, cuero): vienen casi blancas y Roblox las multiplica por el color de la pieza; el importador de OBJ no, y salían blancas. `armar_rig_r15_auto`/`rig_motor6d` multiplican las grises; en escenarios también las claras con poco color (`materiales_escenario` de EP012).
- **Guardar un JSON largo de Studio**: lo que regresa `execute_luau` se lee del transcript con un script (marcadores `===NOMBRE===`), sin volver a escribirlo a mano.
- El visor de Studio puede quedarse en negro después de los diálogos de exportar: no importa para exportar; las fotos de prueba se sacan en Blender.

### 102b. Agrandar algo del catálogo: revisarlo de cerca primero (EP010, lote 3, 2026-11-11)
- Lo que se veía bien chiquito puede fallar en grande. En `objetos_cartoon.concha` la cobertura de azúcar queda **debajo** del domo del pan (solo se ven las rayitas), y el `gato` del catálogo son 10 cajas: se ve crudo del tamaño de una casa. Antes de agrandar un objeto ×10, sacarle una foto de cerca; si falla, hacer la versión del episodio (o arreglar la del catálogo, avisando en `docs/CAMBIOS.md`).
- **Contorno (solidify) en piezas delgadas** (bigotes, hilos, varitas): las engorda y parecen barras. Esas piezas van en un objeto aparte sin contorno.
- **Vapor**: tubitos delgados (radio ≤ 0,035 del pan) y muy transparentes (alfa ~0,25). Con alfa 0,5 y más gruesos parecen dedos de plástico.
- **Nubes de bloque vistas desde abajo**: con mucho brillo (emisión) se ven como una hoja plana. Con poco brillo (~0,2), bultos encima y abajo y orillas redondas (bisel), el sol les da forma.
- **Una nube que se ve de cerca** (columpio, EP010): al usuario las cajas no le parecieron nube. Funcionó una nube de **metaballs** (`objetos_ep010.nube_suave`): elipsoides planos abajo y bolas grandes que se funden arriba = una sola superficie lisa, sin bolitas sueltas; material blanco mate con orillas un poco más claras y abajo azulado.

### 103. Ola gigante de caricatura (EP010, lote 4, 2026-11-11)
- **Espuma de bolitas = se ve falsa**. Las esferas sueltas parecen una fila de bolitas, y los conos colgando parecen carámbanos. Lo que funcionó: **metaballs** (las bolas se funden en una sola superficie), **convertidos a malla** al construir con `bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))`. Si se dejan como metaballs y su padre se mueve, Blender los recalcula en cada cuadro y el render se hace lento. Aplica también a nubes.
- Si las bolas quedan más separadas que su radio, salen franjas o cuentas sueltas: radio ≥ separación.
- **La espuma no debe tapar la forma**: va solo en el gorro de la cresta y en la orilla del labio que rompe. Entre las dos se tiene que ver el labio azul enroscado: eso es lo que hace que se lea como ola y no como pared. Los "dedos" de espuma salen del labio **hacia adelante** (se derraman); no cuelgan derechos.
- **Contraluz**: si el sol viene de atrás de la ola (para que su sombra caiga sobre el pueblo), su cara queda oscura y plana. Hay que darle luz propia (emisión ~0,55 del mismo color), un degradado fuerte de marino abajo a turquesa casi blanco arriba, el techo del tubo más oscuro y la orilla clara (Fresnel).
- Vetas en la cara: pocas y suaves. Con muchas rayas parejas, la ola parece papel tapiz.

### 104. Efectos de sonido que siguen sonando después de su acción (EP010, borrador del gancho, 2026-11-11)
- **Síntoma**: en el borrador, el tecleo de la burbuja del niño rico siguió sonando mucho después de que la toma cambiaba. El usuario: "MUY IMPORTANTE… para los próximos videos y los actuales".
- **Causa**: `armar_video.py` pegaba cada clip completo, y en la librería `typing`, `tick` y `reverse_swell` duran 6 s y `sub_drop` 4,7 s. Las letras salen en menos de 1 s.
- **Solución**: cada efecto se corta con un fade corto al terminar la toma donde empieza, y se puede acortar más con un 5.º dato (segundos o `"hasta:<cuando>"`). El tecleo lo genera la animación (`audio/efectos_animacion.json`: primera y última letra de cada tanda) y suena solo mientras aparecen letras.
- **Antes de usar un efecto**: medir su duración con `ffprobe` y preguntarse cuándo empieza y cuándo termina la acción en pantalla. Al revisar un borrador, escuchar cada efecto pensando en eso.

### 105. Encuadre fuera de la zona segura de Shorts (EP010, borrador de las tomas 1-14, 2026-11-11)
- **Síntoma**: el rayo no se veía caer (a los 7 s). A los 14 s casi no se veía a quién le cayó. La abuela y la hermana estaban muy abajo, que es donde YouTube pone el título, el canal y "suscribirse". A la niña le sobraba cielo arriba, "GIGANTE" estaba casi en la orilla y el gato solo salía de lado.
- **Causa**: las cámaras se ponían a ojo, con coordenadas fijas, y solo se revisaba que nada tapara. Nadie medía dónde caían las caras y burbujas en el cuadro de 9:16.
- **Solución**:
  - `Herramientas/blender/zona_segura.py`: `encuadrar()` pone la cámara para que cabezas y burbujas queden centradas en la zona segura (x 6–86 %, y 12–70 %), y `revisar()` lo comprueba.
  - En el EP010, `cam_zona()` encuadra cada toma así y `revisar_zona.py` revisa las tomas 1-14 antes del borrador. Pasaron de 37 avisos a 5, y los 5 son a propósito.
  - El rayo ahora viaja encendido a la nueva persona y la cámara lo sigue hasta quedar de frente.
  - El gato sale de frente y de lado.
- **Trampas**:
  - Una burbuja que gira hacia la cámara (TRACK_TO) hay que medirla ya volteada, o su ancho sale mal.
  - Con `elev` muy negativo, la cámara queda bajo el pasto: el cuadro sale todo verde. `cam_zona` sube la elevación sola.
  - `despejar()` puede meter la cámara dentro de un objeto: usar `libre=False` cuando la posición ya está calculada.
  - Un golpe de zoom saca cosas de la zona: no usarlo en tomas con texto cerca de la orilla.

### 106. Cosas encima de la cabeza que chocan con el gorro, y objetos medidos ya ocultos (EP010, bloque 3, 2026-11-11)
- **Síntoma**: el foco del apodo quedaba encima de la hélice del gorro de Sikelpa. Además, los dados y los focos salían fuera de cuadro, y el x2 del gancho se quedaba en el balcón todo el video.
- **Causa**:
  - Se ponían a la altura de la coronilla, que no cuenta el gorro ni la hélice.
  - La cámara automática medía el objeto en el último cuadro de la toma, cuando ya estaba oculto, y entonces no lo contaba.
  - `objeto_en`/`ver` solo oculta a los hijos que existen al llamarlo: el x2 se pegó a la burbuja después.
- **Solución**:
  - Lo que va arriba de alguien se pone en `tope_cabeza(papel, f)` + 0,6, con el punto más alto de todas las piezas de la cabeza.
  - Medir dados y focos en un cuadro donde sí se ven (`f_obj = b - 2`, o antes de que el número empiece a parpadear).
  - Llamar `ver()` después de pegar los hijos, o llamarlo también para cada hijo nuevo.


### 107. Luz de color pegada a la cara que pinta la nariz, y cámara que atraviesa techos (EP012, bloque 1, 2026-11-11)
- **Problema**: los ojos rojos del ciervo llevan una luz roja (para que brillen en el bosque) que estaba justo frente al hocico: el usuario vio la **nariz roja**. Además, el dron de la toma 1 bajaba atravesando el techo de una cabaña (cuadros negros en el borrador) y un poste de la bodega quedaba entre la cámara y el vecino.
- **Solución**:
  - Luz de un efecto que no debe teñir al propio personaje → **light linking**: la luz con `light_linking.receiver_collection` = colección con las piezas del personaje en `EXCLUDE` (Eevee lo respeta). Solo brillan los ojos (material emisivo) y la luz sigue pintando el entorno.
  - Drones que bajan al pueblo: trazar el camino por la calle o por el hueco entre casas (medir el alto de las casas: las cabañas del bosque miden 22,3 con chimenea) y revisar el borrador cuadro por cuadro, no solo las fotos de inicio/mitad/final.
  - Si un poste/columna tapa en una toma corta donde no sale el techo, se puede esconder solo en esa toma (`hide_render` con llaves) en vez de mover a todos.
  - **Recuerdos SIN marco** (pedido del usuario, EP012 toma 11): los recuerdos ya no llevan `marco_recuerdo` ni `marco_pensamiento`; se cuentan como una toma normal (la voz dice que es antes). Vale para los episodios actuales y los que siguen.
  - **Agarrar algo fijo (un hacha atorada, una manija)**: primero MEDIR dónde quedan las manos del personaje en la pose (`ep.mano(...)` con el rig en el origen) y poner el objeto ahí (o mover el objeto/corte a esa altura). En EP012 el corte del árbol estaba a 1,5 y las manos de Sikelpa al jalar quedaban a 2,9: el usuario vio que "la mano no toca el hacha". Para jalar sin soltar: dos poses con las manos a la MISMA altura y que solo se deslicen a lo largo del mango.

### 108. Bloques ya aprobados con caras fuera de la zona segura, cámaras que atraviesan paredes al alejarlas y personajes que se enciman (EP011, revisión antes del borrador, 2026-11-11)
- **Problema**: EP011 se animó antes de la regla de la zona segura: `revisar_zona.py` dio 85 avisos (cabezas cortadas arriba, personajes pegados a la orilla). Al corregir alejando la cámara, varias quedaron dentro de paredes, de la puerta del refri o detrás del vidrio de la puerta. Al mover la cámara, la taza de la toma 58 se salió del cuadro. Y en el final (60–65) dos personajes a 2,3–2,9 de distancia se metían uno en el otro con los brazos.
- **Solución**:
  - `zona_segura.reencuadrar(camara, cuadros, rigs, objetos)` corrige una cámara **ya hecha** con todas sus llaves y conserva su movimiento: la gira poquito (paneo e inclinación, sin ladearla) y, si las caras no caben, **abre el lente** hasta 78°, sin moverla. Solo la aleja si el lente no alcanza. En el episodio, `scripts/zona_ep011.py` la aplica a cada sub-cámara con avisos y `animar_ep011.py` la llama solo al final de cada bloque.
  - Solo cuentan los personajes que de verdad salen (el centro de su cara en cuadro en 2 de 3 momentos). El que se asoma por la orilla no se mete a fuerzas: en la 6b y la 41b eso empeoraba la toma.
  - Insertos a propósito en `EXCEPTO` (gafete, pies, piso con la sombra, primerísimo plano de ojos, letrero, alguien que entra por la orilla). Los objetos clave de una toma (taza, cartel) van en `OBJETOS` para que también queden dentro.
  - Después de corregir: correr de nuevo la revisión de tapados (`scripts/revisar_ep011.py`: tapado, atraviesa, cabeza cortada, ojos) y ver las hojas de todas las tomas.
  - Dos personajes Roblox lado a lado (brazos incluidos) miden ~4 de ancho: separarlos **≥ 3,6–4** si saludan o mueven los brazos; para pasarse algo, que esperen separados y solo se acerquen en la palabra (`junto_a_mano`), y luego regresen.
  - **Objeto que no sigue a la mano** (la taza de EP011 nunca se vio: quedaba a ~1000 de distancia): `en_mano` leía `o.matrix_world` justo después de mover el objeto, pero si está **oculto en el viewport** (llaves de `ver`/`esconder`) Blender no lo evalúa y la matriz se queda vieja. Arreglo: armar la matriz a mano con `Matrix.LocRotScale(p, rot, escala)`. Los `en_mano` de `ep6`–`ep12` tienen el mismo patrón: corregirlos al usarlos. Revisarlo con `revisar_objetos` (decía «fuera de cuadro» en todas las tomas).
- **Respaldo**: `Respaldos/EP011/EP011_antes_de_zona_segura_2026-11-11.blend`.

### 107b. La ola rota tapaba todo y las cámaras quedaban adentro de la ola (EP010, bloque 5, 2026-11-11)
- **Síntoma**: tomas todas azules (la cámara estaba dentro de la ola), casas cubiertas de espuma blanca como nieve, y surfistas que no se veían delante de la ola. Además, la ola pasaba por la mansión 90 cuadros antes de llevársela.
- **Causa**:
  - `romper_ola` estiraba la ola 1,6 veces hacia atrás: dejaba una capa de espuma de 500 de largo encima de la isla.
  - El frente con espuma y rocío va unas 66 unidades delante del origen de la ola (117 una vez estirada), y se calculó como si estuviera en el origen.
- **Solución**:
  - Medir la ola en el mundo (bounding box de la ola y sus hijos en varios cuadros, `scratchpad/medir_ola.py`) antes de poner cámaras o personajes junto a ella.
  - Después de romper, escala en y 0,38: queda una franja angosta y el agua detrás se ve tranquila.
  - Los surfistas van a origen + 42 y las cámaras siempre delante del frente o arriba de su altura.
  - Sincronizar la llegada al lugar (la mansión) con la palabra.

### 109. Gancho de adelanto con voz nueva al principio, sin re-animar el episodio (EP011, 2026-11-11)
- **Pedido**: el usuario quiso un gancho más fuerte (opción A): 2 líneas nuevas al principio («Esa noche, algo me perseguía dentro de la tienda…» / «Te cuento cómo pasó.»), con la voz de las otras 65 ya aprobada y todo animado.
- **Solución**:
  - `voz_elevenlabs.py --anteponer`: pide solo las líneas nuevas (≈70 créditos), con las primeras de la voz como contexto y el mismo volumen, y las pega antes. Después `recortar_pausas.py` + `tomas_desde_voz.py`.
  - Las tomas viejas se movieron +2 (y ~4,4 s). En vez de re-animar los 7 bloques (con llaves viejas de objetos que se quedarían en tiempos equivocados), `scripts/recorrer_tiempos_ep011.py` mueve **todas** las llaves de todas las acciones, los marcadores y el final de la escena, toma por toma (estirando lo poquito que cambie cada una). Se comprobó con fotos: las tomas aprobadas quedan idénticas en sus tiempos nuevos.
  - `ep11.OFS = 2`: `T(n)` y `palabra(n)` siguen usando los números de siempre; el adelanto se lee con `TA(k)` / `palabraA(k, w)`. `zona_ep011` y las hojas usan los números de `tomas_voz.json` (1–67).
  - El adelanto muestra lo más fuerte **sin revelar el giro** (la sombra en lo oscuro, no que es Beto). El rebobinado VHS (`rebobinar_ep011.py`, copia del de EP010 que también sirve con el borrador de 1 de cada 2 cuadros) va sobre los cuadros ya renderizados.
  - Respaldo de todo antes del cambio: `Respaldos/EP011/antes_opcion_A_2026-11-11/`.

### 108b. Efectos de sonido de más y cortes que se oyen (EP012, vista previa, 2026-11-11)
- **Problema**: muchos efectos (29 en 2 min) y, al recortarlos en el cambio de toma, se oía el corte.
- **Solución**: pocos efectos (uno por acción importante, ~20 en 2 min) y en `armar_video.py` cada efecto recortado se apaga con un desvanecido seno de 0,15–0,6 s que termina antes del corte; ambientes con 0,4–0,5 s de entrada y salida. Para un efecto que cae en medio de una frase, un 5o dato corto (0,3–0,9 s).

### 110. Vista previa lenta en escenas con muchas luces: lo caro es la resolución de las sombras (EP011, 2026-11-11)
- **Problema**: la vista previa de EP011 (4.073 cuadros, casi todo dentro de la tienda) medía ~3,7 s por cuadro (hasta 7 s en algunas tomas): ~2,5 h con 2 Blender. La escena tiene 123 luces con sombra (tubos, refris, faroles y casas del pueblo).
- **Medido** (mismo cuadro): sin sombras 1,7 s contra 3,8 s; menos rayos de sombra (4 → 1) casi igual; reserva de memoria de sombras 512 → 1024 → 2048 casi igual; **`shadow_resolution_scale` 0,5: la mitad del tiempo**; sombra solo en las luces cercanas a lo que ve la cámara (radio 9): casi nada, porque Eevee ya casi no paga por las lejanas (se probó y se quitó).
- **Solución**: `render_paralelo.py --rapida` (8 muestras + sombras a media resolución): 34–44 % del tiempo y PSNR 40–43 dB contra la normal, no se distingue lado a lado. Con 2 Blender, EP011 baja a ~1 h.

### 111. Corazones de cariño que parezcan corazones (EP012, 2026-11-11)
- **Problema**: los corazones de línea transparentes y luego unos "gorditos" deformes no gustaron; además subían en tanda "como si nada".
- **Solución**: corazón de toda la vida (dos lóbulos redondos y la punta abajo, como el emoji), **lleno y rosa**, sin hueco ni transparencia (`vfx._corazon_solido`). Que **nazcan del personaje** como en los juegos: `vfx.corazones_emisor(nombre, col, f0, f1, objetivo=rig, hueso="UpperTorso", offset=...)` los suelta uno tras otro desde el pecho, **por detrás** (`detras=` ~1; ~3 en animales grandes), con un saltito, suben por los lados y por arriba de la cabeza (`alto=`) sin tapar la cara y se desvanecen solo al final, mientras dure el momento.
- Las líneas de olor de caricatura van en **blanco crema**, no de colores.

### 112. Parados en una tabla de surf o patineta: nada de piernas juntas (EP010 T41, 2026-11-11)
- **Problema**: todos surfeaban con las piernas juntas y rectas: "se notan muy tiesas".
- **Solución**: **una pierna adelante y otra atrás**, rodillas dobladas que suben y bajan suave, torso un poco inclinado, cuerpo y cabeza mirando al frente y brazos abiertos para el equilibrio. Medidas que funcionaron: muslo de adelante 30° con rodilla 40°, muslo de atrás −10° con rodilla 20° (la cadera baja igual con las dos piernas y los pies quedan sobre la tabla), cadera ~0,075 más abajo, punta del pie de atrás 30° arriba y un vaivén de ±4–8° en las rodillas. La llave va cuadro por cuadro con la tabla debajo; si los brazos hacen otra cosa (empujar), se cambian solo los brazos.
