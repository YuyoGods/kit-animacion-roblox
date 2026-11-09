# Textura del billete de caricatura (para objetos_cartoon.billete). Correr con Python normal (Blender no trae PIL):
#   py Herramientas/blender/vfx_texturas/hacer_billete.py  -> vfx_texturas/billete.png
# Referencias (billetes de caricatura): fondo verde claro, marco verde oscuro con borde blanco, ovalo al centro con un
# retrato, el numero grande en las esquinas y el signo $; se tiene que reconocer como BILLETE aunque se vea chiquito.
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
W, H = 1200, 512
VERDE_OSC, VERDE, VERDE_CL, CREMA = (30, 92, 52), (74, 150, 88), (196, 228, 182), (236, 246, 226)


def fuente(tam):
    for f in ("arialbd.ttf", "ariblk.ttf"):
        try:
            return ImageFont.truetype(os.path.join(r"C:\Windows\Fonts", f), tam)
        except OSError:
            pass
    return ImageFont.load_default()


im = Image.new("RGB", (W, H), CREMA)
d = ImageDraw.Draw(im)
d.rectangle((0, 0, W - 1, H - 1), fill=VERDE_OSC)                       # marco
d.rectangle((14, 14, W - 15, H - 15), fill=CREMA)                       # borde blanco
d.rectangle((30, 30, W - 31, H - 31), fill=VERDE_CL)
for i in range(0, W, 18):                                               # guilloche (rayitas finas de billete)
    d.arc((i - 160, 40, i + 160, H - 40), 200, 340, fill=(170, 210, 160), width=2)
d.rectangle((0, 0, W - 1, 13), fill=VERDE_OSC); d.rectangle((0, H - 14, W - 1, H - 1), fill=VERDE_OSC)   # vuelve a tapar las orillas
d.rectangle((0, 0, 13, H - 1), fill=VERDE_OSC); d.rectangle((W - 14, 0, W - 1, H - 1), fill=VERDE_OSC)
for r in ((14, 14, W - 15, 29), (14, H - 30, W - 15, H - 15), (14, 14, 29, H - 15), (W - 30, 14, W - 15, H - 15)):
    d.rectangle(r, fill=CREMA)
d.rectangle((30, 30, W - 31, H - 31), outline=VERDE_OSC, width=6)
cx, cy = W // 2, H // 2                                                  # ovalo con retrato
d.ellipse((cx - 150, cy - 185, cx + 150, cy + 185), fill=CREMA, outline=VERDE_OSC, width=12)
d.ellipse((cx - 118, cy - 150, cx + 118, cy + 150), fill=(160, 205, 150))
d.rounded_rectangle((cx - 62, cy - 110, cx + 62, cy + 10), radius=26, fill=VERDE)          # cabeza de bloque (Roblox)
d.rounded_rectangle((cx - 100, cy + 22, cx + 100, cy + 150), radius=30, fill=VERDE)       # hombros
d.line((cx - 36, cy - 82, cx - 12, cy - 74), fill=VERDE_OSC, width=7); d.line((cx + 12, cy - 74, cx + 36, cy - 82), fill=VERDE_OSC, width=7)   # cejas
d.ellipse((cx - 30, cy - 68, cx - 14, cy - 46), fill=VERDE_OSC); d.ellipse((cx + 14, cy - 68, cx + 30, cy - 46), fill=VERDE_OSC)
d.arc((cx - 36, cy - 62, cx + 30, cy - 18), 15, 120, fill=VERDE_OSC, width=8)          # sonrisa de lado (no la clasica)
for (x, y) in ((110, 105), (W - 110, 105), (110, H - 105), (W - 110, H - 105)):      # numeros en las esquinas
    d.ellipse((x - 72, y - 72, x + 72, y + 72), fill=CREMA, outline=VERDE_OSC, width=8)
    d.text((x, y), "100", font=fuente(66), fill=VERDE_OSC, anchor="mm")
for x in (330, W - 330):                                                  # signo $ grande a los lados del ovalo
    d.text((x, cy + 6), "$", font=fuente(230), fill=VERDE, anchor="mm", stroke_width=6, stroke_fill=VERDE_OSC)
d.text((cx, 62), "BANCO DEL PUEBLO", font=fuente(40), fill=VERDE_OSC, anchor="mm")
d.text((cx, H - 60), "CIEN  PESOS", font=fuente(40), fill=VERDE_OSC, anchor="mm")
im = im.filter(ImageFilter.SMOOTH)
im.save(os.path.join(AQUI, "billete.png"))
print("billete.png", im.size)
