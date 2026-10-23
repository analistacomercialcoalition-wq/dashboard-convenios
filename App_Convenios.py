import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de página corporativa
st.set_page_config(
    page_title="Dashboard Gerencial & Modelo Predictivo | Coalition Convenios",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILOS CSS PERSONALIZADOS (TEMA EJECUTIVO BLANCO Y AZUL OSCURO)
# ==========================================
st.markdown("""
    <style>
        /* Fondo Principal Claro */
        .stApp {
            background-color: #FFFFFF;
            color: #0F172A;
        }
        
        /* Barra Lateral Azul Oscuro Ejecutivo */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important;
            color: #FFFFFF !important;
        }
        
        /* Estilos de texto dentro del Sidebar */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] .stMarkdown {
            color: #F8FAFC !important;
        }
        
        /* Cajas de Selección dentro del Sidebar */
        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border-color: #334155 !important;
        }

        /* Tarjetas de Métricas KPI */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            white-space: nowrap !important;
            color: #0F172A !important;
            font-weight: 700 !important;
        }

        /* Títulos */
        h1, h2, h3 {
            color: #0F172A !important;
            font-weight: 800 !important;
        }

        /* Línea divisoria */
        hr {
            border-color: #CBD5E1 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DETECCIÓN DE IMAGEN LOGO CORPORATIVO
# ==========================================
posibles_logos = ["Convenios Coalition.png", "Convenios Coalition.jpg", "logo.png", "logo.jpg"]
logo_encontrado = next((img for img in posibles_logos if os.path.exists(img)), None)

# ==========================================
# CABECERA CON LOGO Y TÍTULO
# ==========================================
col_logo, col_tit = st.columns([1, 5])

with col_logo:
    if logo_encontrado:
        st.image(logo_encontrado, width=130)
    else:
        st.markdown("## 🦁")

with col_tit:
    st.title("CONVENIOS COALITION")
    st.markdown("##### **Matriz Gerencial de Colocaciones, Remesas y Modelo Predictivo Estacional**")

st.markdown("---")

# ==========================================
# 1. CARGA Y LIMPIEZA DE DATOS (MATRIZ PRINCIPAL Y METAS OFICIALES)
# ==========================================
@st.cache_data(ttl=600)
def cargar_datos_corporativos():
    # Matriz Principal de Operaciones (Hoja 1)
    sheet_url = "https://docs.google.com/spreadsheets/d/1IBvyIN5H1jYrwEAOD9E5nTCpaBLqxD109HMKCW0Ezt8/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    df = pd.read_csv(sheet_url, dtype=str)
    df.columns = df.columns.str.strip()
    
    # Limpieza de NETO
    df['NETO'] = pd.to_numeric(
        df['NETO'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace(' ', '').str.strip(), 
        errors='coerce'
    ).fillna(0)

    # Limpieza rigurosa de texto
    cols_a_limpiar = ['TERRITORIAL', 'ZONA', 'PLAZA', 'JEFE ZONAL', 'SUPERVISOR', 'ASESOR CORRECTO', 'ESTADO']
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
    
    # ID de desduplicación exacta
    cols_id = [c for c in df.columns if any(k in c.upper() for k in ['EXPEDIE', 'DNI', 'CREDITO', 'OPERACION'])]
    df['ID_UNICO'] = df[cols_id[0]].astype(str).str.strip() if cols_id else df.index.astype(str)
    df = df.drop_duplicates(subset=['ID_UNICO', 'AÑO_MES_SOLICITUD'], keep='first')

    # TABLA OFICIAL DE METAS POR SUPERVISOR PROVISTA POR LUIGI
    datos_metas = [
        ["PAOLA PEREZ", "ACTIVO", "LIMA", "FLAVIA LAURA", "CECILIA LOPEZ", 28, 1290000],
        ["FRANK SANTAMARIA", "ACTIVO", "JAEN", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 20, 950000],
        ["ROCIO CASTRO", "ACTIVO", "LIMA", "FLAVIA LAURA", "CECILIA LOPEZ", 28, 1290000],
        ["MIGUEL SANDOVAL", "ACTIVO", "PIURA", "ANA ROLANDO", "ANA ROLANDO", 28, 1290000],
        ["CENTHY RIOJA", "ACTIVO", "CHICLAYO", "JARUMY CHUYEN", "ANA ROLANDO", 28, 1290000],
        ["CAROL ALVAREZ", "ACTIVO", "PUNO", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 28, 1290000],
        ["FRANK HUANCARUNA", "ACTIVO", "CHICLAYO", "JARUMY CHUYEN", "ANA ROLANDO", 28, 1290000],
        ["ANDY MEDINA", "ACTIVO", "PIURA", "ANA ROLANDO", "ANA ROLANDO", 28, 1290000],
        ["VIRGILIA ARMAS", "ACTIVO", "TARAPOTO", "PEDRO PAREDES", "ANA ROLANDO", 28, 1290000],
        ["GUIDO MUCHO", "ACTIVO", "TACNA", "LUIS RAMOS", "CECILIA LOPEZ", 28, 1290000],
        ["ROSMERY REYES", "ACTIVO", "CHICLAYO", "JARUMY CHUYEN", "ANA ROLANDO", 20, 950000],
        ["PERCY RIVAS", "ACTIVO", "LIMA", "LUIS MIGUEL FLORES", "CECILIA LOPEZ", 20, 950000],
        ["FRANKLIN GUEVARA", "ACTIVO", "BAGUA", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 25, 1150000],
        ["LLOYSI FLORES", "ACTIVO", "TARAPOTO", "ANA ROLANDO", "ANA ROLANDO", 28, 1290000],
        ["LUIS MANCHEGO", "ACTIVO", "LIMA", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 28, 1290000],
        ["LIZET COCHACHIN", "ACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 28, 1290000],
        ["MICHAEL CHAVEZ", "ACTIVO", "TACNA", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 28, 1290000],
        ["ROGER MEJIA", "ACTIVO", "TRUJILLO", "GIOVANNY SILVA", "ANA ROLANDO", 28, 1290000],
        ["LOURDES SANCHEZ", "ACTIVO", "BARRANCA", "PEDRO PAREDES", "ANA ROLANDO", 28, 1290000],
        ["ALEXANDRA NARREA", "ACTIVO", "LIMA", "LUIS RAMOS", "CECILIA LOPEZ", 28, 1290000],
        ["MANUEL PUENTE", "ACTIVO", "LIMA", "LUIS RAMOS", "CECILIA LOPEZ", 28, 1290000],
        ["JAIME CRUZ", "ACTIVO", "MOYOBAMBA", "PEDRO PAREDES", "ANA ROLANDO", 28, 1290000],
        ["CLARY QUIROZ", "ACTIVO", "CHICLAYO", "JARUMY CHUYEN", "ANA ROLANDO", 28, 1290000],
        ["RENATTO CORONEL", "ACTIVO", "HUARAZ", "ANA ROLANDO", "ANA ROLANDO", 20, 950000],
        ["GIOVANNA MORALES", "ACTIVO", "TARAPOTO", "ANA ROLANDO", "ANA ROLANDO", 28, 1290000],
        ["GOLBERT BICERRA", "ACTIVO", "IQUITOS", "ANA ROLANDO", "ANA ROLANDO", 28, 1290000],
        ["ELMER BAILON", "ACTIVO", "JUANJUI", "PEDRO PAREDES", "ANA ROLANDO", 28, 1290000],
        ["BENSON WONG", "ACTIVO", "CHIMBOTE", "GIOVANNY SILVA", "ANA ROLANDO", 18, 750000],
        ["FERNANDO YUI", "INACTIVO", "CHIMBOTE", "GIOVANNY SILVA", "ANA ROLANDO", 18, 750000],
        ["LUIS RIOS", "ACTIVO", "TRUJILLO", "GIOVANNY SILVA", "ANA ROLANDO", 20, 950000],
        ["BORIS CORIMAYA", "ACTIVO", "TRUJILLO", "GIOVANNY SILVA", "ANA ROLANDO", 28, 1290000],
        ["ELIDA CARRASCO", "ACTIVO", "TARAPOTO", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 20, 950000],
        ["MARCOS TANTARICO", "ACTIVO", "TARAPOTO", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 25, 1150000],
        ["GABRIEL VARGAS", "ACTIVO", "CUSCO", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 20, 950000],
        ["VERONICA CUSICUNA", "ACTIVO", "CUSCO", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 28, 1290000],
        ["PATRICIA TORRES", "INACTIVO", "ANDAHUAYLAS", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 20, 950000],
        ["FLAVIA LAURA", "ACTIVO", "LIMA", "FLAVIA LAURA", "CECILIA LOPEZ", 28, 1290000],
        ["DAISY NAVARRO", "ACTIVO", "AREQUIPA", "CECILIA LOPEZ", "CECILIA LOPEZ", 28, 1290000],
        ["JIMMY VERA", "ACTIVO", "AREQUIPA", "CECILIA LOPEZ", "CECILIA LOPEZ", 28, 1290000],
        ["SHIRLEY SALAZAR", "ACTIVO", "LIMA", "LUIS RAMOS", "CECILIA LOPEZ", 20, 950000],
        ["JOSE AULLA", "ACTIVO", "ICA", "LUIS RAMOS", "CECILIA LOPEZ", 28, 1290000],
        ["ELVYN BETETA", "ACTIVO", "LIMA", "LUIS RAMOS", "CECILIA LOPEZ", 28, 1290000],
        ["RODRIGO LEON", "INACTIVO", "LIMA", "LUIS RAMOS", "CECILIA LOPEZ", 18, 750000],
        ["JHOEL TITO", "ACTIVO", "LIMA", "LUIS MIGUEL FLORES", "CECILIA LOPEZ", 28, 1290000],
        ["MICAELA BUENO", "ACTIVO", "LIMA", "LUIS MIGUEL FLORES", "CECILIA LOPEZ", 28, 1290000],
        ["ROCIO TRUJILLO", "ACTIVO", "LIMA", "LUIS MIGUEL FLORES", "CECILIA LOPEZ", 18, 750000],
        ["ROCIO RAMOS", "ACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 20, 950000],
        ["PAUL ROMERO", "ACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 28, 1290000],
        ["FIORELLA MORALES", "INACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 18, 750000],
        ["DEISY MANRIQUE", "ACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 20, 950000],
        ["JESUS FARFAN", "ACTIVO", "LIMA", "ANTONELLA REYES", "ENRIQUE CIUDAD", 20, 950000],
        ["YRENE CAMPOS", "ACTIVO", "ICA", "ANTONELLA REYES", "ENRIQUE CIUDAD", 20, 950000],
        ["ONELLA CAYO", "INACTIVO", "PUNO", "ANTONELLA REYES", "ENRIQUE CIUDAD", 18, 750000],
        ["BETZY CRUZ", "ACTIVO", "ABANCAY", "ANTONELLA REYES", "ENRIQUE CIUDAD", 18, 750000],
        ["NATALY CANCHARI", "ACTIVO", "AYACUCHO", "ANTONELLA REYES", "ENRIQUE CIUDAD", 18, 750000],
        ["MELISA VILLENA", "ACTIVO", "HUANCAYO", "ENRIQUE CIUDAD", "ENRIQUE CIUDAD", 20, 950000],
        ["SANDRO SENADO", "INACTIVO", "HUANCAYO", "LUIS ROJAS", "ENRIQUE CIUDAD", 18, 750000],
        ["JOSE SULCA", "ACTIVO", "HUANCAYO", "ENRIQUE CIUDAD", "ENRIQUE CIUDAD", 18, 750000],
        ["LISTAYLER SANCHEZ", "ACTIVO", "HUANUCO", "LUIS ROJAS", "ENRIQUE CIUDAD", 20, 950000],
        ["CARLOS ZUÑIGA", "ACTIVO", "CHICLAYO", "ANTONELLA REYES", "ENRIQUE CIUDAD", 18, 750000],
        ["BENIGNO BUSTINZA", "ACTIVO", "LIMA", "FLAVIA LAURA", "CECILIA LOPEZ", 18, 750000],
        ["GLADYS FLORES", "ACTIVO", "LIMA", "KARINA CHOQUECAHUA", "CECILIA LOPEZ", 18, 750000],
        ["LESLY COTRINA", "INACTIVO", "CHICLAYO", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 28, 1290000],
        ["MIGUEL HINOJOSA", "INACTIVO", "PIURA", "JOSE VALDIVIEZO", "CECILIA LOPEZ", 28, 1290000],
        ["ISAIAS ESCOBEDO", "INACTIVO", "HUACHO", "PEDRO PAREDES", "ANA ROLANDO", 28, 1290000],
        ["EMELYN DELGADO", "ACTIVO", "AREQUIPA", "CECILIA LOPEZ", "CECILIA LOPEZ", 18, 750000],
        ["VICTOR CHUÑE", "ACTIVO", "LIMA", "CECILIA LOPEZ", "CECILIA LOPEZ", 18, 750000],
        ["VERONICA PAUCAR", "ACTIVO", "LIMA", "LUIS MIGUEL FLORES", "CECILIA LOPEZ", 18, 750000],
        ["GIANINA SACHUN", "ACTIVO", "CHIMBOTE", "GIOVANNY SILVA", "ANA ROLANDO", 18, 750000],
        ["YANETH HUAMAN", "ACTIVO", "LIMA", "ANTONELLA REYES", "ENRIQUE CIUDAD", 18, 750000],
        ["RAQUEL ROJAS", "ACTIVO", "HUANCAYO", "RONALD VIDAL", "ENRIQUE CIUDAD", 18, 750000],
        ["JINES SEDANO", "ACTIVO", "HUANCAYO", "LUIS ROJAS", "ENRIQUE CIUDAD", 18, 750000]
    ]

    df_metas_oficial = pd.DataFrame(
        datos_metas, 
        columns=['SUPERVISOR', 'ESTADO_SUP', 'PLAZA', 'JEFE ZONAL', 'TERRITORIAL', 'META DE OPERACIONES', 'META DESEMBOLSO']
    )
    for c in ['SUPERVISOR', 'ESTADO_SUP', 'PLAZA', 'JEFE ZONAL', 'TERRITORIAL']:
        df_metas_oficial[c] = df_metas_oficial[c].str.strip().str.upper()

    return df, df_metas_oficial

with st.spinner("Sincronizando matriz corporativa Coalition y Metas Oficiales..."):
    df_base, df_metas_oficial = cargar_datos_corporativos()

def obtener_opciones_limpias(df_in, col_name):
    if col_name in df_in.columns:
        elementos = sorted([x for x in df_in[col_name].dropna().unique() if x not in ['', 'NAN', 'NAT', 'NONE']])
        return elementos
    return []

# ==========================================
# 2. SISTEMA DE AUTENTICACIÓN Y SEGURIDAD (SOLO LUIGI SOCCA)
# ==========================================
if logo_encontrado:
    st.sidebar.image(logo_encontrado, use_column_width=True)

st.sidebar.markdown("<h2 style='color: #D97706; text-align: center;'>CONVENIOS COALITION</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Credenciales de Acceso")

CREDENCIALES_USUARIOS = {
    "luigi.socca@coalition.com.pe": {
        "password": "45775003",
        "territorial": "TODAS"
    }
}

input_correo = st.sidebar.text_input("Correo Corporativo:", value="").strip().lower()
input_pass = st.sidebar.text_input("Contraseña:", type="password", value="").strip()

if not input_correo or not input_pass:
    st.sidebar.warning("⚠️ Por favor ingrese su correo y contraseña corporativa para acceder al sistema.")
    st.stop()

usuario_info = CREDENCIALES_USUARIOS.get(input_correo, None)
if usuario_info is None or usuario_info["password"] != input_pass:
    st.sidebar.error("⚠️ Correo o contraseña incorrectos.")
    st.stop()

territorial_asignada = usuario_info["territorial"]
df_flt_sidebar = df_base.copy()

if territorial_asignada != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['TERRITORIAL'] == territorial_asignada]
    st.sidebar.info(f"📌 Acceso exclusivo a Territorial: **{territorial_asignada}**")
else:
    st.sidebar.success("👑 Acceso Gerencial Total (Todas las Territoriales)")

st.sidebar.markdown("---")
st.sidebar.subheader("🏢 Estructura Comercial")

# 1. TERRITORIAL
col_territorial = 'TERRITORIAL' if 'TERRITORIAL' in df_base.columns else None
if territorial_asignada == "TODAS":
    territoriales = ["TODOS"] + (obtener_opciones_limpias(df_flt_sidebar, col_territorial) if col_territorial else [])
    sel_territorial = st.sidebar.selectbox("Territorial", territoriales)
    if sel_territorial != "TODOS" and col_territorial:
        df_flt_sidebar = df_flt_sidebar[df_flt_sidebar[col_territorial] == sel_territorial]
else:
    st.sidebar.selectbox("Territorial", [territorial_asignada], disabled=True)
    sel_territorial = territorial_asignada

# 2. ZONA
zonas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'ZONA')
sel_zona = st.sidebar.selectbox("Zona", zonas)
if sel_zona != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['ZONA'] == sel_zona]

# 3. PLAZA
plazas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'PLAZA')
sel_plaza = st.sidebar.selectbox("Plaza", plazas)
if sel_plaza != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['PLAZA'] == sel_plaza]

# 4. JEFE ZONAL (ESTRICTO)
col_jefe_exacta = 'JEFE ZONAL' if 'JEFE ZONAL' in df_base.columns else None
jefes = ["TODOS"] + (obtener_opciones_limpias(df_flt_sidebar, col_jefe_exacta) if col_jefe_exacta else [])
sel_jefe = st.sidebar.selectbox("Jefe Zonal", jefes)
if sel_jefe != "TODOS" and col_jefe_exacta:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar[col_jefe_exacta] == sel_jefe]

# 5. SUPERVISOR
supervisores = ["TODOS"] + obtener_opciones_limpias(df_flt_sidebar, 'SUPERVISOR')
sel_sup = st.sidebar.selectbox("Supervisor", supervisores)
if sel_sup != "TODOS" and 'SUPERVISOR' in df_flt_sidebar.columns:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['SUPERVISOR'] == sel_sup]

# 6. ASESOR
asesores = ["TODOS"] + obtener_opciones_limpias(df_flt_sidebar, 'ASESOR CORRECTO')
sel_asesor = st.sidebar.selectbox("Asesor", asesores)
if sel_asesor != "TODOS" and 'ASESOR CORRECTO' in df_flt_sidebar.columns:
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['ASESOR CORRECTO'] == sel_asesor]

df_flt = df_flt_sidebar.copy()

# ==========================================
# 3. FILTROS EN ENCABEZADO SUPERIOR
# ==========================================
st.markdown("### 🎛️ Controles Temporales y Estado Operativo")
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

# --- FILTRADO PRODUCCIÓN (ESTADO + MES DESEMBOLSO) ---
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
kpi4.metric("📈 Prom. Diario / Ticket", formato_compacto_limpio(prom_diario))

st.markdown("---")

df_mensual = df_flt_prod.groupby('AÑO_MES_DESEMBOLSO').agg(
    MONTO_TOTAL_NETO=('NETO', 'sum'),
    OPERACIONES=('NETO', 'count')
).reset_index() if not df_flt_prod.empty else pd.DataFrame()

# ==========================================
# 4. ESTRUCTURA DE PESTAÑAS DEL DASHBOARD
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Producción Total por Mes", 
    "📦 Remesas (Volumen por Fecha de Solicitud)", 
    "🏆 Red Comercial & Ranking", 
    "🎯 Reporte de Venta por Supervisor",
    "🎲 Monte Carlo (Estacionalidad Perú)"
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
            color_discrete_sequence=['#0F172A']
        )
        fig_bar.update_traces(texttemplate='S/ %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=500, xaxis_tickangle=-45, template="plotly_white")
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
                color_discrete_sequence=['#0D9488']
            )
            fig_rem_bar.update_traces(texttemplate='%{text:,} Ops', textposition='outside')
            fig_rem_bar.update_layout(height=450, xaxis_tickangle=-45, template="plotly_white")
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
            fig_pie_est.update_layout(height=450, template="plotly_white")
            st.plotly_chart(fig_pie_est, use_container_width=True)

# --- PESTAÑA 3: RED COMERCIAL ---
with tab3:
    st.subheader("Evaluación de Desempeño por Plaza y Jefatura Zonal")
    col_a, col_b = st.columns(2)
    with col_a:
        if not df_flt_prod.empty:
            df_plaza = df_flt_prod.groupby('PLAZA')['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_plz = px.bar(df_plaza, x='NETO', y='PLAZA', orientation='h', title="Monto Neto por Plaza (S/)", text_auto=',.0f', color_discrete_sequence=['#1E3A8A'])
            fig_plz.update_layout(template="plotly_white")
            st.plotly_chart(fig_plz, use_container_width=True)
    with col_b:
        if not df_flt_prod.empty and col_jefe_exacta:
            df_jefe = df_flt_prod.groupby(col_jefe_exacta)['NETO'].sum().reset_index().sort_values('NETO', ascending=True)
            fig_jefe = px.bar(df_jefe, x='NETO', y=col_jefe_exacta, orientation='h', title="Monto Neto por Jefe Zonal (S/)", text_auto=',.0f', color_discrete_sequence=['#047857'])
            fig_jefe.update_layout(template="plotly_white")
            st.plotly_chart(fig_jefe, use_container_width=True)

# --- PESTAÑA 4: REPORTE DE VENTA ORDENADO Y NUMEROS COMPACTOS ---
with tab4:
    st.subheader("🎯 Reporte de Venta y Metas por Línea de Supervisión")
    st.markdown("Consolidado ordenado jerárquicamente por **% Cumplimiento Ops** (1º) y **% Cumplimiento Monto** (2º) en formato compacto gerencial.")

    # 1. Utilizar df_flt_prod (YA FILTRADO POR MESES DE DESEMBOLSO Y ESTADO SELECCIONADO)
    if not df_flt_prod.empty and 'SUPERVISOR' in df_flt_prod.columns:
        df_prod_sup = df_flt_prod.groupby('SUPERVISOR').agg(
            OPERACIONES_DESEMBOLSA=('NETO', 'count'),
            MONTO_DESEMBOLSADO=('NETO', 'sum')
        ).reset_index()
    else:
        df_prod_sup = pd.DataFrame(columns=['SUPERVISOR', 'OPERACIONES_DESEMBOLSA', 'MONTO_DESEMBOLSADO'])

    # 2. Aplicar los filtros de la barra lateral sobre la tabla de metas oficial
    df_metas_flt = df_metas_oficial.copy()
    if sel_territorial != "TODOS":
        df_metas_flt = df_metas_flt[df_metas_flt['TERRITORIAL'] == sel_territorial]
    if sel_zona != "TODAS":
        df_metas_flt = df_metas_flt[df_metas_flt['PLAZA'] == sel_zona]
    if sel_plaza != "TODAS":
        df_metas_flt = df_metas_flt[df_metas_flt['PLAZA'] == sel_plaza]
    if sel_jefe != "TODOS":
        df_metas_flt = df_metas_flt[df_metas_flt['JEFE ZONAL'] == sel_jefe]
    if sel_sup != "TODOS":
        df_metas_flt = df_metas_flt[df_metas_flt['SUPERVISOR'] == sel_sup]

    # 3. Cruzar la tabla de metas con el avance real desembolsado
    df_reporte = pd.merge(df_metas_flt, df_prod_sup, on='SUPERVISOR', how='left')
    df_reporte['OPERACIONES_DESEMBOLSA'] = df_reporte['OPERACIONES_DESEMBOLSA'].fillna(0).astype(int)
    df_reporte['MONTO_DESEMBOLSADO'] = df_reporte['MONTO_DESEMBOLSADO'].fillna(0)

    # 4. Calcular % de cumplimiento
    df_reporte['CUMPLIMIENTO_OPS'] = np.where(
        df_reporte['META DE OPERACIONES'] > 0,
        (df_reporte['OPERACIONES_DESEMBOLSA'] / df_reporte['META DE OPERACIONES']) * 100,
        0.0
    )
    df_reporte['CUMPLIMIENTO_MONTO'] = np.where(
        df_reporte['META DESEMBOLSO'] > 0,
        (df_reporte['MONTO_DESEMBOLSADO'] / df_reporte['META DESEMBOLSO']) * 100,
        0.0
    )

    # 5. ORDENAMIENTO EXPLICITO SOLICITADO: 1º CUMPLIMIENTO_OPS, 2º CUMPLIMIENTO_MONTO (AMBOS DESCENDENTES)
    df_reporte = df_reporte.sort_values(
        by=['CUMPLIMIENTO_OPS', 'CUMPLIMIENTO_MONTO'], 
        ascending=[False, False]
    ).reset_index(drop=True)

    # 6. Reordenar y renombrar la tabla final
    cols_ordenadas = [
        'SUPERVISOR', 'ESTADO_SUP', 'PLAZA', 'JEFE ZONAL', 'TERRITORIAL',
        'META DE OPERACIONES', 'OPERACIONES_DESEMBOLSA', 'CUMPLIMIENTO_OPS',
        'META DESEMBOLSO', 'MONTO_DESEMBOLSADO', 'CUMPLIMIENTO_MONTO'
    ]
    df_reporte_final = df_reporte[cols_ordenadas].rename(columns={
        'SUPERVISOR': 'Supervisor',
        'ESTADO_SUP': 'Estado',
        'PLAZA': 'Plaza / Zona',
        'JEFE ZONAL': 'Jefe Zonal',
        'TERRITORIAL': 'Territorial',
        'META DE OPERACIONES': 'Meta de Operaciones',
        'OPERACIONES_DESEMBOLSA': 'Ops Desembolsadas',
        'CUMPLIMIENTO_OPS': '% Cumplimiento Ops',
        'META DESEMBOLSO': 'Meta Desembolso (S/)',
        'MONTO_DESEMBOLSADO': 'Monto Desembolsado (S/)',
        'CUMPLIMIENTO_MONTO': '% Cumplimiento Monto'
    })

    # Función para colorear el semáforo según el porcentaje
    def aplicar_estilo_semaforo(val):
        if val < 80.0:
            return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'  # Rojo
        elif val < 100.0:
            return 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'  # Amarillo tenue
        else:
            return 'background-color: #DCFCE7; color: #166534; font-weight: bold;'  # Verde

    if not df_reporte_final.empty:
        # FORMATOS AJUSTADOS A NÚMEROS COMPACTOS Y ENTEROS EN %
        styled_df = df_reporte_final.style.map(
            aplicar_estilo_semaforo, 
            subset=['% Cumplimiento Ops', '% Cumplimiento Monto']
        ).format({
            'Meta de Operaciones': '{:,.0f}',
            'Ops Desembolsadas': '{:,.0f}',
            '% Cumplimiento Ops': '{:,.0f}%',
            'Meta Desembolso (S/)': formato_compacto_limpio,
            'Monto Desembolsado (S/)': formato_compacto_limpio,
            '% Cumplimiento Monto': '{:,.0f}%'
        })

        st.dataframe(styled_df, use_container_width=True)

        st.markdown("#### 📌 Leyenda de Semáforo y Ranking:")
        l_col1, l_col2, l_col3 = st.columns(3)
        l_col1.markdown("🔴 **Rojo (Bajo):** Menor a 80%")
        l_col2.markdown("🟡 **Amarillo (Medio):** Entre 80% y 99%")
        l_col3.markdown("🟢 **Verde (Meta Alcanzada):** 100% o superior")
    else:
        st.info("No se encontraron registros de metas que coincidan con los filtros comerciales seleccionados.")

# --- PESTAÑA 5: MONTE CARLO ---
with tab5:
    st.subheader("🎲 Motor Estocástico Monte Carlo (100,000 Escenarios - Convenios Perú)")
    st.markdown("Proyección basada en el **promedio mensual histórico real** de la matriz, calibrada con la sensibilidad de créditos por planilla (Picos en Noviembre, Diciembre y Julio).")

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

    df_res_mc['P10_FMT'] = df_res_mc['Pesimista (P10)'].apply(formato_compacto_limpio)
    df_res_mc['P50_FMT'] = df_res_mc['Base / Esperado (P50)'].apply(formato_compacto_limpio)
    df_res_mc['P90_FMT'] = df_res_mc['Optimista (P90)'].apply(formato_compacto_limpio)

    fig_mc = px.line(
        df_res_mc, x='Mes', y=['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)'],
        title="Proyección Anual de Bandas Estacionales Perú - Convenios (S/)",
        markers=True,
        color_discrete_map={
            'Pesimista (P10)': '#EF4444',
            'Base / Esperado (P50)': '#2563EB',
            'Optimista (P90)': '#10B981'
        }
    )

    fig_mc.update_traces(
        mode='lines+markers+text',
        textposition='top center'
    )
    
    fig_mc.data[0].text = df_res_mc['P10_FMT']
    fig_mc.data[1].text = df_res_mc['P50_FMT']
    fig_mc.data[2].text = df_res_mc['P90_FMT']

    fig_mc.update_layout(height=500, yaxis_title="Monto Proyectado (S/)", template="plotly_white")
    st.plotly_chart(fig_mc, use_container_width=True)

    st.markdown("### 📋 Resumen Financiero Proyectado Estacional (S/)")
    df_show = df_res_mc[['Mes', 'Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)']].copy()
    for col in ['Pesimista (P10)', 'Base / Esperado (P50)', 'Optimista (P90)']:
        df_show[col] = df_show[col].apply(formato_compacto_limpio)
    st.dataframe(df_show, use_container_width=True)