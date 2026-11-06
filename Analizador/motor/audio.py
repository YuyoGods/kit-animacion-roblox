# Audio: narracion con tiempos por palabra (Whisper en GPU), volumen (LUFS), efectos de sonido, musica y ritmo.
import re, subprocess
import numpy as np
from comun import log, r

_W = {}


def _whisper():
    if not _W:
        import torch  # noqa: F401  (deja disponibles las DLL de CUDA)
        from faster_whisper import WhisperModel
        try:
            _W["m"] = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
            _W["dev"] = "cuda"
        except Exception:
            _W["m"] = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
            _W["dev"] = "cpu"
    return _W["m"]


def transcribir(audio, idioma=None):
    if len(audio) < 16000 * 0.5:
        return [], [], None
    m = _whisper()
    segs, info = m.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=True, beam_size=5)
    segs = list(segs)
    # energia de cada frase: Whisper a veces "inventa" frases en silencios (ej. "¡Suscríbete al canal!")
    def db(t0, t1):
        x = audio[int(t0 * 16000):int(t1 * 16000)]
        return 20 * np.log10(max(1e-6, float(np.sqrt(np.mean(x ** 2))) if len(x) else 1e-6))
    niveles = [db(s.start, s.end) for s in segs]
    ref = float(np.median(niveles)) if niveles else 0.0
    palabras, segmentos, descartadas = [], [], []
    for s, nv in zip(segs, niveles):
        probs = [w.probability for w in (s.words or [])]
        rapidez = len(probs) / max(0.05, s.end - s.start)          # palabras/s imposibles = invento
        if (nv < ref - 18 or (probs and np.mean(probs) < 0.35) or s.no_speech_prob > 0.8 or s.avg_logprob < -1.0
                or (s.avg_logprob < -0.45 and rapidez > 5.5)):
            descartadas.append({"t0": r(s.start, 2), "texto": s.text.strip(), "motivo": "silencio/alucinación"})
            continue
        palabras += [{"t0": r(w.start, 2), "t1": r(w.end, 2), "p": w.word.strip(), "prob": r(w.probability, 2)} for w in (s.words or [])]
        segmentos.append({"t0": r(s.start, 2), "t1": r(s.end, 2), "texto": s.text.strip()})
    return palabras, segmentos, {"idioma": info.language, "prob": r(info.language_probability, 2), "frases_descartadas": descartadas}


def sonoridad(ruta):
    """volumen integrado (LUFS), rango (LRA) y pico verdadero con el filtro ebur128 de FFmpeg."""
    p = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", ruta, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = p.stderr[p.stderr.rfind("Summary:"):] if "Summary:" in p.stderr else ""

    def num(pat):
        mm = re.search(pat, txt)
        return float(mm.group(1)) if mm else None
    return {"lufs": num(r"I:\s+(-?[\d.]+) LUFS"), "lra": num(r"LRA:\s+(-?[\d.]+) LU"), "pico_dbtp": num(r"Peak:\s+(-?[\d.]+) dBFS")}


def sonidos(audio, palabras, dur, sr=16000):
    import librosa
    out = {}
    if len(audio) < sr:
        return out
    hop = 512
    env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=sr, hop_length=hop, units="frames", backtrack=False)
    t_on = librosa.frames_to_time(on, sr=sr, hop_length=hop)
    fuerza = env[on] if len(on) else np.array([])
    # tramos con voz
    habla = np.zeros(int(dur * 100) + 2, bool)
    for w in palabras:
        habla[int(max(0, w["t0"] - 0.05) * 100):int((w["t1"] + 0.05) * 100)] = True

    def con_voz(t):
        i = int(t * 100)
        return 0 <= i < len(habla) and habla[i]
    umbral = float(np.percentile(fuerza, 70)) if len(fuerza) else 0
    sfx = [r(t, 2) for t, f in zip(t_on, fuerza) if f >= umbral and not con_voz(t)]
    out["golpes_sonido"] = sfx
    out["golpes_por_minuto"] = r(len(sfx) / max(1e-6, dur) * 60, 1)
    # fondo sonoro (musica / ambiente) en los silencios de la voz
    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    tt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    sin_voz = np.array([not con_voz(t) for t in tt])
    if sin_voz.any():
        out["fondo_sonoro_pct"] = r(100 * float((db[sin_voz] > -42).mean()), 0)
        out["nivel_fondo_db"] = r(float(np.median(db[sin_voz])), 1)
    if (~sin_voz).any():
        out["nivel_voz_db"] = r(float(np.median(db[~sin_voz])), 1)
    # parte armonica (musica) vs percusiva/ruido en los silencios
    try:
        idx = np.where(np.repeat(sin_voz, hop)[:len(audio)])[0]
        y_s = audio[idx][: sr * 60]
        if len(y_s) > sr * 2:
            h, p = librosa.effects.hpss(y_s)
            eh, ep = float(np.sum(h ** 2)), float(np.sum(p ** 2))
            out["armonico_en_silencios_pct"] = r(100 * eh / max(1e-9, eh + ep), 0)
    except Exception:
        pass
    try:
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr, hop_length=hop)
        out["bpm_estimado"] = r(float(np.atleast_1d(tempo)[0]), 0)
    except Exception:
        pass
    m = out.get("armonico_en_silencios_pct")
    out["musica_probable"] = bool(m is not None and m > 65 and out.get("fondo_sonoro_pct", 0) > 50)   # EP001: viento de ambiente = 57
    return out


def voz(palabras, dur):
    if not palabras:
        return {"hay_voz": False}
    hueco = [palabras[i + 1]["t0"] - palabras[i]["t1"] for i in range(len(palabras) - 1)]
    pausas = [h for h in hueco if h > 0.5]
    t_habla = sum(w["t1"] - w["t0"] for w in palabras)
    return {"hay_voz": True, "palabras": len(palabras),
            "palabras_por_s": r(len(palabras) / max(1e-6, dur), 2),
            "palabras_por_s_hablando": r(len(palabras) / max(1e-6, palabras[-1]["t1"] - palabras[0]["t0"]), 2),
            "primera_palabra_s": palabras[0]["t0"], "ultima_palabra_s": palabras[-1]["t1"],
            "pausas_por_minuto": r(len(pausas) / max(1e-6, dur) * 60, 1),
            "pausa_mas_larga_s": r(max(hueco), 2) if hueco else 0,
            "tiempo_hablando_pct": r(100 * t_habla / max(1e-6, dur), 0)}
