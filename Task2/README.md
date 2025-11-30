# Инструкция по запуску динамического масштабирования контейнеров

Данная инструкция описывает процесс настройки и тестирования динамического масштабирования в Kubernetes с использованием Minikube.

## Быстрый старт

### Минимальные шаги для запуска Части 1 (масштабирование по памяти):

```bash
# 1. Запуск Minikube и активация metrics-server
minikube start
minikube addons enable metrics-server

# 2. Развертывание приложения
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa-memory.yaml

# 3. Получение URL сервиса
minikube service scaletestapp-service --url

# 4. Запуск Locust (в директории с locustfile.py)
locust

# 5. Открыть http://localhost:8089 и запустить нагрузку
# 6. Мониторинг: minikube dashboard или watch kubectl get hpa
```

### Минимальные шаги для запуска Части 2 (масштабирование по RPS):

```bash
# 1. Установка Prometheus
kubectl apply -f prometheus-namespace.yaml
kubectl apply -f prometheus-rbac.yaml
kubectl apply -f prometheus-configmap.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f prometheus-service.yaml

# 2. Установка Prometheus Adapter
kubectl apply -f prometheus-adapter-config.yaml
kubectl apply -f prometheus-adapter-rbac.yaml
kubectl apply -f prometheus-adapter-deployment.yaml
kubectl apply -f prometheus-adapter-service.yaml
kubectl apply -f prometheus-adapter-api-service.yaml

# 3. Настройка HPA для RPS
kubectl delete -f hpa-memory.yaml  # Удалить старый HPA
kubectl apply -f hpa-rps.yaml

# 4. Проверка метрик в Prometheus
minikube service prometheus -n monitoring --url
# Открыть в браузере и проверить метрики

# 5. Запуск нагрузочного теста (аналогично Части 1)
```

## Предварительные требования

1. **Minikube** - установлен и настроен
   - Скачать: https://minikube.sigs.k8s.io/docs/start/
   - Для Windows: `choco install minikube` или скачать с официального сайта
2. **kubectl** - установлен и настроен
   - Скачать: https://kubernetes.io/docs/tasks/tools/
   - Для Windows: `choco install kubernetes-cli`
3. **Python 3** - для запуска Locust
   - Скачать: https://www.python.org/downloads/
4. **Locust** - установлен
   ```bash
   pip install locust
   ```

**Проверка установки:**
```bash
minikube version
kubectl version --client
python --version
locust --version
```

## Часть 1. Динамическое масштабирование по памяти

### Шаг 1: Запуск Minikube

```bash
# Запустите Minikube кластер
minikube start

# Для Windows может потребоваться указать драйвер
# minikube start --driver=hyperv
# или
# minikube start --driver=docker

# Проверьте статус кластера
kubectl cluster-info

# Проверьте, что Minikube работает
minikube status
```

### Шаг 2: Активация metrics-server

```bash
# Включите metrics-server в Minikube
minikube addons enable metrics-server

# Проверьте, что metrics-server запущен
kubectl get pods -n kube-system | grep metrics-server

# Подождите несколько секунд, пока metrics-server начнет собирать метрики
kubectl top nodes
```

### Шаг 3: Развертывание тестового приложения

```bash
# Примените манифест Deployment
kubectl apply -f deployment.yaml

# Проверьте статус развертывания
kubectl get deployments
kubectl get pods -l app=scaletestapp

# Дождитесь, пока под перейдет в состояние Running
kubectl wait --for=condition=ready pod -l app=scaletestapp --timeout=60s
```

### Шаг 4: Создание Service

```bash
# Примените манифест Service
kubectl apply -f service.yaml

# Проверьте создание сервиса
kubectl get svc scaletestapp-service

# Получите URL для доступа к сервису
minikube service scaletestapp-service --url
```

### Шаг 5: Настройка HPA для масштабирования по памяти

```bash
# Примените манифест HPA
kubectl apply -f hpa-memory.yaml

# Проверьте создание HPA
kubectl get hpa scaletestapp-hpa-memory

# Посмотрите детальную информацию о HPA
kubectl describe hpa scaletestapp-hpa-memory
```

### Шаг 6: Тестирование масштабирования по памяти

#### 6.1: Установка Locust

```bash
# Установите Locust через pip
pip install locust
```

#### 6.2: Подготовка Locustfile

Файл `locustfile.py` уже создан в директории Task2. Убедитесь, что он находится в текущей директории.

#### 6.3: Получение URL сервиса

```bash
# Получите URL сервиса для использования в Locust
SERVICE_URL=$(minikube service scaletestapp-service --url)
echo "Service URL: $SERVICE_URL"
```

#### 6.4: Запуск Locust

**Способ 1: Через переменную окружения**

```bash
# Для Windows PowerShell:
$SERVICE_URL = minikube service scaletestapp-service --url
$env:LOCUST_HOST = $SERVICE_URL
locust

# Для Linux/Mac:
SERVICE_URL=$(minikube service scaletestapp-service --url)
LOCUST_HOST=$SERVICE_URL locust
```

**Способ 2: Изменение locustfile.py (рекомендуется)**

Откройте файл `locustfile.py` и добавьте `host` в класс:

```python
from locust import HttpUser, between, task

class WebsiteUser(HttpUser):
    host = "http://<SERVICE_URL>"  # Замените на ваш URL (например: http://192.168.49.2:31234)
    wait_time = between(1, 5)

    @task
    def index(self):
        self.client.get("/")
```

Затем просто запустите:
```bash
locust
```

**Примечание:** URL можно получить командой `minikube service scaletestapp-service --url`

#### 6.5: Настройка и запуск теста в веб-интерфейсе Locust

1. Откройте браузер и перейдите по адресу: `http://localhost:8089`
2. В поле "Number of users" введите количество пользователей (например, 50)
3. В поле "Spawn rate" введите скорость создания пользователей (например, 5)
4. Нажмите кнопку "Start swarming"

#### 6.6: Мониторинг масштабирования

В другом терминале выполните:

```bash
# Откройте Kubernetes Dashboard
minikube dashboard

# Или отслеживайте HPA в реальном времени
# Для Linux/Mac:
watch kubectl get hpa scaletestapp-hpa-memory

# Для Windows PowerShell (альтернатива watch):
while ($true) { kubectl get hpa scaletestapp-hpa-memory; Start-Sleep -Seconds 2; Clear-Host }

# Или отслеживайте количество подов
# Для Linux/Mac:
watch kubectl get pods -l app=scaletestapp

# Для Windows PowerShell:
while ($true) { kubectl get pods -l app=scaletestapp; Start-Sleep -Seconds 2; Clear-Host }

# Посмотрите метрики использования памяти
kubectl top pods -l app=scaletestapp
```

#### 6.7: Анализ результатов

После запуска нагрузки вы должны увидеть:
- Увеличение количества реплик при росте использования памяти
- Уменьшение количества реплик при снижении нагрузки
- В дашборде Kubernetes можно увидеть графики изменения количества подов

## Часть 2. Динамическое масштабирование по RPS (запросов в секунду)

### Шаг 1: Установка Prometheus

```bash
# Создайте namespace для мониторинга
kubectl apply -f prometheus-namespace.yaml

# Примените RBAC для Prometheus
kubectl apply -f prometheus-rbac.yaml

# Создайте ConfigMap с конфигурацией Prometheus
kubectl apply -f prometheus-configmap.yaml

# Разверните Prometheus
kubectl apply -f prometheus-deployment.yaml

# Создайте Service для Prometheus
kubectl apply -f prometheus-service.yaml

# Проверьте статус Prometheus
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### Шаг 2: Доступ к Prometheus Web UI

```bash
# Получите URL для доступа к Prometheus
minikube service prometheus -n monitoring --url

# Или откройте через port-forward
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

Затем откройте в браузере: `http://localhost:9090`

### Шаг 3: Проверка сбора метрик

1. В Prometheus Web UI перейдите в раздел **Status → Targets**
2. Убедитесь, что target `scaletestapp` находится в состоянии **UP**
3. Перейдите в раздел **Graph**
4. Выполните запросы для проверки:
   - `http_requests_total` - общее количество запросов
   - `rate(http_requests_total[2m])` - скорость запросов в секунду
   - `sum(rate(http_requests_total[2m])) by (pod)` - RPS по подам
5. Убедитесь, что метрики отображаются и обновляются

**Альтернативная проверка через командную строку:**
```bash
# Проверьте метрики приложения напрямую
kubectl port-forward svc/scaletestapp-service 8080:80
# В другом терминале:
curl http://localhost:8080/metrics

# Проверьте, что Prometheus видит метрики
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Затем в браузере откройте: http://localhost:9090
```

### Шаг 4: Установка Prometheus Adapter

Prometheus Adapter необходим для предоставления кастомных метрик в Kubernetes API.

```bash
# Создайте ConfigMap для адаптера
kubectl apply -f prometheus-adapter-config.yaml

# Примените RBAC для адаптера
kubectl apply -f prometheus-adapter-rbac.yaml

# Разверните адаптер
kubectl apply -f prometheus-adapter-deployment.yaml

# Создайте Service для адаптера
kubectl apply -f prometheus-adapter-service.yaml

# Создайте API Service для метрик
kubectl apply -f prometheus-adapter-api-service.yaml

# Проверьте статус адаптера
kubectl get pods -n monitoring | grep prometheus-adapter

# Подождите несколько секунд и проверьте доступность метрик
# Проверка доступности API метрик
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | grep http_requests

# Проверка конкретной метрики для namespace
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/default/http_requests_per_second"

# Если метрики не доступны, проверьте логи адаптера
kubectl logs -n monitoring -l app=prometheus-adapter --tail=50
```

### Шаг 5: Настройка HPA для масштабирования по RPS

**Важно:** Сначала удалите старый HPA для памяти, чтобы избежать конфликтов:

```bash
# Удалите HPA для памяти
kubectl delete -f hpa-memory.yaml

# Примените новый HPA для RPS
kubectl apply -f hpa-rps.yaml

# Проверьте создание HPA
kubectl get hpa scaletestapp-hpa-rps

# Посмотрите детальную информацию
kubectl describe hpa scaletestapp-hpa-rps
```

### Шаг 6: Тестирование масштабирования по RPS

#### 6.1: Запуск нагрузочного теста

Используйте тот же Locust, что и в Части 1:

```bash
# Запустите Locust (используйте URL сервиса из Части 1)
locust
```

#### 6.2: Настройка теста

1. Откройте `http://localhost:8089`
2. Установите большее количество пользователей (например, 100)
3. Установите высокий spawn rate (например, 10)
4. Запустите тест

#### 6.3: Мониторинг масштабирования

```bash
# Отслеживайте HPA в реальном времени
# Для Linux/Mac:
watch kubectl get hpa scaletestapp-hpa-rps

# Для Windows PowerShell:
while ($true) { kubectl get hpa scaletestapp-hpa-rps; Start-Sleep -Seconds 2; Clear-Host }

# Отслеживайте количество подов
# Для Linux/Mac:
watch kubectl get pods -l app=scaletestapp

# Для Windows PowerShell:
while ($true) { kubectl get pods -l app=scaletestapp; Start-Sleep -Seconds 2; Clear-Host }

# Проверьте метрики в Prometheus
# В Prometheus UI выполните запрос: rate(http_requests_total[2m])
```

#### 6.4: Анализ результатов

После запуска нагрузки вы должны увидеть:
- Увеличение количества реплик при росте RPS
- HPA будет масштабировать на основе метрики `http_requests_per_second`
- В Prometheus можно увидеть графики RPS

## Полезные команды для отладки

### Проверка метрик

```bash
# Проверка метрик ресурсов (CPU/Memory)
kubectl top pods
kubectl top nodes

# Проверка кастомных метрик
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1/namespaces/default/pods/*/http_requests_per_second"

# Проверка событий HPA
kubectl describe hpa scaletestapp-hpa-rps
```

### Просмотр логов

```bash
# Логи приложения
kubectl logs -l app=scaletestapp --tail=50

# Логи Prometheus
kubectl logs -n monitoring -l app=prometheus --tail=50

# Логи Prometheus Adapter
kubectl logs -n monitoring -l app=prometheus-adapter --tail=50
```

### Очистка ресурсов

```bash
# Удаление всех ресурсов приложения
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
kubectl delete -f hpa-memory.yaml
kubectl delete -f hpa-rps.yaml

# Удаление Prometheus и связанных ресурсов
kubectl delete -f prometheus-adapter-api-service.yaml
kubectl delete -f prometheus-adapter-service.yaml
kubectl delete -f prometheus-adapter-deployment.yaml
kubectl delete -f prometheus-adapter-rbac.yaml
kubectl delete -f prometheus-adapter-config.yaml
kubectl delete -f prometheus-service.yaml
kubectl delete -f prometheus-deployment.yaml
kubectl delete -f prometheus-configmap.yaml
kubectl delete -f prometheus-rbac.yaml
kubectl delete -f prometheus-namespace.yaml

# Остановка Minikube
minikube stop
```

## Возможные проблемы и решения

### Проблема: metrics-server не собирает метрики

**Решение:**
```bash
# Проверьте статус metrics-server
kubectl get pods -n kube-system | grep metrics-server

# Перезапустите metrics-server
kubectl delete pod -n kube-system -l k8s-app=metrics-server
```

### Проблема: HPA показывает "unknown" в метриках

**Решение:**
```bash
# Убедитесь, что metrics-server работает
kubectl top nodes

# Подождите несколько минут для сбора метрик
# Проверьте события HPA
kubectl describe hpa <hpa-name>
```

### Проблема: Prometheus не видит метрики приложения

**Решение:**
```bash
# Проверьте, что приложение экспортирует метрики
kubectl port-forward svc/scaletestapp-service 8080:80
curl http://localhost:8080/metrics

# Проверьте конфигурацию Prometheus
kubectl get configmap prometheus-config -n monitoring -o yaml

# Проверьте логи Prometheus
kubectl logs -n monitoring -l app=prometheus
```

### Проблема: Prometheus Adapter не предоставляет метрики

**Решение:**
```bash
# Проверьте логи адаптера
kubectl logs -n monitoring -l app=prometheus-adapter

# Проверьте конфигурацию адаптера
kubectl get configmap adapter-config -n monitoring -o yaml

# Убедитесь, что Prometheus доступен из адаптера
kubectl exec -n monitoring -it deployment/prometheus-adapter -- wget -O- http://prometheus.monitoring.svc:9090/api/v1/query?query=up
```

## Дополнительные настройки

### Изменение параметров масштабирования

Вы можете изменить параметры HPA, отредактировав соответствующие файлы:
- `hpa-memory.yaml` - для масштабирования по памяти
- `hpa-rps.yaml` - для масштабирования по RPS

Основные параметры:
- `minReplicas` - минимальное количество реплик
- `maxReplicas` - максимальное количество реплик
- `averageUtilization` - целевой уровень утилизации (для памяти)
- `averageValue` - целевое значение метрики (для RPS)

### Настройка поведения масштабирования

В секции `behavior` можно настроить:
- `scaleDown.stabilizationWindowSeconds` - окно стабилизации при уменьшении
- `scaleUp.stabilizationWindowSeconds` - окно стабилизации при увеличении
- `policies` - политики масштабирования (процент или количество подов)

