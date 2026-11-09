# CARTELES DE PANTALLA (contadores, avisos, preguntas al publico) con detalle de caricatura: papel con cinta, post-it,
# relojito, globo de dialogo, boton de suscribirse. Pedido del usuario: los carteles planos se veian feos; mas detalle
# pero ni futurista ni "de IA" (nada de brillos neon ni degradados raros: papel, contorno grueso, sombrita, iconos).
# Se corre con Python normal (Blender no trae PIL) y deja PNG con transparencia que el episodio pone frente a la camara.
#   py Herramientas/carteles.py <carpeta_salida> estilo "TEXTO|segundo renglon" [estilo "TEXTO"] ...
#   estilos: reloj (papel crema con cinta y reloj), postit (nota amarilla), postit_rojo, pregunta (globo de dialogo),
#            suscribete (boton rojo con campana)
import os, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FUENTES = r"C:\Windows\Fonts"
TINTA = (43, 33, 30, 255)


def fuente(tam, gruesa=True):
    for f in (("ariblk.ttf", "arialbd.ttf") if gruesa else ("arialbd.ttf",)):
        try:
            return ImageFont.truetype(os.path.join(FUENTES, f), tam)
        except OSError:
            pass
    return ImageFont.load_default()


def _texto(d, xy, txt, tam, color=TINTA, borde=None, ancho_borde=0, anchor="mm", ancho=None):
    """escribe el texto; si se pasa 'ancho', achica la letra hasta que quepa (nada se sale del cartel)"""
    while ancho and tam > 20 and d.textlength(txt, font=fuente(tam)) + 2 * ancho_borde > ancho:
        tam -= 4
    d.text(xy, txt, font=fuente(tam), fill=color, anchor=anchor, stroke_width=ancho_borde, stroke_fill=borde)


def _sombra(im, dx=10, dy=14, blur=10, alfa=90):
    a = im.split()[3]
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: v * alfa // 255))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base = Image.new("RGBA", (im.size[0] + dx + blur * 2, im.size[1] + dy + blur * 2), (0, 0, 0, 0))
    base.alpha_composite(sh, (dx + blur, dy + blur)); base.alpha_composite(im, (blur, blur))
    return base


def _papel(w, h, color, radio=26, borde=TINTA, grueso=9):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((grueso, grueso, w - grueso, h - grueso), radius=radio, fill=color, outline=borde, width=grueso)
    for i in range(18, h - 18, 34):                                      # textura suave de papel (renglones claritos)
        d.line((30, i, w - 30, i), fill=tuple(max(0, c - 10) for c in color[:3]) + (70,), width=2)
    return im, d


def _cinta(im, x, y, ang):
    t = Image.new("RGBA", (150, 46), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    d.rectangle((0, 0, 149, 45), fill=(235, 226, 200, 205))
    for i in range(0, 150, 12):                                          # orillas cortadas de la cinta
        d.polygon([(i, 0), (i + 6, 5), (i + 12, 0)], fill=(0, 0, 0, 0)); d.polygon([(i, 45), (i + 6, 40), (i + 12, 45)], fill=(0, 0, 0, 0))
    t = t.rotate(ang, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(t, (int(x - t.size[0] / 2), int(y - t.size[1] / 2)))


def _reloj(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 255), outline=TINTA, width=10)
    for k in range(12):
        a = math.radians(k * 30)
        r1 = r * (0.72 if k % 3 == 0 else 0.8)
        d.line((cx + r1 * math.sin(a), cy - r1 * math.cos(a), cx + r * 0.88 * math.sin(a), cy - r * 0.88 * math.cos(a)), fill=TINTA, width=5)
    d.line((cx, cy, cx, cy - r * 0.62), fill=TINTA, width=9); d.line((cx, cy, cx + r * 0.45, cy + r * 0.15), fill=(216, 40, 70, 255), width=8)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=TINTA)
    d.rectangle((cx - 16, cy - r - 22, cx + 16, cy - r - 4), fill=TINTA)                       # perilla de despertador


def reloj(lineas):
    w, h = 1100, 430
    im, d = _papel(w, h, (255, 248, 226, 255))
    _reloj(d, 215, h // 2 + 6, 125)
    if len(lineas) > 1:
        _texto(d, (690, 140), lineas[0], 76, ancho=620)
        _texto(d, (690, 275), lineas[1], 128, color=(216, 40, 70, 255), borde=TINTA, ancho_borde=6, ancho=620)
    else:
        _texto(d, (690, h // 2), lineas[0], 110, color=(216, 40, 70, 255), borde=TINTA, ancho_borde=6, ancho=620)
    _cinta(im, 160, 22, 12); _cinta(im, w - 160, 22, -9)
    return im.rotate(-3, expand=True, resample=Image.BICUBIC)


def postit(lineas, color=(255, 228, 92, 255), tinta=TINTA, icono="?"):
    w, h = 900, 520 if len(lineas) > 1 else 420
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(10, 10), (w - 10, 10), (w - 10, h - 90), (w - 90, h - 10), (10, h - 10)], fill=color, outline=TINTA)
    d.line([(10, 10), (w - 10, 10), (w - 10, h - 90), (w - 90, h - 10), (10, h - 10), (10, 10)], fill=TINTA, width=9)
    d.polygon([(w - 10, h - 90), (w - 90, h - 90), (w - 90, h - 10)], fill=tuple(int(c * 0.82) for c in color[:3]) + (255,), outline=TINTA)
    d.line([(w - 10, h - 90), (w - 90, h - 90), (w - 90, h - 10)], fill=TINTA, width=7)       # esquina doblada
    d.rectangle((10, 10, w - 10, 70), fill=tuple(int(c * 0.93) for c in color[:3]) + (255,)); d.line((10, 70, w - 10, 70), fill=TINTA, width=4)
    d.line([(10, 10), (w - 10, 10)], fill=TINTA, width=9)
    if icono:
        d.ellipse((40, 100, 160, 220), fill=(255, 255, 255, 255), outline=TINTA, width=8)
        _texto(d, (100, 162), icono, 88, color=(216, 40, 70, 255))
    x0, an = (530, 640) if icono else (w // 2, w - 120)
    if len(lineas) > 1:
        _texto(d, (x0, 200), lineas[0], 130, color=tinta, ancho=an)
        _texto(d, (x0, 350), lineas[1], 100, color=tinta, ancho=an)
    else:
        _texto(d, (x0, h // 2 + 30), lineas[0], 140, color=tinta, ancho=an)
    _cinta(im, w // 2, 18, 3)
    return im.rotate(4, expand=True, resample=Image.BICUBIC)


def pregunta(lineas):
    w, h = 1150, 470
    im = Image.new("RGBA", (w, h + 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, w - 10, h), radius=70, fill=(255, 255, 255, 255), outline=TINTA, width=10)
    d.polygon([(200, h - 8), (300, h - 8), (170, h + 80)], fill=(255, 255, 255, 255))
    d.line([(200, h - 4), (170, h + 80), (300, h - 4)], fill=TINTA, width=10)
    y0 = h // 2 - (len(lineas) - 1) * 62
    for i, l in enumerate(lineas):
        _texto(d, (w // 2, y0 + i * 124), l, 92, color=(216, 40, 70, 255) if i == len(lineas) - 1 else TINTA, ancho=w - 120)
    for (x, y) in ((70, 70), (w - 70, h - 60)):                         # puntitos de comentario
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, 212, 0, 255), outline=TINTA, width=4)
    return im


def suscribete(lineas):
    w, h = 1000, 300
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 26, w - 10, h - 10), radius=60, fill=(150, 18, 30, 255))                 # sombra del boton (relieve)
    d.rounded_rectangle((10, 10, w - 10, h - 34), radius=60, fill=(230, 33, 41, 255), outline=TINTA, width=10)
    d.rounded_rectangle((40, 30, w - 40, 90), radius=30, fill=(255, 255, 255, 60))                     # brillito de plastico
    cx, cy = 140, (h - 24) // 2                                                                        # campana
    d.pieslice((cx - 62, cy - 70, cx + 62, cy + 54), 180, 360, fill=(255, 212, 0, 255), outline=TINTA, width=7)
    d.rectangle((cx - 62, cy - 8, cx + 62, cy + 30), fill=(255, 212, 0, 255)); d.line((cx - 62, cy - 8, cx - 62, cy + 30), fill=TINTA, width=7)
    d.line((cx + 62, cy - 8, cx + 62, cy + 30), fill=TINTA, width=7)
    d.rounded_rectangle((cx - 80, cy + 26, cx + 80, cy + 46), radius=10, fill=(255, 212, 0, 255), outline=TINTA, width=7)
    d.ellipse((cx - 16, cy + 44, cx + 16, cy + 74), fill=(255, 212, 0, 255), outline=TINTA, width=6)
    _texto(d, (605, cy), lineas[0], 112, color=(255, 255, 255, 255), borde=TINTA, ancho_borde=7, ancho=720)
    return im


ESTILOS = {"reloj": reloj, "postit": postit, "pregunta": pregunta, "suscribete": suscribete,
           "postit_rojo": lambda l: postit(l, color=(255, 140, 160, 255), icono="X"),
           "postit_plan": lambda l: postit(l, icono="!")}


def hacer(carpeta, estilo, texto, nombre=None):
    lineas = texto.split("|")
    im = _sombra(ESTILOS[estilo](lineas))
    os.makedirs(carpeta, exist_ok=True)
    nombre = nombre or "".join(c if c.isalnum() else "_" for c in (estilo + "_" + texto))[:60]
    ruta = os.path.join(carpeta, nombre + ".png")
    im.save(ruta)
    return ruta


if __name__ == "__main__":
    out = sys.argv[1]
    a = sys.argv[2:]
    for estilo, texto in zip(a[0::2], a[1::2]):
        print(hacer(out, estilo, texto))
