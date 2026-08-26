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

# Claves de acceso privadas
CLAVE_DOCENTE = "Docente2025"  # Clave de acceso privada para docentes y para ti
CLAVE_PRO = "Ingenia2025"       # Clave de acceso para la versión PRO

# Función auxiliar segura para extraer JSON de la respuesta de Gemini
def limpiar_json(texto):
    texto = texto.strip()
    if "```" in texto:
        bloques = texto.split("```")
        for b in bloques:
            b = b.strip()
            if b.startswith("json"):
                b = b[4:].strip()
            if b.startswith("{") or b.startswith("["):
                return b
    return texto

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
# MÓDULO 1: SECCIÓN MAESTROS RNR (ACCESO PRIVADO / DOCENTES)
# ==========================================
if modulo == "👨‍🏫 Digitación de Notas - Maestros RNR (Gratis / Beta)":
    st.title("📋 Digitación Inteligente de Notas - Docentes RNR")
    st.caption("Acceso exclusivo para docentes autorizados y administración.")
    
    # Control de acceso privado para docentes
    if "docente_autorizado" not in st.session_state:
        st.session_state.docente_autorizado = False

    if not st.session_state.docente_autorizado:
        st.info("🔒 **Módulo Privado de Gestión Académica**")
        st.write("Ingresa la clave de acceso docente otorgada para ingresar:")
        
        clave_docente_ingresada = st.text_input("Clave de acceso docente:", type="password", key="clave_docente_input")
        if st.button("Ingresar al Panel Docente"):
            if clave_docente_ingresada == CLAVE_DOCENTE:
                st.session_state.docente_autorizado = True
                st.success("¡Acceso concedido!")
                st.rerun()
            else:
                st.error("Clave incorrecta. Solo docentes autorizados pueden ingresar.")
    else:
        st.success("🎉 ¡Sesión Docente Activa - Facultad de RNR!")
        if st.button("Cerrar Sesión Docente"):
            st.session_state.docente_autorizado = False
            st.rerun()

        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["1️⃣ Cargar Sílabo", "2️⃣ Cargar Matrícula", "3️⃣ Digitalizar Registro (Foto/Video) a Excel"])

        # ---------------------------------------------------------
        # TAB 1: BOTÓN 1 - ESTRUCTURAR SÍLABO
        # ---------------------------------------------------------
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
                            
                            texto_clean = limpiar_json(response.text)
                            datos_silabo = json.loads(texto_clean)
                            st.session_state["datos_silabo"] = datos_silabo
                            
                            st.success(f"¡Sílabo procesado exitosamente: **{datos_silabo.get('curso', 'Curso Detectado')}**!")
                            
                            df_evals = pd.DataFrame(datos_silabo.get("evaluaciones", []))
                            st.subheader("📊 Ponderaciones del Curso")
                            st.dataframe(df_evals, use_container_width=True)
                            st.info(f"📐 **Fórmula de Evaluación:** {datos_silabo.get('formula', 'No especificada')}")
                            
                        except Exception as e:
                            st.error(f"Error al analizar el PDF del sílabo: {e}")

            if "datos_silabo" in st.session_state:
                st.caption("✅ Ponderaciones guardadas para el cálculo final.")

        # ---------------------------------------------------------
        # TAB 2: BOTÓN 2 - CARGAR MATRÍCULA
        # ---------------------------------------------------------
        with tab2:
            st.subheader("Botón 2: Cargar Matrícula y Alumnos")
            st.write("Sube la lista oficial de estudiantes matriculados (PDF, Excel o CSV).")
            lista_file = st.file_uploader("Sube la nómina oficial", type=["pdf", "xlsx", "csv"], key="lista_uploader")
            
            if lista_file:
                if st.button("Poblar Estudiantes"):
                    with st.spinner("Procesando la lista de estudiantes..."):
                        try:
                            ext = lista_file.name.split(".")[-1].lower()
                            if ext in ["xlsx", "csv"]:
                                if ext == "xlsx":
                                    df_est = pd.read_excel(lista_file)
                                else:
                                    df_est = pd.read_csv(lista_file)
                                st.session_state["lista_estudiantes"] = df_est.to_dict(orient="records")
                                st.success(f"¡Se cargaron {len(df_est)} estudiantes desde la hoja de cálculo!")
                                st.dataframe(df_est, use_container_width=True)
                            
                            elif ext == "pdf":
                                client = genai.Client(api_key=API_KEY_PREDETERMINADA)
                                bytes_data = lista_file.read()
                                prompt = (
                                    "Extrae la lista completa de estudiantes matriculados de este PDF. "
                                    "Devuelve ÚNICAMENTE un JSON válido con esta estructura:\n"
                                    "{\n"
                                    '  "estudiantes": [\n'
                                    '    {"nro": 1, "codigo": "20230001", "nombres_apellidos": "Juan Perez"}\n'
                                    "  ]\n"
                                    "}"
                                )
                                part = genai.types.Part.from_bytes(data=bytes_data, mime_type="application/pdf")
                                response = client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=[part, prompt]
                                )
                                
                                texto_clean = limpiar_json(response.text)
                                datos_est = json.loads(texto_clean)
                                lista_est = datos_est.get("estudiantes", [])
                                st.session_state["lista_estudiantes"] = lista_est
                                
                                df_est = pd.DataFrame(lista_est)
                                st.success(f"¡Se extrajeron {len(df_est)} estudiantes mediante IA!")
                                st.dataframe(df_est, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error al procesar la lista de estudiantes: {e}")

            if "lista_estudiantes" in st.session_state:
                st.subheader("📋 Lista Registrada en Sesión")
                st.dataframe(pd.DataFrame(st.session_state["lista_estudiantes"]), use_container_width=True)

        # ---------------------------------------------------------
        # TAB 3: BOTÓN 3 - FOTO/VIDEO A EXCEL
        # ---------------------------------------------------------
        with tab3:
            st.subheader("Botón 3: Digitalizar Registro Auxiliar (Foto / Video) a Excel")
            st.write("Sube la foto o video del registro auxiliar físico para digitalizar las notas y calcular los promedios.")
            
            foto_registro = st.file_uploader(
                "Sube la imagen o video del registro auxiliar",
                type=["jpg", "png", "jpeg", "mp4"],
                key="registro_uploader"
            )
            
            if foto_registro:
                if st.button("Digitalizar Notas con IA"):
                    with st.spinner("Analizando registro y digitalizando notas con Gemini Visión..."):
                        try:
                            client = genai.Client(api_key=API_KEY_PREDETERMINADA)
                            bytes_data = foto_registro.read()
                            mime_type = "video/mp4" if foto_registro.name.endswith(".mp4") else "image/jpeg"
                            
                            contexto_silabo = ""
                            if "datos_silabo" in st.session_state:
                                contexto_silabo = f"Ponderaciones del curso: {json.dumps(st.session_state['datos_silabo'])}"
                            
                            prompt = (
                                f"Analiza esta imagen/video de un registro auxiliar de notas. {contexto_silabo}\n"
                                "Extrae la lista de alumnos con sus notas por cada criterio evaluado.\n"
                                "Devuelve ÚNICAMENTE un JSON válido con esta estructura:\n"
                                "{\n"
                                '  "registro": [\n'
                                '    {"alumno": "Nombre Alumno", "examen_parcial": 15, "practicas": 14, "promedio_final": 14.7}\n'
                                "  ]\n"
                                "}"
                            )
                            
                            part = genai.types.Part.from_bytes(data=bytes_data, mime_type=mime_type)
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[part, prompt]
                            )
                            
                            texto_clean = limpiar_json(response.text)
                            datos_registro = json.loads(texto_clean)
                            df_notas = pd.DataFrame(datos_registro.get("registro", []))
                            
                            st.success("¡Notas digitalizadas correctamente!")
                            st.subheader("📑 Cuadro Consolidado de Calificaciones")
                            st.dataframe(df_notas, use_container_width=True)
                            
                            st.subheader("💾 Descargar Registro Oficial")
                            col_n1, col_n2 = st.columns(2)
                            
                            with col_n1:
                                csv_notas = df_notas.to_csv(index=False).encode("utf-8-sig")
                                st.download_button(
                                    label="Descargar Registro en CSV",
                                    data=csv_notas,
                                    file_name="registro_notas_rnr.csv",
                                    mime="text/csv"
                                )
                                
                            with col_n2:
                                output_n = io.BytesIO()
                                with pd.ExcelWriter(output_n, engine="xlsxwriter") as writer:
                                    df_notas.to_excel(writer, index=False, sheet_name="Notas_Oficiales")
                                excel_notas = output_n.getvalue()
                                st.download_button(
                                    label="Descargar en Excel (.xlsx)",
                                    data=excel_notas,
                                    file_name="registro_notas_rnr.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                
                        except Exception as e:
                            st.error(f"Error al digitalizar el registro: {e}")


# ==========================================
# MÓDULO 2: EXTRACTOR PRO (REQUIERE SUSCRIPCIÓN)
# ==========================================
elif modulo == "📊 Extractor & Limpiador SIG y R (Pro S/ 5.00)":

    if "acceso_permitido" not in st.session_state:
        st.session_state.acceso_permitido = False

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
            except Exception:
                st.warning("Sube el archivo 'qr_yape.jpg' a GitHub para visualizar el código QR.")

            st.write("Envía tu captura de pago para recibir tu contraseña.")

        with col2:
            st.write("### ¿Ya eres suscriptor?")
            clave_ingresada = st.text_input("Ingresa tu clave de acceso:", type="password")
            if st.button("Ingresar a la Plataforma"):
                if clave_ingresada == CLAVE_PRO:
                    st.session_state.acceso_permitido = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Clave incorrecta. Si realizaste tu Yape, contáctanos para enviarte tu contraseña.")

    else:
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
                                texto_clean = limpiar_json(response.text)
                                datos_json = json.loads(texto_clean)
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
