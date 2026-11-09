# 09 — Receta "simple pero no floja" (estilo Custerk y Gelo, medido)

> Pedido del usuario (2026-11-08): animar como Custerk y Gelo. Que no tarde mucho, pero que tampoco quede flojo: que la gente entienda. Medido con el motor del Analizador en 33 videos; se actualiza al terminar los ~170 (`Analizador/Resultados/Entrenamiento_2026-11-08/simpleza.md`). Notas con video y segundo: `Analizador/Estilos/Custerk_notas.md` y `Gelo_notas.md` (secciones "Animación simple").

## La idea en una frase
**La voz cuenta y la imagen ilustra.** La energía sale de **cortar seguido** (una toma de 1,2–1,4 s, 40–46 cortes por minuto) y de **la cara correcta**, no de mover a los personajes. En Custerk, la mitad de las tomas tienen la cámara fija y el personaje casi quieto.

| | Custerk | Gelo | Nosotros (EP001) |
|---|---|---|---|
| Cámara fija | 51 % | 74 % | 9 % |
| Acercamiento lento | 38 % | 13 % | 45 % |
| Movimiento en cuadro (mediana) | 1,2 % | 2,0 % | 11,9 % |
| Tomas casi quietas | 44 % | 26 % | 0 % |
| Toma mediana | 1,4 s | 1,2 s | 2,5 s |
| Cortes por minuto | 40 | 46 | 20 |

## Los 5 tipos de toma (casi todo el video es uno de estos)
1. **Retrato** (la toma más común): un personaje en plano medio o primer plano, **una pose y una cara sostenidas**, con la cámara fija o con un acercamiento lento (3–8 % en la toma), durante 1–2 s. La voz dice la frase y la imagen la ilustra.
   - Actuación: la cara cambia **en la palabra clave**. Solo un gesto sostenido si la frase lo pide (mano en la cabeza, señalar, brazos arriba, mano en la puerta).
2. **Habla** (diálogo entre comillas): primer plano fijo; **solo cambia la boca** (2–3 bocas), el cuerpo queda quieto en su pose y el que escucha no se mueve.
3. **Traslado**: camina, corre, cae, baja o lo arrastran. **Caminar o correr = el ciclo básico de Roblox** (Custerk y Gelo): brazos y piernas que se balancean en contra (~±30°), sin rebote ni torso que gira y con la cara fija. En el kit: `sb_blender.ciclo("caminar" | "correr", ...)` con `rebote`, `torsion` y `cadera` en 0. La cámara va fija de lado, o de frente retrocediendo con él. El personaje entero se desplaza con un ciclo simple o con la pose fija, y la cámara queda fija o lo sigue. Aun así, lo que se mueve en pantalla no pasa de 10–26 %.
4. **Objeto, letrero o contador**: el objeto clave en un inserto con brillitos, o la regla escrita en pantalla (reloj 0:40, "100" sobre la cabeza, escalones 1→12, "UN DÍA = UNA MONEDA"). Así la regla se ve sin animar nada más.
5. **El pueblo** (sobre todo Gelo): plano general con mucha gente quieta o caminando, para "en este pueblo, todos…".

## Cámara
- **Fija** en la mitad o más de las tomas; si no, **acercamiento lento**. Golpe de zoom solo en 1–2 % de las tomas, en la palabra fuerte. Temblor solo en un impacto.
- Nada de cámara que da vueltas ni de dron en cada toma. El dron es para el pueblo o para un traslado largo.

## Ritmo
- **Una frase, una toma** (una frase larga puede llevar 2 cortes). Toma de 1–2 s; las de 3–5 s solo para la revelación final, la pregunta de cierre o un texto en pantalla.
- La voz va a velocidad normal (preferencia del usuario). El ritmo sale de **frases cortas sin pausas largas** y de los cortes.

## Qué NO animar (ahorra horas)
- Las acciones que la voz ya cuenta ("abrió su mochila", "tocó la puerta"): **pose sostenida + cara**, o el resultado (la puerta abierta), no el ciclo completo.
- Actuación de cuerpo complicada, gestos en cada palabra, cámaras que se mueven todo el tiempo.

## Qué SÍ cuidar (para que no quede flojo)
- **La cara correcta en cada toma**: es lo que más se ve en celular.
- **El objeto clave se ve y se distingue** (`revisar_objetos.py`), de frente a la cámara y con un color que contraste.
- **Contadores y letreros** para las reglas y los números de la historia.
- **Efectos baratos en los golpes**: brillitos, líneas de impacto, partículas (billetes, confeti, migas), en la palabra.
- Subtítulos de 1–2 palabras con la palabra clave en color.
- Cabeza y gorro completos, nada que tape al que habla (revisión obligatoria de siempre).

## Qué se relaciona con MÁS VISTAS (pistas, no leyes)
Vistas por día de 52 videos de Custerk y 22 de Gelo contra las medidas del motor (`Analizador/Resultados/Entrenamiento_2026-11-08/vistas.md`). Todas las relaciones son flojas (|r| < 0,4) y el tema pesa más, pero apuntan para el mismo lado:
- **Cortar en los primeros 3 s**: +0,24 en Custerk y +0,34 en Gelo. Es la única que sale en los dos: el gancho con 2–3 cortes rápidos.
- Custerk: más tomas **con 2 personajes** (+0,28), **cámara fija** (+0,23) y **primeros planos** (+0,20). Más efectos no da más vistas (−0,10).
- Gelo: videos **más cortos** (−0,39 por duración), narración más rápida (+0,32) y más cortes por minuto (+0,26).
- Ninguna relación dice que mover más a los personajes dé más vistas.

## Herramienta: `Herramientas/blender/tomas_simples.py`
- Se le da la lista de tomas `(desde, quién, tipo, caras)` y arma cámaras, cortes, poses quietas, caras y bocas. Probada en EP004 T13–16: 12 tomas en ~24 s de script (`Analizador/Resultados/Entrenamiento_2026-11-08/prueba_simple/`).
- **Que nada tape la cara**: prueba ángulos (0, ±20, ±40, ±60°) con rayos hacia la cara y se queda con el que la ve completa. Sin eso, 3 de 12 tomas quedaban tapadas.
- **Dos personajes en 9:16 = sobre el hombro** (`hombro`): de lado no caben. La cámara va 3,2 m atrás y 1,7 m al lado del que da la espalda.
- **Diálogos**: `{"SK": "bocas"}` + `bocas={"SK": "voz"}` (bocas 21–25 según el volumen de la voz) o `[abierta, cerrada]` para personajes sin bocas (la crush: `[3, 2]`).

## Pendiente (prueba B5 del entrenamiento)
- Render de la prueba, medirla con el motor contra Custerk y mostrarla al usuario.
- Si el otro personaje tapa al que habla, pasar solo a "hombro" (hoy se queda con un 3/4 de 60°).

## Simple NO es congelado (lección de EP005, 2026-11-09)
- **Qué pasó**: EP005 se animó con poses 100 % fijas por toma, y el usuario lo vio «muy tieso, muy cutre». Dijo que así la historia no se entiende.
- **Lo medido**: Custerk y Gelo no congelan. Solo el 45 % y el 31 % de sus tomas están casi quietas; en el resto respiran, mueven un poco la cabeza o hacen un gesto chico.
- **Receta**: pose fija por toma **+ vida suave**:
  - Respiración y vaivén del cuerpo.
  - La cabeza mira y se mueve sola.
  - Brazos que se mecen si no sostienen nada.
  - **Un gesto en la palabra clave** (asentir, negar, mano al pecho, risa, susto, encogerse, saludar, manos a la cabeza, oler…).
  - **Asentir suave al hablar**.
- **Límites**: lento (2 Hz como máximo) y de pocos grados (memoria «movimientos suaves»).
- **Herramienta del kit**: `Herramientas/blender/vida_suave.py`. Se suma encima de cualquier pose (storyboard, `tomas_simples` o poses del episodio) y **`tomas_simples.armar(..., vida=True)` la pone por defecto**. Los gestos van en su palabra: `gestos={clave: [(fotograma, "mano_pecho", None)]}` y `vida_suave.gesto_en_palabra(tomas_voz, toma, "gusta")`. Ejemplo completo con 44 gestos: `Episodios/EP005_No_Te_Sientes_En_Su_Lugar/scripts/animar_ep005.py` (tabla `GESTOS`).
- **Qué gesto para qué palabra** (guía rápida):
  - sí, entendí, listo → `asentir`
  - nadie, no → `negar`
  - me gusta, por fin → `mano_pecho`
  - se ríe → `risa`
  - era yo, ¡era ella! → `susto`
  - vergüenza, no sé → `encoge`
  - saludaba → `agitar`
  - corazón roto → `triste`
  - miré, otro cuarto → `mirar`
  - ¡pelo rojo! → `manos_cabeza`
  - olía a… → `oler`
  - comía → `comer`
  - el más popular → `orgullo`
  - uno, dos, tres → `contar`
  - un diálogo → `habla`

## Lo que va con MÁS VISTAS (todos los videos: Custerk 59 y Gelo 70 con vistas; Spearman, 2026-11-09)
- **Cortar en los primeros 3 s**: r +0,36 en Custerk y +0,39 en Gelo. Es lo más fuerte en los dos.
- **En Gelo, más vida = más vistas**:
  - más cortes por minuto (+0,37);
  - tomas más cortas (−0,31);
  - **más movimiento en cuadro (+0,30)**;
  - menos cámara fija (−0,28).
- **En Custerk**: más primeros planos (+0,25), más planos de 2+ personajes (+0,22) y un poco más de movimiento (+0,17).
- **Conclusión**: la receta simple funciona con **cortes rápidos + vida suave**. Ni congelado ni sacudido. Datos en `Analizador/Resultados/Entrenamiento_2026-11-08/vistas.md`.
