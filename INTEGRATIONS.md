# VoiceOS AI Integrations & Tool Ecosystem

## 1. Google Gemini API Integration
VoiceOS integrates directly with Google's official Gemini AI models via `ai/gemini_provider.py`. Key architectural highlights:

### 1.1 Model Support
- `gemini-2.5-flash`: Ultra-low latency primary model for real-time speech interaction.
- `gemini-2.5-pro`: Complex reasoning, multi-turn synthesis, and detailed coding tasks.
- `gemini-1.5-flash` & `gemini-1.5-pro`: Resilient fallback tiers.

### 1.2 Streaming Generation
Tokens are streamed directly into the Top Notch dynamic island in real-time. This provides instant visual feedback while the neural TTS engine buffers and speaks sentences with natural pauses.

---

## 2. Omniroute Auto-Failover
When API rate limits, temporary 429 quota spikes, or upstream network latency occurs, Omniroute automatically re-dispatches the prompt to the next fallback model candidate. The failover is 100% silent and preserves conversation context.

---

## 3. Tool Calling Ecosystem (`ai/tools.py`)

### 3.1 Weather Forecast (`weather_forecast`)
- Fetches real-time temperatures, cloud conditions, precipitation, and daily highs/lows using Open-Meteo.
- Formats meteorological output directly into the Top Notch weather card (`Kāsaragod`, `25°C`, `Overcast`, `H:32° L:24°`).

### 3.2 Safe Math Calculator (`calculate`)
- Evaluates mathematical expressions using AST (Abstract Syntax Tree) parsing.
- Safe from code injection: forbids arbitrary execution or system imports.

### 3.3 System Diagnostics (`system_status`)
- Reports real-time CPU percentage, RAM consumption, and platform uptime.
