#!/bin/bash

set -e

echo "[+] Step 1: Using HTTP-only nginx config for Certbot challenge"
cp nginx.http.conf nginx.conf

echo "[+] Step 2: Starting containers with HTTP config"
docker-compose up -d nginx db fastapi

echo "[+] Waiting for nginx to fully boot..."
sleep 5

echo "[+] Step 3: Requesting SSL cert from Let's Encrypt..."
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  -d api.freelancelot.app \
  --email admin@freelancelot.app --agree-tos --no-eff-email

echo "[+] Step 4: Switching nginx to HTTPS config"
cp nginx.https.conf nginx.conf

echo "[+] Step 5: Restarting nginx with SSL certs"
docker-compose restart nginx

echo "[✓] SSL is now active for https://api.freelancelot.app"


