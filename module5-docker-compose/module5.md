# Модуль 5. Docker Compose

**Цель модуля:** перестать писать длинные `docker run ...` команды. Освоить `docker-compose.yml` для управления многоконтейнерными приложениями.

## Структура папок

```
module5-docker-compose/
  module5.md              ← отчёт по выполненным заданиям
  docker-compose.yaml     ← рецепт стека (app + db)
  app/                    ← FastAPI-приложение (из М2)
    Dockerfile
    app.py
    requirements.txt
  database/               ← зарезервировано под данные БД (пока пусто)
```

---

# 1. Теория: что такое docker-compose.yml?

**docker-compose.yml** (или `docker-compose.yaml`) — YAML-файл, который **декларативно** (описательно) говорит Docker, что мы хотим запустить: сервисы, сети, volumes.

Вместо длинных императивных команд:

```bash
docker run -d --name app -p 5000:5000 ...
docker run -d --name db -p 5432:5432 -e POSTGRES_PASSWORD=... postgres:14-alpine
```

один файл описывает весь стек. Compose читает «рецепт» и поднимает контейнеры вместе (общая сеть по умолчанию, зависимости, порты).

### Вывод

Compose — это **рецепт** для запуска стека: один файл → несколько сервисов одной командой.

---

# 2. Установка: проверка Compose

Нужен **Docker Compose v2** (плагин `docker compose`) или классический `docker-compose` (v1). В Docker Desktop он встроен.

```bash
docker compose version
# Docker Compose version v5.1.3

docker --version
# Docker version 29.4.2, build 055a478
```

В этом проекте используется плагин v2: команды вида `docker compose ...` (с пробелом). Эквивалент v1: `docker-compose ...` (через дефис).

---

# 3. Создание docker-compose.yml

Файл: `docker-compose.yaml` (версия Compose file format **3.8**).

```yaml
version: "3.8"

services:
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
```

| Ключ | Смысл |
|---|---|
| `version` | формат файла Compose (3.8 / 3.9) |
| `services` | список контейнеров стека |
| `build` | собрать образ из Dockerfile |
| `image` | взять готовый образ с registry |
| `ports` | проброс `хост:контейнер` |
| `environment` | переменные окружения (пароль Postgres) |

---

# 4. Сервис 1: App

Приложение из М2 лежит в `app/` и описано как сервис `app`.

### Dockerfile (`app/Dockerfile`)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Приложение (`app/app.py`)

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello, World!"}


@app.get("/hello")
def hello(name: str = "World"):
    return {"message": f"Hello, {name}!"}
```

### Фрагмент Compose

```yaml
app:
  build:
    context: ./app
    dockerfile: Dockerfile
  ports:
    - "5000:5000"
```

- `build.context: ./app` — контекст сборки и путь к Dockerfile сервиса.
- `ports: "5000:5000"` — API доступен на `http://localhost:5000/`.

---

# 5. Сервис 2: DB

PostgreSQL (из М4) описан как сервис `db` на готовом образе:

```yaml
db:
  image: postgres:14-alpine
  environment:
    - POSTGRES_PASSWORD=password
  ports:
    - "5432:5432"
```

- `image: postgres:14-alpine` — лёгкий официальный Postgres 14.
- `POSTGRES_PASSWORD` — обязательная переменная для старта образа.
- Порт `5432` проброшен на хост (как в ручном `docker run` из М4).

Compose автоматически создаёт общую bridge-сеть для сервисов проекта: `app` может обращаться к БД по имени хоста **`db`** (DNS), без знания IP.

---

# 6. Запуск: docker compose up

Из каталога `module5-docker-compose/`:

```bash
cd module5-docker-compose
docker compose up
```

Первый запуск:

1. Собирает образ сервиса `app` по `app/Dockerfile`.
2. Тянет `postgres:14-alpine` (если ещё нет локально).
3. Стартует оба контейнера.

### Критерий

В **одном терминале** видны логи обоих сервисов (строки чередуются с префиксами `app-1` / `db-1`).

Проверка приложения:

```bash
curl http://localhost:5000/
# {"message":"Hello, World!"}
```

Остановка foreground-режима: **Ctrl+C**.

---

# 7. Фоновый режим: up -d

```bash
docker compose up -d
```

Контейнеры работают в detached-режиме; терминал свободен.

---

# 8. Управление: ps и logs

Статус сервисов:

```bash
docker compose ps
```

Логи одного сервиса:

```bash
docker compose logs app
```

Логи всех сервисов с follow (как `tail -f`):

```bash
docker compose logs -f
```

Выход из follow: **Ctrl+C** (контейнеры при этом продолжают работать в фоне).

---

# 9. Остановка: docker compose down

```bash
docker compose down
```

### Контекст

`down` останавливает и **удаляет** контейнеры проекта и (по умолчанию) созданную Compose-сеть. Именованные volumes, если они объявлены и не переданы с `-v`, по умолчанию **сохраняются**.

Сравнить с ручным миром М4: вместо `docker stop` + `docker rm` + `docker network rm` — одна команда.

---

# 10. Сборка: build / up --build

Явно пересобрать образы (например после правок Dockerfile или `app.py`):

```bash
docker compose build
```

Или поднять стек с принудительной пересборкой:

```bash
docker compose up --build
```

---

# Итог модуля

| Тема | Практический вывод |
|---|---|
| Compose-файл | Декларативный «рецепт» стека (сервисы, порты, env) |
| `app` | Сборка из `./app` + порт 5000 |
| `db` | Готовый `postgres:14-alpine` + порт 5432 |
| `up` | Один терминал — логи всего стека |
| `up -d` / `ps` / `logs` | Фон, статус, логи без длинных `docker run` |
| `down` | Удаляет контейнеры и сеть проекта |
| `build` | Явная пересборка образов сервисов |

Дальше логичный шаг: volumes для данных Postgres в Compose, `depends_on`, переменные окружения для строки подключения App → DB.
