# Informe de Preselección de Variables — Pharma Sales Forecast

## 1. Decisión y Justificación

En esta fase del proyecto **Pharma Sales Forecast**, se ha decidido **NO aplicar una preselección supervisada de variables**. 

### Razones Técnicas:
1. **Modelos Objetivo Priorizados**: Los modelos definidos en la fase de diseño son de la familia de **árboles de decisión y ensamblados** (XGBoost, Random Forest y LightGBM).
2. **Resiliencia de los Modelos**: Los modelos basados en árboles realizan una selección interna y recursiva de variables al dividir los nodos. Son intrínsecamente inmunes a variables irrelevantes, no se ven afectados por la escala de las variables, y manejan de forma muy eficiente la correlación y multicolinealidad sin comprometer la estabilidad del modelo (a diferencia de los modelos lineales como la regresión lineal o logística).
3. **Relación Costo-Beneficio**: Dado el tamaño del conjunto de características actual (16 variables de entrada), el costo computacional de realizar preselección es nulo, pero el beneficio predictivo de eliminar variables es mínimo y podría resultar en una pérdida de información útil para el modelado temporal y de granularidades.

---

## 2. Estado del Dataset

Dado que no se ha filtrado ninguna variable, el dataset se mantiene intacto según el entregable de la fase de preparación de datos:

* **Dataframe de Entrada y Salida**: `../02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl`
* **Número de Filas**: 51,249
* **Número de Features**: 16 variables de entrada
* **Número de Targets**: 8 variables (categorías de fármacos: `m01ab`, `m01ae`, `n02ba`, `n02be`, `n05b`, `n05c`, `r03`, `r06`)
* **Total Columnas**: 24

---

## 3. Recomendaciones para el Agente de Modelización (A_07)

1. **Filtrado por Granularidad**: Es de crítica importancia que antes de entrenar el modelo se filtre el tablón por la granularidad objetivo (por ejemplo, `granularity_week == 1` para predicciones semanales o `granularity_month == 1` para mensuales), ya que el tablón combina múltiples granularidades cuyas escalas de volumen de ventas difieren significativamente.
2. **Valores Faltantes (`hour`)**: La columna `hour` contiene valores nulos para granularidades no horarias. Algoritmos como XGBoost y LightGBM lo manejan nativamente, pero para Random Forest de scikit-learn se debe aplicar una imputación simple (ej. imputar con `-1` o la mediana).
