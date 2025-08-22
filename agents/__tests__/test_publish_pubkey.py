import os
from pathlib import Path
from agents.publish_pubkey import derive_public_pem


def test_derive_public_pem_returns_public_key(tmp_path):
    # create a temporary EC private key PEM file
    key_path = tmp_path / "prov.pem"
    # use openssl to generate a key (system must have openssl available)
    import subprocess
    subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", str(key_path)])
    pub = derive_public_pem(key_path)
    assert "BEGIN PUBLIC KEY" in pub
    assert "BEGIN PRIVATE KEY" not in pub
