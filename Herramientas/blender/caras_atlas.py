# CARAS PARA CABEZAS DINAMICAS (atlas de rasgos, como Crush): cambia la textura completa de la cabeza por una
# secuencia de variantes (atlas_0001.png, atlas_0002.png ...) hechas desde su propia textura, y la elige la propiedad
# "cara" del rig (1, 2, 3...). Sin planos encima: es la misma cabeza con otra boca / rubor dibujados en su textura.
# Uso dentro de Blender:
#   import caras_atlas as ca
#   ca.preparar(bpy.data.objects["Crush_Rig"], bpy.data.objects["Crush_Head"], r"...\Personajes\Secundarios\Crush\caras", cara=1)
#   ca.poner(rig, 3, frame)      # cambia a la cara 3 en ese fotograma (cambio seco)
# Las variantes y sus nombres (caras.json) los hace un script del personaje (ej. Crush/caras/hacer_caras_crush.py).
import bpy, os, json


def nombres(carpeta):
    d = json.load(open(os.path.join(carpeta, "caras.json"), encoding="utf-8"))
    return {c["n"]: c["emocion"] for c in d["caras"]}


def preparar(rig, cabeza, carpeta, cara=1):
    primera = os.path.join(carpeta, "atlas_0001.png")
    seq = bpy.data.images.get(rig.name + "_CarasAtlas")
    if seq is None:
        seq = bpy.data.images.load(primera, check_existing=False)
        seq.name = rig.name + "_CarasAtlas"
    seq.source = 'SEQUENCE'
    tocados = 0
    for m in {s.material for s in cabeza.material_slots if s.material}:
        nt = m.node_tree
        for n in nt.nodes:
            if n.type != 'TEX_IMAGE' or n.image is None:
                continue
            if n.image != seq:
                n["imagen_original"] = n.image.name
            n.image = seq
            iu = n.image_user
            iu.frame_duration = 1; iu.frame_start = 1; iu.frame_offset = cara - 1; iu.use_auto_refresh = True; iu.use_cyclic = False
            path = 'nodes["%s"].image_user.frame_offset' % n.name
            try:
                nt.driver_remove(path)
            except Exception:
                pass
            fc = nt.driver_add(path); d = fc.driver; d.type = 'SCRIPTED'
            v = d.variables.new(); v.name = "cara"; v.type = 'SINGLE_PROP'
            v.targets[0].id_type = 'OBJECT'; v.targets[0].id = rig; v.targets[0].data_path = '["cara"]'
            d.expression = "cara - 1"
            tocados += 1
    rig["cara"] = int(cara)
    try:
        lista = nombres(carpeta)
        rig.id_properties_ui("cara").update(min=1, max=max(lista), description="Cara: " + ", ".join("%d %s" % kv for kv in lista.items()))
    except Exception:
        pass
    return tocados


def poner(rig, cara, frame):
    prev = rig.get("cara", 1)
    rig["cara"] = int(prev); rig.keyframe_insert('["cara"]', frame=frame - 1)
    rig["cara"] = int(cara); rig.keyframe_insert('["cara"]', frame=frame)
