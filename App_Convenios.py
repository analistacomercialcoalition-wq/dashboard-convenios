@st.cache_data(ttl=60)
def cargar_datos_corporativos():
    base_id = "1IBvyIN5H1jYrwEAOD9E5nTCpaBLqxD109HMKCW0Ezt8"
    
    # 1. Matriz Principal de Operaciones (Hoja 1)
    sheet_url_hoja1 = f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet=Hoja%201"
    df = pd.read_csv(sheet_url_hoja1, dtype=str)
    df.columns = df.columns.astype(str).str.strip()
    
    # Limpieza de NETO
    df['NETO'] = pd.to_numeric(
        df['NETO'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace(' ', '').str.strip(), 
        errors='coerce'
    ).fillna(0)

    # Limpieza de textos
    cols_a_limpiar = ['TERRITORIAL', 'ZONA', 'PLAZA', 'JEFE ZONAL', 'SUPERVISOR', 'ASESOR CORRECTO', 'ESTADO']
    for col in cols_a_limpiar:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip().str.upper()

    # Parseo de Fecha de Solicitud
    col_sol = [c for c in df.columns if 'SOLICITUD' in c.upper()][0]
    df['FECHA_SOLICITUD_DT'] = pd.to_datetime(df[col_sol], format='%d/%m/%Y', errors='coerce')
    mask_null_sol = df['FECHA_SOLICITUD_DT'].isna() & (df[col_sol] != '')
    if mask_null_sol.any():
        df.loc[mask_null_sol, 'FECHA_SOLICITUD_DT'] = pd.to_datetime(
            df.loc[mask_null_sol, col_sol], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_SOLICITUD'] = df['FECHA_SOLICITUD_DT'].dt.to_period('M').astype(str)

    # Parseo de Fecha de Desembolso
    col_des = [c for c in df.columns if 'DESEMBOLSO' in c.upper()][0]
    df['FECHA_DESEMBOLSO_DT'] = pd.to_datetime(df[col_des], format='%d/%m/%Y', errors='coerce')
    mask_null_des = df['FECHA_DESEMBOLSO_DT'].isna() & (df[col_des] != '')
    if mask_null_des.any():
        df.loc[mask_null_des, 'FECHA_DESEMBOLSO_DT'] = pd.to_datetime(
            df.loc[mask_null_des, col_des], dayfirst=True, errors='coerce'
        )
    df['AÑO_MES_DESEMBOLSO'] = df['FECHA_DESEMBOLSO_DT'].dt.to_period('M').astype(str)
    df['MES_DESEMBOLSO_NUM'] = df['FECHA_DESEMBOLSO_DT'].dt.month

    df = df[df['FECHA_SOLICITUD_DT'].notna()]
    
    cols_id = [c for c in df.columns if any(k in c.upper() for k in ['EXPEDIE', 'DNI', 'CREDITO', 'OPERACION'])]
    df['ID_UNICO'] = df[cols_id[0]].astype(str).str.strip() if cols_id else df.index.astype(str)
    df = df.drop_duplicates(subset=['ID_UNICO', 'AÑO_MES_SOLICITUD'], keep='first')

    # TABLA OFICIAL DE METAS POR SUPERVISOR
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

    # 3. LECTURA PROTEGIDA DE DOTACIÓN
    df_dotacion = pd.DataFrame()
    posibles_urls = [
        f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet=DOTACION",
        f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet=DOTACI%C3%93N"
    ]

    for url in posibles_urls:
        try:
            df_temp = pd.read_csv(url, dtype=str)
            if df_temp is not None and not df_temp.empty and len(df_temp.columns) > 1:
                df_dotacion = df_temp.copy()
                break
        except Exception:
            continue

    # BLINDAJE ESTRICTO CONTRA DATOS VACÍOS
    if df_dotacion is not None and not df_dotacion.empty:
        df_dotacion.columns = df_dotacion.columns.astype(str).str.strip()
        for col in df_dotacion.columns:
            df_dotacion[col] = df_dotacion[col].astype(str).replace(['nan', 'None', 'NAT', 'NaN'], '').str.strip().str.upper()
    else:
        df_dotacion = pd.DataFrame(columns=['DNI', 'PROMOTOR', 'ESTADO', 'SUPERVISOR', 'JEFE ZONAL', 'PLAZA'])

    return df, df_metas_oficial, df_dotacion