# Junta las fotos de hoja_contacto.py en una sola imagen: una fila por toma (inicio / mitad / fin) con su etiqueta.
#   py Herramientas/componer_hoja.py carpeta salida.jpg [tomas_por_renglon=2]
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

carp, salida = sys.argv[1], sys.argv[2]
ncol = int(sys.argv[3]) if len(sys.argv) > 3 else 2
idx = json.load(open(os.path.join(carp, "indice.json"), encoding="utf-8"))
ims = {f: Image.open(os.path.join(carp, f)).convert("RGB") for t in idx for f, _ in t["fotos"]}
w, h = next(iter(ims.values())).size
pad, lab = 6, 28
cel = 3 * w + 2 * pad
filas = (len(idx) + ncol - 1) // ncol
W = ncol * cel + (ncol + 1) * pad * 3
H = filas * (h + lab + pad * 2) + pad
hoja = Image.new("RGB", (W, H), (25, 25, 30))
dr = ImageDraw.Draw(hoja)
try:
    font = ImageFont.truetype("arialbd.ttf", 18)
except Exception:
    font = ImageFont.load_default()
for k, t in enumerate(idx):
    c, r = k % ncol, k // ncol
    x0 = pad * 3 + c * (cel + pad * 3)
    y0 = pad + r * (h + lab + pad * 2)
    dr.text((x0, y0 + 4), "%d  %s   (fotogramas %d-%d)" % (t["toma"], t["nombre"], t["desde"], t["hasta"]), fill=(255, 220, 90), font=font)
    for j, (f, fr) in enumerate(t["fotos"]):
        hoja.paste(ims[f], (x0 + j * (w + pad), y0 + lab))
hoja.save(salida, quality=88)
print("hoja", salida, hoja.size)
