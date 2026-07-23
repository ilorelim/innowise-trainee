# Модуль 13: ConfigMaps, Secrets и stateful Postgres в Minikube

**Цель:** научиться развёртывать stateful-приложение (БД) и передавать конфигурацию через ConfigMap и пароли через Secret; связать `my-app` с Postgres по DNS внутри кластера.

**Критерии выполнения:**
- Secret `postgres-secret` с `POSTGRES_PASSWORD` создан и применён;
- ConfigMap `postgres-configmap` с `POSTGRES_DB` / `POSTGRES_USER` создан и применён;
- PVC `postgres-pvc` (1Gi, ReadWriteOnce) создан; том привязан (в Minikube — обычно сразу Bound);
- Deployment Postgres (`postgres:14-alpine`) получает env из ConfigMap + Secret и пишет данные в PVC;
- Service `postgres-db` (ClusterIP) даёт DNS-имя внутри кластера;
- ConfigMap для `my-app` содержит `DATABASE_URL`; Deployment `my-app` перезапущен и видит переменную.

---

## 1. Теория: ConfigMap vs Secret

| | ConfigMap | Secret |
|---|---|---|
| Назначение | несекретные настройки | пароли, ключи API, токены |
| Хранение в API | plain text в `data` | base64 в `data` (или `stringData` — K8s закодирует сам) |
| Пример в модуле | `POSTGRES_DB`, `POSTGRES_USER`, `DATABASE_URL` | `POSTGRES_PASSWORD` |

Оба объекта инжектятся в Pod одинаково: через `env` / `envFrom` или как файлы в volume. Разница — в назначении и в том, как к ним относятся политики безопасности (RBAC, etcd encryption и т.д.).

Важно: Secret в Kubernetes — это **не шифрование «из коробки»** для всех кластеров, а отдельный тип ресурса и соглашение «сюда кладём секреты». В учебном задании пароль в `DATABASE_URL` всё равно попал в ConfigMap (так требует формулировка) — в production так делать не стоит.

---

## 2. Теория: PV и PVC

**PersistentVolume (PV)** — «диск» в кластере (hostPath, NFS, cloud disk и т.п.).

**PersistentVolumeClaim (PVC)** — «заявка»: «хочу 1Gi в режиме ReadWriteOnce».

Связка:
1. создаётся PVC;
2. либо находится готовый PV (static), либо StorageClass создаёт PV (dynamic provisioning);
3. статус PVC становится **Bound**;
4. Pod монтирует PVC через `volumes` + `volumeMounts`.

В задании указано ожидание `Pending`, «потому что Minikube создаст PV автоматически». На практике в Minikube default StorageClass (`standard` / hostpath) почти сразу биндит том → статус чаще **Bound**. Это нормально и как раз значит, что provisioner сработал.

`ReadWriteOnce` — том может быть смонтирован на запись одной нодой. Для одной реплики Postgres этого достаточно; `replicas: 3` с одним таким PVC — плохая идея.

---

## 3. Secret — `postgres-secret.yml`

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
stringData:
  POSTGRES_PASSWORD: "mysecret"
```

`stringData` удобнее `data`: пишем пароль как есть, Kubernetes сам кладёт base64 в `data`.

```bash
kubectl apply -f postgres-secret.yml
kubectl get secret postgres-secret
```

---

## 4. ConfigMap Postgres — `postgres-configmap.yml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-configmap
data:
  POSTGRES_DB: "devopsdb"
  POSTGRES_USER: "devops"
```

Ключи совпадают с переменными официального образа Postgres: при первом старте создаются пользователь и БД.

```bash
kubectl apply -f postgres-configmap.yml
```

---

## 5. PVC — `postgres-pvc.yml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

`storageClassName` не указан → берётся default StorageClass Minikube → PV создаётся автоматически.

```bash
kubectl apply -f postgres-pvc.yml
kubectl get pvc postgres-pvc
kubectl get pv
```

---

## 6. Deployment Postgres — `postgres-deployment.yml`

Ключевые решения:
- образ `postgres:14-alpine`;
- `replicas: 1` (одна БД + один RWO PVC);
- labels `app: postgres-app` — и для selector Deployment, и для Service;
- `envFrom` подтягивает все ключи из ConfigMap и Secret как переменные окружения;
- volume `pg-data` → mountPath `/var/lib/postgresql/data`.

Фрагменты инъекции и тома:

```yaml
envFrom:
  - configMapRef:
      name: postgres-configmap
  - secretRef:
      name: postgres-secret
volumeMounts:
  - name: pg-data
    mountPath: /var/lib/postgresql/data
# ...
volumes:
  - name: pg-data
    persistentVolumeClaim:
      claimName: postgres-pvc
```

После apply Postgres «видит» `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Данные кластера переживают пересоздание Pod’а, пока жив PVC.

```bash
kubectl apply -f postgres-deployment.yml
kubectl get pods -l app=postgres-app
kubectl exec -it <postgres-pod> -- env | grep POSTGRES_
```

---

## 7. Service Postgres — `postgres-service.yml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-db
spec:
  type: ClusterIP
  selector:
    app: postgres-app
  ports:
    - port: 5432
      targetPort: 5432
```

`ClusterIP` — доступ только внутри кластера (для БД так и нужно). Имя Service = DNS-имя: другие Pod’ы ходят на `postgres-db:5432` (в том же namespace).

`selector` должен совпадать с labels Pod’ов (`app: postgres-app`), иначе Endpoints пустые.

```bash
kubectl apply -f postgres-service.yml
kubectl get svc postgres-db
kubectl get endpoints postgres-db
```

---

## 8. Обновление my-app — ConfigMap + Deployment

### ConfigMap для my-app — `my-app-configmap.yml`

Отдельный ConfigMap **для приложения**, не для Postgres:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-app-configmap
data:
  DATABASE_URL: "postgresql://devops:mysecret@postgres-db:5432/devopsdb"
```

Разбор URL:
- пользователь / пароль / БД — те же, что в Secret и ConfigMap Postgres;
- хост `postgres-db` — DNS-имя Service.

### Deployment my-app — `app-deploymemt.yml`

В контейнер добавлен `envFrom`:

```yaml
envFrom:
  - configMapRef:
      name: my-app-configmap
```

Применение и перезапуск (чтобы Pod’ы точно подхватили env):

```bash
kubectl apply -f my-app-configmap.yml
kubectl apply -f app-deploymemt.yml
kubectl rollout restart deployment/my-app-deployment
kubectl exec -it <my-app-pod> -- env | grep DATABASE_URL
```

Критерий модуля: `my-app` получает строку подключения к `postgres-db` через K8s DNS. Код FastAPI из М8 сам БД не открывает — для задания важна **инфраструктурная связка** (ConfigMap → env → DNS-имя backend).

---

## 9. Карта ресурсов модуля

```text
postgres-configmap ──┐
                     ├── envFrom ──► Deployment postgres-app ──► Pod (postgres:14-alpine)
postgres-secret ─────┘                      │
                                            ├── volumeMount /var/lib/postgresql/data
postgres-pvc ───────────────────────────────┘
                                            │
                              labels app=postgres-app
                                            │
postgres-db (ClusterIP :5432) ◄─────────────┘
         │
         │  DNS: postgres-db
         ▼
my-app-configmap (DATABASE_URL) ── envFrom ──► Deployment my-app-deployment
```

Порядок apply (логично):
1. Secret, ConfigMap’ы, PVC;
2. Deployment Postgres;
3. Service `postgres-db`;
4. ConfigMap + Deployment `my-app` / rollout restart.

---

## 10. Чеклист задания

| Задача | Статус |
|--------|--------|
| Теория ConfigMap vs Secret | выполнено |
| `postgres-secret.yml` (`stringData`) | выполнено |
| `postgres-configmap.yml` | выполнено |
| Теория PV / PVC | выполнено |
| `postgres-pvc.yml` (1Gi, RWO) | выполнено |
| Deployment Postgres + `envFrom` | выполнено |
| Монтирование PVC в `/var/lib/postgresql/data` | выполнено |
| Service `postgres-db` (ClusterIP) | выполнено |
| ConfigMap `my-app` с `DATABASE_URL` + перезапуск | выполнено |

---

## 11. Выводы

1. **ConfigMap** — несекретный конфиг; **Secret** — чувствительные данные (`stringData` удобнее ручного base64).
2. **PVC** заказывает том; в Minikube default StorageClass сразу даёт **Bound** PV — данные Postgres переживают рестарт Pod’а.
3. **`envFrom`** прокидывает ключи ConfigMap/Secret как переменные окружения (образ Postgres их ожидает).
4. **ClusterIP Service** создаёт стабильное DNS-имя (`postgres-db`) для доступа к эфемерным Pod’ам БД изнутри кластера.
5. Frontend/backend в терминах модуля связываются через **отдельный ConfigMap `my-app`** с `DATABASE_URL`, а не через правку Postgres-конфига.
`)