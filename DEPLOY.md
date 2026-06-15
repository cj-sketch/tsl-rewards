# Деплой TSL Rewards на свой Linux-хост

Статический сайт за nginx (non-root), полностью изолированный контейнер.
Нужен только установленный Docker + плагин Compose.

## Получить код на хост

**Репо публичный** — просто:
```bash
git clone https://github.com/cj-sketch/tsl-rewards.git
```

**Репо приватный** — по read-only deploy-key (приватный ключ — в `credentials.md`, секция «GitHub Deploy Key — tsl-rewards»):
```bash
# 1) положить приватный ключ
install -m 600 /dev/stdin ~/.ssh/tsl_rewards_deploy   # вставить ключ, Ctrl-D
# 2) ssh-алиас
cat >> ~/.ssh/config <<'EOF'
Host github-tsl-rewards
  HostName github.com
  User git
  IdentityFile ~/.ssh/tsl_rewards_deploy
  IdentitiesOnly yes
EOF
# 3) клон по алиасу
git clone git@github-tsl-rewards:cj-sketch/tsl-rewards.git
```

## Запуск
```bash
docker compose up -d --build
```
Открыть: `http://<host>:8080`

Другой host-порт:
```bash
TSL_REWARDS_PORT=9000 docker compose up -d --build
```

## Обновление
```bash
git pull                       # или просто заменить index.html
docker compose up -d --build
```

## Остановить / снести
```bash
docker compose down            # стоп + удалить контейнер и сеть
```

## Что внутри и как изолировано
- образ `nginxinc/nginx-unprivileged:stable-alpine` — nginx работает **не от root**;
- своя bridge-сеть `tsl-rewards-net` — не пересекается с другими проектами на хосте;
- `read_only` корневая ФС + tmpfs только под временные пути nginx (`/tmp`, `/var/cache/nginx`, `/var/run`);
- сняты **все** Linux-capabilities, `no-new-privileges`, лимиты RAM (128m) / CPU (0.5) / pids (64);
- наружу торчит **только** порт 8080;
- healthcheck дёргает сам себя раз в 30с.

## За доменом с HTTPS
Контейнер слушает plain HTTP на 8080. Для домена поставить его за свой reverse-proxy
(nginx / Caddy / Traefik) с TLS, например проксировать `https://rewards.tsl-agency.com` → `127.0.0.1:8080`.

## Примечания
- Tailwind подключён через CDN (`cdn.tailwindcss.com`) — нужен интернет у **браузера клиента**
  (не у контейнера). Для прод-оптимизации позже можно вкомпилить Tailwind в статику и убрать CDN.
- Видео в разделе «База про агентов» — внешний Loom-iframe.
- Если на твоём Docker `read_only` капризничает (старая версия) — убрать строку `read_only: true`
  и блок `tmpfs`; остальная изоляция останется.
