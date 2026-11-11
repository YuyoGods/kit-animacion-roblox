"""REVISAR (Y ARREGLAR) LA PIEL de un personaje con rig: que la cabeza no salga bronceada junto a manos y piernas claras.

Uso (desde la raiz del kit):
  blender -b "Personajes/<Nivel>/<Nombre>/<Nombre>_R15_Rig.blend" --python Herramientas/blender/revisar_piel.py
  blender -b "...R15_Rig.blend" --python Herramientas/blender/revisar_piel.py -- --arreglar      (arregla y guarda)

Que revisa (leccion 88, EP007):
  1. Materiales del cuerpo cuyo color de pieza (nodo Mix, A) quedo pasado DOS VECES a lineal: el Kd del .mtl de Roblox
     ya viene en lineal y armar_rig_r15_auto lo volvia a convertir (corregido el 2026-11-09). Con --arreglar se
     regresa al Kd tal cual.
  2. Que la piel de la cabeza (si es tipo calcomania) y la de las manos coincidan. Si despues del arreglo siguen
     distintas, imprime REVISAR: entonces el personaje trae tonos distintos de fabrica (usar
     objetos_cartoon.igualar_piel en el episodio o preguntar al usuario).
Imprime una linea "PIEL ..." por personaje. Guardar un respaldo antes de usar --arreglar en varios personajes.
"""
import bpy, os, glob, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import objetos_cartoon as oc

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ARREGLAR = "--arreglar" in ARGS


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _srgb(c):
    c = max(0.0, c)
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _hex(c):
    return "#" + "".join(f"{max(0, min(255, round(x * 255))):02x}" for x in c)


D = os.path.dirname(bpy.data.filepath)
KD = {}
for f in glob.glob(os.path.join(D, "*.mtl")) + glob.glob(os.path.join(D, "*", "*.mtl")):
    actual = None
    for linea in open(f, encoding="utf-8", errors="ignore"):
        p = linea.split()
        if p and p[0] == "newmtl":
            actual = " ".join(p[1:])
        elif p and p[0] == "Kd" and actual:
            KD[actual] = tuple(float(x) for x in p[1:4])

rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig is None:
    print("PIEL (sin rig en", bpy.data.filepath, ")")
else:
    mats = {m for o in rig.children_recursive if o.type == 'MESH' for m in o.data.materials if m and m.use_nodes}
    dobles = 0
    for m in sorted(mats, key=lambda m: m.name):
        kd = KD.get(m.name) or KD.get(m.name.rsplit(".", 1)[0])
        if not kd:
            continue
        for n in m.node_tree.nodes:
            if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[6].is_linked and n.inputs[0].is_linked:
                A = n.inputs[6].default_value[:3]
                if all(abs(a - _lin(k)) < 0.01 for a, k in zip(A, kd)) and any(abs(a - k) > 0.01 for a, k in zip(A, kd)):
                    dobles += 1
                    if ARREGLAR:
                        n.inputs[6].default_value = (*kd, 1.0)
    # piel de la cabeza (fondo de la calcomania) contra la de las manos
    cab = oc._pieza_cuerpo(rig, "Head")
    A = None
    for m in (cab.data.materials if cab else []):
        if not (m and m.use_nodes):
            continue
        for n in m.node_tree.nodes:
            # fondo de la cara (color de la pieza). Nota: leer los pixeles de la cara para saber "lo que se ve" NO sirve:
            # en la vecina el alfa leido (0,89) no coincide con lo que se ve en el render (domina el fondo). Comparar el
            # fondo con las manos y confirmar con una foto.
            if n.type == 'MIX' and n.data_type == 'RGBA' and not n.inputs[6].is_linked and n.inputs[0].is_linked:
                A = tuple(_srgb(x) for x in n.inputs[6].default_value[:3])
    mano = oc._piel_de_manos(rig)
    if A and mano:
        dif = max(abs(a - b) for a, b in zip(A, mano))
        estado = "OK" if dif <= 0.06 else ("SE ARREGLA con --arreglar" if dobles and not ARREGLAR else "REVISAR (tonos distintos de fabrica)")
        print(f"PIEL {rig.name:28s} doble_lineal={dobles:2d} cabeza={_hex(A)} manos={_hex(mano)} diferencia={dif:.2f} {estado}")
    else:
        print(f"PIEL {rig.name:28s} doble_lineal={dobles:2d} cabeza calcomania={'si' if A else 'no'} (no se compara)")
    if ARREGLAR and dobles:
        bpy.ops.wm.save_mainfile()
        print("PIEL guardado:", bpy.data.filepath)
