"""
One-time setup: generate RSA key pair for headless Snowflake auth.

Run:
    python setup/generate_snowflake_key.py

Then follow the 3 steps printed at the end.
"""

import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SETUP_DIR       = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_PATH = os.path.join(SETUP_DIR, 'snowflake_private.p8')
PUBLIC_KEY_PATH  = os.path.join(SETUP_DIR, 'snowflake_public.pub')

USER    = 'rohit.singh13@cars24.com'


def main():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(PRIVATE_KEY_PATH, 'wb') as f:
        f.write(private_pem)
    with open(PUBLIC_KEY_PATH, 'wb') as f:
        f.write(public_pem)

    pub_stripped = ''.join(
        line + '\n' for line in public_pem.decode().splitlines()
        if not line.startswith('-----')
    ).strip()

    print('=' * 60)
    print('Keys generated successfully!')
    print(f'  Private key: {PRIVATE_KEY_PATH}')
    print(f'  Public key:  {PUBLIC_KEY_PATH}')
    print('=' * 60)
    print()
    print('STEP 1 -- Register public key in Snowflake.')
    print('Open a Snowflake Worksheet and run:')
    print()
    print(f'  ALTER USER "{USER}" SET RSA_PUBLIC_KEY=\'{pub_stripped}\';')
    print()
    print('STEP 2 — Add private key to GitHub Secrets.')
    print('Go to: GitHub repo -> Settings -> Secrets -> Actions')
    print('Create secret name: SNOWFLAKE_PRIVATE_KEY')
    print('Paste the ENTIRE content below (including the -----BEGIN----- lines):')
    print()
    print(private_pem.decode())
    print()
    print('STEP 3 -- Done. The private key file stays local only (already in .gitignore).')
    print('         Never commit setup/snowflake_private.p8')


if __name__ == '__main__':
    main()
