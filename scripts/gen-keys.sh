#!/bin/bash
# Generate RSA key pair for JWT signing
# Run this script once to generate the keys

CERTS_DIR="./certs"
mkdir -p "$CERTS_DIR"

echo "Generating 2048-bit RSA private key..."
openssl genrsa -out "$CERTS_DIR/private.pem" 2048

echo "Extracting public key from private key..."
openssl rsa -in "$CERTS_DIR/private.pem" -pubout -out "$CERTS_DIR/public.pem"

echo "Done! Keys saved to:"
echo "  Private: $CERTS_DIR/private.pem"
echo "  Public:  $CERTS_DIR/public.pem"
echo ""
echo "IMPORTANT: Add private.pem to .gitignore! Never commit private keys."
echo "The public.pem can be shared freely."