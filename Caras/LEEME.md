# Aquí van las caras (expresiones)

Las caras **se cambian en la textura de la cabeza** (nunca con planos encima) y van cambiando con la emoción de cada toma.

```
Caras/
├── Emociones/                 ← tus caras: PNG con fondo transparente, una emoción por archivo
│   ├── Sad.png, Shocked.png, ...
│   ├── nombres.json           ← (opcional) {"Sad.png": "triste", ...}
│   └── _secuencia/            ← la arma la herramienta (cara_0001.png ... + caras.json con el número de cada cara)
└── Paquete_<Nombre>/          ← paquetes completos de caras (de ahí eliges cuáles pasar a Emociones/)
```

1. Pon tus PNG en `Caras/Emociones/`.
2. Corre `py Herramientas/armar_secuencia_caras.py` (con `--sonrisa <textura del personaje.png>` agrega su cara de siempre al final).
   - ¿Ya tenías la secuencia y agregaste caras nuevas? `py Herramientas/armar_secuencia_caras.py --agregar`: las pone al final (28, 29…) **sin cambiar los números** que ya usan tus episodios, e iguala el tamaño del dibujo. Si una sale muy grande o chica, anota su escala en `Caras/Emociones/ajustes.json` (ej. `{"Crying.png": 0.85}`). Nombres en español: `nombres.json`.
3. Claude prepara a cada personaje con `Herramientas/blender/caras_textura.py` y elige el número de cara en cada toma.

- **Excepciones**: personajes con cara de máscara, dinámica o dibujada no se cambian (se anotan en tu `MI_CANAL.md`); sus emociones se muestran con poses, efectos y sonido.
- Las caras de Roblox tienen licencia: no se suben al repositorio (git ignora esta carpeta salvo este LEEME).
