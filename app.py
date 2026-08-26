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
CLAVE_DOCENTE = "Docente2025"  # Clave de acceso para los profesores y tú
CLAVE_PRO = "Ingenia2025"       # Clave de acceso para la versión PRO

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
                            
                            texto_resp = response.text.strip()
                            if texto_resp.startswith("
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
http://googleusercontent.com/immersive_entry_chip/2
http://googleusercontent.com/immersive_entry_chip/3
http://googleusercontent.com/immersive_entry_chip/4
http://googleusercontent.com/immersive_entry_chip/5

---

### 📌 Claves de acceso configuradas:
* **Clave para el Módulo Docente:** `Docente2025`
* **Clave para el Extractor PRO:** `Ingenia2025`

*(Puedes cambiar estas claves en la línea 15 y 16 del código cuando quieras).*

### 🚀 Pasos para actualizar en GitHub:
1. En GitHub, dale clic al botón del **Lápiz (✏️)**.
2. Selecciona todo (`Ctrl + A`) y **borra todo el código anterior**.
3. Pega este nuevo código completo.
4. Presiona el botón verde **"Commit changes..."** y confirma.

¡Una vez guardado, entra a tu aplicación y prueba la clave `Docente2025` para ver los 3 botones en acción!
