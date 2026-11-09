# ¿SE VE EL OBJETO CLAVE? (checklist "Calidad de cada toma", docs/05; pedido del usuario 2026-11-08: "que las cosas se
# distingan y salgan en el encuadre"). Para los objetos que dice la voz (papelito, billete, galleta, carta...) revisa:
#   - EN CUADRO: que parte de su recuadro cae dentro del 9:16 y si cae en la franja de los subtitulos (abajo)
#   - TAMANO: ancho en pantalla (% del ancho del cuadro). Menos de 6 % = no se va a notar en el celular
#   - TAPADO: rayos desde la camara a 9 puntos del objeto: cuantos llegan a el
#   - SE DISTINGUE (render=True): foto rapida con y sin el objeto; cuanto cambia la imagen dentro de su recuadro
#     (0-1). Menos de 0,06 = casi no se nota (mismo color que lo de atras, ej. papel blanco en una mano blanca)
# Uso dentro de Blender (despues de poner camaras y animacion):
#   import revisar_objetos as rob; rob.revisar(["EP4_Papelito_T20"], f0, f1, camara=cam, render=True)
import os, tempfile
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

DEPURAR = False
SUBS = (0.15, 0.28)          # franja de subtitulos (desde abajo): ~79 % de la altura desde arriba


def _visible(o):
    return not o.hide_render and o.matrix_world.to_scale().length > 1e-3


def _caja(o):
    return [o.matrix_world @ Vector(c) for c in o.bound_box]


def _recuadro(sc, cam, pts):
    vs = [world_to_camera_view(sc, cam, p) for p in pts]
    vs = [v for v in vs if v.z > 0]
    if not vs:
        return None
    return min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs)


def _en_cuadro(r):
    x0, x1, y0, y1 = r
    a = max(1e-9, (x1 - x0) * (y1 - y0))
    ix = max(0.0, min(1.0, x1) - max(0.0, x0)); iy = max(0.0, min(1.0, y1) - max(0.0, y0))
    return ix * iy / a


def _tapado(sc, cam, o):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = _caja(o)
    c = sum(pts, Vector()) / 8
    muestras = [c] + [c.lerp(p, 0.6) for p in pts]
    origen = cam.matrix_world.translation
    llegan = 0
    for p in muestras:
        d = p - origen
        hit, loc, nrm, idx, ob, mat = sc.ray_cast(dg, origen, d.normalized(), distance=d.length + 0.05)
        if hit and ob is not None and (ob.name == o.name or (ob.parent and ob.parent.name == o.name)):
            llegan += 1
        elif not hit:
            llegan += 1                                   # el rayo no pego en nada antes: no hay quien lo tape
    return llegan / len(muestras)


def _diferencia(sc, cam, objs, r):
    """foto chica con y sin los objetos; diferencia media de color dentro del recuadro (0-1)"""
    rr = sc.render
    guard = (rr.resolution_percentage, sc.eevee.taa_render_samples, rr.filepath, sc.camera, rr.image_settings.file_format)
    rr.resolution_percentage = 20; sc.eevee.taa_render_samples = 4; sc.camera = cam; rr.image_settings.file_format = 'PNG'
    tmp = tempfile.mkdtemp(prefix="revobj_")
    rutas = []
    for i, ocultar in enumerate((False, True)):
        estado = [(o, o.hide_render) for o in objs]
        if ocultar:
            for o in objs:
                o.hide_render = True
        rr.filepath = os.path.join(tmp, "v%d.png" % i)
        bpy.ops.render.render(write_still=True)
        for o, h in estado:
            o.hide_render = h
        rutas.append(rr.filepath)
    rr.resolution_percentage, sc.eevee.taa_render_samples, rr.filepath, sc.camera, rr.image_settings.file_format = guard
    ims = [bpy.data.images.load(p) for p in rutas]
    w, h = ims[0].size
    a, b = list(ims[0].pixels), list(ims[1].pixels)
    x0, x1 = int(max(0, r[0]) * w), int(min(1, r[1]) * w)
    y0, y1 = int(max(0, r[2]) * h), int(min(1, r[3]) * h)
    tot, n = 0.0, 0
    for y in range(y0, max(y0 + 1, y1)):
        for x in range(x0, max(x0 + 1, x1)):
            i = (y * w + x) * 4
            if i + 2 < len(a):
                tot += (abs(a[i] - b[i]) + abs(a[i + 1] - b[i + 1]) + abs(a[i + 2] - b[i + 2])) / 3; n += 1
    for im in ims:
        bpy.data.images.remove(im)
    print("  (fotos de la prueba: %s)" % tmp) if DEPURAR else None
    return tot / max(1, n)


def revisar(nombres, f0, f1, camara=None, render=False, cuadros=3, imprimir=True):
    """nombres: lista de objetos (o un prefijo terminado en '*'). Devuelve lista de avisos (vacia = todo bien)."""
    sc = bpy.context.scene
    if isinstance(nombres, str):
        nombres = [nombres]
    objs = []
    for n in nombres:
        if n.endswith("*"):
            objs += [o for o in bpy.data.objects if o.name.startswith(n[:-1]) and o.type == 'MESH']
        elif bpy.data.objects.get(n):
            objs.append(bpy.data.objects[n])
    avisos = []
    fs = sorted({f0 + (f1 - f0) * (i + 1) // (cuadros + 1) for i in range(cuadros)})
    for o in objs:
        filas = []
        for f in fs:
            sc.frame_set(f)
            cam = camara or sc.camera
            if not _visible(o):
                filas.append((f, None)); continue
            r = _recuadro(sc, cam, _caja(o))
            if r is None:
                filas.append((f, "detras de la camara")); continue
            dentro = _en_cuadro(r)
            ancho = max(0.0, min(1.0, r[1]) - max(0.0, r[0]))
            cy = (r[2] + r[3]) / 2
            tap = _tapado(sc, cam, o)
            dif = _diferencia(sc, cam, [o] + list(o.children_recursive), r) if (render and f == fs[len(fs) // 2]) else None
            prob = []
            if dentro < 0.85:
                prob.append("fuera de cuadro %d %%" % round(100 * (1 - dentro)))
            if ancho < 0.06:
                prob.append("muy chico (%.0f %% del ancho)" % (100 * ancho))
            if SUBS[0] <= cy <= SUBS[1]:
                prob.append("en la franja de los subtitulos")
            if tap < 0.5:
                prob.append("tapado (%d %% visible)" % round(100 * tap))
            if dif is not None and dif < 0.06:
                prob.append("casi no se distingue (cambio %.2f): mas contraste o mas grande" % dif)
            filas.append((f, prob, dentro, ancho, tap, dif))
        vis = [x for x in filas if x[1] is not None and not isinstance(x[1], str)]
        if imprimir:
            if not vis:
                print("revisar_objetos %-22s f%d-%d: no se ve en ningun cuadro revisado (oculto, escala 0 o detras)" % (o.name, f0, f1))
            for x in vis:
                f, prob, dentro, ancho, tap, dif = x
                print("revisar_objetos %-22s f%d: en cuadro %3d %% · ancho %4.1f %% · visible %3d %%%s%s" % (
                    o.name, f, round(100 * dentro), 100 * ancho, round(100 * tap),
                    "" if dif is None else " · se distingue %.2f" % dif, (" -> " + "; ".join(prob)) if prob else " · OK"))
        if not vis:
            avisos.append((o.name, "no se ve"))
        for x in vis:
            if x[1]:
                avisos.append((o.name, x[0], x[1]))
    return avisos
