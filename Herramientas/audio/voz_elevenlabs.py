# Genera la narracion con ElevenLabs (con tiempos por letra para sincronizar subtitulos).
# Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt] [--voz ID_DE_VOZ] [--velocidad X] [--linea N [--simular|--reusar]]
#                                                                            [--agregar [--respuesta archivo.json]]
#   Lee el texto de EP###/narracion.txt (lineas con # se ignoran) y guarda en EP###/audio/:
#   narracion.mp3 + narracion_tiempos.json + narracion_info.json (voz y ajustes con que se hizo).
#   Si ya habia una voz, la anterior se guarda en Respaldos/ (nada se pierde) y se usa la misma voz del episodio.
#   --voz: probar otra voz sin cambiar "voz_narrador" de mi_config.json.
#   --velocidad: 0.7 a 1.2. NO usarla salvo que el usuario lo pida: la voz va a velocidad normal (1.0);
#                acelerada pierde la esencia del personaje.
#   --linea N (o N-M): rehace SOLO la linea N (o las lineas N a M, si la voz las dice pegadas) de narracion.txt (ej. una palabra que no se oye completa) y la pega en la voz
#              que ya existe, con la misma voz y ajustes (ElevenLabs recibe las lineas de antes y despues para que
#              suene igual). Gasta solo los creditos de esa linea. Despues: recortar_pausas.py otra vez.
#   --simular: con --linea, prueba el pegado sin llamar a ElevenLabs (no gasta creditos; escribe *_simulada.*).
#   --reusar: con --linea, vuelve a pegar la ultima linea N ya pedida (guardada en Respaldos/) sin gastar creditos.
#   --agregar: genera SOLO las lineas nuevas que agregaste al final de narracion.txt (ej. el bloque 2) y las pega
#              despues de la voz que ya tienes (aprobada), con la misma voz y ajustes; ElevenLabs recibe las ultimas
#              lineas como contexto para que suene igual. Gasta solo los creditos de las lineas nuevas.
#   --respuesta archivo.json: con --agregar, usa una respuesta de ElevenLabs ya guardada (Respaldos/.../agregadas.json)
#              en vez de pedirla otra vez (no gasta creditos; tambien sirve para probar).
# GASTA CREDITOS de ElevenLabs: confirmar con el usuario antes de correrlo.
# La clave se lee de la variable de entorno ELEVENLABS_API_KEY de Windows; nunca se imprime ni se guarda.
import base64, datetime, json, os, shutil, subprocess, sys, urllib.error, urllib.request


def _raiz():
    d = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(d, "Herramientas", "config.py")):
        if os.path.dirname(d) == d:
            sys.exit("No encuentro Herramientas/config.py")
        d = os.path.dirname(d)
    return d


sys.path.insert(0, os.path.join(_raiz(), "Herramientas"))
from config import VOZ_NARRADOR, MODELO_VOZ, RESPALDOS, episodio  # noqa: E402

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass
_args = list(sys.argv[1:])


def _opcion(nombre, con_valor=True):
    if nombre not in _args:
        return None
    i = _args.index(nombre)
    if not con_valor:
        del _args[i]
        return True
    v = _args[i + 1] if i + 1 < len(_args) else None
    del _args[i:i + 2]
    return v


VELOCIDAD = _opcion("--velocidad")
VELOCIDAD = float(VELOCIDAD) if VELOCIDAD else None
VOZ_ELEGIDA = _opcion("--voz")
LINEA = _opcion("--linea")              # una linea ("10") o varias seguidas que la voz dice pegadas ("24-26")
if LINEA:
    _r = [int(x) for x in LINEA.split("-")]
    N1, N2 = _r[0], _r[-1]
    LINEA = "%d" % N1 if N1 == N2 else "%d-%d" % (N1, N2)
SIMULAR = bool(_opcion("--simular", con_valor=False))
REUSAR = bool(_opcion("--reusar", con_valor=False))
AGREGAR = bool(_opcion("--agregar", con_valor=False))
RESPUESTA = _opcion("--respuesta")
if not _args:
    sys.exit("Uso: py voz_elevenlabs.py EP###_Nombre [archivo.txt] [--voz ID_DE_VOZ] [--linea N [--simular|--reusar]] "
             "[--agregar [--respuesta archivo.json]]")
NOMBRE_EP = _args[0]
EP = episodio(NOMBRE_EP)
TXT = _args[1] if len(_args) > 1 else os.path.join(EP, "narracion.txt")
if not os.path.exists(TXT):
    sys.exit("No existe el texto: " + TXT)
LINEAS = [l.strip() for l in open(TXT, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]
TEXT = " ".join(LINEAS)
if not TEXT:
    sys.exit("El texto esta vacio: " + TXT)
OUT = os.path.join(EP, "audio")
os.makedirs(OUT, exist_ok=True)
MP3, TIEMPOS, INFO = (os.path.join(OUT, f) for f in ("narracion.mp3", "narracion_tiempos.json", "narracion_info.json"))
AJUSTES = {"stability": 0.4, "similarity_boost": 0.75, "style": 0.3, "use_speaker_boost": True}
if VELOCIDAD:
    AJUSTES["speed"] = max(0.7, min(1.2, VELOCIDAD))


def api_key():
    v = os.environ.get("ELEVENLABS_API_KEY")
    if not v and sys.platform == "win32":
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            v, _ = winreg.QueryValueEx(k, "ELEVENLABS_API_KEY")
        except OSError:
            v = None
    if not v:
        sys.exit("Falta la variable de entorno ELEVENLABS_API_KEY (ver README)")
    return v.strip()


def pedir(texto, voz, ajustes, antes=None, despues=None):
    """llama a ElevenLabs -> (mp3 en bytes, tiempos por letra)"""
    body = {"text": texto, "model_id": MODELO_VOZ, "voice_settings": ajustes}
    if antes:
        body["previous_text"] = antes            # contexto: solo sirve para que la linea suene igual que las demas
    if despues:
        body["next_text"] = despues
    url = "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % voz
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("ERROR HTTP", e.code, e.read().decode("utf-8", "replace")[:500])
        sys.exit(1)
    return base64.b64decode(data["audio_base64"]), (data.get("alignment") or data.get("normalized_alignment"))


def respaldar(motivo):
    """copia la voz actual a Respaldos/<EP>_voz_<motivo>_<fecha>/ antes de cambiarla"""
    if not os.path.exists(MP3):
        return None
    dest = os.path.join(RESPALDOS, "%s_voz_%s_%s" % (os.path.basename(EP), motivo,
                                                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
    os.makedirs(dest, exist_ok=True)
    for f in (MP3, TIEMPOS, INFO):
        if os.path.exists(f):
            shutil.copy2(f, dest)
    return dest


# ------------------------------------------------------------------ voz completa
if not LINEA and not AGREGAR:
    antes_info = json.load(open(INFO, encoding="utf-8")) if os.path.exists(INFO) else {}
    VOICE = VOZ_ELEGIDA or antes_info.get("voz") or VOZ_NARRADOR     # rehacer un episodio = misma voz
    if not VOICE:
        sys.exit("Falta \"voz_narrador\" (id de la voz) en mi_config.json")
    print("Voz: %s... (%s) | se cobran unos %d creditos" % (VOICE[:6], "elegida con --voz" if VOZ_ELEGIDA else
          ("la misma del episodio" if antes_info.get("voz") else "la del canal, mi_config.json"), len(TEXT)))
    audio, al = pedir(TEXT, VOICE, AJUSTES)
    previa = respaldar("anterior")
    open(MP3, "wb").write(audio)
    json.dump(al, open(TIEMPOS, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"voz": VOICE, "modelo": MODELO_VOZ, "ajustes": AJUSTES, "lineas": LINEAS},
              open(INFO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok | audio:", len(audio), "bytes | caracteres:", len(TEXT), "| duracion aprox:",
          round((al or {}).get("character_end_times_seconds", [0])[-1], 2), "s")
    if previa:
        print("  la voz anterior quedo en", previa)
    print("Escuchala (audio/narracion.mp3) y despues: py Herramientas/audio/recortar_pausas.py", NOMBRE_EP)
    sys.exit(0)

# ------------------------------------------------------------------ rehacer solo una linea
import numpy as np  # noqa: E402

SRL, HOP = 44100, 0.01


def decodificar(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SRL), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def energia(x):
    """dB de cada 10 ms (0 = voz fuerte) y True donde hay sonido"""
    h = int(HOP * SRL)
    m = len(x) // h
    rms = np.sqrt((x[:m * h].reshape(m, h).astype(np.float64) ** 2).mean(axis=1))
    db = 20 * np.log10(rms / max(float(np.percentile(rms, 95)), 1e-9) + 1e-12)
    umbral = min(-35.0, max(-55.0, float(np.percentile(db, 5)) + 10))
    return db, db >= umbral


def nivel(x):
    h = int(HOP * SRL)
    m = len(x) // h
    if m < 3:
        return None
    return float(np.percentile(np.sqrt((x[:m * h].reshape(m, h).astype(np.float64) ** 2).mean(axis=1)), 90))


def punto_de_pegado(db, son, desde, hasta, lado):
    """segundo donde pegar, dentro del silencio entre desde y hasta (lado 'antes' = justo antes de que empiece
    la linea; 'despues' = justo despues de que termina). None si ahi no hay silencio ni un valle bajo."""
    k0, k1 = max(0, int(desde / HOP)), min(len(son), int(np.ceil(hasta / HOP)))
    runs, k = [], k0
    while k < k1:
        if son[k]:
            k += 1; continue
        b = k
        while b > 0 and not son[b - 1]:
            b -= 1
        while k < len(son) and not son[k]:
            k += 1
        if (k - b) * HOP >= 0.03:
            runs.append((b * HOP, k * HOP))
    if runs:
        r0, r1 = runs[-1] if lado == "antes" else runs[0]
        if lado == "antes":
            return r1 - 0.03 if r1 - r0 > 0.06 else (r0 + r1) / 2
        return r0 + 0.08 if r1 - r0 > 0.12 else (r0 + r1) / 2
    if k1 <= k0:
        return None
    k = k0 + int(np.argmin(db[k0:k1]))                 # sin silencio real: el punto mas bajo, si es bastante bajo
    return (k + 0.5) * HOP if db[k] < -30 else None


# ------------------------------------------------------------------ agregar lineas nuevas al final
if AGREGAR:
    if not (os.path.exists(MP3) and os.path.exists(TIEMPOS)):
        sys.exit("Primero hace falta la voz de las primeras lineas (audio/narracion.mp3 + narracion_tiempos.json)")
    info = json.load(open(INFO, encoding="utf-8")) if os.path.exists(INFO) else {}
    VOICE = VOZ_ELEGIDA or info.get("voz") or VOZ_NARRADOR
    if not VOICE:
        sys.exit("Falta la voz: pasa --voz ID_DE_LA_VOZ")
    ajustes = info.get("ajustes") or AJUSTES
    al = json.load(open(TIEMPOS, encoding="utf-8"))
    ch = list(al["characters"])
    st = list(al["character_start_times_seconds"])
    en = list(al["character_end_times_seconds"])
    viejo = "".join(ch)
    k = next((k for k in range(len(LINEAS), 0, -1) if " ".join(LINEAS[:k]) == viejo), None)
    if k is None:
        sys.exit("La voz actual no coincide con las primeras lineas de narracion.txt (cambiaste alguna?). "
                 "Para una linea usa --linea N; si cambiaron varias, rehaz la voz completa.")
    nuevas = LINEAS[k:]
    if not nuevas:
        sys.exit("No hay lineas nuevas al final de narracion.txt: la voz ya las tiene todas")
    texto = " ".join(nuevas)
    print("Lineas nuevas: %d a %d (%d letras = unos %d creditos) | voz %s..."
          % (k + 1, len(LINEAS), len(texto), 0 if RESPUESTA else len(texto), VOICE[:6]))
    if RESPUESTA:
        r = json.load(open(RESPUESTA, encoding="utf-8"))
        crudo, aln = base64.b64decode(r["audio_base64"]), r["alignment"]
        if "".join(aln["characters"]) != texto:
            sys.exit("La respuesta guardada no es del texto actual de las lineas nuevas")
        print("  usando la respuesta guardada (sin gastar creditos):", RESPUESTA)
    else:
        crudo, aln = pedir(texto, VOICE, ajustes, " ".join(LINEAS[max(0, k - 3):k]), None)
    v = decodificar(MP3)
    db, son = energia(v)
    tmp = os.path.join(OUT, "_nuevas.mp3")
    open(tmp, "wb").write(crudo)
    nuevo = decodificar(tmp)
    os.remove(tmp)
    db_n, son_n = energia(nuevo)
    if not son_n.any():
        sys.exit("ElevenLabs devolvio audio vacio")
    c_ini = max(0.0, int(np.argmax(son_n)) * HOP - 0.03)
    core = nuevo[int(round(c_ini * SRL)):].copy()
    k_fin = len(son) - int(np.argmax(son[::-1]))                 # cuadro despues del ultimo sonido de la voz vieja
    iA = min(len(v), int(round((k_fin * HOP + 0.08) * SRL)))
    izq = v[:iA].copy()
    pausa = np.zeros(int(0.30 * SRL), np.float32)              # respiro entre lo viejo y lo nuevo (recortar_pausas lo ajusta)
    objetivo, nn = nivel(v[:iA]), nivel(core)          # volumen tipico de toda la voz que ya estaba
    ganancia = float(np.clip(objetivo / nn, 0.25, 4.0)) if objetivo and nn else 1.0
    core *= ganancia
    F = int(0.005 * SRL)
    rampa = np.linspace(1.0, 0.0, F, dtype=np.float32)
    if len(izq) > F:
        izq[-F:] *= rampa
    if len(core) > F:
        core[:F] *= rampa[::-1]
    salida = np.concatenate([izq, pausa, core]).astype(np.float32)
    A2 = iA / SRL
    ini_nuevo = A2 + len(pausa) / SRL
    d = ini_nuevo - c_ini
    tiempos2 = {"characters": ch + [" "] + list(aln["characters"]),
                "character_start_times_seconds": [round(min(x, A2), 3) for x in st] + [round(A2, 3)]
                + [round(max(x + d, ini_nuevo), 3) for x in aln["character_start_times_seconds"]],
                "character_end_times_seconds": [round(min(x, A2), 3) for x in en] + [round(ini_nuevo, 3)]
                + [round(max(x + d, ini_nuevo), 3) for x in aln["character_end_times_seconds"]]}
    previa = respaldar("antes_agregar")
    if previa and not RESPUESTA:          # lo pedido queda guardado: se puede volver a pegar con --respuesta
        json.dump({"texto": texto, "audio_base64": base64.b64encode(crudo).decode("ascii"), "alignment": aln},
                  open(os.path.join(previa, "agregadas.json"), "w", encoding="utf-8"), ensure_ascii=False)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SRL), "-ac", "1", "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "192k", MP3], input=salida.tobytes(), check=True)
    json.dump(tiempos2, open(TIEMPOS, "w", encoding="utf-8"), ensure_ascii=False)
    info.update({"voz": VOICE, "modelo": MODELO_VOZ, "ajustes": ajustes, "lineas": LINEAS})
    json.dump(info, open(INFO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok | %d lineas nuevas pegadas despues de %.2f s | volumen x%.2f (como el resto de la voz) | voz %.2f s -> %.2f s"
          % (len(nuevas), A2, ganancia, len(v) / SRL, len(salida) / SRL))
    if previa:
        print("  la voz anterior quedo en", previa)
    print("Escuchala y despues: py Herramientas/audio/recortar_pausas.py", NOMBRE_EP)
    sys.exit(0)

n, n2, etq = N1, N2, LINEA        # primera y ultima linea a rehacer (1, 2, ...) y su nombre ("10", "24-26")
BASE_MP3, BASE_TIEMPOS, BASE_INFO = MP3, TIEMPOS, INFO       # voz sobre la que se pega la linea
guardada = None
if REUSAR:
    import glob
    carpetas = sorted(c for c in glob.glob(os.path.join(RESPALDOS, "%s_voz_antes_linea%s_*" % (os.path.basename(EP), etq)))
                      if os.path.exists(os.path.join(c, "linea_%s_nueva.json" % etq)))
    if not carpetas:
        sys.exit("No hay una linea %s ya pedida en Respaldos/ para reusar" % etq)
    guardada = carpetas[-1]
    actual = json.load(open(INFO, encoding="utf-8")) if os.path.exists(INFO) else {}
    if str((actual.get("lineas_rehechas") or [etq])[-1]) != etq:
        sys.exit("Despues de la linea %s se rehizo otra; reusarla desharia esa. Pide la linea otra vez." % etq)
    BASE_MP3, BASE_TIEMPOS, BASE_INFO = (os.path.join(guardada, f) for f in
                                         ("narracion.mp3", "narracion_tiempos.json", "narracion_info.json"))
if not (os.path.exists(BASE_MP3) and os.path.exists(BASE_TIEMPOS)):
    sys.exit("Primero hace falta la voz completa (audio/narracion.mp3 + narracion_tiempos.json)")
if not 1 <= n <= n2 <= len(LINEAS):
    sys.exit("No existe la linea %s (narracion.txt tiene %d lineas de texto)" % (etq, len(LINEAS)))
if os.path.exists(BASE_INFO):
    info = json.load(open(BASE_INFO, encoding="utf-8"))
elif REUSAR and os.path.exists(INFO):
    info = json.load(open(INFO, encoding="utf-8"))
else:
    info = {}
VOICE = VOZ_ELEGIDA or info.get("voz") or VOZ_NARRADOR
if not VOICE:
    sys.exit("Falta la voz: pasa --voz ID_DE_LA_VOZ")
if not (VOZ_ELEGIDA or info.get("voz")) and not (SIMULAR or REUSAR):
    print("  Aviso: no se sabe con que voz se hizo narracion.mp3; uso voz_narrador de mi_config.json.")
    print("  Si la voz completa se hizo con otra, para (Ctrl+C) y pasa --voz ID_DE_ESA_VOZ.")
ajustes = info.get("ajustes") or AJUSTES
al = json.load(open(BASE_TIEMPOS, encoding="utf-8"))
ch = list(al["characters"])
st = list(al["character_start_times_seconds"])
en = list(al["character_end_times_seconds"])
viejo = "".join(ch)
viejas = info["lineas"] if len(info.get("lineas") or []) == len(LINEAS) else list(LINEAS)
pre = " ".join(viejas[:n - 1]) + (" " if n > 1 else "")
suf = (" " if n2 < len(viejas) else "") + " ".join(viejas[n2:])
otras_iguales = all(viejas[k] == LINEAS[k] for k in range(len(LINEAS)) if not n - 1 <= k < n2)
if not (otras_iguales and viejo.startswith(pre) and viejo.endswith(suf) and len(pre) + len(suf) < len(viejo)):
    sys.exit("La voz actual no coincide con narracion.txt fuera de la linea %s (cambiaron otras lineas?). "
             "Rehaz la voz completa." % etq)
i0, i1 = len(pre), len(viejo) - len(suf)                 # letras de la linea vieja: viejo[i0:i1]
v = decodificar(BASE_MP3)
dur = len(v) / SRL
db, son = energia(v)
t_ini, t_fin = st[i0], en[i1 - 1]
A = 0.0 if n == 1 else punto_de_pegado(db, son, en[i0 - 2] - 0.05, t_ini + 0.05, "antes")
B = dur if n2 == len(viejas) else punto_de_pegado(db, son, t_fin - 0.05, st[i1 + 1] + 0.05, "despues")
if A is None or B is None:
    pega = (n - 1) if A is None else (n2 + 1)
    sys.exit("La linea %s esta pegada a la %d sin silencio: no se puede rehacer sola sin cortar voz. Rehazlas juntas: "
             "--linea %d-%d" % (etq, pega, min(n, pega), max(n2, pega)))

crudo = None
if SIMULAR:                     # la misma linea vieja hace de "nueva" (con silencio antes y despues, como ElevenLabs)
    a_, b_ = int(round(A * SRL)), int(round(B * SRL))
    nuevo = np.concatenate([np.zeros(int(0.25 * SRL), np.float32), v[a_:b_], np.zeros(int(0.35 * SRL), np.float32)])
    off = 0.25 - a_ / SRL
    nch, nst, nen = ch[i0:i1], [x + off for x in st[i0:i1]], [x + off for x in en[i0:i1]]
elif REUSAR:
    nuevo = decodificar(os.path.join(guardada, "linea_%s_nueva.mp3" % etq))
    aln = json.load(open(os.path.join(guardada, "linea_%s_nueva.json" % etq), encoding="utf-8"))["alignment"]
    nch, nst, nen = aln["characters"], aln["character_start_times_seconds"], aln["character_end_times_seconds"]
    print("Reusando la linea %s ya pedida (sin gastar creditos): %s" % (etq, guardada))
else:
    antes = " ".join(LINEAS[max(0, n - 3):n - 1]) or None
    despues = LINEAS[n2] if n2 < len(LINEAS) else None
    texto_nuevo = " ".join(LINEAS[n - 1:n2])
    print('Pidiendo a ElevenLabs solo la linea %s (%d letras = unos %d creditos): "%s"'
          % (etq, len(texto_nuevo), len(texto_nuevo), texto_nuevo))
    crudo, aln = pedir(texto_nuevo, VOICE, ajustes, antes, despues)
    tmp = os.path.join(OUT, "_linea_%s_nueva.mp3" % etq)
    open(tmp, "wb").write(crudo)
    nuevo = decodificar(tmp)
    os.remove(tmp)
    nch, nst, nen = aln["characters"], aln["character_start_times_seconds"], aln["character_end_times_seconds"]
db_n, son_n = energia(nuevo)
if not son_n.any():
    sys.exit("ElevenLabs devolvio audio vacio")
kn0, kn1 = int(np.argmax(son_n)), len(son_n) - int(np.argmax(son_n[::-1]))
c_ini = 0.0 if n == 1 else max(0.0, kn0 * HOP - 0.03)
c_fin = len(nuevo) / SRL if n2 == len(viejas) else min(len(nuevo) / SRL, kn1 * HOP + 0.08)
core = nuevo[int(round(c_ini * SRL)):int(round(c_fin * SRL))].copy()
iA, iB = int(round(A * SRL)), int(round(B * SRL))
# volumen igual al de las lineas vecinas (una linea pedida sola puede salir mucho mas fuerte o mas suave)
vecinas = []
if n > 1:
    r1 = i0 - 1
    vecinas.append(nivel(v[int(st[r1 - len(viejas[n - 2])] * SRL):int(en[r1 - 1] * SRL)]))
if n2 < len(viejas):
    r0 = i1 + 1
    vecinas.append(nivel(v[int(st[r0] * SRL):int(en[r0 + len(viejas[n2]) - 1] * SRL)]))
vecinas = [x for x in vecinas if x]
objetivo, nn = (float(np.mean(vecinas)) if vecinas else nivel(v[iA:iB])), nivel(core)
ganancia = float(np.clip(objetivo / nn, 0.25, 4.0)) if objetivo and nn else 1.0
core *= ganancia
izq, der = v[:iA].copy(), v[iB:].copy()
F = int(0.005 * SRL)
rampa = np.linspace(1.0, 0.0, F, dtype=np.float32)                           # fundidos de 5 ms, en silencio
if len(izq) > F:
    izq[-F:] *= rampa
if len(core) > 2 * F:
    core[:F] *= rampa[::-1]
    core[-F:] *= rampa
if len(der) > F:
    der[:F] *= rampa[::-1]
salida = np.concatenate([izq, core, der]).astype(np.float32)

# tiempos por letra: antes de la linea igual; la linea nueva en su lugar; despues, recorrido lo que cambio el largo
A2, Lc, B2 = iA / SRL, len(core) / SRL, iB / SRL
d_nuevo, d_resto = A2 - c_ini, A2 + Lc - B2


def poner(lista_vieja, lista_nueva):
    return ([round(min(x, A2), 3) for x in lista_vieja[:i0]]
            + [round(min(max(x + d_nuevo, A2), A2 + Lc), 3) for x in lista_nueva]
            + [round(max(x, B2) + d_resto, 3) for x in lista_vieja[i1:]])


tiempos2 = {"characters": ch[:i0] + list(nch) + ch[i1:], "character_start_times_seconds": poner(st, nst),
            "character_end_times_seconds": poner(en, nen)}
fin_arch = "_simulada" if SIMULAR else ""
dest_mp3 = os.path.join(OUT, "narracion%s.mp3" % fin_arch)
dest_json = os.path.join(OUT, "narracion_tiempos%s.json" % fin_arch)
previa = None
if not (SIMULAR or REUSAR):
    previa = respaldar("antes_linea%s" % etq)
    if previa and crudo:            # la linea pedida queda guardada: se puede volver a pegar con --reusar
        open(os.path.join(previa, "linea_%s_nueva.mp3" % etq), "wb").write(crudo)
        json.dump({"texto": " ".join(LINEAS[n - 1:n2]), "alignment": aln},
                  open(os.path.join(previa, "linea_%s_nueva.json" % etq), "w", encoding="utf-8"), ensure_ascii=False)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SRL), "-ac", "1", "-i", "-",
                "-c:a", "libmp3lame", "-b:a", "192k", dest_mp3], input=salida.tobytes(), check=True)
json.dump(tiempos2, open(dest_json, "w", encoding="utf-8"), ensure_ascii=False)
if not SIMULAR:
    info.update({"voz": VOICE, "modelo": MODELO_VOZ, "ajustes": ajustes, "lineas": LINEAS})
    if etq not in [str(x) for x in info.setdefault("lineas_rehechas", [])]:
        info["lineas_rehechas"].append(etq)
    json.dump(info, open(INFO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok | linea %s %s | pegada entre %.2f y %.2f s | volumen x%.2f (como las lineas vecinas) | voz %.2f s -> %.2f s"
      % (etq, "SIMULADA (sin gastar creditos)" if SIMULAR else ("re-pegada (sin gastar creditos)" if REUSAR else "rehecha"),
         A, B, ganancia, dur, len(salida) / SRL))
print("  ->", dest_mp3)
if previa:
    print("  la voz anterior quedo en", previa)
if not SIMULAR:
    print("Ahora: py Herramientas/audio/recortar_pausas.py", NOMBRE_EP, " (la vuelve a escuchar y revisar)")
