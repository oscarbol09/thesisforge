/**
 * ThesisForge — Settings Component
 * Manages BYOK (Bring Your Own Key) LLM providers, model selection, and Fernet vault credentials.
 */

function settingsComponent() {
  return {
    isSaving: false,
    providers: [
      { id: 'openrouter', name: 'OpenRouter (Recomendado)', defaultModel: 'anthropic/claude-3.5-sonnet', keyField: 'openrouter_api_key', placeholder: 'sk-or-v1-...' },
      { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-1.5-pro', keyField: 'gemini_api_key', placeholder: 'AIzaSy...' },
      { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o', keyField: 'openai_api_key', placeholder: 'sk-proj-...' },
      { id: 'groq', name: 'Groq (Inferencia Ultra-Rápida)', defaultModel: 'llama-3.3-70b-versatile', keyField: 'groq_api_key', placeholder: 'gsk_...' },
      { id: 'nvidia_nim', name: 'NVIDIA NIM', defaultModel: 'meta/llama-3.1-70b-instruct', keyField: 'nvidia_nim_api_key', placeholder: 'nvapi-...' },
      { id: 'ollama', name: 'Ollama (Modelos Locales)', defaultModel: 'llama3:latest', keyField: null, placeholder: 'http://localhost:11434' },
    ],

    saveSettings() {
      this.isSaving = true;
      try {
        localStorage.setItem('tf_byok_settings', JSON.stringify(Alpine.store('app').settings));
        Alpine.store('app').toast('success', 'Configuración Guardada', 'Las credenciales BYOK han sido actualizadas.');
        Alpine.store('app').showSettingsModal = false;
      } catch (err) {
        Alpine.store('app').toast('error', 'Error al Guardar', err.message);
      } finally {
        this.isSaving = false;
      }
    },

    renderModal() {
      const app = Alpine.store('app');
      return `
        <div class="space-y-5 text-xs">
          
          <!-- Security Callout -->
          <div class="p-3.5 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-blue-900 dark:text-blue-300 space-y-1">
            <div class="flex items-center gap-2 font-semibold">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
              <span>Seguridad de Claves (Zero Trust & Fernet Vault)</span>
            </div>
            <p class="leading-relaxed">Tus credenciales se cifran localmente con Fernet (AES-128-CBC + HMAC-SHA256). Solo se usan para comunicar con el proveedor seleccionado.</p>
          </div>

          <!-- Provider & Model Selection -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Proveedor Principal *</label>
              <select x-model="$store.app.settings.default_provider" class="w-full text-xs">
                ${this.providers.map(p => `
                  <option value="${p.id}">${p.name}</option>
                `).join('')}
              </select>
            </div>

            <div>
              <label class="block font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Modelo por Defecto *</label>
              <input type="text" x-model="$store.app.settings.default_model" class="w-full text-xs" placeholder="anthropic/claude-3.5-sonnet">
            </div>
          </div>

          <!-- API Keys Inputs Grid -->
          <div class="space-y-3 pt-2 border-t border-[var(--border-subtle)]">
            <h4 class="font-bold text-xs uppercase tracking-wider text-[var(--text-muted)]">Credenciales de Proveedores</h4>

            ${this.providers.filter(p => p.keyField).map(p => `
              <div>
                <label class="block font-semibold text-[var(--text-secondary)] mb-1">${p.name} API Key</label>
                <input 
                  type="password" 
                  x-model="$store.app.settings.${p.keyField}" 
                  placeholder="${p.placeholder}" 
                  class="w-full text-xs font-mono"
                >
              </div>
            `).join('')}

            <div>
              <label class="block font-semibold text-[var(--text-secondary)] mb-1">Semantic Scholar API Key (Opcional — Aumenta Rate Limits)</label>
              <input 
                type="password" 
                x-model="$store.app.settings.semantic_scholar_api_key" 
                placeholder="Clave para consultas académicas masivas" 
                class="w-full text-xs font-mono"
              >
            </div>
          </div>

          <!-- Modal Footer Actions -->
          <div class="pt-4 border-t border-[var(--border-subtle)] flex justify-end gap-2">
            <button type="button" class="btn btn-secondary btn-sm" @click="$store.app.showSettingsModal = false">Cerrar</button>
            <button type="button" class="btn btn-primary btn-sm" @click="saveSettings()" :disabled="isSaving">
              <span x-show="!isSaving">Guardar Claves</span>
              <span x-show="isSaving">Guardando...</span>
            </button>
          </div>

        </div>
      `;
    },

    render() {
      return `
        <div class="max-w-3xl mx-auto space-y-6">
          <div class="card p-6">
            <h3 class="font-bold text-lg text-[var(--text-primary)] mb-4">Configuración de Proveedores de Inferencia (BYOK)</h3>
            ${this.renderModal()}
          </div>
        </div>
      `;
    }
  };
}
