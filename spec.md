# Especificacion del simulador meteorologico para rutas aeronauticas

## 1. Objetivo

Desarrollar un simulador meteorologico para rutas aeronauticas que permita:

- Visualizar campos meteorologicos horizontales derivados de un archivo WRF local.
- Seleccionar una ciudad europea de origen y una ciudad europea de destino.
- Calcular una ruta ortodromica entre ambas ciudades.
- Simular el perfil vertical de vuelo con ascenso, crucero a FL330 y descenso.
- Interpolar la atmosfera del WRF en espacio y tiempo a lo largo de la ruta.
- Generar una seccion vertical con riesgos aeronauticos: engelamiento, cizalladura, visibilidad/conveccion.

El sistema debe estar pensado como una practica academica: codigo claro, estructurado y sin abstracciones innecesarias.

## 2. Estado real del proyecto

El proyecto parte de una base Python con:

- Python `>=3.12`.
- Gestion de dependencias con `uv`.
- Archivo WRF local en `data/wrfout_d01_2009-12-16.nc`.
- Dependencias obligatorias ya declaradas en `pyproject.toml`:
  - `metpy>=1.7.1`
  - `netcdf4>=1.7.4`
  - `xarray>=2026.4.0`
  - `xwrf>=0.0.5`

El prompt original menciona `data/data/wrfout_d01_2009-12-16.nc`, pero en este repositorio el archivo existe en `data/wrfout_d01_2009-12-16.nc`. La implementacion debe usar esta ruta real o definirla como constante configurable.

## 3. Arquitectura

### Backend

El backend se implementara en Python con FastAPI dentro de un paquete principal `src/`.

Estructura propuesta:

```text
src/
  __init__.py
  api.py
  config.py
  cities.py
  wrf_processing.py
  routing.py
  risk.py
  plotting.py
  schemas.py
```

Responsabilidades:

- `api.py`: aplicacion FastAPI, endpoints y gestion de errores HTTP.
- `config.py`: rutas de archivos, constantes fisicas y parametros generales.
- `cities.py`: diccionario/base de ciudades europeas con latitud y longitud.
- `wrf_processing.py`: apertura del NetCDF, diagnosticos WRF e interpolacion.
- `routing.py`: calculo de distancia ortodromica, puntos de ruta y perfil de vuelo.
- `risk.py`: calculo de indices/mascaras de riesgo aeronautico.
- `plotting.py`: generacion de mapas y secciones verticales con Matplotlib/Cartopy.
- `schemas.py`: modelos de entrada/salida de la API.

### Frontend

El frontend sera estatico y estrictamente modular en tres archivos:

```text
frontend/
  index.html
  script.js
  style.css
```

Responsabilidades:

- `index.html`: estructura de la interfaz.
- `script.js`: llamadas a API, gestion de eventos e insercion de imagenes base64.
- `style.css`: estilos visuales y layout responsive.

El frontend no debe calcular meteorologia. Toda la logica WRF, rutas, riesgos y graficas debe vivir en el backend.

## 4. Comunicacion backend-frontend

El backend generara las graficas como PNG con Matplotlib/Cartopy, las codificara en base64 y las devolvera al frontend.

Formato general de imagen:

```json
{
  "image_base64": "data:image/png;base64,...",
  "title": "Mapa de temperatura a 850 hPa",
  "metadata": {}
}
```

Los errores de dominio, variables no disponibles o parametros invalidos se devolveran con codigos HTTP claros y mensajes legibles para la interfaz.

## 5. Endpoints minimos

### `GET /api/cities`

Devuelve la lista de ciudades disponibles.

Respuesta:

```json
[
  {
    "name": "Madrid",
    "lat": 40.4168,
    "lon": -3.7038
  }
]
```

### `GET /api/fields`

Devuelve los campos meteorologicos visualizables.

Campos minimos:

- `surface_wind`: viento 10 m.
- `surface_pressure`: presion en superficie o presion reducida aproximada si se implementa.
- `surface_temperature`: temperatura a 2 m.
- `surface_precipitation`: precipitacion acumulada `RAINC + RAINNC`.
- `z_t_850`: geopotencial y temperatura a 850 hPa.
- `z_t_500`: geopotencial y temperatura a 500 hPa.
- `jet_300`: viento a 300 hPa / jet stream.

### `POST /api/map`

Genera un mapa meteorologico horizontal.

Entrada:

```json
{
  "field": "z_t_500",
  "time_index": 0
}
```

Salida:

```json
{
  "image_base64": "data:image/png;base64,...",
  "title": "Geopotencial y temperatura a 500 hPa",
  "metadata": {
    "time_index": 0
  }
}
```

### `POST /api/route`

Calcula una ruta, simula el perfil de vuelo y genera la seccion vertical de riesgos.

Entrada:

```json
{
  "origin": "Madrid",
  "destination": "Paris"
}
```

Salida:

```json
{
  "image_base64": "data:image/png;base64,...",
  "route": {
    "origin": "Madrid",
    "destination": "Paris",
    "distance_km": 1053.0,
    "flight_time_minutes": 74.3,
    "cruise_level": "FL330"
  },
  "risks": {
    "icing": true,
    "wind_shear": true,
    "convection_visibility": true
  }
}
```

## 6. Procesamiento WRF

El archivo `data/wrfout_d01_2009-12-16.nc` contiene, entre otras, las variables:

- Coordenadas: `XLAT`, `XLONG`.
- Tiempo: `Times`, `XTIME`.
- Viento: `U`, `V`, `W`, `U10`, `V10`.
- Presion: `P`, `PB`, `PSFC`.
- Temperatura: `T`, `T2`.
- Geopotencial: `PH`, `PHB`.
- Hidrometeoros: `QVAPOR`, `QCLOUD`, `QRAIN`, `QICE`, `QSNOW`, `QGRAUP`.
- Precipitacion: `RAINC`, `RAINNC`.
- Terreno: `HGT`.

Diagnosticos requeridos:

- Presion total: `P + PB`.
- Temperatura perturbada WRF convertida a temperatura absoluta.
- Altura geopotencial: `(PH + PHB) / g`.
- Viento destaggered para `U` y `V`.
- Velocidad del viento: `sqrt(u^2 + v^2)`.
- Precipitacion acumulada: `RAINC + RAINNC`.

Se debe usar `xarray`/`netcdf4` para abrir el dataset, `xwrf` cuando ayude con metadatos/diagnosticos WRF y `metpy` para unidades, calculos meteorologicos o interpolacion vertical si resulta conveniente.

## 7. Mapas horizontales

Los mapas horizontales deben cubrir:

### Superficie

- Viento 10 m:
  - Campo sombreado: velocidad del viento.
  - Flechas/barbas: direccion con `U10`, `V10`.
- Presion:
  - Usar `PSFC` como minimo.
  - Si se implementa presion reducida a nivel del mar, documentar la formula en comentarios o README.
- Temperatura:
  - Usar `T2` convertida a grados Celsius.
- Precipitacion:
  - Usar `RAINC + RAINNC`.

### 850 hPa

- Interpolar temperatura y geopotencial al nivel de 850 hPa.
- Mostrar geopotencial como contornos y temperatura como sombreado o contornos secundarios.

### 500 hPa

- Interpolar temperatura y geopotencial al nivel de 500 hPa.
- Mostrar geopotencial y temperatura.

### 300 hPa

- Interpolar viento al nivel de 300 hPa.
- Mostrar velocidad del viento como jet stream, con flechas/barbas opcionales.

## 8. Ciudades y dominio

`cities.py` debe incluir una base pequena de ciudades europeas principales, por ejemplo:

- Madrid
- Barcelona
- Lisboa
- Paris
- Londres
- Dublin
- Roma
- Milan
- Berlin
- Amsterdam
- Bruselas
- Viena
- Zurich
- Praga
- Varsovia
- Copenhague
- Oslo
- Estocolmo
- Helsinki
- Atenas

Antes de calcular mapas o rutas, el backend debe validar que los puntos necesarios caen dentro del dominio WRF. Si una ciudad o tramo de ruta queda fuera, la API debe devolver un error claro, por ejemplo:

```json
{
  "detail": "La ruta Madrid-Helsinki queda fuera del dominio WRF disponible."
}
```

## 9. Ruta y perfil de vuelo

El usuario seleccionara ciudad de origen y destino.

La ruta se calculara siguiendo una distancia ortodromica o great-circle:

- Calcular distancia total con la formula haversine o equivalente.
- Generar puntos intermedios sobre la esfera, no una interpolacion lineal simple lat/lon.
- Usar un numero suficiente de muestras, por ejemplo 100 puntos por ruta.

Perfil vertical:

- Primer 20% de distancia: ascenso lineal desde superficie hasta FL330.
- 60% central: crucero a FL330.
- Ultimo 20%: descenso lineal desde FL330 hasta superficie.
- FL330 se aproximara como 33.000 ft, equivalente a unos 10.058 m.

Evolucion temporal:

- Velocidad de crucero: 850 km/h.
- Hora de salida: primer timestep del archivo WRF.
- Tiempo de vuelo: `distancia_total_km / 850`.
- Cada punto de ruta tendra un tiempo asociado.
- La interpolacion atmosferica debe avanzar temporalmente con el avion usando los timesteps WRF disponibles.
- Si el vuelo dura mas que la cobertura temporal del archivo, devolver error o limitar la ruta con mensaje claro. La opcion preferida es devolver error para evitar resultados extrapolados.

## 10. Interpolacion

La interpolacion debe combinar:

- Espacio horizontal: seleccionar o interpolar el punto WRF mas cercano a cada punto de ruta.
- Vertical: interpolar variables 3D a la altura o presion requerida.
- Tiempo: interpolar entre timesteps WRF segun el tiempo de vuelo.

Para una primera version robusta, se acepta:

- Vecino mas cercano horizontal para reducir complejidad.
- Interpolacion vertical lineal.
- Interpolacion temporal lineal.

Si se implementa una interpolacion mas avanzada, debe mantenerse encapsulada en `wrf_processing.py`.

## 11. Riesgos aeronauticos

### Engelamiento

Marcar riesgo de engelamiento donde:

- Temperatura inferior a 0 C.
- Presencia de agua liquida o nube/hidrometeoros:
  - `QCLOUD > umbral`
  - o `QRAIN > umbral`
  - o, como apoyo visual, presencia de `QICE`, `QSNOW`, `QGRAUP`.

Umbral inicial recomendado: `1e-6 kg/kg`.

### Cizalladura

Calcular cizalladura con gradientes del viento:

- Cizalladura vertical: cambio de vector viento con la altura.
- Cizalladura horizontal: cambio de viento entre puntos consecutivos de la ruta.

La grafica debe resaltar zonas donde el gradiente supere un umbral documentado en `risk.py`.

### Visibilidad y conveccion

El NetCDF no contiene CAPE explicito. Por tanto:

- Si en el futuro aparece una variable CAPE, usarla directamente.
- En este archivo, usar un diagnostico aproximado con:
  - precipitacion `RAINC + RAINNC`;
  - hidrometeoros `QCLOUD`, `QRAIN`, `QGRAUP`;
  - movimiento vertical `W` si ayuda a identificar actividad convectiva.

El frontend y las etiquetas de la grafica deben indicar este campo como "riesgo convectivo/visibilidad aproximado", no como CAPE observado.

## 12. Graficas de ruta

La seccion vertical debe mostrar:

- Eje X: distancia recorrida en km o tiempo de vuelo.
- Eje Y: altura en metros o nivel de vuelo.
- Linea de trayectoria del avion.
- Zonas sombreadas de riesgo:
  - engelamiento;
  - cizalladura;
  - visibilidad/conveccion.
- Titulo con origen, destino, distancia y tiempo de vuelo.

## 13. Interfaz de usuario

La primera pantalla debe ser la herramienta util, no una landing page.

Controles minimos:

- Selector de ciudad origen.
- Selector de ciudad destino.
- Selector de campo meteorologico.
- Selector de timestep disponible.
- Boton para generar mapa.
- Boton para simular ruta.

Salidas:

- Panel de mapa meteorologico.
- Panel de perfil/riesgos de ruta.
- Mensajes de error claros.
- Estado de carga mientras el backend procesa.

## 14. Criterios de aceptacion

La practica se considera completa cuando:

- El backend arranca con `uv run uvicorn src.api:app --reload`.
- `GET /api/cities` devuelve ciudades europeas.
- `GET /api/fields` devuelve los campos disponibles.
- `POST /api/map` genera al menos un mapa valido para superficie, 850, 500 y 300 hPa.
- `POST /api/route` calcula una ruta valida dentro del dominio y devuelve una seccion vertical base64.
- El frontend permite seleccionar campos y rutas sin editar codigo.
- Las imagenes devueltas por backend se renderizan correctamente en navegador.
- Las rutas fuera del dominio WRF se rechazan con un mensaje claro.
- La documentacion explica la ausencia de CAPE y el uso de proxies para conveccion/visibilidad.

