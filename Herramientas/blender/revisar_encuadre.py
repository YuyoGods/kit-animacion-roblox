# ¿LA CARA ESTA BIEN ENCUADRADA? (checklist "Calidad de cada toma", punto 2, docs/05): por cuadro proyecta la cabeza
# con todo lo que lleva encima (gorro, cabello: piezas pegadas al hueso Head) y avisa si:
#   - se corta (sale del cuadro) y cuanto,
#   - el centro de la cara no cae en la franja de arriba (tercio superior: 55-80 % de la altura desde abajo) en planos
#     medios/primeros planos,
#   - la cara es diminuta (< 4 % del alto) -> plano general, no se revisa el tercio.
# Uso dentro de Blender:
#   import revisar_encuadre as re_; re_.revisar("Sikelpa_Rig", f0, f1, camara=None)
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def _piezas_cabeza(rig):
    hijos = rig.children_recursive if hasattr(rig, "children_recursive") else rig.children
    return [o for o in hijos if o.type == 'MESH' and o.parent_bone == "Head" and not o.hide_render]


def revisar(rig_nombre, f0, f1, camara=None, imprimir=True):
    sc = bpy.context.scene
    rig = bpy.data.objects[rig_nombre]
    piezas = _piezas_cabeza(rig)
    malos, filas = [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        cam = camara or sc.camera
        dg = bpy.context.evaluated_depsgraph_get()
        us, vs = [], []
        for o in piezas:
            oe = o.evaluated_get(dg)
            mw = oe.matrix_world
            vs_ = oe.data.vertices
            for i in range(0, len(vs_), 3):                     # vertices reales (la caja envolvente exagera)
                v = vs_[i]
                p = world_to_camera_view(sc, cam, mw @ v.co)
                if p.z > 0:
                    us.append(p.x); vs.append(p.y)
        if not us:
            filas.append((f, "fuera")); malos.append((f, "fuera de cuadro"))
            continue
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        alto = v1 - v0
        corte = max(0, -u0) + max(0, u1 - 1) + max(0, -v0) + max(0, v1 - 1)
        centro = (v0 + v1) / 2
        prob = []
        if corte > 0.01:
            prob.append("cortada %.0f%%" % (100 * corte / max(alto, 1e-6)))
        if alto >= 0.04 and alto < 0.45 and not (0.55 <= centro <= 0.80):
            prob.append("centro de la cara a %.0f%% de altura (ideal 55-80%%)" % (100 * centro))
        filas.append((f, round(alto, 3), round(centro, 3), round(corte, 3)))
        if prob:
            malos.append((f, ", ".join(prob)))
    if imprimir:
        cortes = [r[3] / max(r[1], 1e-6) for r in filas if len(r) == 4]
        n_corte = sum(1 for c in cortes if c > 0.10)
        print("revisar_encuadre %s f%d-%d: cuadros con problema %d de %d (cabeza/gorro cortado >10%%: %d, maximo %.0f%%)"
              % (rig_nombre, f0, f1, len(malos), f1 - f0 + 1, n_corte, 100 * max(cortes or [0])))
        vistos = set()
        for f, p in malos:
            k = p.split(" ")[0]
            if k not in vistos:
                print("   f%d %s" % (f, p)); vistos.add(k)
    return malos
