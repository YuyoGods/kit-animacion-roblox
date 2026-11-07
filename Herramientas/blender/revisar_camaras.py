# Revisa cada fotograma: lanza rayos desde la camara activa hacia lo que sigue esa toma (cabeza y pecho de un
# personaje, o el centro de un objeto). Reporta lo que se interpone y cuando sale de cuadro.
# A quien sigue cada camara: propiedad "sujeto" de la camara ("Coco_Rig,Lila_Rig", "Gato"; vacio = no revisar).
# Si la camara no la tiene, usa RIG_NOMBRE. Rangos tapados a proposito: propiedad "excepto" ("338-350,351-360") o EXCEPT.
#   En el Blender abierto:  py Herramientas/blender/bl.py Herramientas/blender/revisar_camaras.py
#   En segundo plano:       blender.exe -b episodio.blend --python Herramientas/blender/revisar_camaras.py [-- desde hasta]
#   (desde/hasta = fotogramas, para revisar solo un tramo)
import bpy, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

RIG_NOMBRE = "Crista_Rig"          # personaje por defecto (camaras sin "sujeto")
EXCEPT = {"CR_Cam_S4_Giro360": (338, 350), "CR_Cam_S5a_Poste": (351, 360)}   # EP001: tapado a proposito
sc = bpy.context.scene
_a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
F0 = int(_a[0]) if len(_a) > 0 else sc.frame_start
F1 = int(_a[1]) if len(_a) > 1 else sc.frame_end


def sujetos(cam):
    s = cam.get("sujeto")
    if s is None:
        return [bpy.data.objects[RIG_NOMBRE]] if RIG_NOMBRE in bpy.data.objects else []
    return [bpy.data.objects[n.strip()] for n in s.split(",") if n.strip() in bpy.data.objects]


def excepto(cam, f):
    rs = [EXCEPT[cam.name]] if cam.name in EXCEPT else []
    for r in str(cam.get("excepto", "")).split(","):
        if "-" in r:
            a, b = r.split("-"); rs.append((int(a), int(b)))
    return any(a <= f <= b for a, b in rs)


def puntos(ob):
    if ob.type == 'ARMATURE':
        pb = ob.pose.bones
        return {"cabeza": ob.matrix_world @ ((pb["Head"].head + pb["Head"].tail) / 2),
                "pecho": ob.matrix_world @ ((pb["UpperTorso"].head + pb["UpperTorso"].tail) / 2)}
    cs = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return {"centro": sum(cs, Vector()) / 8}


def propios(ob):
    return {ob.name} | {c.name for c in ob.children_recursive}


issues, fuera = {}, {}
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    cam = sc.camera
    if cam is None or excepto(cam, f):
        continue
    dg = bpy.context.evaluated_depsgraph_get()
    co = cam.matrix_world.translation
    for k_s, suj in enumerate(sujetos(cam)):
        if suj.hide_render or suj.matrix_world.translation.z < -100:      # escondido o guardado bajo el piso
            continue
        mio = propios(suj)
        pts = puntos(suj)
        for k, p in pts.items():
            d = p - co
            hit, loc, n, i, ob, mw = sc.ray_cast(dg, co, d.normalized(), distance=d.length - 0.05)
            nm = ob.original.name if (hit and ob) else None
            if nm and nm not in mio:
                issues.setdefault(cam.name, []).append((f, suj.name + ":" + k, nm))
            v = world_to_camera_view(sc, cam, p)
            if not (0.02 < v.x < 0.98 and 0.02 < v.y < 0.98 and v.z > 0):
                fuera.setdefault(cam.name, []).append((f, suj.name + ":" + k))
        if k_s == 0 and f % 3 == 0:
            # rejilla de rayos: algo grande y cercano tapando parte del cuadro
            p = list(pts.values())[-1]
            dist = (p - co).length
            frame = cam.data.view_frame(scene=sc)
            M = cam.matrix_world
            near = tot = 0
            for ix in range(5):
                for iy in range(9):
                    u, w_ = (ix + 0.5) / 5, (iy + 0.5) / 9
                    pt = M @ frame[2].lerp(frame[1], u).lerp(frame[3].lerp(frame[0], u), w_)
                    h2, l2, n2, i2, o2, m2 = sc.ray_cast(dg, co, (pt - co).normalized(), distance=dist * 0.6)
                    tot += 1
                    if h2 and o2 and o2.original.name not in mio and n2.z < 0.8:   # el piso no cuenta
                        near += 1
            if near / tot > 0.22:
                issues.setdefault(cam.name, []).append((f, "cuadro", "objeto cercano %d%%" % int(100 * near / tot)))


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
        objs.setdefault((k, nm), []).append(f)
    for (k, nm), fr in objs.items():
        print("  %-22s %-22s tapa: %-28s frames %s" % (cam, k, nm, rangos(fr)))
print("=== FUERA DE CUADRO ===")
if not fuera:
    print("  ninguno")
for cam, lst in fuera.items():
    for k in sorted({kk for _, kk in lst}):
        print("  %-22s %-22s frames %s" % (cam, k, rangos([f for f, kk in lst if kk == k])))
sc.frame_set(sc.frame_start)
