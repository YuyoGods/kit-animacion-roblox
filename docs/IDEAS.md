# Mejoras pendientes del kit

> Aquí solo van mejoras del **sistema** (sirven para todos). Ideas de episodios y pendientes de un canal van en `MI_CANAL.md`.

## Próximas
- [x] **Storyboard animado con Three.js antes de Blender** (pedido del usuario, 2026-11-07): hecho en `Herramientas/storyboard/` (v1).
  - Pendiente:
    - grabar el storyboard como video para compartirlo;
    - hoja de contacto automática con `SB_foto`;
    - traer objetos de Blender (`EP###_objetos.blend`) como `.glb`;
    - ~~que `sb_blender.py` también ponga a los personajes en su lugar~~ (hecho el 2026-11-07, con objetos como figuras de lugar);
    - pasar a Blender también el día/noche y la luna de cada toma.
- [ ] **Fotogramas temporales** (pedido del usuario, 2026-11-07). Hoy los PNG se quedan para siempre (EP002: 4179 PNG = 2,1 GB, y `Respaldos/EP002_preview_v1` = 0,5 GB). Sirven para renderizar con varios Blender, corregir un tramo y armar el MP4, pero deberían borrarse solos (avisando) al aprobar el video. Opciones: vista previa en JPG (≈6× menos espacio) y un "video maestro" sin subtítulos para que `rehacer_tramo.py` reemplace solo su tramo sin guardar todos los PNG.
- [ ] Convertir el script de animación de EP001 en una **plantilla de animación** reutilizable (trayectorias, ciclos, cámaras, eventos).
- [ ] **Análisis de referencias** → receta de cámara automática a partir de la ficha de estilo (`docs/07_ANALISIS_REFERENCIAS.md`).
- [ ] Separar la parte fija de `armar_video.py` (mezcla, subtítulos, MP4) de la parte de cada episodio (frases, efectos) en un archivo de datos.

- [ ] Detector de partículas confiable (seguimiento de objetos chicos con flujo óptico, ignorando paralaje de dron); hoy da falsos positivos.

## Ideas
- Modo noche del pueblo (ventanas y faroles encendidos, cielo oscuro) como interruptor de un script.
- Biblioteca de poses (JSON) por personaje: saludar, señalar, sorprenderse, sentarse, tocar puerta, agacharse.
- Caras/expresiones intercambiables y sincronía de labios con la voz.
- Música de fondo opcional (libre de derechos).
- Brillo (glare) en el compositor para ojos que brillan, luna y faroles (hoy Eevee no da halo).
- Llevar a `Herramientas/` las piezas de `EP002/scripts/animar_bloque1.py` que sirven en cualquier episodio: cinemática directa sin depsgraph (`Pj`, `resolver_mano`), `paso()` (caminar con parámetros), `mirar()`, burbujas que miran a la cámara, panes/objetos con vuelo balístico.

- **Pueblo_v2: arreglar la fuente y la puerta de la presidencia en el mapa** (EP006): el agua de la pileta (`Fuente_Agua`) quedo debajo de la tapa de piedra (subirla 0,28 o quitar la tapa) y la entrada de la presidencia no tiene hoja de puerta. En EP006 se arreglo solo en el archivo del episodio (`scripts/utileria.py`). Hacerlo en una copia del mapa (`Escenarios/Pueblo_v3/`) para no tocar el original.
