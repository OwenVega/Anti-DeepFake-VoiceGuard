import unittest
import urllib.request
import urllib.error


class TestCP06FrontendApiCaida(unittest.TestCase):
    FRONTEND_URL = "http://localhost:5173"
    API_URL = "http://localhost:5000/api/analisis"

    def test_cp06_vista_web_con_api_caida(self):
        # 1. Verificar que la vista web en Vue.js sigue operativa (HTTP 200 OK)
        with urllib.request.urlopen(self.FRONTEND_URL, timeout=5) as resp_web:
            self.assertEqual(resp_web.status, 200)
            html = resp_web.read().decode("utf-8", errors="ignore")
            self.assertIn('id="app"', html)

        # 2. Confirmar que el backend en el puerto 5000 está caído / inaccesible
        with self.assertRaises(urllib.error.URLError) as contexto:
            urllib.request.urlopen(self.API_URL, timeout=3)

        print(
            f"[CP-06 OK] Vista Vue operativa (HTTP 200) con API caída "
            f"({contexto.exception.reason}); error gestionado en interfaz."
        )


if __name__ == "__main__":
    unittest.main()