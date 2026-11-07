# Mejoras pendientes del kit

> Aquí solo van mejoras del **sistema** (sirven para todos). Ideas de episodios y pendientes de un canal van en `MI_CANAL.md`.

## Próximas
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

