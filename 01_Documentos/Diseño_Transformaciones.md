# Diseño de Transformaciones — Proyecto Pharma Sales Forecast

**Estado**: CONGELADO  
**Fecha**: 4 de Julio, 2026  
**Objetivo del proyecto**: Pronosticar ventas en 8 categorías de fármacos independientes a escala diaria/semanal.  
**Target**: `m01ab`, `m01ae`, `n02ba`, `n02be`, `n05b`, `n05c`, `r03`, `r06`  
**Modelos priorizados**: Modelos basados en árboles (XGBoost, Random Forest, LightGBM).

---

## Tabla de diseño de transformaciones

Dado que se han priorizado **modelos basados en árboles**, los cuales son invariantes a la escala de las variables, **no se aplicará ningún tipo de reescalado o normalización (StandardScaler/MinMaxScaler)** en la FASE 3, lo cual simplifica el pipeline y mantiene la interpretabilidad directa de los datos.

| Variable | Tipo_Original | Trans_1 | Tipo_Res_1 | Trans_2 | Tipo_Res_2 | Escalado_Final | Es_Final | Incluir_DF | Nombre_Col_Final | Justificación |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **m01ab** | num_continua | - | - | - | - | NO | SÍ | SÍ | `m01ab` | Variable objetivo (target) |
| **m01ae** | num_continua | - | - | - | - | NO | SÍ | SÍ | `m01ae` | Variable objetivo (target) |
| **n02ba** | num_continua | - | - | - | - | NO | SÍ | SÍ | `n02ba` | Variable objetivo (target) |
| **n02be** | num_continua | - | - | - | - | NO | SÍ | SÍ | `n02be` | Variable objetivo (target) |
| **n05b** | num_continua | - | - | - | - | NO | SÍ | SÍ | `n05b` | Variable objetivo (target) |
| **n05c** | num_continua | - | - | - | - | NO | SÍ | SÍ | `n05c` | Variable objetivo (target) |
| **r03** | num_continua | - | - | - | - | NO | SÍ | SÍ | `r03` | Variable objetivo (target) |
| **r06** | num_continua | - | - | - | - | NO | SÍ | SÍ | `r06` | Variable objetivo (target) |
| **year** | num_discreta | - | - | - | - | NO | SÍ | SÍ | `year` | Año (como número entero) |
| **month** | num_discreta | - | - | - | - | NO | SÍ | SÍ | `month` | Mes (como número entero) |
| **hour** | num_discreta | - | - | - | - | NO | SÍ | SÍ | `hour` | Hora (0-23, contiene NaN en filas agregadas) |
| **weekday_name** | cat_nominal | OHE | binaria | - | - | NO | SÍ | SÍ | `weekday_name_*` | Día de la semana en formato dummy (drop='first') |
| **granularity** | cat_nominal | OHE | binaria | - | - | NO | SÍ | SÍ | `granularity_*` | Nivel de agregación dummy (drop='first') |
| **date** | fecha | extract_day | num_discreta | - | - | NO | SÍ | SÍ | `day` | Día del mes (1-31) para detectar fin de mes |
| **date** | fecha | extract_dow | num_discreta | - | - | NO | SÍ | SÍ | `dayofweek` | Día de la semana (0-6) para ordenación natural |
| **date** | fecha | extract_woy | num_discreta | - | - | NO | SÍ | SÍ | `weekofyear` | Semana del año (1-53) para estacionalidad anual |
| **date** | fecha | is_weekend | binaria | - | - | NO | SÍ | SÍ | `is_weekend` | Flag indicando fin de semana (1 = Sáb/Dom, 0 = Lun-Vie) |
| **date** | fecha | exclude | - | - | - | NO | SÍ | NO | - | Excluir fecha original (no usable en árboles) |
| **datum** | texto | exclude | - | - | - | NO | SÍ | NO | - | Excluido (redundante, alta cardinalidad) |
| **year_month** | cat_nominal | exclude | - | - | - | NO | SÍ | NO | - | Excluido (redundante, alta cardinalidad) |

---

## Decisiones tomadas

* **No reescalar variables**: Al usar modelos basados en árboles, no se requiere estandarización (StandardScaler) ni normalización (MinMaxScaler/RobustScaler). Se excluyen los escaladores para evitar complejidad innecesaria.
* **One-Hot Encoding**: Se aplicará One-Hot Encoding a `weekday_name` y `granularity` con la opción `drop='first'` para evitar dummies redundantes.
* **Características de fecha**: Se extraen del campo `date` el día del mes, día de la semana (entero), semana del año (entero) y un flag de fin de semana.
* **Hour con valores faltantes**: La variable `hour` contiene NaN para registros de granularidad diaria, semanal y mensual. Se mantendrá como está, ya que XGBoost/LightGBM pueden manejar valores nulos de forma nativa.

---

## Riesgos identificados

1. **Datos de granularidades mezcladas**: El tablón actual combina registros horarios, diarios, semanales y mensuales. Si se entrena un único modelo sobre todos estos registros simultáneamente, la predicción fallará debido a la diferencia masiva en las escalas de venta (por ejemplo, ventas de un mes completo frente a ventas de una hora).
   * *Mitigación:* Se recomienda filtrar el tablón final en la fase de modelado por una sola granularidad (ej. `granularity == 'week'`) antes de entrenar cualquier modelo.
