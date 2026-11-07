# Funciones comunes para construir interiores (cajas, cilindros, materiales, luces) en estilo Roblox.
import bpy, bmesh, math
from mathutils import Vector, Matrix


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mat(nombre, color, rough=0.65, emit=0.0, alpha=1.0):
    m = bpy.data.materials.get(nombre)
    if m:
        return m
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:   # Blender 5.x puede crear el material sin nodos
        sal = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bs.outputs["BSDF"], sal.inputs["Surface"])
    c = tuple(lin(v) for v in (hexrgb(color) if isinstance(color, str) else color))
    bs.inputs["Base Color"].default_value = (*c, 1)
    bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = (*c, 1)
        bs.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        bs.inputs["Alpha"].default_value = alpha
        m.surface_render_method = 'DITHERED'
    m.diffuse_color = (*c, 1)
    return m


class Pieza:
    """junta varias cajas/cilindros en UN objeto (con varios materiales) en coordenadas locales de la casa."""
    def __init__(self, nombre, padre, col, M=None):
        self.nombre, self.padre, self.col = nombre, padre, col
        self.M = M or Matrix.Identity(4)
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def caja(self, mn, mx, m):
        x0, y0, z0 = mn; x1, y1, z1 = mx
        vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        bv = [self.bm.verts.new(self.M @ Vector(v)) for v in vs]
        i = self._mi(m)
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.bm.faces.new([bv[k] for k in f]).material_index = i
        return self

    def cil(self, c, r, h, m, segs=16):
        i = self._mi(m)
        ab = [self.bm.verts.new(self.M @ Vector((c[0] + r * math.cos(2 * math.pi * k / segs), c[1] + r * math.sin(2 * math.pi * k / segs), c[2]))) for k in range(segs)]
        ar = [self.bm.verts.new(self.M @ Vector((c[0] + r * math.cos(2 * math.pi * k / segs), c[1] + r * math.sin(2 * math.pi * k / segs), c[2] + h))) for k in range(segs)]
        self.bm.faces.new(list(reversed(ab))).material_index = i
        self.bm.faces.new(ar).material_index = i
        for k in range(segs):
            self.bm.faces.new([ab[k], ab[(k + 1) % segs], ar[(k + 1) % segs], ar[k]]).material_index = i
        return self

    def esfera(self, c, r, m, segs=10, esc=(1, 1, 1)):
        i = self._mi(m)
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=max(4, segs // 2), radius=r,
                                        matrix=self.M @ Matrix.Translation(c) @ Matrix.Diagonal((*esc, 1.0)))
        for f in {f for v in res["verts"] for f in v.link_faces}:
            f.material_index = i
        return self

    def fin(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.nombre)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.nombre, me)
        self.col.objects.link(ob)
        ob.parent = self.padre
        ob.matrix_parent_inverse = Matrix.Identity(4)
        return ob


def M_en(x, y, z=0.0, giro=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(giro), 4, 'Z')


def caja_local(o):
    ps = [o.matrix_basis @ Vector(b) for b in o.bound_box]
    return (Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps))),
            Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps))))



def luz(inst, col, nombre, pos, energia=260, color=(1.0, 0.86, 0.68), radio=0.6):
    ld = bpy.data.lights.new(nombre, 'POINT')
    ld.energy = energia; ld.color = color; ld.shadow_soft_size = radio
    lo = bpy.data.objects.new(nombre, ld)
    col.objects.link(lo)
    lo.parent = inst; lo.matrix_parent_inverse = Matrix.Identity(4)
    lo.location = pos
    return lo




# ----------------------------------------------------------------- muebles reutilizables
def sofa(nombre, inst, col, M, largo, tela, cojin, madera):
    p = Pieza(nombre, inst, col, M)
    a = largo / 2
    p.caja((-a, -1.0, 0.25), (a, 1.0, 1.15), tela)                 # base (frente hacia -y local)
    p.caja((-a + 0.6, -1.0, 1.15), (a - 0.6, 0.55, 1.65), cojin)     # asiento
    p.caja((-a, 0.55, 1.15), (a, 1.0, 3.2), tela)                   # respaldo
    p.caja((-a, -1.0, 1.15), (-a + 0.6, 0.55, 2.3), tela)            # brazos
    p.caja((a - 0.6, -1.0, 1.15), (a, 0.55, 2.3), tela)
    for sx in (-a + 0.3, a - 0.3):
        p.caja((sx - 0.15, -0.85, 0), (sx + 0.15, -0.55, 0.25), madera)
        p.caja((sx - 0.15, 0.55, 0), (sx + 0.15, 0.85, 0.25), madera)
    return p.fin()


def mesa(nombre, inst, col, M, w, d, h, madera, patas=None):
    p = Pieza(nombre, inst, col, M)
    p.caja((-w / 2, -d / 2, h - 0.25), (w / 2, d / 2, h), madera)
    for sx in (-w / 2 + 0.2, w / 2 - 0.45):
        for sy in (-d / 2 + 0.2, d / 2 - 0.45):
            p.caja((sx, sy, 0), (sx + 0.25, sy + 0.25, h - 0.25), patas or madera)
    return p.fin()


def silla(nombre, inst, col, M, madera, asiento):
    p = Pieza(nombre, inst, col, M)
    p.caja((-0.8, -0.8, 1.55), (0.8, 0.8, 1.8), asiento)
    p.caja((-0.8, 0.6, 1.8), (0.8, 0.8, 3.6), madera)
    for sx in (-0.75, 0.55):
        for sy in (-0.75, 0.55):
            p.caja((sx, sy, 0), (sx + 0.2, sy + 0.2, 1.55), madera)
    return p.fin()


def cama(nombre, inst, col, M, colcha, almohada, madera, largo=5.8, ancho=3.4):
    """cabecera en +y local."""
    p = Pieza(nombre, inst, col, M)
    a = ancho / 2
    p.caja((-a, -largo / 2, 0), (a, largo / 2, 0.9), madera)
    p.caja((-a + 0.1, -largo / 2 + 0.1, 0.9), (a - 0.1, largo / 2 - 0.1, 1.5), almohada)       # colchon
    p.caja((-a + 0.05, -largo / 2 + 0.05, 1.2), (a - 0.05, largo / 2 - 1.5, 1.6), colcha)      # cobija
    p.caja((-a + 0.4, largo / 2 - 1.4, 1.5), (a - 0.4, largo / 2 - 0.3, 1.95), almohada)       # almohada
    p.caja((-a, largo / 2 - 0.3, 0), (a, largo / 2, 3.2), madera)                             # cabecera
    return p.fin()


def librero(nombre, inst, col, M, madera, colores_libros, ancho=2.4, alto=5.5):
    p = Pieza(nombre, inst, col, M)
    p.caja((-ancho / 2, -0.35, 0), (-ancho / 2 + 0.15, 0.35, alto), madera)
    p.caja((ancho / 2 - 0.15, -0.35, 0), (ancho / 2, 0.35, alto), madera)
    p.caja((-ancho / 2, 0.25, 0), (ancho / 2, 0.35, alto), madera)
    k = 0
    for z in [0.1 + i * (alto - 0.2) / 4 for i in range(5)]:
        p.caja((-ancho / 2, -0.35, z), (ancho / 2, 0.35, z + 0.12), madera)
        if z < alto - 0.5:
            x = -ancho / 2 + 0.25
            while x < ancho / 2 - 0.45:
                w = 0.18 + 0.08 * ((k * 7) % 3)
                hh = 0.75 + 0.12 * ((k * 5) % 4)
                p.caja((x, -0.25, z + 0.12), (x + w, 0.2, z + 0.12 + hh), colores_libros[k % len(colores_libros)])
                x += w + 0.04; k += 1
    return p.fin()


def planta(nombre, inst, col, M, maceta, hojas):
    p = Pieza(nombre, inst, col, M)
    p.cil((0, 0, 0), 0.55, 1.1, maceta, 12)
    p.esfera((0, 0, 2.0), 0.95, hojas, 8)
    p.esfera((0.35, 0.2, 2.7), 0.6, hojas, 8)
    p.esfera((-0.3, -0.2, 2.6), 0.55, hojas, 8)
    return p.fin()


def lampara_techo(nombre, inst, col, pos, metal, foco):
    p = Pieza(nombre, inst, col, Matrix.Translation(pos))
    p.cil((0, 0, -0.15), 0.08, 0.15, metal, 8)
    p.cil((0, 0, -0.75), 0.9, 0.6, foco, 16)
    return p.fin()


def cuadro(nombre, inst, col, M, w, h, marco, lienzo):
    p = Pieza(nombre, inst, col, M)
    p.caja((-w / 2, -0.08, -h / 2), (w / 2, 0, h / 2), marco)
    p.caja((-w / 2 + 0.15, -0.12, -h / 2 + 0.15), (w / 2 - 0.15, -0.05, h / 2 - 0.15), lienzo)
    return p.fin()


