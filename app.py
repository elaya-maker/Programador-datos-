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
        value=54.50,  # Valor referencial modificable por el usuario
        step=0.01,
        help="Tasa utilizada para convertir la pestaña 'EFECTIVO' (USD) a Bolívares y viceversa."
    )
    
    st.markdown("---")
    st.markdown("### 🧭 Navegación")
    if st.button("🔄 Conciliación y Consolidado", use_container_width=True):
        st.session_state.modulo_activo = "ConciliacionBancos"
        
    st.caption("JAC Motors Venezuela v2.1 (Entorno de Control Multimoneda)")

# --- MÓDULO PRINCIPAL: CONCILIACIÓN Y CONSOLIDADO DE BANCOS ---
if st.session_state.modulo_activo == "ConciliacionBancos":
    st.header("🔄 Auditoría, Conciliación y Consolidado de Bancos - GULF 2026")
    st.write("Cargue el archivo de movimientos para unificar las cuentas y estructurar la pestaña analítica bi-moneda.")
    
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
                # Omitir de la lectura hojas analíticas previas para evitar redundancias
                if any(x in nombre_hoja.upper() for x in ["CONSOLIDADO", "CONCILIACIÓN", "CONCILIACION"]):
                    continue
                
                # Carga de la estructura de datos correspondiente
                if excel_file is not None:
                    df_hoja = excel_file.parse(nombre_hoja)
                else:
                    archivo_gulf.seek(0)
                    df_hoja = pd.read_csv(archivo_gulf)
                
                diccionario_hojas_originales[nombre_hoja] = df_hoja.copy()
                
                # 1. Salto dinámico de banners superiores buscando la fila de encabezados reales
                skip_rows_index = 0
                for i in range(min(len(df_hoja), 6)):
                    linea_valores = df_hoja.iloc[i].astype(str).str.upper().tolist()
                    if any(any(k in str(cell) for k in ["FECHA", "DESCRIPCION", "CREDITO", "INGRESOS"]) for cell in linea_valores):
                        skip_rows_index = i + 1
                        if excel_file is not None:
                            df_hoja = excel_file.parse(nombre_hoja, skiprows=skip_rows_index)
                        break
                
                # Normalización estricta de nombres de columnas
                df_hoja.columns = [str(c).strip().upper() for c in df_hoja.columns]
                
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
                # Si la pestaña se llama 'EFECTIVO' (sin 'BS'), se procesa nativamente en USD y se calcula su equivalente en Bs.
                es_pestana_usd = any(x in nombre_hoja.upper() for x in ["USD", "CASH", "KTSU", "EFECTIVO"]) and "BS" not in nombre_hoja.upper()
                
                col_debito = [c for c in df_hoja.columns if any(k in c for k in ["DEBITO", "EGRESO", "EGRESOS"])]
                col_credito = [c for c in df_hoja.columns if any(k in c for k in ["CREDITO", "INGRESO", "INGRESOS"])]
                col_saldo = [c for c in df_hoja.columns if any(k in c for k in ["SALDO", "DISPONIBLE"])]
                
                # Casting y limpieza de valores numéricos nulos
                val_debito_orig = pd.to_numeric(df_hoja[col_debito[0]], errors='coerce').fillna(0.0) if col_debito else pd.Series(0.0, index=df_hoja.index)
                val_credito_orig = pd.to_numeric(df_hoja[col_credito[0]], errors='coerce').fillna(0.0) if col_credito else pd.Series(0.0, index=df_hoja.index)
                val_saldo_orig = pd.to_numeric(df_hoja[col_saldo[0]], errors='coerce').fillna(0.0) if col_saldo else pd.Series(0.0, index=df_hoja.index)
                
                if es_pestana_usd:
                    # 💵 Valores originales van a las columnas en Dólares
                    df_normalizado["DEBITO/EGRESO ($)"] = val_debito_orig
                    df_normalizado["CREDITO/INGRESO ($)"] = val_credito_orig
                    df_normalizado["SALDO ($)"] = val_saldo_orig
                    
                    # 🇻🇪 CONVERSIÓN CONCURRENTE A BS (Multiplicado por Tasa BCV)
                    df_normalizado["DEBITO/EGRESO (BS)"] = val_debito_orig * tasa_bcv
                    df_normalizado["CREDITO/INGRESO (BS)"] = val_credito_orig * tasa_bcv
                    df_normalizado["SALDO (BS)"] = val_saldo_orig * tasa_bcv
                else:
                    # 🇻🇪 Valores originales van a las columnas de Bolívares
                    df_normalizado["DEBITO/EGRESO (BS)"] = val_debito_orig
                    df_normalizado["CREDITO/INGRESO (BS)"] = val_credito_orig
                    df_normalizado["SALDO (BS)"] = val_saldo_orig
                    
                    # 💵 CONVERSIÓN CONCURRENTE A DÓLARES (Dividido entre Tasa BCV)
                    df_normalizado["DEBITO/EGRESO ($)"] = val_debito_orig / tasa_bcv
                    df_normalizado["CREDITO/INGRESO ($)"] = val_credito_orig / tasa_bcv
                    df_normalizado["SALDO ($)"] = val_saldo_orig / tasa_bcv

                # Validar tipos numéricos flotantes en bloques transaccionales
                for col_num in columnas_estructuradas[5:11]:
                    df_normalizado[col_num] = pd.to_numeric(df_normalizado[col_num], errors='coerce').fillna(0.0)
                
                # 3. Filtrado de registros vacíos o duplicaciones de cabeceras en el archivo
                df_normalizado = df_normalizado.dropna(subset=['FECHA', 'DESCRIPCION'], how='all')
                df_normalizado = df_normalizado[df_normalizado['DESCRIPCION'].astype(str).str.upper() != 'DESCRIPCION']
                df_normalizado = df_normalizado[df_normalizado['FECHA'].astype(str).str.strip() != ""]
                
                if not df_normalizado.empty:
                    lista_movimientos_consolidados.append(df_normalizado)
                    
                    # Extraer última fila para el reporte de Arqueo / Saldos finales
                    ultima_fila = df_normalizado.iloc[-1]
                    
                    resumen_bancos.append({
                        "Cuenta / Origen": nombre_hoja,
                        "Moneda Original": "USD ($)" if es_pestana_usd else "VES (Bs.)",
                        "Total Débitos (Bs)": float(df_normalizado["DEBITO/EGRESO (BS)"].sum()),
                        "Total Créditos (Bs)": float(df_normalizado["CREDITO/INGRESO (BS)"].sum()),
                        "Saldo Cierre (Bs)": float(ultima_fila["SALDO (BS)"]),
                        "Total Débitos ($)": float(df_normalizado["DEBITO/EGRESO ($)"].sum()),
                        "Total Créditos ($)": float(df_normalizado["CREDITO/INGRESO ($)"].sum()),
                        "Saldo Cierre ($)": float(ultima_fila["SALDO ($)"])
                    })
            
            # Consolidación final de la matriz única
            if lista_movimientos_consolidados:
                df_consolidado_final = pd.concat(lista_movimientos_consolidados, ignore_index=True)
                df_consolidado_final["FECHA"] = pd.to_datetime(df_consolidado_final["FECHA"], errors='coerce').dt.strftime('%Y-%m-%d').fillna("")
            else:
                df_consolidado_final = pd.DataFrame(columns=columnas_estructuradas)
                
            df_conciliacion_resumen = pd.DataFrame(resumen_bancos)
            
            # --- INTERFAZ VISUAL EN PANTALLA ---
            tab1, tab2 = st.tabs(["📋 MATRIZ INTEGRADA (Multimoneda)", "📊 CONTROL DE ARQUEO (Saldos de Cierre)"])
            
            with tab1:
                st.markdown("### 🏦 Matriz Integrada y Homologada de Movimientos (GULF 2026)")
                st.caption(f"La pestaña 'EFECTIVO' fue procesada originalmente como USD y multiplicada por la tasa BCV ({tasa_bcv} Bs/$).")
                st.dataframe(df_consolidado_final, use_container_width=True)
                
            with tab2:
                st.markdown("### ⚖️ Arqueo de Saldos y Cierres Consolidados")
                st.dataframe(df_conciliacion_resumen.style.format({
                    "Total Débitos (Bs)": "{:,.2f} Bs", "Total Créditos (Bs)": "{:,.2f} Bs", "Saldo Cierre (Bs)": "{:,.2f} Bs",
                    "Total Débitos ($)": "$ {:,.2f}", "Total Créditos ($)": "$ {:,.2f}", "Saldo Cierre ($)": "$ {:,.2f}"
                }), use_container_width=True)
                
            # --- GENERACIÓN DE EXCEL DE SALIDA MULTIPESTAÑA ---
            buffer_gulf_salida = io.BytesIO()
            with pd.ExcelWriter(buffer_gulf_salida, engine='openpyxl') as writer:
                df_consolidado_final.to_excel(writer, sheet_name='CONSOLIDADO', index=False)
                df_conciliacion_resumen.to_excel(writer, sheet_name='ARQUEO_RESUMEN', index=False)
                
                # Mantener los respaldos de los crudos de datos cargados originalmente
                for name, df_orig in diccionario_hojas_originales.items():
                    df_orig.to_excel(writer, sheet_name=name[:30], index=False)
                
                # Ajuste automático del ancho de las celdas en el reporte consolidado
                workbook = writer.book
                if 'CONSOLIDADO' in workbook.sheetnames:
                    worksheet = writer.sheets['CONSOLIDADO']
                    for col in worksheet.columns:
                        max_len = max(len(str(cell.value or '')) for cell in col)
                        col_letter = col[0].column_letter
                        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 11)
                        
            st.write("---")
            st.download_button(
                label="📥 Descargar Reporte Consolidado (Excel)",
                data=buffer_gulf_salida.getvalue(),
                file_name="DETALLES_MOV_GULF_2026_CONSOLIDADO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Ocurrió un error procesando las matrices del archivo: {e}")
            st.exception(e)
    else:
        st.info("💡 Por favor, suba el archivo de movimientos en la sección superior para ejecutar el análisis financiero.")
