"""Encryption for member exports sent to Student Life."""

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .config import EXPORT_KEY


def encrypt_export(data: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    encryptor = Cipher(algorithms.AES(EXPORT_KEY), modes.ECB()).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def decrypt_export(blob: bytes) -> bytes:
    decryptor = Cipher(algorithms.AES(EXPORT_KEY), modes.ECB()).decryptor()
    padded = decryptor.update(blob) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()
