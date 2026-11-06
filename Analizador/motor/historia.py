# Estructura de la historia a partir de la narracion: gancho, giros, preguntas, final y llamados a la accion.
# Lo automatico es una primera pasada; Claude completa el analisis leyendo para_claude.md (ver LEEME del Analizador).
import os, re
from comun import r, mmss

GIROS = ["pero", "de repente", "sin embargo", "hasta que", "lo que no sabía", "lo que no sabian", "nadie", "nunca",
         "en ese momento", "de pronto", "resulta que", "al final", "entonces", "sin saber", "lo peor", "y ahí",
         "but", "suddenly", "until", "nobody", "never", "turns out", "then"]
GANCHO = ["?", "¿", "nunca", "nadie", "secreto", "si ves", "no creerás", "imagina", "qué pasaría", "regla", "prohibido",
          "este es", "esta es", "hoy", "nunca debes", "what if", "never", "secret"]
CTA = ["suscr", "like", "comenta", "parte 2", "segunda parte", "sígueme", "siguiente video", "campanita", "subscribe", "comment", "part 2"]


def analizar(segmentos, palabras, dur):
    if not segmentos:
        return {"hay_narracion": False}
    texto = " ".join(s["texto"] for s in segmentos)
    low = texto.lower()
    giros = []
    for s in segmentos:
        sl = " " + s["texto"].lower() + " "
        for g in GIROS:
            if re.search(r"(?<!\w)" + re.escape(g) + r"(?!\w)", sl):
                giros.append({"t": s["t0"], "pct": r(100 * s["t0"] / max(1e-6, dur), 0), "palabra": g, "frase": s["texto"]})
                break
    gancho = segmentos[0]
    marcas_gancho = [g for g in GANCHO if g in gancho["texto"].lower()]
    preguntas = texto.count("?")
    exclam = texto.count("!")
    cta = [{"t": s["t0"], "frase": s["texto"]} for s in segmentos if any(c in s["texto"].lower() for c in CTA)]
    final = segmentos[-1]
    tercio = [0, 0, 0]
    for w in palabras:
        tercio[min(2, int(3 * w["t0"] / max(1e-6, dur)))] += 1
    return {
        "hay_narracion": True,
        "gancho": {"frase": gancho["texto"], "fin_s": gancho["t1"], "marcas": marcas_gancho},
        "preguntas": preguntas, "exclamaciones": exclam,
        "preguntas_por_minuto": r(preguntas / max(1e-6, dur) * 60, 1),
        "giros": giros[:40], "giros_por_minuto": r(len(giros) / max(1e-6, dur) * 60, 1),
        "llamados_accion": cta,
        "final": {"frase": final["texto"], "termina_en_pregunta": final["texto"].strip().endswith("?"),
                  "termina_en_suspenso": final["texto"].strip().endswith("...")},
        "palabras_por_tercio": tercio,
        "palabras_unicas": len(set(re.findall(r"\w+", low))),
    }


def para_claude(out, nombre, creador, datos):
    """documento para que Claude revise la historia y los efectos con las imagenes (entrenamiento cualitativo)."""
    L = ["# Revisión de Claude — %s (%s)" % (nombre, creador), "",
         "> Mirar `hojas/`, `efectos/` y este texto. Escribir el resultado en `notas_claude.md` (misma carpeta)",
         "> y pasar las reglas que se repiten a `Analizador/Estilos/%s_notas.md`." % creador, "",
         "## Narración con tiempos"]
    for s in datos["audio"].get("segmentos", []):
        L.append("- `%s` %s" % (mmss(s["t0"]), s["texto"]))
    L += ["", "## Tomas", "", "| # | Inicio | Dur | Plano | Cámara | Entra con | Texto |", "|---|---|---|---|---|---|---|"]
    for t in datos["tomas"]:
        L.append("| %d | %s | %.2f | %s | %s%s | %s | %s |" % (t["n"], mmss(t["inicio"]), t["duracion"], t.get("plano", ""), t["camara"],
                                                         " + temblor" if t["temblor"] else "", t.get("transicion_entrada", ""), t.get("texto", "")[:60]))
    ef = datos.get("efectos", [])
    if ef:
        L += ["", "## Momentos con posible efecto (ver `efectos/efecto_NN.jpg`)"]
        L += ["- %d. `%s` %s (%.2f s)" % (e["n"], mmss(e["inicio"]), e["tipo"], e["duracion"]) for e in ef[:60]]
    L += ["", "## Para completar (notas_claude.md)",
          "1. **Gancho** (0–3 s): ¿qué se ve y qué se dice? ¿por qué engancha?",
          "2. **Estructura**: planteamiento → problema → escalada → giro → final (con segundos).",
          "3. **Misterio / retención**: ¿qué pregunta deja abierta y cuándo la resuelve?",
          "4. **Personajes**: quiénes salen, cómo se presentan, cuánto tiempo en cámara.",
          "5. **Cámara**: patrones que se repiten (ej. primer plano en cada revelación, dron al cambiar de lugar).",
          "6. **Efectos visuales**: cuáles son de verdad (hojas, humo, destellos, líneas de velocidad, emojis) y cuándo los usa.",
          "7. **Subtítulos**: estilo exacto (fuente, colores, animación, palabras clave resaltadas).",
          "8. **Sonido**: música, efectos, silencios dramáticos.",
          "9. **Fórmula en 5 reglas** para copiar en nuestras animaciones."]
    open(os.path.join(out, "para_claude.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
