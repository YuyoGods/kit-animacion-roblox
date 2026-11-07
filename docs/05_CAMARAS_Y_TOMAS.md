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

## Formato vertical 9:16 (aprendido en EP002)
- El cuadro es **angosto**: a 5 unidades con ángulo vertical de 55° solo caben ~2,9 de ancho. Dos personajes lado a lado casi nunca caben de frente: poner la cámara en **diagonal** para que queden escalonados en profundidad, o apilar en vertical (personaje abajo, burbuja/objeto arriba).
- Para revelar algo **detrás** de un personaje, no alinear cámara-personaje-objeto: la cabeza lo tapa. Dejar el objeto asomando por un lado (sobre el hombro) y mostrarlo completo en la toma siguiente.
- Interiores: la cámara cabe entre los muebles, pero cuidar lámparas del techo cuando la cámara mira hacia arriba (deslumbran; se pueden esconder solo en esa toma).
- Primer plano de un animal u objeto que "mira" al personaje: **punto de vista** del personaje (la cámara en sus ojos, el animal mira a la lente) y la cámara se aleja despacio = el personaje retrocede.

