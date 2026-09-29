from litellm.integrations.custom_logger import CustomLogger

class ClampTokensHandler(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        # Groq free tier enforces an OTPM (output tokens per minute) limit of 1000 for qwen/qwen3.8-27b.
        # Requests asking for > 1000 tokens (or default uncapped) are rejected with:
        # "Limit 1000, Requested XXXX. The request's expected output tokens exceed the enforced limit; reduce max_tokens".
        # We cap max_tokens to 800 to ensure every request stays within Groq's 1000 OTPM limit.
        model = str(data.get("model", "")).lower()
        if "qwen" in model:
            data["max_tokens"] = 800
            if "max_completion_tokens" in data:
                data["max_completion_tokens"] = 800
        else:
            if data.get("max_tokens") is not None and data["max_tokens"] > 8192:
                data["max_tokens"] = 4096
            if data.get("max_completion_tokens") is not None and data["max_completion_tokens"] > 8192:
                data["max_completion_tokens"] = 4096
        return data

proxy_handler_instance = ClampTokensHandler()
