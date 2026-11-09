# Crea partes.json en la carpeta de un personaje exportado: el nombre real (de Roblox Studio) de cada grupo del .obj,
# las piezas que no se exportaron (invisibles o tapadas por ropa en capas) y si cada accesorio es ropa en capas.
# armar_rig_r15_auto.py lo lee solo: asi no adivina piezas por posicion (falla con ninas, cuerpos angostos o piezas ocultas).
#
# Uso:  py Herramientas/roblox/partes_json.py datos.json "NombreEnStudio=Personajes/Pueblo_NPC/Carpeta" [...]
#   datos.json = lo que devuelve _G.CL_datos() de studio_personajes.luau (puede ser el archivo de texto tal cual).
import json, os, sys


def grupos_obj(ruta):
    V, G, orden, cur = [], {}, [], None
    for l in open(ruta, encoding="utf-8", errors="ignore"):
        if l.startswith("v "):
            V.append(tuple(map(float, l.split()[1:4])))
        elif l.startswith("g "):
            cur = l[2:].strip(); G[cur] = set(); orden.append(cur)
        elif l.startswith("f ") and cur:
            for t in l.split()[1:]:
                G[cur].add(int(t.split("/")[0]))
    cen = {}
    for g in orden:
        ps = [V[i - 1] for i in G[g]] or [(0, 0, 0)]
        cen[g] = tuple((min(p[k] for p in ps) + max(p[k] for p in ps)) / 2 for k in range(3))
    return orden, cen


def hacer(info, carpeta, nombre):
    objs = [f for f in os.listdir(carpeta) if f.lower().endswith(".obj")]
    if not objs:
        return "SIN .obj en " + carpeta
    orden, cen = grupos_obj(os.path.join(carpeta, objs[0]))
    P = {n: tuple(v) for n, v in info["cuerpo"].items()}
    cuerpo = [g for g in orden if not g.lower().startswith("handle")]
    handles = [g for g in orden if g.lower().startswith("handle")]
    # se resta el centro de cada lado: sirve aunque el personaje se haya movido despues de exportarlo
    co = [sum(cen[g][k] for g in cuerpo) / len(cuerpo) for k in range(3)]
    cs = [sum(p[k] for p in P.values()) / len(P) for k in range(3)]
    if len(cuerpo) != len(P):            # faltan piezas en el OBJ: el centro no es comparable, usar posicion directa
        co, cs = [0, 0, 0], [0, 0, 0]
    pares = sorted((sum((cen[g][k] - co[k] - (P[n][k] - cs[k])) ** 2 for k in range(3)) ** 0.5, g, n)
                   for g in cuerpo for n in P)
    asig, usadas = {}, set()
    for d, g, n in pares:
        if g in asig or n in usadas:
            continue
        asig[g] = (n, d); usadas.add(n)
    faltan = [n for n in P if n not in usadas]
    faltan += [n for n in ("Head", "UpperTorso", "LowerTorso", "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperArm",
                           "LeftLowerArm", "LeftHand", "RightUpperLeg", "RightLowerLeg", "RightFoot", "LeftUpperLeg",
                           "LeftLowerLeg", "LeftFoot") if n not in P]            # invisibles en Studio
    if len(info["accs"]) != len(handles):
        return "NO COINCIDEN accesorios (%d en Studio, %d en el OBJ): %s" % (len(info["accs"]), len(handles), carpeta)
    grupos = [{"grupo": g, "tipo": "cuerpo", "nombre": asig[g][0], "dist": round(asig[g][1], 3)} for g in orden if g in asig]
    grupos += [{"grupo": h, "tipo": "acc", "nombre": a["nombre"], "accType": a["accType"], "wrap": a["wrap"]}
               for h, a in zip(handles, info["accs"])]
    mira = info.get("mira") or [0, -1]
    out = {"fuente": "Roblox Studio: cuerpo empatado por posicion de cada pieza; accesorios en el orden del OBJ",
           "personaje": nombre,
           "orientacion": "en Studio mira a -Z -> voltear" if mira[1] < 0 else "en Studio mira a +Z -> no_voltear",
           "faltan": faltan, "grupos": grupos}
    json.dump(out, open(os.path.join(carpeta, "partes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    peor = max(v[1] for v in asig.values())
    return "OK %-40s piezas=%d faltan=%s peor_dist=%.3f accesorios=%d%s" % (
        carpeta, len(asig), faltan, peor, len(handles), "  <- REVISAR (dist alta)" if peor > 0.3 else "")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__ or "Uso: py partes_json.py datos.json \"NombreStudio=carpeta\" ...")
    raw = open(sys.argv[1], encoding="utf-8").read()
    datos = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    for par in sys.argv[2:]:
        nombre, carpeta = par.split("=", 1)
        if nombre not in datos:
            print("NO ESTA EN STUDIO:", nombre); continue
        print(hacer(datos[nombre], carpeta, nombre))
