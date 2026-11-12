import os
import time
import glob
import requests

API_URL = "http://localhost:5000/api/analisis"
CARPETA_REALES = os.path.join("tests", "dataset_test", "reales", "*.wav")
CARPETA_SINTETICOS = os.path.join("tests", "dataset_test", "sinteticos", "*.wav")
UMBRAL_MS = 10000.0  # Criterio HU-04: < 10 segundos

tiempos_ms = []

def medir_latencia_lote(patron_archivos, categoria):
    archivos = glob.glob(patron_archivos)
    if not archivos:
        print(f"[AVISO] No se encontraron archivos en: {patron_archivos}")
        return

    for ruta in archivos:
        nombre = os.path.basename(ruta)
        with open(ruta, "rb") as f:
            inicio = time.perf_counter()
            resp = requests.post(API_URL, files={"file": (nombre, f, "audio/wav")}, timeout=15)
            duracion_ms = (time.perf_counter() - inicio) * 1000

        if resp.status_code == 200:
            tiempos_ms.append(duracion_ms)
            estado = "OK" if duracion_ms < UMBRAL_MS else "LENTO"
            print(f"[{categoria:9}] {nombre:28} -> HTTP 200 | Latencia: {duracion_ms:6.1f} ms [{estado}]")
        else:
            print(f"[ERROR HTTP {resp.status_code}] {nombre}: {resp.text}")

print("=== EJECUCIÓN DE PRUEBA CP-08: RENDIMIENTO / LATENCIA DE API (HU-04) ===\n")
medir_latencia_lote(CARPETA_REALES, "REAL")
medir_latencia_lote(CARPETA_SINTETICOS, "SINTETICA")

if tiempos_ms:
    total = len(tiempos_ms)
    lat_min = min(tiempos_ms)
    lat_prom = sum(tiempos_ms) / total
    lat_max = max(tiempos_ms)
    aprobados = sum(1 for t in tiempos_ms if t < UMBRAL_MS)

    print("\n" + "=" * 66)
    print("RESULTADOS CP-08 (RENDIMIENTO / LATENCIA DE INFERENCIA - HU-04)")
    print("=" * 66)
    print(f"Total de peticiones medidas : {total}")
    print(f"Peticiones < 10,000 ms      : {aprobados}/{total}")
    print(f"Tiempo mínimo de respuesta  : {lat_min:.1f} ms")
    print(f"Tiempo promedio respuesta   : {lat_prom:.1f} ms")
    print(f"Tiempo máximo de respuesta  : {lat_max:.1f} ms  (Criterio < 10,000 ms: {'APROBADO' if lat_max < UMBRAL_MS else 'FALLIDO'})")
else:
    print("\nNo se registraron tiempos. Verifica que el backend esté activo y existan audios .wav.")