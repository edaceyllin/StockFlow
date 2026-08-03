"""
license.py
===============================================================================
StockFlow ERP Lite - ISTEMCI TARAFI LISANS DOGRULAMA MODULU
===============================================================================
BU DOSYA UYGULAMAYLA BIRLIKTE DAGITILIR (musteri bilgisayarina kurulur).

Icerdigi SADECE genel anahtardir (public key). Ozel anahtar (private key) bu
dosyada YOKTUR ve musteriye ASLA verilmez; o sadece generator.py ile birlikte
gelistiricide/saticida kalir.

Sorumluluklari:
  1. Bilgisayara ozgu, deterministik bir "Machine ID" uretmek.
  2. Kullanicinin sectigi license.dat dosyasini okuyup RSA-PSS imzasini
     genel anahtar ile dogrulamak.
  3. Lisansin bu makineye, bu urune ait olup olmadigini ve suresinin
     dolup dolmadigini kontrol etmek.
  4. Dogrulanmis lisansi uygulamanin yerel veri klasorune kaydetmek; boylece
     kullanici her acilista dosya secmek zorunda kalmaz.

Guvenlik notu: Bu modulun ic mantigini degistirip yamalamak teknik olarak
mumkundur - hicbir istemci tarafi koruma yuzde yuz kirilamaz degildir.
Tasarimin amaci, lisans DOSYASININ sahtesini private key olmadan uretmeyi
hesaplama olarak imkansiz hale getirmektir.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

PRODUCT_NAME = "StockFlow ERP Lite"

# generator.py "init-keys" komutuyla uretilen ciftin GENEL anahtarini buraya
# yapistirin. production'a gecmeden once KENDI anahtarinizi uretip degistirin.
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAqbh0BEFTEzXA6/56DBAn
hOC2N4ixO7o2xKGN53poqv5onORBKj5zEQumqAZM/ZwOzXw1UaAm+mrzoHf8StME
aNmdRwhGfoTiSbZ3DlmqZokLF/tGTp0G5iDg/jxQ8//Dd4vNe8EprftDPhWeVd5u
5o2XxrvMFjR0Wyz7ahC/mUGG5gH2RenCK2K+cBJjqlLmILaofqEnR1yiiUyXbXTT
13HSAI1dyOcSmLd3Ooizrw+TkE/Nx5hoqR2Zzyn0F1i7L1bKK9mVwOVEPylBe6AS
1OD6ZjcZ/2cTM5uT+puPiw1awvCgALwZAgGzdPdtUM/Epb1gh4q6qCUd2h3nAcEf
ggDR2OhThRHCCYC+yCGvwDOKKwHWvw9Q1iMUlJK7k64jlp5fRBaJrtaOlLtvbtu6
ABEV54MwIPpjFt4OSrLh39eHv9rGo/RM0STtQ/NKs1hfwEvh5wQxIk2Gff6uxDeF
aIbqLYhHMxblDcSOrGuhS/QWHDaB+hxjaEIwnqe+60sH+h24ze00+rcRH3a9agf1
Rp2rNFbkwts9yML2juTsc8vALptcSbjtxuT/9Ww6foFIHcxIoCUEwszRgwVGYa5u
GTAnthvhf1QQ1XUC+a6EdKf7NgwVlLJ71bjw+WNUgAhakcaiGn0f7I4FWddeli0C
bVJk/DgbN2XEzG63jW8vTPMCAwEAAQ==
-----END PUBLIC KEY-----"""


def _load_public_key():
    return serialization.load_pem_public_key(PUBLIC_KEY_PEM)


def _app_data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    path = base / "StockFlowERPLite"
    path.mkdir(parents=True, exist_ok=True)
    return path


LICENSE_STORE_PATH = _app_data_dir() / "license.dat"
_MACHINE_ID_CACHE_PATH = _app_data_dir() / ".machine_id_cache"


def _raw_hardware_fingerprint() -> str:
    system = platform.system()
    parts: list[str] = []
    try:
        if system == "Windows":
            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "UUID"],
                stderr=subprocess.DEVNULL, timeout=5,
            ).decode(errors="ignore")
            lines = [ln.strip() for ln in out.splitlines() if ln.strip() and "UUID" not in ln.upper()]
            if lines:
                parts.append(lines[0])
        elif system == "Darwin":
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL, timeout=5,
            ).decode(errors="ignore")
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    parts.append(line.split('"')[-2])
                    break
        elif system == "Linux":
            for candidate in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
                p = Path(candidate)
                if p.exists():
                    parts.append(p.read_text().strip())
                    break
    except Exception:
        pass

    parts.append(str(uuid.getnode()))
    if not parts:
        parts.append(uuid.uuid4().hex)
    return "|".join(parts)


def get_machine_id() -> str:
    if _MACHINE_ID_CACHE_PATH.exists():
        cached = _MACHINE_ID_CACHE_PATH.read_text(encoding="utf-8").strip()
        if cached:
            return cached

    raw = _raw_hardware_fingerprint()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()[:32]
    machine_id = "-".join(digest[i:i + 4] for i in range(0, 32, 4))

    try:
        _MACHINE_ID_CACHE_PATH.write_text(machine_id, encoding="utf-8")
    except OSError:
        pass

    return machine_id


class LicenseError(Exception):
    """Lisans okunamadi / imza gecersiz / makineye ya da urune uymuyor / suresi dolmus."""


@dataclass
class LicenseInfo:
    machine_id: str
    product: str
    version: str
    created: str
    expires: Optional[str] = None
    customer: Optional[str] = None

    @property
    def expires_dt(self) -> Optional[datetime]:
        if not self.expires:
            return None
        return datetime.fromisoformat(self.expires)

    @property
    def is_perpetual(self) -> bool:
        return self.expires is None


def _canonical_payload_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _read_license_file(path: Path) -> "tuple[dict, bytes]":
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LicenseError(f"Lisans dosyasi okunamadi veya bozuk: {exc}") from exc

    if not isinstance(raw, dict) or "payload" not in raw or "signature" not in raw:
        raise LicenseError("Lisans dosyasi formati gecersiz.")

    try:
        signature = base64.b64decode(raw["signature"], validate=True)
    except Exception as exc:
        raise LicenseError("Imza verisi cozumlenemedi.") from exc

    return raw["payload"], signature


def _verify_signature(payload: dict, signature: bytes) -> None:
    public_key = _load_public_key()
    message = _canonical_payload_bytes(payload)
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except InvalidSignature as exc:
        raise LicenseError("Lisans imzasi gecersiz (sahte veya bozulmus dosya).") from exc


def parse_and_verify(path) -> LicenseInfo:
    payload, signature = _read_license_file(Path(path))
    _verify_signature(payload, signature)

    required = {"machine_id", "product", "version", "created"}
    if not required.issubset(payload):
        raise LicenseError("Lisans icerigi eksik alanlar barindiriyor.")

    return LicenseInfo(
        machine_id=payload["machine_id"],
        product=payload["product"],
        version=payload["version"],
        created=payload["created"],
        expires=payload.get("expires"),
        customer=payload.get("customer"),
    )


def _validate_against_machine(info: LicenseInfo) -> None:
    if info.product != PRODUCT_NAME:
        raise LicenseError("Bu lisans dosyasi baska bir urune ait.")

    if info.machine_id != get_machine_id():
        raise LicenseError(
            "Bu lisans baska bir bilgisayar icin olusturulmus; bu makinede kullanilamaz."
        )

    expires_dt = info.expires_dt
    if expires_dt is not None:
        now = datetime.now(expires_dt.tzinfo) if expires_dt.tzinfo else datetime.now()
        if now > expires_dt:
            raise LicenseError(f"Lisans suresi dolmus ({info.expires}).")


def install_license(source_path) -> LicenseInfo:
    source_path = Path(source_path)
    info = parse_and_verify(source_path)
    _validate_against_machine(info)

    LICENSE_STORE_PATH.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return info


def is_license_valid() -> bool:
    if not LICENSE_STORE_PATH.exists():
        return False
    try:
        info = parse_and_verify(LICENSE_STORE_PATH)
        _validate_against_machine(info)
        return True
    except LicenseError:
        return False


def current_license_info() -> Optional[LicenseInfo]:
    if not LICENSE_STORE_PATH.exists():
        return None
    try:
        return parse_and_verify(LICENSE_STORE_PATH)
    except LicenseError:
        return None
