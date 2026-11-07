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
17. **Franjas que parpadean a lo lejos** (z-fighting). → Superficies casi coplanares (0,03 de separación) a mucha distancia. → Separar ≥ 0,5 o esconder la superficie de abajo; `clip_start` de cámaras ≥ 0,5 para tomas lejanas.
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

