#!/bin/bash

# Script to generate mTLS test certificates with proper extensions
# This creates a CA, server certificate, and client certificate for testing

set -e

CERTS_DIR="certs"
mkdir -p "$CERTS_DIR"

echo "Generating mTLS test certificates..."

# 1. Generate CA private key and certificate with proper extensions
echo "1. Generating CA certificate..."
openssl genrsa -out "$CERTS_DIR/ca-key.pem" 4096

# Create CA config for extensions
cat > "$CERTS_DIR/ca.cnf" <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca

[req_distinguished_name]

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,digitalSignature,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

openssl req -new -x509 -days 365 -key "$CERTS_DIR/ca-key.pem" \
    -out "$CERTS_DIR/ca-cert.pem" \
    -config "$CERTS_DIR/ca.cnf" \
    -subj "/C=US/ST=Test/L=Test/O=TestOrg/CN=Test CA"

# 2. Generate server private key and CSR
echo "2. Generating server certificate..."
openssl genrsa -out "$CERTS_DIR/server-key.pem" 4096
openssl req -new -key "$CERTS_DIR/server-key.pem" \
    -out "$CERTS_DIR/server.csr" \
    -subj "/C=US/ST=Test/L=Test/O=TestOrg/CN=localhost"

# Create server config for extensions
cat > "$CERTS_DIR/server.cnf" <<EOF
[v3_server]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:localhost,DNS:host.docker.internal,IP:127.0.0.1
EOF

# 3. Sign server certificate with CA
openssl x509 -req -days 365 -in "$CERTS_DIR/server.csr" \
    -CA "$CERTS_DIR/ca-cert.pem" -CAkey "$CERTS_DIR/ca-key.pem" \
    -CAcreateserial -out "$CERTS_DIR/server-cert.pem" \
    -extfile "$CERTS_DIR/server.cnf" -extensions v3_server

# 4. Generate client private key and CSR
echo "3. Generating client certificate..."
openssl genrsa -out "$CERTS_DIR/client-key.pem" 4096
openssl req -new -key "$CERTS_DIR/client-key.pem" \
    -out "$CERTS_DIR/client.csr" \
    -subj "/C=US/ST=Test/L=Test/O=TestOrg/CN=Test Client"

# Create client config for extensions
cat > "$CERTS_DIR/client.cnf" <<EOF
[v3_client]
basicConstraints = CA:FALSE
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
EOF

# 5. Sign client certificate with CA
openssl x509 -req -days 365 -in "$CERTS_DIR/client.csr" \
    -CA "$CERTS_DIR/ca-cert.pem" -CAkey "$CERTS_DIR/ca-key.pem" \
    -CAcreateserial -out "$CERTS_DIR/client-cert.pem" \
    -extfile "$CERTS_DIR/client.cnf" -extensions v3_client

# Clean up temporary files
rm "$CERTS_DIR/server.csr" "$CERTS_DIR/client.csr"
rm "$CERTS_DIR/ca.cnf" "$CERTS_DIR/server.cnf" "$CERTS_DIR/client.cnf"

echo ""
echo "✓ Certificate generation complete!"
echo ""
echo "Generated files in "$CERTS_DIR/":"
echo "  - ca-cert.pem, ca-key.pem (Certificate Authority)"
echo "  - server-cert.pem, server-key.pem (Server certificate)"
echo "  - client-cert.pem, client-key.pem (Client certificate)"
echo ""
echo "Update your .env file with these certificate paths."
