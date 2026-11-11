# 05 — Cámaras y tomas

## Tipos de toma que ya funcionan (EP001)
| Toma | Cómo se arma | Ángulo vertical |
|---|---|---|
| **Dron de inicio** | sobre el centro de la calle, frente al personaje, baja de ~11 a ~4,6 de altura y retrocede mientras él se acerca | 46→40° |
| **Frontal caminando** | delante del personaje (8,5 → 5,2), a la altura del pecho/cara, empuje suave | 36→30° |
| **Lateral** | al costado desde la calle, sigue en paralelo; baja cuando el personaje se agacha | 42→40° |
| **Giro 360** | órbita alrededor (r 6 → 3,1), empieza de frente, termina detrás de un poste (transición) | 44° |
| **Revelado desde poste** | empieza tapada a 0,45 del poste, se desliza 1,9 y retrocede con el personaje | 46° |
| **Cámara de frente corriendo** | delante 4,7 unid, mira su cara, vaivén lateral 0,38 al ritmo de los pasos + temblor + roll ±3,5° | 52→46° |
| **Ángulo bajo de llegada** | cámara a ~1 de altura, el personaje corre hacia ella | 48→40° |
| **Seguimiento por detrás** | atrás-izquierda, mirando hacia adelante (se ve el destino) | 46→40° |
| **Desde arriba de escaleras** | en el descanso, mira hacia abajo cómo sube | 52→40° |
| **Detalle de acción** (mano en la puerta) | cerca, dentro del pórtico, entre columnas y pared | 48→42° |
| **Primer plano de cara** | 4,4 → 3,0 de distancia, el personaje voltea a la cámara | 34→28° |

## Reglas
- Una cámara por toma (`CR_Cam_S#_Nombre`) con su marcador en el fotograma de inicio.
- **Una toma por línea de voz** (1,5–2,5 s; ClusterK corta cada 1,5 s), el corte cae en la palabra. El final puede sostenerse un poco (suspenso). Las duraciones salen de `audio/tomas_voz.json`.
- Temblor: suma de senos con frecuencias no múltiplos (función `shake`). Poco en tomas tranquilas (0,01–0,03), más al correr (0,07–0,08).
- Zoom in/out animando el ángulo de la lente (`angle_y`), no solo moviendo la cámara.

## Revisión obligatoria
1. `Herramientas/blender/revisar_camaras.py` (en segundo plano o en el Blender del episodio). Cada cámara lleva la propiedad `sujeto` con lo que sigue (uno o varios rigs u objetos):
   - Rayos de la cámara a cabeza y pecho → reporta objetos que tapan.
   - Rejilla de rayos → reporta objetos cercanos que ocupan > 22 % del cuadro (el piso no cuenta).
   - Reporta cuándo la cabeza/pecho salen de cuadro.
   - `EXCEPT`: rangos de fotogramas tapados a propósito (transiciones).
2. Hoja de contacto: fotos de inicio/mitad/fin de cada toma a 22 % (`hoja_contacto.py` + `componer_hoja.py`) → revisar a ojo.
3. Solo con **0 obstrucciones** se renderiza.

## Zona segura de Shorts (pedido del usuario en EP010, 2026-11-11): revisarla ANTES de entregar
En YouTube Shorts, abajo tapan el título, el canal y "suscribirse"; a la derecha están los botones y arriba la barra.
- **Zona segura** (x de izquierda a derecha, y desde arriba): x 6–86 %, y 12–70 %. Caras, burbujas, letreros y el objeto del que se habla van **centrados** ahí, con margen. Si todo queda abajo y sobra cielo arriba, se sube y se agranda.
- **Encuadre automático**: `Herramientas/blender/zona_segura.py` → `encuadrar(puntos, direccion, elev, ang, centro, llenar, zona)`. Los puntos son `puntos_cabeza(rig, f)` y `puntos_objeto(burbuja, f)`, y la función devuelve dónde poner la cámara y hacia dónde mirar para que queden centrados. Las burbujas que giran hacia la cámara se miden ya volteadas. Desde abajo (`elev` negativo), la cámara no debe quedar bajo el pasto.
- **Revisión**: `zona_segura.revisar(f, camara, rigs, objetos)` en 3 momentos de cada toma y al inicio de cada sub-cámara (EP010: `scripts/revisar_zona.py -- 1 14`). Luego **mirar la hoja de fotos**. Solo se aceptan avisos a propósito, como algo enorme arriba del sujeto (ola, rayo, lluvia).
- **Corregir una cámara ya hecha** (lección 108): `zona_segura.reencuadrar(camara, [f0, fm, f1], rigs, objetos)`. Gira poquito y, si no caben, abre el lente en vez de alejarla (alejarla la metía en paredes). Luego volver a revisar los tapados y ver las hojas.
- **La acción pasa a otra persona** (el rayo elige a otro): la cámara **sigue la acción** (el rayo viaja encendido y la cámara lo acompaña) y **termina de frente y grande** en la nueva persona.
- **Algo que cae del cielo sobre alguien**: la cámara llega antes de que caiga, se ve bajar completo hasta la persona y después se aclara para que se vea su cara.
- **Sujeto importante** (el gato gigante): enseñarlo **de frente** y también de lado.
- **Texto casi en la orilla**: alejar un poco la cámara para que se lea completo y con aire.

## Calidad de cada toma (pedido del usuario en EP003, 2026-11-07)
**El storyboard (Three.js) es rápido y sencillo**: sirve para decidir si la historia y las tomas gustan; no se le exige esta calidad. **Esta lista la cumple Blender** al animar y al poner efectos (el script de animación de cada episodio y `revisar_camaras.py`), toma por toma, antes de renderizar. Nada realista: estilo Roblox, pero sin verse básico.
1. **Comer y agarrar de verdad**: el objeto va a la boca al morder (con migas que caen y sonido) y se achica por mordida; lo que se agarra queda en la palma o en el asa, no flotando junto a la mano. Si "sostiene" algo, verlo en la foto y comprobar que sí lo tiene (`revisar_agarre.py`). Y que **se vea y se distinga**: de frente a la cámara (no de canto), grande, fuera de la franja de los subtítulos y de un color que contraste con la mano o la ropa (papel crema sobre guante blanco, no blanco sobre blanco). Comprobarlo con `revisar_objetos.py` (`render=True`).
   - **Morder** (prueba C, 2026-11-08): boca abierta ~6 cuadros antes del contacto; en el cuadro de contacto el borde toca la boca y en el siguiente se cambia a la versión mordida; migas con `vfx.migas_mordida(..., f_mordida, f_mastica)` (dos tandas: al morder y al masticar; mismo costo de render que sin migas, iguales al renderizar por tramos, no suben a los ojos); después **enseñar el mordisco de frente a la cámara**.
   - **Objeto en la mano con personajes de visera** (prueba A): la cámara un poco abajo de los ojos y, si puede, el objeto sube a la cara; comprobar con `revisar_ojos.py`.
2. **Encuadrar la cara**: en planos medios y primeros planos la cabeza va en el tercio superior, completa (sin cortar la frente ni el gorro), dentro de la zona segura de Shorts.
3. **Nada tapa a quien está en foco**: rayo cámara→cabeza/pecho limpio. Si algo tapa, mover la cámara o el objeto, no dejarlo.
4. **Cámara siempre viva**, con sentido: acercamiento lento, deslizamiento o seguimiento en cada toma; nunca una cámara clavada. Golpes de zoom solo en los golpes de la historia. Respetar la guía 9:16.
5. **Ambiente**: polvo en pisadas al correr, líneas de velocidad, brillitos en lo mágico o lo bonito, papelitos u hojas cuando aplique; pocas y acordes a la escena.
6. **Cuerpo con sentido**: mezcla suave entre poses con un pequeño sobrepaso, torso inclinado al correr, anticipación antes de un salto, brazos que no atraviesan el torso. Las piernas y brazos no se cruzan con muebles de forma fea; **atravesar un objeto al caminar está bien, subirse encima no**.
7. **Textos en escena** (letreros, carteles): pegados al objeto (al frente de la mesa, en la pared), nunca flotando; letras grandes y legibles en 9:16. Si hay zoom, el texto puede quedar cortado porque ya se leyó antes.
8. **Objetos un poco mejor cada vez** (empanada con repulgo, lonchera con asa, mesa con mantel), siempre de bloques simples.

## Formato vertical 9:16 (aprendido en EP002)
- El cuadro es **angosto**: a 5 unidades con ángulo vertical de 55° solo caben ~2,9 de ancho. Dos personajes lado a lado casi nunca caben de frente: poner la cámara en **diagonal** para que queden escalonados en profundidad, o apilar en vertical (personaje abajo, burbuja/objeto arriba).
- Para revelar algo **detrás** de un personaje, no alinear cámara-personaje-objeto: la cabeza lo tapa. Dejar el objeto asomando por un lado (sobre el hombro) y mostrarlo completo en la toma siguiente.
- Interiores: la cámara cabe entre los muebles, pero cuidar lámparas del techo cuando la cámara mira hacia arriba (deslumbran; se pueden esconder solo en esa toma).
- Primer plano de un animal u objeto que "mira" al personaje: **punto de vista** del personaje (la cámara en sus ojos, el animal mira a la lente) y la cámara se aleja despacio = el personaje retrocede.

## Reglas del usuario (2026-11-07, EP004)
- **Por toma**: animación, render y sonido se trabajan por toma (una línea = una cámara); se rehace solo la toma que no gustó (`rehacer_tramo.py EP### --toma N`). Al final se juntan en un solo video editable antes de exportar.
- **Cámara de frente**: en cada toma se ve la cara, la expresión y la acción de quien se habla; la cámara no se queda en la espalda (solo un instante en transiciones). Si camina y la escena lo pide, seguimiento tipo dron bien encuadrado. Movimiento con sentido, nunca totalmente quieta.
- **Escala con espacio**: cabinas, bancas, mesas e interiores un poco más grandes que lo real: dos personajes caben con espacio y nada les tapa la cabeza.
- **Efectos con criterio**: el efecto que mejora cada toma (migas, brillitos, corazones, confeti, polvo…), corto y sin tapar la cara más de un instante (`Herramientas/blender/vfx.py`). Burbujas de pensamiento: imagen 2D ilustrada con el dibujo centrado.
- **Noche suave**: un poco luminosa para que no se vea tan oscura (salvo que la escena pida oscuro).
- **Textos para celular**: papelitos y letreros grandes y en negritas.
- **Comprobar**: foto de prueba de cada cambio (encuadre, centrado, que no tape) antes de seguir.

## Lo que el usuario revisa en cada borrador (EP006, 2026-11-09): cumplirlo ANTES de mandárselo
> El usuario pidió que estas reglas se apliquen solas en cada episodio, sin que tenga que señalarlas. Revisar el borrador con esta lista (fotos cada 0,5 s en los primeros 8 s y fotos de cada toma con su cámara real, `fotos_cuadros.py`).
1. **Gancho sin huecos (0–8 s)**: cada segundo tiene acción que ilustra lo que dice la voz, con 2–3 cortes por frase. Si alguien desaparece («¡puf!»), **nunca cortar a un lugar vacío**: mostrar cómo pasa (la fuente lo jala, vuela, cae al agua con chapoteo) y cerrar con un objeto que cuente el final («nunca vuelve» = solo queda flotando la moneda). En EP006 los segundos 3–6 eran piso vacío y el usuario lo marcó.
2. **Ninguna toma con más de ~1 s sin que pase algo**: ni piso vacío ni la cámara viendo la nada mientras habla la voz.
3. **Lo que se lanza se ve caer**: de espaldas → de frente cuando lo avienta → corte rápido al lugar donde cae (agua con chapoteo). El destino tiene que verse (en la fuente, entre la cascada y la orilla; detrás de la cascada no se ve).
4. **Nada tapa**: gente de la fiesta, postes, cascada, muebles. Revisar con la cámara real de cada toma.
5. **Caras**: nunca la de fábrica (la cara 15 parece de fábrica: usar 16 u 8). Los extras también reaccionan: nadie sonriendo al fondo cuando pasa algo malo.
6. **Luz de noche sin deslumbrar**: trajes claros, letreros y caras no se queman.
7. **Accesorios bien puestos** (banda, sombrero, bigote): medidos en ejes del rig (lecciones 86–87), foto de cerca en varias tomas, y el ala del sombrero no tapa la cara (cámara de frente o un poco abajo).
8. **Cada personaje con su identidad**: el presidente con sombrero de copa, bigote de una pieza y banda; los objetos de un personaje con SU modelo y colores (el peluche azul de la hermana, no uno genérico).
9. **Objetos chiquitos que importan** (monedas, llaves): grandes, brillando y de frente para que se lean a 540×960.
10. **Volumen** a −14 LUFS (`armar_video.py` lo ajusta en 2 pasadas).

## Recetas vistas en Custerk y Gelo (investigación nocturna, 2026-11-08)
> Vistas por fotogramas, con video y segundo (detalle en `Analizador/Estilos/Custerk_notas.md` y `Gelo_notas.md`). Son **propuestas** para nuestras historias hasta que el usuario opine; las marcadas [2+] se vieron en 2 o más videos.
- **[2+] Objeto importante junto a la cara, de frente a la cámara** al cerrar el momento (Custerk SiW3923d7zg 118,4 s; Gelo yfXNsN5BLck 79,5 s). En la prueba A además deja ver los ojos bajo la visera.
- **[2+] La mirada va primero**: los ojos (la textura de la cara) cambian antes que la cabeza y el cuerpo, y la dirección de la última mirada es la del siguiente movimiento o corte (Gelo 7WhnQwuNoE8 92,3 s: ojos → cabeza → corre hacia ese lado; Custerk 5lSYLwGZSYE 13,75 s: ojos de lado → corte a lo que ve; Custerk dHKb7RKyV0Q 0,83 → 1,03 s: la cara cambia ~6 cuadros antes de caer). Se aplicó en la prueba A y en la demostración H.
- **[2+] Reacción con cámara baja** (Custerk SiW3923d7zg 102,5 s; Gelo yfXNsN5BLck 78,8 s).
- **[2+] Primer segundo**: Custerk abre con una acción ya en marcha y corta a 1,0–1,33 s (5/5); Gelo abre con el pueblo en grupo de frente + letrero de la regla, ≥ 1 s (4/4).
- **[2+] Objeto clave en un inserto con acercamiento lento y brillitos alrededor** (Custerk PriU_tz_L30 77,0–79,0 s; SiW3923d7zg 117,9 s). Para "se pone rojo/a": mejillas rojas + vapor de la cabeza + mano a la cara, sostenido ~1,7 s (PriU_tz_L30 87,3–89,0 s).
- **Descubrir un objeto en 3 tomas de ~1 s**: la cara nota → el objeto en grande (sobre el hombro, asomando la visera) → reacción con cámara baja. Probado en la prueba A (`Analizador/Resultados/Investigacion_2026-11-08/A_actuacion/A_corte3.mp4`); **Los dos creadores revelan con la toma sobre el hombro** [2+] (Gelo 1MdGA9eFkQk 38,1 s y JRVnNzWjmUQ 31,3 s; Custerk baNZsKW7tIc 103,1 s, después de mostrar solo una parte a oscuras y prender la luz) y a veces entra con el personaje pasando pegado a la cámara (JRVnNzWjmUQ 30,9 s).
- **[2+] Golpe en la palabra + corte a la consecuencia en grande** (dron alto sobre el pueblo), y reacciones de grupo escalonadas (Gelo 1MdGA9eFkQk 31,5–33 s; 08xYJOKAYnI 105,6 s: en "tiré" se apaga todo y corte al dron). Impacto grande en 3 tiempos (Custerk TYDW2fNQYYU 42,5–47 s): temblor con brazos para equilibrarse → preparación en el cielo → "¡pum!" con líneas de impacto y el personaje que se agacha → resultado visto desde abajo sobre el hombro.
- **Empujar/abrir algo = el objeto sale del cuadro como cortina y revela lo de atrás** (Custerk En3xFS4y_mg 44,1 s); no hace falta ver el brazo.
- **[2+] La revelación fuerte se sostiene más** (~1,7–1,9 s, primerísimo plano con acercamiento lento) que el ritmo normal (Gelo 1MdGA9eFkQk 41,1–42,8 s; gy5P3dBqUOA 110,5–112,4 s).
