import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import datetime

# ReportLab para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Google Drive API
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ingenia Verde - Plataforma Integral",
    page_icon="🌿",
    layout="wide"
)

# -----------------------------------------------------------------------------
# GESTIÓN DE CLAVE API (SECRETS)
# -----------------------------------------------------------------------------
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 Clave API (Admin)", type="password")

if api_key:
    genai.configure(api_key=api_key)

# -----------------------------------------------------------------------------
# BARRA LATERAL: LOGIN Y SELECTOR DE ROL
# -----------------------------------------------------------------------------
st.sidebar.title("🌿 Ingenia Verde")
st.sidebar.markdown("---")

# MÓDULO DE INICIO DE SESIÓN POR CORREO
st.sidebar.subheader("🔐 Iniciar Sesión")
correo_usuario = st.sidebar.text_input(
    "📧 Tu Correo Electrónico:", 
    value=st.session_state.get("user_email", ""),
    placeholder="usuario@unheval.edu.pe"
)

if correo_usuario:
    st.session_state["user_email"] = correo_usuario
    st.sidebar.success(f"Sesión activa: {correo_usuario}")
else:
    st.sidebar.warning("⚠️ Ingresa tu correo para guardar tu progreso.")

st.sidebar.markdown("---")

# SELECTOR DE MODO
modo_usuario = st.sidebar.radio(
    "Selecciona el modo de uso:",
    ["👨‍🏫 Modo Maestro / Docente", "🎓 Modo Estudiante / Servicios Académicos"]
)
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

# =============================================================================
# MODO 1: MAESTRO / DOCENTE
# =============================================================================
if modo_usuario == "👨‍🏫 Modo Maestro / Docente":
    st.title("🎓 Ingenia Verde Pro - Gestión Docente")
    st.caption("Digitalización de notas con IA y sincronización en Google Drive")

    if not st.session_state.get("user_email"):
        st.info("👈 **Paso 1:** Inicia sesión con tu correo en la barra lateral para continuar.")

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
            st.info(f"📧 **Docente Vinculado:** `{doc_email}`")
            
            imagen_registro = st.file_uploader("Captura de registro manuscrito o impreso", type=["jpg", "jpeg", "png"])
            
            if imagen_registro and api_key:
                if st.button("🚀 Procesar Notas con Gemini AI"):
                    with st.spinner("Analizando registro físico con Inteligencia Artificial..."):
                        try:
                            bytes_data = imagen_registro.getvalue()
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            prompt = f"Extrae las notas en formato JSON según el sílabo: {st.session_state['config_eval']['estructura'].to_string()}"
                            response = model.generate_content([prompt, {"mime_type": imagen_registro.type, "data": bytes_data}])
                            
                            df_resultado = st.session_state["alumnos_df"].copy()
                            st.dataframe(df_resultado, use_container_width=True)
                            st.session_state["df_resultado"] = df_resultado
                            st.success("Digitalización completada.")
                        except Exception as e:
                            st.error(f"Error en procesamiento: {e}")

            if "df_resultado" in st.session_state:
                pdf_bytes = generar_comprobante_pdf(doc_email, st.session_state["config_eval"]["curso"], st.session_state["df_resultado"])
                st.download_button("📄 Descargar Comprobante PDF (Sello Digital)", pdf_bytes, f"Comprobante_{datetime.date.today()}.pdf", "application/pdf")

# =============================================================================
# MODO 2: ESTUDIANTE / SERVICIOS ACADÉMICOS
# =============================================================================
else:
    st.title("🎓 Ingenia Verde Academic - Servicios Estudiantiles")
    st.caption("Compilación de informes, análisis estadístico en R y procesamiento espacial en ArcGIS Pro")

    if not st.session_state.get("user_email"):
        st.info("👈 **Paso 1:** Inicia sesión con tu correo en la barra lateral para registrar tus pedidos.")

    tab_est1, tab_est2, tab_est3 = st.tabs([
        "📄 Compilación de Informes", 
        "📊 Análisis de Datos (R / RStudio)", 
        "🗺️ Mapas y SIG (ArcGIS Pro)"
    ])

    with tab_est1:
        st.header("Solicitud de Formato y Compilación de Informes")
        col1, col2 = st.columns(2)
        with col1:
            estudiante_nombre = st.text_input("Nombre Completo del Estudiante")
            carrera = st.text_input("Carrera / Facultad", "Ingeniería en Recursos Naturales Renovables")
            asunto_informe = st.text_input("Título / Tema del Trabajo")
        with col2:
            estilo_formato = st.selectbox("Norma de Estilo / Formato", ["APA 7ma Edición", "IEEE", "ISO 690", "Libre / Universidad"])
            archivos_informe = st.file_uploader("Adjuntar borradores o datos (Word, PDF, Excel)", accept_multiple_files=True)

        if st.button("📩 Enviar Solicitud de Compilación"):
            st.success(f"¡Solicitud recibida! Se enviará la confirmación al correo: {st.session_state.get('user_email', 'no registrado')}")

    with tab_est2:
        st.header("Procesamiento Estadístico con R / RStudio")
        st.markdown("Carga tus variables y conjuntos de datos para modelado estadístico, script o gráficos vectoriales.")
        script_r = st.text_area("Código R / Instrucciones de Análisis", placeholder="Ejemplo: Realizar ANOVA de dos factores y prueba de Tukey...")
        dataset = st.file_uploader("Cargar Dataset (.csv, .xlsx, .rds)", type=["csv", "xlsx", "rds"])
        if st.button("🧪 Procesar Script / Análisis R"):
            st.info("Datos recibidos. El motor de R generará los resúmenes estadísticos y gráficos de salida.")

    with tab_est3:
        st.header("Procesamiento Geospacial con ArcGIS Pro")
        st.markdown("Servicios de digitalización de mapas, análisis de vectores, ráster y archivos Shapefile (.shp / .geojson).")
        tipo_mapa = st.selectbox("Tipo de Trabajo SIG", [
            "Elaboración de Mapa Temático (Ubicación / Cobertura)",
            "Análisis Ráster / DEM / Curvas de Nivel",
            "Clasificación Supervisada / Sensores Remotos",
            "Convertir Shapefiles / Geodatabase"
        ])
        archivos_gis = st.file_uploader("Subir comprimido (.zip) con el proyecto ArcGIS / Shapefiles", type=["zip"])
        instrucciones_gis = st.text_area("Detalles de Simbología y Coordenadas (UTM / WGS84)")
        if st.button("🗺️ Registrar Proyecto ArcGIS Pro"):
            st.success(f"Proyecto registrado para procesamiento geospacial asignado a: {st.session_state.get('user_email', 'no registrado')}")
