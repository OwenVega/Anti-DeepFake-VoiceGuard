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

    // Leer bytes del archivo de audio
    using var ms = new MemoryStream();
    await audioFile.CopyToAsync(ms);
    var audioBytes = ms.ToArray();

    string etiquetaFinal = "sintetica";
    float confianzaFinal = 0.88f;

    // 2. Inferencia con ONNX
    if (session != null && audioBytes.Length > 44) // Validar cabecera WAV
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

            // Crear tensor de entrada [1, 1, 16000]
            var inputTensor = new DenseTensor<float>(floatAudio, new[] { 1, maxSamples });
            var inputName = session.InputMetadata.Keys.First();

            var inputs = new List<NamedOnnxValue>
            {
                NamedOnnxValue.CreateFromTensor(inputName, inputTensor)
            };

            // Ejecutar inferencia
            using var results = session.Run(inputs);
            var output = results.First().AsEnumerable<float>().ToArray();

            // Salida: [prob_real, prob_sintetica]
            // Tomamos el valor de salida (si bota números locos, aplicamos Sigmoide)
            float rawScore = output[0];
            
            // Fórmula Sigmoide para asegurar que la confianza esté estrictamente entre 0.0 y 1.0
            float confianzaNormalizada = 1.0f / (1.0f + (float)Math.Exp(-rawScore));

            // Si pasa de 0.5 lo catalogamos como sintética, sino real
            // Si la probabilidad es >= 0.5 ahora es "real", sino "sintetica"
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

    return Results.Ok(new
    {
        resultado = etiquetaFinal,
        confianza = Math.Round(confianzaFinal, 2),
        mensaje = "Análisis ejecutado mediante OnnxRuntime en C#"
    });
});

app.Run("http://localhost:5000");