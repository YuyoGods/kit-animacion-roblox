# Recorta las pausas de la voz para que suene de corrido, con un respiro corto entre frases, SIN cortar nunca la voz.
# Sirve para cualquier voz (ElevenLabs o una voz propia). Como trabaja:
#   1) Mide la energia del audio cada 10 ms y solo quita SILENCIO REAL: nunca un pedazo de palabra ni el final suave
#      de una palabra. Cada corte queda dentro del silencio y lejos de la voz (lo comprueba antes de guardar).
#   2) Deja pausas cortas y naturales (segundos):
#        entre palabras ............... hasta --max (0,2)
#        despues de coma .............. hasta --coma (0,3)
#        fin de linea y . ! ? : ....... de 0,3 a --respiro (0,4)     <- un respiro corto entre tomas
#        despues de "..." ............. de 0,41 a --suspenso (0,55)
#      Si la voz dice dos lineas pegadas pero baja casi a silencio entre ellas, ahi mete el respiro.
#      Las pausas mas largas se acortan y las muy cortas de fin de frase se alargan un poco con su mismo silencio.
#      La velocidad de la voz NO cambia.
#   3) Volumen parejo: si una linea suena mucho mas suave o fuerte que las demas, la acerca (queda +-2 dB).
#   4) Revisa la voz con revisar_voz.py: la "oye" con Whisper, la compara con narracion.txt y la mide; avisa con su
#      segundo si una palabra no se oye completa, hay algo de mas, una linea va atropellada, etc.
#   py Herramientas/audio/recortar_pausas.py EP###_Titulo [--audio su_voz.mp3] [--max 0.2] [--coma 0.3]
#                                             [--respiro 0.4] [--suspenso 0.55] [--sin_oir]
# Entrada: audio/narracion.mp3 + audio/narracion_tiempos.json (ElevenLabs), o --audio <archivo> (voz propia: los
#          tiempos de cada palabra salen de Whisper; la primera vez descarga el modelo).
# Salida: audio/voz.wav (la usa el video), audio/voz_escuchar.mp3 (para escucharla) y audio/voz_palabras.json
#         (cada palabra con su tiempo en la voz recortada + la revision).
# Despues: py Herramientas/audio/tomas_desde_voz.py EP###_Titulo
import argparse, difflib, json, os, re, subprocess, sys, unicodedata
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import episodio  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revisar_voz import oir, revisar  # noqa: E402

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
ap = argparse.ArgumentParser(description="Recorta pausas sin cortar la voz y revisa que se oiga completa")
ap.add_argument("ep")
ap.add_argument("--audio", help="voz propia (cualquier formato); si no, audio/narracion.mp3 de ElevenLabs")
ap.add_argument("--max", type=float, default=0.20, help="pausa maxima entre palabras (s)")
ap.add_argument("--coma", type=float, default=0.30, help="pausa maxima despues de coma (s)")
ap.add_argument("--respiro", type=float, default=0.40, help="pausa al final de linea o frase (s); minimo el 75%%")
ap.add_argument("--suspenso", "--max_suspenso", dest="suspenso", type=float, default=0.55,
                help="pausa despues de '...' (s); minimo el 75%%")
ap.add_argument("--sin_oir", action="store_true", help="no revisar la voz con Whisper al final")
ap.add_argument("--detalle", action="store_true", help="mostrar cada pausa (entre que palabras, antes y ahora)")
ap.add_argument("--sin_nivelar", action="store_true", help="no emparejar el volumen de las lineas")
ap.add_argument("--idioma", default="es")
a = ap.parse_args()
EP = episodio(a.ep)
AUD = os.path.join(EP, "audio")
SR, HOP = 48000, 0.01
MARGEN = 0.06          # silencio que queda siempre pegado a la voz a cada lado de un corte (s)
if a.audio and not os.path.exists(a.audio) and os.path.exists(os.path.join(AUD, a.audio)):
    a.audio = os.path.join(AUD, a.audio)          # --audio su_voz.mp3 puesto dentro de EP###/audio/
src = a.audio or os.path.join(AUD, "narracion.mp3")
if not os.path.exists(src):
    sys.exit("No encuentro la voz: " + src)


def decodificar(path, sr):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return "".join(c for c in w if c.isalnum() and unicodedata.category(c) != "Mn")


# ---- voz y palabras (t0 = primer sonido de la palabra, t1 = ultimo sonido; sin contar la puntuacion)
voz = decodificar(src, SR)
dur = len(voz) / SR
palabras = []
tiempos = os.path.join(AUD, "narracion_tiempos.json")
if not a.audio and os.path.exists(tiempos):
    fuente = "elevenlabs"
    al = json.load(open(tiempos, encoding="utf-8"))
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    i = 0
    while i < len(ch):
        if ch[i].isspace():
            i += 1; continue
        j = i
        while j < len(ch) and not ch[j].isspace():
            j += 1
        letras = [k for k in range(i, j) if ch[k].isalnum()]
        if letras:
            palabras.append({"texto": "".join(ch[i:j]), "t0": st[letras[0]], "t1": en[letras[-1]]})
        i = j
else:
    fuente = "whisper"
    print("Whisper esta sacando el tiempo de cada palabra...")
    palabras = oir(decodificar(src, 16000), a.idioma) or []
if not palabras:
    sys.exit("No encontre palabras en la voz")

# ---- guion: a que linea de narracion.txt pertenece cada palabra (fin de linea = cambio de toma -> respiro)
txt = os.path.join(EP, "narracion.txt")
lineas = ([l.strip() for l in open(txt, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]
          if os.path.exists(txt) else [])
guion = [(norm(w), w, li) for li, l in enumerate(lineas) for w in l.split() if norm(w)]


def emparejar(ref, otras):
    """para cada palabra de 'otras', el indice de su palabra en 'ref' (tolera palabras mal dichas u oidas)"""
    sm = difflib.SequenceMatcher(None, ref, otras, autojunk=False)
    par = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("equal", "replace"):
            for j in range(j1, j2):
                par[j] = i1 + min(i2 - i1 - 1, (j - j1) * (i2 - i1) // (j2 - j1))
    return sm, par


linea_de = {}
if guion:
    _, par = emparejar([g[0] for g in guion], [norm(p["texto"]) for p in palabras])
    linea_de = {j: guion[i][2] for j, i in par.items()}
ultima = {}
for j, li in linea_de.items():
    ultima[li] = max(ultima.get(li, -1), j)
fin_linea = {j: li for li, j in ultima.items() if li < len(lineas) - 1}

# ---- energia cada 10 ms: que es voz y que es silencio de verdad
h = int(HOP * SR)
nfr = len(voz) // h
rms = np.sqrt((voz[:nfr * h].reshape(nfr, h).astype(np.float64) ** 2).mean(axis=1))
ref = max(float(np.percentile(rms, 95)), 1e-9)
db = 20 * np.log10(rms / ref + 1e-12)
UMBRAL = float(min(-35.0, max(-55.0, np.percentile(db, 5) + 10)))   # debajo de esto = silencio (dB bajo la voz)
sonido = db >= UMBRAL
if not sonido.any():
    sys.exit("La voz parece vacia (no hay sonido)")
k_ini = int(np.argmax(sonido))
k_fin = nfr - int(np.argmax(sonido[::-1]))
voz_ini, voz_fin = k_ini * HOP, k_fin * HOP
silencios = []
k = k_ini
while k < k_fin:
    if sonido[k]:
        k += 1; continue
    k0 = k
    while k < k_fin and not sonido[k]:
        k += 1
    if (k - k0) * HOP >= 0.06:
        silencios.append((k0 * HOP, k * HOP))


def tipo_pausa(j):
    t = palabras[j]["texto"].rstrip()
    k = len(t)
    while k > 0 and not t[k - 1].isalnum():
        k -= 1
    cola = t[k:]
    if "..." in cola or "…" in cola:
        return "suspenso"
    if j in fin_linea or any(c in cola for c in ".!?:"):
        return "respiro"
    if any(c in cola for c in ",;"):
        return "coma"
    return "palabra"


LIMITES = {"palabra": (0.0, a.max), "coma": (0.0, a.coma), "respiro": (0.75 * a.respiro, a.respiro),
           "suspenso": (0.75 * a.suspenso, a.suspenso), "final": (0.0, 0.40)}

# ---- cada silencio pertenece al hueco entre dos palabras (si hay un respiro en medio quedan 2 silencios en el hueco)
fronteras = np.array([(p["t1"] + q["t0"]) / 2 for p, q in zip(palabras, palabras[1:])])
grupos = {}
for r0, r1 in silencios:
    c = (r0 + r1) / 2
    if c > palabras[-1]["t1"] + 0.05:
        grupos.setdefault("final", []).append((r0, r1)); continue
    if (r1 - r0) < 0.25 and any(p["t0"] + 0.03 < c < p["t1"] - 0.03 for p in palabras):
        continue                  # silencio corto dentro de una palabra (ej. antes de una "p" o "t"): no se toca
    if not len(fronteras) or c < palabras[0]["t0"] - 0.05:
        continue
    j = int(np.argmin(np.abs(fronteras - c)))
    grupos.setdefault(j, []).append((r0, r1))

ediciones = []        # (q0, q1, extra, silencio): quitar [q0, q1) de la voz original y poner 'extra' s de silencio
cambios = []          # (hueco, tipo, antes, despues) para el resumen
for j, rs in grupos.items():
    tipo = "final" if j == "final" else tipo_pausa(j)
    lo, hi = LIMITES[tipo]
    total = sum(r1 - r0 for r0, r1 in rs)
    despues = total
    if total > hi:
        despues = 0.0
        for r0, r1 in rs:           # se reparte lo que queda entre los silencios del hueco
            L = r1 - r0
            queda = min(L, max(2 * MARGEN, L * hi / total))
            if L - queda > 0.02:
                q0 = r0 + queda / 2
                ediciones.append((q0, q0 + (L - queda), 0.0, None))
                despues += queda
            else:
                despues += L
    elif total < lo and len(rs) == 1 and lo - total >= 0.03:
        r0, r1 = rs[0]
        c = (r0 + r1) / 2
        ediciones.append((c, c, lo - total, (r0, r1)))
        despues = lo
    cambios.append((j, tipo, total, despues))
# fin de linea SIN silencio: si la voz baja casi a silencio entre las dos palabras (valle), ahi se mete el respiro
VALLE = -35.0                       # dB bajo la voz: tan bajo que una pausa ahi suena natural (no corta nada)
tono = max(silencios, key=lambda r: r[1] - r[0]) if silencios else None     # silencio de la grabacion (ruido de fondo)
valles = {}
for j in fin_linea:
    if j in grupos or j + 1 >= len(palabras):
        continue
    k0 = max(0, int((palabras[j]["t1"] - 0.06) / HOP))
    k1 = min(nfr, int((palabras[j + 1]["t0"] + 0.06) / HOP) + 1)
    if k1 <= k0:
        continue
    km = k0 + int(np.argmin(db[k0:k1]))
    lo = LIMITES[tipo_pausa(j)][0]
    if db[km] < VALLE and lo > 0:
        valles[j] = (km + 0.5) * HOP
        ediciones.append((valles[j], valles[j], lo, tono))
        cambios.append((j, tipo_pausa(j), 0.0, lo))
if voz_ini > 0.10:
    ediciones.append((0.0, voz_ini - 0.10, 0.0, None))
if dur - voz_fin > 0.40:
    ediciones.append((voz_fin + 0.40, dur, 0.0, None))
ediciones.sort(key=lambda e: e[0])


# ---- seguridad: ningun corte puede tocar la voz (se revisa con la energia real antes de guardar)
def hay_sonido(t0, t1):
    k0, k1 = max(0, int(t0 / HOP)), min(nfr, int(np.ceil(t1 / HOP)))
    return bool(sonido[k0:k1].any())


malos = [e for e in ediciones if e[1] > e[0] and hay_sonido(e[0] - 0.05, e[1] + 0.05)]
if malos:
    print("  OJO: %d cortes tocaban la voz y NO se hicieron" % len(malos))
    ediciones = [e for e in ediciones if e not in malos]
n_cortes = sum(1 for e in ediciones if e[1] > e[0])


# ---- armar la voz nueva (los fundidos caen en silencio; los tiempos se calculan con lo que de verdad queda)
def silencio_de(seg, run):
    if run is None:
        return np.zeros(int(seg * SR), dtype=np.float32)
    r0, r1 = run
    L = r1 - r0
    m = voz[int((r0 + L * 0.25) * SR):int((r1 - L * 0.25) * SR)]
    n = int(seg * SR)
    if len(m) < 32:
        return np.zeros(n, dtype=np.float32)
    rep = int(np.ceil(n / len(m))) + 1
    return np.concatenate([m if i % 2 == 0 else m[::-1] for i in range(rep)])[:n].astype(np.float32)


partes, pos = [], 0.0
for q0, q1, extra, run in ediciones:
    if q0 > pos:
        partes.append(("v", pos, q0))
    if extra > 0:
        partes.append(("s", extra, run))
    pos = max(pos, q1)
if pos < dur:
    partes.append(("v", pos, dur))
NF = int(0.008 * SR)
trozos, largo, mapa = [], 0, []      # mapa: (inicio_original, fin_original, inicio_nuevo) en segundos
for tipo, x, y in partes:
    d = voz[int(round(x * SR)):int(round(y * SR))].copy() if tipo == "v" else silencio_de(x, y)
    if trozos and len(trozos[-1]) > NF and len(d) > NF:
        w = np.linspace(0, 1, NF, dtype=np.float32)
        trozos[-1][-NF:] = trozos[-1][-NF:] * np.sqrt(1 - w) + d[:NF] * np.sqrt(w)
        ini = largo - NF
        d = d[NF:]
    else:
        ini = largo
    if tipo == "v":
        mapa.append((x, y, ini / SR))
    trozos.append(d)
    largo += len(d)
salida = np.concatenate(trozos) if trozos else voz


def nuevo_t(t):
    """tiempo en la voz original -> tiempo en la voz recortada"""
    for s0, s1, o0 in mapa:
        if t < s0:
            return o0               # cae en un silencio quitado: va al inicio del siguiente pedazo
        if t < s1:
            return o0 + (t - s0)
    s0, s1, o0 = mapa[-1]
    return o0 + (s1 - s0)


for r0, r1 in silencios:             # una palabra empieza donde acaba el silencio y termina donde empieza
    for p in palabras:
        if r0 < p["t0"] < r1:
            p["t0"] = r1
        if r0 < p["t1"] < r1:
            p["t1"] = r0
for j, c in valles.items():          # respiro metido en un valle: la palabra siguiente empieza despues de el
    palabras[j + 1]["t0"] = max(palabras[j + 1]["t0"], c)
    palabras[j]["t1"] = min(palabras[j]["t1"], c)
for p in palabras:
    p["t0"], p["t1"] = round(nuevo_t(p["t0"]), 3), round(nuevo_t(p["t1"]), 3)
    p["w"] = norm(p["texto"])

# ---- volumen parejo: ElevenLabs a veces dice una linea mucho mas suave (o fuerte) que las demas
TOLERANCIA = 2.5                     # dB que una linea puede variar sin tocarla (la emocion se respeta)
niveladas = []
if not a.sin_nivelar:
    porlinea = {}
    for j, p in enumerate(palabras):
        if j in linea_de:
            porlinea.setdefault(linea_de[j], []).append(p)
    hh = int(HOP * SR)

    def nivel_db(t0, t1):
        seg = salida[int(t0 * SR):int(t1 * SR)]
        m = len(seg) // hh
        if m < 5:
            return None
        r = np.sqrt((seg[:m * hh].reshape(m, hh).astype(np.float64) ** 2).mean(axis=1))
        return 20 * np.log10(np.percentile(r, 90) + 1e-12)

    niv = {li: nivel_db(ps[0]["t0"], ps[-1]["t1"]) for li, ps in porlinea.items()}
    niv = {li: v for li, v in niv.items() if v is not None}
    if len(niv) >= 3:
        med = float(np.median(list(niv.values())))
        orden = sorted(porlinea)
        curva = np.ones(len(salida), np.float32)
        for k_, li in enumerate(orden):
            d = niv.get(li, med) - med
            if abs(d) <= TOLERANCIA + 0.5:   # cambios de menos de medio dB no valen la pena
                continue
            cambio = float(np.clip(-(d - np.sign(d) * TOLERANCIA), -8, 8))
            ps = porlinea[li]
            ini = (porlinea[orden[k_ - 1]][-1]["t1"] + ps[0]["t0"]) / 2 if k_ > 0 else 0.0
            fin = (ps[-1]["t1"] + porlinea[orden[k_ + 1]][0]["t0"]) / 2 if k_ + 1 < len(orden) else len(salida) / SR
            curva[int(ini * SR):int(fin * SR)] = 10 ** (cambio / 20)
            niveladas.append((li + 1, cambio))
        if niveladas:                     # cambios suaves (40 ms) que caen en la pausa entre lineas
            k_ = int(0.04 * SR)
            c_ = np.cumsum(np.concatenate([[0.0], curva.astype(np.float64)]))
            idx = np.arange(len(curva))
            lo_, hi_ = np.clip(idx - k_ // 2, 0, len(curva)), np.clip(idx + k_ // 2 + 1, 0, len(curva))
            salida = (salida * ((c_[hi_] - c_[lo_]) / (hi_ - lo_))).astype(np.float32)
            pico = float(np.abs(salida).max())
            if pico > 0.98:
                salida *= 0.98 / pico         # nunca saturar

wav = os.path.join(AUD, "voz.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le",
                wav], input=salida.astype(np.float32).tobytes(), check=True)
mp3 = os.path.join(AUD, "voz_escuchar.mp3")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k", mp3], check=True)
dur_nueva = len(salida) / SR
print("Voz lista (%s): %.2f s -> %.2f s | %d palabras (%.1f por segundo)"
      % (fuente, dur, dur_nueva, len(palabras), len(palabras) / max(0.1, palabras[-1]["t1"] - palabras[0]["t0"])))
print("  Ningun corte toca la voz: %d cortes, todos en silencio real (a %.2f s o mas de la voz)" % (n_cortes, MARGEN))
acort = sum(1 for c in cambios if c[3] < c[2] - 0.005)
alarg = sum(1 for c in cambios if c[3] > c[2] + 0.005)
print("  Pausas: %d acortadas, %d alargadas (respiros), %d se quedan igual" % (acort, alarg, len(cambios) - acort - alarg))
resp = ["%d:%.2f>%.2f" % (fin_linea[j] + 1, an, de)
        for j, t, an, de in sorted((c for c in cambios if c[0] in fin_linea), key=lambda c: fin_linea[c[0]])]
if resp:
    print("  Respiro al final de cada linea (linea:antes>ahora, s): " + "  ".join(resp))
if valles:
    print("  Respiro metido donde la voz baja casi a silencio (no tenia pausa): lineas %s"
          % ", ".join(str(fin_linea[j] + 1) for j in sorted(valles, key=lambda x: fin_linea[x])))
sin_silencio = [li + 1 for j, li in sorted(fin_linea.items(), key=lambda x: x[1]) if j not in grupos and j not in valles]
if sin_silencio:
    print("  Lineas que la voz dice pegadas (se dejan asi para no cortar voz): %s"
          % ", ".join(str(x) for x in sin_silencio))
if niveladas:
    print("  Volumen parejo (lineas que sonaban muy suaves o fuertes): "
          + "  ".join("linea %d %+.1f dB" % (li, cb) for li, cb in niveladas))
if a.detalle:
    for j, tipo, an, de in sorted(cambios, key=lambda c: (c[0] == "final", c[0] if c[0] != "final" else 0)):
        entre = "fin" if j == "final" else "%s | %s" % (palabras[j]["texto"], palabras[j + 1]["texto"])
        print("    %-34s %-9s %.2f > %.2f s" % (entre, tipo, an, de))

# ---- revision: la voz se escucha con Whisper y se mide (revisar_voz.py)
revision = None
if not a.sin_oir:
    print("Revisando la voz (Whisper + medidas)...")
    revision = revisar(EP, a.idioma, wav, palabras)
json.dump({"fuente": fuente, "audio_original": os.path.basename(src), "duracion": round(dur_nueva, 3),
           "recortado_s": round(dur - dur_nueva, 3), "umbral_silencio_db": round(UMBRAL, 1),
           "pausas": {"max": a.max, "coma": a.coma, "respiro": a.respiro, "suspenso": a.suspenso},
           "revision": revision, "palabras": palabras},
          open(os.path.join(AUD, "voz_palabras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("  ->", wav, "| para escucharla:", mp3)
