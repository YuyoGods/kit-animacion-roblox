# BOCAS PARA HABLAR (lip-sync sencillo, estilo caricatura): 5 bocas sobre una cara clasica y un calculo de que boca
# va en cada fotograma segun el volumen de la voz (no es realista a proposito: abre y cierra con el ritmo de la voz).
#   py Herramientas/bocas_hablar.py hacer                        -> agrega las caras 21-25 a Caras/Emociones/_secuencia
#   py Herramientas/bocas_hablar.py calcular voz.wav [desde hasta] -> bocas.json: una boca por fotograma (30 fps)
# OJO: los rigs viejos traen la propiedad "cara" con tope 20 -> rig.id_properties_ui("cara").update(max=30) o no salen.
# Prueba completa (personaje hablando a camara): Herramientas/blender/prueba_habla.py
# Caras: 21 casi cerrada -> 25 muy abierta: SIEMPRE la misma boca, solo cambia cuanto se abre (pedido del usuario). Ojos y cejas FIJOS (de fuente_bocas/risa_base.png):
# solo cambia la boca, como en la referencia del usuario (estilo creadores de Shorts de Roblox).  En Blender: rig["cara"] = numero.
import json, os, sys, wave
import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEQ = os.path.join(RAIZ, "Caras", "Emociones", "_secuencia")
BOCAS = {21: "hablar: casi cerrada", 22: "hablar: poco abierta", 23: "hablar: media", 24: "hablar: abierta", 25: "hablar: muy abierta (la risa completa)"}


def hacer(base_png=None):
    """Bocas desde UNA cara dibujada (ojos y cejas fijos, como en la referencia del usuario): solo se abre/cierra su
    propia sonrisa. Por columna: la banda de arriba (labio) se queda y la de abajo se acerca segun lo abierta."""
    from PIL import Image
    base_png = base_png or os.path.join(RAIZ, "Caras", "Emociones", "fuente_bocas", "risa_base.png")
    im = Image.open(base_png).convert("RGBA").resize((1024, 1024), Image.LANCZOS)
    a = np.array(im)
    alfa = a[..., 3].astype(np.float32) / 255.0
    alfa = alfa * (1.0 - a[..., :3].mean(axis=2) / 255.0)       # solo la tinta negra (el blanco de adentro aparte)
    Y0 = 540                                                   # arriba de esto: ojos y cejas (no se tocan)
    ojos = a.copy(); ojos[Y0:] = 0
    boca = alfa.copy(); boca[:Y0] = 0
    cx = int(np.mean(np.nonzero(boca > 0.5)[1]))

    def abrir(k, ancho=1.0, solo_labio=False):
        out = np.zeros_like(boca); dentro = np.zeros_like(boca)
        for x in range(1024):
            col = boca[:, x]
            on = np.nonzero(col > 0.5)[0]
            if len(on) == 0:
                continue
            runs = np.split(on, np.nonzero(np.diff(on) > 1)[0] + 1)
            top = runs[0]; t0, t1 = top[0], top[-1] + 1
            out[t0:t1, x] = col[t0:t1]
            if solo_labio:
                continue
            if len(runs) == 1:                                 # costado vertical de la boca: se acorta
                grosor = 14
                largo = int(grosor + k * max(0, (t1 - t0) - grosor))
                out[t0:t1, x] = 0; out[t0:t0 + largo, x] = col[t0:t0 + largo]
                continue
            bot = runs[-1]; b0, b1 = bot[0], bot[-1] + 1
            nb0 = int(round(t1 + k * (b0 - t1)))
            dentro[t1:nb0, x] = 1.0                           # adentro de la boca: blanco, como el dibujo
            out[nb0:nb0 + (b1 - b0), x] = np.maximum(out[nb0:nb0 + (b1 - b0), x], col[b0:b1])
        if ancho != 1.0:                                       # mas angosta (la "o")
            def angosta(m):
                src = Image.fromarray((m * 255).astype(np.uint8)).resize((int(1024 * ancho), 1024), Image.LANCZOS)
                lien = Image.new("L", (1024, 1024), 0); lien.paste(src, (cx - int(cx * ancho), 0))
                return np.array(lien).astype(np.float32) / 255.0
            out, dentro = angosta(out), angosta(dentro)
        from PIL import ImageFilter                            # suaviza las esquinas (sin picos al cerrar)
        lim = Image.fromarray((out * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
        lim = lim.filter(ImageFilter.GaussianBlur(1.2))
        out = np.clip((np.array(lim).astype(np.float32) / 255.0 - 0.5) * 2.2 + 0.5, 0, 1)
        dentro = dentro * (out < 0.5)
        return out, dentro

    formas = {21: abrir(0.1), 22: abrir(0.32), 23: abrir(0.55), 24: abrir(0.78), 25: abrir(1.0)}   # LA MISMA boca, solo mas o menos abierta
    for n, (m, w) in formas.items():
        res = ojos.copy()
        res[..., :3][w > 0.02] = 255
        res[..., 3] = np.maximum(res[..., 3], (w * 255).astype(np.uint8))
        res[..., :3][m > 0.02] = (res[..., :3][m > 0.02] * (1 - m[m > 0.02, None])).astype(np.uint8)
        res[..., 3] = np.maximum(res[..., 3], (m * 255).astype(np.uint8))
        Image.fromarray(res).save(os.path.join(SEQ, "cara_%04d.png" % n))
    ruta = os.path.join(SEQ, "caras.json")
    d = json.load(open(ruta, encoding="utf-8"))
    d["caras"] = [c for c in d["caras"] if c["n"] not in BOCAS] + [{"n": n, "archivo": "Herramientas/bocas_hablar.py (desde fuente_bocas/risa_base.png)", "emocion": e} for n, e in BOCAS.items()]
    json.dump(d, open(ruta, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("bocas 21-25 listas en", SEQ)


def calcular(wav, desde=0.0, hasta=None, fps=30):
    w = wave.open(wav); sr = w.getframerate(); ch = w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    x = x[int(desde * sr): int(hasta * sr) if hasta else None] / 32768.0
    paso = sr // fps
    rms, zcr = [], []
    for i in range(0, len(x) - paso, paso):
        s = x[i:i + paso]
        rms.append(float(np.sqrt(np.mean(s * s)))); zcr.append(float(np.mean(np.abs(np.diff(np.sign(s)))) / 2))
    rms = np.array(rms); top = np.percentile(rms, 95) or 1.0
    v = rms / top
    bocas, prev, quieta = [], 21, 0
    for i, a in enumerate(v):
        meta = 21 + int(np.searchsorted([0.12, 0.3, 0.5, 0.72], a))     # que tan abierta segun el volumen
        if quieta < 2:                                # aguanta al menos 2 fotogramas
            b = prev
        else:
            b = prev + max(-2, min(2, meta - prev))   # abre y cierra de a poco (sin saltos de cerrada a abierta)
        quieta = quieta + 1 if b == prev else 0
        bocas.append(b); prev = b
    return bocas


if __name__ == "__main__":
    if sys.argv[1] == "hacer":
        hacer(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        wav = sys.argv[2]; a = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0; b = float(sys.argv[4]) if len(sys.argv) > 4 else None
        bocas = calcular(wav, a, b)
        json.dump({"fps": 30, "bocas": bocas}, open("bocas.json", "w"), indent=0)
        print("bocas.json: %d fotogramas" % len(bocas), {k: bocas.count(k) for k in BOCAS})
