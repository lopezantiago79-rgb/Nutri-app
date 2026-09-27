import json
import os
import tempfile
from datetime import datetime

from dotenv import load_dotenv
import streamlit as st

from ai.gemini import GeminiExtractor
from ai.mock import MockExtractor
from models.etiqueta import DatosEtiqueta
from models.paciente import Paciente
from models.perfil import PerfilNutricional
from nutrition.evaluator import evaluar_producto

# ============================================================
# CONFIGURACIÓN
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="Nutri App",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

RUTA_PACIENTES = os.path.join("profiles", "pacientes.json")
RUTA_HISTORIAL = os.path.join("profiles", "historial.json")

PROVEEDOR = os.getenv("AI_PROVIDER", "gemini").strip().lower()
MODELO_GEMINI = os.getenv("AI_MODEL", "").strip()

if not MODELO_GEMINI:
    MODELO_GEMINI = "gemini-3.8-flash"


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
<style>
.block-container {
    max-width: 520px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}
.nutri-logo {
    text-align: center;
    color: #087f5b;
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: .2rem;
}
.nutri-subtitle {
    text-align: center;
    color: #667085;
    font-size: 1rem;
    margin-bottom: .4rem;
}
.nutri-provider {
    text-align: center;
    color: #667085;
    font-size: .82rem;
    margin-bottom: 1.2rem;
}
.scan-card {
    border: 1px solid #d0d5dd;
    border-radius: 24px;
    padding: 1.5rem;
    text-align: center;
    background: #f8faf9;
    margin: .8rem 0 1rem;
}
.scan-icon {
    font-size: 3rem;
    line-height: 1;
    margin-bottom: .7rem;
}
.scan-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #101828;
}
.scan-description {
    color: #667085;
    margin-top: .5rem;
}
.result-card {
    border-radius: 28px;
    padding: 1.5rem 1.2rem;
    text-align: center;
    margin: .8rem 0 1rem;
}
.apto {
    background: #dff7e9;
    border: 1px solid #8bd5aa;
}
.no-apto {
    background: #ffe5df;
    border: 1px solid #f4a18e;
}
.revision {
    background: #fff4d6;
    border: 1px solid #e8c66b;
}
.result-icon {
    font-size: 3.2rem;
    line-height: 1;
}
.result-title {
    font-size: 2rem;
    font-weight: 800;
    margin-top: .5rem;
}
.result-text {
    color: #344054;
    line-height: 1.45;
    margin-top: .5rem;
}
.rule {
    padding: .75rem 0;
    border-bottom: 1px solid #eaecf0;
}
.ok {
    color: #087f5b;
    font-weight: 700;
}
.bad {
    color: #c4320a;
    font-weight: 700;
}
.review {
    color: #9a6700;
    font-weight: 700;
}
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PACIENTES
# ============================================================

def cargar_pacientes():
    # 1. Diagnóstico de carpetas en pantalla
    if not os.path.exists("profiles"):
        st.error(f"❌ No existe la carpeta 'profiles'. Archivos en raíz: {os.listdir('.')}")
    else:
        archivos_profiles = os.listdir("profiles")
        st.info(f"📂 Archivos encontrados en 'profiles/': {archivos_profiles}")

    # 2. Intentar cargar desde JSON
    pacientes = {}
    if os.path.exists(RUTA_PACIENTES):
        try:
            with open(RUTA_PACIENTES, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
                
            for paciente_id, datos_paciente in datos.items():
                if "id_paciente" in datos_paciente:
                    paciente = Paciente.model_validate(datos_paciente)
                elif "id_perfil" in datos_paciente:
                    perfil = PerfilNutricional.model_validate(datos_paciente)
                    paciente = Paciente(
                        id_paciente=paciente_id,
                        nombre=perfil.nombre,
                        descripcion=perfil.descripcion,
                        perfil=perfil,
                    )
                else:
                    continue
                pacientes[paciente.id_paciente] = paciente
        except Exception as e:
            st.error(f"❌ Error leyendo/validando JSON: {e}")

    # 3. RESPALDO: Si no hay pacientes cargados, crear uno en memoria para destrabar la App
    if not pacientes:
        st.warning("⚠️ Cargando paciente de prueba automático (Fallback)...")
        perfil_demo = PerfilNutricional(
            id_perfil="demo",
            nombre="Paciente Demo",
            descripcion="Perfil temporal de prueba",
            reglas_numericas=[],
            ingredientes_prohibidos=[],
            ingredientes_permitidos=[],
            prohibir_azucares_anadidos=False,
            prohibir_maltodextrina=False,
            prohibir_jarabe_maiz_alta_fructosa=False,
            prohibir_gluten=False,
            prohibir_leche=False,
            prohibir_huevo=False
        )
        pacientes["demo"] = Paciente(
            id_paciente="demo",
            nombre="Paciente Demo",
            descripcion="Perfil temporal",
            perfil=perfil_demo
        )

    return pacientes

# ============================================================
# HISTORIAL
# ============================================================

def cargar_historial():
    if not os.path.exists(RUTA_HISTORIAL):
        return {}
        
    try:
        with open(RUTA_HISTORIAL, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return {}

def guardar_historial(historial):
    os.makedirs("profiles", exist_ok=True)
    with open(RUTA_HISTORIAL, "w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, indent=2, ensure_ascii=False)

def guardar_analisis(historial, paciente, resultado, perfil):
    paciente_id = paciente.id_paciente
    historial.setdefault(paciente_id, [])
    
    historial[paciente_id].append(
        {
            "fecha_hora": datetime.now().astimezone().isoformat(timespec="seconds"),
            "producto": resultado.producto_detectado or "No identificado",
            "estado": resultado.estado.value,
            "motivo": resultado.motivo,
            "reglas_incumplidas": resultado.reglas_incumplidas,
            "advertencias": resultado.advertencias,
            "datos_extraidos": resultado.datos_extraidos.model_dump(mode="json"),
            "reglas_evaluadas": [
                regla.model_dump(mode="json") for regla in resultado.reglas_evaluadas
            ],
            "perfil_utilizado": perfil.model_dump(mode="json"),
            "proveedor_ia": resultado.proveedor_ia,
            "modelo_ia": resultado.modelo_ia,
        }
    )
    guardar_historial(historial)


# ============================================================
# MOCK
# ============================================================

def datos_mock():
    return DatosEtiqueta(
        producto_detectado="Producto de prueba",
        tamano_porcion_g=30,
        calorias_por_porcion=123,
        grasas_g_por_porcion=3.8,
        grasas_saturadas_g_por_porcion=0.3,
        grasas_trans_g_por_porcion=0,
        colesterol_mg_por_porcion=None,
        sodio_mg_por_porcion=100,
        carbohidratos_g_por_porcion=19,
        fibra_g_por_porcion=1.6,
        azucares_g_por_porcion=None,
        proteinas_g_por_porcion=3.2,
        hierro_mg_por_porcion=None,
        calcio_mg_por_porcion=None,
        ingredientes_detectados=[],
        contiene_azucares_anadidos=False,
        contiene_maltodextrina=False,
        contiene_jarabe_maiz_alta_fructosa=False,
        contiene_gluten=False,
        contiene_leche=False,
        contiene_huevo=False,
        texto_no_legible=False,
        advertencias_lectura=[],
    )


# ============================================================
# EXTRACTOR
# ============================================================

def extraer_datos(ruta_imagen):
    if PROVEEDOR == "gemini":
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("No se encontró GEMINI_API_KEY.")
            
        extractor = GeminiExtractor(model=MODELO_GEMINI)
        datos = extractor.extraer(ruta_imagen)
        return extractor, datos
        
    if PROVEEDOR == "mock":
        datos = datos_mock()
        extractor = MockExtractor(datos)
        return extractor, datos
        
    raise RuntimeError(f"Proveedor de IA no soportado: {PROVEEDOR}")


# ============================================================
# RESULTADO
# ============================================================

def mostrar_resultado(resultado):
    estado = resultado.estado.value
    
    if estado == "APTO":
        clase = "apto"
        icono = "✓"
        titulo = "APTO PARA TI"
    elif estado == "NO_APTO":
        clase = "no-apto"
        icono = "×"
        titulo = "NO APTO"
    else:
        clase = "revision"
        icono = "!"
        titulo = "REVISAR PRODUCTO"

    st.markdown(
        f"""
<div class="result-card {clase}">
    <div class="result-icon">{icono}</div>
    <div class="result-title">{titulo}</div>
    <div class="result-text">
        {resultado.motivo}
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("¿Por qué?")

    for regla in resultado.reglas_evaluadas:
        if regla.cumplida is True:
            clase_regla = "ok"
            simbolo = "✓"
        elif regla.cumplida is False:
            clase_regla = "bad"
            simbolo = "✕"
        else:
            clase_regla = "review"
            simbolo = "?"

        st.markdown(
            f"""
<div class="rule">
    <div class="{clase_regla}">
        {simbolo} {regla.regla}
    </div>
    <div>
        {regla.detalle}
    </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    if resultado.advertencias:
        st.warning("\n".join(f"• {x}" for x in resultado.advertencias))

    with st.expander("Ver datos detectados"):
        datos = resultado.datos_extraidos
        st.write(
            "**Producto:**",
            datos.producto_detectado or "No identificado",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Porción",
                f"{datos.tamano_porcion_g:g} g" if datos.tamano_porcion_g is not None else "—",
            )
        with c2:
            st.metric(
                "Calorías",
                f"{datos.calorias_por_porcion:g} kcal" if datos.calorias_por_porcion is not None else "—",
            )
        with c3:
            st.metric(
                "Sodio",
                f"{datos.sodio_mg_por_porcion:g} mg" if datos.sodio_mg_por_porcion is not None else "—",
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Hierro",
                f"{datos.hierro_mg_por_porcion:g} mg" if datos.hierro_mg_por_porcion is not None else "—",
            )
        with c2:
            st.metric(
                "Calcio",
                f"{datos.calcio_mg_por_porcion:g} mg" if datos.calcio_mg_por_porcion is not None else "—",
            )
        with c3:
            st.metric(
                "Proteínas",
                f"{datos.proteinas_g_por_porcion:g} g" if datos.proteinas_g_por_porcion is not None else "—",
            )

        if datos.ingredientes_detectados:
            st.markdown("**Ingredientes detectados:**")
            st.write(", ".join(datos.ingredientes_detectados))

    with st.expander("Ver detalles técnicos"):
        st.caption(f"IA: {resultado.proveedor_ia} — {resultado.modelo_ia}")


# ============================================================
# CARGA
# ============================================================

pacientes = cargar_pacientes()
historial = cargar_historial()

if not pacientes:
    st.error("Todavía no hay pacientes configurados.")
    st.stop()


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    '<div class="nutri-logo">🥗 NUTRI APP</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="nutri-subtitle">¿Este producto es para vos?</div>',
    unsafe_allow_html=True,
)

if PROVEEDOR == "gemini":
    st.markdown(
        f"""
<div class="nutri-provider">
    Extractor activo: Google Gemini — {MODELO_GEMINI}
</div>
        """,
        unsafe_allow_html=True,
    )
elif PROVEEDOR == "mock":
    st.markdown(
        """
<div class="nutri-provider">
    Extractor activo: Mock — modo de prueba
</div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PACIENTE
# ============================================================

with st.sidebar:
    st.subheader("👤 Acceso de paciente")
    st.caption("Seleccioná el paciente para aplicar su perfil nutricional.")
    paciente_id = st.selectbox(
        "Paciente",
        list(pacientes.keys()),
        format_func=lambda pid: pacientes[pid].nombre,
    )

paciente = pacientes[paciente_id]
perfil = paciente.perfil

if perfil is None:
    st.error("Este paciente no tiene un perfil nutricional configurado.")
    st.stop()


# ============================================================
# PACIENTE ACTUAL
# ============================================================

st.markdown("### 👤 Paciente")
st.markdown(f"**{paciente.nombre}**")

if perfil.nombre != paciente.nombre:
    st.caption(f"Perfil nutricional: {perfil.nombre}")


# ============================================================
# RECOMENDACIONES
# ============================================================

st.markdown("### 🥗 Tus recomendaciones")

if perfil.reglas_numericas:
    st.markdown("**Valores nutricionales a controlar**")
    for regla in perfil.reglas_numericas:
        texto_limite = ""
        if regla.maximo is not None:
            texto_limite = f"≤ {regla.maximo:g} {regla.unidad}"
        elif regla.minimo is not None:
            texto_limite = f"≥ {regla.minimo:g} {regla.unidad}"
            
        descripcion = regla.descripcion or regla.nutriente
        
        if texto_limite:
            st.markdown(f"• **{regla.nutriente.capitalize()} {texto_limite}** — {descripcion}")
        else:
            st.markdown(f"• {descripcion}")
else:
    st.caption("No hay valores nutricionales específicos configurados.")

componentes = []
if perfil.ingredientes_prohibidos:
    componentes.extend(perfil.ingredientes_prohibidos)
if perfil.prohibir_azucares_anadidos:
    componentes.append("azúcares añadidos")
if perfil.prohibir_maltodextrina:
    componentes.append("maltodextrina")
if perfil.prohibir_jarabe_maiz_alta_fructosa:
    componentes.append("jarabe de maíz de alta fructosa")
if perfil.prohibir_gluten:
    componentes.append("gluten")
if perfil.prohibir_leche:
    componentes.append("leche")
if perfil.prohibir_huevo:
    componentes.append("huevo")

if componentes:
    st.markdown("**Componentes a evitar**")
    for componente in componentes:
        st.markdown(f"• Sin {componente}")
else:
    st.caption("No hay componentes específicos para evitar.")


# ============================================================
# TARJETA DE ESCANEO
# ============================================================

st.markdown(
    """
<div class="scan-card">
    <div class="scan-icon">📷</div>
    <div class="scan-title">
        Escaneá la etiqueta nutricional
    </div>
    <div class="scan-description">
        Tomá una foto clara de la tabla nutricional.
    </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CÁMARA & GALERÍA
# ============================================================

foto = st.camera_input("Escanear con cámara")

st.markdown(
    """
<div style="text-align:center; color:#667085; margin:.5rem 0;">
    o elegí una foto
</div>
    """,
    unsafe_allow_html=True,
)

archivo = st.file_uploader(
    "Galería",
    type=["jpg", "jpeg", "png", "webp"],
)


# ============================================================
# IMAGEN
# ============================================================

imagen = foto if foto is not None else archivo


# ============================================================
# ANALIZAR
# ============================================================

if imagen is not None:
    st.image(
        imagen,
        caption="Etiqueta seleccionada",
        use_container_width=True,
    )
    
    if st.button("🔎 ANALIZAR PRODUCTO", type="primary", use_container_width=True):
        archivo_temporal = None
        try:
            extension = os.path.splitext(getattr(imagen, "name", ""))[1]
            if not extension:
                extension = ".jpg"
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temporal:
                temporal.write(imagen.getbuffer())
                archivo_temporal = temporal.name
                
            with st.spinner("La IA está leyendo la etiqueta..."):
                extractor, datos = extraer_datos(archivo_temporal)
                
            with st.spinner("Comparando con tu perfil..."):
                resultado = evaluar_producto(
                    datos=datos,
                    perfil=perfil,
                    proveedor_ia=extractor.proveedor,
                    modelo_ia=extractor.modelo,
                )
                
            guardar_analisis(
                historial=historial,
                paciente=paciente,
                resultado=resultado,
                perfil=perfil,
            )
            
            st.session_state["ultimo_resultado"] = resultado
            
        except Exception as error:
            st.error("No se pudo analizar la etiqueta.")
            st.exception(error)
            
        finally:
            if archivo_temporal:
                try:
                    os.remove(archivo_temporal)
                except OSError:
                    pass


# ============================================================
# RESULTADO ACTUAL
# ============================================================

resultado_actual = st.session_state.get("ultimo_resultado")

if resultado_actual is not None:
    st.divider()
    mostrar_resultado(resultado_actual)
    
    if st.button("📷 ESCANEAR OTRO PRODUCTO", use_container_width=True):
        st.session_state.pop("ultimo_resultado", None)
        st.rerun()


# ============================================================
# HISTORIAL
# ============================================================

registros = historial.get(paciente.id_paciente, [])

if registros:
    st.divider()
    with st.expander(f"📋 Historial ({len(registros)} análisis)"):
        for registro in reversed(registros):
            estado = registro.get("estado", "REVISION_MANUAL")
            
            if estado == "APTO":
                icono = "🟢"
            elif estado == "NO_APTO":
                icono = "🔴"
            else:
                icono = "🟡"
                
            producto = registro.get("producto", "Producto")
            fecha = registro.get("fecha_hora", "")
            motivo = registro.get("motivo", "")
            
            st.markdown(f"**{icono} {producto}**")
            
            if fecha:
                st.caption(fecha)
            if motivo:
                st.write(motivo)
                
            st.divider()
