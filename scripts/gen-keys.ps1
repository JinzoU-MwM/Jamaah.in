#!/usr/bin/env pwsl
# Generate RSA key pair for JWT signing (PowerShell version)
# Run this script once to generate the keys

$certsDir = "./certs"
if (-not (Test-Path -LiteralPath $certsDir)) {
    New-Item -ItemType Directory -Path $certsDir | Out-Null
}

Write-Host "Generating 2048-bit RSA private key..."
openssl genrsa -out "$certsDir/private.pem" 2048

Write-Host "Extracting public key from private key..."
openssl rsa -in "$certsDir/private.pem" -pubout -out "$certsDir/public.pem"

Write-Host "Done! Keys saved to:"
Write-Host "  Private: $certsDir/private.pem"
Write-Host "  Public:  $certsDir/public.pem"
Write-Host ""
Write-Host "IMPORTANT: Add private.pem to .gitignore! Never commit private keys."
Write-Host "The public.pem can be shared freely."