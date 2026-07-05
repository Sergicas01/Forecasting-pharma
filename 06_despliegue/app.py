import re
import pickle
import unicodedata
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Pharma Sales Forecast",
    layout="wide",
    page_icon="💊",
    initial_sidebar_state="expanded"
)

# Estilos CSS premium para UI moderna
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1d3557;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #495057;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #028090;
    }
</style>
""", unsafe_allow_html=True)

# Rutas del proyecto
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
    with open(ARTEFACTO_PATH, "rb") as f:
        return pickle.load(f)

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

# Iniciar aplicación
st.markdown("<div class='main-title'>💊 Pharma Sales Forecast — Decision Support</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Sistema predictivo e inteligente de soporte de decisiones para compras y stock de seguridad</div>", unsafe_allow_html=True)

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
    st.sidebar.header("🎯 Parámetros de Simulación")
    
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
        "Semanas históricas a mostrar en gráfico",
        min_value=10,
        max_value=100,
        value=52,
        step=10
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Stock de Seguridad:** Ajuste sugerido para amortiguar fluctuaciones imprevistas de demanda.")

    # 1. Row de KPIs para la categoría seleccionada
    st.subheader(f"Métricas y Pronóstico: {DESCRIPTIONS[selected_target]}")
    
    pred_val = next_predictions[selected_target]
    rec_order = pred_val * (1 + safety_stock / 100)
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Modelo Seleccionado</div>
            <div class="metric-value" style="font-size: 1.2rem; margin-top:0.4rem;">{WINNERS[selected_target]}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Error del Modelo (MAPE)</div>
            <div class="metric-value">{MAPES[selected_target]}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Predicción (Próx. Semana)</div>
            <div class="metric-value">{pred_val:.1f} cajas</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card" style="border-color: #028090; background-color: #f0fdfa;">
            <div class="metric-title" style="color: #028090;">Pedido Sugerido</div>
            <div class="metric-value" style="color: #028090;">{rec_order:.1f} cajas</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Gráfico interactivo (Últimas N semanas + predicción)
    st.subheader("📈 Tendencia de Ventas y Pronóstico Futuro")
    
    # Recortar datos históricos
    df_plot = df_data[['date', selected_target]].tail(view_weeks).copy()
    df_plot['Tipo'] = 'Histórico Real'
    
    # Agregar fila de predicción
    df_pred_row = pd.DataFrame({
        'date': [next_date],
        selected_target: [pred_val],
        'Tipo': ['Pronóstico Modelo']
    })
    
    # Concatenar para graficar continuo
    # Para que se conecte la línea, duplicamos la última fila histórica como pronóstico
    df_conn_row = pd.DataFrame({
        'date': [df_plot.iloc[-1]['date']],
        selected_target: [df_plot.iloc[-1][selected_target]],
        'Tipo': ['Pronóstico Modelo']
    })
    
    df_combined = pd.concat([df_plot, df_conn_row, df_pred_row]).reset_index(drop=True)
    df_combined['Ventas (Unidades)'] = df_combined[selected_target]
    
    # Graficar con altair integrado en streamlit
    import altair as alt
    
    chart = alt.Chart(df_combined).mark_line(point=True).encode(
        x=alt.X('date:T', title='Fecha'),
        y=alt.Y('Ventas (Unidades):Q', title='Ventas (Cajas)'),
        color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Histórico Real', 'Pronóstico Modelo'], range=['#028090', '#fca311'])),
        tooltip=['date:T', 'Ventas (Unidades):Q', 'Tipo:N']
    ).properties(
        width=1000,
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

    # 3. Planificador Global Logístico de Compras
    st.markdown("---")
    st.subheader("📋 Planificador Global de Compras Semanales (Todos los Targets)")
    
    summary_data = []
    for t in TARGETS:
        p_val = next_predictions[t]
        s_order = p_val * (1 + safety_stock / 100)
        summary_data.append({
            "Código ATC": t,
            "Descripción": DESCRIPTIONS[t].split(" (")[0],
            "Algoritmo": WINNERS[t].split(" ")[0],
            "Error (MAPE)": MAPES[t],
            "Predicción Base": f"{p_val:.1f} cajas",
            f"Pedido Recomendado (+{safety_stock}%)": f"{s_order:.1f} cajas"
        })
        
    df_summary = pd.DataFrame(summary_data)
    st.table(df_summary)

    # Descarga
    csv = df_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Plan de Pedidos en CSV",
        data=csv,
        file_name=f"plan_compras_semana_{next_date.strftime('%Y_%W')}.csv",
        mime="text/csv"
    )
