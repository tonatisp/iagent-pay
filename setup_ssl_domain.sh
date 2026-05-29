#!/bin/bash

# Este script instalara Certbot (Let's Encrypt) para asegurar iAgent-Pay
# Requiere que el dominio ya apunte a la IP de este servidor (A Record)

echo "=== INICIANDO INSTALACION DE SSL (HTTPS) PARA PRODUCCION ==="

if [ -z "$1" ]
then
    echo "ERROR: Debes proveer un dominio."
    echo "Uso: ./setup_ssl_domain.sh tu-dominio.com"
    exit 1
fi

DOMAIN=$1

echo "[*] Preparando el sistema..."
apt-get update
apt-get install -y software-properties-common
apt-get install -y certbot python3-certbot-nginx

echo "[*] Configurando Nginx para el dominio $DOMAIN..."
# Se reemplaza localhost con el dominio real en la configuracion de Nginx
sed -i "s/server_name localhost;/server_name $DOMAIN www.$DOMAIN;/g" /etc/nginx/sites-available/default

echo "[*] Reiniciando Nginx..."
systemctl restart nginx

echo "[*] Solicitando certificado SSL a Let's Encrypt para $DOMAIN..."
# --non-interactive y --agree-tos permiten que el proceso sea silencioso (ideal para despliegue automatizado)
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

echo "=== INSTALACION SSL COMPLETADA EXITOSAMENTE ==="
echo "Tu plataforma ahora esta corriendo segura en https://$DOMAIN"
