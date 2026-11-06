# Analisis visual: cortes, movimiento de camara, transiciones, efectos, tipo de plano (CLIP) y hojas de contacto.
import os
import numpy as np
import cv2
from comun import log, suav, r, fuente

SW = 320  # ancho de trabajo para medir movimiento


# ----------------------------------------------------------------- cortes
def detectar_cortes(proxy, fps, nf, umbral=22.0):
    """candidatos sensibles (PySceneDetect) + verificacion: un corte real es un SALTO AISLADO entre dos cuadros;
    en un movimiento rapido (giro, algo pasando cerca) los cuadros vecinos cambian igual de rapido.
    Calibrado con EP001: reales ratio>=2 o salto>=42; falsos ratio 1.1-1.3 y salto 23-29."""
    from scenedetect import detect, ContentDetector
    esc = detect(proxy, ContentDetector(threshold=umbral, min_scene_len=max(2, int(fps * 0.25))))
    cand = sorted(set([s[0].frame_num for s in esc[1:]])) if esc else []
    cand = [c for c in cand if 0 < c < nf]
    cap = cv2.VideoCapture(proxy)
    cortes = [0]
    for c in cand:
        a = max(0, c - 6)
        cap.set(cv2.CAP_PROP_POS_FRAMES, a)
        g = []
        for f in range(a, min(nf, c + 6)):
            ok, fr = cap.read()
            if not ok:
                break
            g.append(cv2.cvtColor(cv2.resize(fr, (SW, int(SW * fr.shape[0] / fr.shape[1]))), cv2.COLOR_BGR2GRAY).astype(np.float32))
        k = c - a                      # posicion del corte dentro de la ventana
        if len(g) <= k:
            cortes.append(c)
            continue
        d = [float(np.abs(g[i] - g[i - 1]).mean()) for i in range(1, len(g))]
        salto = d[k - 1]
        vec = d[:k - 1] + d[k:]
        ratio = salto / max(1.0, float(np.median(vec))) if vec else 99
        if ratio >= 2.0 or salto >= 42:
            cortes.append(c)
    cap.release()
    return cortes + [nf]


# ----------------------------------------------------------------- medicion por fotograma
def medir_fotogramas(proxy, cortes, nf):
    cap = cv2.VideoCapture(proxy)
    W, H = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    SH = int(round(SW * H / W / 2) * 2)
    z = lambda: np.zeros(nf)
    m = {k: z() for k in ("dx", "dy", "rot", "brillo", "sat", "lab_a", "lab_b", "nitidez", "vineta", "resid", "blobs", "dif")}
    m["escala"] = np.ones(nf)
    m["blobs_franja"] = np.zeros((nf, 10))
    m["ok"] = np.zeros(nf, bool)
    yy, xx = np.mgrid[0:SH, 0:SW]
    cx, cy = SW / 2, SH / 2
    dn = np.hypot((xx - cx) / cx, (yy - cy) / cy)
    centro, esquinas = dn < 0.45, dn > 1.15
    orb = cv2.ORB_create(800)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    cs = set(cortes)
    prev = prev_k = prev_d = None
    borde = np.zeros((SH, SW), np.uint8)
    borde[6:-6, 6:-6] = 1
    n_ok = 0
    for i in range(nf):
        okf, fr = cap.read()
        if not okf:
            break
        n_ok = i + 1
        sm = cv2.resize(fr, (SW, SH), interpolation=cv2.INTER_AREA)
        g = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB)
        m["brillo"][i] = g.mean()
        m["sat"][i] = hsv[..., 1].mean()
        m["lab_a"][i] = lab[..., 1].mean() - 128
        m["lab_b"][i] = lab[..., 2].mean() - 128
        m["nitidez"][i] = cv2.Laplacian(g, cv2.CV_32F).var()
        m["vineta"][i] = g[esquinas].mean() / max(1.0, g[centro].mean())
        k, d = orb.detectAndCompute(g, None)
        if prev is not None:
            m["dif"][i] = cv2.absdiff(g, prev).mean()
        if (i not in cs and prev is not None and d is not None and prev_d is not None
                and len(k) >= 25 and len(prev_k) >= 25):
            mt = bf.match(prev_d, d)
            if len(mt) >= 20:
                p1 = np.float32([prev_k[x.queryIdx].pt for x in mt])
                p2 = np.float32([k[x.trainIdx].pt for x in mt])
                A, inl = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if A is not None and inl is not None and inl.sum() >= 15:
                    s = float(np.hypot(A[0, 0], A[1, 0]))
                    c = np.array([cx, cy])
                    t = A[:, :2] @ c + A[:, 2] - c          # traslacion respecto al centro (separa zoom de paneo)
                    m["escala"][i] = s
                    m["dx"][i] = t[0] / SW
                    m["dy"][i] = t[1] / SW
                    m["rot"][i] = np.degrees(np.arctan2(A[1, 0], A[0, 0]))
                    m["ok"][i] = True
                    # lo que se mueve aparte de la camara (personajes, particulas)
                    w = cv2.warpAffine(prev, A, (SW, SH), borderMode=cv2.BORDER_REPLICATE)
                    mask = ((cv2.absdiff(g, w) > 28) & (borde > 0)).astype(np.uint8)
                    m["resid"][i] = mask.mean()
                    n, _, st, cen = cv2.connectedComponentsWithStats(mask, connectivity=8)
                    ar = st[1:, cv2.CC_STAT_AREA]
                    chicos = (ar >= 2) & (ar <= 60)
                    m["blobs"][i] = int(chicos.sum())
                    if chicos.any():
                        fr_ = np.clip((cen[1:, 1][chicos] / SH * 10).astype(int), 0, 9)
                        m["blobs_franja"][i] = np.bincount(fr_, minlength=10)
        prev, prev_k, prev_d = g, k, d
    cap.release()
    if n_ok < nf:
        for kk in m:
            m[kk] = m[kk][:n_ok]
    return m, n_ok


# ----------------------------------------------------------------- tomas
def _color(a, b):
    if abs(a) < 4 and abs(b) < 6:
        return "neutro"
    ang = np.degrees(np.arctan2(b, a)) % 360
    if ang < 40 or ang >= 340:
        return "rojizo/rosa"
    if ang < 75:
        return "cálido (naranja)"
    if ang < 120:
        return "amarillento"
    if ang < 200:
        return "verdoso"
    if ang < 290:
        return "frío (azul)"
    return "morado"


def analizar_tomas(m, cortes, fps):
    tomas = []
    nit_med = float(np.median(m["nitidez"][m["nitidez"] > 0])) if (m["nitidez"] > 0).any() else 1.0
    for ti in range(len(cortes) - 1):
        a, b = cortes[ti], cortes[ti + 1]
        if b - a < 2:
            continue
        seg = slice(a + 1, b)
        sc, mx, my, rt, okk = m["escala"][seg], m["dx"][seg], m["dy"][seg], m["rot"][seg], m["ok"][seg]
        dur = (b - a) / fps
        zoom_total = float(np.prod(sc)) - 1.0
        log_s = np.log(np.clip(sc, 1e-3, None))
        zoom_vel = float(np.max(np.abs(suav(log_s, 5))) * fps) if len(log_s) else 0.0
        n_ini = max(1, int(0.35 * fps))
        zoom_ini = float(np.prod(sc[:n_ini])) - 1.0
        pan_x, pan_y = float(np.sum(mx)), float(np.sum(my))
        rot_total = float(np.sum(rt))
        rx, ry = mx - suav(mx, 9), my - suav(my, 9)
        temblor = float(np.sqrt(np.mean(rx ** 2 + ry ** 2))) * 100 if len(mx) else 0.0
        frec = None
        if temblor > 0.25 and len(rx) >= 16:
            sp = np.abs(np.fft.rfft((rx - rx.mean()) * np.hanning(len(rx))))
            fr_ = np.fft.rfftfreq(len(rx), 1.0 / fps)
            if len(sp) > 2:
                frec = float(fr_[1:][np.argmax(sp[1:])])
        cobertura = float(okk.mean()) if len(okk) else 0.0
        if cobertura < 0.4:
            tipo = "indeterminado"
        elif zoom_ini > 0.06 and zoom_vel > 0.8:
            tipo = "golpe de zoom"
        elif zoom_vel > 0.9 and abs(zoom_total) > 0.06 and dur < 1.2:
            tipo = "golpe de zoom"
        elif zoom_total > 0.03:
            tipo = "acercamiento lento"
        elif zoom_total < -0.03:
            tipo = "alejamiento lento"
        elif abs(rot_total) > 6:
            tipo = "giro de cámara"
        elif abs(pan_x) > 0.12 and abs(pan_x) >= abs(pan_y):
            tipo = "paneo horizontal"
        elif abs(pan_y) > 0.12:
            tipo = "paneo vertical"
        else:
            tipo = "fija"
        con_temblor = temblor > 2.5 and tipo != "indeterminado"   # calibrado con EP001: ruido de medicion <= 2, temblor real ~8
        accion = float(np.mean(m["resid"][seg])) * 100 if len(okk) else 0.0
        tomas.append({
            "n": len(tomas) + 1, "f0": a, "f1": b, "inicio": r(a / fps, 3), "fin": r(b / fps, 3), "duracion": r(dur, 3),
            "camara": tipo, "temblor": con_temblor,
            "zoom_total_pct": r(zoom_total * 100, 1), "zoom_vel": r(zoom_vel, 3), "zoom_inicio_pct": r(zoom_ini * 100, 1),
            "paneo_x_pct": r(pan_x * 100, 1), "paneo_y_pct": r(pan_y * 100, 1), "giro_grados": r(rot_total, 1),
            "temblor_pct": r(temblor, 3), "temblor_hz": r(frec, 2),
            "movimiento_en_cuadro_pct": r(accion, 2), "medicion_ok_pct": round(cobertura * 100),
            "brillo": r(np.mean(m["brillo"][a:b]), 1), "saturacion": r(np.mean(m["sat"][a:b]), 1),
            "tono": _color(float(np.mean(m["lab_a"][a:b])), float(np.mean(m["lab_b"][a:b]))),
            "desenfoque": bool(np.median(m["nitidez"][a:b]) < 0.35 * nit_med),
            "vineta": bool(np.median(m["vineta"][a:b]) < 0.62),
        })
    return tomas


# ----------------------------------------------------------------- transiciones
def _gris(cap, f, w=SW):
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, f))
    ok, fr = cap.read()
    if not ok:
        return None
    return cv2.cvtColor(cv2.resize(fr, (w, int(w * fr.shape[0] / fr.shape[1]))), cv2.COLOR_BGR2GRAY).astype(np.float32)


def _es_disolvencia(cap, c, nf):
    """una disolvencia mezcla las dos tomas: el cuadro del medio se explica como alfa*A + (1-alfa)*B."""
    A, B = _gris(cap, max(0, c - 9)), _gris(cap, min(nf - 1, c + 8))
    if A is None or B is None or np.abs(A - B).mean() < 12:
        return False
    for f in (c - 3, c - 1, c + 1):
        M = _gris(cap, f)
        if M is None:
            continue
        d = (A - B).ravel()
        alfa = float(np.clip(np.dot((M - B).ravel(), d) / max(1e-6, np.dot(d, d)), 0, 1))
        if 0.2 < alfa < 0.8:
            e_mix = np.abs(M - (alfa * A + (1 - alfa) * B)).mean()
            if e_mix < 0.55 * min(np.abs(M - A).mean(), np.abs(M - B).mean()):
                return True
    return False


def detectar_transiciones(m, cortes, fps, tomas, proxy):
    br, nit = m["brillo"], m["nitidez"]
    nf = len(br)
    cap = cv2.VideoCapture(proxy)
    salida = []
    for t in tomas[1:]:
        c = t["f0"]
        a0, b0 = max(0, c - 8), min(nf, c + 8)
        pre = float(np.median(br[max(0, c - 15):max(1, c - 6)])) if c > 6 else float(br[a0])
        post = float(np.median(br[min(nf - 1, c + 6):min(nf, c + 15)])) if c + 6 < nf else float(br[b0 - 1])
        ventana = br[a0:b0]
        ult = slice(max(0, c - 4), c)
        nit_toma = float(np.median(nit[max(0, c - 20):c])) if c > 0 else 1.0
        borroso = len(nit[ult]) and float(np.min(nit[ult])) < 0.3 * max(1.0, nit_toma)
        tipo = "corte directo"
        if len(ventana) and ventana.min() < 14 and min(pre, post) > 28:
            tipo = "fundido a negro"
        elif len(ventana) and ventana.max() > max(pre, post) + 45:
            tipo = "destello blanco"
        elif _es_disolvencia(cap, c, nf):
            tipo = "disolvencia"
        elif (abs(float(np.sum(m["dx"][ult]))) > 0.35 or abs(float(np.sum(m["dy"][ult]))) > 0.35) and borroso:
            tipo = "barrido (látigo)"
        elif borroso:
            tipo = "barrido (desenfoque)"
        elif float(np.prod(m["escala"][ult])) > 1.25:
            tipo = "zoom de transición"
        salida.append({"t": t["inicio"], "toma": t["n"], "tipo": tipo})
    cap.release()
    return salida


# ----------------------------------------------------------------- efectos
def _eventos(mask, fps, min_frames, tipo, extra=None):
    ev = []
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            if j - i >= min_frames:
                e = {"tipo": tipo, "f0": i, "f1": j, "inicio": r(i / fps, 2), "fin": r(j / fps, 2), "duracion": r((j - i) / fps, 2)}
                if extra:
                    e.update(extra(i, j))
                ev.append(e)
            i = j
        else:
            i += 1
    return ev


def detectar_efectos(m, cortes, fps, tomas, banda_subs=None):
    br, nf = m["brillo"], len(m["brillo"])
    base = suav(br, 11)
    ev = []
    ev += _eventos((br - base > 40) & (br > 120), fps, 1, "destello")
    ev += _eventos(br < 12, fps, 3, "pantalla negra")
    ev += _eventos(br > 238, fps, 2, "pantalla blanca")
    # particulas: muchos puntos chicos moviendose aparte de la camara, SIN la franja de subtitulos
    # (las letras que cambian parecen particulas) ni zooms/paneos rapidos (paralaje). Calibrado con ClusterK.
    bf_ = m.get("blobs_franja")
    if bf_ is not None and banda_subs:
        y0, y1 = int(banda_subs[0] / 10), int(np.ceil(banda_subs[1] / 10))
        quitar = list(range(max(0, y0 - 1), min(10, y1 + 1)))
        bl = bf_.sum(1) - bf_[:, quitar].sum(1)
    else:
        bl = m["blobs"].copy()
    rapido = (np.abs(np.log(np.clip(m["escala"], 1e-3, None))) > 0.012) | (np.hypot(m["dx"], m["dy"]) > 0.03)
    bl = np.where(rapido, 0, bl)
    umbral_b = max(18.0, 4.0 * float(np.median(bl)))
    ev += _eventos(suav(bl, 5) > umbral_b, fps, int(fps * 0.4), "posibles partículas (hojas/lluvia/chispas/polvo)",
                   lambda i, j: {"puntos_medios": r(np.mean(bl[i:j]), 1)})
    # temblor fuerte y corto (impacto): pico muy por encima del temblor normal de su toma, que dura poco
    sh = suav(np.hypot(m["dx"] - suav(m["dx"], 7), m["dy"] - suav(m["dy"], 7)) * 100, 3)
    pico = np.zeros(nf, bool)
    for t in tomas:
        a, b = t["f0"], t["f1"]
        base_t = float(np.median(sh[a:b])) if b > a else 0.0
        pico[a:b] = sh[a:b] > max(3.0, 3.5 * base_t)
        pico[a:min(b, a + 4)] = False          # justo despues de un corte la medicion no vale
    ev += [e for e in _eventos(pico, fps, 2, "sacudida de impacto") if e["duracion"] <= 0.6]
    # camara congelada / imagen fija (nada se mueve)
    quieto = (m["dif"] < 0.4) & m["ok"]
    for t in tomas:
        quieto[t["f0"]] = False
    ev += _eventos(quieto, fps, int(fps * 0.6), "imagen congelada")
    # cambio de color dentro de una toma (tinte rojo, flash de color)
    for t in tomas:
        a, b = t["f0"], t["f1"]
        if b - a < 6:
            continue
        la, lb = m["lab_a"][a:b], m["lab_b"][a:b]
        dev = np.hypot(la - np.median(la), lb - np.median(lb))
        for e in _eventos(dev > 18, fps, 3, "cambio de color", lambda i, j: {"tono": _color(float(np.mean(la[i:j])), float(np.mean(lb[i:j])))}):
            e["f0"] += a; e["f1"] += a
            e["inicio"], e["fin"] = r(e["f0"] / fps, 2), r(e["f1"] / fps, 2)
            ev.append(e)
    # camara lenta: fotogramas repetidos dentro de tomas con movimiento
    rep = (m["dif"] < 0.15)
    for t in tomas:
        rep[t["f0"]] = False
    if rep.mean() < 0.5:
        ev += _eventos(np.convolve(rep, np.ones(4), "same") >= 2, fps, int(fps * 0.5), "posible cámara lenta")
    ev.sort(key=lambda e: e["f0"])
    for i, e in enumerate(ev):
        e["n"] = i + 1
    return ev


# ----------------------------------------------------------------- CLIP (tipo de plano, lugar, ambiente)
GRUPOS = {
    "plano": [
        ("primerísimo primer plano", "an extreme close-up of a character's eyes or face filling the frame"),
        ("primer plano", "a close-up shot of a cartoon character's face"),
        ("plano medio", "a medium shot of a cartoon character from the waist up"),
        ("plano entero", "a full body shot of a cartoon character standing"),
        ("plano general", "a wide shot of a place with small characters far away"),
        ("plano aéreo", "an aerial drone view looking down from high above"),
        ("plano detalle", "a close-up of an object or hands"),
        ("texto en pantalla", "a screen with big text on it"),
        ("negro", "a completely black screen"),
    ],
    "lugar": [
        ("interior", "an indoor room"),
        ("exterior", "an outdoor scene"),
    ],
    "hora": [
        ("día", "a bright daytime scene"),
        ("atardecer", "a sunset scene with orange sky"),
        ("noche", "a dark night scene"),
    ],
    "ambiente": [
        ("alegre", "a happy cheerful colorful scene"),
        ("tenso", "a tense dramatic scene"),
        ("terror", "a scary horror scene"),
        ("triste", "a sad gloomy scene"),
        ("acción", "an action scene with explosions or chase"),
    ],
}
_CLIP = {}


def _clip():
    if not _CLIP:
        import torch, open_clip
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        model, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k", device=dev)
        model.eval()
        tok = open_clip.get_tokenizer("ViT-B-32")
        txt = {}
        with torch.no_grad():
            for g, et in GRUPOS.items():
                ft = model.encode_text(tok(["a 3D Roblox animation frame: " + e for _, e in et]).to(dev))
                txt[g] = ft / ft.norm(dim=-1, keepdim=True)
        _CLIP.update(model=model, prep=prep, dev=dev, txt=txt)
    return _CLIP


def clasificar_tomas(proxy, tomas):
    import torch
    from PIL import Image
    c = _clip()
    cap = cv2.VideoCapture(proxy)
    ims, idx = [], []
    for ti, t in enumerate(tomas):
        a, b = t["f0"], t["f1"]
        for q in (0.25, 0.5, 0.75):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(a + (b - a) * q))
            ok, fr = cap.read()
            if ok:
                ims.append(c["prep"](Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))))
                idx.append(ti)
    cap.release()
    if not ims:
        return
    feats = []
    with torch.no_grad():
        for i in range(0, len(ims), 64):
            f = c["model"].encode_image(torch.stack(ims[i:i + 64]).to(c["dev"]))
            feats.append(f / f.norm(dim=-1, keepdim=True))
    F = torch.cat(feats)
    idx = np.array(idx)
    for ti, t in enumerate(tomas):
        sel = np.where(idx == ti)[0]
        if not len(sel):
            continue
        fi = F[sel].mean(0, keepdim=True)
        fi = fi / fi.norm(dim=-1, keepdim=True)
        for g, et in GRUPOS.items():
            p = (100 * fi @ c["txt"][g].T).softmax(-1)[0].cpu().numpy()
            k = int(np.argmax(p))
            clave = "plano_clip" if g == "plano" else g
            t[clave] = et[k][0]
            t[clave + "_conf"] = r(p[k], 2)
            if g == "plano":
                t.setdefault("plano", et[k][0])


# ----------------------------------------------------------------- personajes y caras (Grounding DINO)
_DINO = {}


def _dino():
    if not _DINO:
        import torch
        from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
        mid = "IDEA-Research/grounding-dino-tiny"
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        _DINO.update(proc=AutoProcessor.from_pretrained(mid), dev=dev,
                     model=AutoModelForZeroShotObjectDetection.from_pretrained(mid).to(dev).eval())
    return _DINO


def _nms(cajas, umbral=0.6):
    cajas = sorted(cajas, key=lambda c: -c[0])
    out = []
    for s, b in cajas:
        ok = True
        for _, o in out:
            ix = max(0, min(b[2], o[2]) - max(b[0], o[0])); iy = max(0, min(b[3], o[3]) - max(b[1], o[1]))
            inter = ix * iy
            u = (b[2] - b[0]) * (b[3] - b[1]) + (o[2] - o[0]) * (o[3] - o[1]) - inter
            if u > 0 and inter / u > umbral:
                ok = False
                break
        if ok:
            out.append((s, b))
    return out


def _plano_por_tamano(alto_cara, alto_pj, n_pj):
    """tipo de plano segun cuanto ocupa la cara / el cuerpo del alto del cuadro."""
    if alto_cara >= 0.40:
        return "primerísimo primer plano"
    if alto_cara >= 0.22:
        return "primer plano"
    if alto_cara >= 0.11 or alto_pj >= 0.85:
        return "plano medio"
    if alto_pj >= 0.40:
        return "plano entero"
    if n_pj:
        return "plano general"
    return None


def medir_personajes(proxy, tomas):
    """por toma: cuantos personajes, que tan grandes y que tan grande la cara -> tipo de plano medido."""
    import torch
    from PIL import Image
    d = _dino()
    cap = cv2.VideoCapture(proxy)
    for t in tomas:
        a, b = t["f0"], t["f1"]
        mejores = []
        for q in (0.4, 0.75):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(a + (b - a) * q))
            ok, fr = cap.read()
            if not ok:
                continue
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
            inp = d["proc"](images=im, text=[["a cartoon character", "a face"]], return_tensors="pt").to(d["dev"])
            with torch.no_grad():
                o = d["model"](**inp)
            res = d["proc"].post_process_grounded_object_detection(o, inp.input_ids, threshold=0.3, text_threshold=0.25,
                                                                   target_sizes=[im.size[::-1]])[0]
            labs = res.get("text_labels", res.get("labels"))
            H_, W_ = im.size[1], im.size[0]
            pj = _nms([(float(s), [float(x) for x in bb]) for l, s, bb in zip(labs, res["scores"], res["boxes"]) if "character" in str(l) and s >= 0.35])
            ca = _nms([(float(s), [float(x) for x in bb]) for l, s, bb in zip(labs, res["scores"], res["boxes"]) if "face" in str(l) and s >= 0.35])
            alto_pj = max([(bb[3] - bb[1]) / H_ for _, bb in pj], default=0.0)
            alto_ca = max([(bb[3] - bb[1]) / H_ for _, bb in ca], default=0.0)
            cx = None
            if pj:
                bb = max(pj, key=lambda x: (x[1][3] - x[1][1]))[1]
                cx = ((bb[0] + bb[2]) / 2 / W_, (bb[1] + bb[3]) / 2 / H_)
            mejores.append((alto_ca, alto_pj, len(pj), cx))
        if not mejores:
            continue
        alto_ca = float(np.median([x[0] for x in mejores])); alto_pj = float(np.median([x[1] for x in mejores]))
        n_pj = int(round(np.median([x[2] for x in mejores])))
        t["personajes_n"] = n_pj
        t["alto_personaje_pct"] = r(100 * alto_pj, 0)
        t["alto_cara_pct"] = r(100 * alto_ca, 0)
        cx = [x[3] for x in mejores if x[3]]
        if cx:
            t["posicion_personaje"] = [r(100 * np.mean([c[0] for c in cx]), 0), r(100 * np.mean([c[1] for c in cx]), 0)]
        medido = _plano_por_tamano(alto_ca, alto_pj, n_pj)
        clip = t.get("plano_clip")
        if clip in ("negro", "texto en pantalla") and (t.get("plano_clip_conf") or 0) > 0.5:
            t["plano"] = clip
        elif clip == "plano aéreo" and (t.get("plano_clip_conf") or 0) > 0.4 and alto_pj < 0.35:
            t["plano"] = "plano aéreo"
        elif medido:
            t["plano"] = medido
        else:
            t["plano"] = "plano general (sin personaje)"
        t["plano_fuente"] = "medido" if medido else "clip"
    cap.release()


# ----------------------------------------------------------------- imagenes
def _frame(cap, f, w):
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, f))
    ok, fr = cap.read()
    if not ok:
        return None
    h = int(round(w * fr.shape[0] / fr.shape[1]))
    return cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA)


def imagenes(proxy, tomas, efectos, out):
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(out, "miniaturas"), exist_ok=True)
    os.makedirs(os.path.join(out, "hojas"), exist_ok=True)
    os.makedirs(os.path.join(out, "efectos"), exist_ok=True)
    cap = cv2.VideoCapture(proxy)
    TW = 200
    for t in tomas:
        im = _frame(cap, (t["f0"] + t["f1"]) // 2, 180)
        if im is not None:
            cv2.imwrite(os.path.join(out, "miniaturas", "toma_%03d.jpg" % t["n"]), im, [cv2.IMWRITE_JPEG_QUALITY, 82])
    f_t, f_b = fuente(17, True), fuente(15)
    POR_HOJA = 6
    for h0 in range(0, len(tomas), POR_HOJA):
        filas = []
        for t in tomas[h0:h0 + POR_HOJA]:
            a, b = t["f0"], t["f1"]
            ims = [_frame(cap, f, TW) for f in (a + 1, (a + b) // 2, b - 2)]
            ims = [x for x in ims if x is not None]
            if not ims:
                continue
            TH = ims[0].shape[0]
            ims = [cv2.resize(x, (TW, TH)) for x in ims]
            fila = cv2.cvtColor(np.hstack(ims), cv2.COLOR_BGR2RGB)
            panel = Image.new("RGB", (380, TH), (28, 28, 32))
            d = ImageDraw.Draw(panel)
            lin = ["%.2f–%.2f s  (%.2f s)" % (t["inicio"], t["fin"], t["duracion"]),
                   "Plano: %s · %s pj · cara %s%%" % (t.get("plano", "?"), t.get("personajes_n", "?"), t.get("alto_cara_pct", "?")),
                   "Cámara: %s%s" % (t["camara"], " + temblor" if t["temblor"] else ""),
                   "Zoom %+.1f%% · paneo %.0f/%.0f%%" % (t["zoom_total_pct"], t["paneo_x_pct"], t["paneo_y_pct"]),
                   "%s · %s · %s" % (t.get("lugar", ""), t.get("hora", ""), t.get("ambiente", "")),
                   "Entra con: %s" % t.get("transicion_entrada", "inicio")]
            texto = t.get("texto", "")
            while texto and len(lin) < 10:
                lin.append(texto[:40]); texto = texto[40:]
            d.text((10, 8), "TOMA %d" % t["n"], font=f_t, fill=(255, 210, 80))
            for li, s in enumerate(lin):
                d.text((10, 34 + li * 21), s, font=f_b, fill=(235, 235, 235) if li < 6 else (160, 220, 255))
            filas.append(np.hstack([fila, np.array(panel)]))
        if filas:
            wmax = max(f.shape[1] for f in filas)
            filas = [np.pad(f, ((0, 4), (0, wmax - f.shape[1]), (0, 0))) for f in filas]
            Image.fromarray(np.vstack(filas)).save(os.path.join(out, "hojas", "hoja_%02d.jpg" % (h0 // POR_HOJA + 1)), quality=85)
    for e in efectos[:60]:
        a, b = e["f0"], max(e["f0"] + 1, e["f1"])
        fr = [_frame(cap, int(f), 160) for f in np.linspace(max(0, a - 2), b + 2, 4)]
        fr = [x for x in fr if x is not None]
        if fr:
            hh = fr[0].shape[0]
            cv2.imwrite(os.path.join(out, "efectos", "efecto_%02d.jpg" % e["n"]), np.hstack([cv2.resize(x, (160, hh)) for x in fr]),
                        [cv2.IMWRITE_JPEG_QUALITY, 82])
    cap.release()
