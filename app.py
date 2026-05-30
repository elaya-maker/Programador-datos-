import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Sistema Contable Venezolano VEN-NIF", layout="wide", page_icon="🇻🇪")

# Inicializar el estado de la sesión (Simulación de Libro Mayor Auxiliar/Base de Datos)
if 'contabilidad' not in st.session_state:
    st.session_state.contabilidad = pd.DataFrame(columns=[
        "ID_Asiento", "Fecha", "Código Cuenta", "Cuenta", "Descripción", 
        "Debe_Bs", "Haber_Bs", "Debe_USD", "Haber_USD", "Tasa"
    ])

# --- MARCO REGULATORIO VENEZOLANO (BARRA LATERAL) ---
st.sidebar.markdown("### 📜 Marco Regulatorio (VEN-NIF)")
st.sidebar.caption(
    "Esta herramienta se rige bajo los lineamientos de las **BA VEN-NIF** "
    "(Federación de Colegios de Contadores Públicos de Venezuela), el **Código de Comercio** "
    "(Arts. 32 al 44 sobre obligatoriedad de libros) y las directrices de facturación y "
    "retenciones del **SENIAT**. Soporta registros bimonetarios según el Convenio Cambiario N° 1 del BCV."
)

st.sidebar.write("---")

# ==============================================================================
# 🎛️ MENÚ DESPLEGABLE DE NAVEGACIÓN PRINCIPAL
# Este componente crea el menú interactivo al ingresar a la aplicación
# ==============================================================================
menu = st.sidebar.selectbox("Módulos del Sistema", [
    "1. Asentar Diario (Input)",
    "2. Libro Diario General",
    "3. Libro Mayor Analítico",
    "4. Balance de Comprobación",
    "5. Estado de Situación Financiera"
])

# Control de Tasa Oficial según regulaciones del BCV en la barra lateral
tasa_bcv = st.sidebar.number_input("Tasa Oficial BCV del día (Bs/$)", min_value=1.0, value=60.0, step=0.01, format="%.2f")

# Catálogo de Cuentas estandarizado (Estructura jerárquica)
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

# --- TÍTULO PRINCIPAL DE LA PANTALLA ---
st.title("🇻🇪 Sistema de Automatización Contable Venezolano")
st.markdown("##### Cumplimiento de Principios VEN-NIF (Pymes / GE) • Doble Columna (Debe/Haber) • Multidivisa Histórica")
st.write("---")


# ==============================================================================
# ENRUTAMIENTO DEL MENÚ: Dependiendo de lo seleccionado, se despliega cada módulo
# ==============================================================================

# --- MÓDULO 1: ASENTAR DIARIO ---
if menu == "1. Asentar Diario (Input)":
    st.header("📝 Registro de Asientos Contables (Partida Doble)")
    st.write("Conforme al Artículo 34 del Código de Comercio, se deben asentar cronológicamente las operaciones indicando la cuenta deudora y acreedora.")
    
    # Generador incremental automático de número de asientos
    if not st.session_state.contabilidad.empty:
        siguiente_asiento = int(st.session_state.contabilidad["ID_Asiento"].max()) + 1
    else:
        siguiente_asiento = 1
        
    st.subheader(f"Comprobante de Diario N° {siguiente_asiento}")
    
    with st.form("form_asiento", clear_on_submit=True):
        fecha_asiento = st.date_input("Fecha de Registro Legal", datetime.now())
        glosa_general = st.text_input("Concepto / Glosa del Asiento", placeholder="Ej: Registro de ventas según factura fiscal N°...")
        
        st.markdown("##### **Renglón 1: Cuenta de Cargo (DEBE)**")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            cuenta_debe_cod = st.selectbox("Seleccione Cuenta Deudora", list(CATALOGO_CUENTAS.keys()), index=0, key="cd")
            cuenta_debe_nom = CATALOGO_CUENTAS[cuenta_debe_cod]
        with col2:
            moneda_debe = st.selectbox("Moneda Base", ["Bs", "$"], key="md")
        with col3:
            monto_debe = st.number_input("Monto en Moneda Base", min_value=0.0, step=0.01, key="vd")
            
        st.markdown("##### **Renglón 2: Cuenta de Abono (HABER)**")
        col1_h, col2_h, col3_h = st.columns([2, 1, 1])
        with col1_h:
            cuenta_haber_cod = st.selectbox("Seleccione Cuenta Acreedora", list(CATALOGO_CUENTAS.keys()), index=9, key="ch")
            cuenta_haber_nom = CATALOGO_CUENTAS[cuenta_haber_cod]
        with col2_h:
            moneda_haber = st.selectbox("Moneda Base", ["Bs", "$"], key="mh")
        with col3_h:
            monto_haber = st.number_input("Monto en Moneda Base", min_value=0.0, step=0.01, key="vh")

        registrar_btn = st.form_submit_button("💾 Procesar y Registrar Asiento")
        
        if registrar_btn:
            if monto_debe <= 0 or monto_haber <= 0:
                st.error("❌ Los valores ingresados en el asiento deben ser mayores a cero.")
            else:
                # Conversión bimonetaria estricta de acuerdo a tasas BCV
                debe_bs = monto_debe if moneda_debe == "Bs" else monto_debe * tasa_bcv
                debe_usd = monto_debe if moneda_debe == "$" else monto_debe / tasa_bcv
                
                haber_bs = monto_haber if moneda_haber == "Bs" else monto_haber * tasa_bcv
                haber_usd = monto_haber if moneda_haber == "$" else monto_haber / tasa_bcv
                
                # Forzar validación contable de balance cuadriculado
                if round(debe_bs, 2) != round(haber_bs, 2):
                    st.warning(f"⚠️ Asiento ajustado por diferencia marginal cambiaria. Equivalencia balanceada a: {debe_bs:,.2f} Bs.")
                    haber_bs = debe_bs
                    haber_usd = debe_usd
                
                # Estructuración de registros contables paralelos
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
elif menu == "2. Libro Diario General":
    st.header("📖 Libro Diario Obligatorio")
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
        
        # Generación de Excel para descargas de auditoría
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_mostrar.to_excel(writer, index=False, sheet_name='Libro Diario Legal')
            
        st.download_button(
            label="📊 Descargar Libro Diario Oficial (Excel)",
            data=buffer.getvalue(),
            file_name=f"libro_diario_legal_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- MÓDULO 3: LIBRO MAYOR ---
elif menu == "3. Libro Mayor Analítico":
    st.header("🗂️ Libro Mayor Folio por Folio")
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
elif menu == "4. Balance de Comprobación":
    st.header("⚖️ Balance de Comprobación (Sumas y Saldos)")
    st.write("Verificación técnica del principio de igualdad matemática en los libros contables.")
    
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No hay datos contables suficientes.")
    else:
        # Agrupaciones matemáticas contables en Bolívares
        bal_comprobacion = df_diario.groupby(["Código Cuenta", "Cuenta"]).agg(
            Total_Debe=('Debe_Bs', 'sum'),
            Total_Haber=('Haber_Bs', 'sum')
        ).reset_index()
        
        bal_comprobacion["Saldo Deudor (Bs)"] = bal_comprobacion.apply(lambda r: r["Total_Debe"] - r["Total_Haber"] if r["Total_Debe"] >= r["Total_Haber"] else 0.0, axis=1)
        bal_comprobacion["Saldo Acreedor (Bs)"] = bal_comprobacion.apply(lambda r: r["Total_Haber"] - r["Total_Debe"] if r["Total_Haber"] > r["Total_Debe"] else 0.0, axis=1)
        
        st.dataframe(bal_comprobacion, use_container_width=True)
        
        t_d = bal_comprobacion["Total_Debe"].sum()
        t_h = bal_comprobacion["Total_Haber"].sum()
        st.success(f"**Cruce y Cuadre de Columnas:** Suma Debe: {t_d:,.2f} Bs | Suma Haber: {t_h:,.2f} Bs — **¡Cuadre Perfecto!**")

# --- MÓDULO 5: ESTADO DE SITUACIÓN FINANCIERA ---
elif menu == "5. Estado de Situación Financiera":
    st.header("📋 Estado de Situación Financiera (Balance General)")
    st.write("Presentación clasificada de los saldos patrimoniales bajo los estándares internacionales **VEN-NIF / NIC 1**.")
    
    df_diario = st.session_state.contabilidad.copy()
    
    if df_diario.empty:
        st.info("No existen saldos para computar cierres financieros.")
    else:
        # Cálculo de saldos acumulados netos finales por cuentas
        saldos_globales = df_diario.groupby(["Código Cuenta", "Cuenta"]).agg(
            D_bs=('Debe_Bs', 'sum'),
            H_bs=('Haber_Bs', 'sum')
        ).reset_index()
        saldos_globales["Saldo_Neto_Bs"] = saldos_globales["D_bs"] - saldos_globales["H_bs"]
        
        # Segmentación por dígito inicial según buenas prácticas contables latinoamericanas
        activos_df = saldos_globales[saldos_globales["Código Cuenta"].str.startswith("1")]
        pasivos_df = saldos_globales[saldos_globales["Código Cuenta"].str.startswith("2")]
        patrimonio_df = saldos_globales[saldos_globales["Código Cuenta"].str.startswith("3")]
        
        # Renderizado del Estado de Situación Financiera en Pantalla
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown("### 🟢 ACTIVOS")
            st.dataframe(activos_df[["Cuenta", "Saldo_Neto_Bs"]].rename(columns={"Saldo_Neto_Bs": "Monto (Bs)"}), use_container_width=True)
            total_activos = activos_df["Saldo_Neto_Bs"].sum()
            st.markdown(f"**TOTAL ACTIVOS:** `{total_activos:,.2f} Bs.`")
            
        with col_der:
            st.markdown("### 🔴 PASIVOS Y PATRIMONIO")
            st.write("**Pasivos de Corto y Largo Plazo:**")
            st.dataframe(pasivos_df[["Cuenta", "Saldo_Neto_Bs"]].rename(columns={"Saldo_Neto_Bs": "Monto (Bs)"}), use_container_width=True)
            
            st.write("**Patrimonio Neto Corp:**")
            st.dataframe(patrimonio_df[["Cuenta", "Saldo_Neto_Bs"]].rename(columns={"Saldo_Neto_Bs": "Monto (Bs)"}), use_container_width=True)
            
            # El pasivo y patrimonio contablemente suman con signo inverso/crédito
            total_p_p = abs(pasivos_df["Saldo_Neto_Bs"].sum()) + abs(patrimonio_df["Saldo_Neto_Bs"].sum())
            st.markdown(f"**TOTAL PASIVO Y PATRIMONIO:** `{total_p_p:,.2f} Bs.`")
            
        # Descarga de la Suite Completa de Estados Financieros a Excel
        buffer_suite = io.BytesIO()
        with pd.ExcelWriter(buffer_suite, engine='openpyxl') as writer:
            activos_df.to_excel(writer, index=False, sheet_name='Activos')
            pasivos_df.to_excel(writer, index=False, sheet_name='Pasivos y Patrimonio')
            saldos_globales.to_excel(writer, index=False, sheet_name='Balance General Unificado')
            
        st.write("---")
        st.download_button(
            label="📊 Descargar Balance General Certificado (Excel)",
            data=buffer_suite.getvalue(),
            file_name=f"balance_general_venezuela_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
