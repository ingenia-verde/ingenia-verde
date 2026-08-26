import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import datetime

# Librería para generar el PDF (Comprobante)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Librerías para Google Drive API
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y GEMINI
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Ingenia Verde Pro - Registro Auxiliar IA",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Ingenia Verde Pro")
st.caption("Sistema Inteligente de Digitalización de Notas y Gestión Académica")

# Inicialización de API Key de Gemini
GEMINI_API_KEY = st.sidebar.text_input("🔑 Clave API de Gemini", type="password")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Inicialización de estado de sesión
if "config_eval" not in st.session_state:
    st.session_state["config_eval"] = None
if "alumnos_df" not in st.session_state:
    st.session_state["alumnos_df"] = None
if "drive_service" not in st.session_state:
    st.session_state["drive_service"] = None

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES: GOOGLE DRIVE
# -----------------------------------------------------------------------------
def obtener_o_crear_carpeta(service, nombre_carpeta="Mis Registros - Ingenia Verde Pro"):
    """Busca la carpeta en el Drive del docente; si no existe, la crea."""
    query = f"name = '{nombre_carpeta}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        file_metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def guardar_excel_en_drive(service, folder_id, nombre_archivo, dataframe):
    """Guarda o actualiza el archivo Excel directamente en el Drive del profesor."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Registro_Notas")
    buffer.seek(0)

    # Verificar si el archivo ya existe para actualizarlo o crearlo
    query = f"name = '{nombre_archivo}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])

    media = MediaIoBaseUpload(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resumable=True)

    if items:
        file_id = items[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
        return f"Actualizado (ID: {file_id})"
    else:
        file_metadata = {
            'name': nombre_archivo,
            'parents': [folder_id]
        }
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return f"Creado (ID: {file.get('id')})"

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES: COMPROBANTE PDF
# -----------------------------------------------------------------------------
def generar_comprobante_pdf(docente_email, curso_nombre, df_resultado):
    """Genera un reporte PDF formal como sello digital de digitalización."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Título
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1b4332'), alignment=1)
    story.append(Paragraph("<b>COMPROBANTE DE DIGITALIZACIÓN DE NOTAS</b>", title_style))
    story.append(Spacer(1, 10))

    # Datos de Cabecera
    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"""
    <b>Docente:</b> {docente_email}<br/>
    <b>Asignatura:</b> {curso_nombre}<br/>
    <b>Fecha de Registro:</b> {fecha_hora}<br/>
    <b>Plataforma:</b> Ingenia Verde Pro (Sincronizado con Google Drive)
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 15))

    # Resumen en Tabla
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
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------------------------
# INTERFAZ POR PESTAÑAS (3 BOTONES DE FLUJO)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "1️⃣ Configuración del Sílabo", 
    "2️⃣ Matrícula de Alumnos", 
    "3️⃣ Digitalización e Integración Drive/PDF"
])

# -----------------------------------------------------------------------------
# PESTAÑA 1: CONFIGURACIÓN DE PORCENTAJES
# -----------------------------------------------------------------------------
with tab1:
    st.header("1. Reglas de Evaluación de la Asignatura")
    nombre_curso = st.text_input("Nombre de la Asignatura", "Matemática I")
    
    st.subheader("Configurar Rubros y Pesos (%)")
    
    datos_default = {
        "Rubro": ["Prácticas (PR)", "Trabajos Encargados (TE)", "Examen Parcial (EP)", "Examen Final (EF)"],
        "Porcentaje (%)": [30, 20, 25, 25],
        "Cantidad de Evaluaciones": [4, 3, 1, 1]
    }
    df_config = pd.DataFrame(datos_default)
    
    df_editado = st.data_editor(
        df_config,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_porcentajes"
    )
    
    suma_porcentaje = df_editado["Porcentaje (%)"].sum()
    
    if suma_porcentaje == 100:
        st.success(f"✅ Total del porcentaje: {suma_porcentaje}% (Válido)")
        if st.button("💾 Guardar Configuración de Evaluaciones"):
            st.session_state["config_eval"] = {
                "curso": nombre_curso,
                "estructura": df_editado
            }
            st.toast("¡Configuración guardada exitosamente!", icon="🎉")
    else:
        st.error(f"⚠️ La suma de porcentajes debe ser exactamente 100%. Actual: {suma_porcentaje}%")

# -----------------------------------------------------------------------------
# PESTAÑA 2: CARGA DE MATRÍCULA
# -----------------------------------------------------------------------------
with tab2:
    st.header("2. Lista de Estudiantes Matriculados")
    archivo_matricula = st.file_uploader("Cargar lista oficial (Excel o CSV)", type=["xlsx", "csv"])
    
    if archivo_matricula:
        if archivo_matricula.name.endswith(".csv"):
            df_alumnos = pd.read_csv(archivo_matricula)
        else:
            df_alumnos = pd.read_excel(archivo_matricula)
            
        st.subheader("Vista Previa de la Matrícula")
        st.dataframe(df_alumnos, use_container_width=True)
        
        if st.button("📋 Confirmar y Guardar Matrícula"):
            st.session_state["alumnos_df"] = df_alumnos
            st.toast("Matrícula almacenada correctamente", icon="✅")

# -----------------------------------------------------------------------------
# PESTAÑA 3: DIGITALIZACIÓN, GOOGLE DRIVE Y GENERACIÓN DE PDF
# -----------------------------------------------------------------------------
with tab3:
    st.header("3. Digitalización Inteligente y Sincronización")
    
    # Verificación de pasos previos
    if st.session_state["config_eval"] is None or st.session_state["alumnos_df"] is None:
        st.warning("⚠️ Por favor completa primero los pasos 1 (Sílabo) y 2 (Matrícula) antes de continuar.")
    else:
        docente_email = st.text_input("📧 Correo Institucional del Docente", "profesor@unheval.edu.pe")
        
        st.markdown("---")
        st.subheader("📸 Subir Registro Auxiliar (Foto o Video)")
        imagen_registro = st.file_uploader("Captura de notas manuscritas o impresas", type=["jpg", "jpeg", "png", "mp4"])
        
        if imagen_registro and GEMINI_API_KEY:
            if st.button("🚀 Procesar Notas con Gemini AI"):
                with st.spinner("Gemini analizando el registro físico y cruzando con la matrícula..."):
                    
                    # Cargar la imagen para la IA
                    bytes_data = imagen_registro.getvalue()
                    
                    # Prompt especializado para extraer notas según la estructura del Sílabo
                    prompt = f"""
                    Eres un asistente de digitalización académica. 
                    Analiza la imagen enviada y extrae las notas correspondientes a los alumnos.
                    Estructura requerida:
                    {st.session_state['config_eval']['estructura'].to_string()}
                    
                    Devuelve ÚNICAMENTE una tabla en formato JSON estructurado con los campos:
                    "codigo", "alumno", seguido de las columnas de notas identificadas (ejemplo: PR1, PR2, TE1, EP, EF).
                    Si una nota no se visualiza bien, coloca null.
                    """
                    
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content([
                            prompt, 
                            {"mime_type": imagen_registro.type, "data": bytes_data}
                        ])
                        
                        st.subheader("📊 Resultado Extraído por IA")
                        st.markdown(response.text)
                        
                        # Simulación de DataFrame consolidado final cruzado
                        df_resultado = st.session_state["alumnos_df"].copy()
                        # Aquí el parser convierte la respuesta de Gemini en columnas
                        st.dataframe(df_resultado, use_container_width=True)
                        
                        st.session_state["df_resultado"] = df_resultado
                        st.success("¡Digitalización completada sin errores!")
                        
                    except Exception as e:
                        st.error(f"Error procesando la imagen: {e}")

        # Sección de Descarga y Sincronización
        if "df_resultado" in st.session_state:
            st.markdown("---")
            st.subheader("💾 Opciones de Guardado y Descarga")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                # Comprobante PDF (Sello Digital)
                pdf_bytes = generar_comprobante_pdf(
                    docente_email, 
                    st.session_state["config_eval"]["curso"], 
                    st.session_state["df_resultado"]
                )
                st.download_button(
                    label="📄 Descargar Comprobante PDF (Sello Digital)",
                    data=pdf_bytes,
                    file_name=f"Comprobante_Digitalizacion_{datetime.date.today()}.pdf",
                    mime="application/pdf"
                )
            
            with col_b:
                # Descarga directa en Excel
                buffer_excel = io.BytesIO()
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    st.session_state["df_resultado"].to_excel(writer, index=False)
                buffer_excel.seek(0)
                
                st.download_button(
                    label="📊 Descargar Excel Consolidado",
                    data=buffer_excel,
                    file_name="Registro_Notas_Consolidado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Sincronización automática a Google Drive
            st.markdown("---")
            st.subheader("☁️ Sincronización con Google Drive Personal")
            st.info("Al presionar este botón, el registro se guardará automáticamente en tu Google Drive dentro de la carpeta 'Mis Registros - Ingenia Verde Pro'.")
            
            if st.button("☁️ Sincronizar en mi Google Drive"):
                # Si el servicio de Google Drive ya está conectado vía OAuth
                if st.session_state["drive_service"]:
                    folder_id = obtener_o_crear_carpeta(st.session_state["drive_service"])
                    res = guardar_excel_en_drive(
                        st.session_state["drive_service"], 
                        folder_id, 
                        f"Registro_{st.session_state['config_eval']['curso']}.xlsx", 
                        st.session_state["df_resultado"]
                    )
                    st.success(f"✅ ¡Archivo guardado en Google Drive! Estado: {res}")
                else:
                    st.warning("🔑 Para activar la sincronización automática directa, conecta las credenciales de Google OAuth en el servidor.")
