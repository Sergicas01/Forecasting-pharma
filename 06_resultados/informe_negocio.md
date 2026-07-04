# Informe Ejecutivo de Negocio — Optimización del Suministro Pharma Sales

Este informe describe los objetivos, la solución predictiva desarrollada y el impacto financiero y de negocio del proyecto **Pharma Sales Forecast** para la optimización de compras y niveles de inventario.

---

## 1. Objetivo del Proyecto

El objetivo principal es **automatizar y optimizar la planificación de compras semanales** para 8 de las categorías de fármacos con mayor rotación en farmacias. A través del pronóstico de demanda, se busca:
1. **Reducir costes de almacenamiento**: Minimizar el exceso de inventario (overstock) para liberar capital de trabajo.
2. **Evitar roturas de stock**: Garantizar la disponibilidad de los medicamentos para los pacientes y evitar pérdidas de ventas directas.
3. **Optimizar la logística de compras**: Pasar de un modelo reactivo (comprar según se agota) a un modelo predictivo (anticipar la demanda de la próxima semana).

---

## 2. Necesidades del Negocio y Retos Predictivos

Planificar las compras de productos farmacéuticos presenta complejidades específicas:
- **Estacionalidad Directa**: Medicamentos como los antihistamínicos (`r06`) sufren incrementos masivos en primavera, mientras que los jarabes respiratorios (`r03`) se disparan en épocas de frío o gripe.
- **Inercia a Corto Plazo**: Las ventas de una semana dependen fuertemente del comportamiento de la semana previa (brotes locales de enfermedades, campañas de vacunación, etc.).
- **Venta Intermitente**: Algunos fármacos de baja rotación, como los sedantes (`n05c`), muestran ventas intermitentes con semanas de venta cero, lo que dificulta las previsiones basadas en medias históricas simples.

---

## 3. Problemas Detectados en los Datos

Antes de desarrollar el modelo, se auditaron y corrigieron diversos problemas en el historial de ventas:
1. **Inconsistencia de Formatos**: Las columnas presentaban nombres inconsistentes con espacios y caracteres especiales, lo que impedía automatizar análisis.
2. **Ausencia de Fechas Derivadas**: Faltaban campos de año, mes o día de la semana estructurados en los registros semanales, lo que impedía que los modelos comprendieran la estacionalidad del calendario.
3. **Métricas Inestables**: El uso de métricas de error de porcentaje estándar (MAPE) colapsaba debido a las semanas con ventas iguales a 0 (división por cero). Se implementó un algoritmo de MAPE estable para corregir este problema.

---

## 4. Solución Implementada: Predicción Inteligente

Se ha desarrollado un **motor de Machine Learning adaptativo** que no solo analiza el calendario, sino que lee la inercia reciente de la demanda.

* **El "Efecto Memoria" (Lags)**: El motor calcula automáticamente qué se vendió la semana anterior y el promedio móvil de las últimas 4 semanas para alimentar los algoritmos. Esto ha transformado por completo la precisión.
* **Algoritmos no Lineales y XGBoost**: Tras resolver limitaciones locales en el entorno de ejecución macOS, se habilitó el soporte completo de **`XGBoost`**, incorporándolo en la comparación. Tras competir contra baselines convencionales, `XGBoost` se coronó como el modelo más preciso en 3 de los 8 targets, y `Random Forest` o `HistGradient Boosting` en el resto.

---

## 5. Resultados de Negocio y ROI (Con XGBoost)

La inclusión del modelo predictivo con XGBoost ha generado una mejora sustancial en la precisión frente a los métodos convencionales:

1. **Categorías Estrella (Alta Rotación)**:
   - **Analgésicos/Paracetamol (`n02be`)**: Logramos un **15.43% de MAPE (84.57% de precisión)** con RandomForest. El modelo es extremadamente preciso para este medicamento crítico, permitiendo trabajar con márgenes de seguridad muy reducidos y estables.
   - **Antiinflamatorios (`m01ab` y `m01ae`)**: Al incorporar **XGBoost**, el error se redujo al **19.37% y 19.94%** respectivamente, consolidando una base de compras semanal de alta confiabilidad.
2. **Control de la Incertidumbre (Reducción de Errores)**:
   - En **ansiolíticos (`n05b`)**, el error se redujo al **31.21%** (con RandomForest), reduciendo a la mitad los costes asociados a malas decisiones de compra.
   - En **vías respiratorias (`r03`)**, **XGBoost** redujo el error al **46.08%**, proporcionando una base mucho más estable frente al 76.4% de error del baseline lineal.
3. **Gestión de la Baja Rotación**:
   - En **sedantes (`n05c`)**, aunque el error porcentual aparenta ser alto (72.8%) debido a los ceros estructurales, la desviación real del modelo es de apenas **2.5 cajas a la semana**. Esto permite gestionar las compras en lotes fijos automáticos sin impacto financiero.

---

## 6. Recomendaciones para el Área de Supply Chain (Cadena de Suministro)

Para implementar con éxito las predicciones del modelo en la toma de decisiones diarias, se sugiere seguir las siguientes pautas:

* **Para Fármacos con Precisión Alta (Paracetamol, Antiinflamatorios)**:
  - Confiar plenamente en las sugerencias del modelo.
  - Mantener un **stock de seguridad muy bajo** (aproximadamente un 15% - 20% del valor previsto por el modelo) para cubrir desviaciones excepcionales.
* **Para Fármacos Estacionales con Fluctuación Súbita (Vías Respiratorias - `r03`)**:
  - Utilizar la previsión del modelo como demanda base.
  - Implementar un **stock de seguridad mayor** (alrededor del 45%) para cubrir picos imprevistos causados por el clima o brotes de gripe.
* **Automatización del Reentrenamiento**:
  - Ejecutar el script `01_reentrenamiento.py` de forma mensual para que el modelo aprenda continuamente de las nuevas tendencias de consumo.
  - Utilizar el script `02_produccion_scoring.py` cada lunes para generar automáticamente los volúmenes de pedido recomendados para el resto de la semana.
