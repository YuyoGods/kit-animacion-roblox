# Aquí van las caras (expresiones)

PNG con **fondo transparente**, cuadrados, nombrados por emoción (minúsculas, sin acentos ni espacios):

```
Caras/
├── neutral.png      ├── triste.png
├── feliz.png        ├── asombro.png
├── risa.png         ├── miedo.png
├── enojado.png      ├── pensativo.png
├── guino.png        └── ...
└── Paquete_<Nombre>/   ← paquetes completos de caras (Claude busca ahí si falta una emoción)
```

- **Cara propia de un personaje**: si alguien tiene caras distintas, ponlas en su carpeta: `01_Personajes/<nivel>/<Nombre>/caras/feliz.png`. Esas tienen prioridad.
- Claude coloca la cara al frente de la cabeza (pegada al hueso `Head`) y la cambia por fotograma según la emoción del guion. Ver `docs/03_PERSONAJES.md` → Caras.
- Las caras de Roblox tienen licencia: no se suben al repositorio (git ignora esta carpeta salvo este LEEME).
