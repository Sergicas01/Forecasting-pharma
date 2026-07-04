# Informe de EDA - Pharma Sales

## Resumen del dataset
- Dataframe cargado: `../02_datos/03_Entrenamiento/02_train_tablon_calidad.pkl`
- Dataframe EDA guardado: `../02_datos/03_Entrenamiento/03_train_tablon_eda.pkl`
- Filas: 51.249
- Columnas: 16

## Tipos de variables detectadas
- Numéricas discretas: `year`, `month`
- Numéricas continuas: `m01ab`, `m01ae`, `n02ba`, `n02be`, `n05b`, `n05c`, `r03`, `r06`, `hour`
- Categóricas: `datum`, `weekday_name`, `granularity`
- Alta cardinalidad: `datum`
- Texto: `datum`
- Fechas: `date`
- Variable derivada de fecha: `year_month`

## Hallazgos clave
- No se detectaron columnas constantes.
- No hay columnas con más del 20% de valores faltantes.
- La columna `hour` tiene algunos valores faltantes (48.856 no nulos de 51.249 filas), por lo que conviene revisar su uso en el modelo.
- `datum` es de muy alta cardinalidad (50.958 valores diferentes), lo cual sugiere que probablemente actúa como identificador temporal o de instancia. Debe tratarse con cuidado en el modelado o excluirse si no aporta información predictiva.
- `weekday_name` está equilibrada entre los días de la semana, sin evidencias de sesgo fuerte de frecuencia.
- `granularity` está dominada por `hour` en el 95,3% de los registros, mientras que el resto de niveles aportan pocos registros.
- La distribución por `year` es casi uniforme para 2014-2018 y decrece en 2019, lo cual puede reflejar un dataset truncado o un periodo incompleto de 2019.
- La distribución por `month` muestra mayor frecuencia en los meses 1, 3, 5 y 7, aunque no hay valores extremos muy disparejos.

## Observaciones de modelado
- `datum` debe tratarse como columna de alta cardinalidad / posible identificador temporal. Si se usa como feature, debe transformarse con cuidado o limitarse a componentes agregados.
- `date` ya está en formato datetime y se generó `year_month` para análisis de tendencias temporales.
- La ausencia de valores faltantes generales es positiva para los modelos, pero el `hour` requiere una estrategia de imputación si se utiliza.

## Acciones realizadas
- Cargado el dataframe actual desde `copilot-instructions.md`.
- Clasificado el tipo de variables y realizado la detección preliminar de calidad.
- Generado gráficos de frecuencia para variables numéricas discretas, densidad para variables numéricas continuas, barras para variables categóricas y top-20 para `datum`.
- Generado un gráfico temporal mensual basado en `date`.
- Guardado el dataframe de trabajo final como `../02_datos/03_Entrenamiento/03_train_tablon_eda.pkl`.

## Comparación entre versiones de dataframe
- `02_train_tablon_calidad.pkl`: dataset de calidad de datos previo.
- `03_train_tablon_eda.pkl`: dataset actual de EDA con la columna derivada `year_month` añadida.

## Recomendaciones
- Revisar la estrategia para `datum` antes de avanzar a modelado.
- Evaluar si `hour` debe imputarse o reemplazarse por categorías temporales.
- Verificar si el año 2019 representa un periodo completo o está truncado.

---

> Si deseas, puedo añadir comentarios adicionales específicos del forecast o incorporar una sección de conclusiones en función del objetivo de la predicción.
