# Simulador Meteorologico de Rutas Aeronauticas

Simulador academico que visualiza campos meteorologicos de un archivo WRF y simula riesgos aeronauticos en rutas entre ciudades europeas.

## Requisitos

- Python >= 3.12
- `uv` para gestion de dependencias
- Archivos WRF en `data/wrfout_*.nc` (5 snapshots, ~1.3 GB total)

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
| `POST` | `/api/route/export` | Exporta datos de ruta como JSON |

## Mapas disponibles

- `surface_wind`: Viento a 10 m con barbas de direccion
- `surface_pressure`: Presion en superficie (PSFC)
- `mslp`: Presion reducida a nivel del mar (formula barometrica)
- `surface_temperature`: Temperatura a 2 m en Celsius
- `surface_precipitation`: Precipitacion acumulada (RAINC + RAINNC)
- `z_t_850`: Geopotencial y temperatura a 850 hPa
- `z_t_500`: Geopotencial y temperatura a 500 hPa
- `jet_300`: Jet stream a 300 hPa

## Riesgos aeronauticos

- **Engelamiento (icing)**: Temperatura < 0 C con presencia de hidrometeoros (QCLOUD, QRAIN, QICE, QSNOW, QGRAUP)
- **Cizalladura (wind shear)**: Gradiente vertical y horizontal del vector viento
- **Turbulencia (turbulence)**: Velocidad de viento > 25 m/s en nivel de vuelo (CAT proxy)
- **Conveccion (convection)**: Precipitacion + hidrometeoros + velocidad vertical (W) como proxy de CAPE
- **Baja visibilidad (visibility)**: QCLOUD en nivel de vuelo como proxy de nubes/niebla

> Nota: El CAPE no esta disponible en este archivo WRF. Conveccion y visibilidad se aproximan mediante variables disponibles.

## Niveles de vuelo disponibles

- `FL240` (~7.315 m)
- `FL330` (~10.058 m, por defecto)
- `FL380` (~11.582 m)

## Perfil de vuelo

- 20% inicial: ascenso lineal hasta nivel de crucero seleccionado
- 60% central: crucero
- 20% final: descenso lineal hasta superficie
- Velocidad de crucero: 850 km/h
- Interpolacion espacial: vecino mas cercano horizontal, interpolacion vertical lineal
- Interpolacion temporal: lineal entre timesteps WRF

## Dataset WRF

Archivos: `wrfout_2026-05-11_*.nc` (5 snapshots cada 30 minutos)

- Dominio: 28.2N-60.9N, 20.9W-47.4E (Europa occidental y Mediterraneo)
- 5 timesteps (14:00 - 16:00 UTC, espaciado 30 min, cobertura 120 min)
- 47 niveles verticales
- 471 x 345 puntos horizontales (~1.3 km de resolucion)

## Limitaciones

- El CAPE no esta disponible en este archivo WRF. Los riesgos de conveccion y visibilidad se aproximan mediante precipitacion acumulada, hidrometeoros y velocidad vertical.
- La interpolacion horizontal usa vecino mas cercano, no interpolacion bilineal.
- Las rutas cuyo tiempo de vuelo exceda la cobertura temporal del WRF (120 min) son rechazadas.
- Las ciudades y puntos de ruta fuera del dominio WRF son rechazados.
- La presion reducida a nivel del mar (MSLP) se calcula con la formula barometrica estandar usando PSFC, HGT y T2.
- Los datos WRF no estan trackeados en git por su tamano (~1.3 GB).
