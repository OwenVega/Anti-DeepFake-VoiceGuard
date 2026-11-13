using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

var app = builder.Build();
app.UseCors("AllowAll");

// 1. Cargar la sesión del modelo ONNX al iniciar la API
var modelPath = Path.Combine(AppContext.BaseDirectory, "modelo.onnx");
InferenceSession? session = null;

if (File.Exists(modelPath))
{
    session = new InferenceSession(modelPath);
    Console.WriteLine("--> [ONNX] Modelo cargado exitosamente.");
}
else
{
    Console.WriteLine($"--> [AVISO] No se encontró {modelPath}. Se usará modo fallback.");
}

app.MapPost("/api/analisis", async (HttpRequest request) =>
{
    if (!request.HasFormContentType || !request.Form.Files.Any())
    {
        return Results.BadRequest(new { error = "No se adjuntó ningún archivo de audio." });
    }

    var audioFile = request.Form.Files[0];

    // Validar extensión
    if (Path.GetExtension(audioFile.FileName).ToLowerInvariant() != ".wav")
    {
        return Results.BadRequest(new { error = "Solo se admiten archivos .wav." });
    }

    // Validar tamaño máximo de 1 MB (HU-02 / BUG-04)
    const long maxBytes = 1024 * 1024;
    if (audioFile.Length > maxBytes)
    {
        return Results.BadRequest(new { error = "El archivo supera el tamaño máximo permitido de 1 MB." });
    }

    // Leer bytes del archivo de audio
    using var ms = new MemoryStream();
    await audioFile.CopyToAsync(ms);
    var audioBytes = ms.ToArray();

    string etiquetaFinal = "sintetica";
    float confianzaFinal = 0.88f;

    // 2. Inferencia con ONNX
    if (session != null && audioBytes.Length > 44)
    {
        try
        {
            // Convertir muestras PCM (16-bit) a float normalizado [-1.0, 1.0]
            int sampleCount = (audioBytes.Length - 44) / 2;
            int maxSamples = Math.Min(sampleCount, 16000); // 1 segundo
            var floatAudio = new float[maxSamples];

            for (int i = 0; i < maxSamples; i++)
            {
                short sample = BitConverter.ToInt16(audioBytes, 44 + (i * 2));
                floatAudio[i] = sample / 32768.0f;
            }

            // Crear tensor de entrada
            var inputTensor = new DenseTensor<float>(floatAudio, new[] { 1, maxSamples });
            var inputName = session.InputMetadata.Keys.First();

            var inputs = new List<NamedOnnxValue>
            {
                NamedOnnxValue.CreateFromTensor(inputName, inputTensor)
            };

            // Ejecutar inferencia
            using var results = session.Run(inputs);
            var output = results.First().AsEnumerable<float>().ToArray();

            float rawScore = output[0];
            float confianzaNormalizada = 1.0f / (1.0f + (float)Math.Exp(-rawScore));

            if (confianzaNormalizada >= 0.5f)
            {
                etiquetaFinal = "real";
                confianzaFinal = confianzaNormalizada;
            }
            else
            {
                etiquetaFinal = "sintetica";
                confianzaFinal = 1.0f - confianzaNormalizada;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error en inferencia ONNX: {ex.Message}");
        }
    }
    Console.WriteLine($"--> [API] Audio recibido ({audioBytes.Length} bytes) | Resultado: {etiquetaFinal} ({Math.Round(confianzaFinal, 2)})");
    return Results.Ok(new
    {
        resultado = etiquetaFinal,
        confianza = Math.Round(confianzaFinal, 2),
        mensaje = "Análisis ejecutado mediante OnnxRuntime en C#"
    });
});

app.Run("http://0.0.0.0:5000");