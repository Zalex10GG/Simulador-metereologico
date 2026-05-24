# Simulador Meteorologico de Rutas Aeronauticas

Simulador academico que visualiza campos meteorologicos de un archivo WRF y simula riesgos aeronauticos en rutas entre ciudades europeas.

## Requisitos

- Python >= 3.12
- `uv` para gestion de dependencias
- Archivo WRF en `data/wrfout_d01_2009-12-16.nc`

## Instalacion y ejecucion

```bash
uv sync
uv run uvicorn src.api:app --reload
```

La API arranca en `http://localhost:8000`. El frontend se sirve desde la misma URL.

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `GET` | `/health` | Salud de la API |
| `GET` | `/api/cities` | Ciudades europeas disponibles |
| `GET` | `/api/fields` | Campos meteorologicos visualizables |
| `GET` | `/api/times` | Timesteps WRF disponibles |
| `POST` | `/api/map` | Genera mapa meteorologico horizontal |
| `POST` | `/api/route` | Simula ruta y genera perfil vertical de riesgos |

## Mapas disponibles

- `surface_wind`: Viento a 10 m con barbas de direccion
- `surface_pressure`: Presion en superficie (PSFC)
- `surface_temperature`: Temperatura a 2 m en Celsius
- `surface_precipitation`: Precipitacion acumulada (RAINC + RAINNC)
- `z_t_850`: Geopotencial y temperatura a 850 hPa
- `z_t_500`: Geopotencial y temperatura a 500 hPa
- `jet_300`: Jet stream a 300 hPa

## Riesgos aeronauticos

- **Engelamiento (icing)**: Temperatura < 0 C con presencia de hidrometeoros (QCLOUD, QRAIN)
- **Cizalladura (wind shear)**: Gradiente vertical y horizontal del vector viento
- **Conveccion/Visibilidad**: Aproximacion mediante precipitacion e hidrometeoros como proxy (no se usa CAPE porque el archivo WRF no lo contiene)

## Perfil de vuelo

- 20% inicial: ascenso lineal hasta FL330 (~10058 m)
- 60% central: crucero a FL330
- 20% final: descenso lineal hasta superficie
- Velocidad de crucero: 850 km/h
- Interpolacion espacial: vecino mas cercano horizontal, interpolacion vertical por nivel mas cercano
- Interpolacion temporal: lineal entre timesteps WRF

## Limitaciones

- El CAPE no esta disponible en este archivo WRF. El riesgo de conveccion/visibilidad se aproxima mediante precipitacion acumulada y concentracion de hidrometeoros.
- La interpolacion horizontal usa vecino mas cercano, no interpolacion bilineal.
- Las rutas cuyo tiempo de vuelo exceda la cobertura temporal del WRF son rechazadas con un mensaje de error.
- Las ciudades y puntos de ruta fuera del dominio WRF son rechazados.
- La biblioteca `xwrf` esta disponible para post-procesamiento avanzado pero no se usa directamente en los diagnosticos base.

## Dataset WRF

Archivo: `wrfout_d01_2009-12-16.nc`

- Dominio: aprox. 27N-57N, 27W-14E (Europa occidental)
- 17 timesteps (~48 horas, espaciado ~3h)
- 44 niveles verticales
- 120 x 99 puntos horizontales
