import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, make_scorer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except Exception as e:
    XGB_AVAILABLE = False
    print(f"⚠️ Warning: XGBoost could not be loaded: {e}")
    print("XGBRegressor will be skipped, but model selection will proceed with the other candidates.")
import warnings
warnings.filterwarnings('ignore')

def stable_mape(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mask = y_true != 0
    if not np.any(mask):
        return 0.0
    return np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask]))

mape_scorer = make_scorer(stable_mape, greater_is_better=False)

def main():
    # 1. Cargar el dataset
    df_path = '../02_datos/03_Entrenamiento/04_train_tablon_transformado.pkl'
    df = pd.read_pickle(df_path)

    # Filtrar por granularidad semanal
    df_weekly = df[df['granularity_week'] == 1.0].copy()

    # Reconstruir la fecha para asegurar orden cronológico
    df_weekly['date'] = pd.to_datetime(df_weekly[['year', 'month', 'day']])
    df_weekly = df_weekly.sort_values('date').reset_index(drop=True)

    print(f"Dataset semanal filtrado y ordenado. Filas: {df_weekly.shape[0]}, Columnas: {df_weekly.shape[1]}")
    print(f"Rango de fechas: {df_weekly['date'].min()} a {df_weekly['date'].max()}")

    # 2. Definir variables y targets
    features = ['year', 'month', 'day', 'weekofyear']
    targets = ['m01ab', 'm01ae', 'n02ba', 'n02be', 'n05b', 'n05c', 'r03', 'r06']

    print("Features activas para el entrenamiento:", features)
    print("Targets a modelar:", targets)

    # 3. Configuración de Validación Cruzada Temporal
    tscv = TimeSeriesSplit(n_splits=5)
    print(f"Configuración de TimeSeriesSplit con {tscv.n_splits} splits.")

    # 4. Definición de Espacios de Hiperparámetros
    param_grids = {
        'LinearRegression': {},
        'RandomForestRegressor': {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 8, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        },
        'HistGradientBoostingRegressor': {
            'max_iter': [50, 100, 150],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 8, None],
            'min_samples_leaf': [5, 10, 20]
        },
        'XGBRegressor': {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.7, 0.8, 1.0],
            'colsample_bytree': [0.7, 0.8, 1.0]
        }
    }

    # 5. Función de búsqueda
    def run_model_search(target_name, X, y, tscv):
        results = []
        
        # 1. Linear Regression (Baseline)
        print(f"  Entrenando LinearRegression...")
        lr_mape_scores = []
        lr_rmse_scores = []
        lr_mae_scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            preds = model.predict(X_val)
            
            lr_mape_scores.append(stable_mape(y_val, preds))
            lr_rmse_scores.append(np.sqrt(mean_squared_error(y_val, preds)))
            lr_mae_scores.append(mean_absolute_error(y_val, preds))
            
        results.append({
            'algoritmo': 'LinearRegression',
            'parametros': {},
            'mape_mean': np.mean(lr_mape_scores),
            'mape_std': np.std(lr_mape_scores),
            'rmse_mean': np.mean(lr_rmse_scores),
            'mae_mean': np.mean(lr_mae_scores)
        })
        
        # Modelos para RandomizedSearch
        models_to_search = {
            'RandomForestRegressor': RandomForestRegressor(random_state=42),
            'HistGradientBoostingRegressor': HistGradientBoostingRegressor(random_state=42)
        }
        if XGB_AVAILABLE:
            models_to_search['XGBRegressor'] = XGBRegressor(random_state=42)
        
        for model_name, base_model in models_to_search.items():
            print(f"  Entrenando {model_name}...")
            grid = param_grids[model_name]
            
            search = RandomizedSearchCV(
                estimator=base_model,
                param_distributions=grid,
                n_iter=15,
                scoring=mape_scorer,
                cv=tscv,
                random_state=42,
                n_jobs=-1
            )
            
            search.fit(X, y)
            
            best_idx = search.best_index_
            best_mape = -search.best_score_
            mape_std = search.cv_results_['std_test_score'][best_idx]
            best_params = search.best_params_
            
            # Evaluar RMSE y MAE para los mejores hiperparámetros
            best_model = base_model.set_params(**best_params)
            rmse_scores = []
            mae_scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                best_model.fit(X_train, y_train)
                preds = best_model.predict(X_val)
                rmse_scores.append(np.sqrt(mean_squared_error(y_val, preds)))
                mae_scores.append(mean_absolute_error(y_val, preds))
                
            results.append({
                'algoritmo': model_name,
                'parametros': best_params,
                'mape_mean': best_mape,
                'mape_std': mape_std,
                'rmse_mean': np.mean(rmse_scores),
                'mae_mean': np.mean(mae_scores)
            })
            
        return results

    # 6. Ejecución del experimento con características dinámicas por target (lags + rolling)
    all_results = {}
    best_models_config = {}

    for target in targets:
        print(f"\n--- EJECUTANDO MODELADO PARA EL TARGET: {target} ---")
        
        # Construir características para este target (calendario + lags + rolling)
        features_target = ['year', 'month', 'day', 'weekofyear', f'{target}_lag_1', f'{target}_lag_2', f'{target}_roll_mean_4']
        X_target = df_weekly[features_target]
        y_target = df_weekly[target]
        
        # Eliminar las filas donde los retardos/medias móviles contengan NaNs (primeras semanas de la serie)
        non_nan_mask = X_target.notna().all(axis=1)
        X_target = X_target[non_nan_mask].reset_index(drop=True)
        y_target = y_target[non_nan_mask].reset_index(drop=True)
        
        target_results = run_model_search(target, X_target, y_target, tscv)
        all_results[target] = target_results
        
        # Convertir a DataFrame y ordenar
        df_res = pd.DataFrame(target_results)
        df_res = df_res.sort_values('mape_mean').reset_index(drop=True)
        
        print(f"\nRanking de modelos para {target}:")
        print(df_res[['algoritmo', 'mape_mean', 'mape_std', 'rmse_mean', 'mae_mean']])
        
        # Seleccionar el ganador
        ganador = df_res.iloc[0]
        best_models_config[target] = {
            'algoritmo': ganador['algoritmo'],
            'parametros': ganador['parametros'],
            'metricas_cv': {
                'mape_mean': float(ganador['mape_mean']),
                'mape_std': float(ganador['mape_std']),
                'rmse_mean': float(ganador['rmse_mean']),
                'mae_mean': float(ganador['mae_mean'])
            }
        }
        print(f"🏆 Ganador para {target}: {ganador['algoritmo']} (MAPE: {ganador['mape_mean']:.4f})")

    # 7. Interpretabilidad
    from sklearn.inspection import permutation_importance
    interpretabilidad = {}

    for target in targets:
        print(f"\n--- ANALIZANDO IMPORTANCIA DE VARIABLES PARA: {target} ---")
        config = best_models_config[target]
        algoritmo = config['algoritmo']
        params = config['parametros']
        
        # Instanciar el modelo
        if algoritmo == 'LinearRegression':
            model = LinearRegression(**params)
        elif algoritmo == 'RandomForestRegressor':
            model = RandomForestRegressor(random_state=42, **params)
        elif algoritmo == 'HistGradientBoostingRegressor':
            model = HistGradientBoostingRegressor(random_state=42, **params)
        elif algoritmo == 'XGBRegressor':
            if XGB_AVAILABLE:
                model = XGBRegressor(random_state=42, **params)
            else:
                print(f"XGBRegressor selected but not available. Skipping permutation importance.")
                continue
            
        # Reconstruir X_target e y_target del target actual
        features_target = ['year', 'month', 'day', 'weekofyear', f'{target}_lag_1', f'{target}_lag_2', f'{target}_roll_mean_4']
        X_target = df_weekly[features_target]
        y_target = df_weekly[target]
        
        non_nan_mask = X_target.notna().all(axis=1)
        X_target = X_target[non_nan_mask].reset_index(drop=True)
        y_target = y_target[non_nan_mask].reset_index(drop=True)
        
        # Entrenar en la última partición para calcular permutation importance
        train_idx, val_idx = list(tscv.split(X_target))[-1]
        model.fit(X_target.iloc[train_idx], y_target.iloc[train_idx])
        
        # Calcular Permutation Importance
        perm_imp = permutation_importance(
            model, X_target.iloc[val_idx], y_target.iloc[val_idx], 
            scoring=mape_scorer, 
            n_repeats=10, random_state=42
        )
        
        # Guardar importancias ordenadas
        importancias_mean = perm_imp.importances_mean
        importancias_dict = {feat: float(imp) for feat, imp in zip(features_target, importancias_mean)}
        importancias_dict = dict(sorted(importancias_dict.items(), key=lambda item: item[1], reverse=True))
        
        print(f"Permutation Importance (orden descendente):")
        for feat, imp in importancias_dict.items():
            print(f"  {feat}: {imp:.6f}")
            
        interpretabilidad[target] = importancias_dict

    # 8. Guardar resultados
    out_dir = '../06_resultados/Modelizacion'
    os.makedirs(out_dir, exist_ok=True)

    config_final = {
        'tipo_proyecto': 'forecasting_ML_semanal_con_lags',
        'dataset_entrenamiento': df_path,
        'granularidad': 'semanal',
        'targets': targets,
        'features_por_target': {t: ['year', 'month', 'day', 'weekofyear', f'{t}_lag_1', f'{t}_lag_2', f'{t}_roll_mean_4'] for t in targets},
        'mejor_configuracion_por_target': best_models_config,
        'interpretabilidad_permutation_importance': interpretabilidad
    }

    json_out_path = os.path.join(out_dir, 'config_mejor_modelo.json')
    with open(json_out_path, 'w', encoding='utf-8') as f:
        json.dump(config_final, f, indent=4, ensure_ascii=False)
        
    print(f"Configuración del mejor modelo guardada en: {json_out_path}")

    # Guardar el ranking
    rows = []
    for target, results in all_results.items():
        for res in results:
            rows.append({
                'target': target,
                'algoritmo': res['algoritmo'],
                'parametros': str(res['parametros']),
                'mape_mean': res['mape_mean'],
                'mape_std': res['mape_std'],
                'rmse_mean': res['rmse_mean'],
                'mae_mean': res['mae_mean']
            })

    df_ranking = pd.DataFrame(rows)
    csv_out_path = os.path.join(out_dir, 'ranking_modelos.csv')
    df_ranking.to_csv(csv_out_path, index=False, encoding='utf-8')
    print(f"Ranking completo de modelos guardado en: {csv_out_path}")

if __name__ == '__main__':
    main()
