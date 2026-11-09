# Texturas 2D de los efectos de vfx.py (se hacen con Python normal: Blender no trae PIL).
#   py Herramientas/blender/vfx_texturas/hacer_texturas.py
import os
from PIL import Image, ImageDraw, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
# sonrojo: mejilla rosa difuminada con rayitas ///
W, H = 512, 300
m = Image.new("L", (W, H), 0)
ImageDraw.Draw(m).ellipse((60, 50, W - 60, H - 50), fill=210)
m = m.filter(ImageFilter.GaussianBlur(38))
im = Image.new("RGBA", (W, H), (255, 105, 150, 0)); im.putalpha(m)
d = ImageDraw.Draw(im)
for i in range(3):
    x = 170 + i * 70
    d.line((x + 30, 95, x - 20, 205), fill=(215, 45, 100, 255), width=16)
im.save(os.path.join(AQUI, "sonrojo.png"))
print("ok: sonrojo.png")
