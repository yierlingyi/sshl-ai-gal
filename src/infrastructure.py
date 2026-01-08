import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

class APIClient:
    def __init__(self, api_keys: List[str], base_url: str = "https://api.openai.com/v1"):
        self.api_keys = api_keys
        self.base_url = base_url
        self.current_key_index = 0
        self.client = None
        self._init_client()

    def _get_next_key(self) -> str:
        if not self.api_keys:
            raise ValueError("No API keys provided")
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def _init_client(self):
        # Initialize with the first key. Rotation logic would need to re-instantiate 
        # or update the client if the key changes (OpenAI client is immutable regarding key usually).
        # For simple rotation, we can re-create client on call or just use one key for now.
        # Here we will re-instantiate on each call if we really want rotation, 
        # but for efficiency, let's just use the current key logic.
        pass

    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
        """
        Executes an async call to an LLM provider using OpenAI SDK.
        """
        api_key = self._get_next_key()
        
        # We instantiate per call to support key rotation and dynamic config 
        # (though typically client is long-lived, for rotation simplicity we do this).
        client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[APIClient] Error: {e}")
            raise e
        finally:
            await client.close()

    async def list_models(self) -> List[str]:
        """
        Fetches the list of available models from the API.
        """
        api_key = self._get_next_key()
        client = AsyncOpenAI(api_key=api_key, base_url=self.base_url)
        try:
            response = await client.models.list()
            # Extract model ids
            return [model.id for model in response.data]
        except Exception as e:
            print(f"[APIClient] Error listing models: {e}")
            raise e
        finally:
            await client.close()

class SaveManager:
    @staticmethod
    def save_state(file_path: str, data: Dict[str, Any]):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"[SaveManager] Game state saved to {file_path}")
        except Exception as e:
            print(f"[SaveManager] Failed to save state: {e}")

    @staticmethod
    def load_state(file_path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("[SaveManager] No save file found.")
            return None
        except Exception as e:
            print(f"[SaveManager] Failed to load state: {e}")
            return None
