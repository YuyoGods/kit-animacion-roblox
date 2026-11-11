# Arma la secuencia de caras que usa caras_textura.py (caras por emocion en la textura de la cabeza).
#   py Herramientas/armar_secuencia_caras.py [--agregar | --rehacer] [--sonrisa textura_del_personaje.png]
# Lee Caras/Emociones/*.png (fondo transparente, una emocion por archivo; orden alfabetico) y deja
#   Caras/Emociones/_secuencia/cara_0001.png ... (1024 px) + caras.json con el numero de cada cara.
# Nombres de las emociones (opcional): Caras/Emociones/nombres.json  {"Sad.png": "triste", ...}
# --sonrisa: agrega al final la cara de fabrica de un personaje clasico, sacada de su textura de Roblox
#   (el rectangulo de la cara), para que pueda volver a "su cara de siempre".
# Si la secuencia ya existe no la toca (los numeros ya usados en episodios cambiarian), salvo --rehacer.
# --agregar: pone AL FINAL (28, 29...) solo los PNG de Caras/Emociones que la secuencia todavia no tiene, sin cambiar
#   los numeros de las que ya estan. Si el dibujo de una cara nueva es mucho mas grande o chico que el de las demas
#   (otro tamano de imagen o de margen), lo iguala para que en la cabeza salga del mismo tamano.
import argparse, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RAIZ  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--rehacer", action="store_true")
ap.add_argument("--agregar", action="store_true", help="agrega al final las caras nuevas sin cambiar los numeros")
ap.add_argument("--sonrisa", help="textura (PNG) de un personaje clasico para sacar su cara de fabrica")
a = ap.parse_args()
src = os.path.join(RAIZ, "Caras", "Emociones")
out = os.path.join(src, "_secuencia")
if not os.path.isdir(src):
    os.makedirs(src); sys.exit("Pon tus caras (PNG con fondo transparente) en " + src + " y vuelve a correrlo")


def _caja(im):
    """caja del dibujo (alfa > 10) en fraccion del lienzo: (x0, y0, x1, y1)"""
    al = np.asarray(im.convert("RGBA"))[..., 3]
    ys, xs = np.nonzero(al > 10)
    h, w = al.shape
    return (xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h) if len(xs) else (0, 0, 1, 1)


if a.agregar:
    jp = os.path.join(out, "caras.json")
    d = json.load(open(jp, encoding="utf-8"))
    usados = {c["archivo"] for c in d["caras"]}
    nombres = json.load(open(os.path.join(src, "nombres.json"), encoding="utf-8")) if os.path.exists(os.path.join(src, "nombres.json")) else {}
    nuevos = sorted(f for f in os.listdir(src) if f.lower().endswith(".png") and f not in usados)
    # ajustes.json (opcional): {"Crying.png": 0.75} = escala fija del dibujo para esa cara (cuando el calculo
    # automatico se equivoca, ej. lagrimas a los lados que hacen ver la cara mas ancha de lo que es)
    ajustes = json.load(open(os.path.join(src, "ajustes.json"), encoding="utf-8")) if os.path.exists(os.path.join(src, "ajustes.json")) else {}
    if not nuevos:
        sys.exit("No hay caras nuevas en %s: la secuencia ya tiene todas (%d)" % (src, len(d["caras"])))
    ref = [_caja(Image.open(os.path.join(src, f))) for f in sorted(usados) if os.path.exists(os.path.join(src, f))]
    ancho_ref = float(np.median([c[2] - c[0] for c in ref])) if ref else 0.4
    alto_ref = float(np.median([c[3] - c[1] for c in ref])) if ref else 0.55
    cy_ref = float(np.median([(c[1] + c[3]) / 2 for c in ref])) if ref else 0.5
    n = max(c["n"] for c in d["caras"])
    for f in nuevos:
        im = Image.open(os.path.join(src, f)).convert("RGBA")
        x0, y0, x1, y1 = _caja(im)
        S = 1024
        k = 1.0 / max((x1 - x0) / ancho_ref, (y1 - y0) / alto_ref)   # la medida que mas se pasa (ancho o alto)
        if f in ajustes:
            k = float(ajustes[f])
        if f not in ajustes and 0.75 <= k <= 1.3:                        # tamano parecido a las demas: tal cual
            lienzo = im.resize((S, S), Image.LANCZOS); nota = ""
        else:                                       # igualar el tamano del dibujo (centrado como las demas)
            W, H = im.size
            rec = im.crop((round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H)))
            w2 = round((x1 - x0) * k * S); h2 = round((y1 - y0) * k * S)
            rec = rec.resize((max(1, w2), max(1, h2)), Image.LANCZOS)
            lienzo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            lienzo.paste(rec, (round(S / 2 - w2 / 2), round(cy_ref * S - h2 / 2)), rec)
            nota = " (dibujo igualado x%.2f)" % k
        n += 1
        lienzo.save(os.path.join(out, "cara_%04d.png" % n))
        d["caras"].append({"n": n, "archivo": f, "emocion": nombres.get(f, f[:-4])})
        print("  + %2d  %-22s %s%s" % (n, f, nombres.get(f, f[:-4]), nota))
    json.dump(d, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Secuencia: %d caras (las de antes conservan su numero)" % len(d["caras"]))
    sys.exit(0)
if os.path.exists(os.path.join(out, "caras.json")) and not a.rehacer:
    sys.exit("La secuencia ya existe (" + out + "). Para rehacerla: --rehacer (cambian los numeros de las caras); "
             "para sumar caras nuevas sin cambiar numeros: --agregar")
os.makedirs(out, exist_ok=True)
nombres = {}
if os.path.exists(os.path.join(src, "nombres.json")):
    nombres = json.load(open(os.path.join(src, "nombres.json"), encoding="utf-8"))
fs = sorted(f for f in os.listdir(src) if f.lower().endswith(".png"))
if not fs and not a.sonrisa:
    sys.exit("No hay PNG en " + src)
caras = []
for i, f in enumerate(fs, 1):
    Image.open(os.path.join(src, f)).convert("RGBA").resize((1024, 1024), Image.LANCZOS).save(os.path.join(out, "cara_%04d.png" % i))
    caras.append({"n": i, "archivo": f, "emocion": nombres.get(f, f[:-4])})
if a.sonrisa:
    # rectangulo de la cara en la textura de Roblox (cabeza clasica) = solo la parte plana del frente de la cabeza
    at = np.asarray(Image.open(a.sonrisa).convert("RGB")).astype(np.float32) / 255
    H, W = at.shape[:2]
    rect = at[int(round((1 - 0.481) * H)):int(round((1 - 0.040) * H)), int(round(0.186 * W)):int(round(0.382 * W))]
    piel = np.median(rect.reshape(-1, 3), axis=0)
    lum = rect @ np.array([0.299, 0.587, 0.114]); lp = piel @ np.array([0.299, 0.587, 0.114])
    alfa = np.clip((1 - lum / lp) * 1.25, 0, 1)
    rgba = np.zeros(rect.shape[:2] + (4,), np.uint8); rgba[..., 3] = (alfa * 255).astype(np.uint8)
    S = 1024
    lienzo = Image.new("RGBA", (S, S), (0, 0, 0, 0))     # a su tamano real dentro de la cara completa
    lienzo.paste(Image.fromarray(rgba).resize((round(0.85 / 1.2 * S), round(1.026 / 1.2 * S)), Image.LANCZOS),
                 (round(0.175 / 1.2 * S), round(0.084 / 1.2 * S)))
    n = len(caras) + 1
    lienzo.save(os.path.join(out, "cara_%04d.png" % n))
    caras.append({"n": n, "archivo": "(textura " + os.path.basename(a.sonrisa) + ")", "emocion": "su cara de siempre"})
json.dump({"secuencia": "cara_####.png (1024x1024, fondo transparente)", "caras": caras},
          open(os.path.join(out, "caras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("Secuencia lista: %d caras en %s" % (len(caras), out))
for c in caras:
    print("  %2d  %s" % (c["n"], c["emocion"]))
