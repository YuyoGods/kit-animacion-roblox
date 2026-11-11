# Animaciones (personal)

Animaciones sacadas de Roblox Studio para ponérselas a los rigs del kit (bailes, emotes, celebraciones).
Esta carpeta es **personal**: git no la sube (solo este `LEEME.md`).

- `<Nombre>.json` → los datos de la animación (lo saca `Herramientas/roblox/sacar_animacion.luau`).
- `<Nombre>_<Personaje>.blend` → un rig con la animación ya puesta, para verla o compartirla.
  La animación viene como **acción** con el mismo nombre: desde otro `.blend` se anexa con
  *Archivo › Anexar › <archivo>.blend › Action › <Nombre>* y se asigna a cualquier rig R15 del kit
  (mismos nombres de huesos; poner `IK_Piernas` e `IK_Brazos` en 0 para que se vea).

Ponerla a un personaje (hace un `.blend` nuevo, no toca el rig original):

```
blender -b "Personajes/<nivel>/<Nombre>/<Nombre>_R15_Rig.blend" --python Herramientas/blender/animacion_roblox.py -- Personajes/Animaciones/<Anim>.json Personajes/Animaciones/<Anim>_<Nombre>.blend [vueltas] [--empacar]
```

Solo se pueden bajar animaciones tuyas o de Roblox; las publicadas por otras personas las bloquea Roblox.
