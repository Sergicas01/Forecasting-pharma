import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # 1. Cargar el csv de ranking
    csv_path = '../06_resultados/Modelizacion/ranking_modelos.csv'
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} no existe.")
        return

    df = pd.read_csv(csv_path)

    # 2. Configurar el estilo premium
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
        'figure.facecolor': '#ffffff',
        'axes.facecolor': '#f8f9fa',
        'axes.edgecolor': '#cccccc',
        'axes.grid': True,
        'grid.color': '#e9ecef',
        'text.color': '#212529',
        'axes.labelcolor': '#212529',
        'xtick.color': '#495057',
        'ytick.color': '#495057',
    })

    # 3. Crear figura
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)

    # Filtrar o limitar los valores extremos de LinearRegression para no distorsionar la escala
    # (Por ejemplo, recortamos el MAPE máximo a 1.0 para visualización de detalle)
    df_plot = df.copy()
    df_plot['mape_percentage'] = df_plot['mape_mean'] * 100
    df_plot.loc[df_plot['mape_percentage'] > 100, 'mape_percentage'] = 100

    # Paleta de colores elegante y moderna
    # Teal/Cyan para HistGradientBoosting, Slate/Purple para RandomForest, Light Coral/Grey para Linear Regression
    colors = {
        'HistGradientBoostingRegressor': '#00a896',
        'RandomForestRegressor': '#028090',
        'XGBRegressor': '#fca311',
        'LinearRegression': '#f07167'
    }

    # Graficar usando seaborn barplot
    sns.barplot(
        data=df_plot,
        x='target',
        y='mape_percentage',
        hue='algoritmo',
        palette=colors,
        ax=ax,
        edgecolor='black',
        linewidth=0.5,
        alpha=0.9
    )

    # Ajustes de diseño y etiquetas
    ax.set_title('Comparación de Rendimiento de Modelos (Validación Cruzada Temporal)', fontsize=16, fontweight='bold', pad=20, color='#1d3557')
    ax.set_xlabel('Categorías de Fármaco (Targets)', fontsize=12, fontweight='semibold', labelpad=12)
    ax.set_ylabel('MAPE Promedio (%)', fontsize=12, fontweight='semibold', labelpad=12)
    
    # Formatear el eje Y con '%'
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0f}%'.format(y)))
    ax.set_ylim(0, 100) # Clippeado a 100% para ver diferencias finas de los modelos buenos

    # Leyenda estilizada
    ax.legend(title='Algoritmos', title_fontsize='11', fontsize='10', loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#e9ecef')

    # Añadir los valores de porcentaje encima de las barras para los dos mejores modelos
    for p in ax.patches:
        height = p.get_height()
        # Si la barra no tiene altura o representa a la Regresión Lineal muy alta, no ponemos texto para no ensuciar
        if height > 0 and height < 99:
            ax.annotate(
                f'{height:.1f}%',
                (p.get_x() + p.get_width() / 2., height),
                ha='center', va='center',
                xytext=(0, 7),
                textcoords='offset points',
                fontsize=8,
                fontweight='bold',
                color='#495057'
            )

    plt.tight_layout()

    # Guardar imagen en alta resolución
    out_dir = '../06_resultados/Modelizacion'
    os.makedirs(out_dir, exist_ok=True)
    img_path = os.path.join(out_dir, 'comparativa_modelos.png')
    plt.savefig(img_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Gráfico de comparación generado exitosamente en: {img_path}")

if __name__ == '__main__':
    main()
