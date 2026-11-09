# Genera texturas de TELA y PAPEL TAPIZ que se repiten sin costura (1024 px) para cobijas, cojines y paredes.
#   py -X utf8 Herramientas/texturas_tela.py          -> Herramientas/blender/texturas/*.png
# Estampados: estrellas (rosa, azul con lunas), corazones (coral), gatitas kawaii ORIGINALES (lila, rosa).
# Las gatitas son un diseno propio (boquita ":3", cachetes, sin mono de marca): no usar personajes con dueno
# (Hello Kitty, etc.) en videos de YouTube.
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

TAM = 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender", "texturas")
TINTA = (52, 38, 48, 255)


def _hex(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def estrella(d, cx, cy, r, color, ri=0.45, rot=0.0, borde=None):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * ri
        a = rot + math.pi * i / 5 - math.pi / 2
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color, outline=borde)


def corazon(d, cx, cy, r, color, borde=None, ancho=0):
    pts = []
    for i in range(40):
        t = 2 * math.pi * i / 40
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * r / 16, cy + (y - 2.5) * r / 16))
    d.polygon(pts, fill=color)
    if borde:
        d.line(pts + [pts[0]], fill=borde, width=ancho)


def luna(d, cx, cy, r, color, fondo):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    d.ellipse((cx - r * 0.45, cy - r * 1.05, cx + r * 1.35, cy + r * 0.75), fill=fondo)


def gatita(d, cx, cy, r, cara=(255, 255, 255, 255), oreja=(255, 170, 200, 255), cachete=(255, 150, 185, 255)):
    """carita de gatita kawaii original: cabeza ovalada, orejas, ojos de punto, naricita, boca :3, cachetes."""
    w = max(2, int(r * 0.09))
    for s in (-1, 1):                                                        # orejas
        e = [(cx + s * r * 0.95, cy - r * 0.15), (cx + s * r * 0.78, cy - r * 1.05), (cx + s * r * 0.2, cy - r * 0.62)]
        d.polygon(e, fill=cara, outline=TINTA)
        d.line(e + [e[0]], fill=TINTA, width=w)
        ei = [(cx + s * r * 0.8, cy - r * 0.32), (cx + s * r * 0.74, cy - r * 0.82), (cx + s * r * 0.38, cy - r * 0.58)]
        d.polygon(ei, fill=oreja)
    d.ellipse((cx - r, cy - r * 0.72, cx + r, cy + r * 0.72), fill=cara, outline=TINTA, width=w)
    for s in (-1, 1):
        d.ellipse((cx + s * r * 0.42 - r * 0.09, cy - r * 0.12, cx + s * r * 0.42 + r * 0.09, cy + r * 0.1), fill=TINTA)
        d.ellipse((cx + s * r * 0.62 - r * 0.15, cy + r * 0.16, cx + s * r * 0.62 + r * 0.15, cy + r * 0.34), fill=cachete)
        for k in (-1, 1):                                                    # bigotes
            d.line((cx + s * r * 0.82, cy + r * 0.08 + k * r * 0.1, cx + s * r * 1.18, cy + r * 0.02 + k * r * 0.2), fill=TINTA, width=max(1, w // 2))
    d.ellipse((cx - r * 0.08, cy + r * 0.08, cx + r * 0.08, cy + r * 0.2), fill=(255, 120, 160, 255))
    for s in (-1, 1):                                                        # boca :3
        d.arc((cx + (s - 1) * r * 0.11, cy + r * 0.14, cx + (s + 1) * r * 0.11, cy + r * 0.36), 0, 180, fill=TINTA, width=max(1, w // 2 + 1))


def _tile(fn, x, y, margen):
    """dibuja en (x, y) y en las copias del otro lado para que la textura se repita sin costura."""
    for dx in (-TAM, 0, TAM):
        for dy in (-TAM, 0, TAM):
            if -margen < x + dx < TAM + margen and -margen < y + dy < TAM + margen:
                fn(x + dx, y + dy)


def _rejilla(n, semilla, mueve=0.32):
    rnd = random.Random(semilla)
    paso = TAM / n
    pts = []
    for i in range(n):
        for j in range(n):
            off = paso / 2 if i % 2 else 0
            pts.append(((j * paso + off + rnd.uniform(-mueve, mueve) * paso) % TAM, i * paso + paso / 2 + rnd.uniform(-mueve, mueve) * paso, rnd))
    return pts


def _grano(im, fuerza=5, semilla=1):
    """grano de tela muy suave (pixel a pixel, se repite sin costura)."""
    rnd = random.Random(semilla)
    ruido = Image.effect_noise((TAM, TAM), 40).convert("L")
    ruido = ruido.point(lambda v: 128 + (v - 128) * fuerza // 40)
    base = im.convert("RGB")
    r, g, b = base.split()
    from PIL import ImageChops
    out = Image.merge("RGB", [ImageChops.add(c, ruido, 1, -128) for c in (r, g, b)])
    return out


def estampado(nombre, fondo, motivos, n=6, semilla=3, grano=4):
    im = Image.new("RGBA", (TAM, TAM), _hex(fondo))
    d = ImageDraw.Draw(im)
    for k, (x, y, rnd) in enumerate(_rejilla(n, semilla)):
        fn = motivos[k % len(motivos)]
        _tile(lambda X, Y: fn(d, X, Y, rnd), x, y, 140)
    # puntitos de relleno entre motivos
    for x, y, rnd in _rejilla(n * 2, semilla + 7, 0.45):
        if rnd.random() < 0.45:
            _tile(lambda X, Y: d.ellipse((X - 5, Y - 5, X + 5, Y + 5), fill=(255, 255, 255, 150)), x, y, 10)
    im = im.filter(ImageFilter.SMOOTH)
    out = _grano(im, grano, semilla)
    os.makedirs(OUT, exist_ok=True)
    ruta = os.path.join(OUT, nombre + ".png")
    out.save(ruta)
    print("textura", ruta)
    return ruta


def _guardar(im, nombre, grano=3, semilla=1):
    out = _grano(im, grano, semilla)
    os.makedirs(OUT, exist_ok=True)
    ruta = os.path.join(OUT, nombre + ".png")
    out.save(ruta)
    print("textura", ruta)
    return ruta


def cuadritos(nombre, color, fondo="#ffffff", periodo=128):
    """mantel de cuadritos (vichy): franjas al 50 % que se cruzan; se repite sin costura (periodo divide 1024)."""
    import numpy as np
    c, b = np.array(_hex(color)[:3], float), np.array(_hex(fondo)[:3], float)
    y, x = np.mgrid[0:TAM, 0:TAM]
    v = ((x % periodo) < periodo // 2).astype(float)
    h = ((y % periodo) < periodo // 2).astype(float)
    k = (v + h) / 2.0
    img = b[None, None, :] * (1 - k[..., None]) + c[None, None, :] * k[..., None]
    return _guardar(Image.fromarray(img.astype("uint8")), nombre)


def rombos(nombre, colores=("#2f4f8f", "#f3e6cf", "#d9774a", "#f3e6cf"), periodo=256):
    """tapete de rombos (tipo kilim): aros de rombo alrededor de cada centro; se repite sin costura."""
    import numpy as np
    y, x = np.mgrid[0:TAM, 0:TAM]
    d = np.abs((x % periodo) - periodo / 2) + np.abs((y % periodo) - periodo / 2)
    banda = (d // (periodo / 8)).astype(int) % len(colores)
    pal = np.array([_hex(c)[:3] for c in colores], float)
    img = pal[banda]
    return _guardar(Image.fromarray(img.astype("uint8")), nombre)


def rayas(nombre, colores=("#efe3cf", "#efe3cf", "#c9a77c", "#efe3cf", "#8a6a4a"), periodo=128):
    """tapete de rayas horizontales de distintos anchos; se repite sin costura."""
    import numpy as np
    y, x = np.mgrid[0:TAM, 0:TAM]
    anchos = [5, 3, 1, 2, 1][:len(colores)]
    tot = sum(anchos)
    pos = ((y % periodo) / periodo * tot)
    lim = np.cumsum(anchos)
    banda = np.searchsorted(lim, pos, side="right").clip(0, len(colores) - 1)
    pal = np.array([_hex(c)[:3] for c in colores], float)
    return _guardar(Image.fromarray(pal[banda].astype("uint8")), nombre)


def main():
    rosa = "#f6a9c9"
    estampado("tela_estrellas_rosa", rosa, [
        lambda d, x, y, r: estrella(d, x, y, 46, _hex("#ffffff"), rot=r.uniform(-0.4, 0.4)),
        lambda d, x, y, r: estrella(d, x, y, 26, _hex("#ffe07a"), rot=r.uniform(-0.4, 0.4)),
        lambda d, x, y, r: corazon(d, x, y, 24, _hex("#ff6fa5")),
    ], n=6, semilla=3)
    azul = "#34539e"
    estampado("tela_estrellas_azul", azul, [
        lambda d, x, y, r: estrella(d, x, y, 44, _hex("#ffd84a"), rot=r.uniform(-0.4, 0.4)),
        lambda d, x, y, r: luna(d, x, y, 34, _hex("#fff1b0"), _hex(azul)),
        lambda d, x, y, r: estrella(d, x, y, 20, _hex("#ffffff"), rot=r.uniform(-0.4, 0.4)),
    ], n=6, semilla=5)
    coral = "#ff9cb4"
    estampado("tela_corazones_coral", coral, [
        lambda d, x, y, r: corazon(d, x, y, 40, _hex("#ffffff")),
        lambda d, x, y, r: corazon(d, x, y, 22, _hex("#d94f7c")),
    ], n=6, semilla=8)
    lila = "#d9c2f0"
    estampado("tela_gatitas_lila", lila, [
        lambda d, x, y, r: gatita(d, x, y, 60),
        lambda d, x, y, r: corazon(d, x, y, 26, _hex("#ff8fb8")),
        lambda d, x, y, r: estrella(d, x, y, 22, _hex("#ffffff"), rot=r.uniform(-0.4, 0.4)),
    ], n=5, semilla=11)
    estampado("papel_gatitas_rosa", "#f9c9dc", [
        lambda d, x, y, r: gatita(d, x, y, 52),
        lambda d, x, y, r: corazon(d, x, y, 22, _hex("#ffffff")),
        lambda d, x, y, r: estrella(d, x, y, 18, _hex("#ffffff"), rot=r.uniform(-0.4, 0.4)),
    ], n=4, semilla=13, grano=2)
    cuadritos("mantel_cuadros_rojo", "#d9433a")
    cuadritos("mantel_cuadros_azul", "#3f6cc0")
    rombos("tapete_rombos_azul")
    rayas("tapete_rayas_beige")


if __name__ == "__main__":
    main()
