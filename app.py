import streamlit as st
import pandas as pd
import io
import json
import re
import base64
import unicodedata
from PIL import Image
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONFIGURACIÓN Y CLAVES DE ACCESO
# ---------------------------------------------------------
CLAVE_DOCENTE = "Docente2025"
CLAVE_PRO = "Ingenia2025"
API_KEY_PREDETERMINADA = st.secrets.get("GEMINI_API_KEY", "")

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def limpiar_json(texto: str) -> str:
    """Extrae bloques JSON válidos de la respuesta enviada por la IA."""
    texto = texto.strip()
    match = re.search(r'\{.*\}|\[.*\]', texto, re.DOTALL)
    if match:
        return match.group(0)
    return texto

def normalizar_texto(texto: str) -> str:
    """Limpia tildes y caracteres especiales."""
    if not isinstance(texto, str):
        return str(texto)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.strip().lower()

def procesar_dataframe_sig(df_original: pd.DataFrame) -> pd.DataFrame:
    """Función de limpieza para el Módulo 2 (Extractor SIG & R)."""
    df = df_original.copy()
    df.columns = [limpiar_json(str(col)) for col in df.columns]

    df_limpio = df.dropna(how='all')
    df_limpio = df_limpio.dropna(how='all', axis=1)

    for col in df_limpio.select_dtypes(include=['object']).columns:
        df_limpio[col] = df_limpio[col].astype(str).str.strip()

    return df_limpio

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ingenia Verde Pro",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------------------------------------
# NAVEGACIÓN LATERAL
# ---------------------------------------------------------
st.sidebar.title("🌱 Ingenia Verde Pro")
st.sidebar.caption("Plataforma de Herramientas IA & Procesamiento")

modulo = st.sidebar.radio(
    "Selecciona un módulo:",
    [
        "1. Digitación de Notas - Maestros RNR (Gratis / Beta)",
        "2. Extractor & Limpiador SIG y R (Pro S/ 5.00)"
    ]
)

# =========================================================
# MÓDULO 1: SECCIÓN MAESTROS RNR (GRATIS / BETA)
# =========================================================
if modulo == "1. Digitación de Notas - Maestros RNR (Gratis / Beta)":
    st.title("📄 Digitación Inteligente de Notas - Docentes RNR")
    st.caption("Acceso exclusivo para docentes autorizados. Datos aislados por correo electrónico.")

    # 1. Control de Acceso por Clave General
    if "docente_autorizado" not in st.session_state:
        st.session_state.docente_autorizado = False

    if not st.session_state.docente_autorizado:
        st.info("🔒 **Módulo Privado de Gestión Académica**")
        clave_ingresada = st.text_input("Ingresa la clave de acceso docente otorgada:", type="password", key="clave_docente_input")
        if st.button("Ingresar al Panel Docente"):
            if clave_ingresada == CLAVE_DOCENTE:
                st.session_state.docente_autorizado = True
                st.success("¡Acceso concedido!")
                st.rerun()
            else:
                st.error("Clave incorrecta. Solo docentes autorizados pueden ingresar.")
        st.stop()

    # 2. Identificación por Correo Electrónico (Privacidad del Profesor)
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Identificación de Usuario")
    
    user_email = st.sidebar.text_input(
        "Tu Correo Electrónico:", 
        placeholder="ejemplo@profesor.edu.pe",
        key="input_user_email"
    )

    if not user_email:
        st.warning("⚠️ Por favor ingresa tu correo electrónico en el menú lateral para aislar tus registros y evitar que otros profesores vean tu trabajo.")
        st.stop()
    
    # Claves de almacenamiento aisladas por usuario
    user_key_prefix = f"user_{normalizar_texto(user_email)}_"
    eval_config_key = user_key_prefix + "datos_silabo"
    students_key = user_key_prefix + "lista_estudiantes"

    st.success(f"Sesión activa para: **{user_email}**")

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.docente_autorizado = False
        st.rerun()

    st.markdown("---")

    # 3. Configuración de API Key de Gemini
    api_key_docente = st.text_input(
        "🔑 **Gemini API Key:**",
        value=API_KEY_PREDETERMINADA,
        type="password",
        help="Ingresa tu clave de Google AI Studio para procesar imágenes y documentos.",
        key="api_key_docente_input"
    )

    st.markdown("---")

    # PESTAÑAS PRINCIPALES DEL PROCESO (3 BOTONES)
    tab1, tab2, tab3 = st.tabs([
        "⚙️ 1. Configurar Porcentajes de Evaluación", 
        "📋 2. Cargar Matrícula", 
        "📸 3. Digitalizar Registro (Foto/Video) a Excel"
    ])

    # -----------------------------------------------------
    # TAB 1: CONFIGURAR DISTRIBUCIÓN DE NOTAS
    # -----------------------------------------------------
    with tab1:
        st.subheader("Botón 1: Definir Distribución de Porcentajes")
        st.write("Establece los pesos de evaluación de tu curso para el cálculo del promedio final.")

        # Opción A: Formulario Interactivo Manual
        st.markdown("#### ✏️ Opción A: Configuración Manual de Rubros")

        # Datos por defecto basados en el sistema institucional
        default_rubros = pd.DataFrame([
            {"ID": "PR", "Evaluacion": "Prácticas", "Cantidad": 2, "Peso_Porcentaje": 25.0},
            {"ID": "TE", "Evaluacion": "Trabajo Encargado", "Cantidad": 3, "Peso_Porcentaje": 10.0},
            {"ID": "EP", "Evaluacion": "Examen Parcial", "Cantidad": 2, "Peso_Porcentaje": 20.0},
            {"ID": "MC", "Evaluacion": "Medio Curso", "Cantidad": 1, "Peso_Porcentaje": 20.0},
            {"ID": "EA", "Evaluacion": "Evaluación Actitudinal", "Cantidad": 1, "Peso_Porcentaje": 5.0},
            {"ID": "EF", "Evaluacion": "Examen Final", "Cantidad": 1, "Peso_Porcentaje": 20.0},
        ])

        nombre_curso = st.text_input("Nombre de la Asignatura / Curso:", value="FISIOLOGÍA VEGETAL")

        edited_df = st.data_editor(
            default_rubros if eval_config_key not in st.session_state else pd.DataFrame(st.session_state[eval_config_key]["evaluaciones"]),
            num_rows="dynamic",
            use_container_width=True,
            key="editor_rubros"
        )

        total_peso = edited_df["Peso_Porcentaje"].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Suma Total de Porcentajes", f"{total_peso:.1f}%")

        if total_peso == 100.0:
            c1.success("✅ La distribución de porcentajes suma exactamente 100%.")
            if st.button("💾 Guardar Configuración de Evaluación", type="primary"):
                rubros_dict = edited_df.to_dict(orient="records")
                st.session_state[eval_config_key] = {
                    "curso": nombre_curso,
                    "evaluaciones": rubros_dict
                }
                st.success("¡Porcentajes guardados exitosamente para tu usuario!")
        else:
            c1.error(f"⚠️ La suma debe ser exactamente 100%. Actualmente es {total_peso:.1f}%. Ajusta los valores.")

        st.markdown("---")

        # Opción B: Carga opcional vía PDF de Sílabo
        st.markdown("#### 📄 Opción B: Extraer Distribución desde un Sílabo (PDF con IA)")
        silabo_file = st.file_uploader("Subir Sílabo en PDF:", type=["pdf"], key="silabo_uploader")

        if silabo_file and st.button("Procesar Sílabo con IA"):
            if not api_key_docente:
                st.error("Por favor ingresa tu Gemini API Key en el campo superior.")
            else:
                with st.spinner("Analizando documento con Gemini Vision..."):
                    try:
                        client = genai.Client(api_key=api_key_docente)
                        bytes_data = silabo_file.read()

                        prompt = """
                        Analiza este sílabo universitario.
                        Extrae el nombre del curso y el sistema de evaluación (rubros con sus pesos en porcentaje).
                        Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
                        {
                          "curso": "Nombre del Curso",
                          "evaluaciones": [
                            {"ID": "PR", "Evaluacion": "Prácticas", "Cantidad": 2, "Peso_Porcentaje": 25},
                            {"ID": "EP", "Evaluacion": "Examen Parcial", "Cantidad": 2, "Peso_Porcentaje": 20}
                          ]
                        }
                        """

                        part = types.Part.from_bytes(data=bytes_data, mime_type="application/pdf")
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[part, prompt]
                        )

                        texto_clean = limpiar_json(response.text)
                        datos_silabo = json.loads(texto_clean)
                        st.session_state[eval_config_key] = datos_silabo
                        st.success(f"¡Sílabo procesado! Curso detectado: **{datos_silabo.get('curso')}**")
                        st.json(datos_silabo)

                    except Exception as e:
                        st.error(f"Error al procesar el PDF del sílabo: {e}")

    # -----------------------------------------------------
    # TAB 2: CARGAR MATRÍCULA Y ALUMNOS
    # -----------------------------------------------------
    with tab2:
        st.subheader("Botón 2: Cargar Matrícula y Alumnos")
        st.write("Sube la lista oficial de estudiantes matriculados (PDF, Excel o CSV).")

        lista_file = st.file_uploader("Subir nómina oficial:", type=["pdf", "xlsx", "csv"], key="lista_uploader")

        if lista_file and st.button("Procesar Lista de Estudiantes"):
            ext = lista_file.name.split(".")[-1].lower()

            if ext in ["xlsx", "csv"]:
                try:
                    df_est = pd.read_excel(lista_file) if ext == "xlsx" else pd.read_csv(lista_file)
                    st.session_state[students_key] = df_est.to_dict(orient="records")
                    st.success(f"Se cargaron {len(df_est)} estudiantes correctamente.")
                    st.dataframe(df_est, use_container_width=True)
                except Exception as e:
                    st.error(f"Error al leer el archivo Excel/CSV: {e}")

            elif ext == "pdf":
                if not api_key_docente:
                    st.error("Por favor ingresa tu Gemini API Key en el campo superior.")
                else:
                    with st.spinner("Procesando lista de estudiantes con IA..."):
                        try:
                            client = genai.Client(api_key=api_key_docente)
                            bytes_data = lista_file.read()

                            prompt = """
                            Extrae la lista completa de estudiantes matriculados de este PDF.
                            Devuelve ÚNICAMENTE un JSON válido con esta estructura:
                            {
                              "estudiantes": [
                                {"nro": 1, "codigo": "20230001", "nombres_apellidos": "Juan Pérez"}
                              ]
                            }
                            """

                            part = types.Part.from_bytes(data=bytes_data, mime_type="application/pdf")
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[part, prompt]
                            )

                            texto_clean = limpiar_json(response.text)
                            datos_est = json.loads(texto_clean)
                            lista_est = datos_est.get("estudiantes", [])
                            st.session_state[students_key] = lista_est
                            
                            df_est = pd.DataFrame(lista_est)
                            st.success(f"Se extrajeron {len(df_est)} estudiantes mediante IA.")
                            st.dataframe(df_est, use_container_width=True)

                        except Exception as e:
                            st.error(f"Error al procesar el PDF de alumnos: {e}")

        # Mostrar estado actual de la nómina
        if students_key in st.session_state:
            st.info("📌 **Nómina de alumnos cargada actualmente en tu sesión:**")
            st.dataframe(pd.DataFrame(st.session_state[students_key]), use_container_width=True)

    # -----------------------------------------------------
    # TAB 3: DIGITALIZAR REGISTRO (FOTO/VIDEO) A EXCEL
    # -----------------------------------------------------
    with tab3:
        st.subheader("Botón 3: Digitalizar Registro Auxiliar (Foto / Video a Excel)")
        st.write("Sube la foto o video del registro auxiliar para digitalizar las notas y calcular los promedios ponderados automáticamente.")

        foto_registro = st.file_uploader(
            "Subir imagen o video del registro auxiliar:",
            type=["jpg", "jpeg", "png", "mp4"],
            key="registro_uploader"
        )

        if foto_registro and st.button("Digitalizar Notas con IA"):
            if not api_key_docente:
                st.error("Por favor ingresa tu Gemini API Key en el campo superior.")
            elif eval_config_key not in st.session_state:
                st.error("⚠️ Primero debes definir tus porcentajes en la Pestaña 1 (Botón 1).")
            else:
                with st.spinner("Analizando registro y digitalizando notas con Gemini Vision..."):
                    try:
                        client = genai.Client(api_key=api_key_docente)
                        bytes_data = foto_registro.read()
                        mime_type = "video/mp4" if foto_registro.name.endswith(".mp4") else "image/jpeg"

                        contexto_eval = json.dumps(st.session_state[eval_config_key])
                        contexto_alumnos = json.dumps(st.session_state.get(students_key, []))

                        prompt = f"""
                        Analiza esta imagen/video de un registro auxiliar de notas.
                        Utiliza esta configuración de pesos del curso: {contexto_eval}
                        Utiliza esta lista oficial de alumnos: {contexto_alumnos}

                        Extrae la lista de alumnos con sus notas por cada criterio evaluado.
                        Calcula el promedio final usando los porcentajes asignados.
                        Devuelve ÚNICAMENTE un JSON válido con esta estructura:
                        {{
                          "registro": [
                            {{
                              "alumno": "Nombre del Alumno",
                              "PR1": 15,
                              "PR2": 14,
                              "EP1": 13,
                              "EF1": 16,
                              "promedio_final": 14.8
                            }}
                          ]
                        }}
                        """

                        part = types.Part.from_bytes(data=bytes_data, mime_type=mime_type)
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[part, prompt]
                        )

                        texto_clean = limpiar_json(response.text)
                        datos_registro = json.loads(texto_clean)
                        df_notas = pd.DataFrame(datos_registro.get("registro", []))

                        st.success("¡Notas digitalizadas correctamente!")
                        st.subheader("📊 Cuadro Consolidado de Calificaciones")
                        st.dataframe(df_notas, use_container_width=True)

                        # Opciones de Descarga
                        st.subheader("📥 Descargar Registro Oficial")
                        col_d1, col_d2 = st.columns(2)

                        with col_d1:
                            csv_notas = df_notas.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="Descargar Registro en CSV",
                                data=csv_notas,
                                file_name=f"registro_notas_{normalizar_texto(user_email)}.csv",
                                mime="text/csv"
                            )

                        with col_d2:
                            output_n = io.BytesIO()
                            with pd.ExcelWriter(output_n, engine="openpyxl") as writer:
                                df_notas.to_excel(writer, index=False, sheet_name="Notas_Oficiales")
                            excel_notas = output_n.getvalue()

                            st.download_button(
                                label="Descargar en Excel (.xlsx)",
                                data=excel_notas,
                                file_name=f"registro_notas_{normalizar_texto(user_email)}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                    except Exception as e:
                        st.error(f"Error al digitalizar el registro: {e}")

# =========================================================
# MÓDULO 2: EXTRACTOR & LIMPIADOR SIG Y R (PRO S/ 5.00)
# =========================================================
elif modulo == "2. Extractor & Limpiador SIG y R (Pro S/ 5.00)":
    st.title("🌱 Ingenia Verde Pro")
    st.subheader("Plataforma de Limpieza de Datos & Extracción con IA (SIG y R)")

    if "acceso_permitido" not in st.session_state:
        st.session_state.acceso_permitido = False

    if not st.session_state.acceso_permitido:
        col1, col2 = st.columns(2)
        with col1:
            st.info("### 💳 Suscripción Mensual: S/ 5.00 / mes")
            st.markdown("- **Obtén acceso para procesar tus archivos de campo.**")
            st.markdown("- **Limpieza automatizada para R y SIG** (nombres de variables, nulos, etc.).")
            st.markdown("- **Extractor con IA de tablas desde fotos de libretas de campo.**")
            st.markdown("- **Descarga ilimitada en formatos CSV y Excel (.xlsx).**")

            st.markdown("---")
            st.write("### 📲 Escanea el QR para yapear S/ 5.00")
            try:
                st.image("qr_yape.jpg", width=240, caption="Contacto: Víctor Kennedy Cayco Valdivia")
            except Exception:
                st.warning("Sube el archivo 'qr_yape.jpg' a GitHub para visualizar el código QR.")

            st.write("Envía tu captura de pago para recibir tu contraseña.")

        with col2:
            st.write("### 🔑 ¿Ya eres suscriptor?")
            clave_ingresada = st.text_input("Ingresa tu clave de acceso:", type="password", key="clave_pro_input")
            if st.button("Ingresar a la Plataforma"):
                if clave_ingresada == CLAVE_PRO:
                    st.session_state.acceso_permitido = True
                    st.success("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("Clave incorrecta. Si realizaste tu Yape, contáctanos para enviarte tu contraseña.")
        st.stop()

    # Interfaz para usuarios PRO autorizados
    st.success("¡Sesión PRO Activa!")
    
    api_key_pro = st.text_input(
        "🔑 **Gemini API Key:**",
        value=API_KEY_PREDETERMINADA,
        type="password",
        help="Ingresa tu clave de Google AI Studio para continuar.",
        key="api_key_pro_input"
    )

    tab_ex1, tab_ex2 = st.tabs(["📊 Archivo Excel / CSV", "📸 Foto de Campo / Libreta"])

    with tab_ex1:
        archivo_excel = st.file_uploader("Elige tu archivo de Excel:", type=["xlsx", "xls", "csv"], key="excel_uploader")
        if archivo_excel:
            try:
                df_or = pd.read_excel(archivo_excel) if not archivo_excel.name.endswith('.csv') else pd.read_csv(archivo_excel)
                df_fin = procesar_dataframe_sig(df_or)
                
                st.subheader("Datos Procesados y Limpios")
                st.dataframe(df_fin, use_container_width=True)

                out_ex = io.BytesIO()
                with pd.ExcelWriter(out_ex, engine="openpyxl") as writer:
                    df_fin.to_excel(writer, index=False, sheet_name="Datos_Limpios")
                
                st.download_button(
                    label="Descargar Excel Limpio (.xlsx)",
                    data=out_ex.getvalue(),
                    file_name="datos_limpios_ingenia_verde.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    with tab_ex2:
        archivo_imagen = st.file_uploader("Sube una foto clara de tu libreta o tabla:", type=["jpg", "jpeg", "png"], key="img_uploader")
        if archivo_imagen and st.button("Extraer Tabla de la Foto"):
            if not api_key_pro:
                st.error("Ingresa tu Gemini API Key para continuar.")
            else:
                with st.spinner("Analizando la imagen y procesando datos con IA..."):
                    try:
                        client = genai.Client(api_key=api_key_pro)
                        bytes_img = archivo_imagen.read()

                        prompt = """
                        Extrae toda la información tabular de esta imagen.
                        Devuelve ÚNICAMENTE un objeto JSON con una clave "datos" que contenga una lista de objetos.
                        """

                        part = types.Part.from_bytes(data=bytes_img, mime_type="image/jpeg")
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[part, prompt]
                        )

                        texto_clean = limpiar_json(response.text)
                        datos_json = json.loads(texto_clean)
                        df_extracted = pd.DataFrame(datos_json.get("datos", []))

                        st.subheader("Tabla Extraída")
                        st.dataframe(df_extracted, use_container_width=True)

                    except Exception as e:
                        st.error(f"Error al procesar la imagen: {e}")
