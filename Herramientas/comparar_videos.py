# Compara dos versiones del MISMO recorrido (antes/despues) cuadro a cuadro: diferencia media y "parpadeo"
# (cambio brusco de un cuadro al siguiente que no tiene la otra version). Sirve para z-fighting, efectos y velocidad
# de exportacion (perdida de calidad). Imprime por cuadro y un resumen; con --hoja guarda los cuadros mas distintos.
#   py Herramientas/comparar_videos.py A.mp4 B.mp4 [--recorte x0,y0,x1,y1] [--hoja salida.jpg]
import argparse
import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b")
ap.add_argument("--recorte", default=None)
ap.add_argument("--hoja", default=None)
a = ap.parse_args()


def cuadros(ruta):
    cap = cv2.VideoCapture(ruta)
    while True:
        ok, im = cap.read()
        if not ok:
            break
        if a.recorte:
            x0, y0, x1, y1 = [float(v) for v in a.recorte.split(",")]
            h, w = im.shape[:2]
            im = im[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
        yield im.astype(np.float32)


A, B = list(cuadros(a.a)), list(cuadros(a.b))
n = min(len(A), len(B))
dif = [float(np.abs(A[i] - B[i]).mean()) for i in range(n)]
# parpadeo: cuanto cambia cada version de un cuadro al siguiente (la camara se mueve igual en las dos)
pa = [float(np.abs(A[i] - A[i - 1]).mean()) for i in range(1, n)]
pb = [float(np.abs(B[i] - B[i - 1]).mean()) for i in range(1, n)]
psnr = []
for i in range(n):
    mse = float(((A[i] - B[i]) ** 2).mean())
    psnr.append(99.0 if mse < 1e-9 else 10 * np.log10(255.0 ** 2 / mse))
print("cuadros: %d" % n)
print("diferencia media A-B: %.2f (max %.2f en el cuadro %d)" % (np.mean(dif), max(dif), int(np.argmax(dif)) + 1))
print("PSNR medio: %.1f dB (min %.1f) — arriba de ~38 dB no se nota a simple vista" % (np.mean(psnr), min(psnr)))
print("cambio cuadro a cuadro A: %.2f   B: %.2f   (si A >> B, A parpadea)" % (np.mean(pa), np.mean(pb)))
if a.hoja:
    peores = sorted(range(n), key=lambda i: -dif[i])[:6]
    filas = []
    for i in sorted(peores):
        h = 300
        ia = cv2.resize(A[i].astype(np.uint8), (int(A[i].shape[1] * h / A[i].shape[0]), h))
        ib = cv2.resize(B[i].astype(np.uint8), (ia.shape[1], h))
        d = np.clip(np.abs(A[i] - B[i]) * 4, 0, 255).astype(np.uint8)
        idf = cv2.resize(d, (ia.shape[1], h))
        fila = np.hstack([ia, ib, idf])
        cv2.putText(fila, "cuadro %d" % (i + 1), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        filas.append(fila)
    cv2.imwrite(a.hoja, np.vstack(filas), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("hoja (A | B | diferencia x4):", a.hoja)
