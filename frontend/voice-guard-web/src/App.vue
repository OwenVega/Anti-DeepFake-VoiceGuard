<template>
  <div class="app-wrapper">
    <!-- Navbar superior -->
    <header class="navbar">
      <div class="brand">
        <div class="logo-icon">🛡️</div>
        <div>
          <h1>VoiceGuard <span class="tag">AI</span></h1>
          <p class="tagline">Anti-Deep Fake Voice Detection System</p>
        </div>
      </div>
      <div class="status-indicator">
        <span class="status-dot"></span>
        <span>Modelo listo</span>
      </div>
    </header>

    <!-- Contenedor principal -->
    <main class="main-content">
      <div class="analyzer-grid">
        <!-- Panel Izquierdo: Carga y análisis -->
        <section class="card upload-card">
          <div class="card-header">
            <h2>Analizador de Audio</h2>
            <p>Sube una grabación sospechosa en formato WAV para verificar autenticidad.</p>
          </div>

          <!-- Zona Drag and Drop -->
          <div 
            class="dropzone" 
            :class="{ 'has-file': file, 'dragging': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="$refs.fileInput.click()"
          >
            <input 
              ref="fileInput" 
              type="file" 
              accept=".wav" 
              class="hidden-input" 
              @change="handleFileChange" 
            />
            
            <div class="dropzone-content" v-if="!file">
              <div class="upload-icon">🎙️</div>
              <p class="drop-title">Arrastra tu archivo WAV aquí o <span>explora</span></p>
              <p class="drop-sub">PCM 16-bit, 16 kHz • Máx. 1 MB</p>
            </div>

            <div class="file-preview" v-else>
              <div class="file-icon">🎵</div>
              <div class="file-info">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ (file.size / 1024).toFixed(1) }} KB</span>
              </div>
              <button class="remove-btn" @click.stop="file = null; resultado = null">✕</button>
            </div>
          </div>

          <!-- Botón de acción con animación de carga -->
          <button 
            class="action-btn" 
            :class="{ 'btn-loading': loading }"
            :disabled="!file || loading" 
            @click="enviarAudio"
          >
            <span v-if="!loading">🔍 Analizar Espectrograma</span>
            <span v-else class="loader-content">
              <span class="spinner"></span>
              Extrayendo características acústicas...
            </span>
          </button>

          <!-- Animación de ondas cuando está analizando -->
          <div v-if="loading" class="wave-container">
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
            <span class="wave-bar"></span>
          </div>

          <div v-if="error" class="error-banner">
            ⚠️ {{ error }}
          </div>
        </section>

        <!-- Panel Derecho: Resultados -->
        <section class="card result-card">
          <div class="card-header">
            <h2>Diagnóstico del Sistema</h2>
            <p>Resultado del clasificador binario de voz.</p>
          </div>

          <!-- Estado inicial vacío -->
          <div v-if="!resultado && !loading" class="empty-state">
            <div class="empty-icon">📊</div>
            <p class="empty-title">Sin análisis activo</p>
            <p class="empty-sub">Carga un audio y presiona analizar para inspeccionar artefactos sintéticos.</p>
          </div>

          <!-- Resultado generado -->
          <div v-if="resultado" class="report-box" :class="resultado.resultado">
            <div class="badge-result">
              {{ resultado.resultado === 'sintetica' ? '⚠️ ALERTA: VOZ SINTÉTICA (DEEPFAKE)' : '✓ VOZ AUTÉNTICA CONFIRMADA' }}
            </div>

            <div class="score-display">
              <div class="radial-score">
                <span class="score-number">{{ (resultado.confianza * 100).toFixed(0) }}%</span>
                <span class="score-label">Nivel de Confianza</span>
              </div>
              <div class="score-details">
                <p><strong>Clasificación:</strong> {{ resultado.resultado === 'sintetica' ? 'Generada por IA' : 'Humana / Real' }}</p>
                <p><strong>Estado API:</strong> 200 OK</p>
                <p><strong>Respuesta:</strong> {{ resultado.mensaje }}</p>
              </div>
            </div>

            <!-- Medidor de certeza -->
            <div class="meter-wrapper">
              <div class="meter-header">
                <span>Certeza del modelo</span>
                <span>{{ (resultado.confianza * 100).toFixed(1) }}%</span>
              </div>
              <div class="meter-bar">
                <div class="meter-fill" :style="{ width: (resultado.confianza * 100) + '%' }"></div>
              </div>
            </div>

            <!-- Recomendación de seguridad -->
            <div class="security-tip" v-if="resultado.resultado === 'sintetica'">
              <strong>Protocolo de seguridad:</strong> No proporciones datos confidenciales ni claves. Corta la llamada y valida la identidad por un medio alterno oficial.
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const file = ref(null);
const loading = ref(false);
const resultado = ref(null);
const error = ref('');
const isDragging = ref(false);

const handleFileChange = (e) => {
  if (e.target.files.length) {
    file.value = e.target.files[0];
    error.value = '';
    resultado.value = null;
  }
};

const handleDrop = (e) => {
  isDragging.value = false;
  if (e.dataTransfer.files.length) {
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile.name.endsWith('.wav')) {
      file.value = droppedFile;
      error.value = '';
      resultado.value = null;
    } else {
      error.value = 'Solo se admiten archivos .wav';
    }
  }
};

const enviarAudio = async () => {
  if (!file.value) return;

  loading.value = true;
  error.value = '';
  resultado.value = null;

  const formData = new FormData();
  formData.append('audio', file.value);

  try {
    const res = await fetch('http://localhost:5000/api/analisis', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'Error al procesar el audio');
    }
    // Pequeño delay de 800ms para mostrar la animación fluida
    setTimeout(() => {
      resultado.value = data;
      loading.value = false;
    }, 800);
  } catch (err) {
    error.value = err.message || 'No se pudo conectar con la API en localhost:5000';
    loading.value = false;
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }

.app-wrapper {
  min-height: 100vh;
  background-color: #0b0f19;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
}

/* Navbar */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 2.5rem;
  background: #111827;
  border-bottom: 1px solid #1f2937;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 1.8rem;
  background: rgba(59, 130, 246, 0.1);
  padding: 8px;
  border-radius: 10px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.brand h1 {
  font-size: 1.3rem;
  font-weight: 700;
  color: #f8fafc;
}

.tag {
  font-size: 0.75rem;
  background: #2563eb;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
}

.tagline {
  font-size: 0.8rem;
  color: #94a3b8;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 8px #10b981;
}

/* Contenido Principal */
.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2.5rem;
}

.analyzer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  max-width: 1050px;
  width: 100%;
}

.card {
  background: #111827;
  border: 1px solid #1f2937;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.card-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f8fafc;
  margin-bottom: 6px;
}

.card-header p {
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 1.5rem;
}

/* Dropzone */
.dropzone {
  border: 2px dashed #374151;
  border-radius: 12px;
  padding: 2.5rem 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #0f172a;
}

.dropzone:hover, .dropzone.dragging {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.dropzone.has-file {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.04);
}

.hidden-input { display: none; }

.upload-icon { font-size: 2.5rem; margin-bottom: 10px; }

.drop-title {
  font-weight: 500;
  font-size: 0.95rem;
  color: #cbd5e1;
}

.drop-title span { color: #3b82f6; text-decoration: underline; }

.drop-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 4px;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #1e293b;
  border-radius: 8px;
}

.file-icon { font-size: 1.5rem; }

.file-info {
  display: flex;
  flex-direction: column;
  text-align: left;
  flex: 1;
  margin-left: 12px;
}

.file-name { font-weight: 600; font-size: 0.9rem; color: #f1f5f9; }
.file-size { font-size: 0.75rem; color: #94a3b8; }

.remove-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  font-size: 1.2rem;
  cursor: pointer;
}

/* Botón */
.action-btn {
  width: 100%;
  margin-top: 1.5rem;
  padding: 14px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
}

.action-btn:hover:not(:disabled) {
  opacity: 0.95;
  transform: translateY(-1px);
}

.action-btn:disabled {
  background: #374151;
  color: #6b7280;
  cursor: not-allowed;
  box-shadow: none;
}

/* Ondas animadas */
.wave-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  height: 30px;
  margin-top: 1.5rem;
}

.wave-bar {
  width: 5px;
  height: 100%;
  background: #3b82f6;
  border-radius: 4px;
  animation: wave 1s infinite ease-in-out;
}

.wave-bar:nth-child(2) { animation-delay: 0.2s; }
.wave-bar:nth-child(3) { animation-delay: 0.4s; }
.wave-bar:nth-child(4) { animation-delay: 0.1s; }
.wave-bar:nth-child(5) { animation-delay: 0.3s; }

@keyframes wave {
  0%, 100% { height: 6px; }
  50% { height: 26px; }
}

/* Estado de Resultados */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 250px;
  color: #64748b;
  text-align: center;
}

.empty-icon { font-size: 3rem; margin-bottom: 10px; opacity: 0.5; }
.empty-title { font-weight: 600; color: #94a3b8; font-size: 1rem; }
.empty-sub { font-size: 0.85rem; max-width: 250px; margin-top: 4px; }

.report-box {
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid;
  animation: fadeIn 0.3s ease-in;
}

.report-box.sintetica {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.3);
}

.report-box.real {
  background: rgba(16, 185, 129, 0.05);
  border-color: rgba(16, 185, 129, 0.3);
}

.badge-result {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 1.2rem;
}

.sintetica .badge-result { color: #f87171; }
.real .badge-result { color: #34d399; }

.score-display {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.radial-score {
  background: #1e293b;
  padding: 14px 20px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-number {
  font-size: 2rem;
  font-weight: 800;
  color: #f8fafc;
}

.score-label {
  font-size: 0.7rem;
  color: #94a3b8;
  text-transform: uppercase;
}

.score-details p {
  font-size: 0.85rem;
  color: #cbd5e1;
  margin-bottom: 4px;
}

.meter-wrapper { margin-bottom: 1.2rem; }

.meter-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #94a3b8;
  margin-bottom: 6px;
}

.meter-bar {
  width: 100%;
  height: 8px;
  background: #1e293b;
  border-radius: 6px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  transition: width 0.6s ease;
}

.sintetica .meter-fill { background: linear-gradient(90deg, #f87171, #ef4444); }
.real .meter-fill { background: linear-gradient(90deg, #34d399, #10b981); }

.security-tip {
  font-size: 0.8rem;
  background: rgba(239, 68, 68, 0.1);
  padding: 10px 12px;
  border-radius: 8px;
  color: #fca5a5;
  line-height: 1.4;
}

.error-banner {
  margin-top: 1rem;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.85rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 850px) {
  .analyzer-grid { grid-template-columns: 1fr; }
}
</style>