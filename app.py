import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# CONFIG DE PÁGINA
# ==============================
st.set_page_config(page_title="Dashboard de Embalajes", layout="wide")

# ==============================
# CARGA DE DATOS
# ==============================
try:
    df = pd.read_excel("tabla_embalajes.xlsx")
except FileNotFoundError:
    st.error("❌ No se encontró 'tabla_embalajes.xlsx'. Colócalo junto a app.py.")
    st.stop()

# Normaliza nombres de columnas
df.columns = df.columns.str.strip().str.upper()

# Columnas mínimas necesarias
minimas = ["IMAGEN", "TIPO DE CARGA"]
faltan = [c for c in minimas if c not in df.columns]
if faltan:
    st.error(f"❌ Faltan columnas requeridas: {', '.join(faltan)}")
    st.stop()

# Ruta base de imágenes
SUBCARPETA = ""  
BASE_RAW = "https://raw.githubusercontent.com/mmejiamorales810-a11y/embalajes-dashboard/main/Imagenes-tuberia-o-tek/"
base_url = BASE_RAW + SUBCARPETA
df["IMAGEN_URL"] = base_url + df["IMAGEN"].astype(str)

# Cast numéricos seguros
def to_num(col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

for col in ["NUMERO DE TUBOS X PAQUETE", "VELOCIDAD DE PRODUCCION EN METROS HORA", 
            "DN", "MTS", "CLAVOS", "CANTIDAD MADEROS", "CANTIDAD SEPARADORES", 
            "CANTIDAD TABLONES", "CANTIDAD CUÑAS", "ALTO", "ANCHO",
            "COSTO TOTAL DE EMBALAJE  (NACIONAL)", "COSTO TOTAL DE EMBALAJE(EXPORTACION)"]:
    to_num(col)

# ==============================
# FILTROS (SIDEBAR)
# ==============================
st.sidebar.header("Filtros")

# --- Tipo de Carga ---
tipos_disp = sorted(df["TIPO DE CARGA"].dropna().unique().tolist())
tipos_disp_all = ["Seleccionar todos"] + tipos_disp
f_tipo = st.sidebar.multiselect("Tipo de Carga", tipos_disp_all, default=["Seleccionar todos"])
if "Seleccionar todos" in f_tipo:
    f_tipo = tipos_disp  # Selecciona todos si se elige la opción especial

# --- DN ---
dns_disp = sorted(df["DN"].dropna().unique().tolist()) if "DN" in df.columns else []
if dns_disp:
    dns_disp_all = ["Seleccionar todos"] + list(map(str, dns_disp))
    f_dn = st.sidebar.multiselect("DN", dns_disp_all, default=["Seleccionar todos"])
    if "Seleccionar todos" in f_dn:
        f_dn = dns_disp
    else:
        f_dn = [int(x) for x in f_dn]
else:
    f_dn = []

# --- Construcción del filtro ---
mask = df["TIPO DE CARGA"].isin(f_tipo)
if f_dn:
    mask &= df["DN"].isin(f_dn)

df_f = df[mask].copy()

# ==============================
# MÉTRICAS
# ==============================
st.title("📦 Dashboard de Embalajes")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Registros filtrados", len(df_f))
with col2:
    st.metric("Tipos de carga (filtro)", df_f["TIPO DE CARGA"].nunique())
prom_vel = "-"
if "VELOCIDAD DE PRODUCCION EN METROS HORA" in df_f.columns and not df_f["VELOCIDAD DE PRODUCCION EN METROS HORA"].dropna().empty:
    prom_vel = round(df_f["VELOCIDAD DE PRODUCCION EN METROS HORA"].mean(), 2)
with col3:
    st.metric("Velocidad prod. promedio", prom_vel)

# ==============================
# GRÁFICOS
# ==============================
st.subheader("📈 Visualizaciones")

if not df_f.empty and "COSTO TOTAL DE EMBALAJE  (NACIONAL)" in df_f.columns and "COSTO TOTAL DE EMBALAJE(EXPORTACION)" in df_f.columns:
    aux_costos = df_f.groupby("TIPO DE CARGA", as_index=False)[
        ["COSTO TOTAL DE EMBALAJE  (NACIONAL)", "COSTO TOTAL DE EMBALAJE(EXPORTACION)"]
    ].sum()

    aux_melt = aux_costos.melt(
        id_vars="TIPO DE CARGA", 
        value_vars=["COSTO TOTAL DE EMBALAJE  (NACIONAL)", "COSTO TOTAL DE EMBALAJE(EXPORTACION)"],
        var_name="Tipo de Costo", 
        value_name="Valor"
    )

    fig_costos = px.bar(
        aux_melt, 
        x="TIPO DE CARGA", 
        y="Valor", 
        color="Tipo de Costo", 
        barmode="group", 
        title="Costo total de embalaje (Nacional vs Exportación)",
        text="Valor"
    )
    fig_costos.update_traces(
        texttemplate='$%{text:,.0f}', 
        textposition='inside'
    )
    fig_costos.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

    st.plotly_chart(fig_costos, use_container_width=True)
else:
    st.info("No hay datos de costos para mostrar.")

# ==============================
# TARJETAS DE CANTIDADES
# ==============================
st.subheader("🪵 Cantidades Totales (según filtro)")

if not df_f.empty:
    total_maderos = int(df_f["CANTIDAD MADEROS"].sum()) if "CANTIDAD MADEROS" in df_f.columns else 0
    total_tablones = int(df_f["CANTIDAD TABLONES"].sum()) if "CANTIDAD TABLONES" in df_f.columns else 0
    total_separadores = int(df_f["CANTIDAD SEPARADORES"].sum()) if "CANTIDAD SEPARADORES" in df_f.columns else 0
    total_cunas = int(df_f["CANTIDAD CUÑAS"].sum()) if "CANTIDAD CUÑAS" in df_f.columns else 0
    total_clavos = int(df_f["CLAVOS"].sum()) if "CLAVOS" in df_f.columns else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Maderos", f"{total_maderos:,}")
    c2.metric("Tablones", f"{total_tablones:,}")
    c3.metric("Separadores", f"{total_separadores:,}")
    c4.metric("Cuñas", f"{total_cunas:,}")
    c5.metric("Clavos", f"{total_clavos:,}")
else:
    st.info("No hay datos para mostrar métricas de cantidades.")

# ==============================
# TARJETAS DETALLADAS POR EMBALAJE
# ==============================
st.subheader("🖼️ Embalajes filtrados")

if df_f.empty:
    st.warning("No hay registros para mostrar.")
else:
    cols = st.columns(3)
    for i, (_, row) in enumerate(df_f.iterrows()):
        with cols[i % 3]:
            st.image(row["IMAGEN_URL"], 
                     caption=f"{row['TIPO DE CARGA']} · DN {row['DN'] if 'DN' in row else ''}", 
                     use_container_width=True)

            st.markdown("### 📋 Detalles del Embalaje")

            if pd.notna(row.get("NUMERO DE TUBOS X PAQUETE", None)):
                st.markdown(f"**Tubos por paquete:** {int(row['NUMERO DE TUBOS X PAQUETE']):,}")

            if pd.notna(row.get("CLAVOS", None)):
                st.markdown(f"**Clavos:** {int(row['CLAVOS']):,}")

            if pd.notna(row.get("CANTIDAD MADEROS", None)):
                st.markdown(f"**Maderos:** {int(row['CANTIDAD MADEROS']):,}")

            if pd.notna(row.get("CANTIDAD TABLONES", None)):
                st.markdown(f"**Tablones:** {int(row['CANTIDAD TABLONES']):,}")

            if pd.notna(row.get("CANTIDAD SEPARADORES", None)):
                st.markdown(f"**Separadores:** {int(row['CANTIDAD SEPARADORES']):,}")

            if pd.notna(row.get("CANTIDAD CUÑAS", None)):
                st.markdown(f"**Cuñas:** {int(row['CANTIDAD CUÑAS']):,}")

            if pd.notna(row.get("ALTO", None)):
                st.markdown(f"**Alto:** {row['ALTO']}")

            if pd.notna(row.get("ANCHO", None)):
                st.markdown(f"**Ancho:** {row['ANCHO']}")

            if pd.notna(row.get("VELOCIDAD DE PRODUCCION EN METROS HORA", None)):
                st.markdown(f"**Velocidad prod.:** {row['VELOCIDAD DE PRODUCCION EN METROS HORA']:,} m/h")

            if pd.notna(row.get("OBSERVACIONES", None)):
                st.markdown(f"**Obs.:** {str(row['OBSERVACIONES'])}")
