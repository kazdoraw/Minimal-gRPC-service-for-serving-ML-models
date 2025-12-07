# gRPC ML Service

Минимальный gRPC-сервис для обслуживания ML-моделей с эндпоинтами Health и Predict.

## Описание

Проект реализует gRPC сервис на Python для обслуживания ML-модели (LogisticRegression на датасете Iris). Сервис предоставляет два эндпоинта:
- `/health` - проверка состояния сервиса и версии модели
- `/predict` - получение предсказаний от ML-модели

## Структура проекта

```
ml_grpc_service/
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
│   └── model.pkl               # Обученная ML модель
├── memory-bank/                # Документация разработки
├── requirements.txt            # Python зависимости
├── Dockerfile                  # Docker конфигурация
├── .dockerignore              # Исключения для Docker
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

### Сборка образа

```bash
docker build -t grpc-ml-service .
```

### Запуск контейнера

```bash
docker run -p 50051:50051 grpc-ml-service
```

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `PORT` | 50051 | Порт gRPC сервера |
| `MODEL_PATH` | /app/models/model.pkl | Путь к файлу модели |
| `MODEL_VERSION` | v1.0.0 | Версия модели |

Пример запуска с кастомными переменными:
```bash
docker run -p 50051:50051 \
  -e MODEL_VERSION=v2.0.0 \
  grpc-ml-service
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

## Разработка

### Требования

- Python 3.11+
- Docker (для контейнеризации)
- grpcurl (опционально, для тестирования)

### Команды

```bash
# Генерация proto кода
./generate_proto.sh

# Обучение модели
python train_model.py

# Запуск сервера
python -m server.server

# Запуск клиента
python -m client.client

# Docker сборка
docker build -t grpc-ml-service .

# Docker запуск
docker run -p 50051:50051 grpc-ml-service
```

## Автор

Проект выполнен в рамках модуля «Архитектурные паттерны для обслуживания ML-моделей».

## Лицензия

Учебный проект.
