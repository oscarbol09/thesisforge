/**
 * ThesisForge — Settings Component
 * Manages BYOK (Bring Your Own Key) LLM providers, model selection, and Fernet vault credentials.
 * Connects directly to backend /api/settings/keys for zero-plaintext cryptographic persistence.
 */

function settingsComponent() {
  return {
    isSaving: false,
    isLoadingKeys: false,
    configuredProviders: [],
    keyInputs: {
      openrouter: '',
      gemini: '',
      openai: '',
      groq: '',
      nvidia_nim: '',
      semantic_scholar: '',
    },
    providers: [
      { id: 'openrouter', name: 'OpenRouter (Recomendado)', defaultModel: 'anthropic/claude-3.5-sonnet', keyField: 'openrouter', placeholder: 'sk-or-v1-...' },
      { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-1.5-pro', keyField: 'gemini', placeholder: 'AIzaSy...' },
      { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o', keyField: 'openai', placeholder: 'sk-proj-...' },
      { id: 'groq', name: 'Groq (Inferencia Ultra-Rápida)', defaultModel: 'llama-3.3-70b-versatile', keyField: 'groq', placeholder: 'gsk_...' },
      { id: 'nvidia_nim', name: 'NVIDIA NIM', defaultModel: 'meta/llama-3.1-70b-instruct', keyField: 'nvidia_nim', placeholder: 'nvapi-...' },
      { id: 'ollama', name: 'Ollama (Modelos Locales - 100% Offline)', defaultModel: 'llama3:latest', keyField: null, placeholder: 'http://localhost:11434' },
    ],
    _cleanupTrap: null,

    init() {
      this.loadConfiguredKeys();
      this.$watch('$store.app.showSettingsModal', (isOpen) => {
        if (isOpen) {
          this.loadConfiguredKeys();
          this.$nextTick(() => {
            const modalEl = this.$el.closest('.modal-content') || this.$el;
            if (typeof attachModalFocusTrap === 'function') {
              this._cleanupTrap = attachModalFocusTrap(modalEl, () => {
                Alpine.store('app').showSettingsModal = false;
              });
            }
          });
        } else if (this._cleanupTrap) {
          this._cleanupTrap();
          this._cleanupTrap = null;
        }
      });
    },

    async loadConfiguredKeys() {
      this.isLoadingKeys = true;
      try {
        const data = await Alpine.store('app').api('/api/settings/keys', { silent: true });
        this.configuredProviders = data.configured_providers || [];
      } catch (err) {
        this.configuredProviders = [];
      } finally {
        this.isLoadingKeys = false;
      }
    },

    async saveSettings() {
      this.isSaving = true;
      try {
        // 1. Save non-sensitive preferences
        localStorage.setItem('tf_byok_settings', JSON.stringify({
          default_provider: Alpine.store('app').settings.default_provider,
          default_model: Alpine.store('app').settings.default_model,
        }));

        // 2. Persist any entered keys securely to Fernet vault in backend
        let savedCount = 0;
        for (const [provider, keyVal] of Object.entries(this.keyInputs)) {
          if (keyVal && keyVal.trim()) {
            await Alpine.store('app').api('/api/settings/keys', {
              method: 'POST',
              body: JSON.stringify({
                provider: provider,
                api_key: keyVal.trim(),
              }),
            });
            this.keyInputs[provider] = ''; // Clear plaintext input memory
            savedCount++;
          }
        }

        await this.loadConfiguredKeys();
        Alpine.store('app').toast(
          'success',
          'Configuración Guardada',
          savedCount > 0 
            ? `${savedCount} clave(s) cifrada(s) en la bóveda Fernet local.`
            : 'Preferencias de modelos actualizadas.'
        );
        Alpine.store('app').showSettingsModal = false;
      } catch (err) {
        Alpine.store('app').toast('error', 'Error al Guardar', err.message);
      } finally {
        this.isSaving = false;
      }
    },

    async removeStoredKey(provider) {
      if (!confirm(`¿Eliminar la clave cifrada de ${provider} de la bóveda local?`)) return;
      try {
        await Alpine.store('app').api(`/api/settings/keys/${provider}`, { method: 'DELETE' });
        Alpine.store('app').toast('info', 'Clave eliminada', `La clave de ${provider} fue removida de la bóveda.`);
        await this.loadConfiguredKeys();
      } catch (err) {
        // Error toast handled in api()
      }
    },

    renderModal() {
      return `
        <div class="space-y-5 text-xs">
          
          <!-- Security & Privacy Callout -->
          <div class="p-3.5 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-blue-900 dark:text-blue-300 space-y-1">
            <div class="flex items-center gap-2 font-semibold">
              <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
              <span>Bóveda Criptográfica Fernet (Zero Plaintext Storage)</span>
            </div>
            <p class="leading-relaxed text-[11px] text-[var(--text-secondary)]">Tus claves de API se cifran en el backend SQLite con Fernet (AES-128-CBC + HMAC-SHA256). Nunca se guardan en texto plano en el navegador ni se transmiten a servidores externos salvo al proveedor que elijas.</p>
          </div>

          <!-- Provider & Model Selection Form -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label for="settings-default-provider" class="block font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Proveedor Principal *</label>
              <select id="settings-default-provider" x-model="$store.app.settings.default_provider" class="w-full text-xs">
                ${this.providers.map(p => `
                  <option value="${p.id}">${p.name}</option>
                `).join('')}
              </select>
            </div>

            <div>
              <label for="settings-default-model" class="block font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1">Modelo por Defecto *</label>
              <input id="settings-default-model" type="text" x-model="$store.app.settings.default_model" class="w-full text-xs font-mono" placeholder="anthropic/claude-3.5-sonnet">
            </div>
          </div>

          <!-- API Keys Inputs Grid -->
          <div class="space-y-3 pt-2 border-t border-[var(--border-subtle)]">
            <div class="flex items-center justify-between">
              <h4 class="font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">Credenciales Cifradas en Bóveda</h4>
              <span class="text-[10px] text-[var(--text-muted)]">Deja en blanco para conservar claves guardadas</span>
            </div>

            ${this.providers.filter(p => p.keyField).map(p => {
              const isConfigured = this.configuredProviders.includes(p.keyField);
              return `
                <div class="space-y-1">
                  <div class="flex items-center justify-between">
                    <label for="key-input-${p.keyField}" class="font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
                      <span>${p.name}</span>
                      ${isConfigured ? '<span class="badge badge-completed text-[10px] py-0 px-1.5">Cifrada en Bóveda</span>' : '<span class="badge badge-setup text-[10px] py-0 px-1.5">No Configurada</span>'}
                    </label>
                    ${isConfigured ? `
                      <button type="button" @click="removeStoredKey('${p.keyField}')" class="text-[11px] text-red-500 hover:text-red-700 underline" title="Eliminar clave de la bóveda">Eliminar</button>
                    ` : ''}
                  </div>
                  <input 
                    id="key-input-${p.keyField}"
                    type="password" 
                    x-model="keyInputs.${p.keyField}" 
                    placeholder="${isConfigured ? '•••••••••••••••• (Guardada y Cifrada — escribe para actualizar)' : p.placeholder}" 
                    class="w-full text-xs font-mono"
                    autocomplete="off"
                  >
                </div>
              `;
            }).join('')}

            <div class="space-y-1">
              <div class="flex items-center justify-between">
                <label for="key-input-semantic-scholar" class="font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
                  <span>Semantic Scholar API Key</span>
                  ${this.configuredProviders.includes('semantic_scholar') ? '<span class="badge badge-completed text-[10px] py-0 px-1.5">Cifrada</span>' : '<span class="text-[10px] text-[var(--text-muted)]">(Opcional)</span>'}
                </label>
                ${this.configuredProviders.includes('semantic_scholar') ? `
                  <button type="button" @click="removeStoredKey('semantic_scholar')" class="text-[11px] text-red-500 hover:text-red-700 underline">Eliminar</button>
                ` : ''}
              </div>
              <input 
                id="key-input-semantic-scholar"
                type="password" 
                x-model="keyInputs.semantic_scholar" 
                placeholder="Clave para consultas académicas masivas sin rate limit" 
                class="w-full text-xs font-mono"
                autocomplete="off"
              >
            </div>
          </div>

          <!-- Modal Footer Actions -->
          <div class="pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <a href="https://oscarbol09.github.io/thesisforge/legal/privacy/" target="_blank" rel="noopener noreferrer" class="text-[11px] text-blue-600 dark:text-blue-400 hover:underline">Política de Privacidad</a>
            <div class="flex items-center gap-2">
              <button type="button" class="btn btn-secondary btn-sm" @click="$store.app.showSettingsModal = false">Cerrar</button>
              <button type="button" class="btn btn-primary btn-sm" @click="saveSettings()" :disabled="isSaving">
                <span x-show="!isSaving">Guardar Cambios</span>
                <span x-show="isSaving">Guardando en Bóveda...</span>
              </button>
            </div>
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
