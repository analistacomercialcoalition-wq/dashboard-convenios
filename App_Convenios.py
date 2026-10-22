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
# 1. CARGA Y LIMPIEZA DE DATOS
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

    # Limpieza de texto de jerarquía comercial
    cols_a_limpiar = ['ZONA', 'PLAZA', 'JEFE ZONAL', 'SUPERVISOR', 'ASESOR CORRECTO', 'ESTADO']
    for col in cols_a_limpiar:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip().str.upper()

    # Parseo de Fecha de Solicitud (DD/MM/YYYY)
    col_sol = [c for c in df.columns if 'SOLICITUD' in c.upper()][0]
    df['FECHA_SOLICITUD_DT'] = pd.to_datetime(df[col_sol], format='%d/%m/%Y', errors='coerce')
    mask_null_sol = df['FECHA_SOLICITUD_DT'].isna() & (df[col_sol] != '')
    if mask_null_sol.any():
        df.loc[mask_null_sol, 'FECHA_SOLICITUD_DT'] = pd.to_datetime(
            df.loc[mask_null_sol, col_sol], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_SOLICITUD'] = df['FECHA_SOLICITUD_DT'].dt.to_period('M').astype(str)

    # Parseo de Fecha de Desembolso (DD/MM/YYYY)
    col_des = [c for c in df.columns if 'DESEMBOLSO' in c.upper()][0]
    df['FECHA_DESEMBOLSO_DT'] = pd.to_datetime(df[col_des], format='%d/%m/%Y', errors='coerce')
    mask_null_des = df['FECHA_DESEMBOLSO_DT'].isna() & (df[col_des] != '')
    if mask_null_des.any():
        df.loc[mask_null_des, 'FECHA_DESEMBOLSO_DT'] = pd.to_datetime(
            df.loc[mask_null_des, col_des], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_DESEMBOLSO'] = df['FECHA_DESEMBOLSO_DT'].dt.to_period('M').astype(str)

    df = df[df['FECHA_SOLICITUD_DT'].notna()]
    
    # ID de desduplicación
    cols_id = [c for c in df.columns if any(k in c.upper() for k in ['EXPEDIE', 'DNI', 'CREDITO', 'OPERACION'])]
    df['ID_UNICO'] = df[cols_id[0]].astype(str).str.strip() if cols_id else df.index.astype(str)

    df = df.drop_duplicates(subset=['ID_UNICO', 'AÑO_MES_SOLICITUD'], keep='first')
    
    return df

with st.spinner("Sincronizando base comercial..."):
    df_base = cargar_datos_corporativos()

def obtener_opciones_limpias(df_in, col_name):
    if col_name in df_in.columns:
        elementos = sorted([x for x in df_in[col_name].dropna().unique() if x not in ['', 'NAN', 'NAT', 'NONE']])
        return elementos
    return []

# ==========================================
# 2. FILTROS EN BARRA LATERAL (ESTRUCTURA COMERCIAL ESTRICTA)
# ==========================================
st.sidebar.header("🔍 Panel de Filtros y Control")
st.sidebar.subheader("🏢 Estructura Comercial")

df_flt_sidebar = df_base.copy()

zonas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'ZONA')
sel_zona = st.sidebar.selectbox("Zona", zonas)
if sel_zona != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['ZONA'] == sel_zona]

plazas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'PLAZA')
sel_plaza = st.sidebar.selectbox("Plaza", plazas)
if sel_plaza != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['PLAZA'] == sel_plaza]

col_jefe_exacta = 'JEFE ZONAL' if 'JEFE ZONAL' in df_base.columns else ('JDN' if 'JDN' in df_base.columns else None)
jefes = ["TODOS"] + (obtener_opciones_limpias(df_flt_sidebar, col_jefe_exacta) if col_jefe_exacta else [])
sel_jefe = st.sidebar.selectbox("Jefe Zonal", jefes)
if sel_jefe != "TODOS" and col_jefe_exacta:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar[col_jefe_exacta] == sel_jefe]

supervisores = ["TODOS"] + obtener_opciones_limpias(df_flt_sidebar, 'SUPERVISOR')
sel_sup = st.sidebar.selectbox("Supervisor", supervisores)
if sel_sup != "TODOS" and 'SUPERVISOR' in df_flt_sidebar.columns:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['SUPERVISOR'] == sel_sup]

asesores = ["TODOS"] + obtener_opciones_limpias(df_flt_sidebar, 'ASESOR CORRECTO')
sel_asesor = st.sidebar.selectbox("Asesor", asesores)
if sel_asesor != "TODOS" and 'ASESOR CORRECTO' in df_flt_sidebar.columns:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['ASESOR CORRECTO'] == sel_asesor]

df_flt = df_flt_sidebar.copy()

# ==========================================
# 3. FILTROS EN ENCABEZADO SUPERIOR
# ==========================================
st.markdown("### 🎛️ Filtros de Control Temporal y Estado")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    estados_disp = obtener_opciones_limpias(df_flt, 'ESTADO')
    sel_estados_prod = st.multiselect(
        "📌 Estado Operación (Filtro Producción)", 
        options=estados_disp, 
        default=["DESEMBOLSADO"] if "DESEMBOLSADO" in estados_disp else []
    )

with f_col2:
    meses_des_disp = obtener_opciones_limpias(df_base, 'AÑO_MES_DESEMBOLSO')
    sel_meses_desembolso = st.multiselect(
        "🗓️ Meses Desembolso (Filtro Producción)", 
        options=meses_des_disp, 
        default=[]
    )

with f_col3:
    meses_sol_disp = obtener_opciones_limpias(df_base, 'AÑO_MES_SOLICITUD')
    sel_meses_remesa = st.multiselect(
        "📥 Filtrar Meses de Remesa (Fecha Solicitud)", 
        options=meses_sol_disp, 
        default=[]
    )

# --- FILTRADO PRODUCCIÓN ---
df_flt_prod = df_flt.copy()
if sel_estados_prod:
    df_flt_prod = df_flt_prod[df_flt_prod['ESTADO'].isin(sel_estados_prod)]
if sel_meses_desembolso:
    df_flt_prod = df_flt_prod[df_flt_prod['AÑO_MES_DESEMBOLSO'].isin(sel_meses_desembolso)]

# --- FILTRADO REMESAS ---
df_remesas = df_flt.copy()
if sel_meses_remesa:
    df_remesas = df_remesas[df_remesas['AÑO_MES_SOLICITUD'].isin(sel_meses_remesa)]

st.markdown("---")

def formato_compacto_limpio(val):
    if val >= 1e6:
        return f"S/ {val/1e6:,.2f}M"
    elif val >= 1e3:
        return f"S/ {val/1e3:,.1f}k"
    else:
        return f"S/ {val:,.2f}"

total_neto = df_flt_prod['NETO'].sum() if not df_flt_prod.empty else 0
total_ops = len(df_flt_prod)
dias_efectivos = df_flt_prod['FECHA_DESEMBOLSO_DT'].nunique() if not df_flt_prod.empty else 0
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
# 4. ESTRUCTURA DE PESTAÑAS
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

# --- PESTAÑA 2: REMESAS ---
with tab2:
    st.subheader("📦 Conteo Exacto de Remesas por Fecha de Solicitud (Sincronizado con Excel)")
    st.markdown("Contabiliza el total de operaciones agrupadas por su **`FECHA DE SOLICITUD`**.")

    est_rem_disp = ["TODOS"] + obtener_opciones_limpias(df_remesas, 'ESTADO')
    sel_est_rem = st.selectbox("📌 Filtrar Estado interno en Remesas (Opcional):", est_rem_disp)
    
    df_rem_tab = df_remesas.copy()
    if sel_est_rem != "TODOS":
        df_rem_tab = df_rem_tab[df_rem_tab['ESTADO'] == sel_est_rem]

    rem_total_ops = len(df_rem_tab)
    rem_dias_sol = df_rem_tab['FECHA_SOLICITUD_DT'].nunique() if not df_rem_tab.empty else 0
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
            df_rem_mensual = df_rem_mensual[df_rem_mensual['AÑO_MES_SOLICITUD'] != 'NaT'].sort_values('AÑO_MES_SOLICITUD')

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
        if not df_flt_prod.empty and col_jefe_exacta:
            df_jefe = df_flt_prod.groupby(col_jefe_exacta)['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_jefe = px.bar(df_jefe, x=col_jefe_exacta, y='NETO', orientation='h', title="Monto Neto por Jefe Zonal (S/)", text_auto=',.0f')
            st.plotly_chart(fig_jefe, use_container_width=True)

# --- PESTAÑA 4: MOTOR MONTE CARLO RESTAURADO COMPLETO ---
with tab4:
    st.subheader("🎲 Motor Estocástico Monte Carlo (100,000 Escenarios - Convenios Perú)")
    st.markdown("Proyección basada en el **promedio mensual histórico real** de la matriz, calibrada con la sensibilidad de créditos por planilla (Picos en Noviembre, Diciembre y Julio).")

    # Controles de Calibración Estacional
    with st.expander("⚙️ Calibración Avanzada de Factores Estacionales (Perú)", expanded=True):
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            f_jul = st.slider("Factor Julio (Gratificación Fiestas Patrias)", 1.0, 1.8, 1.25, 0.05)
        with col_s2:
            f_nov = st.slider("Factor Noviembre (CTS y Pre-cierre)", 1.0, 1.8, 1.20, 0.05)
        with col_s3:
            f_dic = st.slider("Factor Diciembre (Aguinaldo / Navidad)", 1.0, 2.0, 1.35, 0.05)
        with col_s4:
            f_mar = st.slider("Factor Marzo (Campaña Escolar)", 0.8, 1.4, 1.10, 0.05)

    # Cálculo dinámico basado en la producción real filtrada
    base_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].mean() if not df_mensual.empty else 28500000
    std_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].std() if (not df_mensual.empty and len(df_mensual) > 1) else base_mensual_historica * 0.12

    factores_peru = {
        'Enero': 0.85, 'Febrero': 0.90, 'Marzo': f_mar, 'Abril': 1.00,
        'Mayo': 1.02, 'Junio': 1.08, 'Julio': f_jul, 'Agosto': 0.95,
        'Setiembre': 1.00, 'Octubre': 1.05, 'Noviembre': f_nov, 'Diciembre': f_dic
    }

    sims = 100000
    np.random.seed(42)
    meses_nombres = list(factores_peru.keys())
    p10_l, p50_l, p90_l = [], [], []

    for m in meses_nombres:
        factor = factores_peru[m]
        media_mes = base_mensual_historica * factor
        std_mes = max(std_mensual_historica * factor, base_mensual_historica * 0.05)
        
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

    # Gráfico de Líneas con Bandas
    fig_mc = px.line(
        df_res_mc, x='Mes', y=['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)'],
        title="Proyección Anual de Bandas Estacionales Perú - Convenios (S/)",
        markers=True,
        color_discrete_map={
            'Pesimista (P10)': '#ef4444',
            'Base / Esperado (P50)': '#3b82f6',
            'Optimista (P90)': '#10b981'
        }
    )
    fig_mc.update_layout(height=450, yaxis_title="Monto Proyectado (S/)")
    st.plotly_chart(fig_mc, use_container_width=True)

    st.markdown("### 📋 Resumen Financiero Proyectado Estacional (S/)")
    df_show = df_res_mc.copy()
    for col in ['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)']:
        df_show[col] = df_show[col].apply(formato_compacto_limpio)
    st.dataframe(df_show, use_container_width=True)