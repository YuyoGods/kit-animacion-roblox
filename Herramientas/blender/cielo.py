# Cielo decorativo para cualquier mapa: de dia azul bonito con sol y nubes; de noche con estrellas.
# SOLO lo ve la camara: la luz y el brillo del mapa NO cambian (siguen saliendo del "Background" del mundo, como siempre).
# Cambia solo a noche cuando el mapa se pone oscuro (cuando un episodio oscurece el color del Background), asi los
# episodios no tienen que hacer nada extra. Las nubes se mueven despacito.
#   En el Blender abierto:  py Herramientas/blender/bl.py Herramientas/blender/cielo.py
#   En segundo plano:       blender -b mapa.blend --python Herramientas/blender/cielo.py -- [--guardar]
#   Desde otro script:      import cielo; cielo.poner(bpy.context.scene)
# Ajustes (argumentos de poner): nubes 0..1 (cuantas), estrellas 0..1, sol_tam (radio del sol en grados, con su brillo
# suave alrededor), sol_altura (grados sobre el horizonte; el sol sale del lado de donde viene la luz del Sol del mapa),
# sol=False para no dibujarlo. Se puede repetir: solo rehace sus propios nodos (los que empiezan con "Cielo_");
# quitar(sc) lo deja como antes.
# OJO en los scripts de episodio: para dia/noche con keyframes en el Background, NO borrar animation_data del mundo
# (ahi viven los drivers del cielo): solo quitar la accion; y usar el Background que NO empieza con "Cielo_".
import math, sys
import bpy
from mathutils import Vector

DIA_CENIT, DIA_HORIZONTE = (0.10, 0.33, 0.85), (0.55, 0.76, 0.98)
NOCHE_CENIT, NOCHE_HORIZONTE = (0.004, 0.008, 0.030), (0.020, 0.040, 0.100)
NUBE_BLANCO, NUBE_SOMBRA = (0.95, 0.96, 0.99), (0.72, 0.79, 0.90)   # un poco menos blancas que el sol
SOL_COLOR, SOL_BRILLO = (1.0, 1.0, 0.98), (1.0, 0.97, 0.88)   # sol blanco; brillo (bloom) blanco calido


def _fondo(nt):
    """el Background que ilumina el mapa (el de siempre, no el del cielo)"""
    return next(n for n in nt.nodes if n.type == "BACKGROUND" and not n.name.startswith("Cielo_"))


def quitar(sc):
    """deja el mundo como estaba: Background -> salida"""
    nt = sc.world.node_tree
    for n in [n for n in nt.nodes if n.name.startswith("Cielo_")]:
        nt.nodes.remove(n)
    salida = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    nt.links.new(_fondo(nt).outputs[0], salida.inputs["Surface"])


def poner(sc, nubes=0.55, estrellas=1.0, sol=True, sol_altura=26.0, sol_tam=4.5):
    if not sc.world:
        sc.world = bpy.data.worlds.new("Cielo")
    w = sc.world
    w.use_nodes = True
    nt = w.node_tree
    if not any(n.type == "BACKGROUND" for n in nt.nodes):
        b = nt.nodes.new("ShaderNodeBackground")
        b.inputs[0].default_value = (0.397, 0.597, 0.823, 1.0); b.inputs[1].default_value = 0.9
    quitar(sc)
    fondo = _fondo(nt)
    salida = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    x0, y0 = fondo.location.x, fondo.location.y - 900

    def nodo(tipo, nombre, x, y, **props):
        n = nt.nodes.new(tipo)
        n.name = n.label = "Cielo_" + nombre
        n.location = (x0 + x, y0 + y)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def sock(lista, ident):
        return next(s for s in lista if s.identifier == ident)

    L = nt.links.new

    def mate(op, a, b=None, x=0, y=0, nombre="m"):
        n = nodo("ShaderNodeMath", nombre, x, y, operation=op)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs[0]

    def rango(v, de0, de1, a0=0.0, a1=1.0, x=0, y=0, nombre="r", suave=True):
        n = nodo("ShaderNodeMapRange", nombre, x, y, data_type="FLOAT",
                 interpolation_type="SMOOTHSTEP" if suave else "LINEAR", clamp=True)
        L(v, n.inputs[0])
        for i, val in zip((1, 2, 3, 4), (de0, de1, a0, a1)):
            n.inputs[i].default_value = val
        return n.outputs[0]

    def color(c, x=0, y=0, nombre="c"):
        n = nodo("ShaderNodeRGB", nombre, x, y)
        n.outputs[0].default_value = (c[0], c[1], c[2], 1.0)
        return n.outputs[0]

    def mezcla(a, b, fac, x=0, y=0, nombre="mix", modo="MIX"):
        n = nodo("ShaderNodeMix", nombre, x, y, data_type="RGBA", blend_type=modo, clamp_result=False)
        f = sock(n.inputs, "Factor_Float")
        if isinstance(fac, (int, float)):
            f.default_value = fac
        else:
            L(fac, f)
        L(a, sock(n.inputs, "A_Color")); L(b, sock(n.inputs, "B_Color"))
        return sock(n.outputs, "Result_Color")

    def degradado(z, cenit, horizonte, x, y, nombre):
        t = rango(z, 0.0, 0.65, x=x, y=y, nombre=nombre + "_t")
        return mezcla(color(horizonte, x + 200, y + 80, nombre + "_h"), color(cenit, x + 200, y - 80, nombre + "_c"), t,
                      x + 400, y, nombre)

    # direccion a la que mira cada pixel del cielo
    tc = nodo("ShaderNodeTexCoord", "Coord", -1600, 0)
    dn = nodo("ShaderNodeVectorMath", "Dir", -1400, 0, operation="NORMALIZE")
    L(tc.outputs["Generated"], dn.inputs[0])
    d = dn.outputs["Vector"]
    sep = nodo("ShaderNodeSeparateXYZ", "XYZ", -1200, 0)
    L(d, sep.inputs[0])
    z = sep.outputs["Z"]

    # ------------------------------------------------ DIA: degradado azul + nubes + sol
    dia = degradado(z, DIA_CENIT, DIA_HORIZONTE, -1000, 400, "Dia")
    cosd = None                                         # que tan cerca del sol mira cada pixel (1 = justo al sol)
    if sol:
        luz = next((o for o in sc.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
        v = (luz.matrix_world.to_3x3() @ Vector((0, 0, 1))) if luz else Vector((-0.7, -0.7, 0.4))
        az, alt = math.atan2(v.y, v.x), math.radians(sol_altura)
        sv = nodo("ShaderNodeCombineXYZ", "SolDir", -1000, 700)
        sv.inputs["X"].default_value = math.cos(alt) * math.cos(az)
        sv.inputs["Y"].default_value = math.cos(alt) * math.sin(az)
        sv.inputs["Z"].default_value = math.sin(alt)
        pd = nodo("ShaderNodeVectorMath", "SolPunto", -800, 700, operation="DOT_PRODUCT")
        L(d, pd.inputs[0]); L(sv.outputs[0], pd.inputs[1])
        cosd = pd.outputs["Value"]
    if nubes > 0:
        # nubes en un "techo" plano: se ven mas chicas hacia el horizonte (perspectiva)
        zz = mate("ADD", z, 0.28, -1000, -100, "TechoZ")
        uv = nodo("ShaderNodeVectorMath", "TechoUV", -800, -100, operation="DIVIDE")
        L(d, uv.inputs[0])
        cz = nodo("ShaderNodeCombineXYZ", "TechoDiv", -1000, -260)
        for k in ("X", "Y", "Z"):
            L(zz, cz.inputs[k])
        L(cz.outputs[0], uv.inputs[1])
        viento = nodo("ShaderNodeValue", "Viento", -1000, -420)
        fc = viento.outputs[0].driver_add("default_value")
        fc.driver.expression = "frame * 0.0005"            # las nubes avanzan despacito
        mv = nodo("ShaderNodeCombineXYZ", "VientoXYZ", -800, -420)
        L(viento.outputs[0], mv.inputs["X"])
        uvm = nodo("ShaderNodeVectorMath", "TechoMov", -600, -200, operation="ADD")
        L(uv.outputs["Vector"], uvm.inputs[0]); L(mv.outputs[0], uvm.inputs[1])
        ruido = nodo("ShaderNodeTexNoise", "Nubes", -400, -200, noise_dimensions="3D")
        L(uvm.outputs["Vector"], ruido.inputs["Vector"])
        ruido.inputs["Scale"].default_value = 1.35
        ruido.inputs["Detail"].default_value = 4.0
        ruido.inputs["Roughness"].default_value = 0.55
        umbral = 0.60 - 0.12 * nubes                     # mas nubes = umbral mas bajo
        forma = rango(ruido.outputs["Fac"], umbral, umbral + 0.06, x=-200, y=-120, nombre="NubeForma")
        lejos = rango(z, 0.02, 0.16, x=-200, y=-300, nombre="NubeHorizonte")
        mascara = mate("MULTIPLY", forma, lejos, 0, -200, "NubeMascara")
        if cosd is not None:                             # cielo despejado alrededor del sol: asi el sol se ve
            cerca = rango(cosd, math.cos(math.radians(sol_tam * 4.0)), math.cos(math.radians(sol_tam * 1.6)),
                          x=-200, y=-40, nombre="NubeSol")
            claro = mate("SUBTRACT", 1.0, cerca, 0, -40, "NubeClaro")
            mascara = mate("MULTIPLY", mascara, claro, 200, -120, "NubeMascaraSol")
        relleno = rango(ruido.outputs["Fac"], umbral + 0.02, umbral + 0.16, x=-200, y=-460, nombre="NubeRelleno")
        nube = mezcla(color(NUBE_SOMBRA, 0, -560, "NubeSombraC"), color(NUBE_BLANCO, 0, -660, "NubeBlancoC"), relleno,
                      200, -500, "NubeColor")
        dia = mezcla(dia, nube, mascara, 400, 200, "DiaNubes")
    if sol:
        # sol blanco con brillo suave alrededor (bloom pintado en el cielo): no se ve el borde de un circulo
        # y no ilumina el mapa (es solo del cielo, no un efecto sobre toda la imagen)
        disco = rango(cosd, math.cos(math.radians(sol_tam * 1.25)), math.cos(math.radians(sol_tam * 0.35)),
                      x=-600, y=760, nombre="SolDisco")                       # centro blanco que se desvanece
        halo = rango(cosd, math.cos(math.radians(sol_tam * 3.2)), 1.0, x=-600, y=600, nombre="SolHalo", suave=False)
        halo = mate("POWER", halo, 3.0, -400, 600, "SolHaloCurva")
        halo = mate("MULTIPLY", halo, 0.75, -200, 600, "SolHaloFuerza")             # brillo cercano
        lejos = rango(cosd, math.cos(math.radians(sol_tam * 8.0)), 1.0, x=-600, y=440, nombre="SolBloom", suave=False)
        lejos = mate("POWER", lejos, 2.0, -400, 440, "SolBloomCurva")
        lejos = mate("MULTIPLY", lejos, 0.15, -200, 440, "SolBloomFuerza")          # resplandor amplio
        dia = mezcla(dia, color(SOL_BRILLO, 400, 600, "SolBloomC"), lejos, 600, 400, "DiaBloom", modo="ADD")
        dia = mezcla(dia, color(SOL_BRILLO, 400, 760, "SolBrilloC"), halo, 600, 500, "DiaHalo", modo="ADD")
        dia = mezcla(dia, color(SOL_COLOR, 600, 760, "SolC"), disco, 800, 500, "DiaSol")

    # ------------------------------------------------ NOCHE: degradado oscuro + estrellas
    noche = degradado(z, NOCHE_CENIT, NOCHE_HORIZONTE, -1000, -1000, "Noche")
    if estrellas > 0:
        arriba = rango(z, 0.02, 0.18, x=-600, y=-1500, nombre="EstrellaHorizonte")
        for k, (escala, radio, cuantas, brillo) in enumerate(((150.0, 0.12, 0.16, 0.9), (55.0, 0.11, 0.10, 1.0))):
            vor = nodo("ShaderNodeTexVoronoi", "Estrellas%d" % k, -800, -1250 - 300 * k, voronoi_dimensions="3D",
                       feature="F1", distance="EUCLIDEAN")
            L(d, vor.inputs["Vector"])
            vor.inputs["Scale"].default_value = escala
            punto = rango(vor.outputs["Distance"], radio, radio * 0.35, x=-600, y=-1250 - 300 * k, nombre="EstPunto%d" % k)
            sepc = nodo("ShaderNodeSeparateColor", "EstAzar%d" % k, -600, -1350 - 300 * k)
            L(vor.outputs["Color"], sepc.inputs[0])
            hay = rango(sepc.outputs["Red"], 1.0 - cuantas * estrellas - 0.002, 1.0 - cuantas * estrellas, x=-400,
                        y=-1350 - 300 * k, nombre="EstHay%d" % k, suave=False)
            fuerza = rango(sepc.outputs["Green"], 0.0, 1.0, 0.35 * brillo, brillo, -400, -1450 - 300 * k, "EstFuerza%d" % k, False)
            e = mate("MULTIPLY", punto, hay, -200, -1250 - 300 * k, "Est%d_a" % k)
            e = mate("MULTIPLY", e, fuerza, 0, -1250 - 300 * k, "Est%d_b" % k)
            e = mate("MULTIPLY", e, arriba, 200, -1250 - 300 * k, "Est%d_c" % k)
            noche = mezcla(noche, color((0.92, 0.95, 1.0), 200, -1400 - 300 * k, "EstColor%d" % k), e,
                           400, -1250 - 300 * k, "NocheEst%d" % k, modo="ADD")

    # ------------------------------------------------ de noche cuando el mapa se pone oscuro (sin tocar nada mas)
    fn = nodo("ShaderNodeValue", "EsNoche", 600, -300)
    fc = fn.outputs[0].driver_add("default_value")
    dv = fc.driver
    dv.type = "SCRIPTED"
    for canal, letra in enumerate("rgb"):
        var = dv.variables.new()
        var.name = letra
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "WORLD"
        var.targets[0].id = w
        var.targets[0].data_path = 'node_tree.nodes["%s"].inputs[0].default_value[%d]' % (fondo.name, canal)
    dv.expression = "1 - min(1, max(0, (0.2126*r + 0.7152*g + 0.0722*b - 0.05) / 0.15))"
    cielo = mezcla(dia, noche, fn.outputs[0], 1000, 0, "DiaNoche")
    bg = nodo("ShaderNodeBackground", "Fondo", 1200, 0)
    L(cielo, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0
    camino = nodo("ShaderNodeLightPath", "SoloCamara", 1200, 300)
    ms = nodo("ShaderNodeMixShader", "Mezcla", 1400, 200)
    L(camino.outputs["Is Camera Ray"], ms.inputs[0])
    L(fondo.outputs[0], ms.inputs[1])                    # la luz del mapa: la de siempre
    L(bg.outputs[0], ms.inputs[2])                       # lo que ve la camara: el cielo nuevo
    L(ms.outputs[0], salida.inputs["Surface"])
    w["cielo_decorativo"] = 1
    return w


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    poner(bpy.context.scene)
    print("Cielo listo: de dia azul con sol y nubes, de noche con estrellas (solo para la camara).")
    if "--guardar" in a:
        bpy.ops.wm.save_mainfile()
        print("Guardado:", bpy.data.filepath)
