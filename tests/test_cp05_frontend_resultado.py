import unittest
import urllib.request
import json
import struct


class TestCP05FrontendResultado(unittest.TestCase):
    FRONTEND_URL = "http://localhost:5173"
    API_URL = "http://localhost:5000/api/analisis"

    def _generar_wav_valido(self):
        sample_rate = 16000
        num_samples = 16000  # 1 segundo
        data_size = num_samples * 2
        cabecera = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,
            1,
            sample_rate,
            sample_rate * 2,
            2,
            16,
            b"data",
            data_size,
        )
        return cabecera + (b"\x00\x00" * num_samples)

    def test_cp05_vista_web_y_resultado_disponible(self):
        # 1. Verificar que la aplicación web en Vue.js responde HTTP 200 OK
        with urllib.request.urlopen(self.FRONTEND_URL, timeout=5) as resp_web:
            self.assertEqual(resp_web.status, 200)
            html = resp_web.read().decode("utf-8", errors="ignore")
            self.assertIn('id="app"', html)

        # 2. Verificar que la API devuelve etiqueta y porcentaje para mostrar en la vista
        boundary = "----VoiceGuardBoundaryCP05"
        wav_bytes = self._generar_wav_valido()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="audio_cp05.wav"\r\n'
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode("utf-8") + wav_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            self.API_URL,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp_api:
            self.assertEqual(resp_api.status, 200)
            datos = json.loads(resp_api.read().decode("utf-8"))
            self.assertIn("resultado", datos)
            self.assertIn("confianza", datos)
            self.assertIn(datos["resultado"], ["real", "sintetica"])
            self.assertTrue(0.0 <= float(datos["confianza"]) <= 1.0)

            etiqueta_ui = "Voz real" if datos["resultado"] == "real" else "Posible voz sintética"
            porcentaje_ui = round(float(datos["confianza"]) * 100, 1)
            print(f"[CP-05 OK] Vista Vue activa (HTTP 200) | Muestra: '{etiqueta_ui}' ({porcentaje_ui}%)")


if __name__ == "__main__":
    unittest.main()