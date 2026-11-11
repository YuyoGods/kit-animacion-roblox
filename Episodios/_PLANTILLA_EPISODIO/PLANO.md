# EP### — Plano de construcción

> Se llena **después de que el usuario aprueba el guion** y **antes** de la voz y de animar. Sirve para que al animar ya exista todo lo que dice la voz (regla "lo que se dice, se hace y se ve") y no se pierda tiempo.
> Fuentes: el guion aprobado (`narracion.txt`, una línea = una toma), `MI_CANAL.md` (reparto A/B/C), `docs/10_CATALOGO.md` (lo que ya existe: objetos, efectos, gestos, caras, personajes, lugares), `docs/09_RECETA_SIMPLE.md` (tipos de toma).
> Sin storyboard (decisión del usuario, 2026-11-08): este plano lo reemplaza.
> **Cada cosa que se modela lleva su referencia de internet** (sección 0) y se construye **por lotes** con foto de prueba comparada contra la referencia. Ejemplo completo: `Episodios/EP009_El_Sol_Cuesta_Mil_Pesos/PLANO.md` (si existe en tu PC).

## 0. Referencias de internet (rasgos que se copian)
| Cosa | Referencia (link) | Rasgos clave que se copian |
|---|---|---|
| | | |

## 1. Lugares
| Lugar | Líneas | Existe en el mapa (`docs/04`) / hay que construir | Hora (día/tarde/noche) | Notas |
|---|---|---|---|---|
| | | | | |

## 2. Personajes
| Personaje | Nivel (A/B/C) | Rig listo | Caras/bocas que necesita | Líneas donde sale |
|---|---|---|---|---|
| Sikelpa | A | sí | bocas 21–25 para sus diálogos | |

## 3. Objetos (cada cosa que la voz nombra o que hace falta para entender)
| Objeto | Líneas | Ya existe (`10_CATALOGO`) / modelar nuevo | Referencia (buscar imágenes antes de modelar) | Color que contraste con lo de atrás | ¿Lo agarra alguien? |
|---|---|---|---|---|---|
| | | | | | |

## 4. Efectos, letreros y contadores
| Qué | Línea / palabra | Herramienta (`vfx.*`, `carteles.py`) |
|---|---|---|
| | | |

## 5. Tabla de tomas (una por línea; tipos de `docs/09_RECETA_SIMPLE.md`)
| # | Línea de la voz (resumen) | Tipo (retrato · habla · hombro · traslado · inserto · pueblo) | Quién | Cara / boca | Objeto o efecto | Corte extra en la palabra |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## 6. Lo que hay que hacer ANTES de animar (orden)
- [ ] Modelar / traer lo nuevo de las secciones 1 y 3 **por lotes** (lo de una escena junto), con foto de prueba de cada cosa comparada contra su referencia de la sección 0
- [ ] Caras o bocas que falten (sección 2)
- [ ] Revisar que cada objeto se distinga (`revisar_objetos.py` con una foto)
- [ ] Voz aprobada → `recortar_pausas.py` → `tomas_desde_voz.py`
- [ ] Animar con `tomas_simples.py` (lista de la sección 5) + caminar/gestos solo donde la línea lo pide

## 7. Tiempo estimado
| Parte | Estimado | Real |
|---|---|---|
| Construir lo nuevo | | |
| Animar (tomas simples) | | |
| Revisión + borrador | | |
| Vista previa (render) | | |
