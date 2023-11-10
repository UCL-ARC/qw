"""Local keyring access for password storing and retrieval."""
import keyring

from qw.base import QwError


def get_qw_password(organisation: str, repository: str):
    """Get the QW password for the repo from local keychain."""
    return keyring.get_password("qw", f"{organisation}/{repository}")


def set_qw_password(organisation: str, repository: str, password: str):
    """Set the QW password for the repo in local keychain."""
    cleaned_password = password.strip(" ")
    if not cleaned_password:
        msg = "Access token was empty, please add again."
        raise QwError(msg)
    keyring.set_password("qw", f"{organisation}/{repository}", cleaned_password)
