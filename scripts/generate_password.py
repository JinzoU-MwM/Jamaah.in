"""
Password Hash Generator for Streamlit Authenticator

Run this script to generate hashed passwords:
    python generate_password.py

Then copy the hashed password to app.py config.
"""
import streamlit_authenticator as stauth

# Passwords to hash
passwords = ['admin123', 'user123']

# Generate hashes
hashed_passwords = stauth.Hasher(passwords).generate()

print("\n=== Password Hashes ===")
for pwd, hashed in zip(passwords, hashed_passwords):
    print(f"Password: {pwd}")
    print(f"Hash: {hashed}")
    print()

print("Copy the hash values to app.py credentials config.")
