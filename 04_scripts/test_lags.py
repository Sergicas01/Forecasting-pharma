import pandas as pd
import numpy as np

def main():
    df_path = '../02_datos/03_Entrenamiento/03_train_tablon_eda.pkl'
    df = pd.read_pickle(df_path)
    
    target_cols = ['m01ab', 'm01ae', 'n02ba', 'n02be', 'n05b', 'n05c', 'r03', 'r06']
    df_lags = pd.DataFrame(index=df.index)
    
    # Probar para el target 'm01ab'
    target = 'm01ab'
    df_temp = pd.DataFrame({
        'granularity': df['granularity'],
        'date': pd.to_datetime(df['date']),
        'val': df[target]
    }, index=df.index)
    
    # Guardar índice original
    df_temp['original_idx'] = df_temp.index
    df_temp = df_temp.sort_values(['granularity', 'date'])
    
    # Calcular lags y rolling
    lag_1 = df_temp.groupby('granularity')['val'].shift(1)
    lag_2 = df_temp.groupby('granularity')['val'].shift(2)
    roll_4 = lag_1.groupby(df_temp['granularity']).rolling(window=4, min_periods=1).mean().reset_index(level=0, drop=True)
    
    # Reindexar
    df_lags[f'{target}_lag_1'] = lag_1
    df_lags[f'{target}_lag_2'] = lag_2
    df_lags[f'{target}_roll_mean_4'] = roll_4
    
    # Imprimir un resumen
    weekly_orig = df[df['granularity'] == 'week'].sort_values('date')
    weekly_lags = df_lags.loc[weekly_orig.index]
    
    print("Original y Lags para Granularidad Semanal:")
    comp = pd.DataFrame({
        'date': weekly_orig['date'],
        'val': weekly_orig[target],
        'lag_1': weekly_lags[f'{target}_lag_1'],
        'lag_2': weekly_lags[f'{target}_lag_2'],
        'roll_4': weekly_lags[f'{target}_roll_mean_4']
    })
    print(comp.head(10))

if __name__ == '__main__':
    main()
