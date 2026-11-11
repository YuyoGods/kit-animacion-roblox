# MUSICA DE FONDO del canal (pedido del usuario 2026-11-10): de principio a fin del video, debajo de la voz.
# - Se recorta al final del video con una salida suave (la cancion sobrante no deja pantalla negra); si es mas corta, se repite.
# - Nivel: MUSICA_FONDO_DB dB por debajo de la voz (RMS de las partes donde habla); mientras habla baja ~4 dB mas y
#   sube en los respiros. Se oye de fondo pero la voz manda.
# Uso (dentro de armar_video.py, antes de la MEZCLA):
#   import musica_fondo
#   mus = musica_fondo.pista(voz, DUR, SR, load)        # None si no hay musica en mi_config.json
#   mix = voz * db(-1.0) + fx * duck + (mus if mus is not None else 0)
import os
import numpy as np

from config import MUSICA_FONDO, MUSICA_FONDO_DB


def _media(x, k):
    """promedio movil rapido (suma acumulada): np.convolve con ventanas grandes tarda minutos en 2 minutos de audio"""
    c = np.cumsum(np.concatenate(([0.0], x.astype(np.float64))))
    i = np.arange(len(x))
    a, b = np.clip(i - k // 2, 0, len(x)), np.clip(i + k // 2 + 1, 0, len(x))
    return ((c[b] - c[a]) / np.maximum(1, b - a)).astype(np.float32)


def pista(voz, dur, sr, load, archivo=None, bajo_voz_db=None, duck_db=-4.0, entrada=0.4, salida=1.5):
    """arreglo del mismo largo que `voz` con la musica ya a su nivel, o None si no hay cancion"""
    archivo = archivo or MUSICA_FONDO
    if not archivo or not os.path.exists(archivo):
        if archivo:
            print("  (musica de fondo no encontrada: %s)" % archivo)
        return None
    bajo_voz_db = MUSICA_FONDO_DB if bajo_voz_db is None else bajo_voz_db
    m = load(archivo)
    largo = len(m) / sr
    n = min(len(voz), int(dur * sr))
    if len(m) < n:                                         # mas corta que el video: se repite
        m = np.tile(m, int(np.ceil(n / len(m))))
    m = m[:n].astype(np.float32).copy()
    a, b = min(n, int(entrada * sr)), min(n, int(salida * sr))
    m[:a] *= np.linspace(0, 1, a)
    m[n - b:] *= np.linspace(1, 0, b)                      # se corta junto con el video, con salida suave
    # nivel respecto a la voz (solo donde habla)
    env = _media(np.abs(voz[:n]), 2400)
    habla = env > 0.08 * (np.max(env) or 1)
    rms_v = np.sqrt(np.mean(voz[:n][habla] ** 2)) if habla.any() else 0.1
    rms_m = np.sqrt(np.mean(m ** 2)) or 1e-6
    m *= rms_v / rms_m * 10 ** (bajo_voz_db / 20.0)
    # baja un poco mientras habla y sube en los respiros (suave: 0,3 s)
    k = int(0.3 * sr)
    suave = _media(habla.astype(np.float32), k)
    m *= 1.0 - (1.0 - 10 ** (duck_db / 20.0)) * suave
    out = np.zeros(len(voz), np.float32)
    out[:n] = m
    print("  musica de fondo: %s (%.0f s de cancion, %.0f dB bajo la voz)" % (os.path.basename(archivo), largo, bajo_voz_db))
    return out
