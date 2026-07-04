import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder

def main():
    # 1. Carga del Dataframe
    pkl_path = '../02_datos/03_Entrenamiento/03_train_tablon_eda.pkl'
    df = pd.read_pickle(pkl_path)
    print(f"Dataset original cargado. Filas: {df.shape[0]}, Columnas: {df.shape[1]}")

    # FASE 1: Derivación de características numéricas temporales
    df_fase1 = pd.DataFrame(index=df.index)
    df_fase1['year'] = df['year'].astype(int)
    df_fase1['month'] = df['month'].astype(int)
    df_fase1['hour'] = pd.to_numeric(df['hour'], errors='coerce')
    
    date_series = pd.to_datetime(df['date'])
    df_fase1['day'] = date_series.dt.day
    df_fase1['dayofweek'] = date_series.dt.dayofweek
    df_fase1['weekofyear'] = date_series.dt.isocalendar().week.astype(int)
    df_fase1['is_weekend'] = date_series.dt.dayofweek.isin([5, 6]).astype(int)

    # FASE 2: Codificación de variables categóricas
    ohe = OneHotEncoder(drop='first', sparse_output=False)
    categorical_cols = ['weekday_name', 'granularity']
    ohe_array = ohe.fit_transform(df[categorical_cols])
    
    ohe_cols = []
    for i, col in enumerate(categorical_cols):
        cats = ohe.categories_[i][1:]
        ohe_cols.extend([f"{col}_{cat}" for cat in cats])
        
    df_fase2_binarias = pd.DataFrame(ohe_array, columns=ohe_cols, index=df.index)

    # FASE 3.5: Generación de Retardos (Lags) y Medias Móviles por Granularidad
    df_lags = pd.DataFrame(index=df.index)
    target_cols = ['m01ab', 'm01ae', 'n02ba', 'n02be', 'n05b', 'n05c', 'r03', 'r06']
    
    for target in target_cols:
        df_temp = pd.DataFrame({
            'granularity': df['granularity'],
            'date': pd.to_datetime(df['date']),
            'val': df[target]
        }, index=df.index)
        
        df_temp = df_temp.sort_values(['granularity', 'date'])
        
        lag_1 = df_temp.groupby('granularity')['val'].shift(1)
        lag_2 = df_temp.groupby('granularity')['val'].shift(2)
        roll_4 = lag_1.groupby(df_temp['granularity']).rolling(window=4, min_periods=1).mean().reset_index(level=0, drop=True)
        
        df_lags[f'{target}_lag_1'] = lag_1
        df_lags[f'{target}_lag_2'] = lag_2
        df_lags[f'{target}_roll_mean_4'] = roll_4

    print(f"Características de lag/rolling creadas: {df_lags.shape[1]} columnas.")

    # FASE 4: Unión final
    df_targets = df[target_cols].copy()
    df_final = pd.concat([df_targets, df_fase1, df_fase2_binarias, df_lags], axis=1)

    print("--- VALIDACIONES CRÍTICAS ---")
    assert df_final.shape[0] == df.shape[0], f"Error en filas: {df_final.shape[0]} vs {df.shape[0]}"
    print(f"✓ Validación 1 pasada: Filas conservadas ({df_final.shape[0]})")
    for col in target_cols:
        assert col in df_final.columns, f"Target {col} faltante"
    print("✓ Validación 2 pasada: Targets presentes")
    excluded = ['datum', 'year_month', 'date', 'weekday_name', 'granularity']
    for col in excluded:
        assert col not in df_final.columns, f"Columna excluida {col} presente"
    print("✓ Validación 3 pasada: Columnas excluidas eliminadas")
    assert len(df_final.columns) == len(set(df_final.columns)), "Nombres duplicados"
    print("✓ Validación 4 pasada: Sin nombres duplicados")

    # Guardar
    pkl_out_path = '../02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl'
    os.makedirs(os.path.dirname(pkl_out_path), exist_ok=True)
    df_final.to_pickle(pkl_out_path)
    print(f"Dataframe final guardado en: {pkl_out_path}")
    print(df_final.info())

if __name__ == '__main__':
    main()
