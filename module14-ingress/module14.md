# Модуль 14: Ingress и Helm

**Цель:** перестать опираться на NodePort для «человеческих» URL; настроить Ingress (L7-маршрутизацию) и освоить Helm как пакетный менеджер Kubernetes.

**Критерии выполнения:**
- Nginx Ingress Controller в Minikube запущен (`minikube addons enable ingress`);
- создан `app-ingress.yml` (`kind: Ingress`, `apiVersion: networking.k8s.io/v1`);
- правило `path: /app` → `my-app-service:80` применено;
- `http://my-app.local/app` отдаёт ответ приложения;
- Helm установлен, репозиторий Bitnami добавлен;
- Postgres из М13 удалён, установлен `helm install my-pg bitnami/postgresql`;
- `helm list` показывает `my-pg`, под Postgres в статусе Running.

---

## 1. Теория: NodePort vs LoadBalancer vs Ingress

| | NodePort | LoadBalancer | Ingress |
|---|---|---|---|
| Уровень | L4 (TCP/UDP) | L4 | L7 (HTTP/HTTPS) |
| Как открывает доступ | порт на **каждой** ноде (например `:30936`) | внешний IP от облака | один вход + маршруты по host/path |
| Минус | неудобные URL, порты 30000–32767 | дорого / не всегда есть вне облака | нужен Ingress Controller |
| Плюс | просто локально | «настоящий» внешний IP | красивые URL: `app.com/api` → Service |

**NodePort** — Service сам пробрасывает порт на ноды. Для демо ок, для «красивых» URL — нет.

**LoadBalancer** — Service типа LoadBalancer просит у облака (AWS/GCP/Azure) внешний IP. В Minikube эмулируется, в проде это платный ресурс на каждый сервис.

**Ingress** — один балансировщик на много сервисов. Правила: `host` + `path` → backend Service. Пример: `app.com/api` → `api-service:80`, `app.com/` → `frontend:80`.

Цепочка трафика:

```text
Браузер → Ingress Controller (nginx) → Service → Pod
         (host + path)              (selector)
```

---

## 2. Включение Ingress Controller в Minikube

```bash
minikube addons enable ingress
```

Появится namespace `ingress-nginx` и под контроллера:

```bash
kubectl get pods -n ingress-nginx
```

**Результат:** `ingress-nginx-controller-...` в статусе `Running`, addon `ingress` — `enabled`.

---

## 3. Service для приложения

Файл `app-service.yml` — backend для Ingress (имя и порт должны совпасть с правилом):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: NodePort          # для Ingress достаточно и ClusterIP
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 5000
```

Ingress ходит на `port: 80` Service; Service пересылает на `targetPort: 5000` в контейнере.

```bash
kubectl apply -f app-service.yml
```

---

## 4. YAML Ingress — `app-ingress.yml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-app
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: my-app.local
      http:
        paths:
          - path: /app
            pathType: Prefix
            backend:
              service:
                name: my-app-service
                port:
                  number: 80
```

Ключевые поля:
- `ingressClassName: nginx` — какой контроллер обрабатывает ресурс;
- `host: my-app.local` — совпадение с HTTP-заголовком `Host`;
- `path: /app`, `pathType: Prefix` — все URL, начинающиеся с `/app`;
- `backend.service` — куда слать трафик.

**Зачем `rewrite-target: /`:** приложение слушает `/`, а снаружи путь `/app`. Без rewrite в под уходит `/app` → JSON `{"detail":"Not Found"}`. Annotation переписывает путь на `/` перед backend.

```bash
kubectl apply -f app-ingress.yml
kubectl get ingress
```

**Результат:** `ingress-app`, CLASS `nginx`, HOSTS `my-app.local`, ADDRESS = IP Minikube.

---

## 5. Тест Ingress и DNS (host-based)

Узнать IP:

```bash
minikube ip
# 192.168.59.100
```

Добавить в `/etc/hosts` (Linux/macOS) или `C:\Windows\System32\drivers\etc\hosts` (Windows):

```text
192.168.59.100 my-app.local
```

Проверка:

```bash
curl http://my-app.local/app
# {"message":"Hello, World!"}
```

В браузере: `http://my-app.local/app`.

### Важно про `curl $(minikube ip)/app`

Команда из формулировки задания **без** заголовка Host не матчит правило `host: my-app.local`:

```bash
curl $(minikube ip)/app
# Host: 192.168.59.100  →  HTML 404 от nginx
```

Рабочий эквивалент по IP:

```bash
curl -H 'Host: my-app.local' http://$(minikube ip)/app
# {"message":"Hello, World!"}
```

После записи в `/etc/hosts` достаточно `curl http://my-app.local/app`.

---

## 6. Теория: что такое Helm

**Helm** — пакетный менеджер для Kubernetes (аналог Apt/Pip/npm).

- **Chart** — пакет: шаблоны Deployment, Service, PVC, Secret и т.д.;
- **Release** — установленный экземпляр chart’а с именем (`my-pg`);
- **Repo** — каталог chart’ов (Bitnami и др.).

Вместо 5–7 YAML для Postgres — одна команда `helm install`. Обновление: `helm upgrade`, удаление: `helm uninstall`.

---

## 7. Установка Helm и репозиторий Bitnami

Helm установлен (проверка: `helm version`).

Официальный URL из задания сейчас часто отдаёт **403**:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
# failed to fetch .../index.yaml : 403 Forbidden
```

Bitnami перевёл charts на OCI; для учебного `helm install bitnami/...` используем зеркало индекса:

```bash
helm repo add bitnami https://raw.githubusercontent.com/bitnami/charts/archive-full-index/bitnami
helm repo update
```

Альтернатива без repo — OCI напрямую:

```bash
helm install my-pg oci://registry-1.docker.io/bitnamicharts/postgresql
```

---

## 8. Helm Install: Postgres вместо манифестов М13

Удаление ручного Postgres:

```bash
kubectl delete deploy postgres-app
kubectl delete svc postgres-db
kubectl delete cm postgres-config
kubectl delete secret postgres-secret
kubectl delete pvc postgres-pvc
```

Установка через Helm:

```bash
helm install my-pg bitnami/postgresql --set auth.postgresPassword=postgres
```

Проверка:

```bash
helm list
# my-pg    deployed    postgresql-...

kubectl get pods
# my-pg-postgresql-0   1/1   Running
```

Helm создал StatefulSet, Service `my-pg-postgresql`, Secret, PVC. DNS внутри кластера: `my-pg-postgresql:5432` (больше не `postgres-db`).

---

## 9. Итог по критериям

| Критерий | Статус |
|---|---|
| Nginx Ingress Controller Running | ✅ `ingress-nginx-controller` |
| `app-ingress.yml` создан и применён | ✅ `ingress-app` |
| Правило `/app` → `my-app-service:80` | ✅ |
| `http://my-app.local/app` отвечает | ✅ `{"message":"Hello, World!"}` |
| Helm установлен, repo Bitnami доступен | ✅ (через archive-full-index) |
| `helm list` содержит `my-pg` | ✅ `deployed` |
| Postgres Running | ✅ `my-pg-postgresql-0` |

---

## 10. Файлы модуля

```text
module14-ingress/
├── app-ingress.yml    # Ingress: my-app.local/app → my-app-service
├── app-service.yml    # Service backend для Ingress
└── module14.md        # этот отчёт
```

**Команды «на память»:**

```bash
minikube addons enable ingress
kubectl apply -f app-ingress.yml
echo "$(minikube ip) my-app.local" | sudo tee -a /etc/hosts
curl http://my-app.local/app

helm repo add bitnami https://raw.githubusercontent.com/bitnami/charts/archive-full-index/bitnami
helm install my-pg bitnami/postgresql --set auth.postgresPassword=postgres
helm list
```
