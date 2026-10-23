import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import urllib.parse

st.set_page_config(
    page_title="Dashboard Gerencial & Modelo Predictivo | Coalition Convenios",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #0F172A; }
        [data-testid="stSidebar"] { background-color: #0F172A !important; color: #FFFFFF !important; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown { color: #F8FAFC !important; }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div { background-color: #1E293B !important; color: #FFFFFF !important; border-color: #334155 !important; }
        div[data-testid="stMetricValue"] { font-size: 1.6rem !important; white-space: nowrap !important; color: #0F172A !important; font-weight: 700 !important; }
        h1, h2, h3 { color: #0F172A !important; font-weight: 800 !important; }
        hr { border-color: #CBD5E1 !important; }
    </style>
""", unsafe_allow_html=True)

posibles_logos = ["Convenios Coalition.png", "Convenios Coalition.jpg", "logo.png", "logo.jpg"]
logo_encontrado = next((img for img in posibles_logos if os.path.exists(img)), None)

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_correo' not in st.session_state:
    st.session_state.usuario_correo = ""

CREDENCIALES_USUARIOS = {
    "luigi.socca@coalition.com.pe": {
        "password": "45775003",
        "territorial": "TODAS"
    },
    "cecilia.lopez@coalition.com.pe": {
        "password": "123456789",
        "territorial": "CECILIA LOPEZ"
    }
}

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_login_a, col_login_b, col_login_c = st.columns([1, 2, 1])
    with col_login_b:
        st.markdown("""
            <div style="text-align: center; background-color: #0F172A; padding: 30px; border-radius: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.2);">
                <h1 style="color: #F59E0B; margin-bottom: 0;">🦁 CONVENIOS COALITION</h1>
                <h4 style="color: #F8FAFC; margin-top: 5px;">Portal Gerencial de Control & Analytics</h4>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("form_login"):
            st.subheader("🔐 Iniciar Sesión en el Sistema")
            input_correo = st.text_input("Correo Corporativo:", value="").strip().lower()
            input_pass = st.text_input("Contraseña:", type="password", value="").strip()
            btn_ingresar = st.form_submit_button("🚀 Ingresar al Dashboard", use_container_width=True)
            if btn_ingresar:
                usuario_info = CREDENCIALES_USUARIOS.get(input_correo, None)
                if usuario_info and usuario_info["password"] == input_pass:
                    st.session_state.autenticado = True
                    st.session_state.usuario_correo = input_correo
                    st.success("✅ Acceso verificado. Cargando entorno ejecutivo...")
                    st.rerun()
                else:
                    st.error("⚠️ Correo o contraseña incorrectos. Verifique sus credenciales.")
    st.stop()

@st.cache_data(ttl=60)
def cargar_datos_corporativos():
    base_id = "1IBvyIN5H1jYrwEAOD9E5nTCpaBLqxD109HMKCW0Ezt8"
    
    sheet_url_hoja1 = f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    df = pd.read_csv(sheet_url_hoja1, dtype=str)
    df.columns = df.columns.astype(str).str.strip()
    
    df['NETO'] = pd.to_numeric(
        df['NETO'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace(' ', '').str.strip(), 
        errors='coerce'
    ).fillna(0)

    cols_a_limpiar = ['TERRITORIAL', 'ZONA', 'PLAZA', 'JEFE ZONAL', 'SUPERVISOR', 'ASESOR CORRECTO', 'ESTADO']
    for col in cols_a_limpiar:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip().str.upper()

    col_sol = [c for c in df.columns if 'SOLICITUD' in c.upper()][0]
    dt_sol = pd.to_datetime(df[col_sol], errors='coerce', format='mixed', dayfirst=True)
    df['FECHA_SOLICITUD_DT'] = dt_sol
    df['AÑO_MES_SOLICITUD'] = dt_sol.dt.strftime('%Y-%m').fillna('')
    mask_sol = df['AÑO_MES_SOLICITUD'] == ''
    if mask_sol.any():
        df.loc[mask_sol, 'AÑO_MES_SOLICITUD'] = df.loc[mask_sol, col_sol].astype(str).str.slice(0, 7)

    col_des = [c for c in df.columns if 'DESEMBOLSO' in c.upper()][0]
    dt_des = pd.to_datetime(df[col_des], errors='coerce', format='mixed', dayfirst=True)
    df['FECHA_DESEMBOLSO_DT'] = dt_des
    df['AÑO_MES_DESEMBOLSO'] = dt_des.dt.strftime('%Y-%m').fillna('')
    mask_des = df['AÑO_MES_DESEMBOLSO'] == ''
    if mask_des.any():
        df.loc[mask_des, 'AÑO_MES_DESEMBOLSO'] = df.loc[mask_des, col_des].astype(str).str.slice(0, 7)

    df['MES_DESEMBOLSO_NUM'] = dt_des.dt.month.fillna(0).astype(int)

    # Identificar columna DNI de Hoja 1 (Columna V / índice 21 o por nombre)
    if len(df.columns) > 21:
        col_v_nombre = df.columns[21]
        df['DNI_HOJA1'] = df[col_v_nombre].astype(str).str.strip()
    else:
        cols_dni_h1 = [c for c in df.columns if 'DNI' in c.upper()]
        df['DNI_HOJA1'] = df[cols_dni_h1[0]].astype(str).str.strip() if cols_dni_h1 else ''
    
    df['DNI_HOJA1'] = df['DNI_HOJA1'].apply(lambda x: x.zfill(8) if x.isdigit() and len(x) < 8 else x)

    cols_id = [c for c in df.columns if any(k in c.upper() for k in ['EXPEDIE', 'DNI', 'CREDITO', 'OPERACION'])]
    df['ID_UNICO'] = df[cols_id[0]].astype(str).str.strip() if cols_id else df.index.astype(str)
    df = df.drop_duplicates(subset=['ID_UNICO', 'AÑO_MES_SOLICITUD'], keep='first')

    try:
        nombre_pestana_codificado = urllib.parse.quote("Dotación")
        sheet_url_dotacion = f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet={nombre_pestana_codificado}"
        df_dotacion = pd.read_csv(sheet_url_dotacion, dtype=str)
        df_dotacion.columns = df_dotacion.columns.astype(str).str.strip()
        
        # Limpieza y estandarización de columnas para filtros
        for c in df_dotacion.columns:
            df_dotacion[c] = df_dotacion[c].fillna('').astype(str).str.strip()
            if c.upper() in ['TERRITORIAL', 'ZONA', 'PLAZA', 'JEFE ZONAL', 'SUPERVISOR', 'ASESOR CORRECTO', 'ESTADO']:
                df_dotacion[c] = df_dotacion[c].str.upper()

        # Formatear la columna DNI a 8 dígitos con 0 a la izquierda
        cols_dni = [c for c in df_dotacion.columns if 'DNI' in c.upper()]
        if cols_dni:
            col_dni = cols_dni[0]
            df_dotacion[col_dni] = df_dotacion[col_dni].apply(lambda x: x.zfill(8) if x and x.isdigit() and len(x) < 8 else x)
    except Exception:
        df_dotacion = pd.DataFrame(columns=['ASESOR CORRECTO', 'DNI', 'ESTADO', 'SUPERVISOR', 'JEFE ZONAL', 'PLAZA', 'ZONA', 'TERRITORIAL'])

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
        df_metas_oficial[c] = df_metas_oficial[c].astype(str).str.strip().str.upper()

    return df, df_metas_oficial, df_dotacion

with st.spinner("Sincronizando matriz corporativa Coalition..."):
    df_base, df_metas_oficial, df_dotacion = cargar_datos_corporativos()

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

def obtener_opciones_limpias(df_in, col_name):
    if df_in is not None and isinstance(df_in, pd.DataFrame) and col_name in df_in.columns:
        elementos = sorted([str(x) for x in df_in[col_name].dropna().unique() if str(x).strip() not in ['', 'NAN', 'NAT', 'NONE', 'NaT', 'nan']])
        return elementos
    return []

if logo_encontrado:
    st.sidebar.image(logo_encontrado, use_column_width=True)

st.sidebar.markdown("<h2 style='color: #D97706; text-align: center;'>CONVENIOS COALITION</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"👤 **Usuario:** {st.session_state.usuario_correo}")

if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.usuario_correo = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🏢 Estructura Comercial")

territorial_asignada = CREDENCIALES_USUARIOS[st.session_state.usuario_correo]["territorial"]
df_flt_sidebar = df_base.copy()

if territorial_asignada != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['TERRITORIAL'] == territorial_asignada]
    st.sidebar.info(f"📌 Acceso exclusivo a Territorial: **{territorial_asignada}**")
else:
    st.sidebar.success("👑 Acceso Gerencial Total (Todas las Territoriales)")

col_territorial = 'TERRITORIAL' if 'TERRITORIAL' in df_base.columns else None
if territorial_asignada == "TODAS":
    territoriales = ["TODOS"] + (obtener_opciones_limpias(df_flt_sidebar, col_territorial) if col_territorial else [])
    sel_territorial = st.sidebar.selectbox("Territorial", territoriales)
    if sel_territorial != "TODOS" and col_territorial:
        df_flt_sidebar = df_flt_sidebar[df_flt_sidebar[col_territorial] == sel_territorial]
else:
    st.sidebar.selectbox("Territorial", [territorial_asignada], disabled=True)
    sel_territorial = territorial_asignada

zonas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'ZONA')
sel_zona = st.sidebar.selectbox("Zona", zonas)
if sel_zona != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['ZONA'] == sel_zona]

plazas = ["TODAS"] + obtener_opciones_limpias(df_flt_sidebar, 'PLAZA')
sel_plaza = st.sidebar.selectbox("Plaza", plazas)
if sel_plaza != "TODAS":
    df_flt_sidebar = df_flt_sidebar[df_flt_sidebar['PLAZA'] == sel_plaza]

col_jefe_exacta = 'JEFE ZONAL' if 'JEFE ZONAL' in df_base.columns else None
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

st.markdown("### 🎛️ Controles Temporales y Estado Operativo")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    estados_disp = sorted([x for x in df_base['ESTADO'].dropna().unique() if str(x).strip() not in ['', 'NAN', 'NONE']])
    sel_estados_prod = st.multiselect(
        "📌 Estado Operación (Filtro Producción)", 
        options=estados_disp, 
        default=["DESEMBOLSADO"] if "DESEMBOLSADO" in estados_disp else []
    )

with f_col2:
    meses_des_disp = sorted([x for x in df_base['AÑO_MES_DESEMBOLSO'].dropna().unique() if str(x).strip() not in ['', 'NAN', 'NAT', 'NONE']])
    sel_meses_desembolso = st.multiselect(
        "🗓️ Meses Desembolso (Filtro Producción)", 
        options=meses_des_disp, 
        default=[]
    )

with f_col3:
    meses_sol_disp = sorted([x for x in df_base['AÑO_MES_SOLICITUD'].dropna().unique() if str(x).strip() not in ['', 'NAN', 'NAT', 'NONE']])
    sel_meses_remesa = st.multiselect(
        "📥 Filtrar Meses de Remesa (Fecha Solicitud)", 
        options=meses_sol_disp, 
        default=[]
    )

df_flt_prod = df_flt.copy()
if sel_estados_prod:
    df_flt_prod = df_flt_prod[df_flt_prod['ESTADO'].isin(sel_estados_prod)]
if sel_meses_desembolso:
    df_flt_prod = df_flt_prod[df_flt_prod['AÑO_MES_DESEMBOLSO'].isin(sel_meses_desembolso)]

df_remesas = df_flt.copy()
if sel_meses_remesa:
    df_remesas = df_remesas[df_remesas['AÑO_MES_SOLICITUD'].isin(sel_meses_remesa)]

st.markdown("---")

def formato_compacto_limpio(val):
    if pd.isna(val):
        return "S/ 0.00"
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Producción Total por Mes", 
    "📦 Remesas (Volumen por Fecha de Solicitud)", 
    "🏆 Red Comercial & Ranking", 
    "🎯 Reporte de Venta por Supervisor",
    "🎲 Monte Carlo (Estacionalidad Perú)",
    "👥 Dotación"
])

with tab1:
    st.subheader("💵 Evolución Diaria y Curva Ejecutiva de Producción (Millones de Soles)")
    
    if not df_flt_prod.empty and df_flt_prod['FECHA_DESEMBOLSO_DT'].notna().any():
        df_diario_prod = df_flt_prod.groupby(df_flt_prod['FECHA_DESEMBOLSO_DT'].dt.date)['NETO'].sum().reset_index()
        df_diario_prod = df_diario_prod.sort_values('FECHA_DESEMBOLSO_DT')
        df_diario_prod['FECHA_STR'] = pd.to_datetime(df_diario_prod['FECHA_DESEMBOLSO_DT']).dt.strftime('%d %b')
        df_diario_prod['MILLONES'] = df_diario_prod['NETO'] / 1e6
        df_diario_prod['FMT_M'] = df_diario_prod['MILLONES'].apply(lambda x: f"{x:,.1f}" if x > 0 else "0")

        metas_meta_l = []
        for d in pd.to_datetime(df_diario_prod['FECHA_DESEMBOLSO_DT']):
            is_sabado = (d.dayofweek == 5)
            metas_meta_l.append(1.3 if is_sabado else 2.9)
        df_diario_prod['META_MILLONES'] = metas_meta_l

        fig_prod_dual = go.Figure()

        fig_prod_dual.add_trace(go.Scatter(
            x=df_diario_prod['FECHA_STR'],
            y=df_diario_prod['META_MILLONES'],
            mode='lines+markers+text',
            name='META COALITION',
            text=[f"{m:,.1f}" for m in df_diario_prod['META_MILLONES']],
            textposition='top center',
            textfont=dict(size=13, color='#0F172A', family='Arial Black'),
            line=dict(color='#0F172A', width=3.5, shape='spline'),
            marker=dict(size=8, color='#0F172A'),
            fill='tozeroy',
            fillcolor='rgba(15, 23, 42, 0.08)'
        ))

        fig_prod_dual.add_trace(go.Scatter(
            x=df_diario_prod['FECHA_STR'],
            y=df_diario_prod['MILLONES'],
            mode='lines+markers+text',
            name='AVANCE COALITION',
            text=df_diario_prod['FMT_M'],
            textposition='top center',
            textfont=dict(size=13, color='#475569', family='Arial Black'),
            line=dict(color='#94A3B8', width=3.5, dash='dash', shape='spline'),
            marker=dict(size=8, color='#94A3B8')
        ))

        fig_prod_dual.update_layout(
            title="Curva Ejecutiva Diaria: Avance vs Meta de Producción (M S/)",
            xaxis_title="Fecha de Desembolso",
            yaxis_title="Millones de Soles (M S/)",
            height=500,
            template="plotly_white",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        st.plotly_chart(fig_prod_dual, use_container_width=True)
    else:
        st.info("No hay suficientes registros de desembolso diario para graficar la curva ejecutiva.")

    st.markdown("---")
    if not df_mensual.empty:
        fig_bar = px.bar(
            df_mensual, x='AÑO_MES_DESEMBOLSO', y='MONTO_TOTAL_NETO', text='MONTO_TOTAL_NETO',
            title="Evolución del Monto Neto Total Desembolsado por Mes (S/)",
            labels={'AÑO_MES_DESEMBOLSO': 'Periodo Desembolso', 'MONTO_TOTAL_NETO': 'Monto Total Neto (S/)'},
            color_discrete_sequence=['#0F172A']
        )
        fig_bar.update_traces(texttemplate='S/ %{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=450, xaxis_tickangle=-45, template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("📦 Control General de Remesas (Solicitudes)")
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

    if not df_rem_tab.empty:
        df_rem_mensual = df_rem_tab.groupby('AÑO_MES_SOLICITUD').size().reset_index(name='CANTIDAD_SOLICITUDES')
        df_rem_mensual = df_rem_mensual[df_rem_mensual['AÑO_MES_SOLICITUD'] != ''].sort_values('AÑO_MES_SOLICITUD')

        fig_rem_bar = px.bar(
            df_rem_mensual, x='AÑO_MES_SOLICITUD', y='CANTIDAD_SOLICITUDES', text='CANTIDAD_SOLICITUDES',
            title="Conteo de Remesas por Mes de Solicitud",
            labels={'AÑO_MES_SOLICITUD': 'Mes de Solicitud', 'CANTIDAD_SOLICITUDES': 'N° de Solicitudes'},
            color_discrete_sequence=['#0D9488']
        )
        fig_rem_bar.update_traces(texttemplate='%{text:,} Ops', textposition='outside')
        fig_rem_bar.update_layout(height=450, xaxis_tickangle=-45, template="plotly_white")
        st.plotly_chart(fig_rem_bar, use_container_width=True)

    st.markdown("---")

    col_r1, col_r2 = st.columns([2, 1])

    with col_r1:
        if not df_rem_tab.empty and df_rem_tab['FECHA_SOLICITUD_DT'].notna().any():
            df_diario_rem = df_rem_tab.groupby(df_rem_tab['FECHA_SOLICITUD_DT'].dt.date).size().reset_index(name='CANTIDAD')
            df_diario_rem = df_diario_rem.sort_values('FECHA_SOLICITUD_DT')
            df_diario_rem['FECHA_STR'] = pd.to_datetime(df_diario_rem['FECHA_SOLICITUD_DT']).dt.strftime('%d %b')

            fig_rem_line = go.Figure()
            fig_rem_line.add_trace(go.Scatter(
                x=df_diario_rem['FECHA_STR'],
                y=df_diario_rem['CANTIDAD'],
                mode='lines+markers+text',
                name='Remesas Diarias',
                text=df_diario_rem['CANTIDAD'],
                textposition='top center',
                textfont=dict(size=13, color='#16A34A', family='Arial Black'),
                line=dict(color='#16A34A', width=3.5, shape='spline'),
                marker=dict(size=9, color='#16A34A', line=dict(color='#FFFFFF', width=1.5)),
                fill='tozeroy',
                fillcolor='rgba(22, 163, 74, 0.12)'
            ))
            fig_rem_line.add_hline(
                y=90, 
                line_dash="dash", 
                line_color="#0F172A", 
                line_width=2.5,
                annotation_text="🎯 Meta Ejecutiva: 90 Ops", 
                annotation_position="top left",
                annotation=dict(font_size=12, font_color="#0F172A", bgcolor="#FEF3C7", borderpad=4)
            )
            fig_rem_line.update_layout(
                title="Curva de Ingreso de Remesas por Día (Tendencia Ejecutiva)",
                xaxis_title="Fecha de Solicitud", yaxis_title="N° de Operaciones",
                height=450, template="plotly_white", showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
            )
            st.plotly_chart(fig_rem_line, use_container_width=True)
        else:
            st.info("No hay suficientes datos diarios de remesas para graficar.")

    with col_r2:
        if not df_rem_tab.empty:
            df_est = df_rem_tab.groupby('ESTADO').size().reset_index(name='CANTIDAD')
            fig_pie_est = px.pie(
                df_est, names='ESTADO', values='CANTIDAD',
                title="Distribución de Estados", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie_est.update_traces(textinfo='value+percent')
            fig_pie_est.update_layout(height=450, template="plotly_white")
            st.plotly_chart(fig_pie_est, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Participación y Distribución de Remesas")

    p_col1, p_col2, p_col3 = st.columns(3)

    with p_col1:
        if not df_rem_tab.empty and 'TERRITORIAL' in df_rem_tab.columns:
            df_part_ter = df_rem_tab.groupby('TERRITORIAL').size().reset_index(name='CANTIDAD').sort_values('CANTIDAD', ascending=True)
            fig_ter = px.bar(df_part_ter, x='CANTIDAD', y='TERRITORIAL', orientation='h', title="Participación por Territorial", text_auto=',.0f', color_discrete_sequence=['#2563EB'])
            fig_ter.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_ter, use_container_width=True)

    with p_col2:
        if not df_rem_tab.empty and 'ZONA' in df_rem_tab.columns:
            df_part_zona = df_rem_tab.groupby('ZONA').size().reset_index(name='CANTIDAD').sort_values('CANTIDAD', ascending=True)
            fig_zona = px.bar(df_part_zona, x='CANTIDAD', y='ZONA', orientation='h', title="Participación por Zona", text_auto=',.0f', color_discrete_sequence=['#0D9488'])
            fig_zona.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_zona, use_container_width=True)

    with p_col3:
        if not df_rem_tab.empty and 'SUPERVISOR' in df_rem_tab.columns:
            df_part_sup = df_rem_tab.groupby('SUPERVISOR').size().reset_index(name='CANTIDAD').sort_values('CANTIDAD', ascending=True)
            fig_sup = px.bar(df_part_sup, x='CANTIDAD', y='SUPERVISOR', orientation='h', title="Participación por Supervisor", text_auto=',.0f', color_discrete_sequence=['#D97706'])
            fig_sup.update_layout(height=350, template="plotly_white")
            st.plotly_chart(fig_sup, use_container_width=True)

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

with tab4:
    st.subheader("🎯 Reporte de Venta, Remesas y Metas por Línea de Supervisión")
    
    if not df_flt_prod.empty and 'SUPERVISOR' in df_flt_prod.columns:
        df_prod_sup = df_flt_prod.groupby('SUPERVISOR').agg(
            OPERACIONES_DESEMBOLSA=('NETO', 'count'),
            MONTO_DESEMBOLSADO=('NETO', 'sum')
        ).reset_index()
    else:
        df_prod_sup = pd.DataFrame(columns=['SUPERVISOR', 'OPERACIONES_DESEMBOLSA', 'MONTO_DESEMBOLSADO'])

    if not df_remesas.empty and 'SUPERVISOR' in df_remesas.columns:
        df_rem_sup = df_remesas.groupby('SUPERVISOR').size().reset_index(name='REMESAS_INGRESADAS')
    else:
        df_rem_sup = pd.DataFrame(columns=['SUPERVISOR', 'REMESAS_INGRESADAS'])

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

    df_reporte = pd.merge(df_metas_flt, df_prod_sup, on='SUPERVISOR', how='left')
    df_reporte = pd.merge(df_reporte, df_rem_sup, on='SUPERVISOR', how='left')
    
    df_reporte['OPERACIONES_DESEMBOLSA'] = df_reporte['OPERACIONES_DESEMBOLSA'].fillna(0).astype(int)
    df_reporte['MONTO_DESEMBOLSADO'] = df_reporte['MONTO_DESEMBOLSADO'].fillna(0.0)
    df_reporte['REMESAS_INGRESADAS'] = df_reporte['REMESAS_INGRESADAS'].fillna(0).astype(int)

    df_reporte['% Cumplimiento Ops'] = np.where(
        df_reporte['META DE OPERACIONES'] > 0,
        (df_reporte['OPERACIONES_DESEMBOLSA'] / df_reporte['META DE OPERACIONES']) * 100,
        0.0
    )
    df_reporte['% Cumplimiento Monto'] = np.where(
        df_reporte['META DESEMBOLSO'] > 0,
        (df_reporte['MONTO_DESEMBOLSADO'] / df_reporte['META DESEMBOLSO']) * 100,
        0.0
    )

    df_reporte = df_reporte.sort_values(by=['% Cumplimiento Ops', '% Cumplimiento Monto'], ascending=[False, False]).reset_index(drop=True)

    if not df_reporte.empty:
        promedio_desembolsado = df_reporte['MONTO_DESEMBOLSADO'].mean()
        
        df_top_sup = df_reporte.sort_values('MONTO_DESEMBOLSADO', ascending=False).head(12).copy()
        df_top_sup['MONTO_MILLONES'] = df_top_sup['MONTO_DESEMBOLSADO'] / 1e6
        df_top_sup['FMT_TEXTO'] = df_top_sup['MONTO_MILLONES'].apply(lambda x: f"S/ {x:,.2f}M" if x >= 1 else f"S/ {x*1000:,.0f}k")
        df_top_sup = df_top_sup.sort_values('MONTO_DESEMBOLSADO', ascending=True)

        fig_bar_sup_monto = go.Figure()

        fig_bar_sup_monto.add_trace(go.Bar(
            x=df_top_sup['MONTO_DESEMBOLSADO'],
            y=df_top_sup['SUPERVISOR'],
            orientation='h',
            text=df_top_sup['FMT_TEXTO'],
            textposition='auto',
            textfont=dict(size=14, color='white', family='Arial Black'),
            marker=dict(color='#2563EB')
        ))

        fig_bar_sup_monto.add_vline(
            x=promedio_desembolsado,
            line_dash="dash",
            line_color="#EF4444",
            line_width=3,
            annotation_text=f"Promedio: S/ {promedio_desembolsado:,.2f}",
            annotation_position="top right",
            annotation=dict(font_size=12, font_color="#EF4444", font_family="Arial Black", bgcolor="#FEE2E2", borderpad=4)
        )

        fig_bar_sup_monto.update_layout(
            title="Top Mejores Supervisores por Monto Desembolsado (S/) vs Promedio General",
            xaxis_title="Monto Desembolsado (S/)",
            yaxis_title="Supervisor",
            height=480,
            template="plotly_white",
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
        st.plotly_chart(fig_bar_sup_monto, use_container_width=True)
        st.markdown("---")

    df_reporte_final = df_reporte[[
        'SUPERVISOR', 'ESTADO_SUP', 'PLAZA', 'JEFE ZONAL', 'TERRITORIAL',
        'META DE OPERACIONES', 'OPERACIONES_DESEMBOLSA', 'REMESAS_INGRESADAS', '% Cumplimiento Ops',
        'META DESEMBOLSO', 'MONTO_DESEMBOLSADO', '% Cumplimiento Monto'
    ]].rename(columns={
        'SUPERVISOR': 'Supervisor', 'ESTADO_SUP': 'Estado', 'PLAZA': 'Plaza / Zona',
        'JEFE ZONAL': 'Jefe Zonal', 'TERRITORIAL': 'Territorial',
        'META DE OPERACIONES': 'Meta de Operaciones', 'OPERACIONES_DESEMBOLSA': 'Ops Desembolsadas',
        'REMESAS_INGRESADAS': 'Remesas Ingresadas',
        '% Cumplimiento Ops': '% Cumplimiento Ops',
        'META DESEMBOLSO': 'Meta Desembolso (S/)', 'MONTO_DESEMBOLSADO': 'Monto Desembolsado (S/)',
        '% Cumplimiento Monto': '% Cumplimiento Monto'
    })

    if not df_reporte_final.empty:
        def color_semaforo(val):
            if val < 80.0:
                return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
            elif val < 100.0:
                return 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'
            else:
                return 'background-color: #DCFCE7; color: #166534; font-weight: bold;'

        styled_reporte = df_reporte_final.style.map(
            color_semaforo, subset=['% Cumplimiento Ops', '% Cumplimiento Monto']
        ).format({
            'Meta de Operaciones': '{:,.0f}',
            'Ops Desembolsadas': '{:,.0f}',
            'Remesas Ingresadas': '{:,.0f}',
            '% Cumplimiento Ops': '{:.0f}%',
            'Meta Desembolso (S/)': formato_compacto_limpio,
            'Monto Desembolsado (S/)': formato_compacto_limpio,
            '% Cumplimiento Monto': '{:.0f}%'
        })
        st.dataframe(styled_reporte, use_container_width=True)
    else:
        st.info("No hay datos para el reporte de supervisión con los filtros actuales.")

with tab5:
    st.subheader("🎲 Motor Estocástico Monte Carlo (100,000 Escenarios - Convenios Perú)")
    base_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].mean() if not df_mensual.empty else 28500000
    std_mensual_historica = df_mensual['MONTO_TOTAL_NETO'].std() if (not df_mensual.empty and len(df_mensual) > 1) else base_mensual_historica * 0.12

    factores_peru = {
        'Enero': 0.85, 'Febrero': 0.90, 'Marzo': 1.10, 'Abril': 1.00,
        'Mayo': 1.02, 'Junio': 1.08, 'Julio': 1.25, 'Agosto': 0.95,
        'Setiembre': 1.00, 'Octubre': 1.05, 'Noviembre': 1.20, 'Diciembre': 1.35
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
        title="Proyección Anual de Bandas Estacionales Perú - Convenios (S/)", markers=True,
        color_discrete_map={'Pesimista (P10)': '#EF4444', 'Base / Esperado (P50)': '#2563EB', 'Optimista (P90)': '#10B981'}
    )
    fig_mc.update_traces(mode='lines+markers+text', textposition='top center')
    fig_mc.data[0].text = df_res_mc['P10_FMT']
    fig_mc.data[1].text = df_res_mc['P50_FMT']
    fig_mc.data[2].text = df_res_mc['P90_FMT']
    fig_mc.update_layout(height=500, yaxis_title="Monto Proyectado (S/)", template="plotly_white")
    st.plotly_chart(fig_mc, use_container_width=True)

with tab6:
    st.subheader("👥 Dotación de Asesores (Personal Activo & Cruce de Desembolsos Ene-Oct)")
    
    if df_dotacion is not None and not df_dotacion.empty:
        df_dot_flt = df_dotacion.copy()
        
        # 1. Retirar columnas no deseadas: ss, q(cese), mes cese, filtro
        cols_a_retirar = ['SS', 'Q(CESE)', 'Q (CESE)', 'MES CESE', 'FILTRO']
        cols_mantener_dot = [c for c in df_dot_flt.columns if c.upper() not in cols_a_retirar]
        df_dot_flt = df_dot_flt[cols_mantener_dot].copy()

        # 2. Filtrar únicamente personal en estado ACTIVO
        cols_est = [c for c in df_dot_flt.columns if 'ESTADO' in c.upper()]
        if cols_est:
            df_dot_flt = df_dot_flt[df_dot_flt[cols_est[0]].astype(str).str.upper() == 'ACTIVO']

        # 3. Aplicar filtros del dashboard (Sidebar)
        cols_ter = [c for c in df_dot_flt.columns if 'TERRITORIAL' in c.upper()]
        if cols_ter:
            if territorial_asignada != "TODAS":
                df_dot_flt = df_dot_flt[df_dot_flt[cols_ter[0]] == territorial_asignada]
            elif sel_territorial != "TODOS":
                df_dot_flt = df_dot_flt[df_dot_flt[cols_ter[0]] == sel_territorial]

        cols_zona = [c for c in df_dot_flt.columns if 'ZONA' in c.upper()]
        if cols_zona and sel_zona != "TODAS":
            df_dot_flt = df_dot_flt[df_dot_flt[cols_zona[0]] == sel_zona]

        cols_plz = [c for c in df_dot_flt.columns if 'PLAZA' in c.upper()]
        if cols_plz and sel_plaza != "TODAS":
            df_dot_flt = df_dot_flt[df_dot_flt[cols_plz[0]] == sel_plaza]

        cols_jefe = [c for c in df_dot_flt.columns if 'JEFE' in c.upper()]
        if cols_jefe and sel_jefe != "TODOS":
            df_dot_flt = df_dot_flt[df_dot_flt[cols_jefe[0]] == sel_jefe]

        cols_sup = [c for c in df_dot_flt.columns if 'SUPERVISOR' in c.upper()]
        if cols_sup and sel_sup != "TODOS":
            df_dot_flt = df_dot_flt[df_dot_flt[cols_sup[0]] == sel_sup]

        cols_asesor = [c for c in df_dot_flt.columns if 'ASESOR' in c.upper()]
        if cols_asesor and sel_asesor != "TODOS":
            df_dot_flt = df_dot_flt[df_dot_flt[cols_asesor[0]] == sel_asesor]

        # 4. Cruzar con Hoja 1 por DNI para calcular montos netos por mes (Enero a Octubre) + Promedio
        if not df_dot_flt.empty and not df_base.empty:
            map_meses = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Setiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
            df_base_temp = df_base[df_base['ESTADO'] == 'DESEMBOLSADO'].copy()
            df_base_temp['MES_NUM'] = df_base_temp['FECHA_DESEMBOLSO_DT'].dt.month
            df_base_temp['MES_NOMBRE'] = df_base_temp['MES_NUM'].map(map_meses)

            # Pivot por DNI de Hoja 1
            df_pivot = df_base_temp.pivot_table(index='DNI_HOJA1', columns='MES_NOMBRE', values='NETO', aggfunc='sum', fill_value=0)

            meses_cols = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre']
            for m in meses_cols:
                if m not in df_pivot.columns:
                    df_pivot[m] = 0.0
            
            df_pivot = df_pivot[meses_cols].copy()
            df_pivot['Promedio'] = df_pivot[meses_cols].mean(axis=1)
            df_pivot = df_pivot.reset_index()

            cols_dni_dot = [c for c in df_dot_flt.columns if 'DNI' in c.upper()]
            if cols_dni_dot:
                col_dni_dot = cols_dni_dot[0]
                df_dot_flt = pd.merge(df_dot_flt, df_pivot, left_on=col_dni_dot, right_on='DNI_HOJA1', how='left')
                if 'DNI_HOJA1' in df_dot_flt.columns:
                    df_dot_flt = df_dot_flt.drop(columns=['DNI_HOJA1'])
                
                for m in meses_cols + ['Promedio']:
                    if m in df_dot_flt.columns:
                        df_dot_flt[m] = df_dot_flt[m].fillna(0.0)

        if not df_dot_flt.empty:
            st.markdown(f"**Total Personal Activo Filtrado:** `{len(df_dot_flt)}` colaboradores")
            
            # Formatear columnas monetarias para visualización
            cols_a_formatear = [c for c in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Promedio'] if c in df_dot_flt.columns]
            
            styled_dot = df_dot_flt.style.format({col: formato_compacto_limpio for col in cols_a_formatear})
            st.dataframe(styled_dot, use_container_width=True)
        else:
            st.info("No se encontraron colaboradores en estado ACTIVO que coincidan con la combinación de filtros seleccionados.")
    else:
        st.info("No se encontraron registros en la pestaña 'Dotación' del Google Sheets.")