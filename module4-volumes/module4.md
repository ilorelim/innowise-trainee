# Модуль 4. Volumes и Networking

**Цель модуля:** научиться сохранять данные (Volumes) и связывать контейнеры (Networking), чтобы App мог «увидеть» DB.

## Структура папок

```
module4-volumes/
  module4.md          ← отчёт по выполненным заданиям
  task1/              ← FastAPI + uvicorn --reload (Bind Mount / hot-reload)
```

---

# 1. Теория: почему данные пропадают?

Файловая система контейнера **эфемерна**. Всё, что создано внутри writable-слоя контейнера, живёт только пока существует этот контейнер. `docker rm` удаляет контейнер вместе с его данными.

## Задание: убедиться на практике

```bash
docker run -it --name ephemeral-demo ubuntu bash
# внутри контейнера:
mkdir -p /data
touch /data/test.txt
ls /data
exit

docker rm ephemeral-demo

docker run -it --name ephemeral-demo ubuntu bash
# внутри:
ls /data
# файла /data/test.txt нет — каталог даже может отсутствовать
exit
docker rm ephemeral-demo
```

### Вывод

Новый контейнер из того же образа стартует «с чистого листа». Данные не переживают `docker rm`, пока их явно не вынесли наружу (Volume / Bind Mount).

---

# 2. Теория: Bind Mount vs Volume

| | Bind Mount | Named Volume |
|---|---|---|
| Флаг | `-v /host/path:/container/path` | `-v volume-name:/container/path` |
| Где живут данные | Конкретная папка на хосте | Управляется Docker (`/var/lib/docker/volumes/...`) |
| Типичный кейс | Разработка, hot-reload | Production-данные (БД) |
| Контроль пути | Вы задаёте путь сами | Docker сам выбирает расположение |

## Схема

```
                    ┌─────────────────────┐
  Host path         │  Container FS       │
  /home/me/app ────►│  /app               │  Bind Mount
                    │  (та же папка)      │
                    └─────────────────────┘

                    ┌─────────────────────┐
  Docker volume     │  Container FS       │
  postgres-data ───►│  /var/lib/postgresql│  Named Volume
  (управляет Docker)│  /data              │
                    └─────────────────────┘
```

- **Bind Mount** — «горячая» проброска: правки на хосте сразу видны в контейнере.
- **Volume** — изолированное хранилище Docker, удобно для персистентности БД и переноса между машинами через backup/restore volume.

---

# 3. Bind Mount: hot-reload

Приложение: `task1/` (FastAPI + uvicorn с флагом `--reload`).

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]
```

Сборка и запуск с Bind Mount:

```bash
cd task1
docker build -t my-app:1.0 .

docker run --rm -p 5000:5000 -v "$(pwd)":/app my-app:1.0
```

Проверка:

1. Открыть `http://localhost:5000/` — ответ `{"message": "..."}`.
2. Изменить строку в `app.py` на хосте.
3. Обновить страницу — uvicorn подхватил изменения **без пересборки образа**.

### Вывод

`-v $(pwd):/app` подменяет `/app` в контейнере кодом с хоста. Вместе с `--reload` это даёт hot-reload для разработки.

---

# 4. Named Volume: создать volume

```bash
docker volume create postgres-data
docker volume ls
```

В списке появляется `postgres-data`.

---

# 5. Volume: PostgreSQL с именованным volume

```bash
docker run -d \
  --name pg-demo \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=mysecret \
  postgres
```

Проверка:

```bash
docker ps
# контейнер postgres в статусе Up, порт 5432 проброшен
```

Данные кластера Postgres пишутся в volume `postgres-data`, а не только в эфемерный слой контейнера.

---

# 6. Проверка персистентности Volume

```bash
docker stop pg-demo
docker rm pg-demo

# та же команда запуска снова:
docker run -d \
  --name pg-demo \
  -p 5432:5432 \
  -v postgres-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=mysecret \
  postgres
```

### Вывод

Postgres стартует быстро и **не инициализирует БД заново** (нет долгого «database system is ready» с полной инициализацией с нуля, как в первый раз). Данные остались в `postgres-data` — они пережили `docker rm` контейнера.

Очистка после эксперимента (по желанию):

```bash
docker stop pg-demo && docker rm pg-demo
# volume пока оставляем — пригодится для сетевых задач, либо:
# docker volume rm postgres-data
```

---

# 7. Теория сети: bridge по умолчанию

Контейнеры в default bridge могут общаться по IP, но IP **меняются** при пересоздании. DNS-имён контейнеров в default bridge обычно нет (кроме `--link`, устаревший способ).

## Задание: ping по IP

```bash
docker run -d --name u1 ubuntu sleep 1000
docker run -d --name u2 ubuntu sleep 1000

docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' u1
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' u2
# например: 172.17.0.2 и 172.17.0.3

docker exec -it u1 bash
# внутри (если нет ping — apt-get update && apt-get install -y iputils-ping):
ping <IP_u2>
# пинг проходит
exit

docker rm -f u1 u2
```

### Вывод

На default bridge связь по IP работает, но опираться на IP в конфиге приложения нельзя — они нестабильны.

---

# 8. Своя bridge-сеть

```bash
docker network create my-app-net
docker network ls
```

Сеть `my-app-net` создана (driver `bridge`).

---

# 9. Postgres в кастомной сети

```bash
docker run -d \
  --name pg-db \
  --network my-app-net \
  -v postgres-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=mysecret \
  postgres
```

Проверка:

```bash
docker inspect -f '{{json .NetworkSettings.Networks}}' pg-db
# есть ключ my-app-net
```

---

# 10. DNS-Discovery: ping по имени контейнера

```bash
docker run -it --rm --network my-app-net ubuntu bash
```

Внутри:

```bash
apt-get update && apt-get install -y iputils-ping dnsutils
ping pg-db
# пинг по имени проходит
nslookup pg-db
# Docker DNS резолвит pg-db в IP контейнера
```

### Вывод

В **кастомной** bridge-сети Docker поднимает встроенный DNS: контейнеры находят друг друга по `--name` (например `pg-db`). Приложение может подключаться к БД как `postgres://...@pg-db:5432/...` без знания IP.

---

# Итог модуля

| Тема | Практический вывод |
|---|---|
| Эфемерность | Без volume/mount данные исчезают вместе с контейнером |
| Bind Mount | Удобен для разработки и hot-reload |
| Named Volume | Нужен для production-данных (Postgres и т.п.) |
| Default bridge | Связь по IP есть, IP нестабильны |
| Custom network | DNS по имени контейнера — App «видит» DB как `pg-db` |

Дальше логичный шаг: один `docker compose` / два контейнера (app + db) в общей сети с volume для данных Postgres.
