import io
import unittest
import requests

API_URL = "http://localhost:5000/api/analisis"

class TestCP04ApiArchivoInvalido(unittest.TestCase):
    def test_cp04_formato_invalido_retorna_400(self):
        archivo_falso = io.BytesIO(b"Este es un archivo de texto plano, no un audio WAV.")
        resp = requests.post(
            API_URL,
            files={"file": ("documento_invalido.txt", archivo_falso, "text/plain")},
            timeout=15
        )
        self.assertEqual(resp.status_code, 400, f"Se esperaba HTTP 400 por formato inválido, se recibió {resp.status_code}: {resp.text}")
        print(f"\n[CP-04A APROBADO] Formato inválido (.txt) -> HTTP {resp.status_code} | Respuesta: {resp.text}")

    def test_cp04_tamano_mayor_1mb_retorna_400(self):
        # Generar payload WAV simulado de ~1.2 MB (1,258,291 bytes > 1,048,576 bytes)
        cabecera_wav = b"RIFF" + (1_258_283).to_bytes(4, "little") + b"WAVEfmt "
        payload_excedido = io.BytesIO(cabecera_wav + (b"\x00" * (1_258_291 - len(cabecera_wav))))
        resp = requests.post(
            API_URL,
            files={"file": ("audio_pesado.wav", payload_excedido, "audio/wav")},
            timeout=15
        )
        self.assertEqual(resp.status_code, 400, f"Se esperaba HTTP 400 por tamaño > 1 MB, se recibió {resp.status_code}: {resp.text}")
        print(f"\n[CP-04B APROBADO] Tamaño > 1 MB (1.2 MB) -> HTTP {resp.status_code} | Respuesta: {resp.text}")

if __name__ == "__main__":
    unittest.main(verbosity=2)