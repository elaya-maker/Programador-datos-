import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="JAC Venezuela - Control GULF 2026",
    page_icon="📊",
    layout="wide"
)

# --- CONFIGURACIÓN DE ESTILOS VISUALES (CSS) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; color: #007bff; }
    .stTabs [data-baseweb="tab"] { font-weight: bold; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DEL ESTADO DE LA APLICACIÓN ---
if "modulo_activo" not in st.session_state:
    st.session_state.modulo_activo = "ConciliacionBancos"

# --- BARRA LATERAL (CONTROLES GLOBALES Y TASAS) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/JAC_Motors_logo.svg", width=120)
    st.title("Control Financiero 2026")
    st.markdown("---")
    
    # Input de la tasa del BCV usada para las conversiones automáticas
    tasa_bcv = st.number_input(
        "💱 Tasa de Cambio Oficial (BCV):",
        min_value=1.0,
        value=54.50,  # Modificable dinámicamente
        step=0.01,
        help="Tasa oficial para convertir la pestaña 'EFECTIVO' (USD) a Bolívares y viceversa."
    )
    
    st.markdown("---")
    st.markdown("### 🧭 Navegación")
    if st.button("🔄 Conciliación y Consolidado", use_container_width=True):
        st.session_state.modulo_activo = "ConciliacionBancos"
        
    st.caption("JAC Motors Venezuela v2.2 (Entorno Homologado Multi-moneda)")

# --- MÓDULO PRINCIPAL: CONCILIACIÓN Y CONSOLIDADO DE BANCOS ---
if st.session_state.modulo_activo == "ConciliacionBancos":
    st.header("🔄 Auditoría, Conciliación y Consolidado de Bancos - GULF 2026")
    st.write("Cargue el archivo de movimientos de Windows para agrupar las cuentas y estructurar la pestaña analítica unificada.")
    
    archivo_gulf = st.file_uploader(
        "Cargar archivo de movimientos bancarios (DETALLES MOV GULF 2026)", 
        type=["xlsx", "xls", "csv"]
    )
    
    if archivo_gulf is not None:
        try:
            # Manejo flexible por si suben un archivo CSV plano o el libro de Excel
            if archivo_gulf.name.endswith('.csv'):
                pestanas = [archivo_gulf.name.split('.')[0]]
                excel_file = None
            else:
                excel_file = pd.ExcelFile(archivo_gulf)
                pestanas = excel_file.sheet_names
                
            st.success(f"✅ Archivo leído correctamente. Se detectaron {len(pestanas)} fuentes/pestañas de información.")
            
            # Estructura homologada del Modelo unificado de datos VEN-NIF
            columnas_estructuradas = [
                "ORIGEN_PESTANA", "FECHA", "REFERENCIA/CONCEPTO", "DESCRIPCION", 
                "CLASIFICACION INTERNA", "DEBITO/EGRESO (BS)", "CREDITO/INGRESO (BS)", 
                "SALDO (BS)", "DEBITO/EGRESO ($)", "CREDITO/INGRESO ($)", "SALDO ($)", "TASA DE CAMBIO"
            ]
            
            lista_movimientos_consolidados = []
            diccionario_hojas_originales = {}
            resumen_bancos = []
            
            for nombre_hoja in pestanas:
                # Omitir de la lectura hojas analíticas previas o generadas
                if any(x in nombre_hoja.upper() for x in ["CONSOLIDADO", "CONCILIACIÓN", "CONCILIACION", "ARQUEO"]):
                    continue
                
                # Carga de la estructura de datos correspondiente
                if excel_file is not None:
                    df_hoja = excel_file.parse(nombre_hoja)
                else:
                    archivo_gulf.seek(0)
                    df_hoja = pd.read_csv(archivo_gulf)
                
                diccionario_hojas_originales[nombre_hoja] = df_hoja.copy()
                
                # 1. Eliminar columnas completamente vacías/fantasmas ("Unnamed:") al inicio
                df_hoja = df_hoja.loc[:, ~df_hoja.columns.str.contains('^Unnamed:', case=False, na=True)]
                
                # Salto dinámico de banners superiores buscando la fila de encabezados reales
                skip_rows_index = 0
                for i in range(min(len(df_hoja), 6)):
                    linea_valores = df_hoja.iloc[i].astype(str).str.upper().tolist()
                    if any(any(k in str(cell) for k in ["FECHA", "DESCRIPCION", "CREDITO", "INGRESOS", "EGRESOS"]) for cell in linea_valores):
                        skip_rows_index = i + 1
                        if excel_file is not None:
                            df_hoja = excel_file.parse(nombre_hoja, skiprows=skip_rows_index)
                        break
                
                # Normalización estricta de nombres de columnas (Quitar espacios y pasar a mayúsculas)
                df_hoja.columns = [str(c).strip().upper() for c in df_hoja.columns]
                # Eliminar columnas sin nombre después del re-parse
                df_hoja = df_hoja.loc[:, ~df_hoja.columns.str.contains('^UNNAMED', case=False, na=True)]
                
                if df_hoja.empty or len(df_hoja.columns) < 2:
                    continue
                
                # 2. Inicializar la plantilla de salida limpia para la pestaña actual
                df_normalizado = pd.DataFrame(index=range(len(df_hoja)), columns=columnas_estructuradas)
                df_normalizado["ORIGEN_PESTANA"] = nombre_hoja
                df_normalizado["TASA DE CAMBIO"] = tasa_bcv
                
                # --- MAPEO DE TEXTOS E IDENTIFICADORES ---
                col_fecha = [c for c in df_hoja.columns if "FECHA" in c]
                if col_fecha: df_normalizado["FECHA"] = df_hoja[col_fecha[0]]
                
                col_ref = [c for c in df_hoja.columns if any(k in c for k in ["REFERENCIA", "CONCEPTO", "CODIGO"])]
                if col_ref: df_normalizado["REFERENCIA/CONCEPTO"] = df_hoja[col_ref[0]]
                
                col_desc = [c for c in df_hoja.columns if "DESCRIPCION" in c]
                if col_desc: df_normalizado["DESCRIPCION"] = df_hoja[col_desc[0]]
                
                col_clas = [c for c in df_hoja.columns if any(k in c for k in ["COLUMNA1", "CLASIFICACION"])]
                if col_clas: df_normalizado["CLASIFICACION INTERNA"] = df_hoja[col_clas[0]]
                
                # --- REGLA LÓGICA CORE: CONTROL DE MONEDA (EFECTIVO USD vs BOLÍVARES) ---
                # Identifica si es la pestaña analítica de divisas en efectivo
                es_pestana_usd = any(x in nombre_hoja.upper() for x in ["USD", "CASH", "KTSU", "EFECTIVO"]) and "BS" not in nombre_hoja.upper()
                
                # Identificación inteligente y unificada de flujos monetarios (Soporta Bancos y Efectivo)
                col_debito = [c for c in df_hoja.columns if any(k in c for k in ["DEBITO", "EGRESO", "EGRESOS"])]
                col_credito = [c for c in df_hoja.columns if any(k in c for k in ["CREDITO", "INGRESO", "INGRESOS"])]
                col_saldo = [c for c in df_hoja.columns if any(k in c for k in ["SALDO", "DISPONIBLE"])]
                
                # Extraer series y forzar casteo numérico seguro limpiando strings o nulos
                val_debito_orig = pd.to_numeric(df_hoja[col_debito[0]], errors='coerce').fillna(0.0) if col_debito else pd.Series(0.0, index=df_hoja.index)
                val_credito_orig = pd.to_numeric(df_hoja[col_credito[0]], errors='coerce').fillna(0.0) if col_credito else pd.Series(0.0, index=df_hoja.index)
                val_saldo_orig = pd.to_numeric(df_hoja[col_saldo[0]], errors='coerce').fillna(0.0) if col_saldo else pd.Series(0.0, index=df_hoja.index)
                
                if es_pestana_usd:
                    # 💵 Valores originales de "Efectivo" van directamente a las columnas de Dólares ($)
                    df_normalizado["DEBITO/EGRESO ($)"] = val_debito_orig
                    df_normalizado["CREDITO/INGRESO ($)"] = val_credito_orig
                    df_normalizado["SALDO ($)"] = val_saldo_orig
                    
                    # 🇻🇪 CONVERSIÓN CONCURRENTE A BOLÍVARES (Multiplicado por la tasa BCV de la barra lateral)
                    df_normalizado["DEBITO/EGRESO (BS)"] = val_debito_orig * tasa_bcv
                    df_normalizado["CREDITO/INGRESO (BS)"] = val_credito_orig * tasa_bcv
                    df_normalizado["SALDO (BS)"] = val_saldo_orig * tasa_bcv
                else:
                    # 🇻🇪 Valores de cuentas en Bolívares nativos van a sus respectivas columnas
