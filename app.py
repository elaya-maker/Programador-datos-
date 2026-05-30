import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Librerías para procesar archivos de la biblioteca de Windows
import pypdf
import docx

# Configuración de la página
st.set_page_config(page_title="Portal de Herramientas Contables - Empresa JAC Venezuela", layout="wide", page_icon="🇻🇪")

# Inicializar el estado de la sesión (Libro Mayor Auxiliar / Base de Datos)
if 'contabilidad' not in st.session_state:
    st.session_state.contabilidad = pd.DataFrame(columns=[
        "ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", 
        "Debe_Bs", "Haber_Bs", "Debe_USD", "Haber_USD", "Tasa"
    ])

# Inicializar estado para el módulo activo (Control de navegación por botones en pantalla)
if 'modulo_activo' not in st.session_state:
    st.session_state.modulo_activo = "Portal Principal"

# --- MARCO REGULATORIO VENEZOLANO (BARRA LATERAL) ---
st.sidebar.markdown("### 📜 Marco Regulatorio (VEN-NIF)")
st.sidebar.caption(
    "Esta herramienta se rige bajo los lineamientos de las **BA VEN-NIF** "
    "(Federación de Colegios de Contadores Públicos de Venezuela), el **Código de Comercio** "
    "(Arts. 32 al 44 sobre obligatoriedad de libros) y las directrices de facturación y "
    "retenciones del **SENIAT**. Soporta registros bimonetarios según el Convenio Cambiario N° 1 del BCV."
)
st.sidebar.write("---")

# Control de Tasa Oficial según regulaciones del BCV en la barra lateral
tasa_bcv = st.sidebar.number_input("Tasa Oficial BCV del día (Bs/$)", min_value=1.0, value=60.0, step=0.01, format="%.2f")

# Catálogo de Cuentas estandarizado
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
# 🏢 DISEÑO INTERACTIVO DEL PORTAL DE BIENVENIDA (PANTALLA PRINCIPAL)
# ==============================================================================

# Encabezado exclusivo de la Empresa JAC Venezuela con representación estilizada del logo vectorial
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

# Si estamos dentro de algún módulo, habilitar el botón de retorno arriba
if st.session_state.modulo_activo != "Portal Principal":
    if st.button("⬅️ Volver al Menú Principal (JAC Venezuela)"):
        st.session_state.modulo_activo = "Portal Principal"
        st.rerun()

# --- RENDERIZADO DEL PORTAL PRINCIPAL DE HERRAMIENTAS ---
if st.session_state.modulo_activo == "Portal Principal":
    st.markdown("### 🏛️ Distribución General de Módulos")
    st.write("Seleccione la dimensión operativa contable o fiscal que desea ejecutar en este momento:")
    st.write("")
    
    # Grid de Categorías con columnas de herramientas estructuradas
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    
    with cat_col1:
        st.markdown("#### 📊 Análisis y Conciliación")
        if st.button("📈 Dashboard Analítico Empresarial", use_container_width=True):
            st.session_state.modulo_activo = "Dashboard"
            st.rerun()
        if st.button("📝 Módulo: Asentar Diario (Input / Archivos)", use_container_width=True):
            st.session_state.modulo_activo = "Asentar"
            st.rerun()
        st.button("⚙️ Auditoría de Bancos (Próximamente)", use_container_width=True, disabled=True)
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

# Sincronizar el menú lateral por si el usuario prefiere navegar desde allí
menu = st.sidebar.selectbox("Navegación Rápida", [
    "Ir al Portal Principal",
    "0. Dashboard Interactividad Empresarial",
    "1. Asentar Diario (Input)",
    "2. Libro Diario General",
    "3. Libro Mayor Analítico",
    "4. Balance de Comprobación",
    "5. Estado de Situación Financiera"
], index=0)

# Atajo de la barra lateral para cambiar el estado del módulo
if menu == "Ir al Portal Principal":
    pass  
elif menu == "0. Dashboard Interactividad Empresarial":
    st.session_state.modulo_activo = "Dashboard"
elif menu == "1. Asentar Diario (Input)":
    st.session_state.modulo_activo = "Asentar"
elif menu == "2. Libro Diario General":
    st.session_state.modulo_activo = "Diario"
elif menu == "3. Libro Mayor Analítico":
    st.session_state.modulo_activo = "Mayor"
elif menu == "4. Balance de Comprobación":
    st.session_state.modulo_activo = "Comprobacion"
elif menu == "5. Estado de Situación Financiera":
    st.session_state.modulo_activo = "Situacion"


# ==============================================================================
# ENRUTAMIENTO DINÁMICO DE MÓDULOS ACTIVOS
# ==============================================================================

# --- MÓDULO 0: DASHBOARD INTERACTIVO ---
if st.session_state.modulo_activo == "Dashboard":
    st.header("📈 Dashboard Analítico de Rendimiento - JAC Venezuela")
    st.write("Análisis gráfico en tiempo real del flujo operativo de la empresa (Ingresos vs. Gastos).")
    
    df_dashboard = st.session_state.contabilidad.copy()
    
    if df_dashboard.empty:
        st.info("📊 El dashboard se estructurará automáticamente cuando registre los primeros movimientos en el Libro Diario.")
    else:
        moneda_dash = st.radio("Expresar analíticas del Dashboard en:", ["Bolívares (Bs)", "Dólares ($)"], horizontal=True)
        
        df_dashboard["Clasificacion"] = df_dashboard["Código Cuenta"].apply(
            lambda x: "Ingreso" if x.startswith("4") else ("Gasto" if x.startswith("5") else "Otro")
        )
        
        df_res = df_dashboard[df_dashboard["Clasificacion"].isin(["Ingreso", "Gasto"])].copy()
        
        if df_res.empty:
            st.warning("⚠️ Hay asientos registrados, pero ninguno corresponde a cuentas de Ingresos (4) o Gastos (5).")
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
            
            if utilidad_neta >= 0:
                kpi3.metric("Utilidad del Ejercicio (VEN-NIF)", f"{simbolo} {utilidad_neta:,.2f}", delta="Superávit")
            else:
                kpi3.metric("Pérdida del Ejercicio (VEN-NIF)", f"{simbolo} {utilidad_neta:,.2f}", delta="Déficit", delta_color="inverse")
                
            st.write("---")
            
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader("Comparativa Temporal: Ingresos vs Gastos")
                df_trend = df_res.groupby(["Fecha", "Clasificacion"])["Monto_Final"].sum().reset_index()
                fig_trend = px.bar(
                    df_trend, x="Fecha", y="Monto_Final", color="Clasificacion",
                    barmode="group", labels={"Monto_Final": f"Total ({simbolo})"},
                    color_discrete_map={"Ingreso": "#2ecc71", "Gasto": "#e74c3c"}
                )
                st.plotly_chart(fig_trend, use_container_width=True)
                
            with col_g2:
                st.subheader("Distribución Porcentual de Gastos")
                df_pie_gastos = df_res[df_res["Clasificacion"] == "Gasto"].groupby("Cuenta")["Monto_Final"].sum().reset_index()
                if not df_pie_gastos.empty:
                    fig_pie = px.pie(
                        df_pie_gastos, values="Monto_Final", names="Cuenta",
                        hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.write("No se registran gastos para graficar segmentaciones.")

# --- MÓDULO 1: ASENTAR DIARIO ---
elif st.session_state.modulo_activo == "Asentar":
    st.header("📝 Registro de Asientos Contables (Partida Doble) - JAC Venezuela")
    st.write("Conforme al Artículo 34 del Código de Comercio, se deben asentar cronológicamente las operaciones indicando la cuenta deudora y acreedora.")
    
    st.markdown("### 📥 Asistente de Importación Inteligente (Excel, PDF, Word)")
    st.write("Cargue estados de cuenta, facturas de gastos o comprobantes de compras para extraer su información automáticamente.")
    
    archivo_importado = st.file_uploader(
        "Arrastre aquí su archivo desde Windows", 
        type=["xlsx", "xls", "csv", "pdf", "docx"]
    )
    
    glosa_sugerida = ""
    monto_sugerido = 0.0
    
    if archivo_importado is not None:
        nombre_archivo = archivo_importado.name
        st.info(f"📂 Archivo detectado: {nombre_archivo}")
        
        if nombre_archivo.endswith(('.xlsx', '.xls', '.csv')):
            try:
                if nombre_archivo.endswith('.csv'):
                    df_ext = pd.read_csv(archivo_importado)
                else:
                    df_ext = pd.read_excel(archivo_importado)
                
                st.write("📊 **Vista previa de los datos del archivo:**")
                st.dataframe(df_ext.head(3), use_container_width=True)
                
                columnas_numericas = df_ext.select_dtypes(include=['number']).columns
                if len(columnas_numericas) > 0:
                    monto_sugerido = float(df_ext[columnas_numericas[0]].iloc[0])
                glosa_sugerida = f"Importación de datos desde archivo Excel/CSV: {nombre_archivo}"
                st.success("✅ Datos tabulares leídos. Use la información de la tabla para llenar el asiento abajo.")
            except Exception as e:
                st.error(f"Error al leer el archivo Excel/CSV: {e}")
                
        elif nombre_archivo.endswith('.pdf'):
            try:
                lector_pdf = pypdf.PdfReader(archivo_importado)
                texto_extraido = ""
                for pagina in lector_pdf.pages:
                    texto_extraido += pagina.extract_text()
                
                st.write("📄 **Texto detectado en la Factura/Documento PDF:**")
                st.text_area("Contenido extraído", texto_extraido[:1000], height=120)
                
                glosa_sugerida = f"Gasto según documento PDF: {nombre_archivo}"
                st.success("✅ Texto del PDF extraído con éxito para auditoría visual.")
            except Exception as e:
                st.error(f"Error al procesar el PDF: {e}")
                
        elif nombre_archivo.endswith('.docx'):
            try:
                doc = docx.Document(archivo_importado)
                texto_word = "\n".join([p.text for p in doc.paragraphs])
                
                st.write("📝 **Texto detectado en el documento de Word:**")
                st.text_area("Contenido del contrato/comprobante", texto_word[:1000], height=120)
                
                glosa_sugerida = f"Registro según documento Word: {nombre_archivo}"
                st.success("✅ Documento Word leído con éxito.")
            except Exception as e:
                st.error(f"Error al procesar el archivo Word: {e}")

    st.markdown("---")
    
    if not st.session_state.contabilidad.empty:
        siguiente_asiento = int(st.session_state.contabilidad["ID_Asiento"].max()) + 1
    else:
        siguiente_asiento = 1
        
    st.subheader(f"Comprobante de Diario N° {siguiente_asiento}")
    
    with st.form("form_asiento", clear_on_submit=True):
        fecha_asiento = st.date_input("Fecha de Registro Legal", datetime.now())
        glosa_general = st.text_input("Concepto / Glosa del Asiento", value=glosa_sugerida, placeholder="Ej: Registro de ventas...")
        
        st.markdown("##### **Renglón 1: Cuenta de Cargo (DEBE)**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            cuenta_debe_cod = st.selectbox("Seleccione Cuenta Deudora", list(CATALOGO_CUENTAS.keys()), index=0, key="cd")
            cuenta_debe_nom = CATALOGO_CUENTAS[cuenta_debe_cod]
        with col2:
            moneda_debe = st.selectbox("Moneda Base", ["Bs", "$"], key="md")
        with col3:
            monto_debe = st.number_input("Monto en Moneda Base", min_value=0.0, value=abs(monto_sugerido), step=0.01, key="vd")
            
        st.markdown("##### **Renglón 2: Cuenta de Abono (HABER)**")
        col1_h, col2_h, col3_h = st.columns([2, 1, 1])
        with col1_h:
            cuenta_haber_cod = st.selectbox("Seleccione Cuenta Acreedora", list(CATALOGO_CUENTAS.keys()), index=9, key="ch")
            cuenta_haber_nom = CATALOGO_CUENTAS[cuenta_haber_cod]
        with col2_h:
            moneda_haber = st.selectbox("Moneda Base", ["Bs", "$"], key="mh")
        with col3_h:
            monto_haber = st.number_input("Monto en Moneda Base", min_value=0.0, value=abs(monto_sugerido), step=0.01, key="vh")

        registrar_btn = st.form_submit_button("💾 Procesar y Registrar Asiento")
        
        if registrar_btn:
            if monto_debe <= 0 or monto_haber <= 0:
                st.error("❌ Los valores ingresados en el asiento deben ser mayores a cero.")
            else:
                debe_bs = monto_debe if moneda_debe == "Bs" else monto_debe * tasa_bcv
                debe_usd = monto_debe if moneda_debe == "$" else monto_debe / tasa_bcv
                
                haber_bs = monto_haber if moneda_haber == "Bs" else monto_haber * tasa_bcv
                haber_usd = monto_haber if moneda_haber == "$" else monto_haber / tasa_bcv
                
                if round(debe_bs, 2) != round(haber_bs, 2):
                    st.warning(f"⚠️ Asiento ajustado por diferencia marginal cambiaria. Equivalencia balanceada a: {debe_bs:,.2f} Bs.")
                    haber_bs = debe_bs
                    haber_usd = debe_usd
                
                fila_debe = {
                    "ID_Asiento": siguiente_asiento, "Fecha": str(fecha_asiento), 
                    "Código Cuenta": cuenta_debe_cod, "Cuenta": cuenta_debe_nom, 
                    "Descripción": glosa_general, "Debe_Bs": debe_bs, "Haber_Bs": 0.0, 
                    "Debe_USD": debe_usd, "Haber_USD": 0.0, "Tasa": tasa_bcv
                }
                fila_haber = {
                    "ID_Asiento": siguiente_asiento, "Fecha": str(fecha_asiento), 
                    "Código Cuenta": cuenta_haber_cod, "Cuenta": cuenta_haber_nom, 
                    "Descripción": glosa_general, "Debe_Bs": 0.0, "Haber_Bs": haber_bs, 
                    "Debe_USD": 0.0, "Haber_USD": haber_usd, "Tasa": tasa_bcv
                }
                
                st.session_state.contabilidad = pd.concat([
                    st.session_state.contabilidad, 
                    pd.DataFrame([fila_debe, fila_haber])
                ], ignore_index=True)
                st.success(f"✅ Comprobante Contable N° {siguiente_asiento} guardado en el Libro Diario.")

# --- MÓDULO 2: LIBRO DIARIO GENERAL ---
elif st.session_state.modulo_activo == "Diario":
    st.header("📖 Libro Diario Obligatorio - JAC Venezuela")
    st.write("Estructura legal exigida para la presentación ante tribunales de comercio o registros mercantiles.")
    
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No hay registros en el Libro Diario.")
    else:
        moneda_vista = st.radio("Presentar Libro Diario expresado en:", ["Bolívares (Moneda de Cuenta Legal)", "Dólares Americanos (USD)"], horizontal=True)
        
        if moneda_vista == "Dólares Americanos (USD)":
            df_mostrar = df_diario[["ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", "Debe_USD", "Haber_USD", "Tasa"]].copy()
            df_mostrar.columns = ["Asiento", "Fecha", "Código", "Cuenta Contable", "Glosa/Descripción", "Debe ($)", "Haber ($)", "Tasa BCV"]
        else:
            df_mostrar = df_diario[["ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", "Debe_Bs", "Haber_Bs"]].copy()
            df_mostrar.columns = ["Asiento", "Fecha", "Código", "Cuenta Contable", "Glosa/Descripción", "Debe (Bs.)", "Haber (Bs.)"]
            
        st.dataframe(df_mostrar, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, index=False, sheet_name='Libro Diario Legal')
            
        st.download_button(
            label="📊 Descargar Libro Diario Oficial (Excel)",
            data=buffer.getvalue(),
            file_name=f"libro_diario_jac_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- MÓDULO 3: LIBRO MAYOR ---
elif st.session_state.modulo_activo == "Mayor":
    st.header("🗂️ Libro Mayor Folio por Folio - JAC Venezuela")
    st.write("Sintetiza los movimientos cargados al Debe y al Haber de cada cuenta de forma analítica.")
    
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("El Libro Mayor se encuentra vacío (requiere asientos previos).")
    else:
        moneda_mayor = st.radio("Moneda de análisis del Mayor:", ["Bolívares (Bs.)", "Dólares ($)"], horizontal=True)
        cuentas_afectadas = df_diario["Cuenta"].unique()
        
        for cuenta in cuentas_afectadas:
            st.markdown(f"📦 **Cuenta Analítica: {cuenta}**")
            df_cuenta = df_diario[df_diario["Cuenta"] == cuenta].copy()
            
            if moneda_mayor == "Bolívares (Bs.)":
                df_c_vista = df_cuenta[["Fecha", "ID_Asiento", "Descripción", "Debe_Bs", "Haber_Bs"]]
                saldo_neto = df_c_vista["Debe_Bs"].sum() - df_c_vista["Haber_Bs"].sum()
                st.dataframe(df_c_vista.rename(columns={"Debe_Bs": "Debe (Bs)", "Haber_Bs": "Haber (Bs)"}), use_container_width=True)
                st.markdown(f"**Saldo de Cuenta:** `{saldo_neto:,.2f} Bs.`")
            else:
                df_c_vista = df_cuenta[["Fecha", "ID_Asiento", "Descripción", "Debe_USD", "Haber_USD"]]
                saldo_neto = df_c_vista["Debe_USD"].sum() - df_c_vista["Haber_USD"].sum()
                st.dataframe(df_c_vista.rename(columns={"Debe_USD": "Debe ($)", "Haber_USD": "Haber ($)"}), use_container_width=True)
                st.markdown(f"**Saldo de Cuenta:** `$ {saldo_neto:,.2f}`")
            st.write("---")

# --- MÓDULO 4: BALANCE DE COMPROBACIÓN ---
elif st.session_state.modulo_activo == "Comprobacion":
    st.header("⚖️ Balance de Comprobación - JAC Venezuela")
    st.write("Verificación técnica del principio de igualdad matemática en los libros contables.")
    
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No hay datos contables suficientes.")
    else:
        bal_comprobacion = df_diario.groupby(["Código Cuenta", "Cuenta"]).agg(
            Total_Debe=('Debe_Bs', 'sum'),
            Total_Haber=('Haber_Bs', 'sum')
        ).reset_index()
        
        bal_comprobacion["Saldo Deudor (Bs)"] = bal_comprobacion.apply(lambda r: r["Total_Debe"] - r["Total_Haber"] if r["Total_Debe"] >= r["Total_Haber"] else 0.0, axis=1)
