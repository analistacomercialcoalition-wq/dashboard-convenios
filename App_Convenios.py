import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de página corporativa
st.set_page_config(
    page_title="Dashboard Gerencial & Modelo Predictivo | Coalition",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo para evitar recortes en métricas
st.markdown("""
    <style>
        [data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            white-space: nowrap !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Ejecutivo de Gestión Comercial & Convenios")
st.markdown("### **Coalition Group — Matriz de Colocaciones y Proyecciones Estacionales Perú**")
st.markdown("---")

# ==========================================
# 1. CARGA Y LIMPIEZA DE DATOS
# ==========================================
@st.cache_data(ttl=600)
def cargar_datos_corporativos():
    sheet_url = "https://docs.google.com/spreadsheets/d/1IBvyIN5H1jYrwEAOD9E5nTCpaBLqxD109HMKCW0Ezt8/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    
    df['NETO'] = pd.to_numeric(
        df['NETO'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace(' ', '').str.strip(), 
        errors='coerce'
    ).fillna(0)
    
    df['FECHA_DT'] = pd.to_datetime(df['FECHA DE DESEMBOLSO'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['FECHA_DT']).copy()
    
    df['AÑO'] = df['FECHA_DT'].dt.year.astype(int)
    df['MES_NUM'] = df['FECHA_DT'].dt.month.astype(int)
    df['AÑO_MES'] = df['FECHA_DT'].dt.to_period('M').astype(str)
    df['FECHA_CORTE'] = df['FECHA_DT'].dt.date
    
    return df

with st.spinner("Sincronizando base de datos corporativa..."):
    df_base = cargar_datos_corporativos()

# ==========================================
# 2. FILTROS EN BARRA LATERAL (JERARQUÍA)
# ==========================================
st.sidebar.header("🔍 Panel de Filtros y Control")
st.sidebar.subheader("🏢 Estructura Comercial")

zonas = ["TODAS"] + sorted(list(df_base['ZONA'].dropna().unique()))
sel_zona = st.sidebar.selectbox("Zona", zonas)

plazas = ["TODAS"] + sorted(list(df_base['PLAZA'].dropna().unique()))
sel_plaza = st.sidebar.selectbox("Plaza", plazas)

jefes = ["TODOS"] + sorted(list(df_base['JEFE ZONAL'].dropna().unique()))
sel_jefe = st.sidebar.selectbox("Jefe Zonal", jefes)

supervisores = ["TODOS"] + sorted(list(df_base['SUPERVISOR'].dropna().unique()))
sel_sup = st.sidebar.selectbox("Supervisor", supervisores)

asesores = ["TODOS"] + sorted(list(df_base['ASESOR CORRECTO'].dropna().unique()))
sel_asesor = st.sidebar.selectbox("Asesor", asesores)

df_flt = df_base.copy()
if sel_zona != "TODAS":
    df_flt = df_flt[df_flt['ZONA'] == sel_zona]
if sel_plaza != "TODAS":
    df_flt = df_flt[df_flt['PLAZA'] == sel_plaza]
if sel_jefe != "TODOS":
    df_flt = df_flt[df_flt['JEFE ZONAL'] == sel_jefe]
if sel_sup != "TODOS":
    df_flt = df_flt[df_flt['SUPERVISOR'] == sel_sup]
if sel_asesor != "TODOS":
    df_flt = df_flt[df_flt['ASESOR CORRECTO'] == sel_asesor]

# ==========================================
# 3. FILTROS EN ENCABEZADO SUPERIOR
# ==========================================
st.markdown("### 🎛️ Filtros de Control Temporal y Estado")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    min_f = df_flt['FECHA_CORTE'].min() if not df_flt.empty else datetime.today().date()
    max_f = df_flt['FECHA_CORTE'].max() if not df_flt.empty else datetime.today().date()
    
    rango_fechas = st.date_input(
        "📅 Rango Fecha de Desembolso",
        value=(min_f, max_f),
        min_value=min_f,
        max_value=max_f
    )

with f_col2:
    estados_disp = sorted(list(df_flt['ESTADO'].dropna().unique())) if not df_flt.empty else []
    sel_estados = st.multiselect(
        "📌 Estado de Operación", 
        options=estados_disp, 
        default=["DESEMBOLSADO"] if "DESEMBOLSADO" in estados_disp else estados_disp
    )

with f_col3:
    meses_disp = sorted(list(df_flt['AÑO_MES'].dropna().unique())) if not df_flt.empty else []
    sel_meses = st.multiselect(
        "🗓️ Meses Específicos (Año-Mes)", 
        options=meses_disp, 
        default=meses_disp
    )

if isinstance(rango_fechas, (list, tuple)) and len(rango_fechas) == 2:
    f_ini, f_fin = rango_fechas
    df_flt = df_flt[(df_flt['FECHA_CORTE'] >= f_ini) & (df_flt['FECHA_CORTE'] <= f_fin)]

if sel_estados:
    df_flt = df_flt[df_flt['ESTADO'].isin(sel_estados)]

if sel_meses:
    df_flt = df_flt[df_flt['AÑO_MES'].isin(sel_meses)]

st.markdown("---")

# ==========================================
# 4. TARJETAS KPI EN 4 COLUMNAS (COMPACTAS)
# ==========================================
total_neto = df_flt['NETO'].sum() if not df_flt.empty else 0
total_ops = len(df_flt)
dias_efectivos = df_flt['FECHA_CORTE'].nunique() if not df_flt.empty else 0
prom_diario = total_neto / dias_efectivos if dias_efectivos > 0 else 0
ticket_prom = total_neto / total_ops if total_ops > 0 else 0

def formato_compacto_limpio(val):
    if val >= 1e6:
        return f"S/ {val/1e6:,.2f}M"
    elif val >= 1e3:
        return f"S/ {val/1e3:,.1f}k"
    else:
        return f"S/ {val:,.2f}"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("💰 Neto Total Desembolsado", formato_compacto_limpio(total_neto))
kpi2.metric("📋 Total Operaciones", f"{total_ops:,}")
kpi3.metric("📅 Días Con Desembolso", f"{dias_efectivos:,}")
kpi4.metric("📈 Prom. Diario / Ticket", f"{formato_compacto_limpio(prom_diario)}")

st.markdown("---")

df_mensual = df_flt.groupby('AÑO_MES').agg(
    MONTO_TOTAL_NETO=('NETO', 'sum'),
    OPERACIONES=('NETO', 'count'),
    DIAS_TRABAJADOS=('FECHA_CORTE', 'nunique')
).reset_index() if not df_flt.empty else pd.DataFrame()

# ==========================================
# 5. VISUALIZACIÓN Y MONTE CARLO ESTACIONAL
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Producción Total por Mes", "🏆 Red Comercial & Ranking", "🎲 Monte Carlo (Estacionalidad Convenios Perú)"])

with tab1:
    st.subheader("💵 Monto Neto Total Desembolsado por Periodo")
    if not df_mensual.empty:
        fig_bar = px.bar(
            df_mensual, 
            x='AÑO_MES', 
            y='MONTO_TOTAL_NETO',
            text='MONTO_TOTAL_NETO',
            title="Evolución del Monto Neto Total Desembolsado (S/)",
            labels={'AÑO_MES': 'Periodo (Año-Mes)', 'MONTO_TOTAL_NETO': 'Monto Total Neto (S/)'},
            color_discrete_sequence=['#2563eb']
        )
        fig_bar.update_traces(texttemplate='S/ %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No se encontraron registros con los filtros seleccionados.")

with tab2:
    st.subheader("Evaluación de Desempeño por Plaza y Jefatura Zonal")
    col_a, col_b = st.columns(2)
    with col_a:
        if not df_flt.empty:
            df_plaza = df_flt.groupby('PLAZA')['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_plz = px.bar(df_plaza, x='NETO', y='PLAZA', orientation='h', title="Monto Neto por Plaza (S/)", text_auto=',.0f')
            st.plotly_chart(fig_plz, use_container_width=True)
    with col_b:
        if not df_flt.empty:
            df_jefe = df_flt.groupby('JEFE ZONAL')['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_jefe = px.bar(df_jefe, x='NETO', y='JEFE ZONAL', orientation='h', title="Monto Neto por Jefe Zonal (S/)", text_auto=',.0f')
            st.plotly_chart(fig_jefe, use_container_width=True)

with tab3:
    st.subheader("🎲 Motor Estocástico Monte Carlo (100,000 Escenarios - Convenios Perú)")
    st.markdown("Proyección basada en el **promedio mensual histórico real** de la matriz, calibrada con la sensibilidad de créditos por planilla (Picos en Noviembre, Diciembre y Julio).")

    # Controles opcionales para calibrar sensibilidad fina de fin de año
    with st.expander("⚙️ Calibración Avanzada de Factores Estacionales (Perú)"):
        f_jul = st.slider("Factor Julio (Gratificación Fiestas Patrias)", 1.0, 1.8, 1.25)
        f_nov = st.slider("Factor Noviembre (CTS y Pre-cierre)", 1.0, 1.8, 1.20)
        f_dic = st.slider("Factor Diciembre (Aguinaldo / Navidad)", 1.0, 2.0, 1.35)
        f_mar = st.slider("Factor Marzo (Campaña Escolar)", 0.8, 1.4, 1.10)

    if st.button("🚀 Ejecutar Simulación 100k Escenarios Estacionales"):
        # Base: Promedio mensual histórico real de la data filtrada
        base_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].mean() if not df_mensual.empty else 35000000
        std_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].std() if (not df_mensual.empty and len(df_mensual) > 1) else base_mensual_historica * 0.12

        # Factores estacionales refinados para el mercado peruano de convenios
        factores_peru = {
            'Enero': 0.85,
            'Febrero': 0.90,
            'Marzo': f_mar,
            'Abril': 1.00,
            'Mayo': 1.02,
            'Junio': 1.08,
            'Julio': f_jul,
            'Agosto': 0.95,
            'Setiembre': 1.00,
            'Octubre': 1.05,
            'Noviembre': f_nov,
            'Diciembre': f_dic
        }

        sims = 100000
        np.random.seed(42)
        meses_nombres = list(factores_peru.keys())
        p10_l, p50_l, p90_l = [], [], []

        for m in meses_nombres:
            factor = factores_peru[m]
            media_mes = base_mensual_historica * factor
            std_mes = max(std_mensual_historica * factor, base_mensual_historica * 0.05)
            
            # Simulación estocástica directa a nivel mensual (100,000 escenarios)
            totales = np.random.normal(loc=media_mes, scale=std_mes, size=sims)
            totales = np.clip(totales, 0, None)

            p10_l.append(np.percentile(totales, 10))
            p50_l.append(np.percentile(totales, 50))
            p90_l.append(np.percentile(totales, 90))

        df_res_mc = pd.DataFrame({
            'Mes': meses_nombres,
            'Pesimista (P10)': p10_l,
            'Base / Esperado (P50)': p50_l,
            'Optimista (P90)': p90_l
        })

        fig_mc = px.line(
            df_res_mc, x='Mes', y=['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)'],
            title="Proyección Anual de Bandas Estacionales Perú - Convenios (S/)", markers=True
        )
        st.plotly_chart(fig_mc, use_container_width=True)

        st.markdown("### 📋 Resumen Financiero Proyectado Estacional (S/)")
        df_show = df_res_mc.copy()
        for col in ['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)']:
            df_show[col] = df_show[col].apply(formato_compacto_limpio)
        st.dataframe(df_show, use_container_width=True)