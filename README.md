# Kit de Animación Roblox 🎬

Sistema para hacer **Shorts animados estilo Roblox (9:16)** en Blender **con Claude**: tú diriges la historia y los personajes; Claude arma el escenario, el rig de tus personajes, la animación, las cámaras, la voz, los subtítulos y el render.

Incluye un mapa listo (**el Pueblo**: calle con casas, plaza con fuente, presidencia, tiendas, escuela, estanque y colinas), herramientas, plantillas y todas las lecciones aprendidas para que Claude no repita errores.

## Qué necesitas
| | Para qué |
|---|---|
| Windows 10/11 | El kit está probado ahí |
| [Claude](https://claude.com/download) (app de escritorio, pestaña **Code**) | Es quien hace el trabajo |
| [Blender 5.2](https://www.blender.org/download/) | Animación y render |
| Addon **BlenderMCP** ([github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)) | Para que Claude controle tu Blender abierto |
| [Python 3.11+](https://www.python.org/downloads/) | Herramientas del kit |
| FFmpeg (`winget install Gyan.FFmpeg`) | Armar el video con audio y subtítulos |
| [Git](https://git-scm.com/download/win) | Descargar y actualizar el kit |
| *Opcional*: cuenta de [ElevenLabs](https://elevenlabs.io) | Voz del narrador |
| *Recomendado*: tarjeta NVIDIA (RTX) | Que el Analizador de videos sea rápido (sin ella funciona, pero lento) |
| *Opcional*: Roblox Studio | Exportar tus personajes |

## Instalación fácil (Claude lo hace por ti)
1. Instala la app de [Claude](https://claude.com/download), inicia sesión y abre la pestaña **Code**.
2. Elige como carpeta el **lugar** donde quieres guardar el kit (por ejemplo, Documentos).
3. Copia este prompt, cambia lo que está entre corchetes y pégalo. Acepta los permisos que te pida.

```text
Quiero instalar el Kit de Animación Roblox en esta PC.

Datos:
- Lugar donde lo quiero: [EJEMPLO: C:\Users\TuNombre\Documents]
- Nombre de la carpeta: [EJEMPLO: YOUTUBE ANIMACION]

Haz esto en orden:
1. Revisa si tengo Git, Python 3.11 o más nuevo y FFmpeg. Si falta algo, pídeme permiso y lo instalas con winget.
2. Clona https://github.com/YuyoGods/kit-animacion-roblox.git en el lugar y con el nombre que te di.
3. Lee el README.md, el CLAUDE.md y la skill .claude/skills/instalar-kit/SKILL.md del kit y sigue sus pasos: instala los paquetes, revisa con "py instalar.py", ayúdame con Blender 5.2 y el addon BlenderMCP. Pídeme permiso antes de cada descarga.
4. Guarda en tu memoria: "Mi kit de animación Roblox está en [lugar]\[nombre]. Antes de cualquier trabajo de animación lee su CLAUDE.md y MI_CANAL.md. Para actualizarlo uso la skill actualizar-kit (git pull sin forzar nada)."
5. Ayúdame a llenar MI_CANAL.md: pregúntame el nombre de mi canal, mi personaje principal y mis personajes secundarios. Mi rol en el kit es "usuario".
6. Al final dime qué quedó listo, qué falta y cómo abrir una sesión nueva dentro de la carpeta del kit (ahí se cargan sus reglas y skills).

Reglas: respóndeme en español y breve, nunca me pidas claves ni contraseñas en el chat y no borres nada sin preguntarme.
```

4. Al terminar, abre una **sesión nueva eligiendo la carpeta del kit**: así Claude carga sus reglas y skills.

## Instalación a mano
1. Descarga el kit (en la carpeta donde lo quieras tener):
   ```
   git clone https://github.com/YuyoGods/kit-animacion-roblox.git "YOUTUBE ANIMACION"
   ```
2. Entra a la carpeta y corre el instalador (revisa todo, instala lo que falta y crea tus archivos personales; nunca borra nada):
   ```
   cd "YOUTUBE ANIMACION"
   py instalar.py --paquetes
   ```
3. **BlenderMCP**: descarga `addon.py` del proyecto blender-mcp → Blender → *Edit → Preferences → Add-ons → Install from Disk* → actívalo. Luego, en la vista 3D presiona **N** → pestaña **BlenderMCP** → **Connect**.
4. Abre Claude → pestaña **Code** → elige la carpeta del kit. Dile:
   > Lee CLAUDE.md y ayúdame a llenar MI_CANAL.md

## Dónde va cada cosa
| Carpeta | Qué pones tú |
|---|---|
| `Personajes/Protagonista/` | Tu personaje principal (exportado de Roblox Studio) |
| `Personajes/Secundarios/` | Familia, amigos, personajes importantes |
| `Personajes/Pueblo_NPC/` | Gente genérica del pueblo |
| `Personajes/Plantillas_Rigs/` | Los Roblox Starter Rigs (te los pasa el dueño del kit) |
| `Caras/` | Caras PNG por emoción: `feliz.png`, `enojado.png`, `asombro.png`… |
| `Analizador/Videos_para_analizar/<Creador>/` | Videos de otros creadores para sacar su fórmula (ver `Analizador/LEEME.md`) |
| `Escenarios/` | Los mapas, uno por carpeta: `Pueblo/` es el original; tus copias (`Pueblo_v2/`) y mapas nuevos (`Medieval/`) van al lado |
| `Episodios/` | Tus videos terminados y en proceso (Claude los crea desde la plantilla) |
| `Respaldos/` | Versiones viejas que no se borran |

Cada carpeta trae un `LEEME.md` que explica qué va ahí. Las carpetas `docs/` y `Herramientas/` son para Claude; no necesitas abrirlas.

## Cómo se usa (ejemplos de lo que le pides a Claude)
- *"Ya subí a mi personaje a Protagonista, ponle su rig."*
- *"Esta es mi hermana, ponle rig y agrégala como secundaria."*
- *"Quiero un Short de 30 s: mi protagonista llega tarde a la escuela…"* → guion → animación → revisión de cámaras → vista previa → voz y subtítulos → render final.
- *"Analiza los videos nuevos"* (después de subir videos a `Analizador/Videos_para_analizar/<Creador>/`) y luego *"hazlo al estilo de <Creador>"*.
- *"Del segundo 10 al 15 no me gustó, cámbiale…"* → Claude rehace solo ese tramo.

El kit trae **skills** (`.claude/skills/`) que Claude usa solo cuando abres la carpeta del kit: instalar/revisar, poner rig, analizar videos, nuevo episodio, rehacer un tramo y actualizar el kit.

Claude te enseña fotos de avance antes de renderizar y te pide permiso antes de gastar créditos de ElevenLabs o hacer renders largos.

## Clave de ElevenLabs (opcional)
**Nunca la pegues en el chat.** Ponla como variable de entorno (PowerShell), cambiando `TU_CLAVE`:
```
[Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", "TU_CLAVE", "User")
```
Cierra y vuelve a abrir Claude. El id de la voz va en `mi_config.json` → `"voz_narrador"`.

## Actualizar el kit
```
git pull
```
Tus cosas **nunca se borran ni se sobrescriben**: personajes, caras, episodios, referencias, mapas propios, `MI_CANAL.md`, `MI_BITACORA.md` y `mi_config.json` están fuera del repositorio (`.gitignore`).
Si git dice que tienes cambios en archivos del kit, **no fuerces nada**: pídele a Claude que lo revise (los respalda en `Respaldos/` antes de actualizar).
Novedades de cada versión: `docs/CAMBIOS.md`.

## Licencias y créditos
- No se incluyen (ni se deben subir): Roblox Starter Rigs, caras de Roblox, ni avatares de otras personas; cada quien usa los suyos según sus licencias.
- Los efectos de sonido no vienen incluidos; se recomiendan librerías CC0 (por ejemplo, Kenney).
- Uso del kit: compartido con amigos por el dueño del repositorio (licencia por definir).
