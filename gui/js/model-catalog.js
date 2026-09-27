/**
 * ThesisForge — Curated Academic Model Catalog
 * Verified & active models across OpenRouter, Google Gemini, Groq, OpenAI, NVIDIA NIM, and Ollama.
 * Categorized by Free Tier vs Premium Tier with academic research profiles.
 */

const MODEL_CATALOG = {
  openrouter: [
    // --- FREE TIER (OpenRouter :free) ---
    {
      id: 'google/gemma-4-31b-it:free',
      name: 'Google Gemma 4 31B (Free)',
      badge: '⭐ Flagship Free',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Arquitectura frontier de Google DeepMind. Extraordinario razonamiento, rigor metodológico y síntesis bibliográfica.',
      specs: '31B Parámetros • Contexto 128k • Free Tier OpenRouter',
      freeTier: true,
      recommended: true,
    },
    {
      id: 'nvidia/nemotron-3-ultra-550b-a55b:free',
      name: 'NVIDIA Nemotron 3 Ultra 550B (Free)',
      badge: '🚀 550B MoE Free',
      badgeClass: 'bg-green-500/15 text-green-600 dark:text-green-400 border border-green-500/30',
      description: 'Modelo masivo Mixture of Experts con 550B parámetros. Máxima consistencia lógica en marcos teóricos extensos.',
      specs: '550B MoE • Contexto 1M • Free Tier OpenRouter',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'nvidia/nemotron-3-super-120b-a12b:free',
      name: 'NVIDIA Nemotron 3 Super 120B (Free)',
      badge: '⚡ Alta Capacidad Free',
      badgeClass: 'bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30',
      description: 'Gran balance entre profundidad conceptual y velocidad de generación para redacción capitular continua.',
      specs: '120B Parámetros • Contexto 128k • Free Tier OpenRouter',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'nvidia/nemotron-3.5-lightning:free',
      name: 'NVIDIA Nemotron 3.5 Lightning (Free)',
      badge: '⚡ Ultra Rápido Free',
      badgeClass: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30',
      description: 'Inferencia ultra ágil para formulación de preguntas de investigación y validación de objetivos.',
      specs: '30B Parámetros • Inferencia Veloz • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'google/gemma-4-26b-a4b-it:free',
      name: 'Google Gemma 4 26B MoE (Free)',
      badge: '⚖️ MoE Eficiente Free',
      badgeClass: 'bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/30',
      description: 'Mixture of Experts ágil para revisión estilística APA 7 y estructuración de borradores.',
      specs: '26B MoE • Google DeepMind • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'qwen/qwen3.8-27b:free',
      name: 'Qwen 3.8 27B (Free)',
      badge: '🌐 Multilingüe Free',
      badgeClass: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30',
      description: 'Excelente comprensión y redacción en español formal académico y formateo de referencias.',
      specs: '27B Parámetros • Contexto 32k • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'thinkingmachines/inkling:free',
      name: 'ThinkingMachines Inkling (Free)',
      badge: '🧠 Razonamiento Free',
      badgeClass: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30',
      description: 'Especializado en deducción analítica y detección de falacias o contradicciones metodológicas.',
      specs: '41B Activos • Free Tier OpenRouter',
      freeTier: true,
      recommended: false,
    },

    // --- PREMIUM TIER (Requiere saldo en cuenta OpenRouter) ---
    {
      id: 'anthropic/claude-3.5-sonnet',
      name: 'Anthropic Claude 3.5 Sonnet',
      badge: '👑 Estándar de Oro Académico',
      badgeClass: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30',
      description: 'La máxima referencia mundial para redacción científica, profundidad analítica y prosa académica impecable.',
      specs: 'Anthropic • Contexto 200k • Prémium OpenRouter',
      freeTier: false,
      recommended: true,
    },
    {
      id: 'openai/gpt-4o',
      name: 'OpenAI GPT-4o',
      badge: '🚀 Flagship Multimodal',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Alta velocidad e inteligencia para sintetizar documentos densos, tablas y citas estructuradas.',
      specs: 'OpenAI • Contexto 128k • Prémium OpenRouter',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'openai/o3-mini',
      name: 'OpenAI o3-mini (Razonamiento)',
      badge: '🧠 Razonamiento STEM & Estadístico',
      badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30',
      description: 'Cadena de pensamiento rigurosa para diseño de experimentos, análisis estadístico y contraste de hipótesis.',
      specs: 'OpenAI • Contexto 200k • Prémium OpenRouter',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'deepseek/deepseek-r1',
      name: 'DeepSeek R1',
      badge: '🧠 Razonamiento Abierto',
      badgeClass: 'bg-violet-500/15 text-violet-600 dark:text-violet-400 border border-violet-500/30',
      description: 'Capacidad de razonamiento deductivo profundo para la auditoría de jurado y defensas socráticas.',
      specs: 'DeepSeek • Contexto 64k • Prémium OpenRouter',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'deepseek/deepseek-chat',
      name: 'DeepSeek V3 (Chat)',
      badge: '💰 Alta Calidad / Bajo Coste',
      badgeClass: 'bg-fuchsia-500/15 text-fuchsia-600 dark:text-fuchsia-400 border border-fuchsia-500/30',
      description: '671B MoE frontier con excelente relación costo/calidad en redacción de borradores.',
      specs: 'DeepSeek • Contexto 128k • Prémium OpenRouter',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'meta-llama/llama-3.3-70b-instruct',
      name: 'Meta Llama 3.3 70B Instruct',
      badge: '⭐ Meta Flagship',
      badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30',
      description: 'Alta coherencia en redacción bajo normas APA 7 y estructuración de capítulos.',
      specs: '70B Parámetros • Meta • Contexto 128k',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'google/gemini-2.5-pro',
      name: 'Google Gemini 2.5 Pro',
      badge: '📜 Ventana Masiva 1M',
      badgeClass: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30',
      description: 'Razonamiento frontier y capacidad para procesar tesis y monografías completas en un único contexto.',
      specs: 'Google • Contexto 1M • Prémium OpenRouter',
      freeTier: false,
      recommended: false,
    },
  ],

  gemini: [
    // --- GOOGLE AI STUDIO (15 RPM FREE TIER) ---
    {
      id: 'gemini-3.8-flash',
      name: 'Google Gemini 3.8 Flash',
      badge: '⭐ Recomendado Flagship (Free en AI Studio)',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Modelo insignia actual de Google. Velocidad extrema, 1M de tokens y cuota gratuita de 15 RPM en Google AI Studio.',
      specs: 'Google AI Studio • 1M Contexto • 15 RPM Free Tier',
      freeTier: true,
      recommended: true,
    },
    {
      id: 'gemini-3.7-flash',
      name: 'Google Gemini 3.7 Flash',
      badge: '⚡ Alta Eficiencia Free',
      badgeClass: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30',
      description: 'Alta fidelidad en redacción, análisis metodológico y estructuración de citas bibliográficas.',
      specs: 'Google AI Studio • 1M Contexto • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'gemini-3.5-flash',
      name: 'Google Gemini 3.5 Flash',
      badge: '🚀 Ultrarrápido Free',
      badgeClass: 'bg-sky-500/15 text-sky-600 dark:text-sky-400 border border-sky-500/30',
      description: 'Excelente para indexación RAG de PDFs y respuestas inmediatas.',
      specs: 'Google AI Studio • 1M Contexto • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'gemini-2.5-flash',
      name: 'Google Gemini 2.5 Flash',
      badge: '📘 Estable Free',
      badgeClass: 'bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30',
      description: 'Modelo contrastado con gran rendimiento para borradores continuos.',
      specs: 'Google AI Studio • 1M Contexto • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'gemini-2.5-pro',
      name: 'Google Gemini 2.5 Pro',
      badge: '🧠 Razonamiento Máximo',
      badgeClass: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30',
      description: 'Capacidad de razonamiento superior para auditorías de consistencia metodológica e hipótesis complejas.',
      specs: 'Google AI Studio • 1M Contexto • Nivel Pro',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'gemini-1.5-pro',
      name: 'Google Gemini 1.5 Pro',
      badge: '📜 Contexto Extenso (2M)',
      badgeClass: 'bg-violet-500/15 text-violet-600 dark:text-violet-400 border border-violet-500/30',
      description: 'Ventana de 2 millones de tokens para revisar tesis completas de más de 100 páginas.',
      specs: 'Google AI Studio • 2M Contexto • Nivel Pro',
      freeTier: false,
      recommended: false,
    },
  ],

  groq: [
    // --- GROQ CLOUD (Ultra-Fast LPU Inferencia con Free Tier) ---
    {
      id: 'llama-3.3-70b-versatile',
      name: 'Llama 3.3 70B Versatile',
      badge: '⭐ Recomendado Flagship (Groq)',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Inferencia ultra rápida (~300 tokens/segundo) con la máxima capacidad del modelo 70B de Meta.',
      specs: '70B Parámetros • Contexto 128k • Groq LPU Free Tier',
      freeTier: true,
      recommended: true,
    },
    {
      id: 'llama-3.1-8b-instant',
      name: 'Llama 3.1 8B Instant',
      badge: '⚡ Inferencia Instantánea (~700 t/s)',
      badgeClass: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30',
      description: 'Velocidad de respuesta instantánea para brainstorming y retroalimentación inmediata.',
      specs: '8B Parámetros • Contexto 128k • Groq LPU Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'deepseek-r1-distill-llama-70b',
      name: 'DeepSeek R1 Distill Llama 70B',
      badge: '🧠 Razonamiento Acelerado LPU',
      badgeClass: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30',
      description: 'Razonamiento lógico paso a paso combinado con la ultra velocidad de los chips LPU de Groq.',
      specs: '70B Parámetros • Groq LPU • Free Tier',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'mixtral-8x7b-32768',
      name: 'Mixtral 8x7B (32k)',
      badge: '⚖️ Mixture of Experts',
      badgeClass: 'bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30',
      description: 'Excelente fluidez en redacción en español y contexto de 32k tokens.',
      specs: 'Mixtral MoE • Contexto 32k • Groq LPU',
      freeTier: true,
      recommended: false,
    },
  ],

  openai: [
    {
      id: 'gpt-4o',
      name: 'OpenAI GPT-4o',
      badge: '👑 Flagship Omni',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Modelo de referencia multimodal de OpenAI con alta capacidad de comprensión y redacción.',
      specs: 'OpenAI • Contexto 128k • Requiere Clave OpenAI',
      freeTier: false,
      recommended: true,
    },
    {
      id: 'gpt-4o-mini',
      name: 'OpenAI GPT-4o Mini',
      badge: '⚡ Rápido y Económico',
      badgeClass: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30',
      description: 'Gran balance de rapidez y coste para borradores y consultas RAG frecuentes.',
      specs: 'OpenAI • Contexto 128k • Requiere Clave OpenAI',
      freeTier: false,
      recommended: false,
    },
    {
      id: 'o3-mini',
      name: 'OpenAI o3-mini',
      badge: '🧠 Razonamiento Académico & STEM',
      badgeClass: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30',
      description: 'Capacidad de deducción avanzada para metodología cuantitativa, contraste de hipótesis y diseño experimental.',
      specs: 'OpenAI • Contexto 200k • Requiere Clave OpenAI',
      freeTier: false,
      recommended: false,
    },
  ],

  nvidia_nim: [
    {
      id: 'meta/llama-3.3-70b-instruct',
      name: 'NVIDIA Llama 3.3 70B Instruct',
      badge: '⭐ Optimizado TensorRT',
      badgeClass: 'bg-green-500/15 text-green-600 dark:text-green-400 border border-green-500/30',
      description: 'Acelerado por la arquitectura TensorRT-LLM de NVIDIA con alta fidelidad estructural y citas APA 7.',
      specs: '70B Parámetros • NVIDIA NIM • Cuota de prueba gratuita',
      freeTier: true,
      recommended: true,
    },
    {
      id: 'nvidia/llama-3.1-nemotron-70b-instruct',
      name: 'NVIDIA Nemotron 70B Instruct',
      badge: '🎯 Formato Estricto & JSON',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Afinado por NVIDIA para máxima adherencia a esquemas, directrices académicas y estructuración.',
      specs: '70B Parámetros • NVIDIA NIM • Cuota de prueba',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'mistralai/mistral-large-2-instruct',
      name: 'Mistral Large 2 (123B)',
      badge: '🌐 Prosa en Español Formal',
      badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30',
      description: 'Excelente dominio del español académico y redacción de discusiones y marcos teóricos.',
      specs: '123B Parámetros • NVIDIA NIM • Cuota de prueba',
      freeTier: true,
      recommended: false,
    },
  ],

  ollama: [
    {
      id: 'llama3.3:70b',
      name: 'Llama 3.3 70B',
      badge: '🏆 Calidad Máxima Local',
      badgeClass: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/30',
      description: 'Máxima capacidad local 100% privada y offline. Requiere GPU con 24GB+ VRAM o 64GB RAM.',
      specs: '70B Parámetros • Ollama Local • 100% Offline & Gratis',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'llama3.1:8b',
      name: 'Llama 3.1 8B',
      badge: '⭐ Recomendado para Todo PC',
      badgeClass: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
      description: 'Ligero y veloz. Corre fluidamente en cualquier ordenador o laptop estándar con 8GB-16GB RAM.',
      specs: '8B Parámetros • Ollama Local • 100% Offline & Gratis',
      freeTier: true,
      recommended: true,
    },
    {
      id: 'qwen2.5:7b',
      name: 'Qwen 2.5 7B',
      badge: '🌐 Excelente Español Local',
      badgeClass: 'bg-green-500/15 text-green-600 dark:text-green-400 border border-green-500/30',
      description: 'Gran fluidez en español, redacción de párrafos y formateo de referencias bibliográficas.',
      specs: '7B Parámetros • Ollama Local • 100% Offline & Gratis',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'deepseek-r1:8b',
      name: 'DeepSeek R1 8B Local',
      badge: '🧠 Razonamiento Local',
      badgeClass: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30',
      description: 'Razonamiento deductivo ejecutado 100% en tu máquina sin enviar ningún dato a la nube.',
      specs: '8B Parámetros • Ollama Local • 100% Offline & Gratis',
      freeTier: true,
      recommended: false,
    },
    {
      id: 'mistral:7b',
      name: 'Mistral 7B',
      badge: '📘 Clásico Local',
      badgeClass: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30',
      description: 'Modelo clásico de gran estabilidad para generación de texto estructurado.',
      specs: '7B Parámetros • Ollama Local • 100% Offline & Gratis',
      freeTier: true,
      recommended: false,
    },
  ],
};

/**
 * Helper to retrieve catalog list for a given provider
 */
function getModelsForProvider(provider) {
  return MODEL_CATALOG[provider] || [];
}

/**
 * Find model object by provider and model ID
 */
function findModelDetails(provider, modelId) {
  const models = getModelsForProvider(provider);
  return models.find((m) => m.id === modelId) || null;
}

/**
 * Get default recommended model for a provider
 */
function getRecommendedModelForProvider(provider) {
  const models = getModelsForProvider(provider);
  const rec = models.find((m) => m.recommended);
  return rec ? rec.id : (models[0] ? models[0].id : 'custom');
}
