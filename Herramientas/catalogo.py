# CATALOGO de lo que YA EXISTE en el kit (para el plano de construccion de cada episodio: que se reusa y que hay que
# hacer). Lee el codigo y las carpetas; no abre Blender. Escribe docs/10_CATALOGO.md.
#   py -X utf8 Herramientas/catalogo.py
import ast, glob, json, os, re

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H = os.path.join(RAIZ, "Herramientas")


def funciones(ruta, saltar=()):
    arbol = ast.parse(open(ruta, encoding="utf-8").read())
    r = []
    for n in arbol.body:
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("_") and n.name not in saltar:
            doc = (ast.get_docstring(n) or "").strip().split("\n")[0]
            r.append((n.name, ", ".join(a.arg for a in n.args.args[:3]), doc))
    return r


def claves_dict(ruta, nombre):
    s = open(ruta, encoding="utf-8").read()
    m = re.search(r"^%s\s*=\s*\{" % nombre, s, re.M)
    if not m:
        return []
    i, prof = m.end() - 1, 0
    for j in range(i, len(s)):
        prof += s[j] == "{"; prof -= s[j] == "}"
        if prof == 0:
            break
    return re.findall(r'^\s{4}"([^"]+)"\s*:', s[i:j], re.M)


L = ["# 10 — Catálogo: lo que ya existe en el kit", "",
     "> Generado por `py -X utf8 Herramientas/catalogo.py` (volver a correrlo cuando se agregue algo). Se usa en el **plano de construcción** de cada episodio (`PLANO.md`): primero se marca qué se reusa de aquí y qué hay que hacer nuevo.", ""]
L += ["## Objetos de caricatura (`Herramientas/blender/objetos_cartoon.py`)", "", "| Función | Qué es |", "|---|---|"]
for n, a, d in funciones(os.path.join(H, "blender", "objetos_cartoon.py"), saltar=("lin", "mat", "excluir")):
    L.append("| `%s(%s)` | %s |" % (n, a, d[:140]))
L += ["", "## Muebles y decoración de cuartos (`Herramientas/blender/muebles_cartoon.py`)", "",
      "Telas con estampado en `Herramientas/blender/texturas/` (las genera `py -X utf8 Herramientas/texturas_tela.py`): estrellas rosa, estrellas y lunas azul, corazones coral, gatitas lila, papel tapiz de gatitas.", "",
      "| Función | Qué es |", "|---|---|"]
for n, a, d in funciones(os.path.join(H, "blender", "muebles_cartoon.py"), saltar=("emite", "pts_corazon", "pts_estrella", "pts_circulo", "pts_medio_aro", "prisma")):
    L.append("| `%s` | %s |" % (n, d))
L += ["", "## Efectos (`Herramientas/blender/vfx.py`)", "", "| Función | Qué hace |", "|---|---|"]
for n, a, d in funciones(os.path.join(H, "blender", "vfx.py")):
    L.append("| `%s(%s)` | %s |" % (n, a, d[:140]))
gestos = claves_dict(os.path.join(H, "blender", "actuar.py"), "GESTOS")
gestos_vida = claves_dict(os.path.join(H, "blender", "vida_suave.py"), "GESTOS")
L += ["", "## Gestos de actuación (`Herramientas/blender/actuar.py`, en su palabra)", "", ", ".join("`%s`" % g for g in gestos) or "(ver archivo)"]
L += ["", "## Vida suave (`Herramientas/blender/vida_suave.py`, SIEMPRE: nadie queda tieso; gestos en su palabra)", "", ", ".join("`%s`" % g for g in gestos_vida) or "(ver archivo)"]
L += ["", "## Tomas simples (`Herramientas/blender/tomas_simples.py`, receta `docs/09_RECETA_SIMPLE.md`)", "",
      "`retrato` (plano medio quieto) · `habla` (primer plano, solo la boca) · `hombro` (dos personajes en 9:16) · `inserto` (objeto) · `general` (a mano). Caminar o correr: `sb_blender.ciclo` sin rebote."]
cj = os.path.join(RAIZ, "Caras", "Emociones", "_secuencia", "caras.json")
if os.path.exists(cj):
    cs = json.load(open(cj, encoding="utf-8")).get("caras", [])
    L += ["", "## Caras por emoción (propiedad `cara` del rig; clásicas de Roblox)", "", " · ".join("%d %s" % (c["n"], c.get("emocion", "?")) for c in cs)]
L += ["", "## Personajes con rig", ""]
for nivel in ("Protagonista", "Secundarios", "Pueblo_NPC"):
    ps = []
    for d in sorted(glob.glob(os.path.join(RAIZ, "Personajes", nivel, "*"))):
        if os.path.isdir(d):
            rig = glob.glob(os.path.join(d, "*_R15_Rig.blend"))
            caras = os.path.exists(os.path.join(d, "caras"))
            ps.append("%s%s%s" % (os.path.basename(d), "" if rig else " (sin rig)", " +caras" if caras else ""))
    L.append("- **%s**: %s" % (nivel, ", ".join(ps) or "—"))
L += ["", "## Escenarios", ""]
for d in sorted(glob.glob(os.path.join(RAIZ, "Escenarios", "*"))):
    if os.path.isdir(d):
        L.append("- `%s` %s" % (os.path.basename(d), "(original, no se modifica)" if os.path.basename(d) == "Pueblo" else ""))
doc4 = os.path.join(RAIZ, "docs", "04_ESCENARIOS.md")
if os.path.exists(doc4):
    filas = [l for l in open(doc4, encoding="utf-8").read().split("\n") if l.startswith("| ") and not l.startswith("|---")]
    if filas:
        L += ["", "Lugares del Pueblo (de `docs/04_ESCENARIOS.md`):", ""] + filas[:40]
L += ["", "## Otras herramientas para el plano", "",
      "- Carteles y letreros pegados a objetos: `Herramientas/carteles.py` · contadores/relojes: carteles + `vfx`.",
      "- Caras por textura: `Herramientas/blender/caras_textura.py` · bocas para hablar (Sikelpa 21–25): `Herramientas/bocas_hablar.py`.",
      "- Alturas (niños más bajos que los adultos): `Herramientas/blender/alturas.py` → `alturas.escalar(rig, \"nino\")` (adulto 5,1 · niño 4,0 · niño chico 3,45).",
      "- Revisión: `revisar_encuadre.py`, `revisar_ojos.py`, `revisar_objetos.py`, `revisar_agarre.py`, `detectar_superficies.py`."]
os.makedirs(os.path.join(RAIZ, "docs"), exist_ok=True)
open(os.path.join(RAIZ, "docs", "10_CATALOGO.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("docs/10_CATALOGO.md: %d líneas" % len(L))
