import os
import glob
import requests

API_URL = "http://localhost:5000/api/analisis"
CARPETA_REALES = os.path.join("tests", "dataset_test", "reales", "*.wav")
CARPETA_SINTETICOS = os.path.join("tests", "dataset_test", "sinteticos", "*.wav")

# Matriz de confusión (Clase positiva = "sintetica")
VP = 0  # Sintética detectada como sintética
FN = 0  # Sintética detectada como real (Falso Negativo)
VN = 0  # Real detectada como real
FP = 0  # Real detectada como sintética (Falso Positivo)

def evaluar_lote(patron_archivos, etiqueta_esperada):
    global VP, FN, VN, FP
    archivos = glob.glob(patron_archivos)
    if not archivos:
        print(f"[AVISO] No se encontraron archivos en: {patron_archivos}")
        return

    for ruta in archivos:
        nombre = os.path.basename(ruta)
        with open(ruta, "rb") as f:
            resp = requests.post(API_URL, files={"file": (nombre, f, "audio/wav")}, timeout=15)

        if resp.status_code != 200:
            print(f"[ERROR HTTP {resp.status_code}] {nombre}: {resp.text}")
            continue

        data = resp.json()
        prediccion = data.get("resultado", "").strip().lower()
        confianza = data.get("confianza", 0)

        if etiqueta_esperada == "sintetica":
            if prediccion == "sintetica":
                VP += 1
            else:
                FN += 1
        else:
            if prediccion == "real":
                VN += 1
            else:
                FP += 1

        print(f"[{etiqueta_esperada.upper():9}] {nombre:28} -> Pred: {prediccion:9} (Confianza: {confianza:.2f})")

print("=== EJECUCIÓN DE PRUEBA CP-07: DESEMPEÑO DEL MODELO ML (HU-04) ===\n")
evaluar_lote(CARPETA_REALES, "real")
evaluar_lote(CARPETA_SINTETICOS, "sintetica")

total = VP + VN + FP + FN
if total > 0:
    accuracy = ((VP + VN) / total) * 100
    fpr = (FP / (FP + VN) * 100) if (FP + VN) > 0 else 0.0
    fnr = (FN / (FN + VP) * 100) if (FN + VP) > 0 else 0.0

    print("\n" + "=" * 62)
    print("RESULTADOS CP-07 (DESEMPEÑO DEL MODELO ML - HU-04)")
    print("=" * 62)
    print(f"Total de audios evaluados   : {total}")
    print(f"Matriz de Confusión         : VP={VP} | VN={VN} | FP={FP} | FN={FN}")
    print(f"Exactitud (Accuracy)        : {accuracy:.2f}%  (Criterio >= 85%: {'APROBADO' if accuracy >= 85 else 'REVISAR'})")
    print(f"Tasa Falsos Positivos (FPR) : {fpr:.2f}%")
    print(f"Tasa Falsos Negativos (FNR) : {fnr:.2f}%")
else:
    print("\nNo se evaluaron archivos. Verifica que existan .wav en tests/dataset_test/reales y sinteticos.")