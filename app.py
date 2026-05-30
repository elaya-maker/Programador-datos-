import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Automatización Contable", layout="wide", page_icon="📊")

# Inicializar el estado de la sesión para simular una base de datos local
if 'contabilidad' not in st.session_state:
    st.session_state.contabilidad = pd.DataFrame(columns=[
        "Fecha", "Tipo", "Categoría", "Descripción", "Monto", "Estado"
    ])

# --- TÍTULO DE LA APLICACIÓN ---
st.title("💼 Sistema Automatizado de Contabilidad")
st.markdown("Gestione sus finanzas, concilie cuentas bancarias y genere reportes al instante.")
st.write("---")

# --- BARRA LATERAL / NAVEGACIÓN ---
menu = st.sidebar.selectbox("Seleccione un Módulo", [
    "Dashboard Financiero", 
    "Registrar Transacción", 
    "Conciliación Bancaria", 
    "Exportar Reportes"
])

# --- MÓDULO 1: DASHBOARD ---
if menu == "Dashboard Financiero":
    st.header("📈 Dashboard Financiero")
    
    df = st.session_state.contabilidad
    
    if df.empty:
        st.info("No hay datos registrados aún. Vaya al módulo 'Registrar Transacción'.")
    else:
        # Métricas principales
        ingresos = df[df["Tipo"] == "Ingreso"]["Monto"].sum()
        gastos = df[df["Tipo"] == "Gasto"]["Monto"].sum()
        balance = ingresos - gastos
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Ingresos", f"${ingresos:,.2f}", delta=f"{ingresos:,.2f}")
        col2.metric("Total Gastos", f"${gastos:,.2f}", delta=f"-${gastos:,.2f}", delta_color="inverse")
        col3.metric("Balance Neto", f"${balance:,.2f}", delta="Disponible")
        
        st.write("---")
        
        # Gráficos
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("Ingresos vs Gastos")
            fig_bar = px.bar(df, x="Fecha", y="Monto", color="Tipo", barmode="group",
                             color_discrete_map={"Ingreso": "#2ecc71", "Gasto": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_graf2:
            st.subheader("Gastos por Categoría")
            df_gastos = df[df["Tipo"] == "Gasto"]
            if not df_gastos.empty:
                fig_pie = px.pie(df_gastos, values="Monto", names="Categoría", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No hay gastos registrados para categorizar.")

        # Tabla de datos recientes
        st.subheader("📋 Últimos Registros")
        st.dataframe(df.sort_values(by="Fecha", ascending=False), use_container_width=True)

# --- MÓDULO 2: REGISTRAR TRANSACCIÓN ---
elif menu == "Registrar Transacción":
    st.header("📝 Registro de Movimientos")
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha de la operación", datetime.now())
            tipo = st.selectbox("Tipo de Movimiento", ["Ingreso", "Gasto"])
            monto = st.number_input("Monto ($)", min_value=0.01, step=0.01, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoría", [
                "Ventas", "Servicios", "Nómina", "Alquiler", "Marketing", "Impuestos", "Otros"
            ])
            descripcion = st.text_input("Descripción / Concepto")
            estado = st.selectbox("Estado", ["Conciliado", "Pendiente"])
            
        guardar = st.form_submit_form("Guardar Transacción")
        
        if guardar:
            nueva_fila = {
                "Fecha": pd.to_datetime(fecha),
                "Tipo": tipo,
                "Categoría": categoria,
                "Descripción": descripcion,
                "Monto": monto,
                "Estado": estado
            }
            # Añadir al dataframe global
            st.session_state.contabilidad = pd.concat([
                st.session_state.contabilidad, 
                pd.DataFrame([nueva_fila])
            ], ignore_index=True)
            st.success("¡Transacción registrada exitosamente!")

# --- MÓDULO 3: CONCILIACIÓN BANCARIA ---
elif menu == "Conciliación Bancaria":
    st.header("🤖 Conciliación Automatizada")
    st.write("Suba el archivo CSV de su extracto bancario para cruzarlo automáticamente con el sistema.")
    
    # Ejemplo de estructura requerida
    st.caption("El CSV bancario debe tener las columnas: 'Fecha', 'Detalle', 'Monto'")
    
    archivo_banco = st.file_uploader("Cargar Extracto Bancario (CSV)", type=["csv"])
    
    if archivo_banco is not None:
        try:
            df_banco = pd.read_csv(archivo_banco)
            df_banco["Fecha"] = pd.to_datetime(df_banco["Fecha"])
            st.subheader("🏦 Datos del Banco")
            st.dataframe(df_banco, use_container_width=True)
            
            # Algoritmo simple de conciliación automatizada
            st.subheader("🔄 Resultado del Cruce Automático")
            df_sistema = st.session_state.contabilidad
            
            if df_sistema.empty:
                st.warning("El sistema interno no tiene datos para contrastar.")
            else:
                # Buscar coincidencias exactas en monto
                coincidencias = []
                for idx, fila_banco in df_banco.iterrows():
                    # Buscar en el sistema si existe el mismo monto (puede ser ingreso o gasto)
                    match = df_sistema[df_sistema["Monto"] == abs(fila_banco["Monto"])]
                    if not match.empty:
                        coincidencias.append({
                            "Fecha Banco": fila_banco["Fecha"].strftime('%Y-%m-%d'),
                            "Detalle Banco": fila_banco["Detalle"],
                            "Monto": fila_banco["Monto"],
                            "Estado Conciliación": "✅ Conciliado (Coincidencia Encontrada)"
                        })
                    else:
                        coincidencias.append({
                            "Fecha Banco": fila_banco["Fecha"].strftime('%Y-%m-%d'),
                            "Detalle Banco": fila_banco["Detalle"],
                            "Monto": fila_banco["Monto"],
                            "Estado Conciliación": "❌ Alerta (No encontrado en sistema)"
                        })
                
                df_resultado = pd.DataFrame(coincidencias)
                st.dataframe(df_resultado, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}. Asegúrese de que el formato sea correcto.")

# --- MÓDULO 4: EXPORTAR REPORTES ---
elif menu == "Exportar Reportes":
    st.header("📥 Descarga de Estados Financieros")
    df = st.session_state.contabilidad
    
    if df.empty:
        st.info("No hay datos para exportar.")
    else:
        st.write("Seleccione el formato para descargar el Libro Mayor actual.")
        
        # Conversión a Excel en memoria usando openpyxl/io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Libro Mayor')
        
        st.download_button(
            label="📊 Descargar Reporte en Excel",
            data=buffer.getvalue(),
            file_name=f"reporte_contable_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
