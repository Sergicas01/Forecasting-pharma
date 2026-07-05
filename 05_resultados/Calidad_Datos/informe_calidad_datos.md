# Informe de calidad de datos

## Resumen general

- Filas procesadas: 51,249
- Columnas originales: 15
- Columnas finales: 15
- Duplicados completos detectados: 0
- Se mantuvieron las columnas de negocio y se corrigieron los campos derivados de la fecha.

## Problemas detectados

- Nombres de columnas con espacios y formato inconsistente.
- Columnas de fecha derivadas con valores faltantes en filas semanales y mensuales.
- Valores inválidos en la columna hour para granularidades no horarias (marcadores 248/276).
- Valores categóricos con formato inconsistente en granularity y weekday_name.

## Decisiones y transformaciones aplicadas

### 1. Estandarización de nombres

- `datum` -> `datum`
- `M01AB` -> `m01ab`
- `M01AE` -> `m01ae`
- `N02BA` -> `n02ba`
- `N02BE` -> `n02be`
- `N05B` -> `n05b`
- `N05C` -> `n05c`
- `R03` -> `r03`
- `R06` -> `r06`
- `Year` -> `year`
- `Month` -> `month`
- `Hour` -> `hour`
- `Weekday Name` -> `weekday_name`
- `granularity` -> `granularity`
- `date` -> `date`

### 2. Tipado

- `year`, `month` y `hour` convertidas a enteros nullable (`Int64`).
- `granularity` estandarizada a minúsculas y sin espacios.
- `weekday_name` normalizada a formato de texto limpio y completada a partir de `date`.

### 3. Valores ausentes

- Se imputaron `year`, `month` y `weekday_name` a partir de `date`.
- Se dejaron como nulos los valores de `hour` para granularidades no horarias.
- No se detectaron valores ocultos de vacío tipo `''`, `' '`, `'-'` o `N/A` en las columnas principales.

### 4. Reglas lógicas

- Se corrigió `hour` para que solo tenga sentido en filas con `granularity='hour'`.
- Se validó que `year`, `month` y `weekday_name` fuesen consistentes con la fecha real del registro.

## Resumen variable a variable

- `datum`: tipo original `object` -> tipo final `object`
- `m01ab`: tipo original `float64` -> tipo final `float64`
- `m01ae`: tipo original `float64` -> tipo final `float64`
- `n02ba`: tipo original `float64` -> tipo final `float64`
- `n02be`: tipo original `float64` -> tipo final `float64`
- `n05b`: tipo original `float64` -> tipo final `float64`
- `n05c`: tipo original `float64` -> tipo final `float64`
- `r03`: tipo original `float64` -> tipo final `float64`
- `r06`: tipo original `float64` -> tipo final `float64`
- `year`: tipo original `float64` -> tipo final `Int64`
- `month`: tipo original `float64` -> tipo final `Int64`
- `hour`: tipo original `float64` -> tipo final `Int64`
- `weekday_name`: tipo original `object` -> tipo final `object`
- `granularity`: tipo original `object` -> tipo final `object`
- `date`: tipo original `datetime64[ns]` -> tipo final `datetime64[ns]`

## Valores faltantes finales

```text
datum              0
m01ab              0
m01ae              0
n02ba              0
n02be              0
n05b               0
n05c               0
r03                0
r06                0
year               0
month              0
hour            2393
weekday_name       0
granularity        0
date               0
```

## Archivos generados

- Dataframe limpio: `02_datos\03_Entrenamiento\02_train_tablon_calidad.pkl`
- Informe: `05_resultados\Calidad_Datos\informe_calidad_datos.md`
- Instrucciones actualizadas: `copilot-instructions.md`