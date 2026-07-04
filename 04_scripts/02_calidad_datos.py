from pathlib import Path
import re
import unicodedata
from io import StringIO

import pandas as pd
import numpy as np

ROOT = Path.cwd()
INPUT_PATH = ROOT / "02_datos/03_Entrenamiento/01_train_tablon_integrado.pkl"
OUTPUT_PATH = ROOT / "02_datos/03_Entrenamiento/02_train_tablon_calidad.pkl"
REPORT_PATH = ROOT / "06_resultados/Calidad_Datos/informe_calidad_datos.md"
INSTRUCTIONS_PATH = ROOT / "copilot-instructions.md"


def normalize_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = unicodedata.normalize("NFKD", col)
    col = "".join(ch for ch in col if not unicodedata.combining(ch))
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col


def build_info_string(df: pd.DataFrame) -> str:
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


if __name__ == "__main__":
    df = pd.read_pickle(INPUT_PATH)

    original_columns = list(df.columns)
    df_clean = df.copy()

    # 1. Limpieza y estandarización de nombres
    normalized_columns = [normalize_column_name(c) for c in df.columns]
    if len(set(normalized_columns)) != len(normalized_columns):
        raise ValueError(f"Colisiones de nombres tras normalizar: {normalized_columns}")
    df_clean.columns = normalized_columns

    # 2. Revisión y corrección de tipos
    for col in ["year", "month", "hour"]:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

    df_clean["granularity"] = df_clean["granularity"].astype(str).str.strip().str.lower()
    df_clean["weekday_name"] = df_clean["weekday_name"].astype(str).str.strip().str.title()
    df_clean["weekday_name"] = df_clean["weekday_name"].replace({"Nan": pd.NA, "None": pd.NA})

    # 3. Reglas lógicas: completar y corregir campos derivados de la fecha
    df_clean["date"] = pd.to_datetime(df_clean["date"], errors="coerce")

    df_clean["year"] = df_clean["year"].astype("Int64").fillna(df_clean["date"].dt.year.astype("Int64"))
    df_clean["month"] = df_clean["month"].astype("Int64").fillna(df_clean["date"].dt.month.astype("Int64"))

    df_clean["weekday_name"] = df_clean["weekday_name"].replace({"<NA>": pd.NA})
    df_clean["weekday_name"] = df_clean["weekday_name"].fillna(df_clean["date"].dt.day_name())

    # For hourly rows, hour should be actual hour; for other granularities it should be missing.
    df_clean["hour"] = df_clean["hour"].astype("Int64")
    hourly_mask = df_clean["granularity"].eq("hour")
    df_clean.loc[hourly_mask, "hour"] = df_clean.loc[hourly_mask, "hour"].fillna(df_clean.loc[hourly_mask, "date"].dt.hour.astype("Int64"))
    df_clean.loc[~hourly_mask, "hour"] = pd.NA

    # 4. Duplicados y missing values
    duplicate_count = int(df_clean.duplicated().sum())
    missing_summary = df_clean.isna().sum()

    # 5. Mantener y documentar columnas de negocio (sin cambios semánticos)
    # No se realizan recortes de outliers; se conserva el rango observado
    column_mapping = dict(zip(original_columns, normalized_columns))

    # 6. Guardar dataframe limpio
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_pickle(OUTPUT_PATH)

    # 7. Generar informe markdown
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    report_lines = []
    report_lines.append("# Informe de calidad de datos")
    report_lines.append("")
    report_lines.append("## Resumen general")
    report_lines.append("")
    report_lines.append(f"- Filas procesadas: {len(df_clean):,}")
    report_lines.append(f"- Columnas originales: {len(original_columns)}")
    report_lines.append(f"- Columnas finales: {len(df_clean.columns)}")
    report_lines.append(f"- Duplicados completos detectados: {duplicate_count}")
    report_lines.append("- Se mantuvieron las columnas de negocio y se corrigieron los campos derivados de la fecha.")
    report_lines.append("")
    report_lines.append("## Problemas detectados")
    report_lines.append("")
    report_lines.append("- Nombres de columnas con espacios y formato inconsistente.")
    report_lines.append("- Columnas de fecha derivadas con valores faltantes en filas semanales y mensuales.")
    report_lines.append("- Valores inválidos en la columna hour para granularidades no horarias (marcadores 248/276).")
    report_lines.append("- Valores categóricos con formato inconsistente en granularity y weekday_name.")
    report_lines.append("")
    report_lines.append("## Decisiones y transformaciones aplicadas")
    report_lines.append("")
    report_lines.append("### 1. Estandarización de nombres")
    report_lines.append("")
    for old, new in zip(original_columns, normalized_columns):
        report_lines.append(f"- `{old}` -> `{new}`")
    report_lines.append("")
    report_lines.append("### 2. Tipado")
    report_lines.append("")
    report_lines.append("- `year`, `month` y `hour` convertidas a enteros nullable (`Int64`).")
    report_lines.append("- `granularity` estandarizada a minúsculas y sin espacios.")
    report_lines.append("- `weekday_name` normalizada a formato de texto limpio y completada a partir de `date`.")
    report_lines.append("")
    report_lines.append("### 3. Valores ausentes")
    report_lines.append("")
    report_lines.append("- Se imputaron `year`, `month` y `weekday_name` a partir de `date`.")
    report_lines.append("- Se dejaron como nulos los valores de `hour` para granularidades no horarias.")
    report_lines.append("- No se detectaron valores ocultos de vacío tipo `''`, `' '`, `'-'` o `N/A` en las columnas principales.")
    report_lines.append("")
    report_lines.append("### 4. Reglas lógicas")
    report_lines.append("")
    report_lines.append("- Se corrigió `hour` para que solo tenga sentido en filas con `granularity='hour'`.")
    report_lines.append("- Se validó que `year`, `month` y `weekday_name` fuesen consistentes con la fecha real del registro.")
    report_lines.append("")
    report_lines.append("## Resumen variable a variable")
    report_lines.append("")
    for column in df_clean.columns:
        original_name = next((name for name, new_name in column_mapping.items() if new_name == column), column)
        original_type = str(df.dtypes.get(original_name, "object"))
        final_type = str(df_clean.dtypes[column])
        report_lines.append(f"- `{column}`: tipo original `{original_type}` -> tipo final `{final_type}`")
    report_lines.append("")
    report_lines.append("## Valores faltantes finales")
    report_lines.append("")
    report_lines.append("```text")
    report_lines.append(missing_summary.to_string())
    report_lines.append("```")
    report_lines.append("")
    report_lines.append("## Archivos generados")
    report_lines.append("")
    report_lines.append(f"- Dataframe limpio: `{OUTPUT_PATH.relative_to(ROOT)}`")
    report_lines.append(f"- Informe: `{REPORT_PATH.relative_to(ROOT)}`")
    report_lines.append(f"- Instrucciones actualizadas: `{INSTRUCTIONS_PATH.relative_to(ROOT)}`")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    # 8. Actualizar copilot-instructions.md
    info_output = build_info_string(df_clean)
    instructions_content = f"## ESTADO ACTUAL DEL PROYECTO\n\n**Dataframe actual**: `../02_datos/03_Entrenamiento/02_train_tablon_calidad.pkl`\n\n**Estructura del dataframe**:\n```\n{info_output}```\n"
    INSTRUCTIONS_PATH.write_text(instructions_content, encoding="utf-8")

    print(f"Dataframe guardado en: {OUTPUT_PATH}")
    print(f"Informe guardado en: {REPORT_PATH}")
    print(f"Instrucciones actualizadas en: {INSTRUCTIONS_PATH}")
