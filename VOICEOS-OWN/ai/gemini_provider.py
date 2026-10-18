import logging
from typing import Generator, List, Dict, Any, Optional, Callable
from ai.base import AIProvider
from ai.tools import VOICEOS_TOOLS

logger = logging.getLogger("VoiceOS.GeminiProvider")

class GeminiProvider(AIProvider):
    """
    Official Google Gemini API Provider with Omniroute intelligent failover.
    Automatically and silently switches between best available models:
    gemini-3.8-flash -> gemini-3.6-flash -> gemini-3.5-flash-lite -> gemini-2.5-flash -> gemini-2.5-pro -> gemini-1.5-flash.
    
    If a model is unavailable, rate-limited (429), or not responding, it transparently
    routes to the next best model without interrupting or notifying the user.
    """
    AVAILABLE_MODELS = [
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]

    DEFAULT_SYSTEM_INSTRUCTION = (
        "You are VoiceOS, a futuristic, fast, and helpful voice assistant on Windows. "
        "Keep your spoken answers concise, conversational, and direct (1-3 sentences when possible). "
        "When appropriate, utilize tools to answer questions with real-time facts like weather, time, or calculations. "
        "If you use a tool, synthesize the result naturally."
    )

    def __init__(self, api_key: str = "", model_name: str = "gemini-3.8-flash", omniroute: bool = True):
        self.api_key = api_key
        self.model_name = model_name
        self.omniroute = omniroute
        self._client = None
        self._cancelled = False
        self._sdk_mode = "genai" # "genai" or "generativeai"
        self._last_successful_model = model_name
        self._discovered_models: List[str] = []
        if api_key:
            self.initialize(api_key, model_name)

    def initialize(self, api_key: str, model_name: str = "gemini-3.8-flash", **kwargs) -> bool:
        clean_key = api_key.strip()
        if not clean_key:
            logger.warning("Empty Gemini API key provided.")
            return False

        self.api_key = clean_key
        self.model_name = model_name
        self._last_successful_model = model_name

        # Try google.genai first
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_mode = "genai"
            logger.info(f"Gemini client initialized with google.genai SDK (Omniroute active, primary: {self.model_name})")
            return True
        except Exception:
            # Fallback to google.generativeai
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self._client = legacy_genai
                self._sdk_mode = "generativeai"
                logger.info(f"Gemini client initialized with legacy google.generativeai (Omniroute active, primary: {self.model_name})")
                return True
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {e}")
                return False

    def discover_models(self) -> List[str]:
        """
        Dynamically discovers active available models from Google Gemini API.
        Caches discovered models for subsequent candidate queries.
        """
        if self._discovered_models:
            return self._discovered_models

        if not self.api_key:
            return self.AVAILABLE_MODELS

        discovered = []
        try:
            if self._sdk_mode == "genai":
                from google import genai
                client = self._client or genai.Client(api_key=self.api_key)
                pager = client.models.list()
                for m in pager:
                    name = getattr(m, "name", "") or ""
                    clean_name = name.replace("models/", "")
                    if "gemini" in clean_name.lower():
                        discovered.append(clean_name)
            else:
                import google.generativeai as legacy_genai
                for m in legacy_genai.list_models():
                    methods = getattr(m, "supported_generation_methods", []) or []
                    if "generateContent" in methods:
                        clean_name = m.name.replace("models/", "")
                        discovered.append(clean_name)
        except Exception as e:
            logger.warning(f"Dynamic model discovery failed: {e}. Falling back to default list.")

        if discovered:
            self._discovered_models = discovered
            return discovered
        return self.AVAILABLE_MODELS

    def _get_candidate_models(self) -> List[str]:
        """Returns ordered list of models for omniroute failover starting with primary."""
        candidates = [self.model_name]
        for m in self.AVAILABLE_MODELS:
            if m not in candidates:
                candidates.append(m)

        for m in self._discovered_models:
            if m not in candidates:
                candidates.append(m)

        return candidates

    def test_connection(self) -> Dict[str, Any]:
        """
        Validates API key and tests connectivity across the Omniroute pool.
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key configured. Please enter your Gemini API key in Settings."
            }

        candidate_models = self._get_candidate_models() if self.omniroute else [self.model_name]
        last_error = ""

        for candidate in candidate_models:
            try:
                if self._sdk_mode == "genai":
                    from google import genai
                    client = genai.Client(api_key=self.api_key)
                    response = client.models.generate_content(
                        model=candidate,
                        contents="ping"
                    )
                    sample = response.text.strip() if response and response.text else "pong"
                    self._last_successful_model = candidate
                    return {
                        "success": True,
                        "message": f"Connected successfully to Google Gemini ({candidate})!",
                        "sample": sample,
                        "model": candidate
                    }
                else:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=self.api_key)
                    model = legacy_genai.GenerativeModel(candidate)
                    response = model.generate_content("ping", generation_config={"max_output_tokens": 5})
                    self._last_successful_model = candidate
                    return {
                        "success": True,
                        "message": f"Connected successfully to Gemini ({candidate})!",
                        "sample": response.text.strip() if response and response.text else "pong",
                        "model": candidate
                    }
            except Exception as e:
                err_msg = str(e)
                last_error = err_msg
                # If key itself is strictly invalid, no need to cycle through other models
                if "API_KEY_INVALID" in err_msg or "invalid api key" in err_msg.lower():
                    return {"success": False, "error": "Invalid Gemini API Key. Please verify your key from Google AI Studio."}
                logger.warning(f"Omniroute connection test failed for {candidate}: {err_msg}. Trying next model...")

        if "quota" in last_error.lower() or "resource_exhausted" in last_error.lower():
            return {"success": False, "error": "Gemini API quota exceeded across available models. Check your Google AI Studio quota."}
        elif "connection" in last_error.lower() or "timeout" in last_error.lower():
            return {"success": False, "error": f"Network connection error contacting Google Gemini: {last_error}"}
        return {"success": False, "error": f"Gemini connection failed: {last_error}"}

    def generate_response(self, prompt: str,
                          context: Optional[List[Dict[str, str]]] = None,
                          system_instruction: Optional[str] = None,
                          stream: bool = True,
                          tools: Optional[List[Callable]] = None,
                          status_callback: Optional[Callable[[str], None]] = None) -> Generator[Dict[str, Any], None, None]:
        self._cancelled = False
        if not self.api_key:
            yield {
                "type": "error",
                "content": "Gemini API key is not configured. Please set your key in Settings."
            }
            return

        candidate_models = self._get_candidate_models() if self.omniroute else [self.model_name]
        active_tools = tools if tools is not None else VOICEOS_TOOLS
        active_sys_inst = system_instruction or self.DEFAULT_SYSTEM_INSTRUCTION
        last_error_str = ""

        for candidate in candidate_models:
            if self._cancelled:
                return

            yielded_any = False
            try:
                if self._sdk_mode == "genai":
                    from google import genai
                    from google.genai import types
                    client = genai.Client(api_key=self.api_key)

                    contents = []
                    if context:
                        for msg in context:
                            role = "user" if msg.get("role") in ["user", "human"] else "model"
                            contents.append(types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=msg.get("content", ""))]
                            ))
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)]
                    ))

                    config = types.GenerateContentConfig(
                        system_instruction=active_sys_inst,
                        tools=active_tools
                    )

                    if stream:
                        response_stream = client.models.generate_content_stream(
                            model=candidate,
                            contents=contents,
                            config=config
                        )
                        full_text = []
                        for chunk in response_stream:
                            if self._cancelled:
                                yield {"type": "complete", "content": "".join(full_text), "cancelled": True}
                                return

                            if chunk.function_calls:
                                for call in chunk.function_calls:
                                    yielded_any = True
                                    yield {
                                        "type": "tool_call",
                                        "tool_name": call.name,
                                        "input": dict(call.args) if call.args else {}
                                    }

                            if chunk.text:
                                yielded_any = True
                                full_text.append(chunk.text)
                                yield {"type": "chunk", "content": chunk.text}

                        self._last_successful_model = candidate
                        yield {"type": "complete", "content": "".join(full_text)}
                        return # Succeeded!
                    else:
                        response = client.models.generate_content(
                            model=candidate,
                            contents=contents,
                            config=config
                        )
                        self._last_successful_model = candidate
                        yield {"type": "complete", "content": response.text}
                        return # Succeeded!

                else:
                    # Legacy SDK mode
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=self.api_key)
                    model = legacy_genai.GenerativeModel(
                        model_name=candidate,
                        system_instruction=active_sys_inst,
                        tools=active_tools
                    )
                    chat_history = []
                    if context:
                        for msg in context:
                            role = "user" if msg.get("role") in ["user", "human"] else "model"
                            chat_history.append({"role": role, "parts": [msg.get("content", "")]})

                    chat = model.start_chat(history=chat_history)
                    if stream:
                        response = chat.send_message(prompt, stream=True)
                        full_text = []
                        for chunk in response:
                            if self._cancelled:
                                yield {"type": "complete", "content": "".join(full_text), "cancelled": True}
                                return
                            text_chunk = chunk.text
                            if text_chunk:
                                yielded_any = True
                                full_text.append(text_chunk)
                                yield {"type": "chunk", "content": text_chunk}

                        self._last_successful_model = candidate
                        yield {"type": "complete", "content": "".join(full_text)}
                        return # Succeeded!
                    else:
                        response = chat.send_message(prompt, stream=False)
                        self._last_successful_model = candidate
                        yield {"type": "complete", "content": response.text}
                        return # Succeeded!

            except Exception as e:
                err_str = str(e)
                last_error_str = err_str
                logger.warning(f"Omniroute: model '{candidate}' encountered issue: {err_str}. Silently failing over...")

                # If key is completely invalid, fail immediately
                if "API_KEY_INVALID" in err_str or "invalid api key" in err_str.lower():
                    yield {"type": "error", "content": "Invalid Gemini API Key. Please update your key in Settings."}
                    return

                # If we already yielded parts of a stream and it aborted mid-stream,
                # yield a reset signal so the consumer clears any partial buffer before fallback stream begins!
                if yielded_any:
                    logger.info(f"Omniroute: resetting buffer after mid-stream failure on '{candidate}'")
                    yield {"type": "reset", "reason": f"Failover from {candidate}"}
                    yielded_any = False

                if status_callback:
                    try:
                        status_callback("Trying fallback model...")
                    except Exception:
                        pass

                # Otherwise, continue loop silently to the next model!
                continue

        # If all candidates exhausted
        logger.error(f"Omniroute exhausted all candidates: {candidate_models}. Last error: {last_error_str}")
        if "resource_exhausted" in last_error_str.lower() or "429" in last_error_str:
            msg = "Gemini rate limits exceeded across all available models. Please try again shortly."
        elif "quota" in last_error_str.lower():
            msg = "Gemini API quota exceeded. Please check your quota on Google AI Studio."
        else:
            msg = f"Gemini response could not be generated: {last_error_str}"
        yield {"type": "error", "content": msg}

    def cancel_request(self):
        self._cancelled = True

    @property
    def active_model(self) -> str:
        return self._last_successful_model
