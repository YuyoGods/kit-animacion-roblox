# Personajes — aquí van los tuyos

Las carpetas vienen **vacías**: cada quien pone sus personajes exportados de Roblox Studio y le pide a Claude que les ponga su rig (huesos para animarlos).

| Carpeta | Qué va aquí | En cámara |
|---|---|---|
| `Protagonista/` | **Tu personaje principal** (el creador del canal). Solo uno. | Nivel **A**: el que más sale, primeros planos, abre y cierra la historia |
| `Secundarios/` | Personajes importantes de tus historias: mamá, abuela, hermana, primo, amigos, el presidente, la maestra… | Nivel **B**: salen cuando la historia lo pide |
| `Pueblo_NPC/` | Gente genérica de fondo (vecinos, alumnos, tenderos), ropa sencilla | Nivel **C**: llenan escenas, casi nunca en primer plano |
| `Plantillas_Rigs/` | Roblox Starter Rigs (te los pasa el dueño del kit) | — |

Las caras (feliz, enojado, asombro…) van en `Caras/`.

## Cómo subir un personaje
1. En **Roblox Studio**: selecciona tu personaje → clic derecho → **Export Selection…** → guarda el `.obj` (salen también `.mtl` y las texturas `.png`).
2. Crea una carpeta con su nombre dentro del nivel que le toca, y pon ahí todo lo exportado:
   ```
   Protagonista/
   └── Sikelpa/
       ├── Personaje.obj   (+ .mtl y .png)
       └── Accesorios/     ← solo si exportaste los accesorios aparte
   ```
3. Pídele a Claude: **"Ya subí a Sikelpa, ponle su rig"**.

## Qué hace Claude (receta en `docs/03_PERSONAJES.md`)
- Reconoce las 15 piezas R15 y los accesorios, arma el rig y guarda **`<Nombre>_R15_Rig.blend`** en la misma carpeta, con fotos de prueba en `previews/`.
- No borra lo que subiste. Si ya había un rig anterior, lo mueve a `Respaldos/`.
- Anota al personaje en el reparto de `MI_CANAL.md`.

Todos usan **el mismo esqueleto R15 y los mismos nombres de huesos**, así una animación hecha para uno sirve para los demás.
