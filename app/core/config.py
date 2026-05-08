import yaml
from pydantic import BaseModel, Field
from typing import List, Optional

class LLMConfig(BaseModel):
    model: str = "gpt-4o"
    max_tokens: int = 1000
    temperature: float = 0.3

class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379"

class LanguageConfig(BaseModel):
    code: str
    name: str
    sttProvider: str
    sttModelHint: Optional[str] = None
    ttsProvider: str
    ttsVoiceId: str
    promptTemplate: str
    fallbackLang: Optional[str] = None

class AppConfig(BaseModel):
    telephony: str
    speech: str
    crm: str
    commerce: str
    ticketing: str
    languages: List[LanguageConfig]
    skills: List[str] = Field(default_factory=list)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

def load_config(file_path: str) -> AppConfig:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)
