import streamlit as st
import pandas as pd
import re
import unicodedata
import io
import json
from google import genai
from PIL import Image

# Tu clave de API predeterminada de Gemini
API_KEY_PREDETERMINADA = "AQ.AB8NNGHT-53GflQdKC3V0bnAuNeUg_S2a16DTaoVSHWVXGNA"

# Configuración inicial de la página
st.set_page_config(page_title="Ingenia Verde Pro", page_icon="🌿", layout="wide")

# ==========================================
# BARRA LATERAL DE NAVEGACIÓN
# ==========================================
st.sidebar.title("🌿 Ingenia Verde Pro")
st.sidebar.caption("Plataforma de Herramientas IA & Procesamiento")

modulo = st.sidebar.radio(
    "Selecciona un módulo:",
    [
        "👨‍🏫 Digitación de Notas - Maestros RNR (Gratis / Beta)",
        "📊 Extractor & Limpiador SIG y R (Pro S/ 5.00)"
    ]
)

# ==========================================
# MÓDULO 1: SECCIÓN MAESTROS RNR (GRATIS)
# ==========================================
if modulo == "👨‍🏫 Digitación de Notas - Maestros RNR (Gratis / Beta)":
    st.title("📋 Digitación Inteligente de Notas - Docentes RNR")
    st.write("Herramienta automatizada para la estructuración y digitación de registros académicos.")
    st.success("🎉 ¡Acceso de prueba gratuito activado para la Facultad de RNR!")

    tab1, tab2, tab3 = st.tabs(["1️⃣ Cargar Sílabo", "2️⃣ Cargar Matrícula", "3️⃣ Foto/Video a Excel"])

    with tab1:
        st.subheader("Botón 1: Estructurar Sílabo")
        st.write("Sube el sílabo del curso (PDF) para extraer automáticamente las ponderaciones y fórmula de evaluación.")
        silabo_file = st.file_uploader("Sube tu sílabo en PDF", type=["pdf"], key="silabo_uploader")
        
        if silabo_file:
            if st.button("Procesar Sílabo con IA"):
                with st.spinner("Analizando el documento con Gemini Visión..."):
                    try:
                        client = genai.Client(api_key=API_KEY_PREDETERMINADA)
                        bytes_data = silabo_file.read()
                        
                        prompt = (
                            "Analiza este sílabo universitario de la Facultad de Recursos Naturales Renovables. "
                            "Extrae el nombre del curso, el sistema de evaluación (rubros/criterios con sus pesos) "
                            "y la fórmula final para el promedio. "
                            "Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:\n"
                            "{\n"
                            '  "curso": "Nombre del Curso",\n'
                            '  "evaluaciones": [\n'
                            '    {"criterio": "Examen Parcial", "peso_porcentaje": 30},\n'
                            '    {"criterio": "Practicas de Campo", "peso_porcentaje": 20}\n'
                            '  ],\n'
                            '  "formula": "PF = (EP*0.30) + (PC*0.20)..."\n'
                            "}"
                        )
                        
                        part = genai.types.Part.from_bytes(data=bytes_data, mime_type="application/pdf")
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[part, prompt]
                        )
                        
                        texto_resp = response.text.strip()
                        if texto_resp.startswith("```json"): texto_resp = texto_resp[7:]
                        if texto_resp.endswith("```"): texto_resp = texto_resp[:-3]
                        
                        datos_silabo = json.loads(texto_resp.strip())
                        st.session_state["datos_silabo"] = datos_silabo
                        
                        st.success(f"¡Sílabo procesado exitosamente: **{datos_silabo.get('curso', 'Curso Detectado')}**!")
                        
                        df_evals = pd.DataFrame(datos_silabo.get("evaluaciones", []))
                        st.subheader("📊 Ponderaciones del Curso")
                        st.dataframe(df_evals, use_container_width=True)
                        st.info(f"📐 **Fórmula de Evaluación:** {datos_silabo.get('formula', 'No especificada')}")
                        
                    except Exception as e:
                        st.error(f"Error al analizar el PDF del sílabo: {e}")

    with tab2:
        st.subheader("Subir lista de alumnos matriculados")
        lista_file = st.file_uploader("Sube la nómina oficial", type=["pdf", "xlsx", "csv"], key="lista_uploader")
        if lista_file:
            if st.button("Poblar Estudiantes"):
                st.info("Generando lista ordenada...")

    with tab3:
        st.subheader("Subir Foto/Video del registro auxiliar")
        foto_registro = st.file_uploader("Sube la imagen o video del registro", type=["jpg", "png", "jpeg", "mp4"], key="registro_uploader")
        if foto_registro:
            if st.button("Procesar Notas con IA"):
                st.info("Digitalizando calificaciones...")


# ==========================================
# MÓDULO 2: EXTRACTOR PRO (REQUIERE SUSCRIPCIÓN)
# ==========================================
elif modulo == "📊 Extractor & Limpiador SIG y R (Pro S/ 5.00)":

    # Inicializar estado de acceso
    if "acceso_permitido" not in st.session_state:
        st.session_state.acceso_permitido = False

    # Lógica de verificación de pago
    if not st.session_state.acceso_permitido:
        st.title("🌿 Ingenia Verde Pro")
        st.subheader("Plataforma de Limpieza de Datos & Extracción con IA (SIG y R)")

        col1, col2 = st.columns(2)

        with col1:
            st.info("### Suscripción Mensual: S/ 5.00 / mes")
            st.write("Obtén acceso para procesar tus archivos de campo:")
            st.markdown("✅ **Limpieza automatizada para R y SIG** (Nombres de variables, nulos, etc.)")
            st.markdown("✅ **Extractor con IA de tablas desde fotos de libretas de campo**")
            st.markdown("✅ **Descarga ilimitada en formatos CSV y Excel (.xlsx)**")

            st.markdown("---")
            st.write("### Escanea el QR para yapear S/ 5.00")

            try:
                st.image("qr_yape.jpg", width=240, caption="Victor Kennedy Cayco Valdivia")
            except:
                st.warning("Sube el archivo 'qr_yape.jpg' a GitHub para visualizar el código QR.")

            st.write("Envía tu captura de pago para recibir tu contraseña.")

        with col2:
            st.write("### ¿Ya eres suscriptor?")
            clave_ingresada = st.text_input("Ingresa tu clave de acceso:", type="password")
            if st.button("Ingresar a la Plataforma"):
                if clave_ingresada == "Ingenia2025":
                    st.session_state.acceso_permitido = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Clave incorrecta. Si realizaste tu Yape, contáctanos para enviarte tu contraseña.")

    else:
        # --- CÓDIGO PRO PROCESADOR DE DATOS ---
        def limpiar_texto(texto):
            if not isinstance(texto, str):
                return str(texto)
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            texto = texto.lower().strip()
            texto = re.sub(r'[\s\W]+', '_', texto)
            return texto.strip('_')

        def procesar_dataframe(df):
            df_limpio = df.copy()
            df_limpio.columns = [limpiar_texto(col) for col in df_limpio.columns]
            df_limpio = df_limpio.dropna(how='all').dropna(how='all', axis=1)

            for col in df_limpio.select_dtypes(include=['object']).columns:
                df_limpio[col] = df_limpio[col].astype(str).str.strip()

            return df_limpio

        st.title("🌿 Ingenia Verde: Limpiador & Extractor de Datos SIG & R")
        st.write("Sube tu archivo de Excel o la foto de una libreta/tabla de campo para procesarlo al instante.")

        tab1, tab2 = st.tabs(["📁 Archivo Excel", "📷 Foto de Campo / Libreta"])

        df_final = None

        with tab1:
            archivo_excel = st.file_uploader("Elige tu archivo de Excel", type=["xlsx", "xls"], key="excel_uploader")
            if archivo_excel is not None:
                df_original = pd.read_excel(archivo_excel)
                df_final = procesar_dataframe(df_original)

        with tab2:
            st.write("**Extracción automática desde imagen**")
            api_key = st.text_input("Gemini API Key:", value=API_KEY_PREDETERMINADA, type="password", help="Clave configurada por defecto.")
            archivo_imagen = st.file_uploader("Sube una foto clara de tu libreta o tabla", type=["jpg", "jpeg", "png"], key="img_uploader")

            if archivo_imagen is not None:
                imagen = Image.open(archivo_imagen)
                st.image(imagen, caption="Imagen cargada", width=400)

                if st.button("📷 Extraer Tabla de la Foto"):
                    if not api_key:
                        st.error("Por favor ingresa tu API Key de Gemini para continuar.")
                    else:
                        with st.spinner("Analizando la imagen y procesando datos con IA..."):
                            try:
                                client = genai.Client(api_key=api_key)
                                prompt = (
                                    "Extrae toda la información tabular de esta imagen. "
                                    "Devuelve ÚNICAMENTE un objeto JSON con una clave 'datos' "
                                    "que contenga una lista de objetos, donde cada objeto represente una fila con sus columnas. "
                                    "Ejemplo: {\"datos\": [{\"punto\": 1, \"este\": 300557.8, \"norte\": 8897508.1}]}"
                                )
                                response = client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=[imagen, prompt]
                                )
                                texto_resp = response.text.strip()
                                if texto_resp.startswith("```json"):
                                    texto_resp = texto_resp[7:]
                                if texto_resp.endswith("```"):
                                    texto_resp = texto_resp[:-3]

                                texto_resp = texto_resp.strip()
                                datos_json = json.loads(texto_resp)
                                df_extraido = pd.DataFrame(datos_json.get("datos", []))

                                if not df_extraido.empty:
                                    df_final = procesar_dataframe(df_extraido)
                                    st.success("¡Tabla extraída y limpia con éxito desde la imagen!")
                                else:
                                    st.warning("No se pudo estructurar una tabla desde la imagen.")
                            except Exception as e:
                                st.error(f"Error al procesar la imagen: {e}")

        if df_final is not None:
            st.markdown("---")
            st.subheader("📊 Datos Procesados y Limpios")

            col1, col2, col3 = st.columns(3)
            col1.metric("Filas Útiles", df_final.shape[0])
            col2.metric("Columnas estandarizadas", df_final.shape[1])
            col3.metric("Celdas vacías/Nulas", int(df_final.isna().sum().sum()))

            st.dataframe(df_final, use_container_width=True)

            st.subheader("💾 Descargar Resultados")
            col_d1, col_d2 = st.columns(2)

            with col_d1:
                separador = st.radio("Delimitador para CSV:", (", (Coma - R/GIS)", "; (Punto y coma - Excel ES)"), index=0)
                sep_char = "," if separador == ", (Coma - R/GIS)" else ";"
                csv_data = df_final.to_csv(index=False, sep=sep_char).encode('utf-8-sig')

                st.download_button(
                    label="Descargar CSV Limpio",
                    data=csv_data,
                    file_name="datos_limpios_ingenia_verde.csv",
                    mime="text/csv"
                )

            with col_d2:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Datos_Limpios')
                excel_data = output.getvalue()

                st.download_button(
                    label="Descargar en Excel (.xlsx)",
                    data=excel_data,
                    file_name="datos_limpios_ingenia_verde.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
