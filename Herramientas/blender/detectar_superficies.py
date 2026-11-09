# DETECTOR de superficies que se "pelean" por verse (z-fighting) y caras duplicadas. Solo LEE: no cambia ni guarda nada.
# Medido en la prueba B (Analizador/Resultados/Investigacion_2026-11-08/B_zfighting, Eevee 5.2, vista previa):
#   - caras EXACTAMENTE en el mismo plano (separacion 0) parpadean en triangulos aunque la camara este cerca;
#   - separadas 0,001-0,003 fallan a 100-150 m con clip_start 0,1; desde 0,01 no fallaron ni a 150 m (ni de frente
#     ni a 1-2 grados rasantes);
#   - dos objetos identicos en el mismo lugar no parpadean pero se ve "el que no era" (la copia).
# Uso (en segundo plano, sobre el .blend guardado):
#   blender -b archivo.blend --python Herramientas/blender/detectar_superficies.py -- [--eps 0.004] [--col NOMBRE] [--json salida.json]
# Dentro de Blender: import detectar_superficies as ds; ds.revisar(eps=0.004)
import bpy, bmesh, json, math, os, sys, time
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _objetos(col=None):
    fuente = bpy.data.collections[col].all_objects if col else bpy.context.scene.objects
    for o in fuente:
        if o.type == 'MESH' and not o.hide_render and o.visible_get():
            yield o


def revisar(eps=0.004, col=None, min_area=0.0004, limite=60):
    """devuelve lista de pares (obj_a, obj_b, tipo, separacion, area) ordenada por area afectada"""
    t0 = time.time()
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, dueno, normales, centros, areas, muestras = [], [], [], [], [], [], []
    for o in _objetos(col):
        oe = o.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except RuntimeError:
            continue
        mw = o.matrix_world
        base = len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        nm = mw.to_3x3().inverted_safe().transposed()
        for p in me.polygons:
            if p.area < 1e-9:
                continue
            pts = [verts[base + i] for i in p.vertices]
            polys.append([base + i for i in p.vertices])
            dueno.append(o.name)
            n = (nm @ p.normal).normalized()
            c = sum(pts, Vector()) / len(pts)
            # area en el mundo (escala incluida)
            a = 0.0
            for k in range(1, len(pts) - 1):
                a += (pts[k] - pts[0]).cross(pts[k + 1] - pts[0]).length / 2
            normales.append(n); centros.append(c); areas.append(a)
            muestras.append([c] + [c.lerp(q, 0.7) for q in pts[:6]])
        oe.to_mesh_clear()
    if not polys:
        return []
    arbol = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
    pares = {}
    for i in range(len(polys)):
        if areas[i] < min_area:
            continue
        n = normales[i]
        if n.z < -0.9 and centros[i].z < 0.05:
            continue                  # cara de abajo apoyada en el piso: nunca se ve
        vistos = set()
        for s in muestras[i]:
            for co, nq, j, d in arbol.find_nearest_range(s, eps):
                if j is None or j == i or j in vistos:
                    continue
                if abs(n.dot(normales[j])) < 0.9995:
                    continue
                sep = abs((s - co).dot(normales[j]))
                if sep > eps or (s - co).length > sep + 1e-4:
                    continue          # el punto cae fuera de la otra cara
                vistos.add(j)
                misma = n.dot(normales[j]) > 0
                if sep < 1e-4:
                    tipo = "duplicada/al ras" if misma else "espalda con espalda"
                else:
                    tipo = "casi coplanar" if misma else "casi coplanar opuesta"
                if n.z < -0.9:
                    tipo += " (techo)"
                a, b = sorted((dueno[i], dueno[j]))
                k = (a, b, tipo)
                e = pares.setdefault(k, {"obj_a": a, "obj_b": b, "tipo": tipo, "sep_min": sep, "area": 0.0, "caras": 0,
                                         "ejemplo": [round(v, 2) for v in s]})
                e["sep_min"] = min(e["sep_min"], sep)
                e["area"] += areas[i]; e["caras"] += 1
    res = sorted(pares.values(), key=lambda e: (e["tipo"] != "duplicada/al ras", -e["area"]))
    for e in res:
        e["area"] = round(e["area"] / 2 if e["obj_a"] == e["obj_b"] else e["area"], 3)
        e["sep_min"] = round(e["sep_min"], 4)
    print("detectar_superficies: %d caras, %d pares en %.1f s" % (len(polys), len(res), time.time() - t0))
    for e in res[:limite]:
        print("  %-18s %-28s %-28s sep %.4f  area %.2f  caras %d  en %s" % (e["tipo"], e["obj_a"][:28], e["obj_b"][:28],
                                                                          e["sep_min"], e["area"], e["caras"], e["ejemplo"]))
    return res


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    eps = float(a[a.index("--eps") + 1]) if "--eps" in a else 0.004
    col = a[a.index("--col") + 1] if "--col" in a else None
    r = revisar(eps=eps, col=col)
    if "--json" in a:
        with open(a[a.index("--json") + 1], "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
