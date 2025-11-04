import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx

app = FastAPI(title="Traductor EN-ES")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

# Configuración desde variables de entorno
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a professional translator from English to Spanish.")
GLOSSARY_PASSTHROUGH = os.getenv("GLOSSARY_PASSTHROUGH", "")

# Parsear glosario
GLOSSARY_TERMS = [term.strip() for term in GLOSSARY_PASSTHROUGH.split(",") if term.strip()]


@app.get("/", response_class=HTMLResponse)
async def home():
    """Sirve la página HTML principal"""
    try:
        with open("/app/static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=500)


@app.post("/translate")
async def translate(text: str = Form(...), target_lang: str = Form(None)):
    """Endpoint para traducir texto automáticamente (ES↔EN↔PT con detección automática)"""
    if not text or not text.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "El texto no puede estar vacío"}
        )

    # Detección simple de idioma basada en palabras comunes
    spanish_indicators = ['el', 'la', 'los', 'las', 'de', 'en', 'es', 'un', 'una', 'que', 'con', 'por', 'para', 'del']
    english_indicators = ['the', 'is', 'are', 'of', 'in', 'to', 'and', 'a', 'an', 'that', 'with', 'for', 'from']
    portuguese_indicators = ['o', 'a', 'os', 'as', 'de', 'em', 'do', 'da', 'dos', 'das', 'que', 'com', 'para', 'por', 'não', 'um', 'uma']

    text_lower = text.lower()
    spanish_count = sum(1 for word in spanish_indicators if f' {word} ' in f' {text_lower} ')
    english_count = sum(1 for word in english_indicators if f' {word} ' in f' {text_lower} ')
    portuguese_count = sum(1 for word in portuguese_indicators if f' {word} ' in f' {text_lower} ')

    # Detectar idioma de origen
    counts = {
        'spanish': spanish_count,
        'english': english_count,
        'portuguese': portuguese_count
    }
    detected_lang = max(counts, key=counts.get)

    # Determinar dirección de traducción basada en idioma detectado y target especificado
    lang_codes = {
        'spanish': ('ES', 'Spanish'),
        'english': ('EN', 'English'),
        'portuguese': ('PT', 'Portuguese')
    }

    source_code, source_lang = lang_codes[detected_lang]

    # Si no se especifica target_lang, usar lógica por defecto
    if not target_lang:
        # Por defecto: ES/PT → EN, EN → ES
        if detected_lang == 'english':
            target_code, target_lang_name = 'ES', 'Spanish'
        else:
            target_code, target_lang_name = 'EN', 'English'
    else:
        # Usar el target especificado por el usuario
        target_map = {
            'EN': ('EN', 'English'),
            'ES': ('ES', 'Spanish'),
            'PT': ('PT', 'Portuguese')
        }
        if target_lang not in target_map:
            return JSONResponse(
                status_code=400,
                content={"error": f"Idioma de destino inválido: {target_lang}"}
            )
        target_code, target_lang_name = target_map[target_lang]

    direction = f"{source_code}->{target_code}"

    # System prompt muy específico sobre el formato de salida
    system_content = f"You are a {source_lang} to {target_lang_name} translator. Translate the user message and return ONLY the translation. Do not include any instructions, explanations, notes, or preambles in your response."

    # Prompt del usuario - solo el texto a traducir
    user_prompt = text

    # Obtener el nombre del modelo cargado en vLLM
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            models_response = await client.get(f"{VLLM_BASE_URL}/models")
            models_data = models_response.json()
            model_name = models_data["data"][0]["id"]
    except:
        model_name = "/models/Qwen/Qwen2-1.5B-Instruct"  # Fallback

    # Preparar la petición a vLLM con optimizaciones de velocidad
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Más determinista = más rápido
        "max_tokens": 1024,  # Reducido de 2048
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{VLLM_BASE_URL}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # Extraer la traducción
            translated_text = result["choices"][0]["message"]["content"]

            return JSONResponse(content={
                "original": text,
                "translated": translated_text,
                "direction": direction,
                "model": result.get("model", "unknown"),
                "usage": result.get("usage", {})
            })

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": "Timeout: el modelo tardó demasiado en responder"}
        )
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content={"error": f"Error del servidor vLLM: {e.response.text}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error inesperado: {str(e)}"}
        )


@app.post("/refine")
async def refine_text(text: str = Form(...), style: str = Form("clear"), direction: str = Form("ES->EN")):
    """Endpoint para traducir con estilo mejorado desde el texto original (ES↔EN↔PT)"""
    if not text or not text.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "El texto no puede estar vacío"}
        )

    # Determinar idiomas según la dirección
    direction_map = {
        "ES->EN": ("Spanish", "English"),
        "ES->PT": ("Spanish", "Portuguese"),
        "EN->ES": ("English", "Spanish"),
        "EN->PT": ("English", "Portuguese"),
        "PT->ES": ("Portuguese", "Spanish"),
        "PT->EN": ("Portuguese", "English"),
    }

    if direction not in direction_map:
        return JSONResponse(
            status_code=400,
            content={"error": f"Dirección inválida: {direction}. Usa: {', '.join(direction_map.keys())}"}
        )

    source_lang, target_lang = direction_map[direction]

    # Definir los estilos de mejora disponibles con traducción
    style_prompts = {
        "formal": f"Translate the following {source_lang} text to {target_lang} using a formal and professional tone, suitable for business or academic documentation.",
        "concise": f"Translate the following {source_lang} text to {target_lang} in a concise and brief manner, removing any redundancy while preserving all key information.",
        "clear": f"Translate the following {source_lang} text to {target_lang} using clear and simple language that is easy to understand.",
        "technical": f"Translate the following {source_lang} text to {target_lang} using precise technical terminology appropriate for technical documentation."
    }

    # Validar el estilo
    if style not in style_prompts:
        return JSONResponse(
            status_code=400,
            content={"error": f"Estilo inválido. Usa: {', '.join(style_prompts.keys())}"}
        )

    # System prompt - instruir al modelo a dar solo la traducción
    system_content = f"You are a {source_lang} to {target_lang} translator. {style_prompts[style]} Return ONLY the translation. Do not include any instructions, explanations, notes, or preambles in your response."

    # Prompt del usuario - solo el texto
    user_prompt = text

    # Obtener el nombre del modelo
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            models_response = await client.get(f"{VLLM_BASE_URL}/models")
            models_data = models_response.json()
            model_name = models_data["data"][0]["id"]
    except:
        model_name = "/models/Qwen/Qwen2-1.5B-Instruct"

    # Preparar la petición a vLLM
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Más determinista para evitar explicaciones
        "max_tokens": 1024,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{VLLM_BASE_URL}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # Extraer el texto mejorado
            refined_text = result["choices"][0]["message"]["content"]

            return JSONResponse(content={
                "original": text,
                "refined": refined_text,
                "style": style,
                "direction": direction,
                "model": result.get("model", "unknown"),
                "usage": result.get("usage", {})
            })

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": "Timeout: el modelo tardó demasiado en responder"}
        )
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content={"error": f"Error del servidor vLLM: {e.response.text}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error inesperado: {str(e)}"}
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{VLLM_BASE_URL.replace('/v1', '')}/health")
            vllm_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        vllm_status = "unavailable"

    return {
        "status": "ok",
        "vllm_status": vllm_status,
        "vllm_url": VLLM_BASE_URL
    }


@app.get("/config")
async def get_config():
    """Muestra la configuración actual"""
    return {
        "vllm_base_url": VLLM_BASE_URL,
        "system_prompt": SYSTEM_PROMPT,
        "glossary_terms": GLOSSARY_TERMS
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5173)
