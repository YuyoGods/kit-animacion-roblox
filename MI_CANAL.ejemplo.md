# MI CANAL — configuración personal (EJEMPLO)

> `instalar.py` copia este archivo como `MI_CANAL.md`. Llénalo con los datos de tu canal (o pídele a Claude que te pregunte y lo llene).
> `MI_CANAL.md` es solo tuyo: las actualizaciones del kit nunca lo tocan.

## Canal
- **Nombre del canal**: ...
- **Idioma de las historias**: español latinoamericano
- **Estilo**: historias animadas de Roblox, Shorts 9:16
- **Rol en el kit**: `usuario` (recibo actualizaciones con `git pull`)

## Protagonista (nivel A)
- **NOMBRE** → `01_Personajes/1_Protagonista/NOMBRE/`. Es quien más sale en cuadro.

## Reparto
Niveles: **A** protagonista · **B** secundario (sale cuando la historia lo pide) · **C** gente del pueblo (fondo).

| Personaje | Rol en las historias | Nivel | Carpeta | Estado |
|---|---|---|---|---|
| NOMBRE | Creador del canal / protagonista | A | `1_Protagonista/NOMBRE` | pendiente |
| ... | Mamá / hermana / abuela / amigo / presidente / maestra... | B | `2_Secundarios/...` | pendiente |
| Gente del pueblo | Vecinos, alumnos, tenderos | C | `3_Pueblo_NPC/` | pendiente |

### Detalle de personajes listos
| Personaje | Archivo | Altura | Notas |
|---|---|---|---|
| — | — | — | — |

## NPC con nombre
Cuando una historia le da nombre a alguien de `3_Pueblo_NPC/`, Claude propone un modelo con foto de frente; al confirmarlo se anota aquí y queda fijo para siempre. (Vacía hasta que haya uno confirmado.)

| Nombre | Quién es en las historias | Modelo (carpeta) y colores | Foto de frente | Primer episodio |
|---|---|---|---|---|
| — | — | — | — | — |

## Voz del narrador
- ElevenLabs: nombre de la voz (el id va en `mi_config.json`; la clave en la variable de entorno `ELEVENLABS_API_KEY`, nunca aquí).

## Mapa por defecto
- **Pueblo** (`02_Escenarios/Pueblo/`).

## Estado actual
- (Claude lo actualiza al terminar cada sesión.) Historial: `MI_BITACORA.md`.

## Pendientes del canal
- [ ] Subir mi protagonista a `01_Personajes/1_Protagonista/` y pedir su rig.

## Ideas de episodios
- ...
