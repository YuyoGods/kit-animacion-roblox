# MIRADA DE LADO: crea variantes de una cara (PNG con fondo transparente) con los OJOS corridos hacia un lado, para
# contar "miré X" como Custerk (5lSYLwGZSYE 13,75 s: primer plano con los ojos dibujados hacia un lado -> corte a lo
# que ve). Solo mueve los ojos (las manchas de la mitad de arriba); la boca y lo demas se quedan.
#   py Herramientas/mirada_lateral.py CARA.png SALIDA_CARPETA [--px 70] [--alto 0]
# No sirve con ojos cerrados (^^): no hay mirada que mover.
# Escribe <nombre>_izq.png y <nombre>_der.png ("izq" = a la izquierda de la PANTALLA, o sea a la derecha del personaje).
import argparse, os
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("cara"); ap.add_argument("salida")
ap.add_argument("--px", type=int, default=70, help="cuanto se corren los ojos (en una cara de 1024 px)")
ap.add_argument("--alto", type=int, default=0, help="subir (+) o bajar (-) los ojos")
a = ap.parse_args()
im = cv2.imread(a.cara, cv2.IMREAD_UNCHANGED)
if im is None or im.shape[2] != 4:
    raise SystemExit("La cara debe ser PNG con transparencia: " + a.cara)
H, W = im.shape[:2]
alfa = (im[:, :, 3] > 40).astype(np.uint8)
n, lab, st, cen = cv2.connectedComponentsWithStats(alfa, 8)
# ojos: manchas cuyo centro esta en la mitad de arriba de lo dibujado y que no son enormes
ys = np.where(alfa.any(axis=1))[0]
y_mitad = ys.min() + 0.55 * (ys.max() - ys.min()) if len(ys) else H / 2
ojos = [i for i in range(1, n) if cen[i][1] < y_mitad and st[i][4] > 0.0004 * H * W and st[i][4] < 0.08 * H * W]
mask = np.isin(lab, ojos).astype(np.uint8)
# incluir el borde suavizado (alfa bajo) alrededor de cada ojo: si no, queda un 'fantasma' del ojo en su lugar
mask = (cv2.dilate(mask, np.ones((7, 7), np.uint8)) > 0) & (im[:, :, 3] > 0)
os.makedirs(a.salida, exist_ok=True)
base = os.path.splitext(os.path.basename(a.cara))[0]
for nombre, dx in (("izq", -a.px), ("der", a.px)):
    out = im.copy()
    out[mask] = 0                                          # borra los ojos
    M = np.float32([[1, 0, dx], [0, 1, -a.alto]])
    ojos_img = np.zeros_like(im); ojos_img[mask] = im[mask]
    mov = cv2.warpAffine(ojos_img, M, (W, H), flags=cv2.INTER_NEAREST, borderValue=(0, 0, 0, 0))
    m2 = mov[:, :, 3] > 0
    out[m2] = mov[m2]
    cv2.imwrite(os.path.join(a.salida, "%s_%s.png" % (base, nombre)), out)
print("ojos encontrados: %d manchas -> %s_izq.png / %s_der.png en %s" % (len(ojos), base, base, a.salida))
