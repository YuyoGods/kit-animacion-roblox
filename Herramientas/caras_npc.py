# CARAS NUEVAS PARA PERSONAJES CON LA CARA CLASICA " : ) " (pedido del usuario: esa cara se ve antigua).
# Solo para los que la traen POR DEFECTO pegada en su textura (los de cara propia, como Mama, no se tocan).
# Borra la cara clasica de la textura (la pinta del color de su piel) y pega otra cara del Paquete_Roblox_HD en el
# mismo lugar y tamano. Hace varias variantes (su cara + expresiones) para cambiar de vez en cuando con caras_atlas.py.
#   py Herramientas/caras_npc.py <carpeta_personaje> <textura_cabeza.png> "Su Cara.png" "Risa.png" "Sorpresa.png" ...
#   -> <carpeta>/caras/atlas_0001.png (su cara), atlas_0002.png ... + caras.json  (en Blender: caras_atlas.preparar)
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HD = os.path.join(RAIZ, "Caras", "Paquete_Roblox_HD")
CLASICA = os.path.join(HD, "Classic Roblox Face.png")


def _caja_tinta(alfa_tinta, umbral=0.5):
    ys, xs = np.nonzero(alfa_tinta > umbral)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def tinta(im):
    """que tan 'tinta negra' es cada pixel (0..1)."""
    a = np.array(im.convert("RGBA")).astype(np.float32)
    return (a[..., 3] / 255.0) * np.clip(1 - a[..., :3].max(axis=2) / 110.0, 0, 1)


def buscar_cara(tex):
    """caja de la cara clasica en la textura: el bloque de piel mas grande con tinta negra adentro (ojos + boca)."""
    a = np.array(tex).astype(np.int32)
    t = tinta(tex)
    H, W = t.shape
    mejor = None
    for y0 in range(0, H - 120, 8):              # ventana del tamano de una cara, la que tenga ojos y boca en su lugar
        for x0 in range(0, W - 120, 8):
            for lado in (192, 256, 320):
                if y0 + lado > H or x0 + lado > W:
                    continue
                v = t[y0:y0 + lado, x0:x0 + lado]
                if v.max() < 0.5:
                    continue
                fil = (v > 0.5).mean(axis=1)
                ojos = fil[int(lado * .2):int(lado * .4)].mean(); boca = fil[int(lado * .55):int(lado * .8)].mean()
                borde = (v[:8].mean() + v[-8:].mean() + v[:, :8].mean() + v[:, -8:].mean())
                piel = a[y0:y0 + lado, x0:x0 + lado, :3]
                uni = piel.reshape(-1, 3).std(axis=0).mean()
                if ojos > 0.01 and boca > 0.01 and borde < 0.01:
                    s = ojos + boca - uni * 0.002
                    if mejor is None or s > mejor[0]:
                        mejor = (s, x0, y0, lado)
    return mejor


def hacer(carpeta, tex_png, caras, nombres=None):
    tex = Image.open(tex_png).convert("RGBA")
    W, H = tex.size
    t = tinta(tex)
    m = buscar_cara(tex)
    if m is None:
        raise SystemExit("No encontre la cara clasica en " + tex_png)
    _, x0, y0, lado = m
    # caja exacta de la tinta de la cara clasica en la textura y en la imagen original -> escala y posicion
    sub = np.zeros_like(t); sub[y0:y0 + lado, x0:x0 + lado] = t[y0:y0 + lado, x0:x0 + lado]
    tx0, ty0, tx1, ty1 = _caja_tinta(sub)
    cl = Image.open(CLASICA).convert("RGBA")
    cx0, cy0, cx1, cy1 = _caja_tinta(tinta(cl))
    sx = (tx1 - tx0) / (cx1 - cx0); sy = (ty1 - ty0) / (cy1 - cy0)
    ox = tx0 - cx0 * sx; oy = ty0 - cy0 * sy
    # piel: color mas comun del bloque sin tinta
    a = np.array(tex)
    blo = a[y0:y0 + lado, x0:x0 + lado].reshape(-1, 4)
    blo = blo[(t[y0:y0 + lado, x0:x0 + lado].reshape(-1) < 0.05) & (blo[:, 3] > 200)]
    vals, cnt = np.unique(blo[:, :3], axis=0, return_counts=True)
    piel = tuple(int(v) for v in vals[cnt.argmax()])
    # borrar la cara clasica (con un poquito de margen)
    mask = Image.fromarray(((sub > 0.15) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
    limpia = tex.copy()
    limpia.paste(Image.new("RGBA", tex.size, piel + (255,)), (0, 0), mask)
    os.makedirs(os.path.join(carpeta, "caras"), exist_ok=True)
    lista = []
    for i, c in enumerate(caras, 1):
        f = Image.open(c if os.path.isabs(c) else os.path.join(HD, c)).convert("RGBA")
        k = (cl.size[0] / f.size[0])
        f = f.resize((max(1, int(f.size[0] * k * sx)), max(1, int(f.size[1] * k * sy))), Image.LANCZOS)
        im = limpia.copy()
        capa = Image.new("RGBA", im.size, (0, 0, 0, 0)); capa.paste(f, (int(round(ox)), int(round(oy))))
        caja = Image.new("L", im.size, 0); caja.paste(255, (x0, y0, x0 + lado, y0 + lado))   # que no se salga del bloque de la cara
        capa.putalpha(Image.fromarray(np.minimum(np.array(capa.split()[3]), np.array(caja))))
        im.alpha_composite(capa)
        im.save(os.path.join(carpeta, "caras", "atlas_%04d.png" % i))
        lista.append({"n": i, "emocion": (nombres[i - 1] if nombres else os.path.splitext(os.path.basename(c))[0]), "archivo": os.path.basename(c)})
    json.dump({"_nota": "Caras nuevas (la clasica se veia antigua). Hecho con Herramientas/caras_npc.py desde " + os.path.basename(tex_png),
               "caras": lista}, open(os.path.join(carpeta, "caras", "caras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(os.path.basename(carpeta), "cara en", (x0, y0, lado), "piel", piel, "->", len(caras), "caras")


if __name__ == "__main__":
    hacer(sys.argv[1], sys.argv[2], sys.argv[3:])
