---
name: actualizar-kit
description: Actualiza el Kit de Animación Roblox a la última versión del repositorio sin tocar nada del usuario (personajes, mapas, episodios, caras, MI_CANAL). Usar cuando diga "actualiza el kit", "baja la nueva versión", "hay actualización".
---

# Actualizar el kit (rol `usuario`)

Lo personal (personajes, caras, mapas propios, episodios, videos, `MI_*.md`, `mi_config.json`) está fuera del repositorio: `git pull` no lo toca.

1. `git status --short`. Si hay archivos **del kit** modificados (líneas ` M`): copiarlos a `Respaldos/respaldo_<fecha>/` (misma ruta), explicarle al usuario cuáles son y preguntar antes de seguir. Si dice que sí: `git restore <archivos>` (solo esos) y continuar.
2. `git pull`. **Nunca** `git reset --hard`, `git checkout -- .`, `git clean` ni `--force`.
3. Leer `docs/CAMBIOS.md` y contarle al usuario lo nuevo en 3–5 líneas (y si algo cambió de lugar, moverlo con su permiso). Decirle que la guía completa de cada versión (qué es cada cosa nueva, para qué sirve y cómo se usa) está en `docs/CAMBIOS.md`, y hacer con él lo de «Qué hacer después de actualizar» de esa versión (lo opcional, solo si él quiere). Si pregunta por algo, explicárselo con esa guía.
4. `py instalar.py` (y `py instalar.py --paquetes` si marca paquetes nuevos, con permiso).
5. Si el usuario tenía cambios propios en un archivo del kit, ofrecer pasarlos a un archivo personal (`MI_LECCIONES.md`, su copia de mapa, etc.).

(Rol `mantenedor`: no usar esta skill para subir; las reglas de subida están en `CLAUDE.md` sección 8.)
