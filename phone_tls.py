"""Create a project-local CA and short-lived HTTPS certificate. No trust-store changes."""
from pathlib import Path
import datetime as dt
import ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def certificates(folder, host):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    ca_path, key_path = folder/'phone-root.cer', folder/'root-key.pem'
    def write_key(path, key):
        path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    if ca_path.exists() and key_path.exists():
        ca = x509.load_der_x509_certificate(ca_path.read_bytes())
        key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        if ca.not_valid_after_utc < now + dt.timedelta(days=2):
            raise RuntimeError('Local certificate expired. Remove the old iPhone profile and rename .phone-tls, then run again.')
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Squat Counter Local Camera')])
        ca = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now-dt.timedelta(minutes=5))
              .not_valid_after(now+dt.timedelta(days=90))
              .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
              .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()),critical=False)
              .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False), critical=True)
              .sign(key, hashes.SHA256()))
        write_key(key_path,key)
        ca_path.write_bytes(ca.public_bytes(serialization.Encoding.DER))
    leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    leaf = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)]))
            .issuer_name(ca.subject).public_key(leaf_key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-dt.timedelta(minutes=5)).not_valid_after(min(now+dt.timedelta(days=30),ca.not_valid_after_utc))
            .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()),critical=False)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(leaf_key.public_key()),critical=False)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(host))]),critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False)
            .add_extension(x509.KeyUsage(True,False,True,False,False,False,False,False,False),critical=True)
            .sign(key,hashes.SHA256()))
    write_key(folder/'server-key.pem',leaf_key)
    (folder/'server.pem').write_bytes(leaf.public_bytes(serialization.Encoding.PEM)+ca.public_bytes(serialization.Encoding.PEM))
    return ca_path, ca.fingerprint(hashes.SHA256()).hex(':')
