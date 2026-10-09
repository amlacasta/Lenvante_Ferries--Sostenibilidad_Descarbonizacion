# Integración futura del site

El archivo `site/index.html` contiene toda la vista y los datos sintéticos integrados. Funciona sin backend y puede incorporarse como página estática bajo `/proyectos/sostenibilidad/` en `amlacasta.tech`, conservando la navegación, el tema dark y una tarjeta «Explorar Dashboard» en la home del portfolio.

1. Publicar `site/index.html` en la ruta elegida tras revisión visual de la página existente y su navegación.
2. Añadir una tarjeta «Proyecto 7 · Sustainability & Decarbonization Analytics» con enlace al dashboard.
3. Comprobar enlaces, tamaño móvil, accesibilidad y políticas de privacidad. No subir datos empresariales reales dentro del HTML público.
4. Si cambia la semilla, factores, fuente o normativa, ejecutar `python src/build_project.py` y publicar el nuevo `index.html` con versión de hipótesis.

El dashboard del Proyecto 7 se publicó en `https://www.amlacasta.tech/proyectos/sostenibilidad/`. El archivo de este repositorio es una copia autónoma de la versión del paquete; futuras actualizaciones del dominio y del repositorio deben verificarse por separado.
