from mcdreforged.api.all import *
from openai import OpenAI
import time

config = None

# 翻译缓存
translation_cache = {}


class LLM:
    @staticmethod
    def get_client():
        if config is None:
            server = ServerInterface.get_instance()
            server.logger.error("[LLM Translator] Config not initialized")
            raise Exception("Config not initialized")
        client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        return client

    @staticmethod
    def use(message):
        server = ServerInterface.get_instance()
        if config is None:
            server.logger.error("[LLM Translator] Config not initialized")
            return "[Translation Error] Config not initialized"
        
        # 检查缓存
        if config.enable_translation_cache:
            cache_key = f"{message}_{config.first_language}_{config.secondary_language}"
            if cache_key in translation_cache:
                server.logger.debug(f"[LLM Translator] Using cached translation for: {message}")
                return translation_cache[cache_key]
        
        max_retries = config.max_retry_attempts
        retry_delay = config.retry_delay
        
        for attempt in range(max_retries):
            try:
                if config.enable_system_prompt:
                    system_content = config.system_prompt.format(
                        first_language=config.first_language,
                        secondary_language=config.secondary_language
                    )
                    response = LLM.get_client().chat.completions.create(
                        model=config.model,
                        messages=[
                            {"role": "system","content": system_content},
                            {"role": "user", "content": message},
                        ],
                        stream=False,
                    )
                else:
                    response = LLM.get_client().chat.completions.create(
                        model=config.model,
                        messages=[
                            {"role": "user", "content": message}
                        ],
                        stream=False,
                    )
                translation = response.choices[0].message.content
                
                # 更新缓存
                if config.enable_translation_cache:
                    cache_key = f"{message}_{config.first_language}_{config.secondary_language}"
                    translation_cache[cache_key] = translation
                    
                    # 保持缓存大小
                    if len(translation_cache) > config.translation_cache_size:
                        # 删除最早的缓存项
                        oldest_key = next(iter(translation_cache))
                        del translation_cache[oldest_key]
                        server.logger.debug("[LLM Translator] Cache size exceeded, removed oldest item")
                
                return translation
            except Exception as e:
                server.logger.error(f"[LLM Translator] API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    server.logger.info(f"[LLM Translator] Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return f"[Translation Error] API call failed after {max_retries} attempts: {e}"

    @staticmethod
    def clear_cache():
        global translation_cache
        translation_cache = {}
        server = ServerInterface.get_instance()
        server.logger.info("[LLM Translator] Translation cache cleared")
