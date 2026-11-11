# Alturas: que los NINOS se vean ninos y los ADULTOS, adultos (pedido del usuario, EP006, 2026-11-09).
# Antes todos median casi lo mismo (coronilla 4,4-5,45) y Sikelpa salia MAS ALTO que su mama y el presidente.
#
# Se mide la CORONILLA (fin del hueso Head = arriba de la cabeza, sin gorros ni accesorios) y se escala el rig entero
# (piezas, accesorios y lo que tenga en la mano lo siguen). Medidas estandar del kit (coronilla, en metros de Blender):
#   adulto ........ 5,1   (mama, presidente, maestra, vecinos)
#   nino .......... 4,0   (~78 % del adulto: los amigos del protagonista, los ninos del pueblo)
#   nino_chico .... 3,45  (hermanitos menores; Nina y Nina2 ya miden eso)
#   original ...... sin escalar (su tamano tal como se exporto; ej. el protagonista si el usuario lo pide)
# Uso en el script del episodio (despues de anexar el personaje):
#   import alturas
#   alturas.escalar(rig, "nino")        # o un numero: alturas.escalar(rig, 3.85), o "original"
# Al CAMINAR con un rig escalado el paso tambien se encoge (si no, patina):
#   fase = alturas.fase_paso(rig, distancia, "caminar")   en vez de 2*pi*d/CICLOS[tipo]["largo"]
#   y la bajada de cadera que devuelve sb_blender.ciclo se multiplica por alturas.escala(rig).
# tomas_simples.py ya acomoda sus camaras a la escala de cada personaje (la cara sale del mismo tamano).
import math

ADULTO = 5.1
NINO = 4.0
NINO_CHICO = 3.45
ALTURAS = {"adulto": ADULTO, "nino": NINO, "nino_chico": NINO_CHICO}
LARGO_CICLO = {"caminar": 3.0, "correr": 4.6}       # mismo valor que sb_blender.CICLOS[tipo]["largo"] (a escala 1)


def coronilla(rig):
    """altura de la coronilla en reposo, sin la escala del objeto (los rigs del kit tienen los pies en z = 0)"""
    b = rig.data.bones.get("Head")
    if b is not None:
        return b.tail_local.z
    return max(bb.tail_local.z for bb in rig.data.bones)


def escala(rig):
    """escala del rig en el mundo (1 = tamano original)"""
    return rig.matrix_world.to_scale().x


def escalar(rig, altura):
    """escala el rig para que su coronilla quede a 'altura' ("adulto", "nino", "nino_chico", un numero, o "original" =
    sin escalar). Devuelve la escala aplicada."""
    if altura == "original":
        rig.scale = (1.0, 1.0, 1.0)
        rig["altura_kit"] = coronilla(rig)
        return 1.0
    alt = ALTURAS[altura] if isinstance(altura, str) else float(altura)
    s = alt / coronilla(rig)
    rig.scale = (s, s, s)
    rig["altura_kit"] = alt
    return s


def fase_paso(rig, distancia, tipo="caminar"):
    """fase del ciclo de caminar/correr para 'distancia' recorrida, con el paso del tamano del personaje"""
    return 2 * math.pi * distancia / (LARGO_CICLO[tipo] * escala(rig))
