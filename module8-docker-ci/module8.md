# Модуль 8. CI/CD — Docker build & push в Registry

**Цель модуля:** докрутить пайплайн: GitHub Actions собирает Dockerfile и пушит образ в Registry (Docker Hub), с разделением CI/CD и multi-arch сборкой.

## Структура

```
.github/workflows/
  docker-ci.yml            ← CI: тесты на pull_request → main
  docker-cd.yml            ← CD: build & push на push → main
module8-docker-ci/
  module8.md               ← отчёт
  app/
    Dockerfile             ← образ приложения
    app.py                 ← FastAPI
    requirements.txt
    tests/
      test_app.py
```

---

# 1. Что такое Docker Registry?

**Registry** — хранилище Docker-образов (аналог GitHub, но для образов).

Примеры: Docker Hub, GitHub Container Registry (GHCR), GitLab Registry.

| Операция | Смысл |
|----------|--------|
| `docker push` | загрузить образ в Registry |
| `docker pull` | скачать образ откуда угодно |

### Вывод

Registry хранит готовые артефакты сборки. CD публикует образ; сервер деплоя делает `pull` без пересборки из исходников.

---

# 2. Secrets: доступ к Docker Hub

1. На hub.docker.com создан Access Token (Read & Write).
2. В GitHub → Settings → Secrets and variables → Actions:
   - `DOCKER_USERNAME` — логин Docker Hub
   - `DOCKER_PASSWORD` — access token (не пароль от сайта)

В workflow логин:

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}
```

### Вывод

Секреты не попадают в код; CI/CD получает их только во время запуска job.

---

# 3. CI: `.github/workflows/docker-ci.yml`

**Триггер:** `pull_request` → `main`.

**Job `test`:** checkout → setup-python → `pip install` → `flake8` → `pytest`.

Рабочая директория: `module8-docker-ci/app`.

### Вывод

На PR образ **не** пушится — только проверка кода.

---

# 4. CD: `.github/workflows/docker-cd.yml`

**Триггер:** `push` → `main`.

**Job `build-push`:**

1. checkout  
2. Login to Docker Hub  
3. `docker/setup-qemu-action@v3`  
4. `docker/setup-buildx-action@v3`  
5. `docker/build-push-action@v5`:
   - `context: ./module8-docker-ci/app`
   - `push: true`
   - `platforms: linux/amd64,linux/arm64`
   - теги: `ilorelim/my-app:latest` и `ilorelim/my-app:${{ github.sha }}`

### Вывод

После merge в `main` появляется готовый к деплою multi-arch образ. `github.sha` делает тег уникальным для каждого коммита.

---

# 5. Разделение CI и CD

| Workflow | Когда | Что делает |
|----------|--------|------------|
| `docker-ci.yml` | PR в `main` | lint + тесты |
| `docker-cd.yml` | push в `main` | build & push в Docker Hub |

Раньше в одном файле job `build-push` зависел от `test` через `needs: test`. После разделения workflows связь косвенная: в `main` попадает только код, прошедший CI.

### Вывод

`main` всегда соответствует «готовому к деплою» образу в Registry.

---

# 6. Multi-arch (QEMU + Buildx)

- **QEMU** — эмуляция других архитектур на runner.  
- **Buildx** — сборщик, умеющий multi-platform образы.  
- `platforms: linux/amd64,linux/arm64` — один манифест для Intel и ARM (M1/M2/M3).

### Вывод

CI/CD собирает образ, который работает и на AMD64, и на ARM64.

---

# 7. Практика: проверка на Docker Hub

1. PR → зелёный **Docker CI**.  
2. Merge в `main` → **Docker CD** пушит образ.  
3. На Docker Hub в репозитории `my-app` видны теги `latest` и `[commit sha]`.

### Вывод

Пайплайн закрывает цикл: тест на PR → публикация образа из `main` в Registry.
