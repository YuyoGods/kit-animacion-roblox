# CARAS INTERCAMBIABLES EN LA TEXTURA DE LA CABEZA (sin planos encima de la cara).
# La cabeza del personaje recibe un material propio: color de piel + la cara elegida, pintada de frente desde una
# secuencia de imagenes (Caras/Emociones/_secuencia/cara_0001.png ... ; nombres en caras.json). La cara de fabrica
# se borra (queda solo piel) y la nueva se elige con la propiedad "cara" del rig (un numero). Se anima con keyframes.
# Uso dentro de Blender:
#   import caras_textura as ct
#   ct.preparar(bpy.data.objects["Lila_Rig"], cara=15)
#   ct.preparar(bpy.data.objects["Raul_Rig"], cara=16, cabeza_clasica=malla_de_cabeza_clasica)   # cabezas dinamicas
#   ct.poner(rig, 7, frame)            # cambia a la cara 7 en ese fotograma (keyframe)
#   ct.lista()                          # {numero: emocion}
# Las cabezas dinamicas de Roblox traen ojos y boca con relieve: con cabeza_clasica se cambia la malla por una
# cabeza clasica del mismo tamano para que la cara nueva no se encime con el relieve viejo.
import bpy, os, json
from mathutils import Vector


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "Herramientas", "config.py")):
        d = os.path.dirname(d)
    return d


CARPETA = os.path.join(_raiz(), "Caras", "Emociones", "_secuencia")


def lista():
    d = json.load(open(os.path.join(CARPETA, "caras.json"), encoding="utf-8"))
    return {c["n"]: c["emocion"] for c in d["caras"]}


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _piel(head):
    """color de piel (lineal) de la cabeza: el texel de un lado de la cabeza, o el color base si ahi es transparente."""
    m = head.data.materials[0]
    tex = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image), None)
    base = None
    for n in m.node_tree.nodes:
        if n.type == 'MIX' and getattr(n, "data_type", "") == 'RGBA':
            base = tuple(n.inputs[6].default_value)[:3]
        if n.type == 'BSDF_PRINCIPLED' and base is None and not n.inputs["Base Color"].is_linked:
            base = tuple(n.inputs["Base Color"].default_value)[:3]
    if tex is None:
        return base or (0.8, 0.6, 0.45)
    me = head.data
    uv = me.uv_layers.active.data
    M = head.matrix_world.to_3x3()
    lado = max(me.polygons, key=lambda p: (M @ p.normal).x)          # cara del lado de la cabeza (piel)
    u = sum((uv[li].uv for li in lado.loop_indices), Vector((0, 0))) / len(lado.loop_indices)
    img = tex.image
    W, H = img.size
    x, y = min(W - 1, max(0, int(u.x * W))), min(H - 1, max(0, int(u.y * H)))
    px = img.pixels[(y * W + x) * 4:(y * W + x) * 4 + 4]
    if px[3] < 0.5 and base:
        return base
    return tuple(_lin(c) for c in px[:3])


def _cambiar_malla(head, nueva):
    """pone una malla de cabeza clasica del mismo tamano y lugar que la cabeza original."""
    def caja(me):
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
        return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
    a0, a1 = caja(head.data)
    b0, b1 = caja(nueva)
    me = nueva.copy(); me.name = head.name + "_Clasica"
    s = Vector(((a1.x - a0.x) / (b1.x - b0.x), (a1.y - a0.y) / (b1.y - b0.y), (a1.z - a0.z) / (b1.z - b0.z)))
    ca, cb = (a0 + a1) / 2, (b0 + b1) / 2
    for v in me.vertices:
        v.co = ca + Vector(((v.co.x - cb.x) * s.x, (v.co.y - cb.y) * s.y, (v.co.z - cb.z) * s.z))
    viejo = head.data
    head.data = me
    if viejo.users == 0:
        viejo.name = viejo.name + "_dinamica_sin_uso"
    return me


def preparar(rig, cara=15, cabeza_clasica=None, nombre_cabeza=None, piel=None, ajuste=(0.0, 0.0, 1.0), zona="cabeza"):
    """arma el material de caras en la cabeza del rig. ajuste = (mover_x, mover_z, escala) de la cara en la cabeza.
    zona: "cabeza" = la imagen cubre todo el frente de la cabeza (tamano que le gusto al usuario);
          "frente" = solo la parte plana del frente (como la calcomania de Roblox, caras mas chicas)."""
    pref = rig.name.replace("_Rig", "")
    head = bpy.data.objects[nombre_cabeza or pref + "_Head"]
    if piel is None:
        piel = _piel(head) if not head.get("cara_material") else tuple(head["piel"])
    if not head.get("cara_material"):          # brillo del material original (para que la piel se vea igual)
        bs0 = next((n for n in head.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        head["brillo"] = [bs0.inputs["Roughness"].default_value, bs0.inputs["Specular IOR Level"].default_value] if bs0 else [0.65, 0.2]
    if cabeza_clasica is not None and not head.get("cabeza_clasica"):
        _cambiar_malla(head, cabeza_clasica)
        head["cabeza_clasica"] = True
    me = head.data
    frente = [p for p in me.polygons if p.normal.y < -0.7] if zona == "frente" else []
    vs = {i for p in frente for i in p.vertices} or {v.index for v in me.vertices}
    xs = [me.vertices[i].co.x for i in vs]; zs = [me.vertices[i].co.z for i in vs]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    head["cara_zona"] = [round(x0, 3), round(x1, 3), round(z0, 3), round(z1, 3)]
    cx, cz, esc = (x0 + x1) / 2 + ajuste[0], (z0 + z1) / 2 + ajuste[1], ajuste[2]
    hx, hz = (x1 - x0) / 2 / esc, (z1 - z0) / 2 / esc
    m = bpy.data.materials.get(pref + "_CaraMat") or bpy.data.materials.new(pref + "_CaraMat")
    m.use_nodes = True
    nt = m.node_tree
    if nt.animation_data:
        nt.animation_data_clear()
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    N = nt.nodes.new
    out = N("ShaderNodeOutputMaterial"); bs = N("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = head["brillo"][0]
    bs.inputs["Specular IOR Level"].default_value = head["brillo"][1]
    tc = N("ShaderNodeTexCoord")
    so = N("ShaderNodeSeparateXYZ"); sn = N("ShaderNodeSeparateXYZ")
    mu = N("ShaderNodeMapRange"); mv = N("ShaderNodeMapRange"); mm = N("ShaderNodeMapRange")
    for r, a, b in ((mu, cx - hx, cx + hx), (mv, cz - hz, cz + hz), (mm, -0.35, -0.7)):
        r.inputs["From Min"].default_value = a; r.inputs["From Max"].default_value = b; r.clamp = (r == mm)
    cb = N("ShaderNodeCombineXYZ")
    img = N("ShaderNodeTexImage"); img.name = "CaraImg"; img.extension = 'CLIP'
    seq = bpy.data.images.get(pref + "_Caras")          # una secuencia propia por personaje (si la comparten, todos
    if seq is None:                                      # muestran la misma cara)
        seq = bpy.data.images.load(os.path.join(CARPETA, "cara_0001.png"), check_existing=False)
        seq.name = pref + "_Caras"
    seq.source = 'SEQUENCE'
    img.image = seq
    iu = img.image_user
    iu.frame_duration = 1; iu.frame_start = 1; iu.frame_offset = cara - 1; iu.use_auto_refresh = True; iu.use_cyclic = False
    mul = N("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    mix = N("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (*piel, 1.0)
    L = nt.links.new
    L(tc.outputs["Object"], so.inputs[0]); L(tc.outputs["Normal"], sn.inputs[0])
    L(so.outputs["X"], mu.inputs["Value"]); L(so.outputs["Z"], mv.inputs["Value"]); L(sn.outputs["Y"], mm.inputs["Value"])
    L(mu.outputs["Result"], cb.inputs["X"]); L(mv.outputs["Result"], cb.inputs["Y"])
    L(cb.outputs[0], img.inputs["Vector"])
    L(img.outputs["Alpha"], mul.inputs[0]); L(mm.outputs["Result"], mul.inputs[1])
    L(mul.outputs[0], mix.inputs[0]); L(img.outputs["Color"], mix.inputs[7])
    L(mix.outputs[2], bs.inputs["Base Color"]); L(bs.outputs[0], out.inputs[0])
    for i in range(len(me.materials)):
        me.materials[i] = m
    if not me.materials:
        me.materials.append(m)
    for p in me.polygons:
        p.material_index = 0
    head["cara_material"] = m.name; head["piel"] = list(piel)
    # propiedad del rig y driver
    rig["cara"] = int(cara)
    try:
        ui = rig.id_properties_ui("cara")
        ui.update(min=1, max=len(lista()), description="Cara (ver Caras/Emociones/_secuencia/caras.json)")
    except Exception:
        pass
    fc = nt.driver_add('nodes["CaraImg"].image_user.frame_offset')
    dr = fc.driver; dr.type = 'SCRIPTED'
    v = dr.variables.new(); v.name = "cara"; v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'OBJECT'; v.targets[0].id = rig; v.targets[0].data_path = '["cara"]'
    dr.expression = "cara - 1"
    return m


def poner(rig, cara, frame):
    """cambia de cara en ese fotograma (sin mezcla con la anterior)."""
    prev = rig.get("cara", 1)
    rig["cara"] = int(prev); rig.keyframe_insert('["cara"]', frame=frame - 1)
    rig["cara"] = int(cara); rig.keyframe_insert('["cara"]', frame=frame)
