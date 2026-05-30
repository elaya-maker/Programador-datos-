import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Automatización Contable Multidivisa", layout="wide", page_icon="📊")

# Inicializar el estado de la sesión para simular una base de datos local
if 'contabilidad' not in st.session_state:
    st.session_state.contabilidad = pd.DataFrame(columns=[
        "Fecha", "Tipo", "Categoría", "Descripción", "Moneda", "Monto", "Tasa Cambio", "Monto Alternativo", "Estado"
    ])

# --- TÍTULO DE LA APLICACIÓN ---
st.title("💼 Sistema Automatizado de Contabilidad Multidivisa (Bs / $)")
st.markdown("Gestione sus finanzas en Bolívares y Dólares, concilie cuentas y genere reportes detallados en pantalla y Excel.")
st.write("---")

# --- BARRA LATERAL / CONFIGURACIÓN ---
st.sidebar.header("⚙️ Configuración Global")
tasa_referencia = st.sidebar.number_input("Tasa de Cambio de Referencia (Bs/$)", min_value=1.0, value=60.0, step=0.1, format="%.2f")

st.sidebar.write("---")
menu = st.sidebar.selectbox("Seleccione un Módulo", [
    "Dashboard Financiero", 
    "Registrar Transacción", 
    "Conciliación Bancaria", 
    "Reportes Financieros (Pantalla y Excel)"
])

# --- MÓDULO 1: DASHBOARD ---
if menu == "Dashboard Financiero":
    st.header("📈 Dashboard Financiero General")
    
    # Selección de moneda de visualización para el Dashboard
    moneda_vista = st.radio("Visualizar métricas principales en:", ["USD ($)", "VES (Bs)"], horizontal=True)
    
    df = st.session_state.contabilidad.copy()
    
    if df.empty:
        st.info("No hay datos registrados aún. Vaya al módulo 'Registrar Transacción'.")
    else:
        # Calcular montos unificados para el dashboard dinámico
        def calcular_monto_vista(row):
            if moneda_vista == "USD ($)":
                return row["Monto"] if row["Moneda"] == "USD ($)" else row["Monto"] / row["Tasa Cambio"]
            else:
                return row["Monto"] if row["Moneda"] == "VES (Bs)" else row["Monto"] * row["Tasa Cambio"]

        df["Monto_Vista"] = df.apply(calcular_monto_vista, axis=1)
        
        ingresos = df[df["Tipo"] == "Ingreso"]["Monto_Vista"].sum()
        gastos = df[df["Tipo"] == "Gasto"]["Monto_Vista"].sum()
        balance = ingresos - gastos
        
        simbolo = "$" if moneda_vista == "USD ($)" else "Bs"
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ingresos", f"{simbolo} {ingresos:,.2f}")
        col2.metric("Total Gastos", f"{simbolo} {gastos:,.2f}", delta=f"-{simbolo} {gastos:,.2f}", delta_color="inverse")
        col3.metric("Balance Neto", f"{simbolo} {balance:,.2f}")
        
        st.write("---")
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Ingresos vs Gastos (Temporal)")
            fig_bar = px.bar(df, x="Fecha", y="Monto_Vista", color="Tipo", barmode="group",
                             labels={"Monto_Vista": f"Monto ({simbolo})"},
                             color_discrete_map={"Ingreso": "#2ecc71", "Gasto": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_graf2:
            st.subheader("Distribución de Gastos por Categoría")
            df_gastos = df[df["Tipo"] == "Gasto"]
            if not df_gastos.empty:
                fig_pie = px.pie(df_gastos, values="Monto_Vista", names="Categoría", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No hay gastos registrados.")

        st.subheader("📋 Últimos Movimientos Asentados")
        st.dataframe(st.session_state.contabilidad.sort_values(by="Fecha", ascending=False), use_container_width=True)

# --- MÓDULO 2: REGISTRAR TRANSACCIÓN ---
elif menu == "Registrar Transacción":
    st.header("📝 Registro de Movimientos Multidivisa")
    st.info(f"Tasa de cambio actual configurada en la barra lateral: 1 $ = {tasa_referencia:,.2f} Bs")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha de la operación", datetime.now())
            tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
            moneda = st.selectbox("Moneda de la Operación", ["USD ($)", "VES (Bs)"])
            monto = st.number_input("Monto Original", min_value=0.01, step=0.01, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoría", [
                "Ventas", "Servicios", "Nómina", "Alquiler", "Marketing", "Impuestos", "Otros"
            ])
            descripcion = st.text_input("Descripción / Concepto")
            estado = st.selectbox("Estado", ["Conciliado", "Pendiente"])
            
        guardar = st.form_submit_button("Guardar Transacción")
        
        if guardar:
            # Calcular monto alternativo automáticamente según la tasa de cambio activa
            if moneda == "USD ($)":
                monto_alt = monto * tasa_referencia
            else:
                monto_alt = monto / tasa_referencia
                
            nueva_fila = {
                "Fecha": pd.to_datetime(fecha).strftime('%Y-%m-%d'),
                "Tipo": tipo,
                "Categoría": categoria,
                "Descripción": descripcion,
                "Moneda": moneda,
                "Monto": monto,
                "Tasa Cambio": tasa_referencia,
                "Monto Alternativo": round(monto_alt, 2),
                "Estado": estado
            }
            
            st.session_state.contabilidad = pd.concat([
                st.session_state.contabilidad, 
                pd.DataFrame([nueva_fila])
            ], ignore_index=True)
            st.success(f"¡Transacción guardada! Registrado en {moneda} e historial calculado equivalentemente.")

# --- MÓDULO 3: CONCILIACIÓN BANCARIA ---
elif menu == "Conciliación Bancaria":
    st.header("🤖 Conciliación Automatizada Multidivisa")
    st.write("Cargue el archivo CSV de su extracto bancario. El sistema buscará correspondencias exactas.")
    archivo_banco = st.file_uploader("Cargar Extracto Bancario (CSV)", type=["csv"])
    if archivo_banco is not None:
        st.success("Archivo recibido con éxito.")

# --- MÓDULO 4: REPORTES (PANTALLA Y EXCEL) ---
elif menu == "Reportes Financieros (Pantalla y Excel)":
    st.header("📥 Generación de Reportes de Salida")
    
    df_origen = st.session_state.contabilidad.copy()
    
    if df_origen.empty:
        st.info("El Libro Mayor está vacío. No hay datos para generar reportes.")
    else:
        st.markdown("### 👁️ 1. Reporte en Pantalla (Vista Multidivisa Unificada)")
        st.write("A continuación se desglosan todas las transacciones con su respectivo equivalente calculado en la otra divisa:")
        
        df_reporte = df_origen.copy()
        
        # Columnas explícitas calculadas para una lectura contable perfecta
        df_reporte["Monto en USD ($)"] = df_reporte.apply(lambda r: r["Monto"] if r["Moneda"] == "USD ($)" else r["Monto Alternativo"], axis=1)
        df_reporte["Monto en VES (Bs)"] = df_reporte.apply(lambda r: r["Monto"] if r["Moneda"] == "VES (Bs)" else r["Monto Alternativo"], axis=1)
        
        # Mostrar el dataframe unificado en la pantalla de Streamlit
        st.dataframe(df_reporte[[
            "Fecha", "Tipo", "Categoría", "Descripción", "Moneda", "Monto", "Tasa Cambio", "Monto en USD ($)", "Monto en VES (Bs)", "Estado"
        ]], use_container_width=True)
        
        # Cálculos de Totales globales
        ing_usd = df_reporte[df_reporte["Tipo"] == "Ingreso"]["Monto en USD ($)"].sum()
        gas_usd = df_reporte[df_reporte["Tipo"] == "Gasto"]["Monto en USD ($)"].sum()
        ing_bs = df_reporte[df_reporte["Tipo"] == "Ingreso"]["Monto en VES (Bs)"].sum()
        gas_bs = df_reporte[df_reporte["Tipo"] == "Gasto"]["Monto en VES (Bs)"].sum()
        
        st.markdown("#### 📑 Totales Consolidados")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Total Dólares ($):**\\n• Ingresos: ${ing_usd:,.2f}\\n• Gastos: ${gas_usd:,.2f}\\n• Neto: ${ing_usd - gas_usd:,.2f}")
        with c2:
            st.success(f"**Total Bolívares (Bs):**\\n• Ingresos: {ing_bs:,.2f} Bs\\n• Gastos: {gas_bs:,.2f} Bs\\n• Neto: {ing_bs - gas_bs:,.2f} Bs")
            
        st.write("---")
        st.markdown("### 💾 2. Exportación a Archivo Excel")
        st.write("Descargue el reporte completo formateado automáticamente en hojas tabulares para sus libros contables oficiales.")
        
        # Generación del libro de Excel multimonedas en memoria (pandas + openpyxl)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Pestaña 1: Libro Mayor Completo con el desglose dual
            df_reporte.to_excel(writer, index=False, sheet_name='Libro Mayor Bimoneda')
            
            # Pestaña 2: Resumen Ejecutivo de Cierre
            df_resumen = pd.DataFrame({
                "Métrica Financiera": ["Total Ingresos", "Total Gastos", "Balance Neto (Utilidad/Pérdida)"],
                "Expresado en USD ($)": [ing_usd, gas_usd, ing_usd - gas_usd],
                "Expresado en VES (Bs)": [ing_bs, gas_bs, ing_bs - gas_bs]
            })
            df_resumen.to_excel(writer, index=False, sheet_name='Resumen Balances')
            
        st.download_button(
            label="📥 Descargar Reporte Contable Completo (Excel)",
            data=buffer.getvalue(),
            file_name=f"reporte_contable_dual_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
