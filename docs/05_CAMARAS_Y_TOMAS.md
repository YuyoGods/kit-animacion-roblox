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
- Cortes cada 2–4 s; el final puede sostenerse más (suspenso).
- Temblor: suma de senos con frecuencias no múltiplos (función `shake`). Poco en tomas tranquilas (0,01–0,03), más al correr (0,07–0,08).
- Zoom in/out animando el ángulo de la lente (`angle_y`), no solo moviendo la cámara.

## Revisión obligatoria
1. `04_Herramientas/blender/revisar_camaras.py` (ejecutar en el Blender del episodio):
   - Rayos de la cámara a cabeza y pecho → reporta objetos que tapan.
   - Rejilla de rayos → reporta objetos cercanos que ocupan > 22 % del cuadro (el piso no cuenta).
   - Reporta cuándo la cabeza/pecho salen de cuadro.
   - `EXCEPT`: rangos de fotogramas tapados a propósito (transiciones).
2. Hoja de contacto: fotos de inicio/mitad/fin de cada toma a 22 % → revisar a ojo.
3. Solo con **0 obstrucciones** se renderiza.
