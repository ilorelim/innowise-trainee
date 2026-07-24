# Модуль 15: Observability — Metrics и Logs

**Цель:** научиться «видеть», что происходит внутри K8s-кластера: Metrics (Prometheus/Grafana) и базовое логирование (`kubectl logs`).

**Критерии выполнения:**
- понятна разница Metrics / Logs / Traces;
- `kube-prometheus-stack` установлен в `monitoring` (Prometheus + Grafana Running);
- UI Prometheus и Grafana доступны через `port-forward`;
- в Grafana видны дашборды ресурсов кластера;
- у `my-app` есть `/metrics`, образ пересобран и задеплоен;
- создан `ServiceMonitor`; в Prometheus → Targets цель `my-app` в статусе **up**;
- логи Deployment/Pod смотрятся через `kubectl logs` / `kubectl logs -f`.

---

## 1. Теория: Observability (3 столпа)

| Столп | Что это | Пример | Инструменты |
|---|---|---|---|
| **Metrics** | числа во времени | CPU 80%, RPS | Prometheus, Grafana |
| **Logs** | текстовые события | `"GET /metrics 200"` | `kubectl logs`, Loki/ELK |
| **Traces** | путь одного запроса | API → DB → cache | Jaeger, Zipkin |

Metrics отвечают «сколько/как часто», Logs — «что случилось», Traces — «где застрял запрос».

---

## 2. Helm: kube-prometheus-stack

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

Release: `prometheus`, namespace: `monitoring`.

На слабом Minikube (2 CPU / ~4Gi) стек может «душить» ноду (пробы timeout, CrashLoop). Для учебного стенда стек облегчали: отключили Alertmanager и часть kube-component scrape, уменьшили retention.

Имена сервисов у chart’а (не как в формулировке задания):

| Назначение | Service |
|---|---|
| Prometheus UI | `prometheus-kube-prometheus-prometheus:9090` |
| Grafana | `prometheus-grafana:80` |

---

## 3. Доступ к UI

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

- Prometheus: http://localhost:9090  
- Grafana: http://localhost:3000  

Пароль Grafana:

```bash
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d; echo
# user: admin
```

Ошибка RSS на Home (`Error loading RSS feed`) — виджет News, к мониторингу кластера не относится. Нужные графики: **Dashboards → Kubernetes / Compute Resources / Cluster**.

---

## 4. Теория: ServiceMonitor

Prometheus Operator смотрит объекты `kind: ServiceMonitor` и генерирует scrape-конфиг.

Цепочка:

```text
ServiceMonitor → Operator → Prometheus scrape → Pod:/metrics
```

У `kube-prometheus-stack` selector требует label **`release: prometheus`** на ServiceMonitor — без него цель не появится.

`spec.selector` матчит **labels Service** (не Pod). Порт в `endpoints` — **имя** порта в Service (`http`).

---

## 5. App-side: `/metrics` в my-app

Источник: `module8-docker-ci/app` (образ `my-app:kuber`).

- зависимость `prometheus-client` в `requirements.txt`;
- эндпоинт `GET /metrics` отдаёт текст в формате Prometheus.

Сборка и деплой:

```bash
eval $(minikube docker-env)
cd module8-docker-ci/app
docker build -t my-app:kuber .
kubectl rollout restart deployment/my-app-deployment
kubectl rollout status deployment/my-app-deployment

POD=$(kubectl get pod -l app=my-app -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward pod/$POD 5000:5000
curl localhost:5000/metrics
```

---

## 6. YAML: Service + ServiceMonitor

`module15-prometheus/app-service.yml` — label `app: my-app`, порт `name: http`.

`module15-prometheus/app-monitor.yml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app-monitor
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: http
      path: /metrics
```

```bash
kubectl apply -f module15-prometheus/app-service.yml
kubectl apply -f module15-prometheus/app-monitor.yml
```

Проверка: Prometheus → **Status → Targets** — через ~1–2 минуты `my-app-service` / `...:5000/metrics` в статусе **up**.

---

## 7. Логи

```bash
kubectl logs deployment/my-app-deployment
kubectl logs -f deployment/my-app-deployment          # streaming
kubectl logs pod/my-app-deployment-xxxxx --tail=50
```

В логах видны scrape Prometheus (`GET /metrics 200`) и обычные запросы к приложению.

---

## 8. Итог по критериям

| Критерий | Статус |
|---|---|
| 3 столпа Observability | ✅ |
| Prometheus + Grafana в `monitoring` | ✅ |
| UI через port-forward | ✅ |
| Дашборды Compute Resources | ✅ (после стабилизации ресурсов) |
| `/metrics` у my-app | ✅ |
| ServiceMonitor + Target **up** | ✅ |
| `kubectl logs` / `-f` | ✅ |

---

## 9. Файлы модуля

```text
module15-prometheus/
├── app-service.yml    # Service: label app=my-app, port name=http
├── app-monitor.yml    # ServiceMonitor для Prometheus Operator
└── module15.md        # этот отчёт

# изменения приложения (образ my-app:kuber):
module8-docker-ci/app/app.py
module8-docker-ci/app/requirements.txt
```
