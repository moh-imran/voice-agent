import os
from jinja2 import Environment, FileSystemLoader

class PromptTemplateSystem:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptTemplateSystem, cls).__new__(cls)
            prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'prompts')
            cls._instance.env = Environment(loader=FileSystemLoader(prompts_dir))
        return cls._instance

    @classmethod
    def get_instance(cls) -> "PromptTemplateSystem":
        if cls._instance is None:
            cls()
        return cls._instance

    def render(self, lang: str, context: dict) -> str:
        template_name = f"system.{lang}.jinja2"
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            print(f"Warning: Template {template_name} not found, falling back to en-US. Error: {e}")
            try:
                fallback = self.env.get_template("system.en-US.jinja2")
                return fallback.render(**context)
            except Exception:
                return f"You are a helpful voice agent. Language: {lang}. Context: {context}"
