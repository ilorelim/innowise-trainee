# Модуль 1: Концепции и Docker

Запуск готовых контейнеров.

---

## Содержание

- [Установка](#установка)
- [Hello World](#задача-hello-world)
- [Интерактивный режим](#задача-интерактивный-режим)
- [Фоновый режим](#задача-фоновый-режим)
- [Управление контейнерами](#задача-управление)
- [Проброс портов](#задача-проброс-портов)
- [Логи](#задача-логи)
- [Управление образами](#задача-управление-образами)
- [Очистка](#задача-очистка)

---

## Установка

Проверка, что Docker установлен и демон доступен.

### Версия

```bash
docker --version
```

```
Docker version 29.4.2, build 055a478
```

### Информация о системе

```bash
docker info
```

<details>
<summary>Полный вывод <code>docker info</code></summary>

```
Client: Docker Engine - Community
 Version:    29.4.2
 Context:    desktop-linux
 Debug Mode: false
 Plugins:
  agent: Docker AI Agent Runner (Docker Inc.)
    Version:  v1.44.0
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-agent
  ai: Docker AI Agent - Ask Gordon (Docker Inc.)
    Version:  v1.20.2
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-ai
  buildx: Docker Buildx (Docker Inc.)
    Version:  v0.33.0-desktop.1
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-buildx
  compose: Docker Compose (Docker Inc.)
    Version:  v5.1.3
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-compose
  debug: Get a shell into any image or container (Docker Inc.)
    Version:  0.0.47
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-debug
  desktop: Docker Desktop commands (Docker Inc.)
    Version:  v0.3.0
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-desktop
  dhi: CLI for managing Docker Hardened Images (Docker Inc.)
    Version:  v0.0.2
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-dhi
  extension: Manages Docker extensions (Docker Inc.)
    Version:  v0.2.31
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-extension
  init: Creates Docker-related starter files for your project (Docker Inc.)
    Version:  v1.4.0
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-init
  mcp: Docker MCP Plugin (Docker Inc.)
    Version:  v0.40.4
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-mcp
  offload: Docker Offload (Docker Inc.)
    Version:  v0.5.85
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-offload
  pass: Docker Pass Secrets Manager Plugin (beta) (Docker Inc.)
    Version:  v0.0.25
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-pass
  sandbox:  (Docker Inc.)
    Version:  v0.12.0
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-sandbox
  sbom: View the packaged-based Software Bill Of Materials (SBOM) for an image (Anchore Inc.)
    Version:  0.6.0
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-sbom
  scout: Docker Scout (Docker Inc.)
    Version:  v1.20.4
    Path:     /home/dzmitriy/.docker/cli-plugins/docker-scout

Server:
 Containers: 0
  Running: 0
  Paused: 0
  Stopped: 0
 Images: 0
 Server Version: 29.4.1
 Storage Driver: overlayfs
  driver-type: io.containerd.snapshotter.v1
 Logging Driver: json-file
 Cgroup Driver: cgroupfs
 Cgroup Version: 2
 Plugins:
  Volume: local
  Network: bridge host ipvlan macvlan null overlay
  Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
 CDI spec directories:
  /etc/cdi
  /var/run/cdi
 Discovered Devices:
  cdi: docker.com/gpu=webgpu
 Swarm: inactive
 Runtimes: runc io.containerd.runc.v2
 Default Runtime: runc
 Init Binary: docker-init
 containerd version: 77c84241c7cbdd9b4eca2591793e3d4f4317c590
 runc version: v1.3.5-0-g488fc13e
 init version: de40ad0
 Security Options:
  seccomp
   Profile: builtin
  cgroupns
 Kernel Version: 6.12.76-linuxkit
 Operating System: Docker Desktop
 OSType: linux
 Architecture: x86_64
 CPUs: 12
 Total Memory: 3.658GiB
 Name: docker-desktop
 ID: d4fde94c-113c-434e-992e-bf81c6af6b25
 Docker Root Dir: /var/lib/docker
 Debug Mode: false
 HTTP Proxy: http.docker.internal:3128
 HTTPS Proxy: http.docker.internal:3128
 No Proxy: hubproxy.docker.internal
 Labels:
  com.docker.desktop.address=unix:///home/dzmitriy/.docker/desktop/docker-cli.sock
 Experimental: false
 Insecure Registries:
  hubproxy.docker.internal:5555
  ::1/128
  127.0.0.0/8
 Live Restore Enabled: false
 Firewall Backend: iptables
```

</details>

| Параметр | Значение |
| --- | --- |
| Client | 29.4.2 |
| Server | 29.4.1 (Docker Desktop) |
| Context | `desktop-linux` |
| OS / Arch | linux / x86_64 |
| Storage | overlayfs |
| Swarm | inactive |

---

## Задача: Hello World

Первый запуск готового образа — проверка, что Docker скачивает образ и запускает контейнер.

```bash
docker run hello-world
```

```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
4f55086f7dd0: Pull complete
d5e71e642bf5: Download complete
Digest: sha256:96498ffd522e70807ab6384a5c0485a79b9c7c08ca79ba08623edcad1054e62d
Status: Downloaded newer image for hello-world:latest
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

---

## Задача: Интерактивный режим

Запуск Ubuntu с интерактивным терминалом (`-it`), затем выход из контейнера.

```bash
docker run -it ubuntu bash
```

```
Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
2c1ce1d0a589: Pull complete
a9be9fd915e9: Pull complete
bce5ee84b2b4: Download complete
Digest: sha256:b7f48194d4d8b763a478a621cdc81c27be222ba2206ca3ca6bc42b49685f3d9e
Status: Downloaded newer image for ubuntu:latest
root@4f1947a364eb:/# exit
exit
```

---

## Задача: Фоновый режим

Запуск nginx в фоне (`-d` — detached).

```bash
docker run -d nginx
```

```
Unable to find image 'nginx:latest' locally
latest: Pulling from library/nginx
0b19be717994: Pull complete
3b9f3509a826: Pull complete
45ef33eb91c8: Pull complete
062e450697fa: Pull complete
39694cde734e: Pull complete
8d2092eabbc5: Pull complete
6a24a6ebcf30: Pull complete
cd64a2895680: Download complete
29456554d205: Download complete
Digest: sha256:b5a9a3cfc86b81dd6f1458d53f2ad2b559cc255653d2efd6cacee5636bf2066f
Status: Downloaded newer image for nginx:latest
34055217dd607c945229a9e2b9aaf93211e1fdb1335433e7b4912083ace52e55
```

Контейнер запущен, ID: `34055217dd60…`

---

## Задача: Управление

### Работающие контейнеры

```bash
docker ps
```

```
CONTAINER ID   IMAGE     COMMAND                  CREATED         STATUS         PORTS     NAMES
bb0e70df7886   nginx     "/docker-entrypoint.…"   8 seconds ago   Up 8 seconds   80/tcp    hardcore_edison
34055217dd60   nginx     "/docker-entrypoint.…"   6 minutes ago   Up 6 minutes   80/tcp    flamboyant_wright
```

### Все контейнеры (включая остановленные)

```bash
docker ps -a
```

```
CONTAINER ID   IMAGE         COMMAND                  CREATED          STATUS                      PORTS     NAMES
bb0e70df7886   nginx         "/docker-entrypoint.…"   23 seconds ago   Up 22 seconds               80/tcp    hardcore_edison
34055217dd60   nginx         "/docker-entrypoint.…"   7 minutes ago    Up 7 minutes                80/tcp    flamboyant_wright
4f1947a364eb   ubuntu        "bash"                   8 minutes ago    Exited (0) 8 minutes ago              nostalgic_cohen
ef3e0922f171   hello-world   "/hello"                 10 minutes ago   Exited (0) 10 minutes ago             dazzling_visvesvaraya
```

| Контейнер | Образ | Статус |
| --- | --- | --- |
| `hardcore_edison` | nginx | Running |
| `flamboyant_wright` | nginx | Running |
| `nostalgic_cohen` | ubuntu | Exited (0) |
| `dazzling_visvesvaraya` | hello-world | Exited (0) |

---

## Задача: Проброс портов

Остановка одного контейнера и запуск nginx с пробросом порта `8080 → 80`.

```bash
docker stop bb0e7
```

```
bb0e7
```

```bash
docker run -d -p 8080:80 nginx
```

```
b5b98b5b7b0617e78366d4a93508c8a4f3fe1caeb11583c92c06b039f0a0c800
```

Открыть в браузере: [http://localhost:8080](http://localhost:8080)

```
Welcome to nginx!
If you see this page, nginx is successfully installed and working. Further configuration is required for the web server, reverse proxy, API gateway, load balancer, content cache, or other features.

For online documentation and support please refer to nginx.org.
To engage with the community please visit community.nginx.org.
For enterprise grade support, professional services, additional security features and capabilities please refer to f5.com/nginx.

Thank you for using nginx.
```

---

## Задача: Логи

### Просмотр логов

```bash
docker logs b5b98
```

<details>
<summary>Полный вывод логов</summary>

```
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
10-listen-on-ipv6-by-default.sh: info: Enabled listen on IPv6 in /etc/nginx/conf.d/default.conf
/docker-entrypoint.sh: Sourcing /docker-entrypoint.d/15-local-resolvers.envsh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
/docker-entrypoint.sh: Configuration complete; ready for start up
2026/07/15 14:16:35 [notice] 1#1: using the "epoll" event method
2026/07/15 14:16:35 [notice] 1#1: nginx/1.31.2
2026/07/15 14:16:35 [notice] 1#1: built by gcc 14.2.0 (Debian 14.2.0-19)
2026/07/15 14:16:35 [notice] 1#1: OS: Linux 6.12.76-linuxkit
2026/07/15 14:16:35 [notice] 1#1: getrlimit(RLIMIT_NOFILE): 1048576:1048576
2026/07/15 14:16:35 [notice] 1#1: start worker processes
2026/07/15 14:16:35 [notice] 1#1: start worker process 29
2026/07/15 14:16:35 [notice] 1#1: start worker process 30
2026/07/15 14:16:35 [notice] 1#1: start worker process 31
2026/07/15 14:16:35 [notice] 1#1: start worker process 32
2026/07/15 14:16:35 [notice] 1#1: start worker process 33
2026/07/15 14:16:35 [notice] 1#1: start worker process 34
2026/07/15 14:16:35 [notice] 1#1: start worker process 35
2026/07/15 14:16:35 [notice] 1#1: start worker process 36
2026/07/15 14:16:35 [notice] 1#1: start worker process 37
2026/07/15 14:16:35 [notice] 1#1: start worker process 38
2026/07/15 14:16:35 [notice] 1#1: start worker process 39
2026/07/15 14:16:35 [notice] 1#1: start worker process 40
172.17.0.1 - - [15/Jul/2026:14:17:03 +0000] "GET / HTTP/1.1" 200 896 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
172.17.0.1 - - [15/Jul/2026:14:17:03 +0000] "GET /favicon.ico HTTP/1.1" 404 555 "http://localhost:8080/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36" "-"
2026/07/15 14:17:03 [error] 29#29: *1 open() "/usr/share/nginx/html/favicon.ico" failed (2: No such file or directory), client: 172.17.0.1, server: localhost, request: "GET /favicon.ico HTTP/1.1", host: "localhost:8080", referrer: "http://localhost:8080/"
```

</details>

В логах видно:

- nginx стартовал (`nginx/1.31.2`)
- успешный запрос `GET /` → **200**
- отсутствует `favicon.ico` → **404**

### Слежение за логами в реальном времени

```bash
docker logs -f b5b98
```

---

## Задача: Управление образами

### Список образов

```bash
docker images
```

```
IMAGE                ID             DISK USAGE   CONTENT SIZE   EXTRA
hello-world:latest   96498ffd522e       25.9kB         9.49kB    U
nginx:latest         b5a9a3cfc86b        241MB           66MB    U
ubuntu:latest        b7f48194d4d8        160MB         45.3MB    U
```

| Образ | Disk usage | Content size |
| --- | --- | --- |
| `hello-world:latest` | 25.9 kB | 9.49 kB |
| `nginx:latest` | 241 MB | 66 MB |
| `ubuntu:latest` | 160 MB | 45.3 MB |

### Удаление образа

```bash
docker rmi hello-world:latest
```

```
Untagged: hello-world:latest
Deleted: sha256:96498ffd522e70807ab6384a5c0485a79b9c7c08ca79ba08623edcad1054e62d
```

```bash
docker images
```

```
IMAGE           ID             DISK USAGE   CONTENT SIZE   EXTRA
nginx:latest    b5a9a3cfc86b        241MB           66MB    U
ubuntu:latest   b7f48194d4d8        160MB         45.3MB    U
```

---

## Задача: Очистка

Остановка и удаление всех контейнеров.

```bash
docker stop $(docker ps -aq)
```

```
b5b98b5b7b06
bb0e70df7886
34055217dd60
4f1947a364eb
```

```bash
docker rm $(docker ps -aq)
```

```
b5b98b5b7b06
bb0e70df7886
34055217dd60
4f1947a364eb
```

```bash
docker ps -a
```

```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

Список контейнеров пуст — очистка выполнена успешно.
