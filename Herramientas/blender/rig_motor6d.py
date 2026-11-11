# RIG DE UN MODELO DE ROBLOX CON ARTICULACIONES PROPIAS (no R15): ciervo, monstruos, animales... (2026-11-11, EP012).
# Arma los huesos EXACTAMENTE como los Motor6D de Studio (cada hueso = Part0 * C0 de su articulacion), asi las animaciones
# de Roblox caen tal cual (animacion_roblox.aplicar_motor6d) sin adivinar ejes.
#
# En Studio (MCP): pegar Herramientas/roblox/studio_personajes.luau, _G.CL_juntas(workspace.<Modelo>) -> juntas.json,
# aislar y exportar el .obj (exportar_obj.ps1) en la MISMA carpeta. Animaciones (opcional): sacar_animacion.luau ->
# <carpeta>/animaciones/<Nombre>.json (quedan como acciones del rig, con usuario falso, listas para anexar).
#
#   blender -b --factory-startup --python Herramientas/blender/rig_motor6d.py -- "<carpeta>" <Nombre>
# Sale <carpeta>/<Nombre>_Rig.blend + previews/ (frente, lado y una hoja con cada animacion). No sobrescribe el .blend.
import bpy, glob, json, math, os, sys
from mathutils import Matrix, Vector

_AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _AQUI)
import animacion_roblox as ar   # noqa: E402

# Roblox (x, y, z) -> Blender (x, -z, y), lo mismo que hace el importador de OBJ (forward -Z, up Y)
Q = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def cf_mat(c):
    """CFrame de Roblox (x, y, z, R00..R22) -> Matrix 4x4."""
    x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = c
    return Matrix(((r00, r01, r02, x), (r10, r11, r12, y), (r20, r21, r22, z), (0, 0, 0, 1)))


def _textura_gris(img):
    import numpy as np
    a = np.empty(len(img.pixels), np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(-1, 4)[::97, :3]
    return float((a.max(1) - a.min(1)).mean()) < 0.06


def materiales(carpeta):
    """como armar_rig_r15_auto: menos brillo, alfa, color de la pieza (Kd) debajo de la textura y texturas grises de
    Material multiplicadas por el color."""
    KD, actual = {}, None
    for f in glob.glob(os.path.join(carpeta, "*.mtl")):
        for linea in open(f, encoding="utf-8", errors="ignore"):
            p = linea.split()
            if p and p[0] == "newmtl":
                actual = " ".join(p[1:])
            elif p and p[0] == "Kd" and actual:
                KD[actual] = tuple(float(x) for x in p[1:4])
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        tx = next((n for n in nt.nodes if n.type == 'TEX_IMAGE'), None)
        if not bs:
            continue
        bs.inputs["Roughness"].default_value = 0.65
        bs.inputs["Specular IOR Level"].default_value = 0.2
        m.use_backface_culling = False
        kd = KD.get(m.name) or KD.get(m.name.rsplit(".", 1)[0])
        if not (tx and tx.image and kd):
            continue
        for l in list(bs.inputs["Alpha"].links):
            nt.links.remove(l)
        bs.inputs["Alpha"].default_value = 1.0
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
        if _textura_gris(tx.image) and min(kd) < 0.9:
            mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
            nt.links.new(tx.outputs["Color"], mix.inputs[6]); mix.inputs[7].default_value = (*kd, 1)
            print("  textura de material x color:", m.name, [round(c, 2) for c in kd])
        else:                                   # lo transparente de la textura muestra el color de la pieza
            mix.blend_type = 'MIX'
            mix.inputs[6].default_value = (*kd, 1)
            nt.links.new(tx.outputs["Color"], mix.inputs[7]); nt.links.new(tx.outputs["Alpha"], mix.inputs[0])
        nt.links.new(mix.outputs[2], bs.inputs["Base Color"])


def armar(carpeta, nombre):
    J = json.load(open(os.path.join(carpeta, "juntas.json"), encoding="utf-8"))
    piezas = {p["n"]: p for p in J["piezas"]}
    motores = {m["p1"]: m for m in J["motores"]}
    raiz = J.get("raiz") or "HumanoidRootPart"

    # --- importar el OBJ: el grupo k del OBJ es la pieza visible numero k (orden inverso de GetDescendants)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    obj = glob.glob(os.path.join(carpeta, "*.obj"))[0]
    antes = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=obj, forward_axis='NEGATIVE_Z', up_axis='Y', use_split_groups=True)
    grupos = [l[2:].strip() for l in open(obj, encoding="utf-8", errors="ignore") if l.startswith("g ")]
    nuevos = {o.name: o for o in set(bpy.data.objects) - antes}
    por_k = {p["obj"]: p for p in J["piezas"] if p["obj"]}
    malla = {}
    peor = 0.0
    for k, g in enumerate(grupos, 1):
        o = nuevos.get(g)
        p = por_k.get(k)
        if not (o and p):
            print("AVISO: grupo sin pieza", k, g)
            continue
        cen = o.matrix_world @ (sum((Vector(v) for v in o.bound_box), Vector()) / 8)
        esperado = (Q @ cf_mat(p["cf"])).translation
        d = (cen - esperado).length
        peor = max(peor, d)
        o.name = "%s_%s" % (nombre, p["n"])
        o.data.name = o.name
        malla[p["n"]] = o
    print("piezas:", len(malla), "de", len(grupos), "| peor distancia centro OBJ vs Studio: %.3f" % peor)

    # --- revisar que el modelo este en su pose de descanso (Part1 = Part0 * C0 * C1^-1)
    err = 0.0
    for p1, m in motores.items():
        if m["p0"] in piezas and p1 in piezas:
            a = cf_mat(piezas[m["p0"]]["cf"]) @ cf_mat(m["c0"]) @ cf_mat(m["c1"]).inverted()
            err = max(err, (a.translation - cf_mat(piezas[p1]["cf"]).translation).length)
    print("pose de descanso: error %.4f studs" % err)

    # --- marco de cada hueso en Roblox: raiz = su CFrame; los demas = CFrame de la PIEZA Part0 * C0
    #     (ojo: la pieza, no el marco del hueso padre; solo coinciden si el C1 del padre no tiene desplazamiento)
    marco = {raiz: cf_mat(piezas[raiz]["cf"])}
    padre = {raiz: None}
    pend = dict(motores)
    while pend:
        avance = False
        for p1, m in list(pend.items()):
            if m["p0"] in marco:
                marco[p1] = cf_mat(piezas[m["p0"]]["cf"]) @ cf_mat(m["c0"])
                padre[p1] = m["p0"]
                del pend[p1]; avance = True
        if not avance:
            print("AVISO: articulaciones sin llegar a la raiz:", list(pend)); break

    # --- acomodo final: mirando a -Y, pies en z = 0, centrado
    pts = [o.matrix_world @ Vector(v) for o in malla.values() for v in o.bound_box]
    zmin = min(p.z for p in pts)
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    look = J.get("mira") or [0, -1]
    girar = Matrix.Rotation(math.pi, 4, 'Z') if look[1] < 0 else Matrix.Identity(4)   # Studio -Z -> Blender +Y
    R = girar @ Matrix.Translation((-cx, -cy, -zmin))
    G = R @ Q
    for o in malla.values():
        o.data.transform(R @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)

    # --- armadura
    arm = bpy.data.armatures.new(nombre + "_Rig")
    rig = bpy.data.objects.new(nombre + "_Rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    alto = max(p.z for p in pts) - zmin
    largo = max(0.25, alto * 0.04)
    eb = {}
    for n in marco:
        b = arm.edit_bones.new(n)
        b.head = (0, 0, 0); b.tail = (0, largo, 0)
        b.matrix = G @ marco[n]
        eb[n] = b
    for n, pa in padre.items():
        if pa:
            eb[n].parent = eb[pa]
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.display_type = 'STICK'
    rig.show_in_front = True

    # --- cada pieza sigue a su hueso (soldadas: al de la pieza con la que estan soldadas)
    hueso_de = {n: n for n in marco}
    for _ in range(5):
        for s in J["soldaduras"]:
            for a, b in ((s["p0"], s["p1"]), (s["p1"], s["p0"])):
                if a in hueso_de and b not in hueso_de:
                    hueso_de[b] = hueso_de[a]
    for n, o in malla.items():
        h = hueso_de.get(n, raiz)
        vg = o.vertex_groups.new(name=h)
        vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
        mod = o.modifiers.new("Armature", 'ARMATURE'); mod.object = rig
        o.parent = rig
    materiales(carpeta)
    print("huesos:", len(marco), "| alto %.2f" % alto)
    return rig, malla, alto


def previews(rig, malla, alto, carpeta, nombre, acciones):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 600, 800
    sc.view_settings.view_transform = 'Standard'
    try:
        sc.eevee.taa_render_samples = 32
    except Exception:
        pass
    if not sc.world:
        sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.68, 0.76, 1)
    for nom, e, rot in (("Sol", 3.0, (50, 0, -30)), ("Relleno", 1.0, (65, 0, 150))):
        ld = bpy.data.lights.new(nom, 'SUN'); ld.energy = e
        lo = bpy.data.objects.new(nom, ld); sc.collection.objects.link(lo)
        lo.rotation_euler = [math.radians(a) for a in rot]
    bpy.ops.mesh.primitive_plane_add(size=alto * 6)
    piso = bpy.context.active_object
    pm = bpy.data.materials.new("Piso_Preview"); pm.use_nodes = True
    pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.38, 0.42, 1)
    piso.data.materials.append(pm)
    cd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cd); sc.collection.objects.link(cam); sc.camera = cam
    cd.lens = 50
    PREV = os.path.join(carpeta, "previews"); os.makedirs(PREV, exist_ok=True)
    cen = Vector((0, 0, alto * 0.5))

    def foto(ruta, d, dist):
        cam.location = cen + Vector(d).normalized() * dist
        cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = ruta
        bpy.ops.render.render(write_still=True)

    rig.animation_data_create()
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    foto(os.path.join(PREV, "frente.png"), (0, -1, 0.12), alto * 2.4)
    foto(os.path.join(PREV, "lado.png"), (1, -0.35, 0.12), alto * 2.4)
    # hoja: 4 momentos de cada animacion
    hojas = []
    for act in acciones:
        rig.animation_data.action = act
        f0, f1 = [int(x) for x in act.frame_range]
        for i in range(4):
            f = f0 + round((f1 - f0) * i / 4)
            sc.frame_set(f)
            ruta = os.path.join(PREV, "_%s_%d.png" % (act.name, i))
            foto(ruta, (0.7, -1, 0.15), alto * 2.6)
            hojas.append((act.name, i, ruta))
    rig.animation_data.action = None
    sc.frame_set(1)
    bpy.data.objects.remove(piso)
    try:
        import numpy as np  # noqa: F401
        w, h = 300, 400
        filas = len(acciones)
        lienzo = bpy.data.images.new("hoja", w * 4, h * max(1, filas))
        px = [0.0] * (w * 4 * h * max(1, filas) * 4)
        for fi, act in enumerate(acciones):
            for (an, i, ruta) in [x for x in hojas if x[0] == act.name]:
                im = bpy.data.images.load(ruta); im.scale(w, h)
                src = list(im.pixels)
                for yy in range(h):
                    y_dst = (filas - 1 - fi) * h + yy
                    a = (y_dst * w * 4 + i * w) * 4
                    px[a:a + w * 4] = src[yy * w * 4:(yy + 1) * w * 4]
                bpy.data.images.remove(im)
                os.remove(ruta)
        lienzo.pixels = px
        lienzo.filepath_raw = os.path.join(PREV, "animaciones.png"); lienzo.file_format = 'PNG'; lienzo.save()
    except Exception as e:
        print("AVISO hoja de animaciones:", e)


if __name__ == "__main__" and "--" in sys.argv:
    a = sys.argv[sys.argv.index("--") + 1:]
    carpeta, nombre = os.path.abspath(a[0]), a[1]
    salida = os.path.join(carpeta, nombre + "_Rig.blend")
    if os.path.exists(salida):
        sys.exit("YA EXISTE (no se sobrescribe): " + salida)
    sc = bpy.context.scene
    sc.render.fps, sc.render.fps_base = 30, 1.0
    rig, malla, alto = armar(carpeta, nombre)
    acciones = []
    for f in sorted(glob.glob(os.path.join(carpeta, "animaciones", "*.json"))):
        anim = ar.cargar(f)
        fin = ar.aplicar_motor6d(rig, anim, inicio=1, nombre_accion=anim["nombre"])
        acciones.append(rig.animation_data.action)
    if rig.animation_data:
        rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
    previews(rig, malla, alto, carpeta, nombre, acciones)
    bpy.ops.wm.save_as_mainfile(filepath=salida)
    print(nombre.upper(), "OK ->", salida, "| acciones:", [x.name for x in acciones])
