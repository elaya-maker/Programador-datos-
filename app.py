import os
import pandas as pd

# 1. Configuración de archivos
archivo_origen = "DETALLES MOV GULF 2026.xlsx"
archivo_destino = "DETALLES MOV GULF 2026_CONSOLIDADO.xlsx"

if not os.path.exists(archivo_origen):
    raise FileNotFoundError(
        f"No se pudo encontrar el archivo '{archivo_origen}' en el directorio actual. "
        f"Asegúrate de colocar el script en la misma carpeta que el archivo Excel."
    )

print("📖 Abriendo el archivo original y leyendo las pestañas...")
excel_file = pd.ExcelFile(archivo_origen)
todas_las_pestanas = excel_file.sheet_names

bloques_consolidados = []

print("🚀 Iniciando procesamiento...")

for nombre_hoja in todas_las_pestanas:
    if "CONSOLIDADO" in nombre_hoja.upper():
        continue

    print(f"  📦 Analizando: {nombre_hoja}")

    # --- CASO ESPECIAL 1: PESTAÑA 'EFECTIVO' (Doble estructura / Caja Chica) ---
    if "EFECTIVO" in nombre_hoja.upper() and "BS" not in nombre_hoja.upper():
        # Leemos la hoja completa sin procesar el header todavía
        df_efectivo = pd.read_excel(excel_file, sheet_name=nombre_hoja, header=None)
        
        # Buscar en qué fila se encuentra realmente el encabezado (donde dice FECHA y DESCRIPCION)
        fila_header = None
        for idx, fila in df_efectivo.iterrows():
            valores_fila = [str(val).upper().strip() for val in fila.values if pd.notna(val)]
            if "FECHA" in valores_fila and "DESCRIPCION" in valores_fila:
                fila_header = idx
                break
        
        if fila_header is None:
            print(f"  ⚠️ No se encontró la fila de encabezados en '{nombre_hoja}'. Se saltará.")
            continue

        # Reasignamos los datos usando la fila detectada como cabecera
        headers = [str(c).strip().upper() for c in df_efectivo.iloc[fila_header]]
        df_datos = df_efectivo.iloc[fila_header + 1:].copy()
        df_datos.columns = headers

        # Encontrar los índices de las columnas para separar Bloque Principal y Caja Chica
        indices_fecha = [i for i, h in enumerate(headers) if h == "FECHA"]
        
        if len(indices_fecha) >= 1:
            # --- SECCIÓN 1: EFECTIVO PRINCIPAL ---
            idx_p = indices_fecha[0]
            df_izq = pd.DataFrame()
            df_izq["FECHA"] = df_datos.iloc[:, idx_p]
            df_izq["DESCRIPCION"] = df_datos.iloc[:, idx_p + 1] if (idx_p + 1) < len(headers) else ""
            
            # En tu excel usas INGRESOS/EGRESOS en efectivo en vez de DEBITO/CREDITO
            df_izq["CREDITO"] = df_datos.iloc[:, idx_p + 2] if (idx_p + 2) < len(headers) else 0 # INGRESOS
            df_izq["DEBITO"] = df_datos.iloc[:, idx_p + 3] if (idx_p + 3) < len(headers) else 0  # EGRESOS
            
            df_izq["BANCO / EFECTIVO"] = f"{nombre_hoja.strip()} (PPAL)"
            df_izq["MONEDA"] = "USD"
            bloques_consolidados.append(df_izq)

        if len(indices_fecha) >= 2:
            # --- SECCIÓN 2: CAJA CHICA ---
            idx_c = indices_fecha[1]
            df_der = pd.DataFrame()
            df_der["FECHA"] = df_datos.iloc[:, idx_c]
            df_der["DESCRIPCION"] = df_datos.iloc[:, idx_c + 1] if (idx_c + 1) < len(headers) else ""
            df_der["CREDITO"] = df_datos.iloc[:, idx_c + 2] if (idx_c + 2) < len(headers) else 0 # INGRESOS
            df_der["DEBITO"] = df_datos.iloc[:, idx_c + 3] if (idx_c + 3) < len(headers) else 0  # EGRESOS
            
            df_der["BANCO / EFECTIVO"] = f"{nombre_hoja.strip()} (CAJA CHICA)"
            df_der["MONEDA"] = "USD"
            bloques_consolidados.append(df_der)
            
        continue

    # --- CASO ESPECIAL 2: PESTAÑA 'PRESTAMO KTSU' ---
    elif "PRESTAMO" in nombre_hoja.upper():
        df = pd.read_excel(excel_file, sheet_name=nombre_hoja, skiprows=1)
        df.columns = df.columns.str.strip()
        
        df_mapeado = pd.DataFrame()
        df_mapeado["FECHA"] = df["FECHA"]
        df_mapeado["BANCO / EFECTIVO"] = nombre_hoja
        df_mapeado["DESCRIPCION"] = df["DESCRIPCION"]
        df_mapeado["CATEGORIA"] = df["CONCEPTO"] if "CONCEPTO" in df.columns else "PRESTAMO"
        df_mapeado["MONEDA"] = "USD"
        
        df_mapeado["DEBITO"] = df["PRESTAMO GULF A KTSU"] if "PRESTAMO GULF A KTSU" in df.columns else 0
        df_mapeado["CREDITO"] = df["PRESTAMO KTSU A GULF"] if "PRESTAMO KTSU A GULF" in df.columns else 0
        df_mapeado["DEBITO $"] = df_mapeado["DEBITO"]
        df_mapeado["CREDITO $"] = df_mapeado["CREDITO"]
        
        bloques_consolidados.append(df_mapeado)
        continue

    # --- CASO 3: CUENTAS BANCARIAS ESTÁNDAR Y EFECTIVO BS ---
    else:
        filas_a_saltar = 1
        if "MERCANTIL NO FISCAL" in nombre_hoja.upper():
            filas_a_saltar = 2

        df = pd.read_excel(excel_file, sheet_name=nombre_hoja, skiprows=filas_a_saltar)
        df.columns = df.columns.str.strip()

        if "FECHA" not in df.columns:
            df = pd.read_excel(excel_file, sheet_name=nombre_hoja, skiprows=0)
            df.columns = df.columns.str.strip()
            if "FECHA" not in df.columns:
                print(f"  ⚠️ Se omitió la pestaña '{nombre_hoja}' porque no se encontró la columna 'FECHA'.")
                continue

        moneda = "USD" if ("USD" in nombre_hoja.upper() or "CASH" in nombre_hoja.upper()) else "BS"

        # Capturar variaciones de ingresos/egresos o débitos/créditos
        debito_orig = df["DEBITO"] if "DEBITO" in df.columns else (df["EGRESOS"] if "EGRESOS" in df.columns else 0)
        credito_orig = df["CREDITO"] if "CREDITO" in df.columns else (df["INGRESOS"] if "INGRESOS" in df.columns else 0)

        categoria = "SIN CATEGORÍA"
        for col_cat in ["CODIGO", "CONCEPTO", "Columna1"]:
            if col_cat in df.columns:
                categoria = df[col_cat]
                break

        df_mapeado = pd.DataFrame()
        df_mapeado["FECHA"] = df["FECHA"]
        df_mapeado["BANCO / EFECTIVO"] = nombre_hoja
        df_mapeado["DESCRIPCION"] = df["DESCRIPCION"] if "DESCRIPCION" in df.columns else ""
        df_mapeado["CATEGORIA"] = categoria
        df_mapeado["MONEDA"] = moneda
        df_mapeado["DEBITO"] = debito_orig
        df_mapeado["CREDITO"] = credito_orig

        if moneda == "USD":
            df_mapeado["DEBITO $"] = df_mapeado["DEBITO"]
            df_mapeado["CREDITO $"] = df_mapeado["CREDITO"]
        else:
            df_mapeado["DEBITO $"] = df["DEBITO $"] if "DEBITO $" in df.columns else 0
            df_mapeado["CREDITO $"] = df["CREDITO $"] if "CREDITO $" in df.columns else 0

        bloques_consolidados.append(df_mapeado)

# 2. Consolidación y Limpieza Final del Maestro
if bloques_consolidados:
    print("\n🔄 Unificando todos los bloques de datos...")
    df_maestro = pd.concat(bloques_consolidados, ignore_index=True)

    # Limpieza de textos y nulos
    df_maestro["DESCRIPCION"] = df_maestro["DESCRIPCION"].fillna("").astype(str).str.strip()
    df_maestro["CATEGORIA"] = df_maestro["CATEGORIA"].fillna("SIN CATEGORÍA").astype(str).str.strip()
    
    # Estandarizar columnas numéricas
    columnas_numericas = ["DEBITO", "CREDITO", "DEBITO $", "CREDITO $"]
    for col in columnas_numericas:
        df_maestro[col] = pd.to_numeric(df_maestro[col], errors="coerce").fillna(0)

    # Convertir FECHA y descartar nulos
    df_maestro["FECHA"] = pd.to_datetime(df_maestro["FECHA"], errors="coerce")
    df_maestro = df_maestro[df_maestro["FECHA"].notna()]

    # Filtrar saldos iniciales o anteriores
    palabras_filtro = "SALDO INICIAL|SALDO ANTERIOR|SALDO"
    df_maestro = df_maestro[
        ~df_maestro["DESCRIPCION"].str.upper().str.contains(palabras_filtro, na=False) &
        ~df_maestro["CATEGORIA"].str.upper().str.contains(palabras_filtro, na=False)
    ]

    # Eliminar líneas vacías sin movimientos reales
    df_maestro = df_maestro[
        (df_maestro["DEBITO"] != 0) | 
        (df_maestro["CREDITO"] != 0) | 
        (df_maestro["DEBITO $"] != 0) | 
        (df_maestro["CREDITO $"] != 0)
    ]

    # Ordenar cronológicamente
    df_maestro = df_maestro.sort_values(by="FECHA", ascending=True).reset_index(drop=True)
    df_maestro["FECHA"] = df_maestro["FECHA"].dt.strftime("%Y-%m-%d")

    # Reordenar al formato definitivo
    columnas_finales = ["FECHA", "BANCO / EFECTIVO", "DESCRIPCION", "CATEGORIA", "MONEDA", "DEBITO", "CREDITO", "DEBITO $", "CREDITO $"]
    df_maestro = df_maestro[columnas_finales]

    # 3. Guardar en el archivo destino
    print(f"💾 Guardando libro unificado en: '{archivo_destino}'...")
    with pd.ExcelWriter(archivo_destino, engine="openpyxl") as writer:
        df_maestro.to_excel(writer, sheet_name="CONSOLIDADO MAESTRO", index=False)
        
        for nombre_hoja in todas_las_pestanas:
            if "CONSOLIDADO" not in nombre_hoja.upper():
                df_original = pd.read_excel(excel_file, sheet_name=nombre_hoja)
                df_original.to_excel(writer, sheet_name=nombre_hoja, index=False)

    print("\n✨ ¡Proceso completado con éxito sin errores! ✨")
    print(f"📊 Se han unificado un total de {len(df_maestro)} transacciones reales.")
else:
    print("\n❌ Error: No se pudo extraer información estructurada de ninguna pestaña.")
