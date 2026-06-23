import traceback
from openai import OpenAI
from config import Config

def _build_model_list(preferred_model: str = None) -> list:
    """Return model list with preferred model first (if given), falling back to full OR_MODELS chain."""
    if preferred_model and preferred_model != "auto":
        rest = [m for m in Config.OR_MODELS if m != preferred_model]
        return [preferred_model] + rest
    return Config.OR_MODELS


def query_openrouter(prompt: str, preferred_model: str = None) -> str:
    """Send a prompt to OpenRouter, cycling through fallback models on rate-limit."""
    last_error = None
    models = _build_model_list(preferred_model)
    for model in models:
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
                timeout=Config.OR_TIMEOUT,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.85,
            )
            print(f"[OpenRouter] Used model: {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "400" in err_str or "rate" in err_str.lower()
                    or "not a valid model" in err_str.lower()
                    or "timeout" in err_str.lower() or "timed out" in err_str.lower()):
                print(f"[OpenRouter] {model} skipped ({type(e).__name__}), trying next...")
                last_error = e
                continue
            print("[OpenRouter ERROR]", type(e).__name__, err_str)
            traceback.print_exc()
            raise RuntimeError(f"OpenRouter error — {type(e).__name__}: {e}")
    raise RuntimeError(f"All models rate-limited. Try again in 30 seconds. Last error: {last_error}")


def query_openrouter_stream(prompt: str, preferred_model: str = None):
    """Send a prompt to OpenRouter, streaming the response chunks, cycling through fallbacks on error."""
    models = _build_model_list(preferred_model)
    last_error = None
    for model in models:
        yielded_any = False
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
                timeout=Config.OR_TIMEOUT,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.85,
                stream=True,
            )
            print(f"[OpenRouter] Streaming from model: {model}")
            in_thinking = False
            for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    
                    reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
                    if reasoning:
                        if not in_thinking:
                            yield "<think>"
                            in_thinking = True
                        yield reasoning
                        yielded_any = True
                    else:
                        if in_thinking:
                            yield "</think>"
                            in_thinking = False
                        
                        content = getattr(delta, "content", None)
                        if content:
                            yield content
                            yielded_any = True
            
            if in_thinking:
                yield "</think>"
            
            if not yielded_any:
                print(f"[OpenRouter] {model} returned empty response, trying next model...")
                last_error = Exception(f"Empty response from {model}")
                continue

            return
        except Exception as e:
            err_str = str(e)
            if yielded_any:
                print(f"[OpenRouter ERROR] Mid-stream failure on {model}: {err_str}")
                raise
                
            if ("429" in err_str or "400" in err_str or "rate" in err_str.lower()
                    or "not a valid model" in err_str.lower()
                    or "timeout" in err_str.lower() or "timed out" in err_str.lower()):
                print(f"[OpenRouter] {model} skipped ({type(e).__name__}) during stream initialization, trying next...")
                last_error = e
                continue
            print("[OpenRouter ERROR]", type(e).__name__, err_str)
            traceback.print_exc()
            raise RuntimeError(f"OpenRouter error — {type(e).__name__}: {e}")
    raise RuntimeError(f"All models rate-limited. Try again in 30 seconds. Last error: {last_error}")


def query_openrouter_extraction(prompt: str, preferred_model: str = None) -> str:
    """Special extraction helper with low temperature and timeout optimized for background jobs."""
    # Use Llama 3.3 70B instruction as primary extraction model
    models = ["meta-llama/llama-3.3-70b-instruct"]
    if preferred_model and preferred_model != "auto":
        models.insert(0, preferred_model)
    # Append the rest of config options
    for m in Config.OR_MODELS:
        if m not in models:
            models.append(m)
            
    last_error = None
    for model in models:
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=Config.OPENROUTER_API_KEY,
                timeout=20,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1,
            )
            print(f"[OpenRouter Extraction] Used model: {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "400" in err_str or "rate" in err_str.lower()
                    or "not a valid model" in err_str.lower()
                    or "timeout" in err_str.lower() or "timed out" in err_str.lower()):
                print(f"[OpenRouter Extraction] {model} skipped ({type(e).__name__}), trying next...")
                last_error = e
                continue
            print("[OpenRouter Extraction ERROR]", type(e).__name__, err_str)
            raise RuntimeError(f"OpenRouter extraction error — {type(e).__name__}: {e}")
    raise RuntimeError(f"All extraction models failed/rate-limited. Last error: {last_error}")
