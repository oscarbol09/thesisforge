/**
 * ThesisForge — Settings Component
 * Manages BYOK (Bring Your Own Key) LLM providers, dynamic model catalog selection,
 * real-time connection verification, and Fernet vault credentials.
 */

function settingsComponent() {
  return {
    isSaving: false,
    isLoadingKeys: false,
    isTestingConnection: false,
    testResult: null,
    isCustomModel: false,
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
      { id: 'openrouter', name: 'OpenRouter (Multi-Proveedor & Free Tier)', keyField: 'openrouter', placeholder: 'sk-or-v1-...' },
      { id: 'gemini', name: 'Google Gemini (Google AI Studio)', keyField: 'gemini', placeholder: 'AIzaSy...' },
      { id: 'groq', name: 'Groq (Inferencia Ultra-Rápida LPU)', keyField: 'groq', placeholder: 'gsk_...' },
      { id: 'openai', name: 'OpenAI (GPT-4o / o3-mini)', keyField: 'openai', placeholder: 'sk-proj-...' },
      { id: 'nvidia_nim', name: 'NVIDIA NIM (TensorRT-LLM)', keyField: 'nvidia_nim', placeholder: 'nvapi-...' },
      { id: 'ollama', name: 'Ollama (Modelos Locales - 100% Offline)', keyField: null, placeholder: 'http://localhost:11434' },
    ],

    _cleanupTrap: null,

    init() {
      this.loadConfiguredKeys();
      this.syncModelSelection();

      this.$watch('$store.app.showSettingsModal', (isOpen) => {
        if (isOpen) {
          this.loadConfiguredKeys();
          this.syncModelSelection();
          this.testResult = null;
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

    get keyProviders() {
      return this.providers.filter((p) => p.keyField !== null);
    },

    get currentProvider() {
      return Alpine.store('app').settings.default_provider || 'openrouter';
    },

    get availableModels() {
      return typeof getModelsForProvider === 'function'
        ? getModelsForProvider(this.currentProvider)
        : [];
    },

    get freeModels() {
      return this.availableModels.filter((m) => m.freeTier);
    },

    get premiumModels() {
      return this.availableModels.filter((m) => !m.freeTier);
    },

    get selectedModelInfo() {
      const currentModel = Alpine.store('app').settings.default_model;
      if (typeof findModelDetails === 'function') {
        return findModelDetails(this.currentProvider, currentModel);
      }
      return null;
    },

    syncModelSelection() {
      const currentModel = Alpine.store('app').settings.default_model;
      const modelInfo = this.selectedModelInfo;

      if (!modelInfo && currentModel && currentModel.trim()) {
        // Current model is custom or not in provider catalog
        const modelsForProv = this.availableModels;
        const belongsToProvider = modelsForProv.some((m) => m.id === currentModel);
        if (!belongsToProvider && modelsForProv.length > 0) {
          // Auto select recommended model for this provider
          const rec = typeof getRecommendedModelForProvider === 'function'
            ? getRecommendedModelForProvider(this.currentProvider)
            : modelsForProv[0].id;
          Alpine.store('app').settings.default_model = rec;
          this.isCustomModel = false;
        } else if (!belongsToProvider) {
          this.isCustomModel = true;
        }
      } else {
        this.isCustomModel = false;
      }
    },

    onProviderChange(newProvider) {
      Alpine.store('app').settings.default_provider = newProvider;
      this.testResult = null;
      // Auto select the recommended model for the new provider
      if (typeof getRecommendedModelForProvider === 'function') {
        Alpine.store('app').settings.default_model = getRecommendedModelForProvider(newProvider);
      }
      this.isCustomModel = false;
    },

    onModelChange(newModel) {
      Alpine.store('app').settings.default_model = newModel;
      this.testResult = null;
      this.isCustomModel = false;
    },

    toggleCustomModel() {
      this.isCustomModel = !this.isCustomModel;
      this.testResult = null;
      if (this.isCustomModel) {
        this.$nextTick(() => {
          const el = document.getElementById('settings-custom-model-input');
          if (el) el.focus();
        });
      } else {
        this.syncModelSelection();
      }
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

    async testConnection() {
      this.isTestingConnection = true;
      this.testResult = null;

      const provider = this.currentProvider;
      const model = Alpine.store('app').settings.default_model;
      const enteredKey = this.keyInputs[provider] ? this.keyInputs[provider].trim() : '';

      try {
        const result = await Alpine.store('app').api('/api/settings/test-connection', {
          method: 'POST',
          body: JSON.stringify({
            provider: provider,
            model: model,
            api_key: enteredKey || null,
          }),
        });

        this.testResult = result;
      } catch (err) {
        this.testResult = {
          status: 'error',
          message: err.message || 'Error al verificar conexión con el proveedor.',
        };
      } finally {
        this.isTestingConnection = false;
      }
    },

    async saveSettings() {
      this.isSaving = true;
      try {
        // 1. Save non-sensitive preferences
        localStorage.setItem(
          'tf_byok_settings',
          JSON.stringify({
            default_provider: Alpine.store('app').settings.default_provider,
            default_model: Alpine.store('app').settings.default_model,
          })
        );

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
            this.keyInputs[provider] = ''; // Clear plaintext memory
            savedCount++;
          }
        }

        await this.loadConfiguredKeys();
        Alpine.store('app').toast(
          'success',
          'Configuración Guardada',
          savedCount > 0
            ? `${savedCount} clave(s) cifrada(s) en la bóveda Fernet local.`
            : `Proveedor configurado: ${this.currentProvider} (${Alpine.store('app').settings.default_model})`
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
        Alpine.store('app').toast(
          'info',
          'Clave eliminada',
          `La clave de ${provider} fue removida de la bóveda.`
        );
        await this.loadConfiguredKeys();
      } catch (err) {
        // Handled in api()
      }
    },
  };
}
