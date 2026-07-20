# Модуль 6. Продвинутый Docker Compose

**Цель модуля:** настроить production-ready `docker-compose.yml` со связями сервисов, volumes, переменными окружения и healthcheck (стек из 3+ сервисов: `app`, `db`, `redis`).

## Структура папок

```
module6-docker-compose-advanced/
  module6.md              ← отчёт по выполненным заданиям
  docker-compose.yml      ← стек app + db + redis
  .env                    ← секреты (локально, не в git)
  .gitignore              ← запрещает пуш .env
  app/
    Dockerfile
    app.py
    requirements.txt
```

---

# 1. Переменные окружения в сервисе `db`

В сервис PostgreSQL добавлен блок `environment`. Значения не захардкожены в compose — подставляются из `.env` через `${...}`:

```yaml
db:
  image: postgres:14-alpine
  environment:
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - POSTGRES_DB=pg-db
```

### Вывод

Сервис `db` получает учётные данные Postgres из переменных окружения Compose.

---

# 2. Файл `.env` и защита секретов

В корне модуля создан `.env`:

```env
POSTGRES_USER=devops
POSTGRES_PASSWORD=mysecret
```

В `docker-compose.yml` используются подстановки:

```yaml
- POSTGRES_USER=${POSTGRES_USER}
- POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

Compose автоматически читает `.env` из каталога проекта и подставляет значения при парсинге файла.

### `.gitignore` — чтобы секреты не попали в git

Добавлен файл `.gitignore`:

```gitignore
# Секреты и локальные переменные окружения — не коммитить
.env
.env.*
!.env.example
```

Так `.env` не попадёт в коммит и не будет запушен в удалённый репозиторий. В `docker-compose.yml` остаются только ссылки `${POSTGRES_USER}` / `${POSTGRES_PASSWORD}`, без паролей в открытом виде.

### Критерий

Compose «подтягивает» переменные из `.env`. Секреты не хранятся в `docker-compose.yml` и не уходят в git благодаря `.gitignore`.

---

# 3. Связь сервисов: `DATABASE_URL` в `app`

В сервис `app` передана строка подключения к БД. Имя хоста — **`db`** (имя сервиса в Compose = DNS-имя во внутренней сети):

```yaml
app:
  environment:
    - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/pg-db
```

Compose создаёт общую сеть по умолчанию: контейнеры видят друг друга по именам сервисов (`db`, `redis`, `app`).

### Критерий

Приложение `app` может обратиться к PostgreSQL по адресу `db:5432` внутри сети Compose.

---

# 4. Named volume для `db`

Данные Postgres вынесены в именованный volume:

```yaml
db:
  volumes:
    - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### Критерий

Данные персистентны: при `docker compose down` volume сохраняется (удаляется только с `docker compose down -v`).

---

# 5. Bind mount для `app` (разработка)

Для «горячей» подмены кода смонтирован каталог приложения:

```yaml
app:
  volumes:
    - ./app:/app
```

Изменения в `app/` на хосте сразу видны в контейнере (при `--reload` у uvicorn — без пересборки образа).

### Критерий

Bind mount `./app:/app` даёт удобную разработку с живым кодом внутри контейнера.

---

# 6. `depends_on`: порядок запуска

Базовый порядок: `app` зависит от `db` (и от `redis`). Сначала стартуют зависимости, затем приложение.

```yaml
app:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_started
```

### Критерий

`db` (и `redis`) стартуют раньше, чем `app`.

---

# 7. Healthcheck в `db`

Проверка готовности Postgres через `pg_isready`:

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    retries: 5
    interval: 10s
    timeout: 5s
```

Пользователь берётся из той же переменной, что и `POSTGRES_USER`, чтобы healthcheck не расходился с реальными credentials.

### Критерий

`docker compose ps` показывает статус `(healthy)` у `db` после успешного `pg_isready`.

---

# 8. `depends_on` + healthcheck

`app` ждёт не просто старта контейнера `db`, а **здорового** состояния:

```yaml
depends_on:
  db:
    condition: service_healthy
```

### Критерий

`app` не запускается, пока healthcheck `db` не станет успешным (`pg_isready` вернёт ok).

---

# 9. Третий сервис: Redis

Добавлен сервис из готового образа:

```yaml
redis:
  image: redis:alpine
```

`app` зависит от него с условием `service_started` (достаточно факта старта контейнера).

### Критерий

`docker compose up` поднимает три сервиса: `app`, `db`, `redis`.

---

# 10. Масштабирование `app`

Запуск трёх инстансов приложения:

```bash
docker compose up -d --scale app=3
```

### Критерий / ограничение

В `docker compose ps` видно 3 инстанса `app` и по одному `db` / `redis`.  
Проброс одного и того же порта хоста (`ports: "5000:5000"`) при `--scale app=3` конфликтует: на хосте порт `5000` может занять только один контейнер. Для нескольких реплик нужен reverse-proxy (Nginx и т.п.) или отказ от фиксированного publish порта — это уже шаг в сторону оркестрации (Kubernetes).

---

# Итоговый `docker-compose.yml`

```yaml
version: "3.8"

services:
  db:
    image: postgres:14-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=pg-db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      retries: 5
      interval: 10s
      timeout: 5s
  redis:
    image: redis:alpine
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/pg-db
    ports:
      - "5000:5000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./app:/app

volumes:
  postgres-data:
```

---

# Команды для проверки

```bash
# поднять стек
docker compose up -d --build

# статус и healthy
docker compose ps

# логи
docker compose logs -f

# масштабирование (ожидаем конфликт портов на 5000)
docker compose up -d --scale app=3

# остановить (volume postgres-data сохранится)
docker compose down
```

### Итог модуля

Собран стек из трёх сервисов с секретами в `.env` (защищены `.gitignore`), named volume для Postgres, bind mount для разработки, healthcheck и ожиданием healthy `db`, плюс Redis и попытка масштабирования `app`.
