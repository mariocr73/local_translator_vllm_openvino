# Trilingual Technical Translator ES↔EN↔PT

Technical Spanish-English-Portuguese translator using local LLM with Intel Arc Graphics acceleration and OpenVINO.

## 🚀 Features

- **Automatic Trilingual Translation**: Automatically detects source language (ES/EN/PT) and translates to any target language
- **Flexible Language Selection**: Choose target language or use automatic mode (ES/PT → EN, EN → ES)
- **AI-Powered Refinement**: Improve translations with 4 styles (formal, concise, clear, technical)
- **Local LLM**: Uses Qwen2.5-3B-Instruct with FP8 KV cache quantization running completely offline for high-quality translations
- **GPU Acceleration**: Optimized for Intel Arc Graphics with OpenVINO
- **Technical Glossary**: Preserves Kubernetes/OpenShift technical terms without translation
- **Modern Web Interface**: Responsive UI with real-time feedback and language selector
- **REST API**: Documented endpoints for integration

## 📋 Requirements

### Recommended Hardware
- **CPU**: Intel Core Ultra 7 (or similar with Intel Arc integrated graphics)
- **RAM**: 16GB minimum, 32GB+ recommended
- **GPU**: Intel Arc Graphics (integrated or discrete)
- **Storage**: ~10GB for the model

### Software
- **OS**: Fedora 42 (or any modern Linux distro)
- **Podman**: For container execution
- **podman-compose**: For service orchestration

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <your-repository>
cd local_translator_vllm_openvino
```

### 2. Configure Environment Variables

Edit the `.env` file:

```bash
# Model to use (3B for optimal balance of quality and speed)
MODEL_ID=Qwen/Qwen2.5-3B-Instruct
MAX_MODEL_LEN=8192
VLLM_PORT=8000
HUGGINGFACE_HUB_TOKEN=
```

**Note**: `HUGGINGFACE_HUB_TOKEN` is optional. Only needed for private models.

### 3. Verify Intel GPU Access

```bash
ls -la /dev/dri/
# You should see: renderD128 (Intel GPU)
```

### 4. Download the Model

```bash
podman-compose --profile bootstrap up --build downloader
```

This downloads the Qwen2.5-3B-Instruct model (~6GB) to a persistent volume.

### 5. Start the Services

```bash
env MODEL_ID=Qwen/Qwen2.5-3B-Instruct \
    MAX_MODEL_LEN=8192 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

**Important**: Using `env` to force variables is necessary due to caching limitations in podman-compose.

### 6. Verify Status

```bash
# View vLLM logs
podman logs -f local_translator_vllm_openvino_vllm_1

# Wait for message: "Application startup complete"
# Startup time: ~2-3 minutes
```

## 🌐 Usage

### Web Interface

1. Open your browser at: **http://localhost:5173**
2. Type or paste text in Spanish, English, or Portuguese
3. **[Optional]** Select target language (Auto, EN, ES, or PT)
4. Click "Translate"
5. Translation will appear in seconds
6. **[OPTIONAL]** Use "Improve with AI" to refine the translation:
   - Select a style: **Formal**, **Concise**, **Clear**, or **Technical**
   - Click "Mejorar con IA"
   - Improved text appears in ~3-5 seconds

**Expected Translation Times:**
- Short phrase (10-20 words): ~5-6 seconds
- Medium paragraph (30-50 words): ~8-12 seconds
- Long text (80+ words): ~20-22 seconds

**AI Refinement Styles:**
- **Formal**: More professional and academic tone
- **Concise**: Shorter, removing redundancy
- **Clear**: Simpler language, easier to understand
- **Technical**: More precise technical terminology

### REST API

#### Translate Text

**Automatic Mode** (detects source language and translates to default target):
```bash
curl -X POST http://localhost:5173/translate \
  -F "text=KubeVirt is an open-source project"
```

**With Specific Target Language**:
```bash
# English to Portuguese
curl -X POST http://localhost:5173/translate \
  -F "text=KubeVirt is an open-source project" \
  -F "target_lang=PT"

# Spanish to Portuguese
curl -X POST http://localhost:5173/translate \
  -F "text=KubeVirt es un proyecto de código abierto" \
  -F "target_lang=PT"
```

**Available target languages**: `EN`, `ES`, `PT`, or omit for automatic mode

**Response:**
```json
{
  "original": "KubeVirt is an open-source project",
  "translated": "KubeVirt es un proyecto de código abierto",
  "direction": "EN->ES",
  "model": "/models/Qwen/Qwen2.5-3B-Instruct",
  "usage": {
    "prompt_tokens": 145,
    "total_tokens": 163,
    "completion_tokens": 18
  }
}
```

#### Refine/Improve Text

```bash
curl -X POST http://localhost:5173/refine \
  -F "text=KubeVirt is an open-source project that allows executing virtual machines in Kubernetes." \
  -F "style=formal"
```

**Available styles**: `formal`, `concise`, `clear`, `technical`

**Response:**
```json
{
  "original": "KubeVirt is an open-source project that allows executing virtual machines in Kubernetes.",
  "refined": "KubeVirt is an open-source project designed to facilitate the execution of virtual machines within the Kubernetes framework.",
  "style": "formal",
  "model": "/models/Qwen/Qwen2.5-3B-Instruct",
  "usage": {
    "prompt_tokens": 92,
    "total_tokens": 115,
    "completion_tokens": 23
  }
}
```

#### Check Health

```bash
curl http://localhost:5173/health
```

**Response:**
```json
{
  "status": "ok",
  "vllm_status": "healthy",
  "vllm_url": "http://vllm:8000/v1"
}
```

#### View Configuration

```bash
curl http://localhost:5173/config
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Web Browser   │
│  localhost:5173 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│   Web Service   │─────▶│   vLLM Service   │
│   (FastAPI)     │      │  (OpenVINO GPU)  │
│   Port 5173     │      │   Port 8000      │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Qwen2 Model    │
                         │  1.5B-Instruct  │
                         │ (Local Volume)  │
                         └─────────────────┘
```

### Services

1. **downloader**: Downloads models from HuggingFace (one-time use)
2. **vllm**: Serves the LLM model with OpenVINO acceleration
3. **web**: Web interface and REST API with FastAPI

## ⚙️ Advanced Configuration

### Switch to a Different Model

**Recommended Models:**

| Model | Size | Speed | Quality | RAM Usage |
|-------|------|-------|---------|-----------|
| Qwen2-1.5B-Instruct | 1.5B | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~4GB |
| **Qwen2.5-3B-Instruct** | 3B | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~6GB |
| Qwen2.5-7B-Instruct | 7B | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~14GB |

To switch:

```bash
# 1. Edit .env
nano .env
# MODEL_ID=Qwen/Qwen2.5-7B-Instruct

# 2. Download new model
podman-compose --profile bootstrap up --build downloader

# 3. Restart services
podman-compose down
env MODEL_ID=Qwen/Qwen2.5-7B-Instruct \
    MAX_MODEL_LEN=8192 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

### Customize Technical Glossary

Edit [docker-compose.yml](docker-compose.yml) line 78:

```yaml
GLOSSARY_PASSTHROUGH: "control plane,namespace,pod,PV,PVC,SCC,Route,Ingress,Service,Deployment,StatefulSet,DaemonSet,CRD,etcd,API server,oc,kubectl,Helm,ArgoCD,GitOps,OpenShift"
```

Add your own terms separated by commas.

### Adjust Resource Limits

Edit [docker-compose.yml](docker-compose.yml) lines 42-48:

```yaml
deploy:
  resources:
    limits:
      cpus: "6"
      memory: 16g
    reservations:
      cpus: "2"
      memory: 8g
```

## 🐛 Troubleshooting

### Error: "workdir /app does not exist"

**Solution**: Rebuild the vLLM image:

```bash
podman-compose build vllm
podman-compose up -d vllm
```

### Error: "The model `X` does not exist"

**Cause**: Mismatch between downloaded model and configured model.

**Solution**:

```bash
# Check downloaded model
podman volume inspect local_translator_vllm_openvino_models

# Check model in vLLM
curl http://localhost:8000/v1/models

# Force environment variables
podman-compose down
env MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    MAX_MODEL_LEN=4096 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

### Slow Translation (>30s)

**Possible causes:**

1. **Model too large**: Switch to Qwen2-1.5B or 0.5B
2. **GPU not detected**: Verify `/dev/dri/renderD128`
3. **Limited resources**: Increase `memory` in docker-compose.yml

**Diagnosis**:

```bash
# Verify OpenVINO uses the GPU
podman exec -it local_translator_vllm_openvino_vllm_1 clinfo

# View vLLM logs
podman logs local_translator_vllm_openvino_vllm_1 | grep -i "gpu\|openvino"
```

### Blank Page in Browser

**Solution**: Clear browser cache:

- **Chrome/Brave**: `Ctrl + Shift + R`
- **Firefox**: `Ctrl + Shift + R`
- **Or**: Use incognito/private mode

## 📊 Performance

**Test Configuration:**
- CPU: Intel Core Ultra 7 165H
- GPU: Intel Arc Graphics (Meteor Lake)
- RAM: 64GB
- Model: Qwen2.5-3B-Instruct with FP8 KV Cache

**Results:**

| Text Length | Translation Time | Improvement vs 7B |
|------------|------------------|-------------------|
| 16 words | ~5-6s | 2.3x faster |
| 87 words | ~20-22s | 2.2x faster |

**Speed**: ~4-5 tokens/second with Intel Arc GPU + FP8 quantization

**Note**: The Qwen2.5-3B model with FP8 KV cache quantization provides excellent translation quality (equal or better than 7B) with **56% faster speed** and **60% less memory usage**. No hallucinations or spurious instructions observed.

## 🔒 Security

- ✅ **No Telemetry**: Everything works offline
- ✅ **No API Keys**: No external keys required
- ✅ **Local Data**: Translations never leave your machine
- ⚠️ **SELinux Disabled**: For `/dev/dri` (see docker-compose.yml:40)

**Production Recommendation**: Configure specific SELinux policies instead of `label=disable`.

## 📁 Project Structure

```
local_translator_vllm_openvino/
├── app/
│   ├── main.py              # FastAPI API
│   └── static/
│       └── index.html       # Web interface
├── docker-compose.yml       # Service orchestration
├── Dockerfile.downloader    # Image for model download
├── Dockerfile.vllm-openvino # vLLM image with OpenVINO
├── Dockerfile.web           # Web service image
├── download.py              # Download script
├── .env                     # Environment variables
└── README.md               # This file
```

## 🤝 Contributing

Contributions are welcome. Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project uses the following open source components:

- **vLLM**: Apache License 2.0
- **OpenVINO**: Apache License 2.0
- **Qwen2**: Qwen License (check on HuggingFace)
- **FastAPI**: MIT License

## 🙏 Acknowledgments

- [vLLM Project](https://github.com/vllm-project/vllm) - Inference engine
- [OpenVINO](https://github.com/openvinotoolkit/openvino) - Intel acceleration
- [Qwen Team](https://github.com/QwenLM/Qwen2) - LLM models
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Verify logs: `podman logs local_translator_vllm_openvino_vllm_1`
3. Open an issue in the repository

---

**Developed with ❤️ for offline technical translations**

---
---
---

# Traductor Técnico Trilingüe ES↔EN↔PT

Traductor técnico español-inglés-portugués usando LLM local con aceleración Intel Arc Graphics y OpenVINO.

## 🚀 Características

- **Traducción Trilingüe Automática**: Detecta automáticamente el idioma fuente (ES/EN/PT) y traduce a cualquier idioma destino
- **Selección Flexible de Idioma**: Elige el idioma destino o usa modo automático (ES/PT → EN, EN → ES)
- **Refinamiento con IA**: Mejora traducciones con 4 estilos (formal, conciso, claro, técnico)
- **LLM Local**: Utiliza Qwen2.5-3B-Instruct con cuantización FP8 KV cache ejecutándose completamente offline para traducciones de alta calidad
- **Aceleración por GPU**: Optimizado para Intel Arc Graphics con OpenVINO
- **Glosario Técnico**: Preserva términos técnicos de Kubernetes/OpenShift sin traducir
- **Interfaz Web Moderna**: UI responsive con retroalimentación en tiempo real y selector de idioma
- **API REST**: Endpoints documentados para integración

## 📋 Requisitos

### Hardware Recomendado
- **CPU**: Intel Core Ultra 7 (o similar con gráficos integrados Intel Arc)
- **RAM**: 16GB mínimo, 32GB+ recomendado
- **GPU**: Intel Arc Graphics (integrada o discreta)
- **Almacenamiento**: ~10GB para el modelo

### Software
- **SO**: Fedora 42 (o cualquier distro Linux moderna)
- **Podman**: Para ejecución de contenedores
- **podman-compose**: Para orquestación de servicios

## 🛠️ Instalación

### 1. Clonar el Repositorio

```bash
git clone <tu-repositorio>
cd local_translator_vllm_openvino
```

### 2. Configurar Variables de Entorno

Edita el archivo `.env`:

```bash
# Modelo a usar (3B para balance óptimo de calidad y velocidad)
MODEL_ID=Qwen/Qwen2.5-3B-Instruct
MAX_MODEL_LEN=8192
VLLM_PORT=8000
HUGGINGFACE_HUB_TOKEN=
```

**Nota**: `HUGGINGFACE_HUB_TOKEN` es opcional. Solo necesario para modelos privados.

### 3. Verificar Acceso a Intel GPU

```bash
ls -la /dev/dri/
# Deberías ver: renderD128 (Intel GPU)
```

### 4. Descargar el Modelo

```bash
podman-compose --profile bootstrap up --build downloader
```

Esto descarga el modelo Qwen2.5-3B-Instruct (~6GB) a un volumen persistente.

### 5. Iniciar los Servicios

```bash
env MODEL_ID=Qwen/Qwen2.5-3B-Instruct \
    MAX_MODEL_LEN=8192 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

**Importante**: Usar `env` para forzar las variables es necesario debido a limitaciones de caché en podman-compose.

### 6. Verificar el Estado

```bash
# Ver logs de vLLM
podman logs -f local_translator_vllm_openvino_vllm_1

# Esperar mensaje: "Application startup complete"
# Tiempo de inicio: ~2-3 minutos
```

## 🌐 Uso

### Interfaz Web

1. Abre tu navegador en: **http://localhost:5173**
2. Escribe o pega texto en español, inglés o portugués
3. **[Opcional]** Selecciona el idioma destino (Auto, EN, ES o PT)
4. Haz clic en "Traducir"
5. La traducción aparecerá en segundos
6. **[OPCIONAL]** Usa "Mejorar con IA" para refinar la traducción:
   - Selecciona un estilo: **Formal**, **Conciso**, **Claro** o **Técnico**
   - Haz clic en "Mejorar con IA"
   - El texto mejorado aparece en ~3-5 segundos

**Tiempos de Traducción Esperados:**
- Frase corta (10-20 palabras): ~5-6 segundos
- Párrafo mediano (30-50 palabras): ~8-12 segundos
- Texto largo (80+ palabras): ~20-22 segundos

**Estilos de Refinamiento con IA:**
- **Formal**: Tono más profesional y académico
- **Conciso**: Más breve, eliminando redundancias
- **Claro**: Lenguaje más simple, fácil de entender
- **Técnico**: Terminología técnica más precisa

### API REST

#### Traducir Texto

```bash
curl -X POST http://localhost:5173/translate \
  -F "text=KubeVirt es un proyecto de código abierto"
```

**Respuesta:**
```json
{
  "original": "KubeVirt es un proyecto de código abierto",
  "translated": "KubeVirt is an open-source project",
  "direction": "ES->EN",
  "model": "/models/Qwen/Qwen2.5-3B-Instruct",
  "usage": {
    "prompt_tokens": 145,
    "total_tokens": 163,
    "completion_tokens": 18
  }
}
```

#### Refinar/Mejorar Texto

```bash
curl -X POST http://localhost:5173/refine \
  -F "text=KubeVirt es un proyecto de código abierto que permite ejecutar máquinas virtuales en Kubernetes." \
  -F "style=formal"
```

**Estilos disponibles**: `formal`, `concise`, `clear`, `technical`

**Respuesta:**
```json
{
  "original": "KubeVirt es un proyecto de código abierto que permite ejecutar máquinas virtuales en Kubernetes.",
  "refined": "KubeVirt es un proyecto de código abierto diseñado para facilitar la ejecución de máquinas virtuales dentro del marco de Kubernetes.",
  "style": "formal",
  "model": "/models/Qwen/Qwen2.5-3B-Instruct",
  "usage": {
    "prompt_tokens": 95,
    "total_tokens": 125,
    "completion_tokens": 30
  }
}
```

#### Verificar Estado

```bash
curl http://localhost:5173/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "vllm_status": "healthy",
  "vllm_url": "http://vllm:8000/v1"
}
```

#### Ver Configuración

```bash
curl http://localhost:5173/config
```

## 🏗️ Arquitectura

```
┌─────────────────┐
│  Navegador Web  │
│  localhost:5173 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│   Web Service   │─────▶│   vLLM Service   │
│   (FastAPI)     │      │  (OpenVINO GPU)  │
│   Port 5173     │      │   Port 8000      │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Modelo Qwen2   │
                         │  1.5B-Instruct  │
                         │ (Volumen Local) │
                         └─────────────────┘
```

### Servicios

1. **downloader**: Descarga modelos de HuggingFace (uso único)
2. **vllm**: Sirve el modelo LLM con aceleración OpenVINO
3. **web**: Interfaz web y API REST con FastAPI

## ⚙️ Configuración Avanzada

### Cambiar a un Modelo Diferente

**Modelos Recomendados:**

| Modelo | Tamaño | Velocidad | Calidad | Uso RAM |
|--------|--------|-----------|---------|---------|
| Qwen2-1.5B-Instruct | 1.5B | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~4GB |
| **Qwen2.5-3B-Instruct** | 3B | ⚡⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~6GB |
| Qwen2.5-7B-Instruct | 7B | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~14GB |

Para cambiar:

```bash
# 1. Editar .env
nano .env
# MODEL_ID=Qwen/Qwen2.5-7B-Instruct

# 2. Descargar nuevo modelo
podman-compose --profile bootstrap up --build downloader

# 3. Reiniciar servicios
podman-compose down
env MODEL_ID=Qwen/Qwen2.5-7B-Instruct \
    MAX_MODEL_LEN=8192 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

### Personalizar el Glosario Técnico

Edita [docker-compose.yml](docker-compose.yml) línea 78:

```yaml
GLOSSARY_PASSTHROUGH: "control plane,namespace,pod,PV,PVC,SCC,Route,Ingress,Service,Deployment,StatefulSet,DaemonSet,CRD,etcd,API server,oc,kubectl,Helm,ArgoCD,GitOps,OpenShift"
```

Agrega tus propios términos separados por comas.

### Ajustar Límites de Recursos

Edita [docker-compose.yml](docker-compose.yml) líneas 42-48:

```yaml
deploy:
  resources:
    limits:
      cpus: "6"
      memory: 16g
    reservations:
      cpus: "2"
      memory: 8g
```

## 🐛 Solución de Problemas

### Error: "workdir /app does not exist"

**Solución**: Reconstruir la imagen vLLM:

```bash
podman-compose build vllm
podman-compose up -d vllm
```

### Error: "The model `X` does not exist"

**Causa**: Desajuste entre el modelo descargado y el configurado.

**Solución**:

```bash
# Verificar modelo descargado
podman volume inspect local_translator_vllm_openvino_models

# Verificar modelo en vLLM
curl http://localhost:8000/v1/models

# Forzar variables de entorno
podman-compose down
env MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    MAX_MODEL_LEN=4096 \
    VLLM_PORT=8000 \
    podman-compose up -d vllm web
```

### Traducción Lenta (>30s)

**Posibles causas:**

1. **Modelo muy grande**: Cambia a Qwen2-1.5B o 0.5B
2. **GPU no detectada**: Verifica `/dev/dri/renderD128`
3. **Recursos limitados**: Aumenta `memory` en docker-compose.yml

**Diagnóstico**:

```bash
# Verificar que OpenVINO usa la GPU
podman exec -it local_translator_vllm_openvino_vllm_1 clinfo

# Ver logs de vLLM
podman logs local_translator_vllm_openvino_vllm_1 | grep -i "gpu\|openvino"
```

### Página en Blanco en el Navegador

**Solución**: Limpiar caché del navegador:

- **Chrome/Brave**: `Ctrl + Shift + R`
- **Firefox**: `Ctrl + Shift + R`
- **O**: Usar modo incógnito

## 📊 Rendimiento

**Configuración de Prueba:**
- CPU: Intel Core Ultra 7 165H
- GPU: Intel Arc Graphics (Meteor Lake)
- RAM: 64GB
- Modelo: Qwen2.5-3B-Instruct con FP8 KV Cache

**Resultados:**

| Longitud del Texto | Tiempo de Traducción | Mejora vs 7B |
|-------------------|---------------------|--------------|
| 16 palabras | ~5-6s | 2.3x más rápido |
| 87 palabras | ~20-22s | 2.2x más rápido |

**Velocidad**: ~4-5 tokens/segundo con GPU Intel Arc + cuantización FP8

**Nota**: El modelo Qwen2.5-3B con cuantización FP8 KV cache proporciona excelente calidad de traducción (igual o mejor que 7B) con **56% más velocidad** y **60% menos uso de memoria**. Sin alucinaciones ni instrucciones espurias observadas.

## 🔒 Seguridad

- ✅ **Sin Telemetría**: Todo funciona offline
- ✅ **Sin API Keys**: No requiere claves externas
- ✅ **Datos Locales**: Las traducciones no salen de tu máquina
- ⚠️ **SELinux Deshabilitado**: Para `/dev/dri` (ver docker-compose.yml:40)

**Recomendación de Producción**: Configurar políticas SELinux específicas en lugar de `label=disable`.

## 📁 Estructura del Proyecto

```
local_translator_vllm_openvino/
├── app/
│   ├── main.py              # API FastAPI
│   └── static/
│       └── index.html       # Interfaz web
├── docker-compose.yml       # Orquestación de servicios
├── Dockerfile.downloader    # Imagen para descarga de modelos
├── Dockerfile.vllm-openvino # Imagen vLLM con OpenVINO
├── Dockerfile.web           # Imagen servicio web
├── download.py              # Script de descarga
├── .env                     # Variables de entorno
└── README.md               # Este archivo
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork del proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📝 Licencia

Este proyecto usa los siguientes componentes open source:

- **vLLM**: Apache License 2.0
- **OpenVINO**: Apache License 2.0
- **Qwen2**: Qwen License (verificar en HuggingFace)
- **FastAPI**: MIT License

## 🙏 Agradecimientos

- [vLLM Project](https://github.com/vllm-project/vllm) - Inference engine
- [OpenVINO](https://github.com/openvinotoolkit/openvino) - Aceleración Intel
- [Qwen Team](https://github.com/QwenLM/Qwen2) - Modelos LLM
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección [Solución de Problemas](#-solución-de-problemas)
2. Verifica los logs: `podman logs local_translator_vllm_openvino_vllm_1`
3. Abre un issue en el repositorio

---

**Desarrollado con ❤️ para traducciones técnicas offline**
