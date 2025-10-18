import os
from openai import AzureOpenAI
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("TextEmbeddingTool")
class TextEmbeddingTool(BaseTool):
    """
    Tool to generate text embeddings using Azure OpenAI.
    """

    def __init__(self, tool_config):
        super().__init__(tool_config)
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        )
        self.model = tool_config.get("model", "text-embedding-3-large")

    def validate_input(self, **kwargs):
        """Validate input parameters."""
        text = kwargs.get("text")

        if not text:
            raise ValueError("Text is required")

        if isinstance(text, str):
            if len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
        elif isinstance(text, list):
            if len(text) == 0:
                raise ValueError("Text list cannot be empty")
            for item in text:
                if not isinstance(item, str):
                    raise ValueError("All items in text list must be strings")
                if len(item.strip()) == 0:
                    raise ValueError("Text items cannot be empty")
        else:
            raise ValueError("Text must be a string or list of strings")

    def run(self, arguments):
        text = arguments.get("text")
        if not text:
            return {"error": "`text` parameter is required."}
        return self._get_embedding(text)

    def _get_embedding(self, text):
        try:
            # OpenAI API supports both single string and list of strings
            response = self.client.embeddings.create(input=text, model=self.model)
            
            # If single text, return single embedding
            if isinstance(text, str):
                embedding = response.data[0].embedding
                return {"embedding": embedding}
            # If list of texts, return list of embeddings
            else:
                embeddings = [item.embedding for item in response.data]
                return {"embedding": embeddings}
        except Exception as e:
            return {"error": f"Failed to generate embedding: {str(e)}"}

