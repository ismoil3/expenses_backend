#!/usr/bin/env bash
# ============================================================
#  Amiri — домен ва HTTPS тавассути nginx-и худи сервер.
#
#     bash backend/deploy/https.sh amiri.example.tj
#
#  Скрипт:
#    • ба nginx-и сервер як vhost илова мекунад → 127.0.0.1:WEB_PORT
#    • бо certbot сертификати Let's Encrypt мегирад
#    • .env-ро ба HTTPS ва реҷаи webhook мегузаронад
#    • контейнери api-ро аз нав меоғозад
#
#  Ба конфигҳои мавҷудаи nginx даст намерасонад — танҳо як файли
#  нав меофарад ва пеш аз reload ҳатман `nginx -t` мекунад.
# ============================================================
set -euo pipefail

DOMAIN=${1:-}
[ -n "$DOMAIN" ] || { echo "Истифода: bash backend/deploy/https.sh домен.tj"; exit 1; }
DOMAIN=${DOMAIN#http*://}; DOMAIN=${DOMAIN%%/*}

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
cd "$ROOT"
[ -f .env ] || { echo "✗ $ROOT/.env нест"; exit 1; }

WEB_PORT=$(grep -E '^WEB_PORT=' .env | cut -d= -f2)
WEB_PORT=${WEB_PORT:-8348}

command -v nginx >/dev/null || { echo "✗ nginx дар сервер нест"; exit 1; }

# --- 1. vhost ---
SITE=/etc/nginx/sites-available/amiri.conf
echo "→ vhost: $SITE"
cat > "$SITE" <<CONF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Панел, /api ва /webhook/ — ҳамаашро nginx-и контейнер тақсим мекунад
    location / {
        proxy_pass http://127.0.0.1:$WEB_PORT;
        proxy_http_version 1.1;

        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # Аксҳои чек ва дархостҳои OpenAI вақт мегиранд
        client_max_body_size 12m;
        proxy_read_timeout   60s;
    }
}
CONF
ln -sfn "$SITE" /etc/nginx/sites-enabled/amiri.conf

nginx -t
systemctl reload nginx
echo "✓ nginx: http://$DOMAIN"

# --- 2. сертификат ---
if ! command -v certbot >/dev/null; then
    echo "→ certbot насб мешавад…"
    apt-get update -qq && apt-get install -y -qq certbot python3-certbot-nginx
fi
echo "→ certbot (саволҳояшро ҷавоб диҳед)…"
certbot --nginx -d "$DOMAIN"

# --- 3. .env → HTTPS ва webhook ---
sed -i "s|^BOT_MODE=.*|BOT_MODE=webhook|"           .env
sed -i "s|^PUBLIC_URL=.*|PUBLIC_URL=https://$DOMAIN|" .env
sed -i "s|^PANEL_URL=.*|PANEL_URL=https://$DOMAIN|"   .env
echo "✓ .env: реҷаи webhook, суроға https://$DOMAIN"

# --- 4. аз нав оғоз ---
# `restart` .env-ро аз нав намехонад — маҳз --force-recreate лозим аст
docker compose up -d --force-recreate api

echo
echo "Тайёр:  https://$DOMAIN"
echo "Санҷиш: docker compose logs -f api   →  «Бот дар реҷаи webhook»"
