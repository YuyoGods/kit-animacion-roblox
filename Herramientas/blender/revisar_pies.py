# ¿LOS PIES RESBALAN? Cuadro por cuadro mide cada pie: si esta apoyado (su punto mas bajo cerca del piso) y aun asi se
# desliza de lado, es "patinar" (defecto clasico al caminar o al cambiar el peso). Tambien avisa si se hunde en el piso.
# Uso dentro de Blender:
#   import revisar_pies as rp
#   rp.revisar("Sikelpa_Rig", f0, f1, piso=0.0)          # piso = altura del suelo en esa toma
# Umbrales (vista previa 540x960, personaje de ~5,5): apoyado si el pie esta a < 0.04 del piso; resbala si se mueve
# > 0.01 por cuadro estando apoyado; se hunde si baja > 0.03 del piso.
import bpy
from mathutils import Vector


def _pie_obj(rig, hueso):
    for o in rig.children_recursive if hasattr(rig, "children_recursive") else rig.children:
        if o.type == 'MESH' and o.parent_bone == hueso:
            return o
    return None


def revisar(rig_nombre, f0, f1, piso=0.0, apoyo=0.04, resbala=0.01, imprimir=True):
    """piso=None: el piso de cada pie es su punto mas bajo en el tramo (sirve en mapas con alturas distintas)."""
    sc = bpy.context.scene
    rig = bpy.data.objects[rig_nombre]
    pies = {h: _pie_obj(rig, h) for h in ("LeftFoot", "RightFoot")}
    prev, filas = {}, []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for h, o in pies.items():
            if o is None:
                continue
            oe = o.evaluated_get(dg)
            vs = [oe.matrix_world @ v.co for v in oe.data.vertices]
            zmin = min(v.z for v in vs)
            if zmin < -100:                                    # personaje "estacionado" fuera de la toma
                prev.pop(h, None)
                continue
            bajos = [v for v in vs if v.z < zmin + 0.03]
            c = sum(bajos, Vector()) / len(bajos)              # centro de la suela
            alt = zmin - (piso if piso is not None else 0.0)
            mov = (c.xy - prev[h].xy).length if h in prev else 0.0
            prev[h] = c
            filas.append((f, h, round(alt, 3), round(mov, 4), alt < apoyo and mov > resbala, alt < -0.03))
    if piso is None and filas:                             # recalcular "apoyado" con el piso de cada pie
        bajo = {h: min(r[2] for r in filas if r[1] == h) for h in pies}
        filas = [(f, h, round(alt - bajo[h], 3), mov, (alt - bajo[h]) < apoyo and mov > resbala, False)
                 for f, h, alt, mov, _, _ in filas]
    if imprimir:
        res = [r for r in filas if r[4]]
        hund = [r for r in filas if r[5]]
        print("revisar_pies %s f%d-%d: cuadros con pie apoyado que resbala %d, pie hundido %d, maximo resbalon %.3f/cuadro"
              % (rig_nombre, f0, f1, len(res), len(hund), max((r[3] for r in filas if r[2] < apoyo), default=0)))
        for r in (res + hund)[:10]:
            print("   f%d %s altura %.3f movimiento %.4f" % r[:4])
    return filas
