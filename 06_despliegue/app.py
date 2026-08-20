import re
import math
import pickle
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Optimización de la Gestión de Inventario",
    layout="wide",
    page_icon="💊",
    initial_sidebar_state="expanded"
)

# Estilos CSS premium para UI moderna y corporativa (no genérica)
st.markdown("""
<style>
    /* Importación de tipografías premium */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Aplicar tipografía a toda la app */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }
    
    /* Ocultar marca de Streamlit para acabado profesional */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero Banner Premium (Efecto Gradiente Azul Profundo - Esquinas Rectas y Borde Uniforme) */
    .hero-banner {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        color: #ffffff;
        padding: 3rem 2.5rem;
        border-radius: 0px !important;
        margin-bottom: 2.5rem;
        border: 2px solid #1e3a8a;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.75px;
        margin-bottom: 0.5rem;
        color: #f8fafc;
    }
    
    .hero-desc {
        font-size: 1.15rem;
        font-weight: 400;
        color: #cbd5e1;
        max-width: 800px;
    }
    
    /* Tarjetas de Métricas - Diseño Clean Blue con Esquinas Rectas y Borde Uniforme */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 0px !important;
        padding: 1.5rem 1.3rem;
        text-align: left;
        box-shadow: none;
        transition: border-color 0.2s, background-color 0.2s;
    }
    
    .metric-card:hover {
        border-color: #1e3a8a;
        background-color: #f8fafc;
    }
    
    .metric-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    
    .metric-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    
    /* Tarjeta de ROI Premium (Elegante, Esquinas Rectas y Borde Uniforme) */
    .roi-card {
        background: #0f172a;
        color: #ffffff;
        border-radius: 0px !important;
        padding: 1.75rem;
        border: 2px solid #1e3a8a;
        margin-bottom: 1.5rem;
    }
    
    .roi-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #60a5fa; /* Light Electric Blue */
        text-transform: uppercase;
        letter-spacing: 0.75px;
        margin-bottom: 0.5rem;
    }
    
    .roi-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1.1;
    }
    
    .roi-sub {
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Banner de Presupuesto Corporativo (Esquinas Rectas y Borde Uniforme) */
    .budget-banner {
        background: #1c2541;
        color: #f8fafc;
        border-radius: 0px !important;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 2px solid #1e3a8a;
    }
    
    /* Caja de Fórmulas Matemáticas (Esquinas Rectas y Borde Uniforme) */
    .formula-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 0px !important;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }
    
    .formula-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    /* Personalización Premium del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0b132b !important;
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1 !important;
    }
    /* Estilos robustos para cabeceras de expansores en el Sidebar (evita fondos blancos en cualquier estado) */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] details summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderHeader,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:focus,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:active,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:hover,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:focus,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:active {
        background-color: #1c2541 !important;
        color: #cbd5e1 !important;
        border: 1px solid #1e3a8a !important;
        border-radius: 0px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] summary *,
    [data-testid="stSidebar"] [data-testid="stExpander"] details summary *,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary *,
    [data-testid="stSidebar"] [data-testid="stExpander"] .streamlit-expanderHeader *,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover *,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:focus *,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:active *,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:hover *,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:focus *,
    [data-testid="stSidebar"] [data-testid="stExpander"] details[open] summary:active * {
        background-color: transparent !important;
        color: #cbd5e1 !important;
    }
    
    /* Prevenir fondos blancos en inputs al hacer click/foco */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] div[data-baseweb="select"],
    [data-testid="stSidebar"] div[data-baseweb="input"] {
        background-color: #1c2541 !important;
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] input:focus,
    [data-testid="stSidebar"] div[data-baseweb="select"]:focus-within,
    [data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
        background-color: #1c2541 !important;
        color: #ffffff !important;
        border-color: #1e3a8a !important;
    }
    
    /* Prevenir colisiones en dropdowns (desplegables) de selectbox */
    div[role="listbox"] {
        background-color: #1c2541 !important;
        color: #cbd5e1 !important;
    }
    div[role="option"] {
        color: #cbd5e1 !important;
    }
    div[role="option"]:hover, div[role="option"][aria-selected="true"] {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
    }
    
    /* Estilos para pestañas de Streamlit */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #cbd5e1;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 600;
        font-size: 1rem;
        padding: 0 8px;
        transition: color 0.2s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #1e3a8a;
    }
    
    .stTabs [aria-selected="true"] {
        color: #1e3a8a !important;
        border-bottom: 3px solid #1e3a8a !important;
    }
    
    /* Botones de Streamlit - Esquinas Rectas y Borde */
    .stDownloadButton>button {
        border-radius: 0px !important;
        border: 2px solid #1e3a8a !important;
        background-color: transparent !important;
        color: #1e3a8a !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: background-color 0.2s, color 0.2s !important;
    }
    .stDownloadButton>button:hover {
        background-color: #1e3a8a !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "02_datos" / "01_Originales" / "salesweekly.csv"
ARTEFACTO_PATH = PROJECT_ROOT / "06_despliegue" / "artefacto_pipeline.pkl"
TARGETS = ['m01ab', 'm01ae', 'n02ba', 'n02be', 'n05b', 'n05c', 'r03', 'r06']

MAPES = {
    'm01ab': '19.37%',
    'm01ae': '19.94%',
    'n02ba': '24.76%',
    'n02be': '15.43%',
    'n05b': '31.21%',
    'n05c': '72.88%',
    'r03': '46.08%',
    'r06': '28.52%'
}

WINNERS = {
    'm01ab': 'XGBRegressor',
    'm01ae': 'XGBRegressor',
    'n02ba': 'RandomForestRegressor',
    'n02be': 'RandomForestRegressor',
    'n05b': 'RandomForestRegressor',
    'n05c': 'HistGradientBoostingRegressor',
    'r03': 'XGBRegressor',
    'r06': 'RandomForestRegressor'
}

DESCRIPTIONS = {
    'm01ab': 'Antiinflamatorios no esteroideos (m01ab)',
    'm01ae': 'Antiinflamatorios no esteroideos (m01ae)',
    'n02ba': 'Otros analgésicos y antipiréticos (n02ba)',
    'n02be': 'Analgésicos (Anilidas - Paracetamol) (n02be)',
    'n05b': 'Ansiolíticos (n05b)',
    'n05c': 'Hipnóticos y sedantes (n05c)',
    'r03': 'Anti-asmáticos / Vías respiratorias (r03)',
    'r06': 'Antihistamínicos de uso sistémico (r06)'
}

UNIT_COSTS = {
    'm01ab': 4.50,
    'm01ae': 3.80,
    'n02ba': 2.90,
    'n02be': 3.20,
    'n05b': 5.10,
    'n05c': 6.50,
    'r03': 14.20,
    'r06': 4.80
}

# Funciones de procesamiento de datos
def normalize_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = unicodedata.normalize("NFKD", col)
    col = "".join(ch for ch in col if not unicodedata.combining(ch))
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col

@st.cache_data
def load_data():
    df_raw = pd.read_csv(CSV_PATH)
    df_clean = df_raw.copy()
    df_clean.columns = [normalize_column_name(c) for c in df_clean.columns]
    df_clean['date'] = pd.to_datetime(df_clean['datum'], errors='coerce')
    df_clean = df_clean.sort_values('date').reset_index(drop=True)
    return df_clean

@st.cache_resource
def load_pipelines():
    try:
        with open(ARTEFACTO_PATH, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print("⚠️ Discrepancia de versión del modelo detectada. Ajustando y reentrenando pipelines localmente...")
        
        # Importación dinámica para evitar lentitud si no es necesario
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
            
        def stable_mape(y_true, y_pred):
            y_true = np.array(y_true)
            y_pred = np.array(y_pred)
            mask = y_true != 0
            if not np.any(mask):
                return 0.0
            return np.mean(np.abs(y_true[mask] - y_pred[mask]) / np.abs(y_true[mask]))

        mape_scorer = make_scorer(stable_mape, greater_is_better=False)
        
        # Obtener datos procesados
        df_clean = load_data()
        
        # Ingeniería de características para entrenamiento (lags, rollings y calendario)
        date_series = pd.to_datetime(df_clean['date'])
        df_clean['year'] = date_series.dt.year
        df_clean['month'] = date_series.dt.month
        df_clean['day'] = date_series.dt.day
        df_clean['weekofyear'] = date_series.dt.isocalendar().week.astype(int)
        
        for t in TARGETS:
            if t in df_clean.columns:
                lag_1 = df_clean[t].shift(1)
                lag_2 = df_clean[t].shift(2)
                roll_4 = lag_1.rolling(window=4, min_periods=1).mean()
                
                df_clean[f'{t}_lag_1'] = lag_1
                df_clean[f'{t}_lag_2'] = lag_2
                df_clean[f'{t}_roll_mean_4'] = roll_4
                
        df_clean = df_clean.dropna(subset=[f'{t}_roll_mean_4' for t in TARGETS if t in df_clean.columns]).reset_index(drop=True)
        
        max_date = df_clean['date'].max()
        cutoff_date = max_date - pd.DateOffset(months=3)
        df_train = df_clean[df_clean['date'] < cutoff_date].copy()
        
        tscv = TimeSeriesSplit(n_splits=3)
        trained_pipelines = {}
        
        for target in TARGETS:
            features_target = ['year', 'month', 'day', 'weekofyear', f'{target}_lag_1', f'{target}_lag_2', f'{target}_roll_mean_4']
            
            preprocesador = make_column_transformer(
                ("passthrough", features_target),
                remainder="drop"
            )
            
            pipe = Pipeline([
                ('preprocessor', preprocesador),
                ('regressor', RandomForestRegressor(random_state=42))
            ])
            
            param_distributions = [
                {
                    'regressor': [RandomForestRegressor(random_state=42)],
                    'regressor__n_estimators': [50, 100],
                    'regressor__max_depth': [3, 5, None],
                    'regressor__min_samples_split': [2, 5],
                    'regressor__min_samples_leaf': [1, 2]
                },
                {
                    'regressor': [HistGradientBoostingRegressor(random_state=42)],
                    'regressor__max_iter': [50, 100],
                    'regressor__learning_rate': [0.01, 0.1],
                    'regressor__max_depth': [3, 5, None]
                }
            ]
            
            if XGB_AVAILABLE:
                param_distributions.append({
                    'regressor': [XGBRegressor(random_state=42)],
                    'regressor__n_estimators': [50, 100],
                    'regressor__max_depth': [3, 5],
                    'regressor__learning_rate': [0.01, 0.1]
                })
                
            search = RandomizedSearchCV(
                estimator=pipe,
                param_distributions=param_distributions,
                n_iter=5,  # Pocas iteraciones para entrenar súper rápido
                cv=tscv,
                scoring=mape_scorer,
                random_state=42,
                n_jobs=-1,
                refit=True
            )
            
            y_train = df_train[target]
            search.fit(df_train, y_train)
            trained_pipelines[target] = search.best_estimator_
            
        # Guardar el nuevo pkl compatible para acelerar los siguientes arranques
        try:
            with open(ARTEFACTO_PATH, "wb") as f:
                pickle.dump(trained_pipelines, f)
        except Exception:
            pass  # Si el entorno en la nube es de solo lectura, continuamos en memoria
            
        return trained_pipelines

# Generación del dataframe del futuro (Next Week)
def predict_next_week(df_processed, pipelines):
    last_row = df_processed.iloc[-1]
    last_date = last_row['date']
    next_date = last_date + pd.Timedelta(days=7)
    
    # Construir fila para el modelo
    next_row_dict = {
        'datum': [next_date.strftime('%Y-%m-%d')],
        'date': [next_date],
        'year': [next_date.year],
        'month': [next_date.month],
        'day': [next_date.day],
        'weekofyear': [int(next_date.isocalendar().week)]
    }
    
    # Calcular lags y rollings para la nueva fila
    for target in TARGETS:
        next_row_dict[f'{target}_lag_1'] = [df_processed.iloc[-1][target]]
        next_row_dict[f'{target}_lag_2'] = [df_processed.iloc[-2][target]]
        next_row_dict[f'{target}_roll_mean_4'] = [df_processed.iloc[-4:][target].mean()]
        
    df_next = pd.DataFrame(next_row_dict)
    
    # Predecir
    predictions = {}
    for target in TARGETS:
        if target in pipelines:
            pipe = pipelines[target]
            pred = pipe.predict(df_next)[0]
            predictions[target] = float(np.clip(pred, 0, None))
    return next_date, predictions


# Calcular desviaciones estándar de residuos e históricas para cada target (capturando estacionalidad)
@st.cache_data
def calculate_catalog_uncertainty(_pipelines, df_processed):
    uncertainty_data = {}
    for target in TARGETS:
        df_feat = df_processed.copy()
        date_series = pd.to_datetime(df_feat['date'])
        df_feat['year'] = date_series.dt.year
        df_feat['month'] = date_series.dt.month
        df_feat['day'] = date_series.dt.day
        df_feat['weekofyear'] = date_series.dt.isocalendar().week.astype(int)
        
        df_feat[f'{target}_lag_1'] = df_feat[target].shift(1)
        df_feat[f'{target}_lag_2'] = df_feat[target].shift(2)
        df_feat[f'{target}_roll_mean_4'] = df_feat[f'{target}_lag_1'].rolling(window=4, min_periods=1).mean()
        
        df_feat = df_feat.dropna(subset=[f'{target}_roll_mean_4']).reset_index(drop=True)
        
        if target in _pipelines:
            pipe = _pipelines[target]
            preds = pipe.predict(df_feat)
            residuals = df_feat[target] - preds
            
            std_actual_w = df_feat[target].std()
            std_ia_w = residuals.std()
            
            std_actual_d = std_actual_w / np.sqrt(7.0)
            std_ia_d = std_ia_w / np.sqrt(7.0)
            
            mean_w = df_feat[target].mean()
            d_anual = mean_w * 52.18
            
            uncertainty_data[target] = {
                'std_actual_d': float(std_actual_d),
                'std_ia_d': float(std_ia_d),
                'd_anual': float(d_anual),
                'mean_w': float(mean_w)
            }
    return uncertainty_data

# Renderizar Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">Optimización de la Gestión del Inventario</div>
    <div class="hero-desc">Sistema de Soporte de Decisiones (DSS) para la planificación y compra inteligente de suministros farmacéuticos.</div>
</div>
""", unsafe_allow_html=True)

# Cargar recursos
try:
    df_data = load_data()
    pipelines = load_pipelines()
    next_date, next_predictions = predict_next_week(df_data, pipelines)
    catalog_uncertainty = calculate_catalog_uncertainty(pipelines, df_data)
    data_loaded = True
except Exception as e:
    st.error(f"Error al cargar los datos o modelos: {e}")
    st.info("Asegúrate de haber ejecutado el reentrenamiento (`python3 06_despliegue/01_reentrenamiento.py`) para generar el artefacto.")
    data_loaded = False

if data_loaded:
    # Sidebar de Control
    st.sidebar.header("Configuración Suministro")
    
    # Menú de selección de Fármaco
    selected_target = st.sidebar.selectbox(
        "Categoría Terapéutica (ATC)",
        options=TARGETS,
        format_func=lambda x: DESCRIPTIONS[x]
    )
    
    # Histórico a mostrar
    view_weeks = st.sidebar.slider(
        "Historial visible (Semanas)",
        min_value=10,
        max_value=100,
        value=52,
        step=10
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("Parámetros Logísticos")
    
    # 1. Nivel de Servicio
    with st.sidebar.expander("🎯 Garantía de Suministro (Nivel Servicio)", expanded=True):
        st.caption("Porcentaje de la demanda que deseamos cubrir garantizadamente sin quedarnos sin stock.")
        servicio_opciones = {
            "90% (Z = 1.28)": 1.282,
            "95% (Z = 1.645)": 1.645,
            "98% (Z = 2.05)": 2.054,
            "99% (Z = 2.33)": 2.326,
            "99.9% (Z = 3.09)": 3.090
        }
        opt_z_label = st.selectbox(
            "Nivel de Servicio Deseado",
            options=list(servicio_opciones.keys()),
            index=1, # 95% por defecto
            help="Probabilidad deseada de no incurrir en roturas de stock."
        )
        opt_z = servicio_opciones[opt_z_label]
    
    # 2. Tiempos del Proveedor (Lead Time)
    with st.sidebar.expander("🚚 Tiempos del Proveedor (Lead Time)", expanded=True):
        st.caption("Tiempos de entrega y fiabilidad del proveedor logístico.")
        opt_l_dias = st.number_input(
            "Plazo de Entrega (L) [Días]",
            min_value=0.5,
            max_value=365.0,
            value=10.08,
            step=1.0,
            help="Tiempo promedio en días que transcurre desde que se pide hasta que se recibe."
        )
        opt_sigma_l = st.number_input(
            "Desviación Lead Time (σ_L) [Días]",
            min_value=0.0,
            max_value=30.0,
            value=2.00,
            step=0.5,
            help="Medida de la variabilidad o días máximos de retraso habituales del proveedor."
        )
    
    # 3. Costes Operativos
    with st.sidebar.expander("💶 Costes Operativos e Inventario", expanded=True):
        st.caption("Costes administrativos y de almacenamiento para evaluar optimizaciones.")
        opt_s_pedido = st.number_input(
            "Coste por Pedido (S) [€]",
            min_value=1.0,
            max_value=5000.0,
            value=50.0,
            step=5.0,
            help="Costo fijo administrativo y de transporte por emitir cada orden de compra."
        )
        opt_h_almacen = st.number_input(
            "Coste Almacén Anual/Ud (H) [€]",
            min_value=0.1,
            max_value=500.0,
            value=15.02,
            step=1.0,
            help="Coste anual de mantener una unidad o caja inmovilizada en almacén."
        )
    
    # Coste unitario configurable
    costs = {}
    with st.sidebar.expander("Configurar Costes Unitarios (€)"):
        for t in TARGETS:
            costs[t] = st.number_input(
                f"{t.upper()} Coste/Caja",
                min_value=0.10,
                max_value=150.0,
                value=UNIT_COSTS[t],
                step=0.50,
                format="%.2f"
            )
            
    st.sidebar.markdown("---")
    st.sidebar.header("Visualización Gráfica")
    dispersion_type = st.sidebar.selectbox(
        "Visualizar Dispersión en Gráfico",
        options=[
            "Ninguna",
            "Basada en MAPE (Error Histórico Medio)",
            "Basada en Confianza Estadística (σ Residuos)"
        ],
        index=2,
        help="Permite visualizar en el gráfico la dispersión del pronóstico en base al error o precisión del modelo."
    )

    st.sidebar.info("Inventario Inteligente: El Stock de Seguridad y Punto de Pedido se calculan dinámicamente usando fórmulas estadísticas basadas en la estacionalidad corregida por la IA.")

    # Definición de pestañas principales
    tab_plan, tab_scen, tab_roi = st.tabs([
        "Pronóstico y Plan de Compras", 
        "Simulador Logístico 'What-If'", 
        "Simulador ROI Negocio (IA vs Tradicional)"
    ])
    
    with tab_plan:
        pred_val = next_predictions[selected_target]
        unit_cost = costs[selected_target]
        
        # Calcular Stock de Seguridad Estadístico para el target seleccionado usando su error residual de IA y estacionalidad
        t_info = catalog_uncertainty[selected_target]
        t_std_ia_d = t_info['std_ia_d']
        t_d_diaria = pred_val / 7.0  # estacional para la semana que viene
        
        var_base = (t_d_diaria ** 2) * (opt_sigma_l ** 2)
        ss_val = opt_z * math.sqrt(opt_l_dias * (t_std_ia_d ** 2) + var_base)
        
        # Pedido recomendado con el Stock de Seguridad óptimo
        rec_order = pred_val + ss_val
        total_cost = rec_order * unit_cost
        
        recent_mean = df_data[selected_target].tail(4).mean()
        percentage_above = ((pred_val - recent_mean) / recent_mean) * 100
        
        st.subheader(f"Análisis Operativo: {DESCRIPTIONS[selected_target]}")
        
        if percentage_above > 30:
            st.warning(f"**RIESGO DE ROTURA (ALTO)**: La predicción ({pred_val:.0f} cajas) excede la media reciente de 4 semanas ({recent_mean:.0f} cajas) en un **{percentage_above:.1f}%**. Incremento estacional detectado.")
        else:
            st.info(f"**Estado de Stock (Estable)**: Demanda estable ({percentage_above:+.1f}% respecto a la media reciente de {recent_mean:.0f} cajas).")
            
        # Tarjetas de KPI (Bordes rectos uniformes)
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        with kpi_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Modelo Predictivo</div>
                <div class="metric-value" style="font-size: 1.25rem; color: #1e3a8a; font-weight: 700;">{WINNERS[selected_target]}</div>
                <div class="metric-sub">MAPE Validación: {MAPES[selected_target]}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Pronóstico de Demanda</div>
                <div class="metric-value">{pred_val:.0f} <span style="font-size: 1rem; color: #64748b; font-weight: normal;">cajas</span></div>
                <div class="metric-sub">Semana: {next_date.strftime('%d/%m/%Y')}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title" style="color: #1e3a8a;">Pedido Sugerido</div>
                <div class="metric-value">{rec_order:.0f} <span style="font-size: 1rem; color: #64748b; font-weight: normal;">cajas</span></div>
                <div class="metric-sub">Incluye SS óptimo: +{ss_val:.0f} cajas</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title" style="color: #0f172a;">Inversión Estimada</div>
                <div class="metric-value">{total_cost:,.2f} €</div>
                <div class="metric-sub">Costo unitario: {unit_cost:.2f} €</div>
            </div>
            """, unsafe_allow_html=True)
     
        st.markdown("<br>", unsafe_allow_html=True)
    
        # 2. Gráfico interactivo (Últimas N semanas + predicción)
        st.subheader("Proyección Histórica y Pronóstico Futuro")
        
        # Recortar datos históricos
        df_plot = df_data[['date', selected_target]].tail(view_weeks).copy()
        df_plot['Tipo'] = 'Venta Histórica'
        
        # Agregar fila de predicción (una sola semana)
        df_pred_row = pd.DataFrame({
            'date': [next_date],
            selected_target: [pred_val],
            'Tipo': 'Pronóstico Futuro'
        })
        
        # Concatenar para continuidad visual
        df_conn_row = pd.DataFrame({
            'date': [df_plot.iloc[-1]['date']],
            selected_target: [df_plot.iloc[-1][selected_target]],
            'Tipo': 'Pronóstico Futuro'
        })
        
        df_combined = pd.concat([df_plot, df_conn_row, df_pred_row]).reset_index(drop=True)
        df_combined['Cajas Vendidas'] = df_combined[selected_target]
        
        # Calcular la dispersión según el tipo seleccionado
        dispersion_val_outer = 0.0
        dispersion_val_inner = 0.0
        dispersion_label_outer = ""
        dispersion_label_inner = ""
        
        if dispersion_type == "Basada en MAPE (Error Histórico Medio)":
            mape_pct = float(MAPES[selected_target].replace('%', '')) / 100.0
            dispersion_val_outer = pred_val * mape_pct
            dispersion_val_inner = pred_val * (mape_pct * 0.5)
            dispersion_label_outer = f"MAPE ({MAPES[selected_target]})"
            dispersion_label_inner = f"50% MAPE (±{mape_pct * 50:.2f}%)"
        elif dispersion_type == "Basada en Confianza Estadística (σ Residuos)":
            t_std_ia_w = t_std_ia_d * math.sqrt(7.0)
            dispersion_val_outer = opt_z * t_std_ia_w
            dispersion_val_inner = 0.67449 * t_std_ia_w
            dispersion_label_outer = f"Confianza {opt_z_label.split(' ')[0]} (Z={opt_z:.2f}, ±{dispersion_val_outer:.0f} cajas)"
            dispersion_label_inner = f"Confianza Central 50% (Z=0.67, ±{dispersion_val_inner:.0f} cajas)"

        # Graficar con altair usando colores azulados corporativos
        import altair as alt
        
        # Gráfico de líneas (historial y pronóstico)
        line_chart = alt.Chart(df_combined).mark_line(point=True).encode(
            x=alt.X('date:T', title='Eje Temporal (Semanas)'),
            y=alt.Y('Cajas Vendidas:Q', title='Cantidad (Cajas)'),
            color=alt.Color('Tipo:N', scale=alt.Scale(
                domain=['Venta Histórica', 'Pronóstico Futuro', 'Intervalo Central (50%)', 'Intervalo Externo'], 
                range=['#475569', '#1e3a8a', '#60a5fa', '#93c5fd']
            ), title="Leyenda"),
            tooltip=['date:T', 'Cajas Vendidas:Q', 'Tipo:N']
        )
        
        if dispersion_type != "Ninguna" and dispersion_val_outer > 0:
            # Banda de dispersión externa (ligera)
            df_band_outer = pd.DataFrame({
                'date': [df_plot.iloc[-1]['date'], next_date],
                'lower': [df_plot.iloc[-1][selected_target], max(0.0, pred_val - dispersion_val_outer)],
                'upper': [df_plot.iloc[-1][selected_target], pred_val + dispersion_val_outer],
                'Tipo': ['Intervalo Externo', 'Intervalo Externo']
            })
            
            band_outer_chart = alt.Chart(df_band_outer).mark_area(
                opacity=0.15,
                color='#1e3a8a'
            ).encode(
                x='date:T',
                y=alt.Y('lower:Q'),
                y2='upper:Q',
                tooltip=[
                    alt.Tooltip('date:T', title='Fecha'),
                    alt.Tooltip('lower:Q', title='Límite Inferior Externo (Cajas)', format='.1f'),
                    alt.Tooltip('upper:Q', title='Límite Superior Externo (Cajas)', format='.1f')
                ]
            )
            
            # Banda de dispersión interna (más oscura)
            df_band_inner = pd.DataFrame({
                'date': [df_plot.iloc[-1]['date'], next_date],
                'lower': [df_plot.iloc[-1][selected_target], max(0.0, pred_val - dispersion_val_inner)],
                'upper': [df_plot.iloc[-1][selected_target], pred_val + dispersion_val_inner],
                'Tipo': ['Intervalo Central (50%)', 'Intervalo Central (50%)']
            })
            
            band_inner_chart = alt.Chart(df_band_inner).mark_area(
                opacity=0.35,
                color='#1e3a8a'
            ).encode(
                x='date:T',
                y=alt.Y('lower:Q'),
                y2='upper:Q',
                tooltip=[
                    alt.Tooltip('date:T', title='Fecha'),
                    alt.Tooltip('lower:Q', title='Límite Inferior Central (Cajas)', format='.1f'),
                    alt.Tooltip('upper:Q', title='Límite Superior Central (Cajas)', format='.1f')
                ]
            )
            
            # Combinar gráficos
            chart = alt.layer(band_outer_chart, band_inner_chart, line_chart)
        else:
            chart = line_chart
            
        chart = chart.properties(
            width=1000,
            height=380
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            gridColor='#f1f5f9',
            labelColor='#64748b',
            titleColor='#475569'
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        if dispersion_type != "Ninguna" and dispersion_val_outer > 0:
            st.markdown(f"""
            <div style="background-color: #f8fafc; border-left: 4px solid #1e3a8a; padding: 0.85rem 1.25rem; margin-top: -0.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; color: #334155;">
                <div style="font-weight: 700; margin-bottom: 0.25rem; color: #1e3a8a;">Abanico de Dispersión Estimado ({dispersion_type.split(" ")[2]}):</div>
                <ul style="margin: 0; padding-left: 1.2rem; line-height: 1.45;">
                    <li><strong>Intervalo Central (50% Probabilidad):</strong> Entre <strong>{max(0.0, pred_val - dispersion_val_inner):.0f}</strong> y <strong>{pred_val + dispersion_val_inner:.0f}</strong> cajas ({dispersion_label_inner}).</li>
                    <li><strong>Intervalo Externo ({opt_z_label.split(" ")[0]}):</strong> Entre <strong>{max(0.0, pred_val - dispersion_val_outer):.0f}</strong> y <strong>{pred_val + dispersion_val_outer:.0f}</strong> cajas ({dispersion_label_outer}).</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
        # 3. Planificador Global Logístico de Compras
        st.markdown("---")
        st.subheader("Plan de Adquisición de Suministros (Consolidado Semanal)")
        
        summary_data = []
        total_budget = 0.0
        
        for t in TARGETS:
            p_val = next_predictions[t]
            u_cost = costs[t]
            
            # Calcular Stock de Seguridad óptimo estadístico para cada producto
            t_info = catalog_uncertainty[t]
            t_std_ia_d = t_info['std_ia_d']
            t_d_diaria = p_val / 7.0
            
            t_var_base = (t_d_diaria ** 2) * (opt_sigma_l ** 2)
            t_ss_val = opt_z * math.sqrt(opt_l_dias * (t_std_ia_d ** 2) + t_var_base)
            
            s_order = p_val + t_ss_val
            t_cost = s_order * u_cost
            total_budget += t_cost
            
            rec_mean_t = df_data[t].tail(4).mean()
            risk_status = "Alto" if (p_val - rec_mean_t) / rec_mean_t > 0.30 else "Bajo"
            
            summary_data.append({
                "Código ATC": t.upper(),
                "Descripción": DESCRIPTIONS[t].split(" (")[0],
                "Riesgo Rotura": risk_status,
                "Pronóstico (Cajas)": f"{p_val:.0f}",
                "Stock Seguridad (Cajas)": f"{t_ss_val:.0f}",
                "Pedido Sugerido (Cajas)": f"{s_order:.0f}",
                "Coste/Caja": f"{u_cost:.2f} €",
                "Coste Total": f"{t_cost:,.2f} €"
            })
            
        df_summary = pd.DataFrame(summary_data)
        
        # Formatear tabla limpia y profesional en streamlit
        st.dataframe(
            df_summary,
            column_config={
                "Código ATC": st.column_config.TextColumn("Código ATC", width="small"),
                "Descripción": st.column_config.TextColumn("Fármaco", width="medium"),
                "Riesgo Rotura": st.column_config.TextColumn("Riesgo Rotura", width="small"),
                "Pronóstico (Cajas)": st.column_config.TextColumn("Pronóstico", width="small"),
                "Stock Seguridad (Cajas)": st.column_config.TextColumn("Stock Seguridad", width="small"),
                "Pedido Sugerido (Cajas)": st.column_config.TextColumn("Pedido Sugerido", width="small"),
                "Coste/Caja": st.column_config.TextColumn("Coste/Caja", width="small"),
                "Coste Total": st.column_config.TextColumn("Coste Total", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    
        # Mostrar la tarjeta de presupuesto total consolidado
        st.markdown(f"""
        <div class="budget-banner">
            PRESUPUESTO CONSOLIDADO DE COMPRA SEMANAL SUGERIDO: {total_budget:,.2f} €
        </div>
        """, unsafe_allow_html=True)
    
        # Descarga
        csv = df_summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Exportar Plan de Compras a CSV (Formato Logístico)",
            data=csv,
            file_name=f"plan_compras_semana_{next_date.strftime('%Y_%W')}.csv",
            mime="text/csv"
        )
    with tab_scen:
        st.subheader("Simulador Logístico 'What-If': Resiliencia de la Cadena de Suministro")
        st.markdown("""
        Evalúa el impacto de disrupciones en la cadena de suministro (retrasos de proveedores, cambios de plazos) 
        sobre el **Stock de Seguridad**, los **pedidos sugeridos** y los **costes financieros asociados**.
        """)
        
        st.markdown("---")
        
        # Crear dos columnas principales para configurar y comparar
        col_scen_in, col_scen_res = st.columns([4, 6])
        
        with col_scen_in:
            st.markdown("### 🛠️ Configurar Escenario Alternativo")
            st.markdown("Ajusta los parámetros para simular disrupciones (ej. retrasos del proveedor).")
            
            scen_l_dias = st.slider(
                "Simular Nuevo Plazo de Entrega (Lead Time) [Días]",
                min_value=0.5,
                max_value=90.0,
                value=float(opt_l_dias),
                step=1.0,
                key="scen_l_dias",
                help="Tiempo total estimado que tardará el envío en llegar a tu almacén (mínimo 0.5 días, máximo 90 días)."
            )
            st.caption("⏱️ **Lead Time:** Días transcurridos desde que haces el pedido hasta que se recibe físicamente.")
            
            scen_sigma_l = st.slider(
                "Simular Variabilidad / Retraso del Proveedor [Días]",
                min_value=0.0,
                max_value=30.0,
                value=float(opt_sigma_l),
                step=0.5,
                key="scen_sigma_l",
                help="Margen de retraso o días habituales de variación que experimenta el transporte."
            )
            st.caption("⚠️ **Retrasos:** Días de desviación habitual que el transportista puede sufrir.")
            
            scen_servicio_opciones = {
                "90% (Z = 1.28)": 1.282,
                "95% (Z = 1.645)": 1.645,
                "98% (Z = 2.05)": 2.054,
                "99% (Z = 2.33)": 2.326,
                "99.9% (Z = 3.09)": 3.090
            }
            # Buscar el index por defecto que coincide con opt_z_label
            default_idx = list(scen_servicio_opciones.keys()).index(opt_z_label) if opt_z_label in scen_servicio_opciones else 1
            
            scen_z_label = st.selectbox(
                "Nivel de Servicio Alternativo",
                options=list(scen_servicio_opciones.keys()),
                index=default_idx,
                key="scen_z_label"
            )
            scen_z = scen_servicio_opciones[scen_z_label]
            
            scen_h_almacen = st.number_input(
                "Coste Almacén Anual/Ud Alternativo (H) [€]",
                min_value=0.1,
                max_value=500.0,
                value=float(opt_h_almacen),
                step=1.0,
                key="scen_h_almacen"
            )
            
        # Cálculos de comparación
        t_info = catalog_uncertainty[selected_target]
        t_std_ia_d = t_info['std_ia_d']
        t_d_diaria = pred_val / 7.0
        unit_cost = costs[selected_target]
        
        # Base
        ss_base = ss_val
        order_base = rec_order
        cost_base = order_base * unit_cost
        holding_base = ss_base * opt_h_almacen
        
        # Alternativo
        var_base_alt = (t_d_diaria ** 2) * (scen_sigma_l ** 2)
        ss_alt = scen_z * math.sqrt(scen_l_dias * (t_std_ia_d ** 2) + var_base_alt)
        order_alt = pred_val + ss_alt
        cost_alt = order_alt * unit_cost
        holding_alt = ss_alt * scen_h_almacen
        
        # Diferencias
        diff_ss = ss_alt - ss_base
        diff_ss_pct = (diff_ss / ss_base) * 100 if ss_base > 0 else 0.0
        diff_holding = holding_alt - holding_base
        
        with col_scen_res:
            st.markdown("### 📊 Comparador de Impacto Logístico")
            
            # Tarjetas de comparación lado a lado
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Stock de Seguridad</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{ss_base:.0f} ➔ {ss_alt:.0f} <span style="font-size: 0.9rem; font-weight: normal; color: #64748b;">cajas</span></div>
                    <div class="metric-sub" style="color: {'#ef4444' if diff_ss > 0 else '#10b981'}; font-weight: 600;">
                        Diferencia: {diff_ss:+.0f} cajas ({diff_ss_pct:+.1f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Coste Almacenamiento Anual (SS)</div>
                    <div class="metric-value" style="font-size: 1.4rem;">{holding_base:,.2f} € ➔ {holding_alt:,.2f} €</div>
                    <div class="metric-sub" style="color: {'#ef4444' if diff_holding > 0 else '#10b981'}; font-weight: 600;">
                        Diferencia: {diff_holding:+,.2f} €
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mostrar gráfico comparativo de barras
            import altair as alt
            df_compare = pd.DataFrame({
                'Escenario': ['Base', 'Alternativo', 'Base', 'Alternativo'],
                'Métrica': ['Stock de Seguridad', 'Stock de Seguridad', 'Pedido Sugerido', 'Pedido Sugerido'],
                'Cajas': [ss_base, ss_alt, order_base, order_alt]
            })
            
            compare_chart = alt.Chart(df_compare).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X('Escenario:N', title=None),
                y=alt.Y('Cajas:Q', title='Cantidad (Cajas)'),
                color=alt.Color('Escenario:N', scale=alt.Scale(domain=['Base', 'Alternativo'], range=['#64748b', '#1e3a8a']), legend=None),
                column=alt.Column('Métrica:N', title=None)
            ).properties(
                width=180,
                height=220
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(compare_chart, use_container_width=True)
            
            # Alertas comerciales
            if diff_ss > 0:
                st.warning(f"""
                ⚠️ **Alerta de Cadena de Suministro:** La disrupción simulada incrementa la necesidad de Stock de Seguridad en un **{diff_ss_pct:.1f}%**. 
                Esto inmovilizará **{diff_holding:,.2f} €** adicionales al año en almacenamiento para mantener el nivel de servicio deseado.
                """)
            elif diff_ss < 0:
                st.success(f"""
                ✅ **Oportunidad de Optimización:** La mejora simulada reduce el Stock de Seguridad en un **{abs(diff_ss_pct):.1f}%**, 
                liberando **{abs(diff_holding):,.2f} €** al año en costes de almacenamiento.
                """)
            else:
                st.info("ℹ️ Ambos escenarios son idénticos. Modifica los parámetros de la izquierda para ver el impacto.")



    with tab_roi:
        st.markdown("### Simulador ROI de Negocio: Forecast vs Tradicional")
        st.markdown("""
        Este simulador evalúa el impacto financiero completo en la cuenta de resultados logística de una farmacéutica. 
        Compara un modelo de previsión tradicional frente a un modelo de Inteligencia Artificial en base a ineficiencias de inventario, WACC y el lote económico de pedido (EOQ).
        """)
        
        st.markdown("---")
        
        col_roi_in, col_roi_res = st.columns([4, 6])
        
        with col_roi_in:
            st.subheader("Parámetros Base")
            
            roi_demanda = st.number_input(
                "Demanda Anual Total",
                min_value=1000,
                max_value=100000000,
                value=5000000,
                step=100000,
                key="roi_demanda",
                help="Demanda anual estimada en unidades."
            )
            
            roi_coste_u = st.number_input(
                "Coste de Producción Unitario",
                min_value=0.01,
                max_value=1000.0,
                value=0.35,
                step=0.01,
                format="%.2f",
                key="roi_coste_u",
                help="Coste unitario de adquisición o producción."
            )
            
            roi_margen_u = st.number_input(
                "Margen de Beneficio Unitario",
                min_value=0.01,
                max_value=1000.0,
                value=0.25,
                step=0.01,
                format="%.2f",
                key="roi_margen_u",
                help="Margen de beneficio comercial por unidad vendida."
            )
            
            roi_coste_pedido = st.number_input(
                "Coste por Emisión de Pedido (S)",
                min_value=1.0,
                max_value=10000.0,
                value=200.0,
                step=10.0,
                format="%.2f",
                key="roi_coste_pedido",
                help="Coste administrativo y logístico por emitir una orden."
            )
            
            st.subheader("Financiero y Precisión")
            
            roi_espacio = st.number_input(
                "Coste Espacio Físico / Seguros (%)",
                min_value=0.0,
                max_value=100.0,
                value=7.0,
                step=0.5,
                key="roi_espacio",
                help="Porcentaje sobre el coste unitario del stock por almacenamiento y seguro anual."
            )
            
            roi_wacc = st.number_input(
                "Tipos de Interés (WACC) (%)",
                min_value=0.0,
                max_value=100.0,
                value=8.0,
                step=0.5,
                key="roi_wacc",
                help="Coste promedio ponderado del capital. Un valor más alto penaliza más el inventario inmovilizado."
            )
            
            roi_acc_trad = st.slider(
                "Precisión Modelo Tradicional (%)",
                min_value=50,
                max_value=100,
                value=70,
                step=1,
                key="roi_acc_trad",
                help="Precisión o exactitud de los métodos de previsión tradicionales basados en medias móviles."
            )
            
            roi_acc_ia = st.slider(
                "Precisión Modelo IA (%)",
                min_value=50,
                max_value=100,
                value=85,
                step=1,
                key="roi_acc_ia",
                help="Precisión estimada utilizando el modelo predictivo de Inteligencia Artificial."
            )
            
        with col_roi_res:
            st.subheader("Resultados de la Cuenta de Resultados Logística")
            
            # Cálculos Logísticos
            roi_H_pct = (roi_espacio + roi_wacc) / 100.0
            roi_H_val = roi_coste_u * roi_H_pct
            
            roi_EOQ = 0.0
            if roi_H_val > 0:
                roi_EOQ = math.sqrt((2 * roi_demanda * roi_coste_pedido) / roi_H_val)
                
            roi_num_pedidos = roi_demanda / roi_EOQ if roi_EOQ > 0 else 0.0
            roi_coste_pedidos = roi_num_pedidos * roi_coste_pedido
            
            # Ineficiencias basadas en la precisión (No lineales)
            def calc_roi_stats(accuracy):
                error = 1.0 - (accuracy / 100.0)
                ratio_error = error / 0.30 # Normalizado contra el 70% tradicional
                
                # Stock de Seguridad (Exponencial 1.5)
                ss = (roi_demanda / 12.0) * 1.5 * math.pow(ratio_error, 1.5)
                # Roturas (Exponencial 2.5)
                roturas = roi_demanda * 0.03 * math.pow(ratio_error, 2.5)
                # Mermas/Caducidad (Exponencial 2.0)
                mermas = roi_demanda * 0.005 * math.pow(ratio_error, 2.0)
                
                return ss, roturas, mermas
                
            roi_ss_trad, roi_roturas_trad, roi_mermas_trad = calc_roi_stats(roi_acc_trad)
            roi_ss_ia, roi_roturas_ia, roi_mermas_ia = calc_roi_stats(roi_acc_ia)
            
            # Costes en Euros
            roi_costs_trad = {
                'pedidos': roi_coste_pedidos,
                'espacio': roi_ss_trad * roi_coste_u * (roi_espacio / 100.0),
                'capital': roi_ss_trad * roi_coste_u * (roi_wacc / 100.0),
                'caducidad': roi_mermas_trad * roi_coste_u,
                'lucro': roi_roturas_trad * roi_margen_u
            }
            
            roi_costs_ia = {
                'pedidos': roi_coste_pedidos,
                'espacio': roi_ss_ia * roi_coste_u * (roi_espacio / 100.0),
                'capital': roi_ss_ia * roi_coste_u * (roi_wacc / 100.0),
                'caducidad': roi_mermas_ia * roi_coste_u,
                'lucro': roi_roturas_ia * roi_margen_u
            }
            
            roi_total_trad = sum([roi_costs_trad[k] for k in ['espacio', 'capital', 'caducidad', 'lucro']])
            roi_total_ia = sum([roi_costs_ia[k] for k in ['espacio', 'capital', 'caducidad', 'lucro']])
            roi_total_ahorro = roi_total_trad - roi_total_ia
            
            roi_cap_liberado = (roi_ss_trad - roi_ss_ia) * roi_coste_u
            
            # KPIs (Bordes rectos)
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            with kpi_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Lote Óptimo (EOQ)</div>
                    <div class="metric-value" style="font-size: 1.55rem;">{roi_EOQ:,.0f}</div>
                    <div class="metric-sub">Unidades por pedido</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Capital Liberado</div>
                    <div class="metric-value" style="font-size: 1.55rem; color: #1e3a8a;">{roi_cap_liberado:,.2f} €</div>
                    <div class="metric-sub">Efectivo recuperado</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Ahorro EBITDA</div>
                    <div class="metric-value" style="font-size: 1.55rem; color: #10b981;">{roi_total_ahorro:,.2f} €</div>
                    <div class="metric-sub">Reducción de coste/año</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Fila de tabla de comparación
            roi_conceptos = [
                ("Coste Espacio Físico", roi_costs_trad['espacio'], roi_costs_ia['espacio']),
                ("Coste Capital Inmovilizado", roi_costs_trad['capital'], roi_costs_ia['capital']),
                ("Coste Caducidad / Mermas", roi_costs_trad['caducidad'], roi_costs_ia['caducidad']),
                ("Lucro Cesante (Roturas)", roi_costs_trad['lucro'], roi_costs_ia['lucro']),
            ]
            
            roi_table_rows = []
            for name, t_cost, i_cost in roi_conceptos:
                ahorro = t_cost - i_cost
                roi_table_rows.append({
                    "Concepto de Coste": name,
                    "Tradicional": f"{t_cost:,.2f} €",
                    "Modelo IA": f"{i_cost:,.2f} €",
                    "Ahorro IA": f"+{ahorro:,.2f} €" if ahorro > 10 else f"{ahorro:,.2f} €"
                })
                
            df_roi_table = pd.DataFrame(roi_table_rows)
            
            st.dataframe(
                df_roi_table,
                column_config={
                    "Concepto de Coste": st.column_config.TextColumn("Concepto de Coste", width="medium"),
                    "Tradicional": st.column_config.TextColumn("Tradicional", width="small"),
                    "Modelo IA": st.column_config.TextColumn("Modelo IA", width="small"),
                    "Ahorro IA": st.column_config.TextColumn("Ahorro IA", width="small"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Presupuesto total consolidado banner
            st.markdown(f"""
            <div class="budget-banner" style="background: linear-gradient(135deg, #1c2541 0%, #0b132b 100%); margin-top: 1.5rem; border: 1px solid #cbd5e1;">
                AHORRO ANUAL TOTAL DE GESTIÓN: {roi_total_ahorro:,.2f} €
            </div>
            """, unsafe_allow_html=True)
            
            # CSV de descarga
            csv_data = (
                "PARAMETROS DE ENTRADA\n"
                f"Demanda Anual;{roi_demanda}\n"
                f"Coste Unitario;{roi_coste_u}\n"
                f"Margen Unitario;{roi_margen_u}\n"
                f"Coste Pedido;{roi_coste_pedido}\n"
                f"Tasa Espacio (%);{roi_espacio}\n"
                f"WACC (%);{roi_wacc}\n"
                f"Precision Tradicional (%);{roi_acc_trad}\n"
                f"Precision IA (%);{roi_acc_ia}\n\n"
                "Concepto;Tradicional (EUR);Modelo IA (EUR);Ahorro (EUR)\n"
            )
            for name, t_cost, i_cost in roi_conceptos:
                ahorro = t_cost - i_cost
                csv_data += f"{name};{t_cost:.2f};{i_cost:.2f};{ahorro:.2f}\n"
            csv_data += f"COSTE TOTAL GESTIÓN;{roi_total_trad:.2f};{roi_total_ia:.2f};{roi_total_ahorro:.2f}\n"
            
            st.download_button(
                label="Exportar a Excel (CSV)",
                data=csv_data.encode('utf-8'),
                file_name="business_case_farma_ia.csv",
                mime="text/csv",
                key="roi_export_btn"
            )
