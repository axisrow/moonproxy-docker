from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
from datetime import datetime, timedelta
import jwt
import hashlib
import json
from pathlib import Path

app = FastAPI(title="MoonProxy", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("MOONPROXY_SECRET_KEY", "change-this-secret-key")
ADMIN_PASSWORD = os.getenv("MOONPROXY_ADMIN_PASSWORD", "admin123")

# Data storage
DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(exist_ok=True)
TOKENS_FILE = DATA_DIR / "tokens.json"
CONFIG_FILE = DATA_DIR / "config.json"


class TokenRequest(BaseModel):
    provider: str  # openai, anthropic, etc.
    api_key: str
    model: Optional[str] = None
    endpoint: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    token_id: str
    provider: str
    model: Optional[str] = None
    created_at: str


class ProxyRequest(BaseModel):
    model: str
    messages: List[dict]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


def load_tokens() -> dict:
    """Загрузка токенов из файла"""
    if TOKENS_FILE.exists():
        with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_tokens(tokens: dict):
    """Сохранение токенов в файл"""
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)


def load_config() -> dict:
    """Загрузка конфигурации"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def generate_token_id(api_key: str) -> str:
    """Генерация уникального ID токена"""
    return hashlib.sha256(api_key.encode() + datetime.now().isoformat().encode()).hexdigest()[:16]


def generate_jwt_token(token_id: str) -> str:
    """Генерация JWT токена"""
    payload = {
        'token_id': token_id,
        'exp': datetime.now() + timedelta(days=365)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def verify_jwt_token(token: str) -> dict:
    """Верификация JWT токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "MoonProxy",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "admin": "/admin",
            "tokens": "/tokens",
            "proxy": "/v1/chat/completions"
        }
    }


@app.post("/admin/create-token")
async def create_token(request: TokenRequest, admin_password: Optional[str] = None):
    """Создание нового токена (требует админ пароль)"""
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")

    tokens = load_tokens()

    # Проверка на дубликаты
    for token_data in tokens.values():
        if token_data.get('api_key') == request.api_key and token_data.get('provider') == request.provider:
            # Если токен уже существует, возвращаем его
            jwt_token = generate_jwt_token(token_data['token_id'])
            return TokenResponse(
                token=jwt_token,
                token_id=token_data['token_id'],
                provider=token_data['provider'],
                model=token_data.get('model'),
                created_at=token_data['created_at']
            )

    # Создание нового токена
    token_id = generate_token_id(request.api_key)
    jwt_token = generate_jwt_token(token_id)

    tokens[token_id] = {
        'token_id': token_id,
        'provider': request.provider,
        'api_key': request.api_key,
        'model': request.model,
        'endpoint': request.endpoint,
        'created_at': datetime.now().isoformat(),
        'last_used': None
    }

    save_tokens(tokens)

    return TokenResponse(
        token=jwt_token,
        token_id=token_id,
        provider=request.provider,
        model=request.model,
        created_at=datetime.now().isoformat()
    )


@app.get("/admin/list-tokens")
async def list_tokens(admin_password: Optional[str] = None):
    """Получение списка всех токенов"""
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")

    tokens = load_tokens()
    result = []

    for token_data in tokens.values():
        result.append({
            'token_id': token_data['token_id'],
            'provider': token_data['provider'],
            'model': token_data.get('model'),
            'created_at': token_data['created_at'],
            'last_used': token_data.get('last_used')
        })

    return {"tokens": result}


@app.delete("/admin/delete-token/{token_id}")
async def delete_token(token_id: str, admin_password: Optional[str] = None):
    """Удаление токена"""
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")

    tokens = load_tokens()

    if token_id not in tokens:
        raise HTTPException(status_code=404, detail="Token not found")

    del tokens[token_id]
    save_tokens(tokens)

    return {"message": "Token deleted successfully"}


@app.post("/v1/chat/completions")
async def proxy_completion(
    request: ProxyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Проксирование запроса к API провайдера"""

    # Верификация JWT токена
    payload = verify_jwt_token(credentials.credentials)
    token_id = payload['token_id']

    # Получение информации о токене
    tokens = load_tokens()
    if token_id not in tokens:
        raise HTTPException(status_code=401, detail="Token not found")

    token_data = tokens[token_id]

    # Обновление времени последнего использования
    token_data['last_used'] = datetime.now().isoformat()
    save_tokens(tokens)

    # Определение endpoint для запроса
    provider = token_data['provider']
    api_key = token_data['api_key']

    endpoints = {
        'openai': 'https://api.openai.com/v1/chat/completions',
        'anthropic': 'https://api.anthropic.com/v1/messages',
        'openrouter': 'https://openrouter.ai/api/v1/chat/completions'
    }

    # Если указан кастомный endpoint
    if token_data.get('endpoint'):
        endpoint = token_data['endpoint']
    else:
        endpoint = endpoints.get(provider)
        if not endpoint:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    # Подготовка headers для запроса
    headers = {}
    if provider == 'openai':
        headers['Authorization'] = f'Bearer {api_key}'
        headers['Content-Type'] = 'application/json'
    elif provider == 'anthropic':
        headers['x-api-key'] = api_key
        headers['anthropic-version'] = '2023-06-01'
        headers['Content-Type'] = 'application/json'
    elif provider == 'openrouter':
        headers['Authorization'] = f'Bearer {api_key}'
        headers['Content-Type'] = 'application/json'

    # Подготовка данных запроса
    request_data = request.model_dump()

    # Если указана модель в токене, заменяем её
    if token_data.get('model'):
        request_data['model'] = token_data['model']

    # Отправка запроса
    async with httpx.AsyncClient() as client:
        try:
            if provider == 'anthropic':
                # Для Anthropic нужен другой формат запроса
                anthropic_request = {
                    'model': request_data.get('model', 'claude-3-sonnet-20240229'),
                    'max_tokens': request_data.get('max_tokens', 1024),
                    'messages': request_data.get('messages', [])
                }
                if 'temperature' in request_data:
                    anthropic_request['temperature'] = request_data['temperature']

                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=anthropic_request,
                    timeout=60.0
                )
            else:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=request_data,
                    timeout=60.0
                )

            # Возврат ответа клиенту
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    tokens = load_tokens()
    return {
        "status": "healthy",
        "tokens_count": len(tokens),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
