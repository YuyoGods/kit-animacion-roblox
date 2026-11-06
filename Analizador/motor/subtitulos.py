# Lee los textos quemados en el video (OCR) y deduce el estilo de los subtitulos:
# palabras por subtitulo, posicion, tamano, colores, resaltado, mayusculas, animacion de entrada y sincronia con la voz.
import difflib, re
from collections import Counter
import numpy as np
import cv2
from comun import log, r

_OCR = {}
MUESTRAS_POR_S = 6


def _lector():
    if not _OCR:
        import torch, easyocr
        _OCR["r"] = easyocr.Reader(["es", "en"], gpu=torch.cuda.is_available(), verbose=False)
    return _OCR["r"]


def _norm(t):
    return re.sub(r"[^0-9a-záéíóúñü]+", "", t.lower())


def _color_nombre(h, s, v):
    if s < 60:
        return "blanco" if v > 170 else "gris"
    if h < 8 or h >= 165:
        return "rojo"
    if h < 18:
        return "naranja"
    if h < 36:
        return "amarillo"
    if h < 85:
        return "verde"
    if h < 100:
        return "cian"
    if h < 130:
        return "azul"
    return "morado/rosa"


def _colores(crop):
    """colores del texto (relleno), si hay una segunda palabra resaltada y si tiene contorno oscuro."""
    if crop.size == 0:
        return None
    hsv_im = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    v = hsv_im[..., 2]
    oscuro_m = (v < 70).astype(np.uint8)
    oscuro = float((v < 60).mean())
    # relleno del texto = pixeles claros pegados al contorno oscuro (asi no se cuela el cielo o el fondo)
    cerca = cv2.dilate(oscuro_m, np.ones((5, 5), np.uint8)) > 0
    m_txt = (v > 150) & cerca
    if m_txt.sum() < 30:
        m_txt = v > 150
    hsv = hsv_im.reshape(-1, 3)
    claro = hsv[m_txt.ravel()]
    if len(claro) < 20:
        return {"relleno": None, "resaltado": None, "contorno_oscuro": oscuro > 0.18}
    nombres = Counter(_color_nombre(int(h), int(s), int(v)) for h, s, v in claro[:: max(1, len(claro) // 1500)])
    tot = sum(nombres.values())
    orden = nombres.most_common()
    relleno = orden[0][0]
    resaltado = orden[1][0] if len(orden) > 1 and orden[1][1] / tot >= 0.15 and orden[1][0] != "gris" else None
    return {"relleno": relleno, "resaltado": resaltado, "contorno_oscuro": oscuro > 0.18}


def _bloques(res, W, H):
    """agrupa cajas de OCR en bloques de texto (lineas cercanas)."""
    cajas = []
    for pts, txt, conf in res:
        if conf < 0.35 or not re.search(r"\w", txt):
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cajas.append({"x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys), "t": txt.strip(), "c": conf})
    cajas.sort(key=lambda c: (c["y0"], c["x0"]))
    bloques = []
    for c in cajas:
        h = c["y1"] - c["y0"]
        for b in bloques:
            if c["y0"] - b["y1"] < 0.7 * h and min(c["x1"], b["x1"]) - max(c["x0"], b["x0"]) > -0.5 * W:
                b["cajas"].append(c)
                b["x0"], b["x1"] = min(b["x0"], c["x0"]), max(b["x1"], c["x1"])
                b["y0"], b["y1"] = min(b["y0"], c["y0"]), max(b["y1"], c["y1"])
                break
        else:
            bloques.append({"cajas": [c], "x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"]})
    for b in bloques:
        filas = []
        for c in sorted(b["cajas"], key=lambda c: (c["y0"], c["x0"])):
            if filas and abs(c["y0"] - filas[-1][0]["y0"]) < 0.5 * (c["y1"] - c["y0"]):
                filas[-1].append(c)
            else:
                filas.append([c])
        b["lineas"] = len(filas)
        b["texto"] = " / ".join(" ".join(c["t"] for c in sorted(f, key=lambda c: c["x0"])) for f in filas)
        b["alto_linea"] = float(np.median([c["y1"] - c["y0"] for c in b["cajas"]]))
        b["yc"] = (b["y0"] + b["y1"]) / 2 / H
        b["xc"] = (b["x0"] + b["x1"]) / 2 / W
        b["ancho"] = (b["x1"] - b["x0"]) / W
    return bloques


def _iguales(a, b):
    na, nb = _norm(a), _norm(b)
    return bool(na) and (na == nb or difflib.SequenceMatcher(None, na, nb).ratio() > 0.8)


def analizar(proxy, fps, nf, palabras):
    lector = _lector()
    cap = cv2.VideoCapture(proxy)
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    paso = max(1, int(round(fps / MUESTRAS_POR_S)))
    muestras = []
    for i in range(nf):
        if i % paso:
            if not cap.grab():
                break
            continue
        ok, fr = cap.read()
        if not ok:
            break
        bl = _bloques(lector.readtext(fr), W, H)
        for b in bl:
            pad = int(0.15 * b["alto_linea"])
            crop = fr[max(0, int(b["y0"]) - pad):int(b["y1"]) + pad, max(0, int(b["x0"]) - pad):int(b["x1"]) + pad]
            b["color"] = _colores(crop)
        muestras.append({"f": i, "t": i / fps, "bloques": bl})
    cap.release()
    n = len(muestras)
    if not n:
        return {"hay_subtitulos": False}

    # textos fijos (logo, marca de agua, nombre del canal): mismo texto y lugar en muchas muestras
    cuenta = Counter()
    for s in muestras:
        for b in s["bloques"]:
            cuenta[(_norm(b["texto"])[:20], round(b["yc"] * 25), round(b["xc"] * 10))] += 1
    fijos = {k for k, v in cuenta.items() if v >= max(4, 0.35 * n) and k[0]}
    for s in muestras:
        s["bloques"] = [b for b in s["bloques"] if (_norm(b["texto"])[:20], round(b["yc"] * 25), round(b["xc"] * 10)) not in fijos]

    # franja de subtitulos: la altura donde mas textos distintos aparecen
    hist = Counter()
    for s in muestras:
        for b in s["bloques"]:
            hist[round(b["yc"] * 50)] += 1
    if not hist:
        return {"hay_subtitulos": False, "textos_fijos": [k[0] for k in fijos]}
    modo = max(hist.items(), key=lambda kv: sum(hist.get(kv[0] + d, 0) for d in (-2, -1, 0, 1, 2)))[0] / 50
    banda = (modo - 0.09, modo + 0.09)

    # eventos de subtitulo (texto que se mantiene) y otros textos en pantalla
    subs, otros = [], []
    actual = None
    for s in muestras:
        en_banda = [b for b in s["bloques"] if banda[0] <= b["yc"] <= banda[1]]
        ids = {id(b) for b in en_banda}
        fuera = [b for b in s["bloques"] if id(b) not in ids]
        for b in fuera:
            if otros and _iguales(otros[-1]["texto"], b["texto"]) and s["t"] - otros[-1]["fin"] < 0.6:
                otros[-1]["fin"] = s["t"] + 1 / MUESTRAS_POR_S
            else:
                otros.append({"inicio": s["t"], "fin": s["t"] + 1 / MUESTRAS_POR_S, "texto": b["texto"], "y_pct": round(100 * b["yc"]),
                              "alto_pct": r(100 * b["alto_linea"] / H, 1)})
        texto = " / ".join(b["texto"] for b in sorted(en_banda, key=lambda b: b["yc"]))
        if not texto:
            actual = None
            continue
        if actual is not None and _iguales(actual["texto"], texto):
            actual["fin"] = s["t"] + 1 / MUESTRAS_POR_S
            actual["muestras"].append((s, en_banda))
        else:
            actual = {"inicio": s["t"], "fin": s["t"] + 1 / MUESTRAS_POR_S, "texto": texto, "muestras": [(s, en_banda)]}
            subs.append(actual)

    eventos = []
    for e in subs:
        bls = [b for _, bb in e["muestras"] for b in bb]
        textos = Counter(b["texto"] for b in bls)
        txt = textos.most_common(1)[0][0]
        voz = [w for w in palabras if e["inicio"] - 0.12 <= (w["t0"] + w["t1"]) / 2 < e["fin"]]
        cols = [b["color"] for b in bls if b.get("color")]
        rell = Counter(c["relleno"] for c in cols if c["relleno"])
        res = Counter(c["resaltado"] for c in cols if c["resaltado"])
        letras = [ch for ch in txt if ch.isalpha()]
        eventos.append({
            "inicio": r(e["inicio"], 2), "fin": r(e["fin"], 2), "duracion": r(e["fin"] - e["inicio"], 2), "texto": txt,
            "palabras_ocr": len([p for p in re.split(r"[\s/]+", txt) if re.search(r"\w", p)]),
            "palabras_voz": len(voz),
            "lineas": int(np.median([b["lineas"] for b in bls])),
            "y_pct": r(100 * np.median([b["yc"] for b in bls]), 1),
            "x_pct": r(100 * np.median([b["xc"] for b in bls]), 1),
            "ancho_pct": r(100 * np.median([b["ancho"] for b in bls]), 1),
            "alto_letra_pct": r(100 * np.median([b["alto_linea"] for b in bls]) / H, 2),
            "relleno": rell.most_common(1)[0][0] if rell else None,
            "resaltado": res.most_common(1)[0][0] if res and sum(res.values()) >= 0.3 * max(1, len(cols)) else None,
            "contorno_oscuro": bool(np.mean([c["contorno_oscuro"] for c in cols]) > 0.5) if cols else None,
            "mayusculas": bool(letras) and sum(ch.isupper() for ch in letras) / len(letras) > 0.8,
            "desfase_voz_ms": int(round((e["inicio"] - voz[0]["t0"]) * 1000)) if voz else None,
        })

    # animacion de entrada (pop): mirar fotograma a fotograma los primeros subtitulos
    # fotograma a fotograma en los primeros 12 subtitulos: inicio exacto y animacion de entrada (pop)
    pops, desfases_exactos = [], []
    cap = cv2.VideoCapture(proxy)
    y0, y1 = int(max(0, (banda[0] - 0.03) * H)), int(min(H, (banda[1] + 0.03) * H))
    for e in eventos[:12]:
        f0 = int(e["inicio"] * fps)
        alturas = []
        primero = None
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, f0 - paso))
        for f in range(max(0, f0 - paso), f0 + int(0.35 * fps)):
            ok, fr = cap.read()
            if not ok:
                break
            bl = _bloques(lector.readtext(fr[y0:y1]), W, H)
            h = max([b["alto_linea"] for b in bl], default=0)
            if h > 0 and primero is None:
                primero = f
            if primero is not None:
                alturas.append(h)
        if primero is not None:
            e["inicio_exacto"] = r(primero / fps, 3)
            voz = [w for w in palabras if e["inicio"] - 0.4 <= w["t0"] < e["fin"]]
            if voz:
                desfases_exactos.append(int(round((primero / fps - voz[0]["t0"]) * 1000)))
        al = [a for a in alturas if a > 0]
        if len(al) >= 4:
            final = np.median(al[-3:])
            pops.append(bool(max(al[:2]) > 1.08 * final or min(al[:2]) < 0.85 * final))
    cap.release()

    estilo = {}
    if eventos:
        pal = [e["palabras_voz"] or e["palabras_ocr"] for e in eventos]
        med = float(np.median(pal))
        modo_txt = ("palabra por palabra" if med <= 1.3 else "grupos de 2-3 palabras" if med <= 3.5
                    else "frases cortas (4-7 palabras)" if med <= 7 else "frases completas")
        cubiertas = 0
        for w in palabras:
            if any(e["inicio"] - 0.2 <= w["t0"] <= e["fin"] + 0.2 for e in eventos):
                cubiertas += 1
        rell = Counter(e["relleno"] for e in eventos if e["relleno"])
        resal = Counter(e["resaltado"] for e in eventos if e["resaltado"])
        desf = [e["desfase_voz_ms"] for e in eventos if e["desfase_voz_ms"] is not None]
        # color de resaltado = el segundo color mas comun (como relleno o resaltado) en al menos 10% de los subtitulos
        todos = Counter()
        for e in eventos:
            for c_ in {e["relleno"], e["resaltado"]} - {None}:
                todos[c_] += 1
        principal = rell.most_common(1)[0][0] if rell else None
        otros_c = [(c_, k) for c_, k in todos.most_common() if c_ != principal and c_ != "gris" and k >= 0.1 * len(eventos)]
        col_res = otros_c[0][0] if otros_c else None
        estilo = {
            "modo": modo_txt, "palabras_por_subtitulo": r(med, 1),
            "duracion_subtitulo_s": r(np.median([e["duracion"] for e in eventos]), 2),
            "subtitulos_por_minuto": r(len(eventos) / max(1e-6, nf / fps) * 60, 1),
            "posicion_y_pct": r(np.median([e["y_pct"] for e in eventos]), 1),
            "posicion": "abajo" if modo > 0.66 else "centro" if modo > 0.36 else "arriba",
            "alto_letra_pct": r(np.median([e["alto_letra_pct"] for e in eventos]), 2),
            "ancho_pct": r(np.median([e["ancho_pct"] for e in eventos]), 1),
            "lineas": int(np.median([e["lineas"] for e in eventos])),
            "color_relleno": rell.most_common(1)[0][0] if rell else None,
            "colores": dict(rell.most_common(4)),
            "resaltado_pct": r(100 * sum(1 for e in eventos if col_res and col_res in (e["relleno"], e["resaltado"])) / len(eventos), 0),
            "color_resaltado": col_res,
            "contorno_oscuro_pct": r(100 * np.mean([bool(e["contorno_oscuro"]) for e in eventos]), 0),
            "mayusculas_pct": r(100 * np.mean([e["mayusculas"] for e in eventos]), 0),
            "aparece_vs_voz_ms": int(np.median(desfases_exactos)) if desfases_exactos else (int(np.median(desf)) if desf else None),
            "voz_cubierta_pct": r(100 * cubiertas / len(palabras), 0) if palabras else None,
            "entrada_pop_pct": r(100 * np.mean(pops), 0) if pops else None,
        }
    log("    subtitulos: %d eventos, %d otros textos" % (len(eventos), len(otros)))
    return {"hay_subtitulos": bool(eventos), "estilo": estilo, "eventos": eventos,
            "otros_textos": [o for o in otros if o["fin"] - o["inicio"] >= 0.3][:80],
            "textos_fijos": sorted({k[0] for k in fijos}), "banda_y_pct": [r(100 * banda[0], 0), r(100 * banda[1], 0)]}
