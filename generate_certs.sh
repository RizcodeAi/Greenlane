#!/usr/bin/env bash
set -euo pipefail

# Generate, check, and rotate self-signed TLS certificates for GreenLane Maritime.
# Usage:
#   ./generate_certs.sh generate   # Create or regenerate certificates
#   ./generate_certs.sh check      # Check days until expiry
#   ./generate_certs.sh renew      # Force regenerate certificates
#   ./generate_certs.sh auto-renew # Regenerate only if expiry < threshold

CERT_DIR="$(dirname "$0")/certs"
CERT_VALIDITY_DAYS="${CERT_VALIDITY_DAYS:-365}"
CERT_RENEWAL_THRESHOLD_DAYS="${CERT_RENEWAL_THRESHOLD_DAYS:-30}"
CERT_PATH="$CERT_DIR/server.crt"
CERT_KEY_PATH="$CERT_DIR/server.key"
CA_CERT_PATH="$CERT_DIR/ca.crt"

openssl-greenlane() {
  cat > /tmp/openssl-greenlane.cnf << 'EOF'
[req]
distinguished_name = dn
prompt = no

[dn]
C = US
ST = Maritime
L = Lloyd
O = GreenLane Maritime
CN = greenlane.local
EOF
}

generate_certs() {
  mkdir -p "$CERT_DIR"
  echo "Generating self-signed TLS certificates for CN=greenlane.local..."

  openssl-greenlane

  # Generate CA key and cert
  openssl genrsa -out "$CERT_DIR/ca.key" 2048
  openssl req -x509 -new -nodes -key "$CERT_DIR/ca.key" \
    -sha256 -days "$CERT_VALIDITY_DAYS" \
    -out "$CA_CERT_PATH" \
    -subj "/C=US/ST=Maritime/L=Lloyd/O=GreenLane Maritime/CN=greenlane.local"

  # Generate server key and CSR
  openssl genrsa -out "$CERT_KEY_PATH" 2048
  openssl req -new -key "$CERT_KEY_PATH" \
    -out "$CERT_DIR/server.csr" \
    -subj "/C=US/ST=Maritime/L=Lloyd/O=GreenLane Maritime/CN=greenlane.local"

  # Sign server cert with CA
  openssl x509 -req -in "$CERT_DIR/server.csr" \
    -CA "$CA_CERT_PATH" -CAkey "$CERT_DIR/ca.key" \
    -CAcreateserial -out "$CERT_PATH" \
    -days "$CERT_VALIDITY_DAYS" -sha256

  chmod 600 "$CERT_KEY_PATH" "$CERT_DIR/ca.key"
  chmod 644 "$CERT_PATH" "$CA_CERT_PATH"

  # Clean up CSR
  rm -f "$CERT_DIR/server.csr"

  echo "Certificates generated in $CERT_DIR/"
  echo "  - $CERT_PATH"
  echo "  - $CERT_KEY_PATH"
  echo "  - $CA_CERT_PATH"
}

check_expiry() {
  if [ ! -f "$CERT_PATH" ]; then
    echo "ERROR: Certificate not found at $CERT_PATH"
    exit 1
  fi

  local expiry_date
  expiry_date=$(openssl x509 -enddate -noout -in "$CERT_PATH" | cut -d= -f2)
  local expiry_epoch
  expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || date -jf "%b %e %T %Y %Z" "$expiry_date" +%s 2>/dev/null || echo "0")
  local now_epoch
  now_epoch=$(date +%s)

  if [ "$expiry_epoch" -eq 0 ]; then
    echo "ERROR: Could not parse certificate expiry date."
    exit 1
  fi

  local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
  echo "Certificate expires in $days_left days (on $expiry_date)"

  if [ "$days_left" -lt "$CERT_RENEWAL_THRESHOLD_DAYS" ]; then
    echo "WARNING: Certificate expiry ($days_left days) is below threshold ($CERT_RENEWAL_THRESHOLD_DAYS days)."
    exit 1
  fi
}

renew() {
  echo "Renewing certificates..."
  generate_certs
  echo "Certificate renewal complete."
}

auto_renew() {
  if [ ! -f "$CERT_PATH" ]; then
    echo "No certificate found. Generating new certificate."
    generate_certs
    exit 0
  fi

  local days_left
  days_left=$(openssl x509 -enddate -noout -in "$CERT_PATH" | cut -d= -f2)
  local expiry_epoch
  expiry_epoch=$(date -d "$days_left" +%s 2>/dev/null || true)
  local now_epoch
  now_epoch=$(date +%s)

  if [ -n "$expiry_epoch" ] && [ "$expiry_epoch" -gt 0 ]; then
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
  else
    # Fallback: use openssl to get days
    days_left=$(openssl x509 -checkend $((CERT_RENEWAL_THRESHOLD_DAYS * 86400)) -noout -in "$CERT_PATH" 2>&1 || true)
    if echo "$days_left" | grep -q "will expire"; then
      echo "Certificate will expire within $CERT_RENEWAL_THRESHOLD_DAYS days. Triggering renewal."
      renew
      exit 0
    fi
    echo "Certificate expiry is beyond threshold. No action needed."
    exit 1
  fi

  echo "Certificate has $days_left days until expiry (threshold: $CERT_RENEWAL_THRESHOLD_DAYS days)."

  if [ "$days_left" -lt "$CERT_RENEWAL_THRESHOLD_DAYS" ]; then
    echo "Expiry below threshold. Renewing..."
    renew
    exit 0
  else
    echo "Certificate is still valid. No renewal needed."
    exit 1
  fi
}

case "${1:-}" in
  generate)
    generate_certs
    ;;
  check)
    check_expiry
    ;;
  renew)
    renew
    ;;
  auto-renew)
    auto_renew
    ;;
  *)
    echo "Usage: $0 {generate|check|renew|auto-renew}"
    exit 1
    ;;
esac
