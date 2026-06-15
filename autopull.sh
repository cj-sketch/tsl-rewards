#!/usr/bin/env bash
# Автопулл tsl-rewards: тянет репо и, если появился новый коммит, пересобирает контейнер.
# Кладётся рядом с docker-compose.yml (в корне клона репо).
#
# Установка в крон (раз в минуту), от пользователя, у которого есть docker:
#   chmod +x autopull.sh
#   ( crontab -l 2>/dev/null; echo "* * * * * /ПУТЬ/К/tsl-rewards/autopull.sh >> /var/log/tsl-rewards-autopull.log 2>&1" ) | crontab -
#
# Дальше: я пушу в GitHub → в течение минуты сервер сам подтягивает и обновляет сайт.

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

before="$(git rev-parse HEAD 2>/dev/null || echo none)"
git pull --quiet --ff-only || { echo "$(date -Is) pull failed"; exit 1; }
after="$(git rev-parse HEAD)"

if [ "$before" != "$after" ]; then
  echo "$(date -Is) новый коммит $after — пересобираю"
  docker compose up -d --build
fi
