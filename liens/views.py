import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_GET, require_http_methods

from .store import LienIntrouvable, UrlInvalide, store


def erreur(code, message, status):
    return JsonResponse({"code": code, "message": message}, status=status)


def en_json(lien):
    return {
        "code": lien.code,
        "url": lien.url,
        "lienCourt": f"{settings.MINILIEN_BASE_URL}/r/{lien.code}",
        "creeLe": lien.cree_le.isoformat().replace("+00:00", "Z"),
        "visites": lien.visites,
    }


@require_http_methods(["GET", "POST"])
def liens(request):
    if request.method == "GET":
        return JsonResponse([en_json(lien) for lien in store.lister()], safe=False)

    try:
        corps = json.loads(request.body or b"null")
    except json.JSONDecodeError:
        corps = None
    if not isinstance(corps, dict):
        return erreur("REQUETE_INVALIDE", 'Le corps de la requête doit être un JSON de la forme {"url": "..."}.', 400)
    try:
        lien = store.creer(corps.get("url"))
    except UrlInvalide as e:
        return erreur("URL_INVALIDE", str(e), 400)
    reponse = JsonResponse(en_json(lien), status=201)
    reponse["Location"] = f"/api/liens/{lien.code}"
    return reponse


@require_http_methods(["GET", "DELETE"])
def lien(request, code):
    try:
        if request.method == "GET":
            return JsonResponse(en_json(store.trouver(code)))

        if request.headers.get("X-Admin-Token") != settings.MINILIEN_ADMIN_TOKEN:
            return erreur("ACCES_REFUSE", "Jeton d'administration absent ou incorrect (en-tête X-Admin-Token).", 401)
        store.supprimer(code)
        return HttpResponse(status=204)
    except LienIntrouvable as e:
        return erreur("LIEN_INTROUVABLE", str(e), 404)


@require_GET
def rediriger(request, code):
    try:
        lien = store.visiter(code)
    except LienIntrouvable as e:
        return erreur("LIEN_INTROUVABLE", str(e), 404)
    return HttpResponseRedirect(lien.url)
