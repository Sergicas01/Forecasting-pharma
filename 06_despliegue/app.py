import re
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
    /* Importación de tipografía corporativa */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Aplicar tipografía a toda la app */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Ocultar marca de Streamlit para acabado profesional */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero Banner Corporativo */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #3b82f6;
    }
    
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
        color: #f8fafc;
    }
    
    .hero-desc {
        font-size: 1.1rem;
        font-weight: 400;
        color: #94a3b8;
    }
    
    /* Tarjetas de métricas Glassmorphism / Clean */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #f1f5f9;
        border-radius: 12px;
        padding: 1.5rem 1.2rem;
        text-align: left;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.08);
    }
    
    .metric-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    
    .metric-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.4rem;
        font-weight: 400;
    }
    
    /* Banner de Presupuesto Corporativo */
    .budget-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-top: 1.5rem;
        margin-bottom: 2rem;
        border-left: 5px solid #028090;
    }
    
    /* Estilos de inputs de barra lateral */
    .css-1644de7 {
        background-color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# Rutas del proyecto y constantes
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
    'm01ab': 'XGBRegressor 🏆',
    'm01ae': 'XGBRegressor 🏆',
    'n02ba': 'RandomForestRegressor 🌲',
    'n02be': 'RandomForestRegressor 🌲',
    'n05b': 'RandomForestRegressor 🌲',
    'n05c': 'HistGradientBoostingRegressor ⚡',
    'r03': 'XGBRegressor 🏆',
    'r06': 'RandomForestRegressor 🌲'
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
    data_loaded = True
except Exception as e:
    st.error(f"Error al cargar los datos o modelos: {e}")
    st.info("Asegúrate de haber ejecutado el reentrenamiento (`python3 06_despliegue/01_reentrenamiento.py`) para generar el artefacto.")
    data_loaded = False

if data_loaded:
    # Sidebar de Control
    st.sidebar.header("🎯 Parámetros del Suministro")
    
    # Menú de selección de Fármaco
    selected_target = st.sidebar.selectbox(
        "Categoría Terapéutica (ATC)",
        options=TARGETS,
        format_func=lambda x: DESCRIPTIONS[x]
    )
    
    # Slider de Stock de Seguridad
    safety_stock = st.sidebar.slider(
        "Stock de Seguridad (%)",
        min_value=0,
        max_value=100,
        value=15,
        step=5
    )
    
    # Histórico a mostrar
    view_weeks = st.sidebar.slider(
        "Historial visible (Semanas)",
        min_value=10,
        max_value=100,
        value=52,
        step=10
    )
    
    # Coste unitario configurable
    costs = {}
    with st.sidebar.expander("💰 Configurar Costes Unitarios (€)"):
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
    st.sidebar.info("💡 **Stock de Seguridad:** Colchón de seguridad para mitigar roturas ante picos de demanda imprevistos.")

    # 1. Alerta de Riesgo de Rotura de Stock
    pred_val = next_predictions[selected_target]
    rec_order = pred_val * (1 + safety_stock / 100)
    unit_cost = costs[selected_target]
    total_cost = rec_order * unit_cost
    
    recent_mean = df_data[selected_target].tail(4).mean()
    percentage_above = ((pred_val - recent_mean) / recent_mean) * 100
    
    st.subheader(f"Análisis Operativo: {DESCRIPTIONS[selected_target]}")
    
    if percentage_above > 30:
        st.warning(f"⚠️ **RIESGO DE ROTURA (ALTO)**: La predicción ({pred_val:.1f} cajas) excede la media reciente de 4 semanas ({recent_mean:.1f} cajas) en un **{percentage_above:.1f}%**. Incremento estacional detectado.")
    else:
        st.info(f"ℹ️ **Estado de Stock (Estable)**: Demanda estable ({percentage_above:+.1f}% respecto a la media reciente de {recent_mean:.1f} cajas).")
        
    # Tarjetas de KPI
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Modelo Predictivo</div>
            <div class="metric-value" style="font-size: 1.25rem; color: #028090;">{WINNERS[selected_target]}</div>
            <div class="metric-sub">MAPE Validación: {MAPES[selected_target]}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Pronóstico de Demanda</div>
            <div class="metric-value">{pred_val:.1f} <span style="font-size: 1rem; color: #64748b; font-weight: normal;">cajas</span></div>
            <div class="metric-sub">Semana: {next_date.strftime('%d/%m/%Y')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #0ea5e9;">
            <div class="metric-title" style="color: #0ea5e9;">Pedido Recomendado</div>
            <div class="metric-value">{rec_order:.1f} <span style="font-size: 1rem; color: #64748b; font-weight: normal;">cajas</span></div>
            <div class="metric-sub">Buffer aplicado: +{safety_stock}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #10b981;">
            <div class="metric-title" style="color: #10b981;">Inversión Estimada</div>
            <div class="metric-value">{total_cost:,.2f} €</div>
            <div class="metric-sub">Costo unitario: {unit_cost:.2f} €</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Gráfico interactivo (Últimas N semanas + predicción)
    st.subheader("📈 Proyección Histórica y Pronóstico Futuro")
    
    # Recortar datos históricos
    df_plot = df_data[['date', selected_target]].tail(view_weeks).copy()
    df_plot['Tipo'] = 'Venta Histórica'
    
    # Agregar fila de predicción
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
    
    # Graficar con altair
    import altair as alt
    
    chart = alt.Chart(df_combined).mark_line(point=True).encode(
        x=alt.X('date:T', title='Eje Temporal (Semanas)'),
        y=alt.Y('Cajas Vendidas:Q', title='Cantidad (Cajas)'),
        color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Venta Histórica', 'Pronóstico Futuro'], range=['#1e293b', '#fca311']), title="Leyenda"),
        tooltip=['date:T', 'Cajas Vendidas:Q', 'Tipo:N']
    ).properties(
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

    # 3. Planificador Global Logístico de Compras
    st.markdown("---")
    st.subheader("📋 Plan de Adquisición de Suministros (Consolidado Semanal)")
    
    summary_data = []
    total_budget = 0.0
    
    for t in TARGETS:
        p_val = next_predictions[t]
        s_order = p_val * (1 + safety_stock / 100)
        u_cost = costs[t]
        t_cost = s_order * u_cost
        total_budget += t_cost
        
        # Calcular riesgo de rotura basado en la predicción semanal
        rec_mean_t = df_data[t].tail(4).mean()
        risk_status = "Alto ⚠️" if (p_val - rec_mean_t) / rec_mean_t > 0.30 else "Bajo ✅"
        
        summary_data.append({
            "Código ATC": t.upper(),
            "Descripción": DESCRIPTIONS[t].split(" (")[0],
            "Riesgo Rotura": risk_status,
            "Pronóstico (Cajas)": f"{p_val:.1f}",
            "Pedido Sugerido (Cajas)": f"{s_order:.1f}",
            "Coste/Caja": f"{u_cost:.2f} €",
            "Coste Total": f"{t_cost:,.2f} €"
        })
        
    df_summary = pd.DataFrame(summary_data)
    
    # Formatear tabla limpia y profesional en streamlit
    st.dataframe(
        df_summary,
        column_config={
            "Código ATC": st.column_config.TextColumn("Código ATC", width="medium"),
            "Descripción": st.column_config.TextColumn("Descripción del Fármaco", width="large"),
            "Riesgo Rotura": st.column_config.TextColumn("Riesgo Rotura", width="small"),
            "Pronóstico (Cajas)": st.column_config.TextColumn("Pronóstico", width="small"),
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
        💼 PRESUPUESTO CONSOLIDADO DE COMPRA SEMANAL SUGERIDO: {total_budget:,.2f} €
    </div>
    """, unsafe_allow_html=True)

    # Descarga
    csv = df_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Plan de Compras a CSV (Formato Logístico)",
        data=csv,
        file_name=f"plan_compras_semana_{next_date.strftime('%Y_%W')}.csv",
        mime="text/csv"
    )
