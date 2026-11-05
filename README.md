# El Plan de Salvación

Una película animada y narrada de unos dos minutos y veinte segundos que presenta el Plan de Salvación. Se ve en [salvacion.idear.pro](https://salvacion.idear.pro) y cualquier sitio puede ofrecerla con una cruz flotante.

## Ponerla en un sitio

Pega esta línea antes de cerrar `</body>`:

```html
<script src="https://salvacion.idear.pro/cruz.js" defer></script>
```

Aparece una cruz en la esquina inferior izquierda que flota unos pixeles. Al tocarla se abre la película en un diálogo; en el teléfono ocupa toda la pantalla. La película se descarga solo al abrirla, así que no hace más lenta la página que la incluye. Si quien visita tiene activado reducir el movimiento, la cruz se queda quieta.

Las opciones van como atributos del mismo `<script>`:

| Atributo | Valores | Por defecto |
|---|---|---|
| `data-lado` | `izquierda`, `derecha` | `izquierda` |
| `data-abajo`, `data-costado` | separación del borde en px | `18`, `20` |
| `data-fondo`, `data-color`, `data-borde` | colores del botón | `#0b0b0b`, `#fff`, `#555` |
| `data-radio` | redondeo del botón en px | `3` |
| `data-tema` | `noche`, `amanecer`, `olivo` | colores originales |
| `data-idioma` | `es`, `en` (botón y diálogo; la película está en español) | `es` |
| `data-capa` | z-index del botón | `9999` |

Por ejemplo, a la derecha y por encima de un botón de chat:

```html
<script src="https://salvacion.idear.pro/cruz.js" data-lado="derecha" data-abajo="90" defer></script>
```

[salvacion.idear.pro/ejemplo.html](https://salvacion.idear.pro/ejemplo.html) muestra la cruz funcionando. La película también se puede insertar directamente con un iframe a `https://salvacion.idear.pro/?autoplay=1`.

## Cómo está hecha

`public/index.html` es la película: un lienzo de 1920×1080 dibujado con SVG y animado en el navegador, que se escala a cualquier pantalla. No es un video; el texto es HTML y se puede corregir. `public/narracion.mp3` lleva la voz y la música ya mezcladas, y el reloj de la animación sigue al audio.

La narración y la música se generan con ElevenLabs:

- `scripts/guion.json` es lo que dice la voz en cada escena.
- `scripts/musica.json` describe la música en seis secciones ligadas a las escenas, su volumen relativo (`level_db`) y cuánto queda bajo la voz (`duck_db`).
- `scripts/narracion.py` pide cada escena con marcas de tiempo por carácter, ajusta la duración de cada escena a su lectura, hace aparecer cada palabra cuando se pronuncia, compone la música a la medida y mezcla todo en `public/narracion.mp3`. Escribe los tiempos en el bloque `NARRACION` de `index.html`.
- `scripts/clips/` guarda cada toma y la música. Solo se vuelve a pedir lo que cambió, así que correr el script sin cambios no gasta créditos.

Para regenerar se necesita `ffmpeg` y una clave de ElevenLabs guardada en un archivo **fuera de este repositorio**:

```bash
python3 -I scripts/narracion.py /ruta/privada/a/la-clave
```

La clave nunca se escribe en el repositorio ni en los archivos generados.

`?tema=noche` (o `amanecer`, `olivo`) cambia la paleta sin tocar las escenas.

## Publicación

Cada push a `main` construye `ghcr.io/erikwco/plan-de-salvacion` (nginx con los archivos de `public/`). La película, el audio y `cruz.js` se sirven con revalidación, así que una versión nueva llega a todos los sitios sin cambiarlos.

## Créditos

- Voz: Erik Chacon, generada con su voz clonada en ElevenLabs.
- Música: compuesta con Eleven Music.
- Fuente: Patrick Hand, de Patrick Wagesreiter, bajo la SIL Open Font License (`public/fonts/PatrickHand-OFL.txt`).
- Texto bíblico: Santa Biblia, versión Reina-Valera 1960 © Sociedades Bíblicas en América Latina, 1960. Renovado © Sociedades Bíblicas Unidas, 1988.
