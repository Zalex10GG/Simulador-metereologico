# Plan de implementacion por fases

## Fase 1: Base del proyecto

Objetivo: preparar la estructura minima para una aplicacion FastAPI con frontend estatico.

Entregables:

- Crear paquete `src/` con modulos:
  - `api.py`
  - `config.py`
  - `cities.py`
  - `wrf_processing.py`
  - `routing.py`
  - `risk.py`
  - `plotting.py`
  - `schemas.py`
- Crear carpeta `frontend/` con:
  - `index.html`
  - `script.js`
  - `style.css`
- Anadir dependencias con `uv`:
  - `fastapi`
  - `uvicorn`
  - `matplotlib`
  - `cartopy`
  - `numpy`
  - `scipy` si se usa interpolacion numerica auxiliar.
- Mantener las dependencias obligatorias existentes:
  - `metpy>=1.7.1`
  - `netcdf4>=1.7.4`
  - `xarray>=2026.4.0`
  - `xwrf>=0.0.5`

Criterios de aceptacion:

- El proyecto sincroniza dependencias con `uv sync`.
- El backend arranca con `uv run uvicorn src.api:app --reload`.
- Existe un endpoint de salud o raiz que confirma que la API responde.

## Fase 2: Carga y diagnostico WRF

Objetivo: abrir el NetCDF local y construir los campos meteorologicos base.

Entregables:

- Definir en `config.py` la ruta real del dataset: `data/wrfout_d01_2009-12-16.nc`.
- Implementar apertura del dataset en `wrf_processing.py` con `xarray` y motor `netcdf4`.
- Leer coordenadas `XLAT`, `XLONG` y tiempos `Times`/`XTIME`.
- Calcular:
  - presion total `P + PB`;
  - altura geopotencial `(PH + PHB) / g`;
  - temperatura absoluta y Celsius;
  - viento destaggered para `U` y `V`;
  - velocidad del viento;
  - precipitacion acumulada `RAINC + RAINNC`.
- Crear funciones de consulta para superficie y niveles de presion.

Criterios de aceptacion:

- Una prueba manual puede abrir el dataset sin errores.
- Se imprimen o devuelven dimensiones esperadas: `Time`, `bottom_top`, `south_north`, `west_east`.
- Los diagnosticos devuelven arrays con dimensiones coherentes.

## Fase 3: Mapas horizontales

Objetivo: generar mapas meteorologicos en PNG base64 desde el backend.

Entregables:

- Implementar en `plotting.py` utilidades para convertir figuras Matplotlib a base64.
- Implementar mapas de:
  - viento 10 m;
  - temperatura 2 m;
  - presion de superficie;
  - precipitacion acumulada;
  - geopotencial y temperatura a 850 hPa;
  - geopotencial y temperatura a 500 hPa;
  - jet stream a 300 hPa.
- Usar Cartopy para proyeccion, costas, fronteras y rejilla geografica.
- Implementar endpoint `GET /api/fields`.
- Implementar endpoint `POST /api/map`.

Criterios de aceptacion:

- Cada campo definido en `GET /api/fields` puede solicitarse desde `POST /api/map`.
- La respuesta incluye `image_base64`, `title` y `metadata`.
- Los indices de tiempo fuera de rango devuelven error HTTP claro.

## Fase 4: Ciudades, dominio y rutas

Objetivo: permitir seleccionar origen/destino y calcular trayectorias ortodromicas.

Entregables:

- Implementar `cities.py` con una base de ciudades europeas principales y sus coordenadas.
- Implementar endpoint `GET /api/cities`.
- Implementar en `routing.py`:
  - calculo haversine de distancia;
  - generacion de puntos great-circle;
  - calculo de tiempo de vuelo con 850 km/h;
  - perfil vertical 20% ascenso, 60% FL330, 20% descenso.
- Implementar validacion de dominio WRF:
  - origen dentro del dominio;
  - destino dentro del dominio;
  - puntos intermedios dentro del dominio.

Criterios de aceptacion:

- La API devuelve ciudades ordenadas o en formato estable.
- Una ruta valida devuelve distancia, tiempo estimado, puntos y perfil.
- Una ruta fuera del dominio devuelve error sin intentar generar grafica.

## Fase 5: Interpolacion espacio-temporal

Objetivo: muestrear la atmosfera del WRF siguiendo la posicion y tiempo del avion.

Entregables:

- Asociar cada punto de ruta con:
  - distancia recorrida;
  - tiempo desde salida;
  - latitud/longitud;
  - altura objetivo del avion.
- Implementar interpolacion temporal entre timesteps WRF.
- Implementar interpolacion vertical a la altura o nivel requerido.
- Implementar seleccion horizontal por vecino mas cercano como primera version.
- Rechazar vuelos cuya duracion exceda la cobertura temporal del archivo WRF.

Criterios de aceptacion:

- La interpolacion devuelve series coherentes de temperatura, viento e hidrometeoros a lo largo de la ruta.
- La ruta avanza en tiempo desde el primer timestep del WRF.
- No se extrapola fuera del rango temporal disponible.

## Fase 6: Riesgos aeronauticos y cross-section

Objetivo: identificar y visualizar riesgos a lo largo de la ruta.

Entregables:

- Implementar en `risk.py`:
  - engelamiento: `T < 0 C` y presencia de hidrometeoros;
  - cizalladura: gradientes horizontal/vertical del vector viento;
  - visibilidad/conveccion aproximada: precipitacion, hidrometeoros y opcionalmente `W`.
- Documentar umbrales como constantes.
- Implementar en `plotting.py` grafica de seccion vertical:
  - eje X con distancia o tiempo;
  - eje Y con altura;
  - trayectoria del avion;
  - zonas sombreadas por tipo de riesgo.
- Implementar endpoint `POST /api/route`.

Criterios de aceptacion:

- La grafica de ruta se genera como PNG base64.
- La salida incluye resumen de distancia, duracion y riesgos detectados.
- La grafica diferencia visualmente los riesgos con leyenda clara.

## Fase 7: Frontend

Objetivo: construir una interfaz simple y usable para consumir la API.

Entregables:

- `index.html` con:
  - selectores de origen/destino;
  - selector de campo meteorologico;
  - selector de timestep;
  - botones de generar mapa y simular ruta;
  - contenedores para imagen de mapa, imagen de perfil y errores.
- `script.js` con:
  - carga inicial de ciudades y campos;
  - llamadas `fetch` a endpoints;
  - gestion de estados de carga y errores;
  - renderizado de imagenes base64.
- `style.css` con:
  - layout responsive;
  - paneles legibles;
  - estados visuales para carga y error.

Criterios de aceptacion:

- El usuario puede operar la practica sin editar codigo.
- Los errores de la API se muestran en pantalla.
- Las imagenes generadas por backend se renderizan correctamente.

## Fase 8: Validacion final

Objetivo: comprobar que la practica funciona de extremo a extremo.

Escenarios de prueba:

- Arranque:
  - `uv sync`
  - `uv run uvicorn src.api:app --reload`
- API:
  - `GET /api/cities`
  - `GET /api/fields`
  - `POST /api/map` para superficie.
  - `POST /api/map` para 850 hPa.
  - `POST /api/map` para 500 hPa.
  - `POST /api/map` para 300 hPa.
  - `POST /api/route` con ruta dentro del dominio.
  - `POST /api/route` con ruta fuera del dominio.
- Frontend:
  - carga de selectores;
  - generacion de mapa;
  - simulacion de ruta;
  - visualizacion de errores.

Criterios de aceptacion:

- No hay errores no controlados en consola backend.
- Las respuestas invalidas tienen mensajes claros.
- Las figuras tienen titulo, unidades y leyenda cuando corresponde.
- La documentacion sigue reflejando las limitaciones reales del dataset.

## Notas de implementacion

- Usar siempre `uv` para gestionar y ejecutar el proyecto.
- Mantener los calculos meteorologicos en backend.
- No introducir una base de datos externa; usar un diccionario Python para ciudades.
- No extrapolar datos WRF fuera de dominio espacial o temporal.
- Mantener CAPE como variable opcional futura; para este archivo usar diagnostico aproximado de conveccion/visibilidad.
- Priorizar claridad y trazabilidad del calculo frente a optimizaciones prematuras.

