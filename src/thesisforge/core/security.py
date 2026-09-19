"""Security hardening utilities: SSRF defense guard and Local Key Vault."""

import asyncio
import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from thesisforge.exceptions import KeyVaultError, SSRFBlockedError

# Subnets explicitly blocked to eliminate Server-Side Request Forgery (SSRF)
BLOCKED_SUBNETS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local & cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
    ipaddress.ip_network("::1/128"),  # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 Unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 Link-local
]


def _check_ip_safety(ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address]) -> None:
    """Verify that none of the resolved IPs fall into blocked or private subnets."""
    for ip in ips:
        if any(ip in subnet for subnet in BLOCKED_SUBNETS):
            raise SSRFBlockedError(
                f"Acceso denegado: La dirección IP {ip} pertenece a una red privada o reservada (SSRF Guard)."
            )


def assert_safe_academic_url(target_url: str) -> str:
    """Validate that an outbound academic literature URL is safe and not targeting internal networks.

    Args:
        target_url: The URL to validate.

    Returns:
        The validated URL string.

    Raises:
        SSRFBlockedError: If URL schema is invalid, unresolvable, or maps to private/internal IPs.
    """
    if not isinstance(target_url, str) or not target_url.strip():
        raise SSRFBlockedError("URL vacía o no válida.")

    parsed = urlparse(target_url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(
            f"Esquema inválido '{parsed.scheme}'. Solo se permiten peticiones HTTP o HTTPS."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError("La URL no contiene un nombre de host válido.")

    try:
        direct_ip = ipaddress.ip_address(hostname)
        ips_to_check = [direct_ip]
    except ValueError:
        try:
            addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
            ips_to_check = [ipaddress.ip_address(sockaddr[0]) for *_, sockaddr in addr_info]
        except (socket.gaierror, OSError) as err:
            raise SSRFBlockedError(f"No fue posible resolver el host '{hostname}': {err}") from err

    if not ips_to_check:
        raise SSRFBlockedError(f"Host '{hostname}' no resolvió ninguna dirección IP válida.")

    _check_ip_safety(ips_to_check)
    return target_url.strip()


async def assert_safe_academic_url_async(target_url: str) -> str:
    """Validate that an outbound URL is safe without blocking the asyncio event loop during DNS resolution.

    Args:
        target_url: The URL to validate.

    Returns:
        The validated URL string.

    Raises:
        SSRFBlockedError: If URL schema is invalid, unresolvable, or maps to private/internal IPs.
    """
    if not isinstance(target_url, str) or not target_url.strip():
        raise SSRFBlockedError("URL vacía o no válida.")

    parsed = urlparse(target_url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(
            f"Esquema inválido '{parsed.scheme}'. Solo se permiten peticiones HTTP o HTTPS."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError("La URL no contiene un nombre de host válido.")

    try:
        direct_ip = ipaddress.ip_address(hostname)
        ips_to_check = [direct_ip]
    except ValueError:
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.run_in_executor(
                None, socket.getaddrinfo, hostname, None, socket.IPPROTO_TCP
            )
            ips_to_check = [ipaddress.ip_address(sockaddr[0]) for *_, sockaddr in addr_info]
        except (socket.gaierror, OSError) as err:
            raise SSRFBlockedError(f"No fue posible resolver el host '{hostname}': {err}") from err

    if not ips_to_check:
        raise SSRFBlockedError(f"Host '{hostname}' no resolvió ninguna dirección IP válida.")

    _check_ip_safety(ips_to_check)
    return target_url.strip()


def resolve_or_create_master_key(
    master_key: bytes | str | None = None,
    key_file_path: Path | str | None = None,
) -> bytes:
    """Resolve master key from parameter, disk file, or generate and persist locally."""
    if master_key is not None:
        return master_key.encode("utf-8") if isinstance(master_key, str) else master_key

    target_path = (
        Path(key_file_path)
        if key_file_path is not None
        else Path.home() / ".thesisforge" / "master.key"
    )

    if target_path.is_file():
        try:
            content = target_path.read_bytes().strip()
            if content:
                return content
        except OSError:
            pass

    new_key = Fernet.generate_key()
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(new_key)
        # Attempt secure permission on POSIX systems
        if os.name != "nt":
            target_path.chmod(0o600)
    except OSError:
        # Fallback to in-memory key if disk write is not permitted
        pass

    return new_key


class LocalKeyVault:
    """Symmetric encryption vault using Fernet (AES-128-CBC + HMAC-SHA256) for local API keys."""

    def __init__(
        self,
        master_key: bytes | str | None = None,
        key_file_path: Path | str | None = None,
        persist: bool = True,
    ) -> None:
        """Initialize vault with a master key or persist/generate one on disk."""
        if persist and master_key is None and key_file_path != ":memory:":
            self._key = resolve_or_create_master_key(master_key, key_file_path)
        elif master_key is None:
            self._key = Fernet.generate_key()
        elif isinstance(master_key, str):
            self._key = master_key.encode("utf-8")
        else:
            self._key = master_key

        try:
            self._cipher = Fernet(self._key)
        except Exception as err:
            raise KeyVaultError(f"Clave maestra de cifrado inválida: {err}") from err

    @property
    def key_bytes(self) -> bytes:
        """Return the raw key bytes."""
        return self._key

    @property
    def key_str(self) -> str:
        """Return the key as a base64-encoded string."""
        return self._key.decode("utf-8")

    @classmethod
    def generate_key(cls) -> str:
        """Generate a new Fernet key string."""
        return Fernet.generate_key().decode("utf-8")

    def encrypt(self, secret: str) -> str:
        """Encrypt a plain text secret into a safe token string."""
        if not secret:
            return ""
        try:
            return self._cipher.encrypt(secret.encode("utf-8")).decode("utf-8")
        except Exception as err:
            raise KeyVaultError(f"Fallo en el cifrado del secreto: {err}") from err

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt an encrypted token back into plain text."""
        if not encrypted_token:
            return ""
        try:
            return self._cipher.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
        except InvalidToken as err:
            raise KeyVaultError("Token cifrado inválido o clave maestra incorrecta.") from err
        except Exception as err:
            raise KeyVaultError(f"Fallo en el descifrado del secreto: {err}") from err
