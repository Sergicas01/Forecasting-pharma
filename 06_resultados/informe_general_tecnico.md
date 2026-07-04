# Informe Técnico General — Pharma Sales Forecast

Este informe documenta detalladamente el desarrollo, la arquitectura y los resultados del proyecto predictivo **Pharma Sales Forecast**, cuyo objetivo es el pronóstico de demanda de 8 categorías terapéuticas (ATC) a escala semanal.

---

## 1. Arquitectura del Proyecto y Ciclo de Vida

El desarrollo se estructuró en 9 fases alineadas con las buenas prácticas de ingeniería de datos y machine learning:

1. **Ingestión e Integración (A_01)**: Carga de 4 granularidades de origen (`hourly`, `daily`, `weekly`, `monthly`) y separación temporal del conjunto de validación externa (los últimos 3 meses cronológicos se separaron para evaluar la capacidad de generalización).
2. **Calidad de Datos (A_02)**: Normalización de nombres de columnas a formato lowercase snake_case, corrección lógica de campos temporales imputándolos a partir del campo principal `date` y tipado correcto de las variables.
3. **Análisis Exploratorio de Datos (A_03)**: Detección de patrones de estacionalidad anual, semanal y diaria, y selección de la granularidad **semanal** como la óptima para la planificación de compras.
4. **Ingeniería de Características (A_04)**: Derivación de calendar features y creación de variables autorregresivas (Lags y Medias Móviles) calculadas de forma chronological-safe dentro de cada serie.
5. **Modelización y Selección de Modelos (A_07)**: Búsqueda hiperparamétrica y comparación de regresores mediante validación cruzada temporal.
6. **Preproducción, Limpieza y Despliegue (A_08 y A_09)**: Optimización del código eliminando transformaciones sin varianza, y estructuración de los pipelines automatizados en scripts lineales de producción.

---

## 2. Ingeniería de Características (Features)

Para capturar tanto la estacionalidad del calendario como la inercia reciente de las ventas, se implementaron dos grupos principales de variables:

* **Características del Calendario**:
  - `year`: Año del registro.
  - `month`: Mes (1 a 12).
  - `day`: Día del mes (1 a 31).
  - `weekofyear`: Semana del año según estándar ISO (1 a 53).
* **Características Autorregresivas**:
  - `lag_1` ($t-1$): Ventas registradas la semana anterior.
  - `lag_2` ($t-2$): Ventas registradas hace dos semanas.
  - `roll_mean_4`: Media móvil de las últimas 4 semanas (excluyendo la semana actual para evitar fugas de información):
    $$\text{roll\_mean\_4}_t = \frac{1}{4} \sum_{i=1}^4 \text{lag\_1}_{t-i+1}$$

*Nota de Calidad*: La introducción de lags y medias móviles genera valores nulos (NaNs) en las primeras 4 semanas del dataset histórico. Estas filas se descartan del entrenamiento para que los modelos no lineales puedan ajustarse correctamente.

---

## 3. Estrategia de Validación y Métricas

* **Validación Cruzada Temporal (`TimeSeriesSplit`)**: Dado que los datos presentan dependencia temporal, se usó validación cruzada temporal con **5 particiones (splits)** secuenciales sin barajar (shuffle=False) para simular escenarios reales de predicción hacia el futuro.
* **Métrica Objetivo (`stable_mape`)**: La métrica principal es el MAPE. Dado que algunas categorías (especialmente ansiolíticos e hipnóticos) tienen semanas con ventas en 0, el MAPE estándar provocaría divisiones por cero e infinitos. Se desarrolló un MAPE personalizado que enmascara los valores nulos del denominador:
  $$\text{stable\_mape} = \frac{1}{|Y^*|} \sum_{y_i \in Y^*} \frac{|y_i - \hat{y}_i|}{|y_i|}$$
  donde $Y^* = \{y_i \in Y \mid y_i \neq 0\}$.

---

## 4. Resultados de Modelización y Comparativa de Modelos (Incluyendo XGBoost)

La incorporación de `XGBoost` tras habilitar su soporte en macOS de forma local ha aportado ganancias adicionales de precisión, resultando ganador en 3 de los 8 targets analizados:

| Target (ATC) | Tipo de Fármaco | Algoritmo Ganador | MAPE final | Mejora vs. Baseline Lineal |
| :--- | :--- | :--- | :---: | :---: |
| **m01ab** | Antiinflamatorios no esteroideos | **XGBRegressor** 🏆 | **19.37%** | +8.21% |
| **m01ae** | Antiinflamatorios no esteroideos | **XGBRegressor** 🏆 | **19.94%** | +19.92% |
| **n02ba** | Otros analgésicos y antipiréticos | RandomForestRegressor | **24.76%** | +21.31% |
| **n02be** | Analgésicos (Anilidas - Paracetamol) | RandomForestRegressor | **15.43%** | +10.11% 🚀 |
| **n05b** | Ansiolíticos | RandomForestRegressor | **31.21%** | +36.20% 🚀 |
| **n05c** | Hipnóticos y sedantes | HistGradientBoostingRegressor | **72.88%** | +128.65% |
| **r03** | Anti-asmáticos / Vías respiratorias | **XGBRegressor** 🏆 | **46.08%** | +30.37% |
| **r06** | Antihistamínicos de uso sistémico | RandomForestRegressor | **28.52%** | +42.11% |

### Análisis de Interpretabilidad (Permutation Importance)
Al evaluar qué variables dominan el modelo usando importancia por permutación sobre el conjunto de test:
- En **`n02be` (analgésicos/paracetamol)**, el lag de la semana previa (`n02be_lag_1`) tiene una importancia de **0.184**, siendo el factor número 1 del modelo.
- En **`r06` (antihistamínicos)**, la media móvil de las últimas 4 semanas (`r06_roll_mean_4`) domina con una importancia de **0.177**, seguida de su lag 1 con **0.127**, confirmando que los modelos se guían por las tendencias locales de la demanda.
- En **`r03` (anti-asmáticos)**, la variable temporal de la semana del año (`weekofyear`) tiene una importancia de **0.0298**, seguida de la inercia local `r03_roll_mean_4` (**0.0291**), capturando el fuerte patrón estacional estacional y la inercia a corto plazo.

---

## 5. Arquitectura de Despliegue en Producción

El pipeline se automatizó mediante scripts Python con un diseño **pipeline-first** basado en `scikit-learn` y serialización robusta mediante `pickle`:

* **`07_despliegue/01_reentrenamiento.py`**:
  - Carga el archivo crudo de series temporales `salesweekly.csv`.
  - Procesa y genera las variables temporales y autorregresivas.
  - Define un preprocesador `ColumnTransformer` para aislar las variables del target de forma dinámica.
  - Envuelve el pipeline en una búsqueda cruzada aleatoria (`RandomizedSearchCV`) que evalúa y optimiza hiperparámetros de `RandomForest`, `HistGradientBoosting` y `XGBoost`.
  - Serializa los 8 pipelines entrenados en un diccionario en `artefacto_pipeline.pkl`.
* **`07_despliegue/02_produccion_scoring.py`**:
  - Diseñado para recibir argumentos de entrada (`--input`) y salida (`--output`) mediante consola.
  - Carga el artefacto serializado, calcula los lags del archivo entrante y genera las predicciones acotadas a valores no negativos (0 o superior), evitando ventas negativas.
