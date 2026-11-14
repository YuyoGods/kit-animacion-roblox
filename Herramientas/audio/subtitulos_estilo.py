# SUBTITULOS con estilo (ASS para quemar con FFmpeg/libass). Lo usa armar_video.py (plantilla del kit).
#
# "custerk" (por defecto): copia de los subtitulos NUEVOS de Custerk (estrenados en su Short mas reciente, p1mP2c4RzUk del
#   12-nov-2026; sus otros 22 videos del 9 al 12-nov siguen en minusculas), medidos cuadro a cuadro el 2026-11-12 en
#   Analizador/Resultados/CuadroACuadro/subtitulos/:
#   - UNA palabra a la vez, EN MAYUSCULAS, letra Montserrat Black (la que usa CapCut; viene con Roblox y CapCut, la
#     busca sola; si no esta, Arial Black). "CONTADOS" mide ~580 px de 1080 en reposo.
#   - relleno con DEGRADADO suave (no es blanco puro): #FAFBFF arriba -> #F3F4FB -> #E9ECF5 abajo; las palabras clave
#     y los numeros en dorado: #FDE181 -> #FEB527 -> #FDA014. Contorno negro grueso (~11 px) y sombra oscura hacia
#     abajo (~7 px), efecto 3D.
#   - ENTRADA POP con rebote: 48 -> 72 -> 96 -> 120 % (cuadro 3) y regresa a 100 % en el cuadro 7
#     (medido: 48, 68, 93, 120, 113, 107, 102, 100).
#   - centro a 69 % de la altura (Custerk 69,2 %), dentro de la zona segura de Shorts.
#   Las palabras largas se achican solas: en reposo caben en 770 px (14-86 % del ancho).
# "custerk_viejo": sus subtitulos de antes (todos sus videos hasta el 12-nov menos el ultimo): minusculas, entrada sutil
#   92 -> 96 -> 100 %, 68 %, palabra clave en rojo.
# "clasico": el nuestro de antes (1-2 palabras en minusculas, 79 % de la altura, entrada 118 % -> 100 %).
#
# Uso (dentro de armar_video.py):
#   import subtitulos_estilo as se
#   texto_ass, eventos = se.armar(VOZ["palabras"], DUR, clave=CLAVE, callar=CALLAR, estilo="custerk")
#   filtro = se.filtro("subtitulos.ass", AUD, estilo="custerk")   # "subtitles=subtitulos.ass:fontsdir=_fuentes"
import glob
import os
import re
import shutil
import unicodedata

FUENTES_WIN = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
_LOCAL = os.environ.get("LOCALAPPDATA", "")
_ROAM = os.environ.get("APPDATA", "")
_KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
# donde buscar una letra que no viene con Windows (en orden): carpeta del kit, Windows, usuario, Roblox, CapCut
BUSCAR = [_KIT, FUENTES_WIN, os.path.join(_LOCAL, "Microsoft", "Windows", "Fonts"),
          os.path.join(_LOCAL, "Roblox", "Versions", "*", "content", "fonts"),
          os.path.join(_ROAM, "weblauncher", "core", "roblox", "*", "content", "fonts"),
          os.path.join(_LOCAL, "CapCut", "User Data", "Cache", "effect", "*", "*")]

BLANCO = ["#FAFBFF", "#F3F4FB", "#E9ECF5"]          # arriba, medio, abajo (medido en su relleno, 8 franjas)
DORADO = ["#FDE181", "#FEB527", "#FDA014"]
ESTILOS = {
    "custerk": dict(fuentes=[("Montserrat Black", "Montserrat-Black.ttf"), ("Arial Black", "ariblk.ttf")], tam=124,
                    mayusculas=True, palabras=1, x=540, y=1325, borde=11, sombra_y=7, color_sombra="#14141C",
                    alfa_sombra=0x18, ancho_max=770, entrada="rebote", relleno=BLANCO, relleno_clave=DORADO,
                    numeros_clave=True, franjas=6, adelanto=0.03, llenar_hueco=0.35),
    "custerk_viejo": dict(fuentes=[("Montserrat Black", "Montserrat-Black.ttf"), ("Arial Black", "ariblk.ttf")], tam=112,
                          mayusculas=False, palabras=1, x=540, y=1311, borde=10, sombra_y=4, color_sombra="#000000",
                          alfa_sombra=0x60, ancho_max=770, entrada="sutil", relleno=["#FFFFFF"], relleno_clave=["#FF3B30"],
                          numeros_clave=False, franjas=1, adelanto=0.03, llenar_hueco=0.35),
    "clasico": dict(fuentes=[("Arial Black", "ariblk.ttf")], tam=96, mayusculas=False, palabras=2, x=540, y=1475,
                    borde=8, sombra_y=3, color_sombra="#000000", alfa_sombra=0x64, ancho_max=980, entrada="encoge",
                    relleno=["#FFFFFF"], relleno_clave=["#FFD82A"], numeros_clave=False, franjas=1, adelanto=0.03,
                    llenar_hueco=0.3),
}
# Entradas (ms desde que aparece la palabra; a 30 fps 1 cuadro = 33 ms): [(desde, hasta, escala_final)], escala inicial
ENTRADAS = {
    "rebote": (48, [(0, 100, 120), (100, 233, 100)]),   # Custerk 10-12 nov: 48, 68, 93, 120, 113, 107, 102, 100
    "sutil": (94, [(0, 66, 100)]),                       # Custerk hasta el 9-nov: 94 -> 99 -> 100
    "encoge": (118, [(0, 90, 100)]),                     # el nuestro de antes
}
LIBASS = 0.72       # libass (PlayResY 1920) dibuja el texto a ~0,72 del ancho que mide PIL al mismo tamano (medido)
ALTO_MAYUS = 0.61   # alto de las mayusculas (relleno) / tamano de letra, Montserrat Black en libass (76 px a 124)

NUMEROS = set("""cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis
diecisiete dieciocho diecinueve veinte veintiuno veintiuna veintidos veintitres veinticuatro veinticinco veintiseis
veintisiete veintiocho veintinueve treinta cuarenta cincuenta sesenta setenta ochenta noventa cien ciento doscientos
trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos mil millon millones primero primera
segundo segunda tercero tercera mitad doble triple
two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen
twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million millions first second third half double
dois duas quatro sete oito dez onze doze treze quatorze catorze quinze dezesseis dezessete dezoito dezenove vinte trinta
quarenta cinquenta sessenta setenta oitenta cem duzentos trezentos milhao milhoes primeiro primeira metade dobro""".split())
# fuera a proposito: "one", "um", "uma" (en ingles y portugues tambien son articulos o pronombres)


def norm(w):
    w = unicodedata.normalize("NFKD", w.lower())
    return "".join(c for c in w if c.isalnum() and not unicodedata.combining(c))


def limpio(w):
    """palabra sin comillas ni signos (. , ! ¡ ? ¿ : ; …): los subtitulos van limpios. Conserva apostrofes y guiones
    internos para el doblaje (DON'T, I'M, INSCREVA-SE)."""
    w = re.sub(r"[^\w'’\-]", "", w)
    return w.strip("'’-")


def _hex_ass(h):
    """#RRGGBB -> &HBBGGRR& (los colores de ASS van al reves)"""
    h = h.lstrip("#")
    return "&H%s%s%s&" % (h[4:6], h[2:4], h[0:2])


def _mezcla(cols, t):
    """color en el punto t (0 = arriba, 1 = abajo) de un degradado de varios colores #RRGGBB"""
    if len(cols) == 1:
        return cols[0]
    t = min(1.0, max(0.0, t)) * (len(cols) - 1)
    i = min(int(t), len(cols) - 2)
    f = t - i
    a = [int(cols[i][k:k + 2], 16) for k in (1, 3, 5)]
    b = [int(cols[i + 1][k:k + 2], 16) for k in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(round(a[k] + (b[k] - a[k]) * f)) for k in range(3))


def buscar_fuente(archivo):
    for patron in BUSCAR:
        for d in sorted(glob.glob(patron), reverse=True):     # Roblox: la version mas nueva primero
            ruta = os.path.join(d, archivo)
            if os.path.isfile(ruta):
                return ruta
    return None


def fuente(estilo="custerk"):
    """(nombre para ASS, ruta del archivo) de la primera letra disponible del estilo"""
    for nombre, archivo in ESTILOS[estilo]["fuentes"]:
        ruta = buscar_fuente(archivo)
        if ruta:
            return nombre, ruta
    return ESTILOS[estilo]["fuentes"][-1][0], None


def _ancho(texto, ruta, tam, borde):
    """ancho en pixeles del video (1080) que va a ocupar el texto, contorno incluido"""
    try:
        from PIL import ImageFont
        return ImageFont.truetype(ruta, tam).getlength(texto) * LIBASS + 2 * borde
    except Exception:
        return len(texto) * tam * 0.56 + 2 * borde


def _ts(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return "%d:%02d:%05.2f" % (h, m, s)


def trozos_de(palabras, e, callar=()):
    out, actual = [], []
    for p in palabras:
        if p["w"] in callar or p.get("sfx"):          # marcas de efecto y onomatopeyas que hace el efecto: sin subtitulo
            continue
        if not limpio(p["texto"]):
            continue
        actual.append(p)
        corta = p["texto"][-1] in ",.:;!?\"»…" or p["texto"].endswith("...")
        if corta or len(actual) >= e["palabras"] or (p["t1"] - actual[0]["t0"]) > 0.65:
            out.append(actual); actual = []
    if actual:
        out.append(actual)
    return out


def _es_clave(w, clave, e):
    n = norm(w)
    return n in clave or (e["numeros_clave"] and (n in NUMEROS or n.isdigit()))


def armar(palabras, dur, clave=(), callar=(), estilo="custerk"):
    """devuelve (texto del .ass, eventos [[t0, t1, texto]]). clave = palabras (normalizadas) que van en color
    (en "custerk" tambien los numeros)."""
    e = ESTILOS[estilo]
    nombre_fuente, ruta_fuente = fuente(estilo)
    ruta_medir = ruta_fuente or os.path.join(FUENTES_WIN, "ariblk.ttf")
    clave = {norm(c) for c in clave}
    trozos = trozos_de(palabras, e, callar)
    eventos = [[tz[0]["t0"] - e["adelanto"], tz[-1]["t1"], [limpio(p["texto"]) for p in tz]] for tz in trozos]
    for k in range(len(eventos)):
        nxt = eventos[k + 1][0] if k + 1 < len(eventos) else dur
        eventos[k][1] = min(nxt, eventos[k][1] + 0.25)
        if nxt - eventos[k][1] < e["llenar_hueco"]:
            eventos[k][1] = nxt
    sombra = _hex_ass(e["color_sombra"])
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2",
           "ScaledBorderAndShadow: yes", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
           "MarginR, MarginV, Encoding",
           # Estilo base COMPATIBLE: Arial Black (siempre esta) abajo al centro, con el centro del texto a la misma altura,
           # para herramientas que copian este encabezado y escriben sus propias lineas sin pos ni fontsdir (el doblaje).
           # Nuestras lineas piden su letra, tamano y posicion por dentro (fn, fs, pos).
           "Style: Sub,Arial Black,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H%02X%s,-1,0,0,0,100,100,0,0,1,%d,0,2,40,40,%d,1"
           % (e["alfa_sombra"], sombra[2:-1], e["borde"], 1920 - e["y"] - 50),
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ini, pasos = ENTRADAS[e["entrada"]]
    salida = []
    for t0, t1, ws in eventos:
        vis = [w.upper() if e["mayusculas"] else w for w in ws]
        texto = " ".join(vis)
        fit = min(1.0, e["ancho_max"] / max(1.0, _ancho(texto, ruta_medir, e["tam"], e["borde"])))
        S = lambda p: int(round(p * fit))
        anim = "\\fscx%d\\fscy%d" % (S(ini), S(ini)) + "".join("\\t(%d,%d,\\fscx%d\\fscy%d)" % (a, b, S(s), S(s)) for a, b, s in pasos)
        es_clave = any(_es_clave(w, clave, e) for w in ws)
        cols = e["relleno_clave"] if es_clave else e["relleno"]
        pos = "\\an5\\pos(%d,%d)\\fn%s\\fs%d\\b0" % (e["x"], e["y"], nombre_fuente, e["tam"])
        ts0, ts1 = _ts(t0), _ts(t1)
        # capa 0: la palabra completa con contorno y sombra 3D, en el color de ABAJO del degradado
        base = "{%s\\bord%d\\xshad0\\yshad%d\\4c%s\\4a&H%02X&\\1c%s%s}" % (pos, e["borde"], e["sombra_y"], sombra,
                                                                         e["alfa_sombra"], _hex_ass(cols[-1]), anim)
        ass.append("Dialogue: 0,%s,%s,Sub,,0,0,0,,%s%s" % (ts0, ts1, base, texto))
        # capas 1..n: la misma palabra sin contorno, recortada cada vez mas arriba y mas clara = degradado suave
        n = e["franjas"] if len(cols) > 1 else 1
        alto = ALTO_MAYUS * e["tam"] * fit
        for k in range(1, n):
            corte = e["y"] + alto * (0.5 - k / float(n))           # de abajo hacia arriba
            col = _mezcla(cols, (n - 1 - k) / float(n - 1))
            capa = "{%s\\bord0\\shad0\\1c%s\\clip(0,0,1080,%d)%s}" % (pos, _hex_ass(col), int(round(corte)), anim)
            ass.append("Dialogue: %d,%s,%s,Sub,,0,0,0,,%s%s" % (k, ts0, ts1, capa, texto))
        salida.append([round(t0, 3), round(t1, 3), texto])
    return "\n".join(ass) + "\n", salida


def filtro(ass_nombre, carpeta, estilo="custerk"):
    """filtro de FFmpeg para quemar los subtitulos. Si la letra no es de Windows (Montserrat de Roblox/CapCut), la copia
    a <carpeta>/_fuentes y la pasa con fontsdir (ruta corta y relativa: correr FFmpeg desde <carpeta>)."""
    nombre, ruta = fuente(estilo)
    if ruta and os.path.dirname(ruta).lower() != FUENTES_WIN.lower():
        dest = os.path.join(carpeta, "_fuentes")
        os.makedirs(dest, exist_ok=True)
        if not os.path.exists(os.path.join(dest, os.path.basename(ruta))):
            shutil.copy2(ruta, dest)
        return "subtitles=%s:fontsdir=_fuentes" % ass_nombre
    return "subtitles=%s" % ass_nombre
