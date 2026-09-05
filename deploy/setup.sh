#!/usr/bin/env bash
# ============================================================
#  Amiri — танзими деплой.
#
#  Аз папкаи `expenses/` иҷро мешавад, баъд аз он ки ҳар ду
#  репозиторий clone шудаанд:
#
#     bash backend/deploy/setup.sh            # суроға = IP-и сервер
#     bash backend/deploy/setup.sh example.ru # суроға = домен (HTTPS)
#
#  Скрипт:
#    • docker-compose.yml-ро аз репо ба папкаи болоӣ мегузорад
#    • .env месозад ва сирҳои тасодуфиро худаш пур мекунад
#    • .env-и мавҷударо ҲЕҶ ГОҲ намешиканад
# ============================================================
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
cd "$ROOT"

[ -d backend ] && [ -d frontend ] || {
    echo "✗ Дар $ROOT папкаҳои backend ва frontend нестанд."
    echo "  Аввал ҳар дуро clone кунед — ниг. README."
    exit 1
}

# --- 1. compose ҳамеша аз репо нав гирифта мешавад ---
cp "$HERE/docker-compose.yml" ./docker-compose.yml
echo "✓ docker-compose.yml"

# --- 2. .env: як бор сохта мешавад ва баъд даст нахӯрда мемонад ---
if [ -f .env ]; then
    echo "• .env аллакай ҳаст — даст намерасонем"
else
    cp "$HERE/env.example" .env
    chmod 600 .env

    # Сирҳо: аз openssl, на дастӣ — то парол «123456» нашавад
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 16)|" .env
    sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$(openssl rand -hex 32)|" .env
    sed -i "s|^WEBHOOK_SECRET=.*|WEBHOOK_SECRET=$(openssl rand -hex 16)|" .env

    if [ "${1:-}" != "" ]; then
        # Домен дода шуд → HTTPS, webhook, Mini App дар Telegram кор мекунад
        HOST=${1#http*://}; HOST=${HOST%%/*}
        sed -i "s|^BOT_MODE=.*|BOT_MODE=webhook|"                 .env
        sed -i "s|^PUBLIC_URL=.*|PUBLIC_URL=https://$HOST|"       .env
        sed -i "s|^PANEL_URL=.*|PANEL_URL=https://$HOST|"         .env
        echo "✓ .env — домени https://$HOST, реҷаи webhook"
    else
        IP=$(curl -fsS --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')
        sed -i "s|SERVER_IP|$IP|g" .env
        echo "✓ .env — IP $IP, реҷаи polling"
    fi
fi

echo
echo "Қадами навбатӣ: BOT_TOKEN ва OPENAI_API_KEY-ро гузоред —"
echo "    nano $ROOT/.env"
echo "Сипас:"
echo "    cd $ROOT && docker compose up -d --build"
