import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Librerías para procesamiento de archivos externos
import pypdf
import docx

# ==============================================================================
# ⚙️ CONFIGURACIÓN DE LA PÁGINA Y ESTADOS DE SESIÓN
# ==============================================================================
st.set_page_config(
    page_title="Portal de Herramientas Contables - Empresa JAC Venezuela", 
    layout="wide", 
    page_icon="🇻🇪"
)

# Inicializar el estado de la sesión para el Libro Mayor Auxiliar
if 'contabilidad' not in st.session_state:
    st.session_state.contabilidad = pd.DataFrame(columns=[
        "ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", 
        "Debe_Bs", "Haber_Bs", "Debe_USD", "Haber_USD", "Tasa"
    ])

# Inicializar el estado para el control de navegación interna del portal
if 'modulo_activo' not in st.session_state:
    st.session_state.modulo_activo = "Portal Principal"

# ==============================================================================
# 📜 MARCO REGULATORIO VENEZOLANO Y CONTROLES (BARRA LATERAL)
# ==============================================================================
st.sidebar.markdown("### 📜 Marco Regulatorio (VEN-NIF)")
st.sidebar.caption(
    "Esta herramienta tecnológica opera bajo los lineamientos de las **BA VEN-NIF** "
    "(Federación de Colegios de Contadores Públicos de Venezuela), el **Código de Comercio** "
    "(Arts. 32 al 44 sobre la obligatoriedad de llevar los libros contables) y las normativas "
    "vigentes de facturación y retenciones dictadas por el **SENIAT**. "
    "Soporta registros bimonetarios concurrentes según el Convenio Cambiario N° 1 del BCV."
)
st.sidebar.write("---")

# Control de Tasa Oficial según regulaciones cambiarias del Banco Central de Venezuela
tasa_bcv = st.sidebar.number_input(
    "Tasa Oficial BCV del día (Bs/$)", 
    min_value=1.0, 
    value=60.0, 
    step=0.01, 
    format="%.2f"
)

# Catálogo de Cuentas Estandarizado (Matriz de Control Contable)
CATALOGO_CUENTAS = {
    "1.1.01.01": "Efectivo en Caja y Bancos (Bs)",
    "1.1.01.02": "Efectivo en Caja y Bancos ($)",
    "1.1.02.01": "Cuentas por Cobrar Comerciales",
    "1.1.03.01": "Inventario de Mercancías (VEN-NIF 2)",
    "1.2.01.01": "Propiedad, Planta y Equipo",
    "2.1.01.01": "Cuentas por Pagar Comerciales",
    "2.1.02.01": "Impuestos por Pagar (IVA/ISLR/IGTF)",
    "3.1.01.01": "Capital Social (Histórico)",
    "3.1.02.01": "Resultados Acumulados",
    "4.1.01.01": "Ingresos por Ventas",
    "5.1.01.01": "Costos de Ventas",
    "5.2.01.01": "Gastos de Personal (Nómina LOTTT)",
    "5.2.01.02": "Gastos de Alquiler y Servicios"
}

# ==============================================================================
# 🏢 DISEÑO INTERACTIVO DEL PORTAL DE ENTRADA (BANNER CORPORATIVO)
# ==============================================================================
st.markdown("""
<div style="background-color: #000000; padding: 25px; border-radius: 12px; margin-bottom: 25px; border-left: 8px solid #ff0000; box-shadow: 0 4px 10px rgba(0,0,0,0.15); display: flex; align-items: center;">
    <div style="margin-right: 25px; border-right: 2px solid #333; padding-right: 25px;">
        <span style="font-family: 'Arial Black', Gadget, sans-serif; font-size: 42px; font-weight: 900; color: #FFFFFF; letter-spacing: -3px; font-style: italic;">JAC</span>
    </div>
    <div>
        <h1 style="margin: 0; color: #FFFFFF; font-size: 30px; font-weight: bold; font-family: sans-serif;">Empresa JAC Venezuela</h1>
        <p style="margin: 4px 0 0 0; color: #aaaaaa; font-size: 14px; letter-spacing: 0.5px;">CONSORCIO AUTOMOTRIZ · SISTEMA DE CONTROL DE HERRAMIENTAS CONTABLES</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Habilitar botón de retorno si el usuario está operando dentro de algún módulo operativo
if st.session_state.modulo_activo != "Portal Principal":
    if st.button("⬅️ Volver al Menú Principal (JAC Venezuela)", use_container_width=False):
        st.session_state.modulo_activo = "Portal Principal"
        st.rerun()

# ==============================================================================
# 🏛️ MENÚ DE DISTRIBUCIÓN GENERAL DE MÓDULOS (PANTALLA HOME)
# ==============================================================================
if st.session_state.modulo_activo == "Portal Principal":
    st.markdown("### 🏛️ Distribución General de Módulos")
    st.write("Seleccione la dimensión operativa contable o fiscal que desea ejecutar en este momento:")
    st.write("")
    
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    
    with cat_col1:
        st.markdown("#### 📊 Análisis y Conciliación")
        if st.button("📈 Dashboard Analítico Empresarial", use_container_width=True):
            st.session_state.modulo_activo = "Dashboard"
            st.rerun()
        if st.button("📝 Módulo: Asentar Diario (Input / Archivos)", use_container_width=True):
            st.session_state.modulo_activo = "Asentar"
            st.rerun()
        if st.button("🔄 Conciliación y Consolidado de Bancos", use_container_width=True):
            st.session_state.modulo_activo = "ConciliacionBancos"
            st.rerun()
        st.button("⚙️ Distribución de Gastos (Próximamente)", use_container_width=True, disabled=True)
        
    with cat_col2:
        st.markdown("#### 📋 Cierres Mensuales")
        if st.button("📖 Ver Libro Diario General", use_container_width=True):
            st.session_state.modulo_activo = "Diario"
            st.rerun()
        if st.button("🗂️ Ver Libro Mayor Analítico", use_container_width=True):
            st.session_state.modulo_activo = "Mayor"
            st.rerun()
        if st.button("⚖️ Balance de Comprobación", use_container_width=True):
            st.session_state.modulo_activo = "Comprobacion"
            st.rerun()
            
    with cat_col3:
        st.markdown("#### ⚙️ Procesos Fiscales")
        if st.button("📋 Estado de Situación Financiera (VEN-NIF)", use_container_width=True):
            st.session_state.modulo_activo = "Situacion"
            st.rerun()
        st.button("🧮 Cálculo Pensiones (9%) / LOCTI (Próximamente)", use_container_width=True, disabled=True)
        st.button("🔍 Verificación Débito Fiscal / Retenciones (Próximamente)", use_container_width=True, disabled=True)

# Selector de navegación de respaldo rápido en la barra lateral
menu = st.sidebar.selectbox("Navegación Rápida", [
    "Ir al Portal Principal",
    "0. Dashboard Interactividad Empresarial",
    "1. Asentar Diario (Input)",
    "2. Conciliación y Consolidado Bancario",
    "3. Libro Diario General",
    "4. Libro Mayor Analítico",
    "5. Balance de Comprobación",
    "6. Estado de Situación Financiera"
], index=0)

if menu == "0. Dashboard Interactividad Empresarial":
    st.session_state.modulo_activo = "Dashboard"
elif menu == "1. Asentar Diario (Input)":
    st.session_state.modulo_activo = "Asentar"
elif menu == "2. Conciliación y Consolidado Bancario":
    st.session_state.modulo_activo = "ConciliacionBancos"
elif menu == "3. Libro Diario General":
    st.session_state.modulo_activo = "Diario"
elif menu == "4. Libro Mayor Analítico":
    st.session_state.modulo_activo = "Mayor"
elif menu == "5. Balance de Comprobación":
    st.session_state.modulo_activo = "Comprobacion"
elif menu == "6. Estado de Situación Financiera":
    st.session_state.modulo_activo = "Situacion"

# ==============================================================================
# ENRUTAMIENTO DINÁMICO DE MÓDULOS OPERATIVOS
# ==============================================================================

# --- MÓDULO: CONCILIACIÓN Y CONSOLIDADO DE BANCOS (DETALLES MOV GULF 2026) ---
if st.session_state.modulo_activo == "ConciliacionBancos":
    st.header("🔄 Auditoría, Conciliación y Consolidado de Bancos - GULF 2026")
    st.write("Cargue el archivo de movimientos de Windows para agrupar las cuentas y estructurar la pestaña analítica unificada.")
    
    archivo_gulf = st.file_uploader(
        "Cargar archivo de movimientos bancarios (DETALLES MOV GULF 2026)", 
        type=["xlsx", "xls"]
    )
    
    if archivo_gulf is not None:
        try:
            excel_file = pd.ExcelFile(archivo_gulf)
            pestanas = excel_file.sheet_names
            st.success(f"✅ Archivo leído correctamente. Se detectaron {len(pestanas)} pestañas originales.")
            
            # Definición estricta de las columnas solicitadas basadas en la estructura contable
            columnas_estructuradas = [
                "BANCOS/CAJA", "FECHA", "REFERENCIA", "DESCRIPCION BANCO", 
                "Columna1", "DEBITO", "CREDITO", "SALDO", "TASA", 
                "DEBITO $", "CREDITO $", "SALDO $"
            ]
            
            lista_movimientos_consolidados = []
            diccionario_hojas_originales = {}
            resumen_bancos = []
            
            for nombre_hoja in pestanas:
                if nombre_hoja in ["Consolidado", "Conciliación"]:
                    continue
                    
                df_hoja = excel_file.parse(nombre_hoja)
                diccionario_hojas_originales[nombre_hoja] = df_hoja.copy()
                
                # Normalizar nombres de columnas (quitar espacios y pasar a mayúsculas para un mapeo robusto)
                df_hoja.columns = [str(c).strip().upper() for c in df_hoja.columns]
                
                df_normalizado = pd.DataFrame(columns=columnas_estructuradas)
                
                # Mapear columnas dinámicamente tolerando ligeras variaciones del archivo de Windows
                for col in columnas_estructuradas:
                    col_key = col.upper()
                    if col_key in df_hoja.columns:
                        df_normalizado[col] = df_hoja[col_key]
                    elif col == "BANCOS/CAJA":
                        df_normalizado[col] = nombre_hoja
                    else:
                        if any(x in col for x in ["SALDO", "TASA", "DEBITO", "CREDITO"]):
                            df_normalizado[col] = 0.0
                        else:
                            df_normalizado[col] = ""
                
                # Asegurar tipos numéricos en columnas críticas de flujos de dinero
                columnas_monetarias = ["DEBITO", "CREDITO", "DEBITO $", "CREDITO $", "SALDO", "SALDO $", "TASA"]
                for c_num in columnas_monetarias:
                    if c_num in df_normalizado.columns:
                        df_normalizado[c_num] = pd.to_numeric(df_normalizado[c_num], errors='coerce').fillna(0.0)
                
                # Tratamiento cronológico de las fechas para cálculos secuenciales correctos
                if "FECHA" in df_normalizado.columns:
                    df_normalizado["FECHA"] = pd.to_datetime(df_normalizado["FECHA"], errors='coerce')
                    df_normalizado = df_normalizado.sort_values(by="FECHA").reset_index(drop=True)
                
                # --- ALGORITMO CORREGIDO: CÓMPUTO DE SALDO SECUENCIAL CONTABLE ---
                saldo_acumulado_bs = 0.0
                saldo_acumulado_usd = 0.0
                
                for idx in range(len(df_normalizado)):
                    debito_bs = df_normalizado.at[idx, "DEBITO"]
                    credito_bs = df_normalizado.at[idx, "CREDITO"]
                    debito_usd = df_normalizado.at[idx, "DEBITO $"]
                    credito_usd = df_normalizado.at[idx, "CREDITO $"]
                    
                    # Saldo = Saldo Anterior + Débitos (Aumentos) - Créditos (Disminuciones)
                    saldo_acumulado_bs += (debito_bs - credito_bs)
                    saldo_acumulado_usd += (debito_usd - credito_usd)
                    
                    df_normalizado.at[idx, "SALDO"] = saldo_acumulado_bs
                    df_normalizado.at[idx, "SALDO $"] = saldo_acumulado_usd
                
                # Formatear columna FECHA de vuelta a string limpio para visualización
                df_normalizado["FECHA"] = df_normalizado["FECHA"].dt.strftime('%Y-%m-%d').fillna("")
                
                lista_movimientos_consolidados.append(df_normalizado)
                
                # Obtener el saldo final real remanente del ciclo analizado
                final_bs = saldo_acumulado_bs
                final_usd = saldo_acumulado_usd
                
                resumen_bancos.append({
                    "Banco / Cuenta": nombre_hoja,
                    "Total Débitos (Bs)": float(df_normalizado["DEBITO"].sum()),
                    "Total Créditos (Bs)": float(df_normalizado["CREDITO"].sum()),
                    "Saldo Final Real (Bs)": final_bs,
                    "Total Débitos ($)": float(df_normalizado["DEBITO $"].sum()),
                    "Total Créditos ($)": float(df_normalizado["CREDITO $"].sum()),
                    "Saldo Final Real ($)": final_usd
                })
            
            df_consolidado_final = pd.concat(lista_movimientos_consolidados, ignore_index=True) if lista_movimientos_consolidados else pd.DataFrame(columns=columnas_estructuradas)
            df_conciliacion_resumen = pd.DataFrame(resumen_bancos)
            
            # Distribución por pestañas visuales de control
            tab1, tab2 = st.tabs(["📋 Nueva Hoja: Consolidado (Estructurado)", "📊 Nueva Hoja: Conciliación / Métricas"])
            
            with tab1:
                st.markdown("### Estructura de Columnas Unificadas por Banco")
                st.dataframe(df_consolidado_final, use_container_width=True)
                
            with tab2:
                st.markdown("### Resumen de Saldos de Auditoría de Cuentas")
                st.dataframe(df_conciliacion_resumen, use_container_width=True)
                
            # Compilación del libro Excel usando openpyxl
            buffer_gulf_salida = io.BytesIO()
            with pd.ExcelWriter(buffer_gulf_salida, engine='openpyxl') as writer:
                for name, df_orig in diccionario_hojas_originales.items():
                    df_orig.to_excel(writer, sheet_name=name, index=False)
                
                df_consolidado_final.to_excel(writer, sheet_name='Consolidado', index=False)
                df_conciliacion_resumen.to_excel(writer, sheet_name='Conciliación', index=False)
                
            st.write("---")
            st.download_button(
                label="📥 Descargar Excel con Hojas 'Consolidado' y 'Conciliación' Añadidas",
                data=buffer_gulf_salida.getvalue(),
                file_name="DETALLES_MOV_GULF_2026_PROCESADO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Error procesando la estructura del archivo bancario: {e}")
    else:
        st.info("💡 Suba el archivo de Excel en el control superior para generar las nuevas estructuras.")

# --- MÓDULO: DASHBOARD INTERACTIVO ---
elif st.session_state.modulo_activo == "Dashboard":
    st.header("📈 Dashboard Analítico de Rendimiento - JAC Venezuela")
    df_dashboard = st.session_state.contabilidad.copy()
    
    if df_dashboard.empty:
        st.info("📊 El dashboard se estructurará automáticamente cuando registre movimientos en el Libro Diario.")
    else:
        moneda_dash = st.radio("Expresar analíticas del Dashboard en:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        
        df_dashboard["Clasificacion"] = df_dashboard["Código Cuenta"].apply(
            lambda x: "Ingreso" if str(x).startswith("4") else ("Gasto" if str(x).startswith("5") else "Otro")
        )
        df_res = df_dashboard[df_dashboard["Clasificacion"].isin(["Ingreso", "Gasto"])].copy()
        
        if df_res.empty:
            st.warning("⚠️ No se registran asientos en cuentas de Ingresos (4) o Gastos (5) en el Diario.")
        else:
            if moneda_dash == "Bolívares (Bs)":
                df_res["Monto_Final"] = df_res.apply(lambda r: r["Haber_Bs"] if r["Clasificacion"] == "Ingreso" else r["Debe_Bs"], axis=1)
                simbolo = "Bs"
            else:
                df_res["Monto_Final"] = df_res.apply(lambda r: r["Haber_USD"] if r["Clasificacion"] == "Ingreso" else r["Debe_USD"], axis=1)
                simbolo = "$"
                
            total_ingresos = df_res[df_res["Clasificacion"] == "Ingreso"]["Monto_Final"].sum()
            total_gastos = df_res[df_res["Clasificacion"] == "Gasto"]["Monto_Final"].sum()
            utilidad_neta = total_ingresos - total_gastos
            
            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Total Ingresos Operativos", f"{simbolo} {total_ingresos:,.2f}")
            kpi2.metric("Total Gastos y Costos", f"{simbolo} {total_gastos:,.2f}", delta=f"-{simbolo} {total_gastos:,.2f}", delta_color="inverse")
            kpi3.metric("Utilidad Neta (VEN-NIF)", f"{simbolo} {utilidad_neta:,.2f}", delta="Superávit" if utilidad_neta >= 0 else "Déficit", delta_color="normal" if utilidad_neta >= 0 else "inverse")

# --- MÓDULO: ASENTAR DIARIO CONTABLE ---
elif st.session_state.modulo_activo == "Asentar":
    st.header("📝 Registro de Asientos Contables (Partida Doble) - JAC Venezuela")
    st.markdown("### 📥 Asistente de Importación Inteligente (Excel, PDF, Word)")
    
    archivo_importado = st.file_uploader(
        "Arrastre aquí su archivo desde Windows", 
        type=["xlsx", "xls", "csv", "pdf", "docx"],
        key="asentar_uploader"
    )
    
    glosa_sugerida, monto_sugerido = "", 0.0
    
    if archivo_importado is not None:
        nombre_archivo = archivo_importado.name
        if nombre_archivo.endswith(('.xlsx', '.xls', '.csv')):
            try:
                df_ext = pd.read_csv(archivo_importado) if nombre_archivo.endswith('.csv') else pd.read_excel(archivo_importado)
                st.dataframe(df_ext.head(3), use_container_width=True)
                columnas_numericas = df_ext.select_dtypes(include=['number']).columns
                if len(columnas_numericas) > 0:
                    monto_sugerido = float(df_ext[columnas_numericas[0]].iloc[0])
                glosa_sugerida = f"Importación de datos desde archivo: {nombre_archivo}"
                st.success("✅ Archivo tabular procesado.")
            except Exception as e:
                st.error(f"Error leyendo archivo tabular: {e}")
                
        elif nombre_archivo.endswith('.pdf'):
            try:
                lector_pdf = pypdf.PdfReader(archivo_importado)
                texto_extraido = "".join([p.extract_text() for p in lector_pdf.pages])
                st.text_area("Contenido del PDF (Vista previa)", texto_extraido[:1000], height=120)
                glosa_sugerida = f"Gasto s/ Factura PDF: {nombre_archivo}"
                st.success("✅ PDF procesado con éxito.")
            except Exception as e:
                st.error(f"Error procesando el PDF: {e}")

    st.markdown("---")
    siguiente_asiento = int(st.session_state.contabilidad["ID_Asiento"].max()) + 1 if not st.session_state.contabilidad.empty else 1
    st.subheader(f"Comprobante de Diario N° {siguiente_asiento}")
    
    with st.form("form_asiento", clear_on_submit=True):
        fecha_asiento = st.date_input("Fecha de Registro Legal", datetime.now())
        glosa_general = st.text_input("Concepto / Glosa del Asiento", value=glosa_sugerida)
        
        st.markdown("##### **Renglón 1: Cuenta de Cargo (DEBE)**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            cuenta_debe_cod = st.selectbox("Seleccione Cuenta Deudora", list(CATALOGO_CUENTAS.keys()), index=0, key="cd")
        with col2:
            moneda_debe = st.selectbox("Moneda Base", ["Bs", "$"], key="md")
        with col3:
            monto_debe = st.number_input("Monto en Moneda Base", min_value=0.0, value=abs(monto_sugerido), step=0.01, key="vd")
            
        st.markdown("##### **Renglón 2: Cuenta de Abono (HABER)**")
        col1_h, col2_h, col3_h = st.columns([2, 1, 1])
        with col1_h:
            cuenta_haber_cod = st.selectbox("Seleccione Cuenta Acreedora", list(CATALOGO_CUENTAS.keys()), index=9, key="ch")
        with col2_h:
            moneda_haber = st.selectbox("Moneda Base", ["Bs", "$"], key="mh")
        with col3_h:
            monto_haber = st.number_input("Monto en Moneda Base", min_value=0.0, value=abs(monto_sugerido), step=0.01, key="vh")

        registrar_btn = st.form_submit_button("💾 Procesar y Registrar Asiento")
        
        if registrar_btn:
            if monto_debe <= 0 or monto_haber <= 0:
                st.error("❌ Los montos deben ser superiores a cero.")
            else:
                debe_bs = monto_debe if moneda_debe == "Bs" else monto_debe * tasa_bcv
                debe_usd = monto_debe if moneda_debe == "$" else monto_debe / tasa_bcv
                haber_bs = monto_haber if moneda_haber == "Bs" else monto_haber * tasa_bcv
                haber_usd = monto_haber if moneda_haber == "$" else monto_haber / tasa_bcv
                
                if round(debe_bs, 2) != round(haber_bs, 2):
                    haber_bs = debe_bs
                    haber_usd = debe_usd
                
                fila_debe = {
                    "ID_Asiento": siguiente_asiento, "Fecha": str(fecha_asiento), 
                    "Código Cuenta": cuenta_debe_cod, "Cuenta": CATALOGO_CUENTAS[cuenta_debe_cod], 
                    "Descripción": glosa_general, "Debe_Bs": debe_bs, "Haber_Bs": 0.0, 
                    "Debe_USD": debe_usd, "Haber_USD": 0.0, "Tasa": tasa_bcv
                }
                fila_haber = {
                    "ID_Asiento": siguiente_asiento, "Fecha": str(fecha_asiento), 
                    "Código Cuenta": cuenta_haber_cod, "Cuenta": CATALOGO_CUENTAS[cuenta_haber_cod], 
                    "Descripción": glosa_general, "Debe_Bs": 0.0, "Haber_Bs": haber_bs, 
                    "Debe_USD": 0.0, "Haber_USD": haber_usd, "Tasa": tasa_bcv
                }
                
                st.session_state.contabilidad = pd.concat([
                    st.session_state.contabilidad, 
                    pd.DataFrame([fila_debe, fila_haber])
                ], ignore_index=True)
                st.success("✅ Asiento contable guardado exitosamente.")

# --- MÓDULO: LIBRO DIARIO GENERAL ---
elif st.session_state.modulo_activo == "Diario":
    st.header("📖 Libro Diario Obligatorio - JAC Venezuela")
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No hay registros en el Libro Diario.")
    else:
        moneda_vista = st.radio("Presentar Libro Diario expresado en:", ["Bolívares (Moneda Legal)", "Dólares Americanos (USD)"], horizontal=True)
        if moneda_vista == "Dólares Americanos (USD)":
            df_mostrar = df_diario[["ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", "Debe_USD", "Haber_USD", "Tasa"]].copy()
        else:
            df_mostrar = df_diario[["ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", "Debe_Bs", "Haber_Bs"]].copy()
        st.dataframe(df_mostrar, use_container_width=True)

# --- MÓDULO: LIBRO MAYOR ---
elif st.session_state.modulo_activo == "Mayor":
    st.header("🗂️ Libro Mayor Analítico - JAC Venezuela")
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("El Libro Mayor se encuentra vacío.")
    else:
        st.write("Cuentas Analíticas registradas:")
        for cuenta in df_diario["Cuenta"].unique():
            st.markdown(f"📦 **Cuenta: {cuenta}**")
            df_cuenta = df_diario[df_diario["Cuenta"] == cuenta].reset_index(drop=True)
            st.dataframe(df_cuenta, use_container_width=True)

# --- MÓDULO: BALANCE DE COMPROBACIÓN ---
elif st.session_state.modulo_activo == "Comprobacion":
    st.header("⚖️ Balance de Comprobación - JAC Venezuela")
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No hay datos contables suficientes para estructurar el Balance de Comprobación.")
    else:
        bal_comprobacion = df_diario.groupby(["Código Cuenta", "Cuenta"]).agg(
            Total_Debe=('Debe_Bs', 'sum'),
            Total_Haber=('Haber_Bs', 'sum')
        ).reset_index()
        
        # Totales generales de control para el principio de partida doble
        sum_debe = bal_comprobacion["Total_Debe"].sum()
        sum_haber = bal_comprobacion["Total_Haber"].sum()
        
        st.dataframe(bal_comprobacion, use_container_width=True)
        
        c_tot1, c_tot2 = st.columns(2)
        c_tot1.metric("Suma Total Debe (Bs)", f"Bs. {sum_debe:,.2f}")
        c_tot2.metric("Suma Total Haber (Bs)", f"Bs. {sum_haber:,.2f}")

# --- MÓDULO: ESTADO DE SITUACIÓN FINANCIERA ---
elif st.session_state.modulo_activo == "Situacion":
    st.header("📋 Estado de Situación Financiera - JAC Venezuela")
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No existen saldos para computar cierres financieros.")
    else:
        saldos_globales = df_diario.groupby(["Código Cuenta", "Cuenta"]).agg(
            D_bs=('Debe_Bs', 'sum'), H_bs=('Haber_Bs', 'sum')
        ).reset_index()
        saldos_globales["Saldo_Neto_Bs"] = saldos_globales["D_bs"] - saldos_globales["H_bs"]
        
        st.markdown("### Balance Unificado VEN-NIF")
        st.dataframe(saldos_globales, use_container_width=True)
