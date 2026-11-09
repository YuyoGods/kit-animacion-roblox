# ¿SE LE VEN LOS OJOS? Revisa cuadro por cuadro si algo tapa los ojos de un personaje desde la camara activa
# (visera o gorro, cabello, su propia mano, un objeto, otro personaje) o si los ojos quedan fuera de cuadro.
# Lanza un rayo de la camara a cada ojo; si choca antes con otra cosa, ese ojo esta tapado (y dice con que).
# Medido con Sikelpa V3 (prueba A, 2026-11-08): con la cabeza derecha la visera tapa los ojos si la camara queda
# mas de ~16 grados por ENCIMA de la linea de los ojos; cada grado que baja la cabeza resta un grado a ese margen.
# Uso dentro de Blender (o con blender -b archivo.blend --python revisar_ojos.py -- RIG [f0 f1]):
#   import revisar_ojos as ro
#   ro.revisar("Sikelpa_Rig", 1, 90)                      # ojos en el lugar medido (OJOS) o estimados del cubo de la cabeza
import bpy, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# ojos medidos en REPOSO (coordenadas del mundo con el rig en el origen, mirando a -Y)
OJOS = {
    "Sikelpa_Rig": [(-0.112, -0.713, 4.92), (0.112, -0.713, 4.92)],
}


def _cabeza_mesh(rig):
    for o in rig.children_recursive if hasattr(rig, "children_recursive") else rig.children:
        if o.type == 'MESH' and o.parent_bone == "Head" and "Acc" not in o.name:
            return o
    return None


def puntos_ojos(rig):
    """ojos en coordenadas del hueso Head (para seguir a la cabeza en cada cuadro)"""
    hb = rig.data.bones["Head"]
    Minv = hb.matrix_local.inverted()
    if rig.name in OJOS:
        return [Minv @ Vector(p) for p in OJOS[rig.name]]
    cab = _cabeza_mesh(rig)
    vs = [cab.matrix_local @ v.co for v in cab.data.vertices] if cab else []
    if not vs:
        return []
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    y0 = min(v.y for v in vs)
    z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
    ancho = x1 - x0
    z = z0 + 0.59 * (z1 - z0)
    return [Minv @ Vector((cx, y0, z)) for cx in ((x0 + x1) / 2 - 0.08 * ancho, (x0 + x1) / 2 + 0.08 * ancho)]


def revisar(rig_nombre, f0=None, f1=None, camara=None, imprimir=True):
    sc = bpy.context.scene
    rig = bpy.data.objects[rig_nombre]
    ojos_hueso = puntos_ojos(rig)
    cab = _cabeza_mesh(rig)
    f0 = sc.frame_start if f0 is None else f0
    f1 = sc.frame_end if f1 is None else f1
    malos, culpables = [], {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        cam = camara or sc.camera
        dg = bpy.context.evaluated_depsgraph_get()
        Mh = rig.matrix_world @ rig.pose.bones["Head"].matrix
        o = cam.matrix_world.translation
        tapados = []
        for p in ojos_hueso:
            w = Mh @ p
            v = world_to_camera_view(sc, cam, w)
            if not (0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0):
                tapados.append("fuera de cuadro")
                continue
            d = w - o
            hit, loc, nor, idx, obj, mat = sc.ray_cast(dg, o, d.normalized(), distance=d.length - 0.03)
            if hit:
                nombre = obj.name if obj else "?"
                if cab is not None and obj is not None and obj.name == cab.name:
                    nombre = "su propia cabeza (de espaldas o de lado)"
                tapados.append(nombre)
        if tapados:
            malos.append((f, tapados))
            for t in tapados:
                culpables[t] = culpables.get(t, 0) + 1
    n = f1 - f0 + 1
    if imprimir:
        print("revisar_ojos %s f%d-%d: ojos visibles en %d de %d cuadros" % (rig_nombre, f0, f1, n - len(malos), n))
        for t, k in sorted(culpables.items(), key=lambda kv: -kv[1]):
            print("   tapados por %-40s %d ojo-cuadros" % (t, k))
        if malos:
            tramos, ini, prev = [], malos[0][0], malos[0][0]
            for f, _ in malos[1:]:
                if f != prev + 1:
                    tramos.append((ini, prev)); ini = f
                prev = f
            tramos.append((ini, prev))
            print("   tramos con ojos tapados:", ", ".join("%d-%d" % t for t in tramos))
    return {"visibles": n - len(malos), "total": n, "culpables": culpables, "malos": [f for f, _ in malos]}


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    revisar(a[0] if a else "Sikelpa_Rig", int(a[1]) if len(a) > 1 else None, int(a[2]) if len(a) > 2 else None)
