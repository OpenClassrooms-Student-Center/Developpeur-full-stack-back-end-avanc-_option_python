"""Stockage en mémoire des liens courts (les données sont perdues au redémarrage)."""
import secrets
import string
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

ALPHABET = string.ascii_letters + string.digits
LONGUEUR_CODE = 6
LONGUEUR_MAX_URL = 2048


class UrlInvalide(Exception):
    pass


class LienIntrouvable(Exception):
    def __init__(self, code):
        super().__init__(f"Aucun lien ne correspond au code « {code} ».")


@dataclass
class Lien:
    code: str
    url: str
    cree_le: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    visites: int = 0


class LienStore:
    def __init__(self):
        self._liens = {}
        self._verrou = threading.Lock()

    def creer(self, url):
        url = verifier_url(url)
        with self._verrou:
            while True:
                code = "".join(secrets.choice(ALPHABET) for _ in range(LONGUEUR_CODE))
                if code not in self._liens:
                    lien = Lien(code=code, url=url)
                    self._liens[code] = lien
                    return lien

    def lister(self):
        return sorted(self._liens.values(), key=lambda lien: lien.cree_le, reverse=True)

    def trouver(self, code):
        try:
            return self._liens[code]
        except KeyError:
            raise LienIntrouvable(code) from None

    def visiter(self, code):
        with self._verrou:
            lien = self.trouver(code)
            lien.visites += 1
            return lien

    def supprimer(self, code):
        with self._verrou:
            if self._liens.pop(code, None) is None:
                raise LienIntrouvable(code)

    def vider(self):
        with self._verrou:
            self._liens.clear()


def verifier_url(url):
    if not isinstance(url, str) or not url.strip():
        raise UrlInvalide("Le champ « url » est obligatoire.")
    url = url.strip()
    if len(url) > LONGUEUR_MAX_URL:
        raise UrlInvalide(f"L'URL dépasse {LONGUEUR_MAX_URL} caractères.")
    morceaux = urlparse(url)
    if morceaux.scheme not in ("http", "https") or not morceaux.netloc:
        raise UrlInvalide("L'URL doit commencer par http:// ou https:// et contenir un domaine.")
    return url


store = LienStore()
