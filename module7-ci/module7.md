# Модуль 7. CI/CD — первый пайплайн

**Цель модуля:** понять концепцию CI/CD и настроить первый пайплайн для linting и unit-тестов.

## Структура

```
.github/workflows/ci.yml   ← workflow GitHub Actions (корень репозитория)
module7-ci/
  module7.md               ← отчёт
  app.py                   ← код для проверки
  requirements.txt         ← pytest, flake8
  tests/
    test_app.py            ← unit-тесты
```

---

# 1. Что такое CI (Continuous Integration)?

**CI** — автоматическая сборка и тестирование кода при каждом `git push` или Pull Request.

Пайплайн проверяет изменения **до** попадания в `main`: линтер, тесты, при необходимости сборка. Если проверки падают — merge блокируется (или как минимум виден красный крестик).

### Вывод

CI — это «защита» ветки `main`: в основную ветку попадает только код, прошедший автоматические проверки.

---

# 2. Что такое CD (Continuous Delivery / Deployment)?

После успешного CI начинается **CD**:

| Понятие | Смысл |
|--------|--------|
| **Continuous Delivery** | Артефакт **готов** к деплою (можно выкатить одной кнопкой / approve). |
| **Continuous Deployment** | Артефакт **уже задеплоен** автоматически на каждый успешный CI. |

### Вывод

Delivery = «готово к выкатке». Deployment = «уже выкатили». Оба опираются на зелёный CI.

---

# 3. Анатомия GitHub Actions

Иерархия:

```
Workflow (ci.yml)
  └── Event (on: pull_request → main)
        └── Job (test, runs-on: ubuntu-latest)
              └── Steps
                    ├── uses: actions/checkout@v4
                    ├── uses: actions/setup-python@v5
                    └── run: pip / flake8 / pytest
```

| Элемент | Что это |
|---------|---------|
| **Workflow** | YAML-файл в `.github/workflows/` |
| **Event** | Когда запускать (`pull_request`, `push`, …) |
| **Runner** | Виртуалка (`ubuntu-latest`) |
| **Job** | Набор шагов на одном runner (`test`) |
| **Step** | Одна команда или готовый action |

---

# 4. Workflow: `.github/workflows/ci.yml`

Создан файл в корне репозитория (именно туда смотрит GitHub Actions).

**Триггер:**

```yaml
on:
  pull_request:
    branches:
      - main
```

**Job:**

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
```

**Steps:** checkout → setup-python → `pip install` → `flake8 app.py tests` → `pytest`.

Рабочая директория шагов — `module7-ci` (там `requirements.txt` и `tests/`).

---

# 5. Практика: PR и статус Checks

1. Закоммитить изменения модуля 7 (сделано).
2. Запушить ветку и открыть PR в `main`:
   ```bash
   git push -u origin HEAD
   # затем PR: feature → main (через GitHub UI или gh pr create)
   ```
3. GitHub Actions запускает job `test`.
4. В PR появляется зелёная галочка (успех) или красный крестик (падение).

### Вывод

CI-пайплайн автоматически проверяет код на каждом PR в `main`.
