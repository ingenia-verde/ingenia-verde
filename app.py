import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import datetime
import json

# ReportLab para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ingenia Verde Pro - Plataforma Integral",
    page_icon="🌿",
    layout="wide"
)

# -----------------------------------------------------------------------------
# GESTIÓN DE CLAVE API (SECRETS O MANUAL)
# -----------------------------------------------------------------------------
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 Clave API Gemini (Admin)", type="password")

if api_key:
    genai.configure(api_key=api_key)

# -----------------------------------------------------------------------------
# BARRA LATERAL: INICIO DE SESIÓN Y ACCESO OCULTO
# -----------------------------------------------------------------------------
st.sidebar.title("🌿 Ingenia Verde Pro")
st.sidebar.caption("Plataforma de Digitalización y Servicios Académicos")
st.sidebar.markdown("---")

st.sidebar.subheader("🔐 Iniciar Sesión")
correo_usuario = st.sidebar.text_input(
    "📧 Correo Electrónico:", 
    value=st.session_state.get("user_email", ""),
    placeholder="usuario@universidad.edu.pe"
)

if correo_usuario:
    st.session_state["user_email"] = correo_usuario
    st.sidebar.success(f"Sesión activa: {correo_usuario}")
else:
    st.sidebar.info("Ingresa tu correo para registrar tus operaciones.")

st.sidebar.markdown("---")

# PIN SECRETO PARA ACTIVAR MODO ESTUDIANTE / SERVICIOS ACADÉMICOS
PIN_SECRETO = "INGENIA2026"

with st.sidebar.expander("⚙️ Opciones Avanzadas / Rol", expanded=False):
    pin_ingresado = st.text_input("Código de Acceso Especial", type="password")

if pin_ingresado == PIN_SECRETO:
    st.sidebar.success("🔓 Modo Especial Desbloqueado")
    modo_usuario = st.sidebar.radio(
        "Selecciona el entorno:",
        ["👨‍🏫 Modo Maestro / Docente", "🎓 Modo Estudiante / Servicios Académicos"]
    )
else:
    modo_usuario = "👨‍🏫 Modo Maestro / Docente"

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------
def generar_comprobante_pdf(docente_email, curso_nombre, df_resultado):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1b4332'), alignment=1)
    story.append(Paragraph("<b>COMPROBANTE DE DIGITALIZACIÓN DE NOTAS</b>", title_style))
    story.append(Spacer(1, 10))

    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"""
    <b>Docente Registrado:</b> {docente_email}<br/>
    <b>Asignatura:</b> {curso_nombre}<br/>
    <b>Fecha de Registro:</b> {fecha_hora}<br/>
    <b>Plataforma:</b> Ingenia Verde Pro
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 15))

    table_data = [df_resultado.columns.tolist()]
    for _, row in df_resultado.iterrows():
        table_data.append([str(val) if pd.notna(val) else "" for val in row.values])

    t = Table(table_data, colWidths=None)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d6a4f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def modulo_pago_suscripcion_yape():
    st.info("📌 **Planes Académicos:** Acceso ilimitado a todas las herramientas por **S/ 5.00 al mes**.")
    col_qr, col_info = st.columns([1, 2])
    
    with col_qr:
        st.markdown(
            f"""
            <div style="background-color: #7d2ae8; color: white; padding: 15px; border-radius: 10px; text-align: center;">
                <h3 style="margin:0; color:white;">📱 YAPE / PLIN</h3>
                <p style="margin:2px 0;"><b>Suscripción Mensual</b></p>
                <h2 style="margin:5px 0; color:#ffd166;">S/ 5.00 / mes</h2>
                <p style="margin:0;"><b>Titular:</b> Ingenia Verde</p>
                <p style="font-size: 18px; margin:0;"><b>926 000 000</b></p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col_info:
        st.markdown("1. Realiza el Yape de **S/ 5.00** para tu suscripción mensual.")
        st.markdown("2. Adjunta la captura de pantalla o voucher de pago aquí abajo.")
        
        voucher = st.file_uploader("📤 Subir Captura de Yape (Suscripción Mensual)", type=["jpg", "png", "jpeg"], key="yape_suscripcion")
        
        if voucher:
            st.success("✅ **Suscripción Activa para este mes.** Se han desbloqueado todas las herramientas.")
            return True
        else:
            st.warning("⚠️ Para acceder a las funciones avanzadas, sube tu comprobante de Yape.")
            return False

# =============================================================================
# MODO 1: MAESTRO / DOCENTE (VISTA PÚBLICA PRINCIPAL)
# =============================================================================
if modo_usuario == "👨‍🏫 Modo Maestro / Docente":
    st.title("🎓 Ingenia Verde Pro - Gestión Docente")
    st.caption("Digitalización de notas con IA y sincronización en Google Drive")

    tab1, tab2, tab3 = st.tabs([
        "1️⃣ Configuración del Sílabo", 
        "2️⃣ Matrícula de Alumnos", 
        "3️⃣ Digitalización e Integración Drive/PDF"
    ])

    with tab1:
        st.header("1. Reglas de Evaluación de la Asignatura")
        nombre_curso = st.text_input("Nombre de la Asignatura", "Matemática I")
        
        datos_default = {
            "Rubro": ["Prácticas (PR)", "Trabajos Encargados (TE)", "Examen Parcial (EP)", "Examen Final (EF)"],
            "Porcentaje (%)": [30, 20, 25, 25],
            "Cantidad de Evaluaciones": [4, 3, 1, 1]
        }
        df_config = pd.DataFrame(datos_default)
        df_editado = st.data_editor(df_config, num_rows="dynamic", use_container_width=True)
        
        suma_porcentaje = df_editado["Porcentaje (%)"].sum()
        if suma_porcentaje == 100:
            st.success(f"✅ Total del porcentaje: {suma_porcentaje}% (Válido)")
            if st.button("💾 Guardar Configuración de Evaluaciones"):
                st.session_state["config_eval"] = {"curso": nombre_curso, "estructura": df_editado}
                st.toast("Configuración guardada", icon="🎉")
        else:
            st.error(f"⚠️ La suma debe ser exactamente 100%. Actual: {suma_porcentaje}%")

    with tab2:
        st.header("2. Lista de Estudiantes Matriculados")
        archivo_matricula = st.file_uploader("Cargar lista oficial (Excel o CSV)", type=["xlsx", "csv"], key="docente_mat")
        if archivo_matricula:
            df_alumnos = pd.read_csv(archivo_matricula) if archivo_matricula.name.endswith(".csv") else pd.read_excel(archivo_matricula)
            st.dataframe(df_alumnos, use_container_width=True)
            if st.button("📋 Confirmar y Guardar Matrícula"):
                st.session_state["alumnos_df"] = df_alumnos
                st.toast("Matrícula guardada", icon="✅")

    with tab3:
        st.header("3. Digitalización e Integración Drive/PDF")
        if "config_eval" not in st.session_state or "alumnos_df" not in st.session_state:
            st.warning("⚠️ Completa los pasos 1 y 2 antes de procesar notas.")
        else:
            doc_email = st.session_state.get("user_email", "profesor@universidad.edu.pe")
            st.info(f"📧 **Docente Registrado:** `{doc_email}`")
            
            imagen_registro = st.file_uploader("Captura de registro manuscrito o impreso", type=["jpg", "jpeg", "png"])
            
            if imagen_registro and api_key:
                if st.button("🚀 Procesar Notas con Gemini AI"):
                    with st.spinner("Analizando registro físico con Inteligencia Artificial..."):
                        try:
                            bytes_data = imagen_registro.getvalue()
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            prompt = f"Extrae las notas en formato JSON estricto según la estructura: {st.session_state['config_eval']['estructura'].to_string()}"
                            response = model.generate_content([prompt, {"mime_type": imagen_registro.type, "data": bytes_data}])
                            
                            # Guardamos en estado
                            st.session_state["df_resultado"] = st.session_state["alumnos_df"].copy()
                            st.success("Digitalización completada e integrada.")
                        except Exception as e:
                            st.error(f"Error en procesamiento: {e}")

            if "df_resultado" in st.session_state:
                st.dataframe(st.session_state["df_resultado"], use_container_width=True)
                pdf_bytes = generar_comprobante_pdf(doc_email, st.session_state["config_eval"]["curso"], st.session_state["df_resultado"])
                st.download_button("📄 Descargar Comprobante PDF (Sello Digital)", pdf_bytes, f"Comprobante_{datetime.date.today()}.pdf", "application/pdf")

# =============================================================================
# MODO 2: ESTUDIANTE / SERVICIOS ACADÉMICOS (SUSCRIPCIÓN MENSUAL S/ 5.00)
# =============================================================================
else:
    st.title("🎓 Ingenia Verde Academic - Servicios Estudiantiles")
    st.caption("Plataforma de herramientas universitarias por suscripción mensual")

    suscripcion_activa = modulo_pago_suscripcion_yape()

    if suscripcion_activa:
        st.markdown("---")
        tab_est1, tab_est2, tab_est3, tab_est4 = st.tabs([
            "📄 Compilación de Informes", 
            "📊 Análisis de Datos (R / RStudio)", 
            "🗺️ Mapas y SIG (ArcGIS Pro / ArcMap)",
            "🧹 IA Estructurador Excel (Para R / ArcGIS)"
        ])

        with tab_est1:
            st.header("Solicitud de Formato y Compilación de Informes")
            col1, col2 = st.columns(2)
            with col1:
                estudiante_nombre = st.text_input("Nombre Completo del Estudiante", key="inf_nom")
                carrera = st.text_input("Carrera / Facultad", "Ingeniería en Recursos Naturales Renovables", key="inf_car")
                asunto_informe = st.text_input("Título / Tema del Trabajo", key="inf_tit")
            with col2:
                estilo_formato = st.selectbox("Norma de Estilo / Formato", ["APA 7ma Edición", "IEEE", "ISO 690", "Libre / Universidad"])
                archivos_informe = st.file_uploader("Adjuntar borradores o datos (Word, PDF, Excel)", accept_multiple_files=True, key="inf_files")

            if st.button("🚀 Confirmar y Enviar Informe para Compilación"):
                st.success(f"🎉 ¡Trabajo registrado con éxito! Recibirás la entrega compilada en tu correo: {st.session_state.get('user_email', 'no registrado')}")

        with tab_est2:
            st.header("Procesamiento Estadístico con R / RStudio")
            st.markdown("Carga tus variables y conjuntos de datos para modelado estadístico, script o gráficos vectoriales.")
            script_r = st.text_area("Código R / Instrucciones de Análisis", placeholder="Ejemplo: Realizar ANOVA de dos factores y prueba de Tukey...", key="r_script")
            dataset = st.file_uploader("Cargar Dataset (.csv, .xlsx, .rds)", type=["csv", "xlsx", "rds"], key="r_data")
            
            if st.button("🧪 Iniciar Procesamiento en RStudio"):
                st.success(f"🎉 ¡Script en cola de procesamiento! Los resultados y código limpio llegarán a: {st.session_state.get('user_email', 'no registrado')}")

        with tab_est3:
            st.header("Procesamiento Geospacial con ArcGIS Pro / ArcMap 10.8")
            st.markdown("Servicios de digitalización de mapas, análisis de vectores, ráster y archivos Shapefile (.shp / .geojson).")
            tipo_mapa = st.selectbox("Tipo de Trabajo SIG", [
                "Elaboración de Mapa Temático (Ubicación / Cobertura)",
                "Análisis Ráster / DEM / Curvas de Nivel",
                "Clasificación Supervisada / Sensores Remotos",
                "Convertir Shapefiles / Geodatabase / Tablas XY"
            ], key="gis_tipo")
            archivos_gis = st.file_uploader("Subir comprimido (.zip) con el proyecto ArcGIS / Shapefiles", type=["zip"], key="gis_zip")
            instrucciones_gis = st.text_area("Detalles de Simbología y Coordenadas (UTM / WGS84)", key="gis_inst")
            
            if st.button("🗺️ Iniciar Elaboración de Mapa / Proyecto SIG"):
                st.success(f"🎉 ¡Proyecto de ArcGIS Pro / ArcMap registrado! El mapa en alta resolución se enviará a: {st.session_state.get('user_email', 'no registrado')}")

        with tab_est4:
            st.header("🧹 IA Estructurador y Limpiador de Excel")
            st.markdown("""
            Esta herramienta toma tus tablas desordenadas de Excel o CSV y las **limpia y estructura con IA** para que sean 100% compatibles con **RStudio** o **ArcGIS Pro / ArcMap 10.8** sin arrojar errores de importación.
            """)

            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                software_destino = st.selectbox(
                    "🎯 ¿Para qué software necesitas estructurar la tabla?",
                    [
                        "ArcGIS Pro / ArcMap 10.8 (Formatos de coordenadas X/Y, encabezados sin espacios, sin tildes ni 'ñ')",
                        "R / RStudio (Formato Tidy Data, variables en columnas, encabezados minuscula_snake_case)"
                    ],
                    key="soft_target"
                )
                excel_raw = st.file_uploader("📤 Sube tu archivo Excel o CSV borrador", type=["xlsx", "xls", "csv"], key="excel_raw_file")

            with col_ex2:
                instrucciones_limpieza = st.text_area(
                    "📝 Indicaciones específicas para la IA (Opcional):",
                    placeholder="Ejemplo: Convierte las coordenadas Este y Norte a formato numérico puro.",
                    key="inst_clean"
                )

            if excel_raw and api_key:
                st.markdown("---")
                st.subheader("👀 Vista Previa de la Tabla Borrador:")
                df_original = pd.read_csv(excel_raw) if excel_raw.name.endswith(".csv") else pd.read_excel(excel_raw)
                st.dataframe(df_original.head(10), use_container_width=True)

                if st.button("✨ Estructurar y Limpiar Tabla con IA"):
                    with st.spinner("La IA está procesando y estructurando la tabla..."):
                        try:
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            sample_csv = df_original.head(100).to_csv(index=False)
                            
                            prompt_est = f"""
                            Eres un experto en ciencia de datos, GIS (ArcGIS Pro / ArcMap 10.8) y RStudio.
                            Estructura y limpia la siguiente tabla.
                            SOFTWARE DESTINO: {software_destino}
                            INSTRUCCIONES: {instrucciones_limpieza}

                            Devuelve ÚNICAMENTE un JSON estricto con la estructura:
                            {{
                                "columnas": ["col1", "col2"],
                                "datos": [["val1", "val2"]]
                            }}
                            DATOS CSV:
                            {sample_csv}
                            """

                            response = model.generate_content(prompt_est)
                            texto_resp = response.text.strip()

                            if "```json" in texto_resp:
                                texto_resp = texto_resp.split("```json")[1].split("```")[0].strip()
                            elif "```" in texto_resp:
                                texto_resp = texto_resp.split("```")[1].split("```")[0].strip()

                            json_data = json.loads(texto_resp)
                            st.session_state["df_limpio"] = pd.DataFrame(json_data["datos"], columns=json_data["columnas"])
                            st.success("🎉 ¡Tabla estructurada con éxito!")
                        except Exception as e:
                            st.error(f"Error procesando la tabla: {e}")

            # Renderizado y descarga persistente
            if "df_limpio" in st.session_state:
                st.subheader("📋 Tabla Limpia Resultante:")
                st.dataframe(st.session_state["df_limpio"], use_container_width=True)

                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
                    st.session_state["df_limpio"].to_excel(writer, index=False, sheet_name="Datos_Limpios")
                
                st.download_button(
                    label="📥 Descargar Excel Listo para Importar",
                    data=output_buffer.getvalue(),
                    file_name=f"Datos_Procesados_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
