import streamlit as st
import pandas as pd
import re
import unicodedata
import io
import json
from google import genai
from PIL import Image

st.set_page_config(page_title="Ingenia Verde Pro", page_icon="🌱", layout="wide")

# Tu clave de API predeterminada de Gemini
API_KEY_PREDETERMINADA = "AQ.Ab8RN6KHt-SJGflqdK3V0BwnAuNeUg_S2a16GdTAovSHWYXGNA"

# Control de acceso/suscripción
if "acceso_permitido" not in st.session_state:
    st.session_state.acceso_permitido = False

if not st.session_state.acceso_permitido:
    st.title("🌱 Ingenia Verde Pro")
    st.subheader("Plataforma de Limpieza de Datos & Extracción con IA (SIG y R)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("### Suscripción Mensual: S/ 5.00 / mes")
        st.write("Obtén acceso para procesar tus archivos de campo:")
        st.write("✅ Limpieza automatizada para R y SIG (Nombres de variables, nulos, etc.)")
        st.write("✅ Extractor con IA de tablas desde fotos de libretas de campo")
        st.write("✅ Descarga ilimitada en formatos CSV y Excel (.xlsx)")
        st.write("---")
        st.markdown("📲 **Escanea el QR para yapear S/ 5.00**")
        
        # Muestra tu imagen QR cargada en el repositorio
        try:
            st.image("qr_yape.jpg", width=240, caption="Victor Kennedy Cayco Valdivia")
        except:
            st.warning("Sube el archivo 'qr_yape.jpg' a GitHub para visualizar el código QR.")
            
        st.write("Envía tu captura de pago para recibir tu contraseña.")
    
    with col2:
        st.write("### ¿Ya eres suscriptor?")
        clave_ingresada = st.text_input("Ingresa tu clave de acceso:", type="password")
        if st.button("Ingresar a la Plataforma"):
            # Clave de suscriptor (puedes cambiarla cuando quieras)
            if clave_ingresada.strip() == "VERDE2026":
                st.session_state.acceso_permitido = True
                st.rerun()
            else:
                st.error("Clave incorrecta. Si realizaste tu Yape, contáctanos para enviarte tu contraseña.")
                
    st.stop()

# --- A PARTIR DE AQUÍ SE MUESTRA LA APLICACIÓN AL SUSCRIPTOR ---

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

st.title("🌱 Ingenia Verde: Limpiador & Extractor de Datos SIG & R")
st.write("Sube tu archivo de Excel o la foto de una libreta/tabla de campo para procesarlo al instante.")

tab1, tab2 = st.tabs(["📄 Archivo Excel", "📷 Foto de Campo / Libreta"])

df_final = None

with tab1:
    archivo_excel = st.file_uploader("Elige tu archivo de Excel", type=["xlsx", "xls"], key="excel_uploader")
    if archivo_excel is not None:
        df_original = pd.read_excel(archivo_excel)
        df_final = procesar_dataframe(df_original)

with tab2:
    st.write("📷 **Extracción automática desde imagen**")
    
    api_key = st.text_input(
        "Gemini API Key", 
        value=API_KEY_PREDETERMINADA, 
        type="password", 
        help="Clave configurada por defecto."
    )
    
    archivo_imagen = st.file_uploader("Sube una foto clara de tu libreta o tabla", type=["jpg", "jpeg", "png"], key="img_uploader")
    
    if archivo_imagen is not None:
        imagen = Image.open(archivo_imagen)
        st.image(imagen, caption="Imagen cargada", width=400)
        
        if st.button("🔍 Extraer Tabla de la Foto"):
            if not api_key:
                st.error("Por favor ingresa tu API Key de Gemini para continuar.")
            else:
                with st.spinner("Analizando la imagen y procesando datos con IA..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        prompt = (
                            "Extrae toda la información tabular de esta imagen. "
                            "Devuelve UNICAMENTE un objeto JSON con una clave 'datos' "
                            "que contenga una lista de objetos, donde cada objeto represente una fila con sus columnas. "
                            "Ejemplo: {\"datos\": [{\"punto\": 1, \"este\": 300557.8, \"norte\": 8897588.1}]}"
                        )
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[imagen, prompt]
                        )
                        
                        texto_resp = response.text.strip()
                        if texto_resp.startswith("```json"):
                            texto_resp = texto_resp[7:]
                        if texto_resp.endswith("```"):
                            texto_resp = texto_resp[:-3]
                            
                        datos_json = json.loads(texto_resp)
                        df_extraido = pd.DataFrame(datos_json.get("datos", []))
                        
                        if not df_extraido.empty:
                            df_final = procesar_dataframe(df_extraido)
                            st.success("¡Tabla extraída y limpiada con éxito desde la imagen!")
                        else:
                            st.warning("No se pudo estructurar una tabla desde la imagen.")
                    except Exception as e:
                        st.error(f"Error al procesar la imagen: {e}")

if df_final is not None:
    st.markdown("---")
    st.subheader("📊 Datos Procesados y Limpios")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Filas útiles", df_final.shape[0])
    col2.metric("Columnas estandarizadas", df_final.shape[1])
    col3.metric("Celdas vacías/Nulas", int(df_final.isna().sum().sum()))
    
    st.dataframe(df_final, use_container_width=True)
    
    st.subheader("📥 Descargar Resultados")
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        separador = st.radio("Delimitador para CSV:", (", (Coma - R/GIS)", "; (Punto y coma - Excel ES)"), index=0)
        sep_char = "," if "," in separador else ";"
        csv_data = df_final.to_csv(index=False, sep=sep_char).encode('utf-8-sig')
        
        st.download_button(
            label="Descargar CSV Limpio",
            data=csv_data,
            file_name="datos_limpios_ingenia_verde.csv",
            mime="text/csv"
        )
        
    with col_dl2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Datos_Limpios')
        excel_data = output.getvalue()
        
        st.download_button(
            label="Descargar en Excel (.xlsx)",
            data=excel_data,
            file_name="datos_limpios_ingenia_verde.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )