#!/usr/bin/env bash
set -euo pipefail

# Generate self-signed TLS certificates for docker-compose development environment.
# Run this before `docker-compose up` if certs/ does not exist.

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/selfsigned.crt" ]; then
  echo "Generating self-signed TLS certificates..."
  cat > /tmp/openssl-greenlane.cnf << 'EOF'
[req]
distinguished_name = dn
prompt = no

[dn]
C = US
ST = Maritime
L = Lloyd
O = GreenLane Maritime
CN = localhost
EOF
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$CERT_DIR/selfsigned.key" \
    -out "$CERT_DIR/selfsigned.crt" \
    -days 365 \
    -config /tmp/openssl-greenlane.cnf
  chmod 600 "$CERT_DIR/selfsigned.key"
  echo "Certificates generated in $CERT_DIR/"
else
  echo "Certificates already exist in $CERT_DIR/. Skipping."
fi
