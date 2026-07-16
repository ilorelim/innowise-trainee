# Эссе: Multi-stage build

**Задание:** объяснить, как `FROM ... AS builder` и `COPY --from=builder ...` решают проблему тяжёлого SDK при сборке и лёгкого Runtime при запуске.

---

## Зачем нужен multi-stage

Для компилируемых и «собираемых» проектов (Java, Go, C#, фронтенд на Node) обычно нужны две разные вещи:

1. **Инструменты сборки (SDK / toolchain)** — тяжёлые: JDK + Maven, .NET SDK, Go compiler, Node + npm. Они нужны, чтобы получить артефакт (`.jar`, `.dll`, папку `dist/`).
2. **Среда запуска (runtime)** — лёгкая: JRE, `aspnet`, `scratch`/`alpine`, nginx. Ей нужен только готовый результат, без компилятора.

Если собирать и запускать в одном образе со SDK, в продакшен уезжают лишние сотни мегабайт или гигабайт: компилятор, зависимости для сборки, исходники. Это медленнее тянуть, больше поверхность атаки и хуже соответствует принципу «в образе только то, что нужно в рантайме».

## Как это решает `FROM ... AS builder` и `COPY --from=builder`

Dockerfile может содержать **несколько этапов**, каждый со своим `FROM`. Имя этапа задаётся через `AS`:

```dockerfile
FROM heavy-sdk-image AS builder
# здесь: restore / compile / publish / npm run build
# результат лежит, например, в /app/publish или /app/dist

FROM light-runtime-image AS final
COPY --from=builder /app/publish /app
# в финальном образе — только runtime + артефакт
```

Что происходит при `docker build`:

1. Собирается этап `builder` на тяжёлом образе.
2. Собирается этап `final` на лёгком образе.
3. `COPY --from=builder ...` копирует файлы **из файловой системы этапа builder**, а не с хоста.
4. В итоговый тег попадает **только последний этап** (или явно указанный `--target`). Слои SDK в финальный образ не входят.

Итог: сборка использует SDK, а запуск — только runtime. Один Dockerfile даёт и воспроизводимую сборку, и маленький безопасный образ.

## Примеры связок

| Сборка (builder) | Запуск (final) | Артефакт |
|---|---|---|
| `node:18` | `nginx:alpine` | `dist/` |
| `dotnet/sdk:8.0` | `dotnet/aspnet:8.0` | publish |
| `maven` + JDK | `eclipse-temurin:jre` | `.jar` |
| `golang` | `scratch` / `alpine` | бинарник |

Практика в этом модуле: `task2/` (Node → nginx) и `task3/` (.NET SDK → aspnet runtime).
