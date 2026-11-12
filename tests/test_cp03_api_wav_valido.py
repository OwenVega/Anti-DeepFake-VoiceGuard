import os
import glob
import unittest
import requests

API_URL = "http://localhost:5000/api/analisis"
CARPETA_REALES = os.path.join("tests", "dataset_test", "reales", "*.wav")

class TestCP03ApiWavValido(unittest.TestCase):
    def test_cp03_envio_wav_valido_retorna_200_y_json(self):
        archivos = glob.glob(CARPETA_REALES)
        self.assertGreater(len(archivos), 0, "No se encontró ningún archivo .wav de prueba.")

        ruta_wav = archivos[0]
        nombre = os.path.basename(ruta_wav)
        tamano_bytes = os.path.getsize(ruta_wav)

        self.assertLessEqual(tamano_bytes, 1_048_576, f"El archivo {nombre} supera el límite de 1 MB")

        with open(ruta_wav, "rb") as f:
            resp = requests.post(API_URL, files={"file": (nombre, f, "audio/wav")}, timeout=15)

        self.assertEqual(resp.status_code, 200, f"Se esperaba HTTP 200, se recibió {resp.status_code}")

        data = resp.json()
        self.assertIn("resultado", data)
        self.assertIn(data["resultado"], ["real", "sintetica"])
        self.assertIn("confianza", data)
        self.assertTrue(0.0 <= float(data["confianza"]) <= 1.0)

        print(f"\n[CP-03 APROBADO] Archivo: {nombre} ({tamano_bytes} bytes) -> HTTP 200 | JSON: {data}")

if __name__ == "__main__":
    unittest.main(verbosity=2)