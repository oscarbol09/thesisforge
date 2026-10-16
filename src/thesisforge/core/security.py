"""Security hardening utilities: SSRF defense guard and Local Key Vault."""

import asyncio
import ipaddress
import os
import socket
import time
from collections.abc import Container
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from thesisforge.core.logging import get_logger
from thesisforge.exceptions import KeyVaultError, SSRFBlockedError

logger = get_logger(__name__)


# Standard academic literature API hosts permitted for outbound fetching (TF-SEC-008)
DEFAULT_ALLOWED_ACADEMIC_HOSTS: frozenset[str] = frozenset(
    {
        "api.semanticscholar.org",
        "export.arxiv.org",
        "api.crossref.org",
        "api.openalex.org",
        "doi.org",
        "dx.doi.org",
    }
)

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
    """Verify that none of the resolved IPs fall into blocked, private, loopback, or cloud metadata subnets."""
    for ip in ips:
        target_ip = (
            ip.ipv4_mapped
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None
            else ip
        )
        if (
            target_ip.is_private
            or target_ip.is_loopback
            or target_ip.is_link_local
            or target_ip.is_reserved
            or target_ip.is_multicast
            or any(target_ip in subnet for subnet in BLOCKED_SUBNETS)
        ):
            raise SSRFBlockedError(
                f"Acceso denegado: La dirección IP {ip} pertenece a una red privada o reservada (SSRF Guard)."
            )


def assert_safe_academic_url(target_url: str, allowed_hosts: Container[str] | None = None) -> str:
    """Validate that an outbound academic literature URL is safe and not targeting internal networks.

    Args:
        target_url: The URL to validate.
        allowed_hosts: Optional container of permitted hostnames (TF-SEC-008).

    Returns:
        The validated URL string.

    Raises:
        SSRFBlockedError: If URL schema is invalid, unresolvable, unallowed, or maps to private IPs.
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

    if allowed_hosts is not None and hostname.lower() not in allowed_hosts:
        raise SSRFBlockedError(
            f"El host '{hostname}' no está en la lista de hosts académicos permitidos (SSRF Guard)."
        )

    try:
        direct_ip = ipaddress.ip_address(hostname)
        ips_to_check = [direct_ip]
    except ValueError:
        try:
            addr_info = socket.getaddrinfo(hostname, 0, socket.AF_UNSPEC, socket.SOCK_STREAM)
            ips_to_check = [ipaddress.ip_address(sockaddr[0]) for *_, sockaddr in addr_info]
        except (socket.gaierror, OSError) as err:
            raise SSRFBlockedError(f"No fue posible resolver el host '{hostname}': {err}") from err

    if not ips_to_check:
        raise SSRFBlockedError(f"Host '{hostname}' no resolvió ninguna dirección IP válida.")

    _check_ip_safety(ips_to_check)
    return target_url.strip()


async def assert_safe_academic_url_async(
    target_url: str, allowed_hosts: Container[str] | None = None
) -> str:
    """Validate that an outbound URL is safe without blocking the asyncio event loop during DNS resolution.

    Args:
        target_url: The URL to validate.
        allowed_hosts: Optional container of permitted hostnames (TF-SEC-008).

    Returns:
        The validated URL string.

    Raises:
        SSRFBlockedError: If URL schema is invalid, unresolvable, unallowed, or maps to private IPs.
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

    if allowed_hosts is not None and hostname.lower() not in allowed_hosts:
        raise SSRFBlockedError(
            f"El host '{hostname}' no está en la lista de hosts académicos permitidos (SSRF Guard)."
        )

    try:
        direct_ip = ipaddress.ip_address(hostname)
        ips_to_check = [direct_ip]
    except ValueError:
        loop = asyncio.get_running_loop()
        try:
            addr_info = await loop.run_in_executor(
                None, socket.getaddrinfo, hostname, 0, socket.AF_UNSPEC, socket.SOCK_STREAM
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
    if isinstance(master_key, str):
        master_key_str = master_key.strip()
        if master_key_str:
            return master_key_str.encode("utf-8")
        master_key = None
    elif isinstance(master_key, bytes):
        master_key_bytes = master_key.strip()
        if master_key_bytes:
            return master_key_bytes
        master_key = None

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
            logger.warning(
                "Master key file at '%s' is empty; generating a new key.",
                target_path,
            )
        except OSError as err:
            logger.error(
                "Failed to read existing master key file at '%s'. Aborting to avoid accidental overwrite.",
                target_path,
                extra={"error": str(err)},
            )
            raise KeyVaultError(
                f"No fue posible leer la clave maestra existente en '{target_path}'. "
                f"Se detiene la ejecución para evitar la sobreescritura accidental de secretos. Causa: {err}"
            ) from err

    new_key = Fernet.generate_key()
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(target_path), flags, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(new_key)
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            # Another process created the key concurrently; retry to ensure write is flushed
            for _ in range(10):
                content = target_path.read_bytes().strip()
                if content:
                    return content
                time.sleep(0.05)
            content = target_path.read_bytes().strip()
            if content:
                return content
            return new_key
    except OSError as err:
        # Hard failure: a silent in-memory fallback would cause all encrypted secrets
        # to become permanently unrecoverable after a process restart.
        raise KeyVaultError(
            f"No fue posible persistir la clave maestra en '{target_path}'. "
            "El arranque de ThesisForge se ha cancelado para proteger los secretos cifrados. "
            "Verifique los permisos del directorio o configure THESISFORGE_MASTER_KEY "
            f"en las variables de entorno. Causa: {err}"
        ) from err

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
        if isinstance(master_key, str):
            master_key_str = master_key.strip()
            master_key = master_key_str.encode("utf-8") if master_key_str else None
        elif isinstance(master_key, bytes):
            master_key_bytes = master_key.strip()
            master_key = master_key_bytes if master_key_bytes else None

        if persist and master_key is None and key_file_path != ":memory:":
            self._key = resolve_or_create_master_key(master_key, key_file_path)
        elif master_key is None:
            self._key = Fernet.generate_key()
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
