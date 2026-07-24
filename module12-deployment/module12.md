# Модуль 12: Deployment и Service в Minikube

**Цель:** научиться декларативно (через YAML) развёртывать stateless-приложение `my-app` (из М8) в локальном Kubernetes (Minikube).

**Критерии выполнения:**
- образ собран так, что Minikube его видит;
- Deployment с 3 репликами создан и применён;
- `kubectl get pods -l app=my-app` показывает 3 Running Pod’а;
- при удалении Pod’а Deployment поднимает новый (self-healing);
- Service типа NodePort открывает приложение через `minikube service`.

---

## 1. Теория: декларативность

**Императивно** (как руками в Docker): «запусти контейнер, потом ещё, потом ещё».

**Декларативно** (как в Kubernetes): «я хочу 3 реплики приложения» — контроллер сам приводит реальность к желаемому состоянию.

Deployment как раз и есть такое желаемое состояние: `replicas: 3`. Не нужно три раза вызывать `kubectl run` — один YAML описывает итог.

Связь с предыдущими модулями:
- Ansible (М9) — тоже декларативность и идемпотентность на серверах;
- Compose (М5–М6) — описание стека, но без полноценного self-healing и оркестрации как в K8s;
- Minikube (М11) — локальный однонодовый Kubernetes для практики.

---

## 2. Контекст: Minikube и образы

Minikube поднимает Kubernetes в отдельной VM (у нас — VirtualBox). У ноды свой runtime / свой набор образов. Образ, собранный только на хосте, кластер сам по себе не видит.

Способы «показать» образ Minikube:

| Способ | Суть |
|--------|------|
| `eval $(minikube docker-env)` + `docker build` | сборка сразу во внутренний Docker Minikube (как в задании) |
| `docker build` на хосте + `minikube image load` | копирование готового образа с хоста в Minikube |
| Registry (Docker Hub и т.п.) | push / pull по сети |

`eval $(minikube docker-env)` выполняет (`eval`) вывод `minikube docker-env` — набор `export DOCKER_HOST=...` и сертификатов, чтобы CLI `docker` ходил в Docker VM, а не на хост.

---

## 3. Сборка образа

Приложение: FastAPI из `module8-docker-ci/app`, порт **5000**.

В процессе работы образ был собран и доставлен в Minikube под тегом **`my-app:kuber`** (вместо `:k8s` из формулировки задания — важно, чтобы тег в YAML совпадал с реальным образом).

Типичные команды:

```bash
# вариант из задания
eval $(minikube docker-env)
cd module8-docker-ci/app
docker build -t my-app:kuber .

# запасной вариант, когда образ уже на хосте
minikube image load my-app:kuber
minikube image ls | grep my-app
```

В Deployment использовался `imagePullPolicy: IfNotPresent` (и при отладке — `Never`), чтобы kubelet не ходил в Docker Hub за несуществующим `my-app:kuber`.

---

## 4. Deployment — итоговый YAML

Файл: `module12-deployment/app-deployment.yml`

Состояние сущности Deployment (зафиксировано в ходе модуля):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: my-app:kuber
          imagePullPolicy: IfNotPresent
```

Что означает каждый блок:

| Поле | Назначение |
|------|------------|
| `kind: Deployment` | контроллер, поддерживающий нужное число Pod’ов |
| `replicas: 3` | желаемое состояние: всегда 3 копии |
| `selector.matchLabels` | по каким label’ам Deployment «владеет» Pod’ами |
| `template` | шаблон Pod’а, который тиражируется |
| `labels: app: my-app` | метка для selector Deployment и для Service |
| `image: my-app:kuber` | локальный образ приложения |
| `imagePullPolicy: IfNotPresent` | сначала локальный образ, не сразу pull из registry |

Обязательное правило: `selector.matchLabels` должен совпадать с `template.metadata.labels`.

Применение:

```bash
kubectl apply -f app-deployment.yml
kubectl get pods -l app=my-app
```

---

## 5. Проблема ImagePullBackOff и решение

Симптом:

```text
ErrImagePull / ImagePullBackOff
minikube service → SVC_UNREACHABLE: no running pod for service
```

Причина: Pod’ы не Running, потому что нода не находила образ `my-app:kuber` (сборка ушла не в тот Docker / тег не совпал / образ не был в VM). Service при этом был создан, но выбирать было некого.

Что помогло:
1. убедиться, что образ есть в Minikube (`minikube image ls` / load);
2. согласовать имя образа в YAML и в `docker` / `image ls`;
3. пересоздать Pod’ы (`kubectl delete pods -l app=my-app` или `rollout restart`).

Итог: три Pod’а в статусе Running.

---

## 6. Self-healing

Проверка желаемого состояния:

```bash
kubectl get pods -l app=my-app
kubectl delete pod <имя-одного-пода>
kubectl get pods -l app=my-app -w
```

Deployment замечает, что реплик стало 2 вместо 3, и сразу создаёт новый Pod. Это и есть self-healing: не «перезапусти вручную», а «поддерживай replicas: 3».

---

## 7. Service — итоговый YAML

Файл: `module12-deployment/app-service.yml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 5000
```

| Поле | Назначение |
|------|------------|
| `apiVersion: v1` | Service живёт в core API (не `apps/v1`) |
| `selector: app: my-app` | те же label’ы, что у Pod’ов |
| `port: 80` | порт сервиса внутри кластера |
| `targetPort: 5000` | порт контейнера (uvicorn / FastAPI) |
| `type: NodePort` | доступ снаружи через ноду Minikube |

Применение и проверка:

```bash
kubectl apply -f app-service.yml
minikube service my-app-service
```

В браузере открывается приложение (ответ вида `{"message":"Hello, World!"}`).

---

## 8. Что сделано по чеклисту задания

| Задача | Статус |
|--------|--------|
| Понять декларативность («хочу 3 реплики») | выполнено |
| Образ доступен Minikube (`docker-env` / `image load`) | выполнено |
| `app-deployment.yml` с `replicas: 3`, labels, образом | выполнено |
| `kubectl apply` → 3 Running Pod’а | выполнено |
| Удаление Pod’а → появление нового | выполнено |
| `app-service.yml` (NodePort, 80→5000) | выполнено |
| `minikube service` → приложение в браузере | выполнено |

---

## 9. Выводы

1. **Deployment** описывает желаемое состояние (число реплик + шаблон Pod’а), а не пошаговый запуск контейнеров.
2. **Labels + selector** связывают Deployment, Pod’ы и Service в одну логическую группу (`app: my-app`).
3. **Локальный образ** в Minikube нужно явно доставить (`docker-env` или `image load`); иначе будет `ImagePullBackOff`, и Service окажется «пустым».
4. **Self-healing** — следствие контроллера: пропал Pod → снова `replicas: 3`.
5. **Service (NodePort)** даёт стабильную точку входа к набору эфемерных Pod’ов и публикует приложение наружу через Minikube.
