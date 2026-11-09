# Revisa la voz como lo haria una persona: la "oye" con Whisper y la mide, y avisa de los fallos tipicos de ElevenLabs
# (o de una grabacion propia), cada uno con el segundo exacto para escucharlo:
#   - palabra que no se oye, se oye distinta o cortada      - palabra o sonido DE MAS que no esta en el guion
#   - palabra poco clara (Whisper duda)                     - linea mas fuerte o mas suave que las demas
#   - linea atropellada o demasiado lenta, palabra estirada - sonido saturado (reventado)
#   py Herramientas/audio/revisar_voz.py EP###_Titulo [--idioma es]
# Lee audio/voz.wav + audio/voz_palabras.json (los deja recortar_pausas.py) y narracion.txt. Deja audio/revision_voz.json.
# recortar_pausas.py la corre sola al final. Lo que marque se escucha; si de verdad suena mal, se corrige esa linea en
# narracion.txt y se rehace sola: py Herramientas/audio/voz_elevenlabs.py EP###_Titulo --linea N
import argparse, difflib, json, os, re, subprocess, sys, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import episodio  # noqa: E402

SR, HOP = 48000, 0.01
_whisper = {}


def decodificar(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


def oir(audio16, idioma="es"):
    """Whisper escucha el audio (16 kHz) -> [{"texto", "t0", "t1", "p"}] (p = que tan seguro esta); None si no se puede."""
    try:
        import torch  # noqa: F401  (carga las librerias de CUDA que Whisper necesita para usar la tarjeta)
    except Exception:
        pass
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("  (no puedo escuchar la voz: falta faster-whisper; corre py instalar.py)")
        return None
    for disp, tipo in (("cuda", "float16"), ("cpu", "int8")):            # tarjeta de video; si falla, procesador
        if _whisper.get(disp) is False:
            continue
        try:
            if disp not in _whisper:
                _whisper[disp] = WhisperModel("large-v3-turbo", device=disp, compute_type=tipo)
            segs, _ = _whisper[disp].transcribe(audio16, language=idioma, word_timestamps=True,
                                                vad_filter=False, beam_size=5)
            return [{"texto": w.word.strip(), "t0": float(w.start), "t1": float(w.end), "p": float(w.probability)}
                    for s in segs for w in (s.words or []) if norm(w.word)]
        except Exception as e:
            print("  Whisper en %s no funciono (%s); probando otra forma..." % (disp, str(e)[:70]))
            _whisper[disp] = False
    return None


def fon(w):
    """como suena en espanol (para no marcar diferencias de pura escritura): Sikelpa = Siquelpa, Crista = Krista"""
    w = re.sub(r"c(?=[ei])", "s", w)
    for a, b in (("qu", "k"), ("c", "k"), ("z", "s"), ("v", "b"), ("ll", "y"), ("h", "")):
        w = w.replace(a, b)
    return w


def lev(x, y):
    fila = list(range(len(y) + 1))
    for i, cx in enumerate(x, 1):
        nueva = [i]
        for j, cy in enumerate(y, 1):
            nueva.append(min(fila[j] + 1, nueva[j - 1] + 1, fila[j - 1] + (cx != cy)))
        fila = nueva
    return fila[-1]


def juzgar(esperada, oida):
    esperada, oida = fon(esperada), fon(oida)
    if esperada == oida:
        return None
    if oida and esperada.startswith(oida) and len(esperada) - len(oida) >= 2:
        return "se corta el final"
    if oida and lev(esperada, oida) <= max(1, len(esperada) // 5):
        return None
    return "se oye distinto" if oida else "no se oye"


def silabas(w):
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", w.lower())))


def mmss(t):
    return "%d:%05.2f" % (int(t // 60), t % 60)


def revisar(ep, idioma="es", wav=None, palabras=None, imprimir=True):
    """revisa la voz del episodio; devuelve {"palabras_bien", "palabras_guion", "problemas": [...]} o None"""
    aud = os.path.join(ep, "audio")
    wav = wav or os.path.join(aud, "voz.wav")
    if palabras is None:
        palabras = json.load(open(os.path.join(aud, "voz_palabras.json"), encoding="utf-8"))["palabras"]
    txt = os.path.join(ep, "narracion.txt")
    lineas = ([l.strip() for l in open(txt, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]
              if os.path.exists(txt) else [])
    guion = [(norm(w), w, li) for li, l in enumerate(lineas) for w in l.split() if norm(w)]
    refp = guion if guion else [(norm(p["texto"]), p["texto"], None) for p in palabras]
    oidas = oir(decodificar(wav, 16000), idioma)
    if oidas is None:
        return None
    problemas = []

    def anotar(t, linea, tipo, detalle):
        problemas.append({"t": round(t, 2), "linea": linea, "tipo": tipo, "detalle": detalle})

    # 1) el guion contra lo que se oye
    refn, oin = [r[0] for r in refp], [norm(o["texto"]) for o in oidas]
    sm = difflib.SequenceMatcher(None, refn, oin, autojunk=False)
    bien, par = 0, {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        lin = lambda i: (refp[i][2] + 1) if i < len(refp) and refp[i][2] is not None else None  # noqa: E731
        t_de = lambda j: oidas[j]["t0"] if j < len(oidas) else (oidas[-1]["t1"] if oidas else 0.0)  # noqa: E731
        if tag == "equal":
            bien += i2 - i1
            par.update({i1 + k: j1 + k for k in range(i2 - i1)})
        elif tag == "insert":
            extra = [o for o in oidas[j1:j2] if len(norm(o["texto"])) >= 2]
            if extra:
                anotar(extra[0]["t0"], lin(i1) or lin(i1 - 1), "de mas",
                       'se oye "%s" y no esta en el guion' % " ".join(o["texto"] for o in extra))
        elif tag == "delete":
            for i in range(i1, i2):
                if len(refn[i]) >= 3:
                    anotar(t_de(j1), lin(i), "falta", 'no se oye "%s"' % refp[i][1])
                else:
                    bien += 1
        else:
            if "".join(map(fon, refn[i1:i2])) == "".join(map(fon, oin[j1:j2])):
                bien += i2 - i1
                if i2 - i1 == j2 - j1:
                    par.update({i1 + k: j1 + k for k in range(i2 - i1)})
            elif i2 - i1 == j2 - j1:
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    pr = juzgar(refn[i], oin[j])
                    if pr and len(refn[i]) >= 3:
                        anotar(oidas[j]["t0"], lin(i), "palabra", 'dice "%s" pero se oye "%s": %s'
                               % (refp[i][1], oidas[j]["texto"], pr))
                    else:
                        bien += 1
                        par[i] = j
            else:
                pr = juzgar("".join(refn[i1:i2]), "".join(oin[j1:j2]))
                if pr:
                    anotar(t_de(j1), lin(i1), "palabra", 'dice "%s" pero se oye "%s": %s'
                           % (" ".join(r[1] for r in refp[i1:i2]), " ".join(o["texto"] for o in oidas[j1:j2]), pr))
                else:
                    bien += i2 - i1
    # 2) palabras poco claras (Whisper las oyo, pero duda)
    for i, j in par.items():
        if len(refn[i]) >= 3 and oidas[j]["p"] < 0.40:
            anotar(oidas[j]["t0"], (refp[i][2] + 1) if refp[i][2] is not None else None, "poco clara",
                   '"%s" no se oye clara (seguridad %d %%)' % (refp[i][1], round(oidas[j]["p"] * 100)))

    # energia de la voz (cada 10 ms)
    voz = decodificar(wav, SR)
    h = int(HOP * SR)
    nfr = len(voz) // h
    rms = np.sqrt((voz[:nfr * h].reshape(nfr, h).astype(np.float64) ** 2).mean(axis=1))
    db = 20 * np.log10(rms / max(float(np.percentile(rms, 95)), 1e-9) + 1e-12)
    # 3) sonidos de mas: voz fuerte fuera de todas las palabras (ej. un "¡oh!" que ElevenLabs invento)
    cubierto = np.zeros(nfr, bool)
    for p in palabras:
        cubierto[max(0, int((p["t0"] - 0.08) / HOP)):min(nfr, int((p["t1"] + 0.12) / HOP) + 1)] = True
    fuera = (db > -30) & ~cubierto
    k = 0
    while k < nfr:
        if not fuera[k]:
            k += 1; continue
        k0 = k
        while k < nfr and fuera[k]:
            k += 1
        if (k - k0) * HOP >= 0.10:
            anotar(k0 * HOP, None, "sonido de mas", "sonido de %.2f s que no es ninguna palabra del guion" % ((k - k0) * HOP))

    # 4 y 5) cada linea: volumen y rapidez comparados con las demas
    if guion:
        pv = {}
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [g[0] for g in guion], [norm(p["texto"]) for p in palabras],
                                                           autojunk=False).get_opcodes():
            if tag in ("equal", "replace"):
                for j in range(j1, j2):
                    pv.setdefault(guion[i1 + min(i2 - i1 - 1, (j - j1) * (i2 - i1) // (j2 - j1))][2], []).append(palabras[j])
        datos = {}
        for li, ps in pv.items():
            t0, t1 = ps[0]["t0"], ps[-1]["t1"]
            if t1 - t0 < 0.3:
                continue
            seg = db[int(t0 / HOP):int(t1 / HOP) + 1]
            hablado = sum(max(0.05, p["t1"] - p["t0"]) for p in ps)       # sin contar las pausas dentro de la linea
            datos[li] = (t0, float(np.percentile(seg, 90)), sum(silabas(p["texto"]) for p in ps) / hablado, ps)
        if len(datos) >= 4:
            vol_med = float(np.median([d[1] for d in datos.values()]))
            vel_med = float(np.median([d[2] for d in datos.values()]))
            for li, (t0, vol, vel, ps) in sorted(datos.items()):
                if vol - vol_med > 3.5 or vol - vol_med < -4.5:
                    anotar(t0, li + 1, "volumen", "la linea suena %.0f dB %s que las demas"
                           % (abs(vol - vol_med), "mas fuerte" if vol > vol_med else "mas suave"))
                n_sil = sum(silabas(p["texto"]) for p in ps)
                if n_sil >= 8 and (vel > vel_med * 1.35 or vel < vel_med * 0.65):   # lineas muy cortas: drama, no se mide
                    anotar(t0, li + 1, "rapidez", "la linea va %s (%.1f silabas/s; lo normal aqui %.1f)"
                           % ("atropellada" if vel > vel_med else "muy lenta", vel, vel_med))
                for p in ps:                       # palabra estirada (ej. una vocal que ElevenLabs alarga de mas)
                    esperado = silabas(p["texto"]) / vel_med
                    if p["t1"] - p["t0"] > max(0.6, 2.2 * esperado):
                        anotar(p["t0"], li + 1, "estirada", '"%s" dura %.2f s (lo normal %.2f s)'
                               % (p["texto"], p["t1"] - p["t0"], esperado))
    # 6) saturacion
    sat = np.flatnonzero(np.abs(voz) > 0.995)
    if len(sat) > 50:
        anotar(sat[0] / SR, None, "saturada", "%d muestras reventadas (la voz esta demasiado fuerte)" % len(sat))

    problemas.sort(key=lambda x: x["t"])
    res = {"palabras_bien": bien, "palabras_guion": len(refp), "problemas": problemas}
    json.dump(res, open(os.path.join(aud, "revision_voz.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if imprimir:
        print("  Whisper oye bien %d de %d palabras del guion." % (bien, len(refp)))
        if not problemas:
            print("  Sin fallos: no hay palabras de mas, ni sonidos raros, ni lineas fuera de volumen o ritmo.")
        for pr in problemas:
            print("  ! %s  linea %-3s %-13s %s" % (mmss(pr["t"]), pr["linea"] or "-", pr["tipo"], pr["detalle"]))
        if problemas:
            print("  Escucha esos segundos. Si de verdad suena mal, corrige esa linea en narracion.txt (sin '...')")
            print("  y rehazla sola: py Herramientas/audio/voz_elevenlabs.py EP --linea N  (o vuelve a grabar esa parte).")
    return res


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Revisa la voz (Whisper + medidas) y marca los fallos con su segundo")
    ap.add_argument("ep")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()
    print("Revisando la voz de", a.ep, "...")
    if revisar(episodio(a.ep), a.idioma) is None:
        sys.exit("No pude escuchar la voz (falta Whisper)")
