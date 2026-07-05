import os
import re
import json
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import make_column_transformer
from sklearn.metrics import make_scorer
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False
import pickle

# Definición de rutas y constantes
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "02_datos" / "01_Originales" / "salesweekly.csv"
ARTEFACTO_PATH = PROJECT_ROOT / "06_despliegue" / "artefacto_pipeline.pkl"
TARGETS = ['m01ab', 'm01ae', 'n02ba', 'n02be', 'n05b', 'n05c', 'r03', 'r06']

# 1. Función de procesamiento de filas y preparación temporal
def prepara_datos(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    
    # Normalización de columnas
    def normalize_column_name(col: str) -> str:
        col = str(col).strip().lower()
        col = unicodedata.normalize("NFKD", col)
        col = "".join(ch for ch in col if not unicodedata.combining(ch))
        col = re.sub(r"[^a-z0-9]+", "_", col)
        col = re.sub(r"_+", "_", col).strip("_")
        return col
        
    df_clean.columns = [normalize_column_name(c) for c in df_clean.columns]
    
    # Asegurar tipo fecha y orden cronológico
    df_clean['date'] = pd.to_datetime(df_clean['datum'], errors='coerce')
    df_clean = df_clean.sort_values('date').reset_index(drop=True)
    
    # Extracción de características del calendario
    date_series = pd.to_datetime(df_clean['date'])
    df_clean['year'] = date_series.dt.year
    df_clean['month'] = date_series.dt.month
    df_clean['day'] = date_series.dt.day
    df_clean['weekofyear'] = date_series.dt.isocalendar().week.astype(int)
    
    # Generación de lags y medias móviles sobre la serie
    for target in TARGETS:
        if target in df_clean.columns:
            lag_1 = df_clean[target].shift(1)
            lag_2 = df_clean[target].shift(2)
            roll_4 = lag_1.rolling(window=4, min_periods=1).mean()
            
            df_clean[f'{target}_lag_1'] = lag_1
            df_clean[f'{target}_lag_2'] = lag_2
            df_clean[f'{target}_roll_mean_4'] = roll_4
            
    # Eliminar filas iniciales con NaNs del retardo
    df_clean = df_clean.dropna(subset=[f'{t}_roll_mean_4' for t in TARGETS if t in df_clean.columns]).reset_index(drop=True)
    return df_clean

# 2. Definición del Scoring MAPE Estable
def stable_mape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mask = y_true != 0
    if not np.any(mask):
        return 0.0
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask]))

mape_scorer = make_scorer(stable_mape, greater_is_better=False)

# 3. Carga y preparación del dataset
print(f"Cargando dataset desde: {CSV_PATH}")
df_raw = pd.read_csv(CSV_PATH)
df_clean = prepara_datos(df_raw)

# Split temporal (forecasting split: últimos 3 meses en validación)
max_date = df_clean['date'].max()
cutoff_date = max_date - pd.DateOffset(months=3)

df_train = df_clean[df_clean['date'] < cutoff_date].copy()
print(f"Dataset semanal de entrenamiento preparado. Filas: {df_train.shape[0]}")

# 4. Búsqueda e hiperparametrización por target
tscv = TimeSeriesSplit(n_splits=3)
trained_pipelines = {}

for target in TARGETS:
    print(f"\n--- INICIANDO BÚSQUEDA Y OPTIMIZACIÓN PARA TARGET: {target} ---")
    
    # Columnas específicas del target
    features_target = ['year', 'month', 'day', 'weekofyear', f'{target}_lag_1', f'{target}_lag_2', f'{target}_roll_mean_4']
    
    # 5. Pipeline-first: preprocesador y pipeline base
    preprocesador = make_column_transformer(
        ("passthrough", features_target),
        remainder="drop"
    )
    
    pipe = Pipeline([
        ('preprocessor', preprocesador),
        ('regressor', RandomForestRegressor(random_state=42))
    ])
    
    # 6. Espacio de hiperparámetros
    param_distributions = [
        {
            'regressor': [RandomForestRegressor(random_state=42)],
            'regressor__n_estimators': [50, 100, 200],
            'regressor__max_depth': [3, 5, 8, None],
            'regressor__min_samples_split': [2, 5, 10],
            'regressor__min_samples_leaf': [1, 2, 4]
        },
        {
            'regressor': [HistGradientBoostingRegressor(random_state=42)],
            'regressor__max_iter': [50, 100, 150],
            'regressor__learning_rate': [0.01, 0.05, 0.1, 0.2],
            'regressor__max_depth': [3, 5, 8, None],
            'regressor__min_samples_leaf': [5, 10, 20]
        }
    ]
    
    if XGB_AVAILABLE:
        param_distributions.append({
            'regressor': [XGBRegressor(random_state=42)],
            'regressor__n_estimators': [50, 100, 200],
            'regressor__max_depth': [3, 5, 7],
            'regressor__learning_rate': [0.01, 0.05, 0.1, 0.2],
            'regressor__subsample': [0.7, 0.8, 1.0],
            'regressor__colsample_bytree': [0.7, 0.8, 1.0]
        })
    
    # 7. Ejecutar Búsqueda Cruzada
    search = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_distributions,
        n_iter=15,
        cv=tscv,
        scoring=mape_scorer,
        random_state=42,
        n_jobs=-1,
        refit=True
    )
    
    X_train = df_train[features_target]
    y_train = df_train[target]
    
    search.fit(df_train, y_train)
    
    # Registrar mejor pipeline
    best_pipe = search.best_estimator_
    trained_pipelines[target] = best_pipe
    
    print(f"Mejor estimador seleccionado: {search.best_params_['regressor'].__class__.__name__}")
    print(f"Mejores hiperparámetros: {search.best_params_}")
    print(f"Mejor stable_mape en CV: {-search.best_score_:.4f}")

# 8. Serialización de los artefactos
ARTEFACTO_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(ARTEFACTO_PATH, "wb") as f:
    pickle.dump(trained_pipelines, f)

print(f"\n✅ Serialización exitosa. Todos los pipelines guardados en: {ARTEFACTO_PATH}")
