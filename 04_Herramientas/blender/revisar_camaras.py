# Revisa cada fotograma: lanza rayos desde la camara activa hacia la cabeza y el pecho de Crista.
# Si algo (que no sea Crista) se interpone, lo reporta por toma. Tambien avisa si ella sale de cuadro.
import bpy, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

RIG_NOMBRE = "Crista_Rig"          # cambiar por el rig del personaje que seguimos
sc = bpy.context.scene
rig = bpy.data.objects[RIG_NOMBRE]
CRISTA = {rig.name} | {o.name for o in rig.children}
EXCEPT = {"CR_Cam_S4_Giro360": (338, 350), "CR_Cam_S5a_Poste": (351, 360)}   # tapado a proposito (transicion)
issues = {}
fuera = {}
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    cam = sc.camera
    dg = bpy.context.evaluated_depsgraph_get()
    pb = rig.pose.bones
    pts = {"cabeza": rig.matrix_world @ ((pb["Head"].head + pb["Head"].tail) / 2),
           "pecho": rig.matrix_world @ ((pb["UpperTorso"].head + pb["UpperTorso"].tail) / 2)}
    co = cam.matrix_world.translation
    ex = EXCEPT.get(cam.name)
    for k, p in pts.items():
        d = p - co
        hit, loc, n, i, ob, mw = sc.ray_cast(dg, co, d.normalized(), distance=d.length - 0.05)
        if hit and ob and ob.name not in CRISTA and ob.original.name not in CRISTA:
            if ex and ex[0] <= f <= ex[1]:
                continue
            nm = ob.original.name if hasattr(ob, "original") else ob.name
            issues.setdefault(cam.name, []).append((f, k, nm))
        v = world_to_camera_view(sc, cam, p)
        if k == "pecho" and f % 3 == 0 and not (ex and ex[0] <= f <= ex[1]):
            # rejilla de rayos: algo grande y cercano tapando parte del cuadro
            frame = cam.data.view_frame(scene=sc)
            M = cam.matrix_world
            near = 0
            tot = 0
            for ix in range(5):
                for iy in range(9):
                    u, w_ = (ix + 0.5) / 5, (iy + 0.5) / 9
                    pt = frame[2].lerp(frame[1], u)          # abajo izq -> abajo der
                    top = frame[3].lerp(frame[0], u)
                    pt = M @ pt.lerp(top, w_)
                    dirv = (pt - co).normalized()
                    h2, l2, n2, i2, o2, m2 = sc.ray_cast(dg, co, dirv, distance=d.length * 0.6)
                    tot += 1
                    if h2 and o2 and o2.original.name not in CRISTA and n2.z < 0.8:   # el piso no cuenta
                        near += 1
            if near / tot > 0.22:
                issues.setdefault(cam.name, []).append((f, "cuadro", "objeto cercano %d%%" % int(100 * near / tot)))
        if not (0.02 < v.x < 0.98 and 0.02 < v.y < 0.98 and v.z > 0):
            if not (ex and ex[0] <= f <= ex[1]):
                fuera.setdefault(cam.name, []).append((f, k))


def rangos(frames):
    out = []
    for f in sorted(set(frames)):
        if out and f == out[-1][1] + 1:
            out[-1][1] = f
        else:
            out.append([f, f])
    return ", ".join("%d-%d" % (a, b) if a != b else str(a) for a, b in out)


print("=== OBSTRUCCIONES ===")
if not issues:
    print("  ninguna")
for cam, lst in issues.items():
    objs = {}
    for f, k, nm in lst:
        objs.setdefault(nm, []).append(f)
    for nm, fr in objs.items():
        print("  %-22s %-28s frames %s" % (cam, nm, rangos(fr)))
print("=== FUERA DE CUADRO ===")
if not fuera:
    print("  ninguno")
for cam, lst in fuera.items():
    for k in ("cabeza", "pecho"):
        fr = [f for f, kk in lst if kk == k]
        if fr:
            print("  %-22s %-7s frames %s" % (cam, k, rangos(fr)))
sc.frame_set(1)
