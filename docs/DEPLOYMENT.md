# Blue-Green Deployment Strategy

## Обзор

Проект реализует **Blue-Green Deployment** стратегию для безопасного развертывания ML моделей с нулевым временем простоя (zero-downtime).

## Архитектура

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ :50050
       ▼
┌─────────────┐
│    Nginx    │
│ Load Balancer│
└──────┬──────┘
       │
       ├─────────────┬─────────────┐
       │             │             │
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│   Blue   │  │  Green   │  │ Inactive │
│ v1.0.0   │  │ v1.1.0   │  │          │
│ :50051   │  │ :50051   │  │          │
└──────────┘  └──────────┘  └──────────┘
  Active        Standby
```

## Компоненты

### 1. Blue Environment (v1.0.0)
- Текущая стабильная версия
- Обслуживает production трафик
- Порт: 50051 (внутри Docker сети)

### 2. Green Environment (v1.1.0)
- Новая версия для тестирования
- Готова к переключению
- Порт: 50051 (внутри Docker сети)

### 3. Nginx Load Balancer
- Маршрутизация трафика
- Health check мониторинг
- Порт: 50050 (внешний)

## Развертывание

### Локальное развертывание

1. **Запуск всей инфраструктуры:**
```bash
docker-compose -f docker-compose.nginx.yml up -d
```

2. **Проверка статуса:**
```bash
docker ps
```

Ожидаемый вывод:
```
CONTAINER ID   IMAGE                  STATUS
xxx            ml-nginx-lb            Up (healthy)
xxx            ml-service-blue        Up (healthy)
xxx            ml-service-green       Up (healthy)
```

3. **Проверка через Nginx:**
```bash
# Health check
python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
channel = grpc.insecure_channel('localhost:50050')
stub = model_pb2_grpc.PredictionServiceStub(channel)
response = stub.Health(model_pb2.HealthRequest())
print(f'Status: {response.status}, Version: {response.model_version}')
"

# Prediction
python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
channel = grpc.insecure_channel('localhost:50050')
stub = model_pb2_grpc.PredictionServiceStub(channel)
response = stub.Predict(model_pb2.PredictRequest(features=[5.1, 3.5, 1.4, 0.2]))
print(f'Prediction: {response.prediction}, Confidence: {response.confidence:.4f}')
"
```

### Blue-Green Switch

**Переключение с Blue на Green:**
```bash
./scripts/switch.sh
```

Скрипт выполняет:
1. ✅ Health check для целевой версии
2. 📦 Backup текущей конфигурации Nginx
3. 🔄 Обновление конфигурации
4. ♻️ Reload Nginx (без downtime)
5. ✅ Проверка успешности переключения

**Откат к предыдущей версии:**
```bash
./scripts/rollback.sh
```

### CI/CD Развертывание

#### GitHub Actions Workflow

Workflow `.github/workflows/deploy.yml` автоматически:
1. Собирает Docker образ
2. Публикует в GitHub Container Registry (GHCR)
3. Выполняет health checks
4. Тестирует prediction endpoint

#### Триггеры

**Автоматический (push в main):**
```bash
git push origin main
```

**Ручной (с выбором версии):**
1. Перейти в GitHub → Actions → Model Deployment
2. Нажать "Run workflow"
3. Выбрать версию модели (v1.0.0 или v1.1.0)
4. Нажать "Run workflow"

#### Необходимые секреты

GitHub автоматически предоставляет `GITHUB_TOKEN` для GHCR. Дополнительные секреты не требуются для базового функционала.

## Мониторинг

### Health Checks

**Nginx:**
```bash
docker exec ml-nginx-lb nginx -t
```

**Blue service:**
```bash
docker exec ml-service-blue python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
channel = grpc.insecure_channel('localhost:50051')
stub = model_pb2_grpc.PredictionServiceStub(channel)
response = stub.Health(model_pb2.HealthRequest())
print(f'Blue: {response.status} - {response.model_version}')
"
```

**Green service:**
```bash
docker exec ml-service-green python -c "
import grpc
from generated import model_pb2, model_pb2_grpc
channel = grpc.insecure_channel('localhost:50051')
stub = model_pb2_grpc.PredictionServiceStub(channel)
response = stub.Health(model_pb2.HealthRequest())
print(f'Green: {response.status} - {response.model_version}')
"
```

### Логи

**Nginx логи:**
```bash
docker logs ml-nginx-lb
```

**Service логи:**
```bash
docker logs ml-service-blue
docker logs ml-service-green
```

## Troubleshooting

### Проблема: Health check не проходит

**Диагностика:**
```bash
docker ps
docker logs ml-service-blue
docker logs ml-service-green
```

**Решение:** Проверить, что модель загружается корректно и порты не заняты.

### Проблема: Nginx не может подключиться к service

**Диагностика:**
```bash
docker network inspect hw2_ml-network
```

**Решение:** Убедиться, что все контейнеры в одной Docker сети.

### Проблема: Switch не работает

**Диагностика:**
```bash
cat nginx/nginx.conf
docker exec ml-nginx-lb nginx -t
```

**Решение:** Проверить синтаксис конфигурации Nginx.

## Преимущества Blue-Green

### ✅ Преимущества:
- **Zero downtime** - переключение без остановки сервиса
- **Instant rollback** - откат за секунды
- **Testing in production** - новая версия доступна для тестирования
- **Easy to understand** - простая концепция
- **Low risk** - старая версия всегда доступна

### ⚠️ Недостатки:
- **Resource usage** - требует 2x ресурсов
- **Database migrations** - требует совместимости схем
- **State management** - сложно для stateful приложений

## Сравнение с Canary

| Характеристика | Blue-Green | Canary |
|---------------|------------|---------|
| Скорость переключения | Мгновенно | Постепенно |
| Использование ресурсов | 200% | 110-200% |
| Сложность | Низкая | Средняя |
| Откат | Мгновенный | Быстрый |
| A/B тестирование | Нет | Да |

## Best Practices

1. **Всегда проверяйте health** перед переключением
2. **Сохраняйте backup** конфигурации
3. **Тестируйте rollback** процедуру
4. **Мониторьте метрики** после переключения
5. **Автоматизируйте** через CI/CD
6. **Версионируйте** модели явно
7. **Логируйте** все операции переключения

## Следующие шаги

После успешного развертывания:
1. Настроить мониторинг метрик (Prometheus + Grafana)
2. Добавить автоматический rollback при ошибках
3. Настроить алерты на критические метрики
4. Интегрировать с системой логирования (ELK Stack)
5. Добавить canary deployments для постепенного раската
