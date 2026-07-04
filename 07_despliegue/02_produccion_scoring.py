import argparse
import re
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np
import pickle

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTEFACTO_PATH = PROJECT_ROOT / "07_despliegue" / "artefacto_pipeline.pkl"
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

# 2. Configurar Argumentos de Consola
parser = argparse.ArgumentParser(description="Script de scoring en producción para Pharma Sales Forecast.")
parser.add_argument("--input", required=True, help="Ruta del CSV de entrada con los datos históricos/nuevos.")
parser.add_argument("--output", required=True, help="Ruta de salida del CSV con las predicciones generadas.")
args = parser.parse_args()

# 3. Cargar el Artefacto
print(f"Cargando artefacto de pipelines desde: {ARTEFACTO_PATH}")
with open(ARTEFACTO_PATH, "rb") as f:
    trained_pipelines = pickle.load(f)

# 4. Leer y Procesar Datos Nuevos
print(f"Cargando y preparando datos de entrada desde: {args.input}")
df_raw = pd.read_csv(args.input)
df_processed = prepara_datos(df_raw)

# 5. Generar Predicciones para cada Target
predictions = {"datum": df_processed['datum']}

for target in TARGETS:
    if target in trained_pipelines:
        print(f"Prediciendo para target: {target}...")
        pipe = trained_pipelines[target]
        preds = pipe.predict(df_processed)
        # Asegurar predicciones no negativas (ventas físicas)
        predictions[target] = np.clip(preds, 0, None)

# 6. Guardar Resultados de Scoring
df_predictions = pd.DataFrame(predictions)
df_predictions.to_csv(args.output, index=False)
print(f"\n✅ Predicciones guardadas exitosamente en: {args.output}")
