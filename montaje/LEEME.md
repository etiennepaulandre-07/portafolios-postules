# Montaje automático de videos · CV Vivo

Apps Script deja aquí, al aprobar el audio en el panel, una carpeta por postulación:

    montaje/<token>/voz.wav · version.json · video_plan.json · pedido.json (estado: pendiente)

Opcional: `video.json` con los textos de la gráfica (nodos, chips, lados de "la línea").

Para armar el video (desde la raíz del repo):

    python3 montaje/_taller/montar.py montaje/<token>

Deja `v/<token>.mp4`, `.jpg` y `.json`; la página los toma sola por el token. Luego `pedido.json` queda en `estado: listo`.
Requiere Python 3, Playwright con Chromium, ffmpeg y Node. La música y los efectos están en `_taller/`.
