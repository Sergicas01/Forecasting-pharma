# Informe de Transformación y Preparación de Datos — Pharma Sales Forecast

## 1. Descripción General
* **Dataframe de Entrada**: `../02_datos/03_Entrenamiento/03_train_tablon_eda.pkl`
* **Dataframe de Salida (Transformado)**: `../02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl`
* **Número de Filas Finales**: 51.249 (conservadas al 100%)
* **Número de Columnas Finales**: 24
* **Breve Resumen del Problema**: Preparación de características del historial de ventas farmacéuticas para entrenar modelos predictivos basados en árboles (XGBoost, Random Forest, LightGBM) enfocados en 8 categorías terapéuticas (ATC).

---

## 2. Gestión de Variables y Transformaciones

| Variable Original | Tipo Original | Transformación(es) Aplicada(s) | Columna(s) Resultante(s) | Justificación y Notas |
| :--- | :--- | :--- | :--- | :--- |
| **m01ab** a **r06** (8 targets) | num_continua | Ninguna (conservada tal cual) | `m01ab`, `m01ae`, `n02ba`, `n02be`, `n05b`, `n05c`, `r03`, `r06` | Representan el volumen de ventas a predecir para cada categoría. |
| **year** | num_discreta | Conversión a tipo entero | `year` | Año del registro de ventas. |
| **month** | num_discreta | Conversión a tipo entero | `month` | Mes del registro de ventas (1-12). |
| **hour** | num_discreta | Conversión a tipo numérico con manejo de nulos | `hour` | Hora del registro (0-23). Contiene NaN para las filas que no son de granularidad horaria. |
| **weekday_name** | cat_nominal | One-Hot Encoding (drop='first') | `weekday_name_Monday`, `weekday_name_Saturday`, `weekday_name_Sunday`, `weekday_name_Thursday`, `weekday_name_Tuesday`, `weekday_name_Wednesday` | Representa el día de la semana. Se omitió `Friday` como la primera columna para evitar multicolinealidad. |
| **granularity** | cat_nominal | One-Hot Encoding (drop='first') | `granularity_hour`, `granularity_month`, `granularity_week` | Flag del nivel de agregación del registro. Se omitió `day` para evitar la colinealidad perfecta. |
| **date** | fecha | Derivación de componentes: día, día de semana entero, semana del año, is_weekend | `day`, `dayofweek`, `weekofyear`, `is_weekend` | `day`: Día del mes (1-31). <br>`dayofweek`: Día de la semana (0-6). <br>`weekofyear`: Semana del año (1-53). <br>`is_weekend`: Flag binario (1 si es Sáb/Dom, 0 en otro caso). |
| **datum** | texto | Exclusión completa | - | Redundante con `date`, de muy alta cardinalidad. |
| **year_month** | cat_nominal | Exclusión completa | - | Redundante con `year` y `month`. |

---

## 3. Gestión de Versiones Intermedias

Siguiendo el principio de **mantener únicamente las versiones finales** y limpiar el dataframe final:

* **Variables originales excluidas por tener versiones transformadas/codificadas**:
  - `date`: Excluida (reemplazada por `day`, `dayofweek`, `weekofyear`, `is_weekend`).
  - `weekday_name`: Excluida (reemplazada por las columnas dummy OHE).
  - `granularity`: Excluida (reemplazada por las columnas dummy OHE).
* **Variables intermedias excluidas**:
  - No se generaron variables intermedias compartidas complejas en este pipeline simplificado.
* **Variables finales incluidas**:
  - Todas las variables listadas en la columna "Columna(s) Resultante(s)" de la sección 2.

---

## 4. Validaciones Realizadas

Se han ejecutado pruebas unitarias automatizadas durante el pipeline, resultando en éxito rotundo:

1. **Conservación de Filas**: Se verifica que las 51.249 filas iniciales se preservan exactamente en el dataframe transformado.
2. **Targets Presentes**: Se valida la existencia e integridad de los 8 targets farmacológicos.
3. **No Variables Intermedias/Originales Sucias**: Columnas como `datum`, `date`, `weekday_name` y `granularity` han sido correctamente eliminadas de las columnas de características finales.
4. **Colisiones de Nombres**: Se confirma que no existen nombres duplicados de columnas en el dataset final (las 24 columnas tienen identificadores únicos).
5. **Detección de Multicolinealidad Perfecta**: Se ha verificado matemáticamente la matriz de correlación de los dummies OHE creados, confirmando que la opción `drop='first'` ha eliminado la trampa de las variables ficticias (multicolinealidad perfecta).

---

## 5. Resumen Global y Recomendaciones para Modelización

* **Recuento de Variables Generadas**:
  - **Targets**: 8 variables numéricas continuas.
  - **Variables Temporales / Numéricas**: 7 variables (año, mes, hora, día del mes, día de semana entero, semana del año, flag weekend).
  - **Dummies OHE (Binarios)**: 9 variables derivadas de la codificación de días de la semana (6) y granularidad (3).
  - **Total**: 24 variables listas para el entrenamiento.

### ⚠️ Riesgos Clave del Dataset:
* **Mezcla de Granularidades**: El dataset contiene registros agregados horarios, diarios, semanales y mensuales en el mismo tablón. 
  * *Recomendación crítica:* Antes de entrenar los modelos (XGBoost, Random Forest, LightGBM), el usuario **debe filtrar estrictamente por el nivel de granularidad objetivo** que desea predecir. Por ejemplo, para predecir las ventas semanales, se debe filtrar por `granularity_week == 1` (o en su defecto `granularity == 'week'` antes de aplicar OHE) para evitar mezclar escalas de magnitud dispar que distorsionen severamente los gradientes del modelo.
* **Valores Faltantes en `hour`**: La columna `hour` contiene valores NaN en registros diarios, semanales y mensuales. Los modelos XGBoost y LightGBM manejan estos NaN de forma nativa sin requerir imputación, pero si se opta por Random Forest de scikit-learn, se requerirá imputación previa (por ejemplo, con un valor centinela como -1 o la mediana).
