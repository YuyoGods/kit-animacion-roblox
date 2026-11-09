# Hoja de fotogramas SUCESIVOS de un video (referencias de otros creadores o nuestras vistas previas), con el segundo
# y el numero de fotograma escritos en cada cuadro. Sirve para estudiar anticipacion, poses, cortes y particulas.
#   py Herramientas/fotogramas_ref.py VIDEO --desde 3.0 --hasta 5.0 --fps 15 [--ancho 200] [--cols 8] [--salida hoja.jpg]
#   --fps 0  = todos los fotogramas del tramo (cuadro por cuadro)
#   --recorte x0,y0,x1,y1 (fracciones 0-1) para acercar una zona (manos, cara)
# El nombre del video debe ser simple (sin emojis/acentos): OpenCV no abre esos nombres (lesson 27 de docs/02).
import argparse, os, sys
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--desde", type=float, default=0.0)
ap.add_argument("--hasta", type=float, default=None)
ap.add_argument("--fps", type=float, default=4.0)
ap.add_argument("--ancho", type=int, default=200)
ap.add_argument("--cols", type=int, default=8)
ap.add_argument("--recorte", default=None)
ap.add_argument("--salida", default=None)
a = ap.parse_args()

cap = cv2.VideoCapture(a.video)
if not cap.isOpened():
    sys.exit("No pude abrir el video: " + a.video)
fps_v = cap.get(cv2.CAP_PROP_FPS) or 30.0
n_tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
hasta = a.hasta if a.hasta is not None else n_tot / fps_v
f0, f1 = int(round(a.desde * fps_v)), min(n_tot - 1, int(round(hasta * fps_v)))
paso = 1 if a.fps <= 0 else max(1, int(round(fps_v / a.fps)))
quiero = set(range(f0, f1 + 1, paso))
cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
cuadros, f = [], f0
while f <= f1:
    ok, img = cap.read()
    if not ok:
        break
    if f in quiero:
        if a.recorte:
            x0, y0, x1, y1 = [float(v) for v in a.recorte.split(",")]
            h, w = img.shape[:2]
            img = img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
        h, w = img.shape[:2]
        img = cv2.resize(img, (a.ancho, int(h * a.ancho / w)), interpolation=cv2.INTER_AREA)
        txt = "%.2fs f%d" % (f / fps_v, f)
        cv2.rectangle(img, (0, 0), (len(txt) * 9 + 6, 18), (0, 0, 0), -1)
        cv2.putText(img, txt, (3, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1, cv2.LINE_AA)
        cuadros.append(img)
    f += 1
if not cuadros:
    sys.exit("Sin fotogramas en ese tramo")
h, w = cuadros[0].shape[:2]
cols = min(a.cols, len(cuadros))
filas = (len(cuadros) + cols - 1) // cols
hoja = np.zeros((filas * h, cols * w, 3), np.uint8)
for i, c in enumerate(cuadros):
    r, k = divmod(i, cols)
    hoja[r * h:r * h + c.shape[0], k * w:k * w + c.shape[1]] = c
sal = a.salida or os.path.splitext(a.video)[0] + "_hoja_%.1f-%.1f.jpg" % (a.desde, hasta)
os.makedirs(os.path.dirname(os.path.abspath(sal)), exist_ok=True)
cv2.imwrite(sal, hoja, [cv2.IMWRITE_JPEG_QUALITY, 88])
print("Hoja: %s (%d cuadros, %.1f fps del video, cada %d fotogramas)" % (sal, len(cuadros), fps_v, paso))
