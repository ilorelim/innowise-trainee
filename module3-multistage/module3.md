# Модуль 3. Продвинутый Dockerfile

**Цель модуля:** научиться писать правильные (эффективные, быстрые, безопасные) Dockerfile, используя кеширование слоёв и multi-stage builds.

## Структура папок

```
module3-multistage/
  module3.md          ← конспект модуля
  esse.md             ← эссе про multi-stage build
  task1/              ← кеш слоёв, оптимизация COPY, .dockerignore (Python из М2)
  task2/              ← multi-stage статичный сайт + non-root + HEALTHCHECK
  task3/              ← multi-stage .NET (SDK → runtime)
```

---

# 1. Теория: что такое кеширование слоёв?

Docker собирает образ **по слоям**. Каждая инструкция (`FROM`, `RUN`, `COPY`, `ADD` и т.д.) создаёт слой.

Docker **кеширует** каждый шаг. Если входные данные для шага не изменились, Docker берёт готовый слой из кеша (`CACHED`) — сборка ускоряется.

Правило: если слой изменился, **все последующие** слои пересобираются заново.

## Задание: собрать my-app:1.0 дважды

Файлы: `task1/` (приложение из модуля 2).

Начальный Dockerfile (неоптимальный):

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

```bash
cd task1
docker build -t my-app:1.0 .
docker build -t my-app:1.0 .
```

### Вывод после первой сборки (~14 с)

```
[+] Building 14.5s (9/9) FINISHED
 => [1/4] FROM docker.io/library/python:3.10-slim
 => CACHED [2/4] WORKDIR /app
 => [3/4] COPY . .
 => [4/4] RUN pip install -r requirements.txt     12.1s
```

### Вывод после второй сборки (~0.4 с)

```
[+] Building 0.4s (9/9) FINISHED
 => CACHED [2/4] WORKDIR /app
 => CACHED [3/4] COPY . .
 => CACHED [4/4] RUN pip install -r requirements.txt
```

Второй раз почти всё из `CACHED` — файлы не менялись.

---

# 2. Проблема: «сломать» кеш

Изменить одну строку в `app.py` и собрать снова:

```bash
docker build -t my-app:1.0 .
```

### Вывод после изменения app.py

```
[+] Building 14.1s (9/9) FINISHED
 => CACHED [2/4] WORKDIR /app
 => [3/4] COPY . .                                          ← кеш сломан
 => [4/4] RUN pip install -r requirements.txt     10.9s   ← выполнилось заново!
```

`COPY . .` копирует весь проект, включая `app.py`. Изменение кода инвалидирует этот слой и **все следующие**, в том числе `RUN pip install`, хотя `requirements.txt` не менялся. Это медленно и неэффективно.

---

# 3. Оптимизация кеша: разделить COPY

Сначала копируем файл зависимостей и ставим их, потом — остальной код.

Итоговый Dockerfile в `task1/`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

Аналогично в других стеках:
- Node: `COPY package.json` → `npm install` → `COPY . .`
- Java: `COPY pom.xml` → `mvn dependency:go-offline` → `COPY . .`
- .NET: `COPY *.csproj` → `dotnet restore` → `COPY . .`

### После оптимизации: снова меняем app.py

```
[+] Building 0.9s (10/10) FINISHED
 => CACHED [3/5] COPY requirements.txt .
 => CACHED [4/5] RUN pip install -r requirements.txt   ← из кеша!
 => [5/5] COPY . .                                     ← пересобран только этот слой
```

`pip install` больше не перезапускается при правках кода — сборка заметно быстрее.

---

# 4. Теория и практика: .dockerignore

`COPY . .` по умолчанию копирует **всё** из контекста: `.git`, `venv`, `node_modules`, `.idea` и т.д. Это мусор в образе и лишние инвалидации кеша.

Файл `task1/.dockerignore`:

```
venv/
__pycache__/
.git/
Dockerfile
node_modules/
```

Критерий: `.dockerignore` создан — при `COPY . .` эти пути не попадают в образ.

---

# 5. Теория: Multi-stage build (эссе)

Эссе вынесено в отдельный файл: [esse.md](./esse.md).

Кратко: тяжёлый SDK нужен только на этапе сборки; финальный образ берёт runtime и артефакт через `COPY --from=builder`, поэтому SDK в продакшен не попадает.

---

# 6. Практика Multi-stage: статичный сайт

**Задача:** Dockerfile для статичного сайта (React/Angular/Vue-паттерн).  
**Критерий:** финальный образ — маленький nginx (~20–40 МБ), а не node (~1 ГБ).

Файлы: `task2/`

## Схема

```
┌─────────────────────────────┐
│  Stage build (node:18)      │
│  npm install                │
│  npm run build → dist/      │
└──────────────┬──────────────┘
               │ COPY --from=build только dist/
               ▼
┌─────────────────────────────┐
│  Stage final (nginx:alpine) │
│  non-root + HEALTHCHECK     │
│  (~20–40 МБ)                │
└─────────────────────────────┘
```

## Dockerfile (`task2/Dockerfile`)

```dockerfile
FROM node:18 AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

RUN apk add --no-cache curl \
    && addgroup -S appgroup && adduser -S appuser -G appgroup \
    && chown -R appuser:appgroup /usr/share/nginx/html /var/cache/nginx /var/log/nginx

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

## package.json

```json
{
  "name": "module3-static-site",
  "private": true,
  "version": "1.0.0",
  "scripts": {
    "build": "mkdir -p dist && cp index.html dist/"
  }
}
```

`npm run build` создаёт папку `dist/` с готовой статикой.  
В реальном React/Vue это обычно `vite build` / `ng build`. Для демо скрипт упрощён (без Vite), чтобы `npm install` не тянул зависимости минутами — смысл multi-stage тот же.

## nginx.conf (порт 8080 для non-root)

Без root нельзя слушать порт 80. Поэтому nginx слушает **8080**, pid/логи/temp — в `/tmp`, плюс `location /health` для HEALTHCHECK.

## Сборка и запуск

```bash
cd task2
docker build -t module3-static:demo .
docker images module3-static:demo
docker run -d -p 8080:8080 --name m3-static module3-static:demo
```

- http://localhost:8080 — страница из `dist/`
- http://localhost:8080/health — `ok`
- `docker ps` — статус `(healthy)`
- `docker exec m3-static whoami` — `appuser` (не root)

---

# 7. Инструкция ARG vs ENV

| | **ARG** | **ENV** |
|---|---|---|
| Когда существует | только во время `docker build` | в образе и в запущенном контейнере |
| После сборки | исчезает (не доступна в `docker run`, если не продублирована в ENV) | остаётся |
| Типичное применение | параметры сборки: версия базы, флаги | настройки приложения в рантайме |

### ARG — для сборки

```dockerfile
ARG NODE_VERSION=18
FROM node:${NODE_VERSION} AS build
```

```bash
docker build --build-arg NODE_VERSION=20 -t my-app .
```

`ARG` удобен для `FROM image:${VERSION}`, выбора режима сборки и т.п. В работающем контейнере его уже нет.

### ENV — для контейнера

```dockerfile
ENV DATABASE_URL=postgres://db:5432/app
ENV ASPNETCORE_URLS=http://+:8080
```

`ENV` виден процессу внутри контейнера (`os.environ`, `process.env`). Секреты лучше не зашивать в образ через `ENV` в Dockerfile — передавать при запуске (`-e`, secrets).

**Кратко:** `ARG` — «как собирать» (`FROM node:${VERSION}`), `ENV` — «как работать» (`DATABASE_URL`).

---

# 8. Безопасность: запуск от non-root

По умолчанию процесс в контейнере часто идёт от `root`. При компрометации приложения злоумышленник получает root внутри контейнера — это опаснее.

Задание (alpine), как в `task2`:

```dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
# ... chown нужных каталогов ...
USER appuser
```

Критерий: контейнер работает от `appuser`, не от `root`.

**Важно для nginx:** non-root не может занять порт ниже 1024. Нужно слушать 8080+ и дать права на pid/cache/logs (см. `task2/nginx.conf`).

В официальном `dotnet/aspnet` уже есть non-root: `USER $APP_UID` (как в `task3`).

---

# 9. Инструкция HEALTHCHECK

Docker периодически проверяет, жив ли сервис внутри контейнера.

В `task2`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1
```

- `CMD` здесь — команда **проверки**, не путать с `CMD` запуска приложения.
- `curl --fail` возвращает ошибку при HTTP ≥ 400 → healthcheck failed.
- Нужен установленный `curl` (`apk add --no-cache curl`) и endpoint `/health`.

Критерий: `docker ps` показывает `(healthy)` / `(unhealthy)`.

`HEALTHCHECK` и основной `CMD` — разные инструкции:

```dockerfile
HEALTHCHECK ... CMD curl --fail http://localhost:8080/health || exit 1
CMD ["nginx", "-g", "daemon off;"]   # как стартует контейнер
```

---

# 10. Практика Multi-stage: Java / C# (.NET)

**Задача:** Dockerfile для Java/C# (.NET-пример).  
**Критерий:** итоговый образ содержит **runtime** (`aspnet`), а не **SDK**.

Файлы: `task3/`

## Схема

```
┌──────────────────────────────────┐
│  Stage build (dotnet/sdk:8.0)    │
│  dotnet restore                  │
│  dotnet publish → /app/publish   │
└──────────────┬───────────────────┘
               │ COPY --from=build
               ▼
┌──────────────────────────────────┐
│  Stage final (dotnet/aspnet:8.0) │
│  runtime + MyApp.dll             │
└──────────────────────────────────┘
```

## Dockerfile (`task3/Dockerfile`)

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src

COPY *.csproj .
RUN dotnet restore

COPY . .
RUN dotnet publish -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final

WORKDIR /app

COPY --from=build /app/publish .

USER $APP_UID

EXPOSE 8080

ENTRYPOINT ["dotnet", "MyApp.dll"]
```

## Program.cs

```csharp
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => "Hello from multi-stage .NET");
app.MapGet("/health", () => Results.Ok("ok"));

app.Run();
```

## Сборка и запуск

```bash
cd task3
docker build -t module3-dotnet:demo .
docker images module3-dotnet:demo
docker run -d -p 8080:8080 module3-dotnet:demo
```

Финальный образ основан на `aspnet:8.0` (runtime), SDK в него не входит.

Для Java идея та же: `maven/jdk` (или `gradle`) как `AS build` → `COPY --from=build` `.jar` в образ с `jre`.

---

# Чеклист критериев модуля

| Задача | Критерий | Где |
|---|---|---|
| Кеш слоёв | вторая сборка — `CACHED` | `task1/` |
| Сломать кеш | правка `app.py` → `pip install` заново | `task1/` (старый порядок COPY) |
| Оптимизация COPY | при правке `app.py` — `pip install` из кеша | `task1/Dockerfile` |
| `.dockerignore` | создан | `task1/.dockerignore` |
| Эссе multi-stage | `AS builder` + `COPY --from=` | [esse.md](./esse.md) |
| Multi-stage сайт | маленький nginx-образ | `task2/` |
| ARG vs ENV | ARG — build, ENV — runtime | раздел 7 |
| non-root | процесс = `appuser` | `task2/` |
| HEALTHCHECK | `docker ps` → `(healthy)` | `task2/` |
| Multi-stage .NET | runtime, не SDK | `task3/` |
