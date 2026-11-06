# Escenarios (mapas)

Un mapa por carpeta:
```
Escenarios/
├── Pueblo/          ← ORIGINAL del kit: no se modifica (se actualiza con el kit)
├── Pueblo_v2/       ← tu copia del pueblo con cambios
├── Pueblo_Noche/    ← otra versión
└── Medieval/        ← un mapa nuevo (murallas, castillo…)
```

- ¿Quieres cambiar el pueblo? Pídele a Claude: **"Haz una copia del Pueblo como Pueblo_v2 y agrégale…"**. El original siempre queda como respaldo.
- ¿Mapa nuevo? **"Hazme un mapa medieval con murallas enormes"** → Claude crea `Escenarios/Medieval/` con su `.blend` y los scripts que lo construyen.
- Los personajes no viven en los mapas: en cada episodio Claude abre el mapa elegido y agrega solo los personajes que salen (ya con su rig). Así Blender no se satura y cambiar de mapa es rápido.
- Tus mapas son tuyos: git no los sube ni los toca al actualizar (solo `Pueblo/`).

Mapa, coordenadas y alturas del Pueblo: `docs/04_ESCENARIOS.md`.
