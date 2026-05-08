import asyncio
from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict

class LLMOrchestrator:
    def __init__(self, api_key: str, model: str = 'gpt-4o'):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(self, system_prompt: str, history: List[Dict[str, str]], user_message: str) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        for t in history:
            messages.append({"role": t.get("role"), "content": t.get("content")})
        messages.append({"role": "user", "content": user_message})

        retries = 3
        delay = 1.0

        while retries > 0:
            try:
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    temperature=0.3,
                    max_tokens=1000
                )
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return
            except Exception as e:
                retries -= 1
                print(f"LLM Error: {e}. Retries left: {retries}")
                if retries == 0:
                    raise e
                await asyncio.sleep(delay)
                delay *= 2
