import re

from django.test import SimpleTestCase, override_settings

from .store import store

CODE = re.compile(r"^[A-Za-z0-9]{6}$")


@override_settings(MINILIEN_ADMIN_TOKEN="jeton-de-test")
class LienApiTest(SimpleTestCase):
    def setUp(self):
        store.vider()

    def creer_lien(self, url):
        reponse = self.client.post("/api/liens", {"url": url}, content_type="application/json")
        self.assertEqual(reponse.status_code, 201)
        return reponse.json()["code"]

    def test_cree_un_lien_court_pour_une_url_valide(self):
        reponse = self.client.post("/api/liens", {"url": "https://openclassrooms.com/fr/"},
                                   content_type="application/json")

        self.assertEqual(reponse.status_code, 201)
        corps = reponse.json()
        self.assertRegex(corps["code"], CODE)
        self.assertEqual(reponse["Location"], f"/api/liens/{corps['code']}")
        self.assertEqual(corps["url"], "https://openclassrooms.com/fr/")
        self.assertEqual(corps["lienCourt"], f"http://localhost:8080/r/{corps['code']}")
        self.assertEqual(corps["visites"], 0)

    def test_refuse_une_url_invalide(self):
        reponse = self.client.post("/api/liens", {"url": "ftp://exemple.fr"}, content_type="application/json")

        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(reponse.json()["code"], "URL_INVALIDE")

    def test_redirige_et_compte_les_visites(self):
        code = self.creer_lien("https://exemple.fr/page")

        reponse = self.client.get(f"/r/{code}")
        self.client.get(f"/r/{code}")

        self.assertEqual(reponse.status_code, 302)
        self.assertEqual(reponse["Location"], "https://exemple.fr/page")
        self.assertEqual(self.client.get(f"/api/liens/{code}").json()["visites"], 2)

    def test_liste_les_liens(self):
        self.creer_lien("https://exemple.fr/1")
        self.creer_lien("https://exemple.fr/2")

        reponse = self.client.get("/api/liens")

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.json()), 2)

    def test_renvoie_404_pour_un_code_inconnu(self):
        reponse = self.client.get("/r/XXXXXX")

        self.assertEqual(reponse.status_code, 404)
        self.assertEqual(reponse.json()["code"], "LIEN_INTROUVABLE")

    def test_refuse_la_suppression_sans_jeton_valide(self):
        code = self.creer_lien("https://exemple.fr")

        self.assertEqual(self.client.delete(f"/api/liens/{code}").status_code, 401)
        self.assertEqual(self.client.delete(f"/api/liens/{code}", headers={"X-Admin-Token": "mauvais"}).status_code, 401)

    def test_supprime_un_lien_avec_le_bon_jeton(self):
        code = self.creer_lien("https://exemple.fr")

        reponse = self.client.delete(f"/api/liens/{code}", headers={"X-Admin-Token": "jeton-de-test"})

        self.assertEqual(reponse.status_code, 204)
        self.assertEqual(self.client.get(f"/api/liens/{code}").status_code, 404)
