import streamlit as st
import pandas as pd
try:
    import openai
except ImportError:
    st.error("📚 Error: La biblioteca OpenAI no está instalada. Por favor ejecuta: pip install openai")
    st.stop()
import json
import os
from dotenv import load_dotenv

# Configuración inicial
st.set_page_config(page_title="Calculo de Huella de la Comida Basado en el Modelo de Índice de Huella Alimentaría ", layout="wide")

# Función para guardar datos
def save_data(data, filename="datos.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Función para cargar datos
def load_data(filename="datos.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

# Inicializar datos
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Menú principal
st.title("🌱 Calculadora Agroecológica")
modulo = st.sidebar.selectbox("Selecciona un módulo", [
    "Módulo 1: País y PD",
    "Módulo 2: Alimentos del día",
    "Módulo 3: Tablas de distancia",
    "Módulo 4: Distancia por alimento",
    "Módulo 5: Modo de consecución",
    "Módulo 6: Cálculo de huella",
    "Módulo 7: Resultado final i-GDA"
])

# Cargar variables de entorno
load_dotenv()  # Cargar variables de entorno

# MÓDULO 1
if modulo == "Módulo 1: País y PD":
    st.header("🌍 Módulo 1: Ubicación del País")
    
    # API key desde variable de entorno
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ No se encontró la API key de OpenAI")
        st.stop()
        
    client = openai.OpenAI(
        api_key=api_key,
        timeout=30.0  # Aumentar el timeout si es necesario
    )

    pais = st.text_input("🌐 Nombre del país:")

    if st.button("Consultar datos con ChatGPT") and pais:
        try:
            with st.spinner("Consultando ChatGPT..."):
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un asistente que proporciona datos geográficos precisos. Responde SOLO con dos números separados por coma."},
                        {"role": "user", "content": f"¿Cuál es el largo máximo (norte a sur) y ancho máximo (este a oeste) en kilómetros de {pais}?"}
                    ]
                )
            
            respuesta = response.choices[0].message.content.strip()
            st.write("Respuesta recibida:", respuesta)  # Debug
            
            # Extraer números de la respuesta
            numeros = [float(n.strip()) for n in respuesta.replace(' ', '').split(',') if n.strip()]
            if len(numeros) != 2:
                raise ValueError(f"Se esperaban 2 números, se obtuvieron {len(numeros)}")
                
            largo, ancho = numeros
            pd = (largo + ancho) / 2

            st.session_state.data.update({
                "pais": pais,
                "largo": largo,
                "ancho": ancho,
                "pd": pd
            })
            save_data(st.session_state.data)

            st.success(f"✅ PD calculado: {pd:.2f} km")
            st.write(f"Largo: {largo} km")
            st.write(f"Ancho: {ancho} km")

        except ValueError as e:
            st.error(f"⚠️ Error en el formato de la respuesta: {str(e)}")
            st.session_state["manual_input"] = True
        except Exception as e:
            st.error(f"⚠️ Error al consultar ChatGPT: {str(e)}")
            st.session_state["manual_input"] = True

    if "manual_input" in st.session_state and st.session_state["manual_input"]:
        st.warning("Modo manual activado. Ingresa los datos a continuación.")
        largo = st.number_input("📏 Largo del país (km):", value=0)
        ancho = st.number_input("📐 Ancho del país (km):", value=0)

        if st.button("Calcular PD manualmente"):
            pd = (largo + ancho) / 2
            st.session_state.data.update({
                "largo": largo,
                "ancho": ancho,
                "pd": pd
            })
            save_data(st.session_state.data)
            st.success(f"✅ PD calculado manualmente: {pd:.2f} km")

# MÓDULO 2
elif modulo == "Módulo 2: Alimentos del día":
    st.header("🍽️ Módulo 2: Ingreso de alimentos")
    alimentos = st.session_state.data.get("alimentos", [])
    num = st.number_input("¿Cuántos alimentos deseas ingresar? (1-9)", 1, 9)
    for i in range(int(num)):
        alimento = st.text_input(f"Alimento #{i+1}", alimentos[i]["nombre"] if i < len(alimentos) else "")
        if len(alimentos) <= i:
            alimentos.append({"nombre": alimento})
        else:
            alimentos[i]["nombre"] = alimento
    st.session_state.data["alimentos"] = alimentos
    save_data(st.session_state.data)
    st.success("Alimentos guardados.")

# MÓDULO 3
elif modulo == "Módulo 3: Tablas de distancia":
    st.header("📏 Módulo 3: Generación de tablas de distancia")
    
    # Verificar si existe PD del Módulo 1
    PD = st.session_state.data.get("pd", 0)
    if PD == 0:
        st.warning("⚠️ Primero completa el Módulo 1 para obtener el PD")
        st.stop()
        
    # Mantener cálculos existentes pero mostrar en tablas
    tablas = {
        "Mundial": {"Muy lejano": 12000, "Lejano": 10000, "Intermedio": 8000, "Cercano": 6000},
        "Continental": {"Muy lejano": 6000, "Lejano": 4000, "Intermedio": 3000, "Cercano": 2000},
        "Nacional": {
            "Muy lejano": PD,
            "Lejano": round(0.6 * PD, 2),
            "Intermedio": round(0.3 * PD, 2),
            "Cercano": round(0.1 * PD, 2),
        }
    }

    # Calcular valores derivados
    nacional_cercano = tablas["Nacional"]["Cercano"]
    tablas["Regional"] = {
        "Muy lejano": nacional_cercano,
        "Lejano": round(0.7 * nacional_cercano, 2),
        "Intermedio": round(0.5 * nacional_cercano, 2),
        "Cercano": round(0.3 * nacional_cercano, 2),
    }
    
    regional_cercano = tablas["Regional"]["Cercano"]
    tablas["Zonal"] = {
        "Muy lejano": regional_cercano,
        "Lejano": round(0.8 * regional_cercano, 2),
        "Intermedio": round(0.6 * regional_cercano, 2),
        "Cercano": round(0.4 * regional_cercano, 2),
    }
    
    tablas["Local"] = {
        "Muy lejano": regional_cercano,
        "Lejano": round(0.6 * regional_cercano, 2),
        "Intermedio": round(0.4 * regional_cercano, 2),
        "Cercano": round(0.2 * regional_cercano, 2),
    }
    
    # Mostrar tablas en formato más amigable
    for nivel, datos in tablas.items():
        st.subheader(f"📊 Tabla {nivel}")
        df = pd.DataFrame([datos]).T
        df.columns = ["Kilómetros"]
        st.dataframe(df, use_container_width=True)
    
    st.session_state.data["tablas"] = tablas
    save_data(st.session_state.data)
    st.success("✅ Tablas generadas y guardadas")

# MÓDULO 4
elif modulo == "Módulo 4: Distancia por alimento":
    st.header("📦 Módulo 4: Registro de kilómetros por alimento")
    alimentos = st.session_state.data.get("alimentos", [])
    tablas = st.session_state.data.get("tablas", {})
    for alimento in alimentos:
        km = st.number_input(f"¿Cuántos km recorrió '{alimento['nombre']}'?", value=alimento.get("km", 0))
        alimento["km"] = km
        nivel = categoria = None
        for niv, cats in tablas.items():
            for cat, val in cats.items():
                if km >= val:
                    nivel, categoria = niv, cat
                    break
            if nivel: break
        alimento["nivel"] = nivel
        alimento["categoria"] = categoria
    st.session_state.data["alimentos"] = alimentos
    save_data(st.session_state.data)
    st.success("Clasificación guardada.")

# MÓDULO 5
elif modulo == "Módulo 5: Modo de consecución":
    st.header("🔄 Módulo 5: ¿Cómo se consiguió cada alimento?")
    opciones = ["Compra", "Cambia", "Produce"]
    alimentos = st.session_state.data.get("alimentos", [])
    for alimento in alimentos:
        modo = st.selectbox(f"¿Cómo se obtuvo '{alimento['nombre']}'?", opciones, index=opciones.index(alimento.get("modo", "Compra")))
        alimento["modo"] = modo
    st.session_state.data["alimentos"] = alimentos
    save_data(st.session_state.data)
    st.success("Modos guardados.")

# MÓDULO 6
elif modulo == "Módulo 6: Cálculo de huella":
    st.header("📊 Módulo 6: Cálculo de valor acumulado por alimento")
    
    # Verificar dependencias
    if not st.session_state.data.get("alimentos"):
        st.warning("⚠️ Primero ingresa alimentos en el Módulo 2")
        st.stop()
        
    nivel_map = {"Mundial": 1, "Continental": 2, "Nacional": 3, "Regional": 4, "Zonal": 5, "Local": 6}
    cat_map = {"Muy lejano": 1, "Lejano": 2, "Intermedio": 3, "Cercano": 4}
    modo_map = {"Compra": 3, "Cambia": 1, "Produce": 0}
    
    # Calcular valores y crear DataFrame
    resultados = []
    for alimento in st.session_state.data["alimentos"]:
        n = nivel_map.get(alimento.get("nivel"), 0)
        c = cat_map.get(alimento.get("categoria"), 0)
        m = modo_map.get(alimento.get("modo"), 0)
        valor = (n + c) - m
        alimento["valor_acumulado"] = valor
        
        resultados.append({
            "Alimento": alimento["nombre"],
            "Nivel": alimento.get("nivel", "No definido"),
            "Categoría": alimento.get("categoria", "No definido"),
            "Modo": alimento.get("modo", "No definido"),
            "Valor Acumulado": valor
        })
    
    # Mostrar tabla de resultados
    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True)
    
    save_data(st.session_state.data)
    st.success("✅ Valores acumulados calculados y guardados")

# MÓDULO 7
elif modulo == "Módulo 7: Resultado final i-GDA":
    st.header("🌐 Módulo 7: Resultado final de globo-dependencia alimentaria")
    
    # Verificar cálculos previos
    alimentos = st.session_state.data.get("alimentos", [])
    if not alimentos or not all("valor_acumulado" in a for a in alimentos):
        st.warning("⚠️ Primero completa el Módulo 6")
        st.stop()
    
    # Cálculos
    N = len(alimentos)
    X = sum([a.get("valor_acumulado", 0) for a in alimentos])
    iGDA = round((N * 10) / X, 2) if X else 0
    
    # Determinar tipo
    if iGDA <= 2:
        tipo = "LOCAL"
        color = "green"
    elif iGDA <= 3:
        tipo = "REGIONAL"
        color = "yellow"
    elif iGDA <= 4:
        tipo = "NACIONAL"
        color = "orange"
    else:
        tipo = "MUNDIAL"
        color = "red"
    
    # Mostrar resultados principales
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Índice i-GDA", f"{iGDA:.2f}")
    with col2:
        st.markdown(f"**Tipo de alimentación:** ::{color}[{tipo}]")
    
    # Tabla de kilómetros por nivel
    km_por_nivel = {
        nivel: sum([a.get("km", 0) for a in alimentos if a.get("nivel") == nivel])
        for nivel in ["Local", "Zonal", "Regional", "Nacional", "Continental", "Mundial"]
    }
    
    st.subheader("📊 Kilómetros recorridos por nivel")
    df_km = pd.DataFrame([km_por_nivel]).T
    df_km.columns = ["Kilómetros"]
    st.dataframe(df_km, use_container_width=True)
    
    # Tabla resumen de alimentos
    st.subheader("📋 Resumen por alimento")
    resumen_alimentos = [{
        "Alimento": a["nombre"],
        "Kilómetros": a.get("km", 0),
        "Nivel": a.get("nivel", "No definido"),
        "Modo": a.get("modo", "No definido"),
        "Valor": a.get("valor_acumulado", 0)
    } for a in alimentos]
    
    df_resumen = pd.DataFrame(resumen_alimentos)
    st.dataframe(df_resumen, use_container_width=True)