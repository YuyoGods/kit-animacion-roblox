# Cambios del kit

> Una entrada por cada actualización que se sube al repositorio (lo más nuevo arriba).
> Si una actualización renombra o mueve archivos compartidos, avisarlo aquí.

## v0.6.0 — 2026-11-11 — Lo que el dueño revisa, Claude ya lo cumple solo

> **Para ti, que recibes esta actualización.** Aquí está, una por una, cada cosa nueva que trae. Todo sale de hacer 7 episodios más (EP006 a EP012) y de las correcciones que el dueño del kit le fue pidiendo a Claude en ese tiempo. Claude ya las conoce y las aplica solo; esta guía es para que **tú** sepas qué va a hacer distinto y por qué.
>
> **No se borra nada tuyo.** Tus personajes, caras, mapas, episodios, `MI_CANAL.md`, `MI_BITACORA.md` y `mi_config.json` quedan igual. Ningún archivo del kit cambió de nombre ni de lugar.

### Qué hacer después de actualizar
1. Corre `py instalar.py` (o dile a Claude «actualiza el kit»). Revisa que todo siga funcionando.
2. **Opcional, música de fondo:** pon una canción en la carpeta `Musica/` y su ruta en tu `mi_config.json` (ver la sección 2).
3. **Opcional, modelo de voz nuevo:** si quieres la voz más actuada, cambia en tu `mi_config.json` la línea `"modelo_voz"` a `"eleven_v4"` (ver la sección 1).
4. Si tienes un episodio a medias con la voz ya recortada, vuelve a correr `recortar_pausas.py` y `tomas_desde_voz.py` para que tenga los huecos cortos nuevos.

---

### 1. Voz en off: sin huecos y con más opciones
- **Huecos más cortos entre frases.** `recortar_pausas.py` ahora deja:

  | Dónde | Antes | Ahora |
  |---|---|---|
  | Entre palabras | hasta 0,2 s | hasta 0,10 s |
  | Después de una coma | 0,3 s | 0,12 s |
  | Al final de cada línea | 0,3–0,4 s | ~0,14 s |
  | Después de "…" | 0,41–0,55 s | 0,2 s |

  Por qué: en EP005, de 2 min 22 s de video, 34 s eran silencio y se sentía lento. Se probaron dos recortes de la misma voz (gratis) y el dueño eligió el de 0,14 s. Viene así por defecto; si quieres otro ritmo, usa `--respiro 0.2` (o el valor que quieras).
- **Modelo `eleven_v4`** (nuevo valor por defecto en `mi_config.ejemplo.json`): la misma voz, pero más actuada. Habla con un poco más de calma. Gastó unos 981 créditos por 2.229 letras.
- **Agregar un gancho al principio sin rehacer toda la voz:** `py Herramientas/audio/voz_elevenlabs.py EP### --anteponer`. Escribes las líneas nuevas arriba en `narracion.txt` y solo se cobran esas. Ojo: después hay que correr `tomas_desde_voz.py` otra vez, porque todas las tomas se recorren.
- **Palabra estirada sin gastar créditos:** si `recortar_pausas.py` avisa que una palabra quedó larga (por ejemplo "detrás" de 0,72 s), `py -X utf8 Herramientas/audio/acortar_palabra.py EP### <segundo_inicio> <segundo_fin> [factor]` la acorta sin cambiar el tono y guarda la versión anterior en `Respaldos/`.
- **El narrador ya no dice onomatopeyas** (¡pop!, ¡boing!, ¡clic!): las pone el efecto de sonido. Si ya tienes una voz aprobada que las dice, `py Herramientas/audio/quitar_onomatopeyas.py EP###` las corta de la voz sin gastar créditos, deja una marca para que el efecto caiga justo ahí y las quita de los subtítulos (`--probar` para ver qué haría).

### 2. Música de fondo (nuevo)
- `Herramientas/audio/musica_fondo.py` pone una canción **desde el primer cuadro hasta el último** del video. Lo usa solo `armar_video.py`.
- Si la canción es más larga que el video, se recorta al final con una salida suave de 1,5 s (no queda pantalla negra con música). Si es más corta, se repite.
- Se oye **por debajo de la voz**: 16 dB más bajita (dato `"musica_fondo_db"`) y mientras habla el narrador baja unos 4 dB más.
- **Cómo activarla:** pon la canción en la carpeta nueva `Musica/` y en tu `mi_config.json` agrega:
  ```json
  "musica_fondo": "Musica/mi_cancion.mp3",
  "musica_fondo_db": -16
  ```
  Si lo dejas vacío, el video sale sin música, como antes.
- La carpeta `Musica/` es **personal**: git no la sube (la música puede tener licencia).
- Para escuchar solo la mezcla sin hacer el video: `py Episodios/EP###/scripts/armar_video.py EP### preview --solo-audio`.
- Si tienes episodios viejos con su propia copia de `armar_video.py`, esas copias no traen música; los episodios nuevos sí (salen de la plantilla nueva).

### 3. Efectos de sonido más limpios
- **Cada efecto suena solo mientras pasa su acción** (el dueño lo marcó como «muy importante»). Muchos sonidos de la librería duran 5–6 s; ahora `armar_video.py` los corta al terminar su toma con un desvanecido suave (0,15–0,6 s), para que no se oiga el corte. Un 5.º dato los acorta más: segundos (`0.6`) o `"hasta:palabra:una"`.
- Los sonidos que dependen de la animación (como el tecleo mientras aparecen letras) van en `audio/efectos_animacion.json` y suenan solo en ese tramo.
- **Pocos efectos:** uno por acción importante (unos 20 en 2 minutos, no 30).
- **Sonidos que cansaron al público:** nada de viento de día (`wind`), nada de aplausos ni multitudes (`applause`, `cheer`) y nada de ladridos (`dog_bark`). El festejo se ve en la animación y lo cubre la música.
- El volumen final queda en −14 LUFS de verdad (antes se quedaba en −15,3).

### 4. Revisión antes de entregar: lo que el dueño siempre corregía, ahora Claude lo revisa solo
- **Lista de cada borrador** (en `docs/05_CAMARAS_Y_TOMAS.md`). Claude la cumple antes de mandarte nada:
  1. Gancho sin huecos en los primeros 8 s (acción en cada segundo, 2–3 cortes por frase).
  2. Ninguna toma con más de ~1 s sin que pase algo.
  3. Lo que se lanza se ve caer.
  4. Nada tapa al personaje (postes, gente, muebles).
  5. Caras con emoción (nunca la de fábrica), y los extras también reaccionan.
  6. Luz de noche que no deslumbra.
  7. Accesorios bien puestos (sombrero, banda, bigote).
  8. Cada personaje con su identidad y sus propios objetos.
  9. Objetos chiquitos que importan (monedas, llaves), grandes y de frente.
  10. Volumen a −14 LUFS.
- **Zona segura de Shorts** (nuevo, `Herramientas/blender/zona_segura.py`): en YouTube Shorts, abajo tapan el título y el botón de suscribirse, y a la derecha están los botones. Caras, burbujas y letreros van centrados en la zona segura (de izquierda a derecha 6–86 %, de arriba abajo 12–70 %).
  - `revisar()` avisa si algo queda fuera.
  - `encuadrar()` calcula dónde poner la cámara para que todo quepa.
  - `reencuadrar()` corrige una cámara ya hecha.
- **Recuerdos sin marco:** los recuerdos (flashbacks) se cuentan como una toma normal, sin marco de nubes. La voz dice que es antes.
- **Letreros grandes:** todo letrero de la historia ocupa al menos 1/3 del ancho del cuadro y nunca se sale del marco.

### 5. Personajes
- **Niños más bajos que los adultos** (nuevo, `Herramientas/blender/alturas.py`). Antes todos medían casi lo mismo. Ahora:
  - Medidas a la coronilla: adulto 5,1 · niño 4,0 · niño chico 3,45.
  - `alturas.escalar(rig, "nino")` escala todo el personaje, con sus accesorios y lo que tenga en la mano.
  - `alturas.fase_paso(...)` ajusta el paso para que los pies no patinen.
  - `tomas_simples.py` ya acerca la cámara según el tamaño, así que la cara sale del mismo tamaño.
  - Quién es niño y quién adulto lo anotas en tu `MI_CANAL.md` (columna *Altura*).
- **Revisar la piel** (nuevo, `Herramientas/blender/revisar_piel.py`): arregla la cabeza bronceada junto a manos y piernas claras. Era un error del rig automático, que pasaba el color dos veces a lineal; `armar_rig_r15_auto.py` ya está corregido. La skill `poner-rig` lo revisa sola. Para tus rigs viejos:
  ```
  blender -b "Personajes/<nivel>/<Nombre>/<Nombre>_R15_Rig.blend" --python Herramientas/blender/revisar_piel.py -- --arreglar
  ```
- **Rig automático:** las capas negras de tela o cuero ya no salen blancas (texturas de material de Roblox × su color), y la opción `no_voltear` ya funciona bien.
- **Modelos que no son R15** (nuevo, `Herramientas/blender/rig_motor6d.py`): ciervos, monstruos o animales con esqueleto propio. Crea un hueso por cada articulación de Studio y trae sus animaciones exactas.
- **Personajes R6** (los viejitos, sin codos ni rodillas): `_G.CL_r6a15` en `Herramientas/roblox/studio_personajes.luau` hace una copia R15 con su ropa, colores, cara y accesorios, y conserva su tamaño. `exportar_obj.ps1 -Espera 25` le da tiempo a Studio de pintar la ropa antes de exportar.
- **Animaciones de Roblox Studio a Blender** (nuevo): bailes, emotes o ataques.
  1. En Studio: `_G.CL_sacarAnim(workspace.MiPersonaje, "Nombre")` (`Herramientas/roblox/sacar_animacion.luau`) la saca a un `.json`.
  2. En Blender: `Herramientas/blender/animacion_roblox.py` la pone en cualquier rig R15 del kit.
  3. Se guardan en la carpeta personal nueva `Personajes/Animaciones/`.
  Solo se pueden bajar animaciones tuyas o de Roblox. Guía completa en `Herramientas/roblox/LEEME.md`.
- **Caras nuevas sin romper tus episodios:** `py Herramientas/armar_secuencia_caras.py --agregar` pone las caras nuevas al final (28, 29…) sin cambiar los números que ya usas.
- **Personajes de una sola historia:** van en `Episodios/EP###/personajes/`, no en `Personajes/`.

### 6. Limpiar residuos de episodios terminados (nuevo)
- Cada episodio deja 2–6 GB de imágenes sueltas. `Herramientas/limpiar_episodio.py` borra `borrador/`, `pruebas/` y los PNG de `fotogramas/`, y deja los MP4 que ya entregaste.
- **Los PNG no se pierden del todo:** antes de borrarlos los guarda comprimidos en `fotogramas/fotogramas.mp4` (~3 % del peso). Si después quieres cambiar una toma, `rehacer_tramo.py` y `armar_video.py` los vuelven a sacar solos.
- Primero hace un **simulacro** (te dice qué borraría y cuánto espacio libera). Solo borra con `--borrar`. Se niega si hay un render en curso o si todavía no existe el MP4.
  ```
  py Herramientas/limpiar_episodio.py EP007            (simulacro)
  py Herramientas/limpiar_episodio.py EP007 --borrar   (de verdad; no se puede deshacer)
  ```
- Al entregarte una vista previa aprobada, Claude te va a preguntar: «¿Hago el render final o limpio los residuos?».

### 7. Objetos nuevos para las escenas (`Herramientas/blender/objetos_cartoon.py`)
Todos de caricatura y originales (sin marcas). Claude los usa cuando la historia los pide:
- **Pensamientos y poderes:** `burbuja_pensamiento` (nube con **una sola** bolita, sin tapar la cara), `aura_poder`, `lucecita` (bolita de luz con estela), `chorro_luz` (rayo curvo de "le robó su poder"), `atrapa_poderes` (máquina del villano), `ventana_rayosx` (pared transparente en un círculo), `destellos`, `rayos_brillo`, `brillar` (hace brillar un objeto), `lineas_velocidad` (para volar), `marco_recuerdo`.
- **Dinero y concursos:** `moneda`, `caja_monedas`, `bolsa_dinero`, `trofeo`, `podio_ganadores`, `mesa_jueces`, `gradas`, `numero_concursante` (dorsal en el pecho), `campanita` de mostrador.
- **Comida y panadería:** `helado`, `bolsa_papas`, `papa_frita`, `chile`, `bolsa_chiles`, `galleta`, `frasco_galletas`, `concha`, `bolillo`, `cuernito`, `charola_panes`, `anaquel_panes`, `horno_lena`, `costal_harina`, `mesa_panadero`.
- **Ropa y vestuario:** `sombrero_copa`, `bigote` (de una pieza lisa), `banda_presidencial`, `gorro_chef`, `chaqueta_chef`, `panuelo_cuello`, `mandil`, `mandil_curvo`, `lentes`, `cachetes` rosados, `babero`, `chupon`, `panal` (pañal de bebé), `letrero_espalda` (papel pegado en la espalda), `ropa_tirada`. Atajos para vestir NPC: `vestir_panadero`, `vestir_tendero` y `vestir_vecina`, además de `ocultar_pelo` (para ponerle otro gorro) e `igualar_piel`.
- **Casa, tienda y calle:** `mostrador`, `caja_registradora`, `estante_frascos`, `frasco`, `frasco_especial`, `barril`, `caja_madera`, `contenedor_basura`, `bote_basura`, `tendedero`, `canasta_ropa` + `cargar_canasta`, `escalera_mano`, `pizarron`, `letrero_colgante`, `manta` (con letras), `libro_abierto`, `marco_foto`, `placa_fuente`, `cuna`, `movil_cuna`, `mecedora`, `control` de videojuego, `linterna_mano`, `telarana`, `veleta`, `vidrios_rotos`, `fondo_noche` (cielo con luna para ver por una ventana).
- **Fiesta:** `racimo_globos` y `arco_globos`.
- **Hélice de un gorro que gira:** `separar_helice` y `girar_helice`.

### 8. Efectos visuales nuevos (`Herramientas/blender/vfx.py`)
- `fuego_vivo`: fuego que sí parece fuego (lenguas con volumen, chispas y luz). Las llamas planas de antes parecían de papel.
- `corazones_emisor`: corazones de cariño **llenos y rosas** (la forma de toda la vida) que nacen del pecho del personaje, uno tras otro, suben por detrás sin tapar la cara y se desvanecen. Reemplazan a los corazones de línea transparentes.
- `chapoteo`: gotas en corona cuando algo cae al agua.
- `lagrimas`: salen de los dos ojos y siguen a la cabeza.
- `dorar_materiales`: vuelve dorado y brillante un material por tramos (por ejemplo, agua dorada).

### 9. Otros arreglos en herramientas
- `tomas_simples.py`: la cámara ya no da una vuelta completa a mitad de la toma.
- `armar_video.py` y `rehacer_tramo.py` recuperan solos los PNG si el episodio ya se limpió.
- `tomas_desde_voz.py` entiende las marcas de `quitar_onomatopeyas.py` (el golpe cae en su momento y sin subtítulo).
- `voz_elevenlabs.py`: si el modelo (v3/v4) no acepta el contexto de las líneas vecinas, pide la línea sola.
- `catalogo.py` anota la herramienta de alturas en tu `docs/10_CATALOGO.md`.
- Plantilla `Episodios/_PLANTILLA_EPISODIO/PLANO.md`: cada cosa que se va a modelar lleva su **referencia de internet** (link y rasgos que se copian) y se construye **por lotes**, con foto de prueba contra la referencia.

### 10. Lecciones nuevas (`docs/02_LECCIONES.md`, de la 80 a la 112)
Son los errores que salieron en los episodios y cómo se arreglaron. Claude las lee antes de animar:
- **80** La voz se sentía lenta por los huecos, no por la voz.
- **81** Los niños no se veían niños (de ahí sale `alturas.py`).
- **82** La cámara daba una vuelta completa a mitad de la toma.
- **83** Revisión toma por toma: cámara dentro de una cascada, postes que tapan, objetos en la mano que tapan la cara.
- **84** Luz de tarde y de noche (sol cálido, contraluz, luz de luna por la ventana).
- **85** Correcciones del dueño a un borrador (que se vea caer la moneda, mano en el hombro calculada, revisar por segundos).
- **86** Accesorios pegados al cuerpo: medir en los ejes del rig, no del mundo.
- **87** Sombreros y bigotes (bigote de una sola pieza; el ala del sombrero no tapa la cara).
- **88** Vestuario de NPC y la cabeza bronceada (de ahí sale `revisar_piel.py`).
- **88b** Gancho sin huecos: mostrar cómo desaparece algo, no el lugar vacío.
- **89** Letreros grandes y dentro de su marco; lo que se agrega a un edificio usa sus mismos materiales.
- **90** Mundos enormes que no se acaban (miles de casas, niebla, nubes que no parecen plástico, humo de verdad).
- **91** Encuadres en 9:16 (cabezas cortadas), fuego que parezca fuego, rayos X y volar con piernas vivas.
- **91b** Animar sin la voz aprobada (voz temporal de Windows, sin gastar créditos) y render por turnos.
- **92** Cámaras que se revisan solas para que nada tape en 67 tomas.
- **93** Revisar el video renderizado, no solo la hoja de fotos.
- **94** Rayos de luz, luces que queman la imagen y cámaras que se despejan solas.
- **95** Que todo se mueva junto y que la acción se lea.
- **96** Reutilizar el Pueblo en mapas nuevos, onomatopeyas fuera de la voz y que la idea se vea.
- **97** Piso que parpadea, rayos que velan y derretir de verdad.
- **98** Revisar cada fotograma antes de la vista previa: nadie atraviesa nada.
- **99** Vestir a un NPC: medir su cara primero.
- **100** Emparentar objetos recién creados y escaleras en un cerro.
- **101** Rayos de luz y cosas que brillan encima de un personaje.
- **102** Modelos de Studio que no son R15 normales (ciervo, R6, escenarios).
- **102b** Agrandar algo del catálogo: revisarlo de cerca primero.
- **103** Ola gigante de caricatura.
- **104** Efectos de sonido que seguían sonando después de su acción.
- **105** Encuadre fuera de la zona segura de Shorts.
- **106** Cosas encima de la cabeza que chocan con el gorro.
- **107** Luz de color pegada a la cara y cámaras que atraviesan techos.
- **107b** La ola rota tapaba todo.
- **108** Caras fuera de la zona segura y cámaras que atraviesan paredes al alejarlas.
- **108b** Efectos de sonido de más y cortes que se oyen.
- **109** Gancho de adelanto con voz nueva al principio, sin re-animar el episodio.
- **110** Vista previa más rápida con muchas luces: `render_paralelo.py --rapida` (sombras a media resolución; con 2 Blender, 2,5 h bajan a ~1 h y no se nota la diferencia).
- **111** Corazones de cariño que parezcan corazones.
- **112** Parados en una tabla de surf o patineta: una pierna adelante y otra atrás, rodillas dobladas que se mueven.

(Algunos números estaban repetidos; los segundos ahora llevan una **b**: 88b, 91b, 102b, 107b y 108b.)

### 11. Carpetas personales nuevas
Git no las sube ni las toca; solo viaja su `LEEME.md`:
- `Musica/`: tu canción de fondo.
- `Personajes/Animaciones/`: las animaciones que saques de Roblox Studio.
- También quedan fuera las fotos sueltas (`.jpg`, `.png`) que pongas directo en `Personajes/`.

### 12. Lista completa de archivos
- **Nuevos (13):**
  - `Herramientas/audio/`: `musica_fondo.py`, `acortar_palabra.py`, `quitar_onomatopeyas.py`
  - `Herramientas/blender/`: `zona_segura.py`, `alturas.py`, `revisar_piel.py`, `rig_motor6d.py`, `animacion_roblox.py`, `texturas/marco_recuerdo.png`
  - `Herramientas/limpiar_episodio.py`
  - `Herramientas/roblox/sacar_animacion.luau`
  - `Musica/LEEME.md`, `Personajes/Animaciones/LEEME.md`
- **Cambiados (31):**
  - Guías: `CLAUDE.md`, `docs/01_PIPELINE.md`, `docs/02_LECCIONES.md`, `docs/03_PERSONAJES.md`, `docs/05_CAMARAS_Y_TOMAS.md`, `docs/06_AUDIO_VOZ_SUBS.md`, `docs/IDEAS.md`, `docs/CAMBIOS.md`, `Caras/LEEME.md`, `Herramientas/LEEME.md`, `Herramientas/roblox/LEEME.md`
  - Skills: `.claude/skills/nuevo-episodio/SKILL.md`, `.claude/skills/poner-rig/SKILL.md`, `.claude/skills/actualizar-kit/SKILL.md` (ahora te dice dónde leer esta guía)
  - Plantilla: `Episodios/_PLANTILLA_EPISODIO/PLANO.md`
  - Audio: `Herramientas/audio/armar_video.py`, `recortar_pausas.py`, `tomas_desde_voz.py`, `voz_elevenlabs.py`
  - Blender: `Herramientas/blender/objetos_cartoon.py`, `vfx.py`, `tomas_simples.py`, `armar_rig_r15_auto.py`
  - Otros: `Herramientas/armar_secuencia_caras.py`, `catalogo.py`, `config.py`, `rehacer_tramo.py`, `Herramientas/roblox/exportar_obj.ps1`, `studio_personajes.luau`
  - Configuración: `.gitignore`, `mi_config.ejemplo.json`

## v0.5.0 — 2026-11-09 — Planear antes de animar (y nada tieso)
**Cómo trabaja Claude un episodio ahora** (`CLAUDE.md`, skill `nuevo-episodio`, `docs/01_PIPELINE.md`). Es lo aprendido en EP004 y EP005 y en el entrenamiento con 172 videos:
1. **Guion desde el título** con la estructura medida (`docs/08_HISTORIAS.md`):
   - «En este pueblo, …» con la regla completa a los ~4 s.
   - Frases de 6–7 palabras, ~2:05 de duración.
   - El «suscríbete» amarrado a la regla.
   - Checklist para niños de 5 a 9 años.
2. **Plano de construcción antes de la voz** (`Episodios/_PLANTILLA_EPISODIO/PLANO.md`):
   - Contiene lugares, personajes, objetos, efectos, letreros y la tabla de tomas.
   - Primero se revisa el **catálogo** de lo que ya existe (`docs/10_CATALOGO.md`). Es personal: lo crea `instalar.py` en cada PC con `Herramientas/catalogo.py`.
   - Se construye solo lo que falta y se muestran fotos.
3. **Receta simple** (`docs/09_RECETA_SIMPLE.md` + `Herramientas/blender/tomas_simples.py`):
   - 5 tipos de toma, cámara fija o con acercamiento lento, una frase = una toma.
   - La energía son los **cortes**: 37–42 por minuto y un corte en los primeros 3 s.
4. **Nada tieso** (regla de oro 14):
   - `Herramientas/blender/vida_suave.py` suma respiración, cabeza, peso, brazos y un gesto en la palabra clave. Viene activado por defecto en `tomas_simples`.
   - `actuar.py` sirve para actuar toma por toma.
5. **Revisión antes de renderizar** (regla de oro 13, checklist «Calidad de cada toma» en `docs/05`):
   - `revisar_encuadre.py`, `revisar_ojos.py`, `revisar_agarre.py`, `revisar_objetos.py`, `revisar_pies.py` y `detectar_superficies.py`.
   - Después, un **borrador MP4 con voz** (cuadros salteados, baja calidad) y hojas por toma para revisar cada fotograma. Al final, la vista previa.
- **Lecciones 37–79** en `docs/02_LECCIONES.md`. Algunas: espejo de verdad, cobija que tapa sin atravesar, beso que sí se note, cámara pegada detrás de alguien, simple ≠ congelado y onomatopeyas que Whisper no escribe.

**Entrenamiento** (`Analizador/Estilos/`):
- **Custerk** (76 videos) y **Gelo** (96 videos), los dos con confiabilidad alta: fórmula, notas y `COMPARACION.md`.
- Ellos casi no mueven la cámara: la energía son los cortes. Lo único que va con más vistas en los dos creadores es **cortar en los primeros 3 s**.

**Para construir escenas**:
- `muebles_cartoon.py` (nuevo): camas con cobija de tela, tocador con foquitos, espejo de cuerpo completo, repisas, peluches, cocina, sala y comedor, entre otros.
- `Herramientas/texturas_tela.py` (nuevo): telas y papel tapiz con estampado propio (estrellas, corazones y gatitas kawaii **originales**, sin personajes con dueño).
- `objetos_cartoon.py`: mochila que se abre, carta, gorra, candado, camita y platito de gato, tenedor, peluche, pastel, globo, billete y galleta de la fortuna.
- `vfx.py`: cambio de cuerpo (almas de luz), sonrojo, líneas de impacto, fuego y humo de caricatura, y un gato con vida que come con tenedor.
- Caras:
  - `caras_atlas.py`: cabezas dinámicas.
  - `caras_npc.py`: reemplaza la cara clásica « : ) ».
  - `bocas_hablar.py`: lip-sync sencillo.
  - `mirada_lateral.py`: ojos hacia un lado.
- Carteles con detalle de caricatura: `carteles.py`.
- Para estudiar videos: `fotogramas_ref.py` y `comparar_videos.py`.

**Voz**:
- `tomas_desde_voz.py`: las onomatopeyas que Whisper no escribe (como «¡Miau!») toman el tiempo de su sonido, así los golpes y el subtítulo caen en su momento.

- **El storyboard del navegador se quitó del kit**: dejaba a los personajes tiesos (EP004). Solo queda su **motor de poses**, `Herramientas/storyboard/sb_blender.py` + `web/poses.json` (ángulos «de persona» → huesos, ciclos de caminar y correr, piso real). Lo usan `vida_suave`, `actuar` y `tomas_simples`.
- `recortar_pausas.py` ahora **escucha** la voz: mide la energía y solo quita silencio real (nunca un pedazo de palabra), deja un **respiro corto** entre líneas (0,3–0,4 s; 0,41–0,55 s después de "…") y al final la oye con Whisper y avisa si alguna palabra no se oye completa. También guarda `audio/voz_escuchar.mp3` para oírla.
- Arreglado: los tiempos de las palabras se atrasaban hasta 0,18 s al final de la voz (golpes y subtítulos caían tarde). Si ya recortaste una voz con la v0.4.1, vuelve a correr `recortar_pausas.py` y `tomas_desde_voz.py`.
- `voz_elevenlabs.py --linea N` (o `--linea 24-26` si la voz dice esas líneas pegadas): rehace solo esa parte (gasta solo sus créditos) y la pega en la voz con la misma voz, ajustes y el volumen de las líneas vecinas; `--simular` lo prueba sin gastar y `--reusar` vuelve a pegar la línea ya pedida sin pagar otra vez. La voz anterior se guarda sola en `Respaldos/`.
- `revisar_voz.py` (nuevo, lo corre solo el recorte): revisa la voz como una persona con Whisper y medidas, y marca con su segundo palabras de más o poco claras, sonidos inventados, líneas atropelladas o fuera de volumen.
- `recortar_pausas.py` empareja el volumen de las líneas (ElevenLabs a veces susurra una) y pega el inicio de cada palabra a donde de verdad empieza el sonido (cortes de toma más exactos).
- Subtítulos sin comillas ni signos (. , ! ¡ ? ¿) en la plantilla `armar_video.py`.
- `cielo.py` (nuevo): cielo decorativo para cualquier mapa, de día azul con nubes y un sol blanco con brillo suave, de noche con estrellas. Solo lo ve la cámara (la luz del mapa no cambia) y pasa solo a noche cuando el mapa se oscurece. Ver `docs/04_ESCENARIOS.md`.
- `voz_elevenlabs.py --agregar`: genera solo las líneas nuevas del final (ej. el bloque 2) y las pega a la voz ya aprobada, sin rehacerla. Al rehacer una voz completa usa la misma voz del episodio.
- Regla nueva: no usar "..." en la narración para ElevenLabs (se come finales, mete sonidos o junta palabras); usar coma o punto. `recortar_pausas.py` también mete el respiro donde la voz junta dos líneas pero baja casi a silencio.
- **Exportar personajes de Roblox Studio en lote** (`Herramientas/roblox/`, nuevo): Claude aísla cada personaje, lo exporta a `.obj` con el menú de Studio y crea su `partes.json` (nombres reales de las piezas). Guía: `Herramientas/roblox/LEEME.md`.
- `armar_rig_r15_auto.py`: la **ropa en capas** (chamarras, mangas, calentadores) ahora se deforma con los huesos; lee `partes.json` (reconoce niñas, cuerpos angostos y piezas que faltan); 3er dato opcional `voltear` / `no_voltear` cuando la detección de giro falla.
- **Trabajo por toma**: `rehacer_tramo.py EP### --toma 12` (o `12-14`) rehace solo esa toma (cámara) y vuelve a mezclar el sonido; `--tomas` lista las tomas con sus segundos.
- `objetos_cartoon.galleta_fortuna()`: galleta de la fortuna cerrada o abierta (dos mitades y el papelito con el texto que quieras).
- `extras_npc.py` (nuevo): gente de fondo con poses (atender, sentados platicando, fila, comprar, saludar) y `platica(a, b, f0, f1)`: dos personajes platicando con movimiento natural (se turnan, asienten, gesticulan, respiran).
- `vfx.py` (nuevo): efectos rápidos que no tapan la cara: `migas`, `brillitos` (con hueco para no tapar un texto), `corazones` de línea delgada, `confeti` y `abrir_galleta` (la galleta se parte con ¡crac!, migas y brillitos).
- `fotos_escenario.py`: `"props"` por vista (por ejemplo prender las luces del parque) y la noche ahora oscurece el fondo correcto (el cielo decorativo pasa a estrellas).
- Arreglado: `hoja_contacto.py` y `fotos_escenario.py` guardaban las fotos en `C:\Episodios\…` si se les daba una carpeta relativa (Blender toma esas rutas desde la raíz del disco); ahora usan la ruta completa.

## v0.4.1 — 2026-11-06 — Voz de corrido
- `recortar_pausas.py` deja pausas de máximo 0,15 s entre palabras y 0,25 s después de "…": la voz se oye hablando de corrido, a velocidad normal.

## v0.4.0 — 2026-11-06 — La voz manda el ritmo
**Reglas nuevas para Shorts** (CLAUDE.md, reglas de oro 9–12; skill `nuevo-episodio` actualizada):
- **Cada escena lleva voz** (no quedan partes calladas): el video dura lo que la voz, aunque el guion sea corto. Una línea de `narracion.txt` = una toma (1,5–2,5 s, corte en cada idea).
- **Voz primero**, con la voz de cada quien (su ElevenLabs o una voz ya hecha), a **velocidad normal** y con emoción. El usuario la escucha y la aprueba antes de animar.
- **Recortar pausas sin que se note**: `Herramientas/audio/recortar_pausas.py` (también para voces propias, con Whisper).
- **Las tomas salen de la voz**: `Herramientas/audio/tomas_desde_voz.py` → `audio/tomas_voz.json` (los golpes ¡pum!/¡pop! caen en su palabra).
- **Efectos que coinciden con la escena** (nueva plantilla `Herramientas/audio/armar_video.py`: voz de corrido, `"palabra:pum"`, subtítulos automáticos de 1–2 palabras).
- **Caras por emoción cambiando la textura** de la cabeza (`Herramientas/blender/caras_textura.py` + `Herramientas/armar_secuencia_caras.py` para armar tus caras), nunca planos encima. Excepciones: caras de máscara, dinámicas o dibujadas (se anotan en `MI_CANAL.md`).
- **Render en paralelo** (`Herramientas/render_paralelo.py`): 2 Blender a la vez ≈ 1,6× más rápido. Claude pregunta antes.

**Herramientas y guías nuevas**
- **Rig automático** (`armar_rig_r15_auto.py`): centra, voltea, reconoce las 15 piezas R15 y pega accesorios; arregla cabezas dinámicas sin cara. La skill `poner-rig` ya lo usa.
- **Interiores para el Pueblo** (scripts en `Escenarios/Pueblo/scripts/`: `interiores.py`, `presidencia_interior.py`, `util_interiores.py`): 2 casas anchas con sala, comedor, cocina, escalera y cuartos; presidencia con vestíbulo, despacho del alcalde, cabildo, secretaría y torre del reloj. Se aplican sobre una **copia** del mapa (ver `docs/04_ESCENARIOS.md`).
- `objetos_cartoon.py` (burbujas de pensamiento, humo "¡pop!", nube que llueve, pan, elefante, sombrero, escoba, gato con cabeza que voltea, paraguas, linterna, cuaderno, monstruo desde un personaje) y `fotos_escenario.py`.
- Revisión: `hoja_contacto.py` + `componer_hoja.py` (hoja con todas las tomas) y `revisar_camaras.py` con varios personajes por toma (propiedad `sujeto`) y por tramos.
- `voz_elevenlabs.py --voz ID`: probar otra voz sin cambiar la del canal.
- Guía `docs/08_HISTORIAS.md`: historias con misterio, giro que no se adivine y narración con voz en cada escena.
- La plantilla vieja de `armar_video.py` (voz acomodada frase por frase) queda solo en EP001.

## v0.3.1 — 2026-11-06 — Segundo entrenamiento
- **ClusterK y Gelo con 5 videos cada uno** (confiabilidad media). Fórmulas, notas y `COMPARACION.md` actualizadas.
- ClusterK: tipos de giro (narrador engañado con montaje de pistas, golpe final), retos por rondas con cameo famoso, finales abiertos para parte 2.
- Gelo: alcalde villano que se aprovecha de la regla (5 de 5), monstruo incomprendido, "suscríbete" pegado al tema, protagonista a color contra el pueblo gris, carteles en la escena.

## v0.3.0 — 2026-11-06 — Skills y primer entrenamiento
- **Skills del kit** (`.claude/skills/`): `instalar-kit`, `poner-rig`, `analizar-videos`, `nuevo-episodio`, `rehacer-tramo`, `actualizar-kit`. Claude las usa solo al abrir la carpeta del kit.
- **Primer entrenamiento** (`Analizador/Estilos/`): fórmulas y notas de **ClusterK** y **Gelo** (3 videos cada uno, confiabilidad baja: se irán afinando) + `COMPARACION.md`.
- Analizador: subtítulos de una palabra bien contados; detector de partículas sin la franja de subtítulos ni el paralaje de zooms.
- README: instalación fácil con un prompt para Claude.

## v0.2.0 — 2026-11-06 — Carpetas claras, Analizador y rehacer tramos
- **Carpetas sin números**, más fáciles de entender: `Personajes/` (`Protagonista`, `Secundarios`, `Pueblo_NPC`, `Plantillas_Rigs`), `Caras/`, `Escenarios/`, `Episodios/`, `Analizador/`, `Herramientas/`, `Respaldos/`.
  Si tenías la v0.1.0 con cosas tuyas: mueve los videos de `00_Referencias` → `Analizador/Videos_para_analizar/<Creador>/`, `01_Personajes/1_Protagonista` → `Personajes/Protagonista` (igual secundarios, NPC y rigs), `05_Recursos/Caras` → `Caras`, `02_Escenarios` → `Escenarios`, `03_Episodios` → `Episodios`, `99_Archivo` → `Respaldos` (o pídeselo a Claude).
- **Analizador de videos v2** (`Analizador/`): cortes verificados, cámara, tipo de plano medido (cara/cuerpo), subtítulos por OCR, voz por GPU, sonido, historia, efectos candidatos, reporte HTML y fórmula por creador (`Analizador/Estilos/`). Reemplaza a `Herramientas/analisis/analizar_referencia.py`.
- **Rehacer solo un tramo** (`Herramientas/rehacer_tramo.py`): respalda, renderiza solo del segundo X al Y y vuelve a armar el video; `--deshacer` regresa la versión anterior.
- Personajes por nivel (protagonista, secundarios, NPC) con receta de rig, NPC con nombre confirmados por el usuario y caras por emoción.
- Mapas: el `Pueblo/` original no se modifica; copias y mapas nuevos van en su propia carpeta de `Escenarios/`. Los episodios anexan solo los personajes que salen.

## v0.1.0 — 2026-11-06 — Primera versión
- Escenario por defecto **Pueblo** (`Escenarios/Pueblo/`): calle con casas y cortinas animables, faroles, plaza con fuente, presidencia con reloj y podio, 4 tiendas, escuela con 2 salones y cancha, estanque, colinas. Incluye los scripts que lo construyen.
- Plantilla de episodio (`Episodios/_PLANTILLA_EPISODIO/`): guion con tabla de tomas, narración y checklist.
- Herramientas (`Herramientas/`): conexión a Blender (`bl.py`), revisión de cámaras, solver de poses de brazos, plantilla de rig R15, voz con ElevenLabs, armado de video (voz + efectos + subtítulos), análisis de videos de referencia.
- Guías en `docs/`: pipeline, 28 lecciones, personajes, escenarios, cámaras, audio y análisis de referencias.
- Archivos personales separados (`MI_CANAL.md`, `MI_BITACORA.md`, `mi_config.json`, personajes, episodios, referencias): las actualizaciones nunca los tocan.
- `instalar.py` + `requirements.txt` para preparar una PC nueva.
