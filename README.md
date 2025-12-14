# gRPC ML Service with Blue-Green Deployment

Минимальный gRPC-сервис для обслуживания ML-моделей с эндпоинтами Health и Predict. Реализована стратегия Blue-Green deployment для безопасного развертывания новых версий моделей.

## Описание

Проект реализует gRPC сервис на Python для обслуживания ML-модели (LogisticRegression на датасете Iris) с полной автоматизацией CI/CD и стратегией Blue-Green deployment.

### Основные возможности:
- ✅ gRPC API с эндпоинтами `/health` и `/predict`
- ✅ Blue-Green deployment для zero-downtime обновлений
- ✅ Автоматический CI/CD через GitHub Actions
- ✅ Nginx load balancer для маршрутизации трафика
- ✅ Instant rollback при ошибках
- ✅ Health checks и мониторинг
- ✅ Версионирование моделей (v1.0.0, v1.1.0)

## Структура проекта

```
/Users/Shared/ml/DEPLOY/HW2/
├── protos/
│   └── model.proto              # Protocol Buffers контракт API
├── generated/
│   ├── model_pb2.py            # Сгенерированные message классы
│   └── model_pb2_grpc.py       # Сгенерированные gRPC stubs
├── server/
│   └── server.py               # gRPC сервер
├── client/
│   └── client.py               # Тестовый клиент
├── models/
│   ├── v1.0.0/
│   │   └── model.pkl           # Модель версии 1.0.0
│   └── v1.1.0/
│       └── model.pkl           # Модель версии 1.1.0
├── nginx/
│   ├── nginx.conf              # Конфигурация для Blue
│   └── nginx-green.conf        # Конфигурация для Green
├── scripts/
│   ├── switch.sh               # Скрипт переключения Blue↔Green
│   └── rollback.sh             # Скрипт отката
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline
├── docs/
│   ├── DEPLOYMENT.md           # Документация по деплою
│   ├── TEST_RESULTS.md         # Результаты тестирования
│   └── screenshots/            # Скриншоты для отчета
├── docker-compose.blue.yml     # Blue environment
├── docker-compose.green.yml    # Green environment
├── docker-compose.nginx.yml    # Полная инфраструктура
├── requirements.txt            # Python зависимости
├── Dockerfile                  # Docker конфигурация
└── README.md                   # Этот файл
```

## Технологии

- **Python**: 3.12
- **gRPC**: 1.60.0
- **Protocol Buffers**: 4.25.1
- **scikit-learn**: 1.3.2
- **Docker**: python:3.11-slim

## Локальная разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Генерация кода из proto файлов

```bash
./generate_proto.sh
```

Или вручную:
```bash
python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ./protos/model.proto
```

### Запуск сервера

```bash
python -m server.server
```

Сервер запустится на порту 50051 и выведет:
```
Server started on port 50051
Model version: v1.0.0
Model path: models/model.pkl
```

### Тестирование клиентом

В новом терминале:
```bash
python -m client.client
```

Ожидаемый вывод:
```
==================================================
Testing Health endpoint
==================================================
Status: ok
Model Version: v1.0.0
Health check: OK

==================================================
Testing Predict endpoint
==================================================
Input features: [5.1, 3.5, 1.4, 0.2]
Prediction: 0
Confidence: 0.9766
Model Version: v1.0.0
Prediction: OK

==================================================
Test Results
==================================================
Health check: PASS
Predict test: PASS
Overall: ALL TESTS PASSED
==================================================
```

## Docker

### Простой запуск (для разработки)

```bash
docker build -t grpc-ml-service .
docker run -p 50051:50051 grpc-ml-service
```

### Blue-Green Deployment (production)

#### Запуск всей инфраструктуры

```bash
docker-compose -f docker-compose.nginx.yml up -d
```

Это запустит:
- **Blue environment** (v1.0.0)
- **Green environment** (v1.1.0)
- **Nginx load balancer** (порт 50050)

#### Проверка статуса

```bash
docker ps
```

#### Тестирование через Nginx

```bash
python test_blue_green.py
```

#### Переключение Blue → Green

```bash
./scripts/switch.sh
```

#### Откат на предыдущую версию

```bash
./scripts/rollback.sh
```

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `PORT` | 50051 | Порт gRPC сервера |
| `MODEL_PATH` | /app/models/v1.0.0/model.pkl | Путь к файлу модели |
| `MODEL_VERSION` | v1.0.0 | Версия модели |

### Архитектура Blue-Green

```
Client → Nginx (50050) → Blue (v1.0.0) или Green (v1.1.0)
```

**Преимущества:**
- Zero-downtime deployment
- Instant rollback
- Тестирование новой версии в production
```

## API

### Health

Проверка состояния сервиса.

**Request:**
```protobuf
message HealthRequest {}
```

**Response:**
```protobuf
message HealthResponse {
    string status = 1;           // "ok" или "error"
    string model_version = 2;    // Версия модели
}
```

**Пример:**
```bash
grpcurl -plaintext localhost:50051 mlservice.v1.PredictionService/Health
```

**Ответ:**
```json
{
  "status": "ok",
  "modelVersion": "v1.0.0"
}
```

### Predict

Получение предсказания от модели.

**Request:**
```protobuf
message PredictRequest {
    repeated float features = 1;  // Массив признаков [4 элемента для Iris]
}
```

**Response:**
```protobuf
message PredictResponse {
    string prediction = 1;        // Класс (0, 1, или 2)
    float confidence = 2;         // Уверенность (0.0 - 1.0)
    string model_version = 3;     // Версия модели
}
```

**Пример:**
```python
import grpc
from generated import model_pb2, model_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = model_pb2_grpc.PredictionServiceStub(channel)

request = model_pb2.PredictRequest(features=[5.1, 3.5, 1.4, 0.2])
response = stub.Predict(request)

print(f"Prediction: {response.prediction}")
print(f"Confidence: {response.confidence}")
```

## Модель

Используется LogisticRegression из scikit-learn, обученная на датасете Iris:
- **Датасет**: Iris (150 образцов, 4 признака, 3 класса)
- **Модель**: LogisticRegression
- **Точность**: 100% на тестовой выборке
- **Формат**: pickle (.pkl)

### Переобучение модели

```bash
python train_model.py
```

## CI/CD

Проект использует GitHub Actions для автоматического развертывания.

### Workflow

При push в `main` автоматически:
1. Собирается Docker образ
2. Публикуется в GitHub Container Registry (GHCR)
3. Выполняются health checks
4. Тестируется prediction endpoint

### Ручной запуск

1. Перейти: **GitHub → Actions → Model Deployment**
2. **Run workflow**
3. Выбрать версию модели (v1.0.0 или v1.1.0)
4. **Run workflow**

### Секреты

GitHub автоматически предоставляет `GITHUB_TOKEN` для GHCR.

## Разработка

### Требования

- Python 3.11+
- Docker & Docker Compose
- Git

### Команды разработки

```bash
# Генерация proto кода
./generate_proto.sh

# Обучение модели v1.0.0
python train_model.py

# Обучение модели v1.1.0
python train_model_v2.py

# Запуск сервера (локально)
python -m server.server

# Тестирование клиентом
python -m client.client

# Тестирование Blue-Green
python test_blue_green.py
```

### Команды деплоя

```bash
# Запуск Blue-Green инфраструктуры
docker-compose -f docker-compose.nginx.yml up -d

# Переключение версий
./scripts/switch.sh

# Откат
./scripts/rollback.sh

# Остановка
docker-compose -f docker-compose.nginx.yml down
```

## Документация

- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - полная документация по Blue-Green deployment
- **[TEST_RESULTS.md](docs/TEST_RESULTS.md)** - результаты тестирования
- **[LEARNING_GUIDE.md](LEARNING_GUIDE.md)** - обучающее руководство по MLOps
- **[TASK3_PLAN.md](docs/TASK3_PLAN.md)** - план выполнения задания 3

## Результаты тестирования

✅ Все тесты пройдены успешно (13/13)

| Категория | Статус |
|-----------|--------|
| Health Endpoints | ✅ PASS |
| Predict Endpoints | ✅ PASS |
| Blue-Green Switch | ✅ PASS |
| Rollback | ✅ PASS |
| Zero-downtime | ✅ PASS |
| Docker Build | ✅ PASS |

Подробнее: [TEST_RESULTS.md](docs/TEST_RESULTS.md)

## Репозиторий

GitHub: [https://github.com/kazdoraw/Minimal-gRPC-service-for-serving-ML-models](https://github.com/kazdoraw/Minimal-gRPC-service-for-serving-ML-models)

## Задания

- ✅ **Задание 2**: Minimal gRPC service for serving ML models
- ✅ **Задание 3**: Blue-Green deployment strategy with CI/CD

## Автор

Проект выполнен в рамках курса MLOps:
- Модуль 2: «Архитектурные паттерны для обслуживания ML-моделей»
- Модуль 3: «Автоматизированное развертывание с помощью CI/CD»

## Лицензия

Учебный проект.
