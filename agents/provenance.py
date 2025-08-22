"""
ECDSA provenance helper using the `cryptography` library.

This module will look for an ECDSA private key PEM at the path given by
`PROVENANCE_KEY_PATH` environment variable. If not found, it will generate a
new P-256 keypair and write the private key to `provenance_key.pem` in the
current working directory (development convenience only).

Provides:
- sign_hex(hexstr) -> hex signature (DER-encoded hex)
- verify_hex(hexstr, sig_hex) -> bool

CLI:
  python -m agents.provenance sign <hexhash>
  python -m agents.provenance verify <hexhash> <sig_hex>

Note: For production, manage keys securely and do not write private keys to
repo or disk in plain PEM without encryption.
"""
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.hazmat.primitives import serialization


KEY_PATH = os.environ.get("PROVENANCE_KEY_PATH", "provenance_key.pem")


def _ensure_key() -> ec.EllipticCurvePrivateKey:
    p = Path(KEY_PATH)
    if p.exists():
        data = p.read_bytes()
        return serialization.load_pem_private_key(data, password=None)
    # generate and persist (development convenience)
    priv = ec.generate_private_key(ec.SECP256R1())
    pem = priv.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption())
    p.write_bytes(pem)
    return priv


def sign_hex(hexstr: str) -> str:
    """Sign the raw bytes represented by hexstr. Returns hex-encoded DER signature."""
    priv = _ensure_key()
    data = bytes.fromhex(hexstr)
    sig = priv.sign(data, ec.ECDSA(hashes.SHA256()))
    # return DER signature as hex
    return sig.hex()


def verify_hex(hexstr: str, sig_hex: str) -> bool:
    p = Path(KEY_PATH)
    if not p.exists():
        return False
    data = bytes.fromhex(hexstr)
    sig = bytes.fromhex(sig_hex)
    # load public key from private key file
    priv = serialization.load_pem_private_key(p.read_bytes(), password=None)
    pub = priv.public_key()
    try:
        pub.verify(sig, data, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: sign <hexhash> | verify <hexhash> <sig_hex>")
        return
    cmd = sys.argv[1]
    if cmd == "sign":
        print(sign_hex(sys.argv[2]))
    elif cmd == "verify":
        ok = verify_hex(sys.argv[2], sys.argv[3])
        print("OK" if ok else "FAIL")
    else:
        print("Unknown command")


if __name__ == "__main__":
    main()
