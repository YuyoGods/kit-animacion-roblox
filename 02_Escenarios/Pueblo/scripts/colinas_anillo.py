# Anillo de colinas alrededor de todo el pueblo (fondo). Se puede repetir.
import bpy, bmesh, math, random
from mathutils import Vector

random.seed(77)
C = Vector((0, 250))          # centro aproximado del pueblo
R_FLAT, R_RISE, R_OUT = 600.0, 820.0, 1600.0
SKY = "#A9CBEA"


def lin(h):
    h = h.lstrip("#")
    o = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        o.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (o[0], o[1], o[2], 1.0)


def far_grass(name, a, b_, haze_dist):
    """pasto que se aclara/azula con la distancia (perspectiva atmosferica)"""
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value = 0.95
    bs.inputs["Specular IOR Level"].default_value = 0.2
    nt.links.new(bs.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.012; nz.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'
    mx.inputs["A"].default_value = lin(a); mx.inputs["B"].default_value = lin(b_)
    nt.links.new(nz.outputs["Fac"], mx.inputs["Factor"])
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 250.0; mr.inputs["From Max"].default_value = haze_dist
    mr.inputs["To Min"].default_value = 0.0; mr.inputs["To Max"].default_value = 0.55
    nt.links.new(cam.outputs["View Distance"], mr.inputs["Value"])
    hz = nt.nodes.new("ShaderNodeMix"); hz.data_type = 'RGBA'
    hz.inputs["B"].default_value = lin(SKY)
    nt.links.new(mr.outputs["Result"], hz.inputs["Factor"])
    nt.links.new(mx.outputs["Result"], hz.inputs["A"])
    nt.links.new(hz.outputs["Result"], bs.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


mat = far_grass("Pasto_ColinaLejana", "#3C7A2B", "#5E9A3A", 2200.0)
# las colinas del norte tambien reciben la perspectiva atmosferica
old = bpy.data.objects.get("Colinas")
if old:
    old.data.materials.clear(); old.data.materials.append(mat)

AF = bpy.data.collections["Afueras"]
for o in list(AF.objects):
    if o.name.startswith(("ColinasAnillo", "PinoAnillo")):
        bpy.data.objects.remove(o)
VEG = bpy.data.collections.get("Vegetacion") or AF
for o in list(VEG.objects):
    if o.name.startswith("PinoAnillo"):
        bpy.data.objects.remove(o)


def ridge(th):
    """altura maxima de la sierra segun el angulo (picos y valles)"""
    h = 85 + 40 * math.sin(3 * th + 1.0) + 28 * math.sin(7 * th + 2.3) + 16 * math.sin(13 * th + 0.4)
    return max(30.0, h)


def ring_z(r, th):
    if r <= R_FLAT:
        return 0.0
    t = min(1.0, (r - R_FLAT) / (R_RISE - R_FLAT))
    rise = t * t * (3 - 2 * t)
    rolls = 0.75 + 0.25 * math.sin(r * 0.012 + th * 9) + 0.12 * math.sin(r * 0.03 - th * 17)
    outer = 1.0 + 0.6 * max(0.0, (r - 1100) / 500)      # al fondo mas alto: varias capas de colinas
    return ridge(th) * rise * rolls * outer


NA, NR = 360, 48
me = bpy.data.meshes.new("ColinasAnillo"); bm = bmesh.new()
rows = []
for j in range(NR + 1):
    r = R_FLAT - 260 + (R_OUT - (R_FLAT - 260)) * j / NR
    row = []
    for i in range(NA):
        th = 2 * math.pi * i / NA
        z = ring_z(r, th) - 0.6
        row.append(bm.verts.new((C.x + r * math.cos(th), C.y + r * math.sin(th), z)))
    rows.append(row)
for j in range(NR):
    for i in range(NA):
        bm.faces.new((rows[j][i], rows[j][(i + 1) % NA], rows[j + 1][(i + 1) % NA], rows[j + 1][i]))
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
me.materials.append(mat)
ring = bpy.data.objects.new("ColinasAnillo", me)
AF.objects.link(ring)

# pinos en las faldas del anillo
PINO = bpy.data.collections.get("Pino_Modelo")
n = 0
for _ in range(3000):
    if n >= 160 or not PINO:
        break
    th = random.uniform(0, 2 * math.pi); r = random.uniform(R_FLAT + 120, 1050)
    z = ring_z(r, th)
    if 3 < z < 70:
        x, y = C.x + r * math.cos(th), C.y + r * math.sin(th)
        # no tapar las colinas del norte ni el camino
        if abs(y - 420) < 22:
            continue
        e = bpy.data.objects.new("PinoAnillo_%03d" % n, None)
        e.instance_type = 'COLLECTION'; e.instance_collection = PINO
        s = random.uniform(1.6, 2.6)
        e.location = (x, y, z - 0.8); e.rotation_euler = (0, 0, random.uniform(0, 6.28)); e.scale = (s, s, s)
        VEG.objects.link(e); n += 1

# que las camaras vean hasta el fondo
for o in bpy.data.objects:
    if o.type == 'CAMERA':
        o.data.clip_end = max(o.data.clip_end, 4000); o.data.clip_start = max(o.data.clip_start, 0.5)

# camaras de prueba hacia el sur, este y oeste
CAMS = bpy.data.collections["Camaras_Centro"]


def cam(name, loc, target, fov):
    o = bpy.data.objects.get(name)
    if o is None:
        cd = bpy.data.cameras.new(name); cd.sensor_fit = 'VERTICAL'
        o = bpy.data.objects.new(name, cd); CAMS.objects.link(o)
    o.data.clip_end = 4000; o.data.angle_y = math.radians(fov); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


cam("Cam_HaciaSur", (0, 322, 9), (0, -400, 40), 42)
cam("Cam_HaciaEste", (-60, 200, 30), (900, 250, 60), 42)
cam("Cam_Panoramica", (0, -560, 260), (0, 300, 0), 46)
print("anillo ok | pinos:", n)
