import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
st.markdown("### **Coalition Group — Matriz de Colocaciones, Remesas y Proyecciones Estacionales Perú**")
st.markdown("---")

# ==========================================
# 1. CARGA Y LIMPIEZA DE DATOS (PARSEO PERUANO DD/MM/YYYY)
# ==========================================
@st.cache_data(ttl=600)
def cargar_datos_corporativos():
    sheet_url = "https://docs.google.com/spreadsheets/d/1IBvyIN5H1jYrwEAOD9E5nTCpaBLqxD109HMKCW0Ezt8/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    df = pd.read_csv(sheet_url, dtype=str)
    df.columns = df.columns.str.strip()
    
    # Limpieza de NETO
    df['NETO'] = pd.to_numeric(
        df['NETO'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace(' ', '').str.strip(), 
        errors='coerce'
    ).fillna(0)

    # 1. Parseo estricto de FECHA DE SOLICITUD (Formato Peruano DD/MM/YYYY)
    df['FECHA_SOLICITUD_DT'] = pd.to_datetime(df['FECHA DE SOLICITUD'], format='%d/%m/%Y', errors='coerce')
    mask_null_sol = df['FECHA_SOLICITUD_DT'].isna() & df['FECHA DE SOLICITUD'].notna()
    if mask_null_sol.any():
        df.loc[mask_null_sol, 'FECHA_SOLICITUD_DT'] = pd.to_datetime(
            df.loc[mask_null_sol, 'FECHA DE SOLICITUD'], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_SOLICITUD'] = df['FECHA_SOLICITUD_DT'].dt.to_period('M').astype(str)

    # 2. Parseo estricto de FECHA DE DESEMBOLSO (Formato Peruano DD/MM/YYYY)
    df['FECHA_DESEMBOLSO_DT'] = pd.to_datetime(df['FECHA DE DESEMBOLSO'], format='%d/%m/%Y', errors='coerce')
    mask_null_des = df['FECHA_DESEMBOLSO_DT'].isna() & df['FECHA DE DESEMBOLSO'].notna()
    if mask_null_des.any():
        df.loc[mask_null_des, 'FECHA_DESEMBOLSO_DT'] = pd.to_datetime(
            df.loc[mask_null_des, 'FECHA DE DESEMBOLSO'], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_DESEMBOLSO'] = df['FECHA_DESEMBOLSO_DT'].dt.to_period('M').astype(str)

    # Filtrar únicamente registros que contengan Fecha de Solicitud real
    df = df[df['FECHA_SOLICITUD_DT'].notna()]
    
    return df

with st.spinner("Sincronizando base de datos corporativa completa..."):
    df_base = cargar_datos_corporativos()

# Función auxiliar segura para ordenar listas con posibles valores mixtos
def obtener_lista_ordenada_segura(serie):
    elementos = serie.dropna().astype(str).unique()
    elementos_limpios = [str(x).strip() for x in elementos if str(x).strip() not in ['', 'nan', 'NaT', 'None']]
    return sorted(elementos_limpios)

# ==========================================
# 2. FILTROS EN BARRA LATERAL (JERARQUÍA COMERCIAL)
# ==========================================
st.sidebar.header("🔍 Panel de Filtros y Control")
st.sidebar.subheader("🏢 Estructura Comercial")

zonas = ["TODAS"] + obtener_lista_ordenada_segura(df_base['ZONA'])
sel_zona = st.sidebar.selectbox("Zona", zonas)

plazas = ["TODAS"] + obtener_lista_ordenada_segura(df_base['PLAZA'])
sel_plaza = st.sidebar.selectbox("Plaza", plazas)

col_jefe_nom = 'JDN' if 'JDN' in df_base.columns else 'JEFE ZONAL'
jefes = ["TODOS"] + obtener_lista_ordenada_segura(df_base[col_jefe_nom])
sel_jefe = st.sidebar.selectbox("Jefe Zonal / JDN", jefes)

supervisores = ["TODOS"] + (obtener_lista_ordenada_segura(df_base['SUPERVISOR']) if 'SUPERVISOR' in df_base.columns else [])
sel_sup = st.sidebar.selectbox("Supervisor", supervisores)

asesores = ["TODOS"] + (obtener_lista_ordenada_segura(df_base['ASESOR CORRECTO']) if 'ASESOR CORRECTO' in df_base.columns else [])
sel_asesor = st.sidebar.selectbox("Asesor", asesores)

df_flt = df_base.copy()
if sel_zona != "TODAS":
    df_flt = df_flt[df_flt['ZONA'] == sel_zona]
if sel_plaza != "TODAS":
    df_flt = df_flt[df_flt['PLAZA'] == sel_plaza]
if sel_jefe != "TODOS":
    df_flt = df_flt[df_flt[col_jefe_nom] == sel_jefe]
if sel_sup != "TODOS" and 'SUPERVISOR' in df_flt.columns:
    df_flt = df_flt[df_flt['SUPERVISOR'] == sel_sup]
if sel_asesor != "TODOS" and 'ASESOR CORRECTO' in df_flt.columns:
    df_flt = df_flt[df_flt['ASESOR CORRECTO'] == sel_asesor]

# ==========================================
# 3. FILTROS EN ENCABEZADO SUPERIOR (SEGURO)
# ==========================================
st.markdown("### 🎛️ Filtros de Control Temporal y Estado")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    estados_disp = obtener_lista_ordenada_segura(df_flt['ESTADO'])
    sel_estados_prod = st.multiselect(
        "📌 Estado Operación (Filtro Producción)", 
        options=estados_disp, 
        default=["DESEMBOLSADO"] if "DESEMBOLSADO" in estados_disp else []
    )

with f_col2:
    meses_des_disp = obtener_lista_ordenada_segura(df_base['AÑO_MES_DESEMBOLSO'])
    sel_meses_desembolso = st.multiselect(
        "🗓️ Meses Desembolso (Filtro Producción)", 
        options=meses_des_disp, 
        default=[]
    )

with f_col3:
    meses_sol_disp = obtener_lista_ordenada_segura(df_base['AÑO_MES_SOLICITUD'])
    sel_meses_remesa = st.multiselect(
        "📥 Filtrar Meses de Remesa (Fecha Solicitud)", 
        options=meses_sol_disp, 
        default=[]
    )

# --- FILTRADO PARA PRODUCCIÓN ---
df_flt_prod = df_flt.copy()
if sel_estados_prod:
    df_flt_prod = df_flt_prod[df_flt_prod['ESTADO'].isin(sel_estados_prod)]
if sel_meses_desembolso:
    df_flt_prod = df_flt_prod[df_flt_prod['AÑO_MES_DESEMBOLSO'].isin(sel_meses_desembolso)]

# --- FILTRADO PARA REMESAS (REMESAS PURAS POR FECHA SOLICITUD) ---
df_remesas = df_flt.copy()
if sel_meses_remesa:
    df_remesas = df_remesas[df_remesas['AÑO_MES_SOLICITUD'].isin(sel_meses_remesa)]

st.markdown("---")

# Formateador global
def formato_compacto_limpio(val):
    if val >= 1e6:
        return f"S/ {val/1e6:,.2f}M"
    elif val >= 1e3:
        return f"S/ {val/1e3:,.1f}k"
    else:
        return f"S/ {val:,.2f}"

# ==========================================
# 4. TARJETAS KPI EN 4 COLUMNAS (PRODUCCIÓN)
# ==========================================
total_neto = df_flt_prod['NETO'].sum() if not df_flt_prod.empty else 0
total_ops = len(df_flt_prod)
dias_efectivos = df_flt_prod['FECHA DE DESEMBOLSO'].nunique() if not df_flt_prod.empty else 0
prom_diario = total_neto / dias_efectivos if dias_efectivos > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("💰 Neto Total Desembolsado", formato_compacto_limpio(total_neto))
kpi2.metric("📋 Total Operaciones Desembolsadas", f"{total_ops:,} Ops")
kpi3.metric("📅 Días Con Desembolso", f"{dias_efectivos:,}")
kpi4.metric("📈 Prom. Diario / Ticket", f"{formato_compacto_limpio(prom_diario)}")

st.markdown("---")

df_mensual = df_flt_prod.groupby('AÑO_MES_DESEMBOLSO').agg(
    MONTO_TOTAL_NETO=('NETO', 'sum'),
    OPERACIONES=('NETO', 'count')
).reset_index() if not df_flt_prod.empty else pd.DataFrame()

# ==========================================
# 5. ESTRUCTURA DE PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Producción Total por Mes", 
    "📦 Remesas (Volumen por Fecha de Solicitud)", 
    "🏆 Red Comercial & Ranking", 
    "🎲 Monte Carlo (Estacionalidad Convenios Perú)"
])

# --- PESTAÑA 1: PRODUCCIÓN ---
with tab1:
    st.subheader("💵 Monto Neto Total Desembolsado por Periodo")
    if not df_mensual.empty:
        fig_bar = px.bar(
            df_mensual, 
            x='AÑO_MES_DESEMBOLSO', 
            y='MONTO_TOTAL_NETO',
            text='MONTO_TOTAL_NETO',
            title="Evolución del Monto Neto Total Desembolsado (S/)",
            labels={'AÑO_MES_DESEMBOLSO': 'Periodo Desembolso', 'MONTO_TOTAL_NETO': 'Monto Total Neto (S/)'},
            color_discrete_sequence=['#2563eb']
        )
        fig_bar.update_traces(texttemplate='S/ %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No se encontraron registros de producción con los filtros seleccionados.")

# --- PESTAÑA 2: REMESAS (PURA Y COMPLETA POR FECHA DE SOLICITUD) ---
with tab2:
    st.subheader("📦 Conteo Exacto de Remesas por Fecha de Solicitud (Sincronizado con Excel)")
    st.markdown("Contabiliza el total de celdas de la hoja de cálculo agrupadas por su **`FECHA DE SOLICITUD`**.")

    # Filtro interno opcional de Estado
    est_rem_disp = ["TODOS"] + obtener_lista_ordenada_segura(df_remesas['ESTADO'])
    sel_est_rem = st.selectbox("📌 Filtrar Estado interno en Remesas (Opcional):", est_rem_disp)
    
    df_rem_tab = df_remesas.copy()
    if sel_est_rem != "TODOS":
        df_rem_tab = df_rem_tab[df_rem_tab['ESTADO'] == sel_est_rem]

    rem_total_ops = len(df_rem_tab)
    rem_dias_sol = df_rem_tab['FECHA DE SOLICITUD'].nunique() if not df_rem_tab.empty else 0
    rem_prom_diario_ops = rem_total_ops / rem_dias_sol if rem_dias_sol > 0 else 0
    rem_total_monto = df_rem_tab['NETO'].sum() if not df_rem_tab.empty else 0

    r_kpi1, r_kpi2, r_kpi3, r_kpi4 = st.columns(4)
    r_kpi1.metric("📥 Total Remesas (Solicitudes)", f"{rem_total_ops:,} Ops")
    r_kpi2.metric("📊 Promedio Diario de Solicitudes", f"{rem_prom_diario_ops:,.1f} Ops/Día")
    r_kpi3.metric("🗓️ Días Con Solicitudes", f"{rem_dias_sol:,} Días")
    r_kpi4.metric("💰 Monto Referencial Solicitado", formato_compacto_limpio(rem_total_monto))

    st.markdown("---")

    col_r1, col_r2 = st.columns([2, 1])

    with col_r1:
        if not df_rem_tab.empty:
            df_rem_mensual = df_rem_tab.groupby('AÑO_MES_SOLICITUD').size().reset_index(name='CANTIDAD_SOLICITUDES')
            df_rem_mensual = df_rem_mensual.sort_values('AÑO_MES_SOLICITUD')

            fig_rem_bar = px.bar(
                df_rem_mensual,
                x='AÑO_MES_SOLICITUD',
                y='CANTIDAD_SOLICITUDES',
                text='CANTIDAD_SOLICITUDES',
                title="Conteo de Remesas por Mes de Solicitud (Sincronizado con Excel)",
                labels={'AÑO_MES_SOLICITUD': 'Mes de Solicitud', 'CANTIDAD_SOLICITUDES': 'N° de Solicitudes'},
                color_discrete_sequence=['#0d9488']
            )
            fig_rem_bar.update_traces(texttemplate='%{text:,} Ops', textposition='outside')
            fig_rem_bar.update_layout(height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig_rem_bar, use_container_width=True)
        else:
            st.info("No hay remesas registradas para los filtros seleccionados.")

    with col_r2:
        if not df_rem_tab.empty:
            df_est = df_rem_tab.groupby('ESTADO').size().reset_index(name='CANTIDAD')

            fig_pie_est = px.pie(
                df_est,
                names='ESTADO',
                values='CANTIDAD',
                title="Distribución de Estados en las Solicitudes",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie_est.update_traces(textinfo='value+percent')
            fig_pie_est.update_layout(height=450)
            st.plotly_chart(fig_pie_est, use_container_width=True)

# --- PESTAÑA 3: RED COMERCIAL ---
with tab3:
    st.subheader("Evaluación de Desempeño por Plaza y Jefatura Zonal")
    col_a, col_b = st.columns(2)
    with col_a:
        if not df_flt_prod.empty:
            df_plaza = df_flt_prod.groupby('PLAZA')['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_plz = px.bar(df_plaza, x='NETO', y='PLAZA', orientation='h', title="Monto Neto por Plaza (S/)", text_auto=',.0f')
            st.plotly_chart(fig_plz, use_container_width=True)
    with col_b:
        if not df_flt_prod.empty:
            df_jefe = df_flt_prod.groupby(col_jefe_nom)['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_jefe = px.bar(df_jefe, x=col_jefe_nom, y='NETO', orientation='h', title="Monto Neto por Jefe Zonal / JDN (S/)", text_auto=',.0f')
            st.plotly_chart(fig_jefe, use_container_width=True)

# --- PESTAÑA 4: MONTE CARLO ---
with tab4:
    st.subheader("🎲 Motor Estocástico Monte Carlo (100,000 Escenarios - Convenios Perú)")
    st.markdown("Proyección basada en el **promedio mensual histórico real** de la matriz, calibrada con la sensibilidad de créditos por planilla (Picos en Noviembre, Diciembre y Julio).")

    with st.expander("⚙️ Calibración Avanzada de Factores Estacionales (Perú)"):
        f_jul = st.slider("Factor Julio (Gratificación Fiestas Patrias)", 1.0, 1.8, 1.25)
        f_nov = st.slider("Factor Noviembre (CTS y Pre-cierre)", 1.0, 1.8, 1.20)
        f_dic = st.slider("Factor Diciembre (Aguinaldo / Navidad)", 1.0, 2.0, 1.35)
        f