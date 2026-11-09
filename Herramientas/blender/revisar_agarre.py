# ¿LO AGARRA DE VERDAD? Revisa cuadro por cuadro un objeto en la mano: hueco entre objeto y mano (flota),
# cuanto se mete dentro de la mano (atraviesa) y si se resbala (se mueve respecto a la mano entre cuadros).
# Uso dentro de Blender:
#   import revisar_agarre as ra
#   ra.revisar("Moneda", "Sikelpa_RightHand", 1, 90)      # objeto, malla de la mano, rango
# Umbrales para la vista previa (540x960): hueco > 0.03 o se mete > 0.05 o resbala > 0.01 por cuadro = revisar.
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _mundo(o, dg):
    oe = o.evaluated_get(dg)
    me = oe.to_mesh()
    vs = [oe.matrix_world @ v.co for v in me.vertices]
    ps = [list(p.vertices) for p in me.polygons]
    oe.to_mesh_clear()
    return vs, ps


def revisar(objeto, mano, f0, f1, hueso_mano=None, imprimir=True):
    sc = bpy.context.scene
    ob, mn = bpy.data.objects[objeto], bpy.data.objects[mano]
    rig = mn.parent if mn.parent and mn.parent.type == 'ARMATURE' else None
    hueso = hueso_mano or mn.parent_bone
    filas, rel0, prev = [], None, None
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        vm, pm = _mundo(mn, dg)
        arbol = BVHTree.FromPolygons(vm, pm)
        vo, _ = _mundo(ob, dg)
        hueco, mete = 1e9, 0.0
        for v in vo:
            co, nor, i, d = arbol.find_nearest(v)
            if co is None:
                continue
            dentro = (v - co).dot(nor) < 0
            if dentro:
                mete = max(mete, d)
                hueco = min(hueco, 0.0)
            else:
                hueco = min(hueco, d)
        # posicion del objeto vista desde la mano (si cambia, se resbala)
        if rig is not None and hueso:
            Mm = rig.matrix_world @ rig.pose.bones[hueso].matrix
        else:
            Mm = mn.matrix_world
        rel = Mm.inverted() @ ob.matrix_world.translation
        resb = (rel - prev).length if prev is not None else 0.0
        prev = rel
        filas.append((f, hueco, mete, resb))
    if imprimir:
        mal = [r for r in filas if r[1] > 0.03 or r[2] > 0.05 or r[3] > 0.01]
        print("revisar_agarre %s en %s f%d-%d: hueco max %.3f, se mete max %.3f, resbala max %.3f/cuadro, cuadros a revisar %d"
              % (objeto, mano, f0, f1, max(r[1] for r in filas), max(r[2] for r in filas), max(r[3] for r in filas), len(mal)))
        for r in mal[:12]:
            print("   f%d  hueco %.3f  se mete %.3f  resbala %.3f" % r)
    return filas
