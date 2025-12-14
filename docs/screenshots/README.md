# Скриншоты тестирования

## Инструкции для создания скриншотов

### 1. Health endpoint (Blue - v1.0.0)
```bash
python test_blue_green.py
```
Сделать скриншот вывода с успешным тестом health endpoint.

### 2. Predict endpoint (Blue - v1.0.0)
Вывод уже включен в test_blue_green.py, показывает predictions для всех классов.

### 3. Docker containers status
```bash
docker ps
```
Показать все запущенные контейнеры (Blue, Green, Nginx).

### 4. Blue-Green Switch
```bash
./scripts/switch.sh
```
Показать процесс переключения с Blue на Green.

### 5. Health endpoint после switch (Green - v1.1.0)
```bash
python test_blue_green.py
```
Показать, что версия изменилась на v1.1.0.

### 6. Rollback
```bash
./scripts/rollback.sh
```
Показать откат обратно на Blue (v1.0.0).

### 7. GitHub Actions (если запущен)
Скриншот успешного workflow из GitHub Actions.

## Примеры выводов для документации

### Health Check (Blue v1.0.0)
```
Testing Nginx Load Balancer (Active) on port 50050
1. Health Check:
   Status:        ok
   Model Version: v1.0.0
```

### Predict (Blue v1.0.0)
```
2. Prediction Test:
   Input:         [5.1, 3.5, 1.4, 0.2]
   Prediction:    0
   Confidence:    0.9766
   Model Version: v1.0.0
```

### Multiple Predictions
```
3. Multiple predictions:
   [5.1, 3.5, 1.4, 0.2] → class 0 (conf: 0.9766)
   [6.3, 2.5, 4.9, 1.5] → class 1 (conf: 0.5627)
   [6.5, 3.0, 5.8, 2.2] → class 2 (conf: 0.9758)
```

### Blue-Green Switch Success
```
=== Blue-Green Deployment Switch ===
Current active: blue
Switching to: green (v1.1.0)
✅ Health check passed for green
✅ Backup created
✅ Configuration updated
✅ Nginx reloaded
✅ Switch successful!
Active version: v1.1.0
```

### Rollback Success
```
=== Blue-Green Deployment Rollback ===
Current active: green
✅ Configuration restored
✅ Configuration valid
✅ Nginx reloaded
✅ Rollback successful!
Version: v1.0.0, Status: ok
```
