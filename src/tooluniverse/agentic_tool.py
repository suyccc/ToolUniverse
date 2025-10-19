from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .base_tool import BaseTool
from .tool_registry import register_tool
from .logging_config import get_logger
from .llm_clients import AzureOpenAIClient, GeminiClient, OpenRouterClient, VLLMClient


# Global default fallback configuration
DEFAULT_FALLBACK_CHAIN = [
    {"api_type": "CHATGPT", "model_id": "gpt-4o-1120"},
    {"api_type": "OPENROUTER", "model_id": "openai/gpt-4o"},
    {"api_type": "GEMINI", "model_id": "gemini-2.0-flash"},
]

# API key environment variable mapping
API_KEY_ENV_VARS = {
    "CHATGPT": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
    "OPENROUTER": ["OPENROUTER_API_KEY"],
    "GEMINI": ["GEMINI_API_KEY"],
    "VLLM": [],  # VLLM_SERVER_URL is optional; not required for batch inference
}


@register_tool("AgenticTool")
class AgenticTool(BaseTool):
    """Generic wrapper around LLM prompting supporting JSON-defined configs with prompts and input arguments."""

    STREAM_FLAG_KEY = "_tooluniverse_stream"

    @staticmethod
    def has_any_api_keys() -> bool:
        """Return True when at least one API type has all required keys set."""

        return any(
            all(os.getenv(var) for var in required_vars)
            for required_vars in API_KEY_ENV_VARS.values()
        )

    def __init__(self, tool_config: Dict[str, Any]):
        super().__init__(tool_config)
        self.logger = get_logger("AgenticTool")
        self.name: str = tool_config.get("name", "")
        self._prompt_template: str = tool_config.get("prompt", "")
        self._input_arguments: List[str] = tool_config.get("input_arguments", [])

        # Extract required arguments from parameter schema
        parameter_info = tool_config.get("parameter", {})
        self._required_arguments: List[str] = parameter_info.get("required", [])
        self._argument_defaults: Dict[str, str] = {}

        # Set up default values for optional arguments
        properties = parameter_info.get("properties", {})
        for arg in self._input_arguments:
            if arg not in self._required_arguments:
                prop_info = properties.get(arg, {})
                if "default" in prop_info:
                    self._argument_defaults[arg] = prop_info["default"]

        # Get configuration from nested 'configs' dict or fallback to top-level
        configs = tool_config.get("configs", {})

        # Helper function to get config values with fallback
        def get_config(key: str, default: Any) -> Any:
            return configs.get(key, tool_config.get(key, default))

        # LLM configuration
        self._api_type: str = get_config("api_type", "CHATGPT")
        self._model_id: str = get_config("model_id", "o1-mini")
        self._temperature: Optional[float] = get_config("temperature", 0.1)
        # Get max_new_tokens from config; if None, client will resolve per model/env
        self._max_new_tokens: Optional[int] = get_config("max_new_tokens", None)
        if self._max_new_tokens is not None:
            try:
                self._max_new_tokens = int(self._max_new_tokens)
            except (TypeError, ValueError):
                self.logger.warning(
                    "Invalid max_new_tokens value '%s' for tool '%s'; defaulting to None.",
                    self._max_new_tokens,
                    self.name,
                )
                self._max_new_tokens = None
        raw_vllm_args = get_config("vllm_specific_args", None)
        if raw_vllm_args is None:
            self._vllm_specific_args: Dict[str, Any] = {}
        elif isinstance(raw_vllm_args, dict):
            self._vllm_specific_args = raw_vllm_args.copy()
        else:
            self.logger.warning(
                "Ignoring vllm_specific_args for tool '%s'; expected dict but got %s.",
                self.name,
                type(raw_vllm_args).__name__,
            )
            self._vllm_specific_args = {}
        self._return_json: bool = get_config("return_json", False)
        self._max_retries: int = get_config("max_retries", 5)
        self._retry_delay: int = get_config("retry_delay", 5)
        self.return_metadata: bool = get_config("return_metadata", True)
        self._validate_api_key: bool = get_config("validate_api_key", True)

        # API fallback configuration
        self._fallback_api_type: Optional[str] = get_config("fallback_api_type", None)
        self._fallback_model_id: Optional[str] = get_config("fallback_model_id", None)

        # Global fallback configuration
        self._use_global_fallback: bool = get_config("use_global_fallback", True)
        self._global_fallback_chain: List[Dict[str, str]] = (
            self._get_global_fallback_chain()
        )

        # Gemini model configuration (optional; env override)
        self._gemini_model_id: str = get_config(
            "gemini_model_id",
            __import__("os").getenv("GEMINI_MODEL_ID", "gemini-2.0-flash"),
        )
        
        # Extract output_schema for structured outputs (used with vLLM)
        self._output_schema: Optional[Dict[str, Any]] = tool_config.get("output_schema")

        # Validation
        if not self._prompt_template:
            raise ValueError("AgenticTool requires a 'prompt' in the configuration.")
        if not self._input_arguments:
            raise ValueError(
                "AgenticTool requires 'input_arguments' in the configuration."
            )

        # Validate temperature range (skip if None)
        if (
            isinstance(self._temperature, (int, float))
            and not 0 <= self._temperature <= 2
        ):
            self.logger.warning(
                f"Temperature {self._temperature} is outside recommended range [0, 2]"
            )

        # Validate model compatibility
        self._validate_model_config()

        # Initialize the provider client
        self._llm_client = None
        self._initialization_error = None
        self._is_available = False
        self._current_api_type = None
        self._current_model_id = None

        # Try primary API first, then fallback if configured
        self._try_initialize_api()

    def _get_global_fallback_chain(self) -> List[Dict[str, str]]:
        """Get the global fallback chain from environment or use default."""
        # Check environment variable for custom fallback chain
        env_chain = os.getenv("AGENTIC_TOOL_FALLBACK_CHAIN")
        if env_chain:
            try:
                chain = json.loads(env_chain)
                if isinstance(chain, list) and all(
                    isinstance(item, dict) and "api_type" in item and "model_id" in item
                    for item in chain
                ):
                    return chain
                else:
                    self.logger.warning(
                        "Invalid fallback chain format in environment variable"
                    )
            except json.JSONDecodeError:
                self.logger.warning(
                    "Invalid JSON in AGENTIC_TOOL_FALLBACK_CHAIN environment variable"
                )

        return DEFAULT_FALLBACK_CHAIN.copy()

    def _try_initialize_api(self):
        """Try to initialize the primary API, fallback to secondary if configured."""
        for index, (api_type, model_id, reason) in enumerate(self._iter_api_candidates()):
            if index == 0:
                self.logger.debug(
                    "Initializing primary API for %s: %s (%s)",
                    self.name,
                    api_type,
                    model_id,
                )
            else:
                self.logger.info(
                    "Attempting %s for %s: %s (%s)",
                    reason,
                    self.name,
                    api_type,
                    model_id,
                )

            if self._try_api(api_type, model_id):
                return

        self.logger.warning(
            "Tool '%s' failed to initialize with all available APIs",
            self.name,
        )

    def _iter_api_candidates(self) -> List[Tuple[str, str, str]]:
        """Yield API/model choices in preference order with a short reason."""

        candidates: List[Tuple[str, str, str]] = [(self._api_type, self._model_id, "primary")]
        seen = {(self._api_type, self._model_id)}

        if self._fallback_api_type and self._fallback_model_id:
            fallback = (self._fallback_api_type, self._fallback_model_id)
            if fallback not in seen:
                candidates.append((*fallback, "explicit fallback"))
                seen.add(fallback)

        if self._use_global_fallback:
            for index, fallback in enumerate(self._global_fallback_chain, start=1):
                api_type = fallback.get("api_type")
                model_id = fallback.get("model_id")
                if not api_type or not model_id:
                    continue
                candidate_key = (api_type, model_id)
                if candidate_key in seen:
                    continue
                candidates.append((api_type, model_id, f"global fallback #{index}"))
                seen.add(candidate_key)

        return candidates

    def _try_api(
        self, api_type: str, model_id: str, server_url: Optional[str] = None
    ) -> bool:
        """Try to initialize a specific API and model."""
        try:
            if api_type == "CHATGPT":
                self._llm_client = AzureOpenAIClient(model_id, None, self.logger)
            elif api_type == "OPENROUTER":
                self._llm_client = OpenRouterClient(model_id, self.logger)
            elif api_type == "GEMINI":
                self._llm_client = GeminiClient(model_id, self.logger)
            elif api_type == "VLLM":
                # Server URL is optional - only needed for API-based inference, not batch
                server_url = os.getenv("VLLM_SERVER_URL")
                if (
                    self._max_new_tokens is not None
                    and isinstance(self._vllm_specific_args, dict)
                    and "max_model_len" not in self._vllm_specific_args
                ):
                    # Ensure remote engine requests mirror per-tool token cap when possible.
                    self._vllm_specific_args["max_model_len"] = self._max_new_tokens
                self._llm_client = VLLMClient(
                    model_id,
                    server_url,
                    self.logger,
                    self._vllm_specific_args,
                )
            else:
                raise ValueError(f"Unsupported API type: {api_type}")

            # Test API key validity after initialization (if enabled)
            if self._validate_api_key:
                self._llm_client.test_api()
                self.logger.debug(
                    f"Successfully initialized {api_type} model: {model_id}"
                )
            else:
                self.logger.info("API key validation skipped (validate_api_key=False)")

            self._is_available = True
            self._current_api_type = api_type
            self._current_model_id = model_id
            self._initialization_error = None

            if api_type != self._api_type or model_id != self._model_id:
                self.logger.info(
                    f"Using fallback API: {api_type} with model {model_id} "
                    f"(originally configured: {self._api_type} with {self._model_id})"
                )

            return True

        except Exception as e:
            error_msg = f"Failed to initialize {api_type} model {model_id}: {str(e)}"
            self.logger.warning(error_msg)
            self._initialization_error = error_msg
            return False

    # ------------------------------------------------------------------ LLM utilities -----------
    def _validate_model_config(self):
        supported_api_types = ["CHATGPT", "OPENROUTER", "GEMINI", "VLLM"]
        if self._api_type not in supported_api_types:
            raise ValueError(
                f"Unsupported API type: {self._api_type}. Supported types: {supported_api_types}"
            )
        if self._max_new_tokens is not None and self._max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive or None")

    def _model_metadata(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "api_type": self._api_type,
            "model_id": self._model_id,
            "temperature": self._temperature,
            "max_new_tokens": self._max_new_tokens,
        }
        if self._api_type == "VLLM" and self._vllm_specific_args:
            info["vllm_specific_args"] = self._vllm_specific_args
        return info

    # ------------------------------------------------------------------ public API --------------
    def run(
        self,
        arguments: Union[Dict[str, Any], List[Dict[str, Any]]],
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        start_time = datetime.now()

        # Batch execution path: accept list of argument dictionaries
        if isinstance(arguments, list):
            return self._run_batch(arguments, stream_callback, start_time)

        raw_arguments = dict(arguments or {})
        basic_snapshot = {arg: raw_arguments.get(arg) for arg in self._input_arguments}

        # Check if tool is available before attempting to run
        if not self._is_available:
            error_msg = f"Tool '{self.name}' is not available due to initialization error: {self._initialization_error}"
            self.logger.error(error_msg)
            if self.return_metadata:
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "ToolUnavailable",
                    "metadata": {
                        "prompt_used": "Tool unavailable",
                        "input_arguments": basic_snapshot,
                        "model_info": {
                            "api_type": self._api_type,
                            "model_id": self._model_id,
                        },
                        "execution_time_seconds": 0,
                        "timestamp": start_time.isoformat(),
                    },
                }
            else:
                return f"error: {error_msg} error_type: ToolUnavailable"

        prepared_input = self._prepare_single_input(raw_arguments)
        stream_flag = prepared_input["stream_flag"]
        streaming_requested = stream_flag or stream_callback is not None
        messages = prepared_input["messages"]
        custom_format = prepared_input["custom_format"]
        formatted_prompt = prepared_input["formatted_prompt"]
        input_snapshot = prepared_input["input_snapshot"]

        try:
            # Delegate to client; client handles provider-specific logic
            response = None

            streaming_permitted = (
                streaming_requested and not self._return_json and custom_format is None
            )

            if streaming_permitted and hasattr(self._llm_client, "infer_stream"):
                try:
                    chunks_collected: List[str] = []
                    stream_iter = self._llm_client.infer_stream(
                        messages=messages,
                        temperature=self._temperature,
                        max_tokens=self._max_new_tokens,
                        return_json=self._return_json,
                        custom_format=custom_format,
                        max_retries=self._max_retries,
                        retry_delay=self._retry_delay,
                    )
                    for chunk in stream_iter:
                        if not chunk:
                            continue
                        chunks_collected.append(chunk)
                        self._emit_stream_chunk(chunk, stream_callback)
                    if chunks_collected:
                        response = "".join(chunks_collected)
                except Exception as stream_error:  # noqa: BLE001
                    self.logger.warning(
                        f"Streaming failed for tool '{self.name}': {stream_error}. Falling back to buffered response."
                    )
                    response = None

            if response is None:
                response = self._llm_client.infer(
                    messages=messages,
                    temperature=self._temperature,
                    max_tokens=self._max_new_tokens,
                    return_json=self._return_json,
                    custom_format=custom_format,
                    max_retries=self._max_retries,
                    retry_delay=self._retry_delay,
                )

                if streaming_requested and response:
                    for chunk in self._iter_chunks(response):
                        self._emit_stream_chunk(chunk, stream_callback)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            if self.return_metadata:
                return {
                    "success": True,
                    "result": response,
                    "metadata": {
                        "prompt_used": (
                            formatted_prompt
                            if len(formatted_prompt) < 1000
                            else f"{formatted_prompt[:1000]}..."
                        ),
                        "input_arguments": input_snapshot,
                        "model_info": self._model_metadata(),
                        "execution_time_seconds": execution_time,
                        "timestamp": start_time.isoformat(),
                    },
                }
            else:
                return response

        except Exception as e:  # noqa: BLE001
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            self.logger.error(f"Error executing {self.name}: {str(e)}")
            if self.return_metadata:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "metadata": {
                        "prompt_used": (
                            formatted_prompt
                            if "formatted_prompt" in locals()
                            else "Failed to format prompt"
                        ),
                        "input_arguments": {
                            arg: input_snapshot.get(arg) for arg in self._input_arguments
                        },
                        "model_info": self._model_metadata(),
                        "execution_time_seconds": execution_time,
                        "timestamp": start_time.isoformat(),
                    },
                }
            else:
                from .utils import format_error_response

                return format_error_response(
                    e,
                    self.name,
                    {
                        "prompt_used": (
                            formatted_prompt
                            if "formatted_prompt" in locals()
                            else "Failed to format prompt"
                        ),
                        "input_arguments": {
                            arg: input_snapshot.get(arg) for arg in self._input_arguments
                        },
                        "model_info": self._model_metadata(),
                        "execution_time_seconds": execution_time,
                    },
                )

    @staticmethod
    def _iter_chunks(text: str, size: int = 800):
        if not text:
            return
        for idx in range(0, len(text), size):
            yield text[idx : idx + size]

    def _emit_stream_chunk(
        self, chunk: Optional[str], stream_callback: Optional[Callable[[str], None]]
    ) -> None:
        if not stream_callback or not chunk:
            return
        try:
            stream_callback(chunk)
        except Exception as callback_error:  # noqa: BLE001
            # Streaming callbacks should not break tool execution; log and continue
            self.logger.debug(
                f"Stream callback for tool '{self.name}' raised an exception: {callback_error}"
            )

    def _prepare_single_input(self, raw_arguments: Dict[str, Any]) -> Dict[str, Any]:
        arguments = dict(raw_arguments or {})
        stream_flag = bool(arguments.pop(self.STREAM_FLAG_KEY, False))

        missing_required_args = [
            arg for arg in self._required_arguments if arg not in arguments
        ]
        if missing_required_args:
            raise ValueError(
                f"Missing required input arguments: {missing_required_args}"
            )

        for arg in self._input_arguments:
            if arg not in arguments:
                arguments[arg] = self._argument_defaults.get(arg, "")

        self._validate_arguments(arguments)
        formatted_prompt = self._format_prompt(arguments)
        messages = [{"role": "user", "content": formatted_prompt}]

        input_snapshot = {arg: arguments.get(arg) for arg in self._input_arguments}

        return {
            "arguments": arguments,
            "stream_flag": stream_flag,
            "messages": messages,
            "custom_format": arguments.get("response_format"),
            "formatted_prompt": formatted_prompt,
            "input_snapshot": input_snapshot,
        }

    def _run_batch(
        self,
        batch_arguments: List[Dict[str, Any]],
        stream_callback: Optional[Callable[[str], None]],
        start_time: datetime,
    ) -> Dict[str, Any]:
        if stream_callback is not None:
            raise ValueError("Streaming callbacks are not supported for batch inference")
        if not isinstance(batch_arguments, list):
            raise ValueError("Batch arguments must be provided as a list of dictionaries")

        raw_arguments_list: List[Dict[str, Any]] = []
        for idx, item in enumerate(batch_arguments):
            if not isinstance(item, dict):
                raise ValueError(f"Batch input at index {idx} must be a dictionary")
            raw_arguments_list.append(dict(item))

        basic_snapshots = [
            {arg: raw.get(arg) for arg in self._input_arguments}
            for raw in raw_arguments_list
        ]

        if not self._is_available:
            error_msg = (
                f"Tool '{self.name}' is not available due to initialization error:"
                f" {self._initialization_error}"
            )
            self.logger.error(error_msg)
            if self.return_metadata:
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "ToolUnavailable",
                    "metadata": {
                        "prompt_used": "Tool unavailable",
                        "input_arguments": basic_snapshots,
                        "model_info": {
                            "api_type": self._api_type,
                            "model_id": self._model_id,
                        },
                        "batch_size": len(raw_arguments_list),
                        "execution_time_seconds": 0,
                        "timestamp": start_time.isoformat(),
                    },
                }
            return f"error: {error_msg} error_type: ToolUnavailable"

        prepared_items = [
            self._prepare_single_input(raw_arguments) for raw_arguments in raw_arguments_list
        ]

        if any(item["stream_flag"] for item in prepared_items):
            raise ValueError("Streaming flags are not supported in batch mode")

        messages_batch = [item["messages"] for item in prepared_items]
        custom_formats = [item["custom_format"] for item in prepared_items]
        custom_formats_param = (
            custom_formats if any(cf is not None for cf in custom_formats) else None
        )

        try:
            responses = self._llm_client.infer_batch(
                messages_batch=messages_batch,
                temperature=self._temperature,
                max_tokens=self._max_new_tokens,
                return_json=self._return_json,
                custom_formats=custom_formats_param,
                json_schema=self._output_schema,
                max_retries=self._max_retries,
                retry_delay=self._retry_delay,
            )

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            if self.return_metadata:
                items_metadata = []
                for idx, item in enumerate(prepared_items):
                    prompt_preview = item["formatted_prompt"]
                    if len(prompt_preview) >= 1000:
                        prompt_preview = f"{prompt_preview[:1000]}..."
                    items_metadata.append(
                        {
                            "index": idx,
                            "prompt_used": prompt_preview,
                            "input_arguments": item["input_snapshot"],
                        }
                    )

                return {
                    "success": True,
                    "result": responses,
                    "metadata": {
                        "items": items_metadata,
                        "batch_size": len(prepared_items),
                        "model_info": self._model_metadata(),
                        "execution_time_seconds": execution_time,
                        "timestamp": start_time.isoformat(),
                    },
                }

            return responses

        except Exception as e:  # noqa: BLE001
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            self.logger.error(f"Batch execution error for {self.name}: {str(e)}")
            prompt_previews = []
            for item in prepared_items:
                prompt_text = item["formatted_prompt"]
                if len(prompt_text) >= 1000:
                    prompt_text = f"{prompt_text[:1000]}..."
                prompt_previews.append(prompt_text)

            if self.return_metadata:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "metadata": {
                        "prompt_used": prompt_previews,
                        "input_arguments": [
                            item["input_snapshot"] for item in prepared_items
                        ],
                        "model_info": self._model_metadata(),
                        "batch_size": len(prepared_items),
                        "execution_time_seconds": execution_time,
                        "timestamp": start_time.isoformat(),
                    },
                }

            from .utils import format_error_response

            return format_error_response(
                e,
                self.name,
                {
                    "prompt_used": prompt_previews,
                    "input_arguments": [
                        item["input_snapshot"] for item in prepared_items
                    ],
                    "model_info": self._model_metadata(),
                    "batch_size": len(prepared_items),
                    "execution_time_seconds": execution_time,
                },
            )

    # ------------------------------------------------------------------ helpers -----------------
    def _validate_arguments(self, arguments: Dict[str, Any]):
        for arg_name, value in arguments.items():
            if arg_name in self._input_arguments:
                if isinstance(value, str) and not value.strip():
                    if arg_name in self._required_arguments:
                        raise ValueError(
                            f"Required argument '{arg_name}' cannot be empty"
                        )
                if isinstance(value, str) and len(value) > 100000:
                    pass

    def _format_prompt(self, arguments: Dict[str, Any]) -> str:
        prompt = self._prompt_template
        for arg_name in self._input_arguments:
            placeholder = f"{{{arg_name}}}"
            value = arguments.get(arg_name, "")
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        return prompt

    def get_prompt_preview(self, arguments: Dict[str, Any]) -> str:
        try:
            args_copy = arguments.copy()
            missing_required_args = [
                arg for arg in self._required_arguments if arg not in args_copy
            ]
            if missing_required_args:
                raise ValueError(
                    f"Missing required input arguments: {missing_required_args}"
                )
            for arg in self._input_arguments:
                if arg not in args_copy:
                    args_copy[arg] = self._argument_defaults.get(arg, "")
            return self._format_prompt(args_copy)
        except Exception as e:
            return f"Error formatting prompt: {str(e)}"

    def get_model_info(self) -> Dict[str, Any]:
        info = self._model_metadata()
        info.update(
            {
                "return_json": self._return_json,
                "max_retries": self._max_retries,
                "retry_delay": self._retry_delay,
                "validate_api_key": self._validate_api_key,
                "gemini_model_id": getattr(self, "_gemini_model_id", None),
                "is_available": self._is_available,
                "initialization_error": self._initialization_error,
                "current_api_type": self._current_api_type,
                "current_model_id": self._current_model_id,
                "fallback_api_type": self._fallback_api_type,
                "fallback_model_id": self._fallback_model_id,
                "use_global_fallback": self._use_global_fallback,
                "global_fallback_chain": self._global_fallback_chain,
            }
        )
        return info

    def is_available(self) -> bool:
        """Check if the tool is available for use."""
        return self._is_available

    def get_availability_status(self) -> Dict[str, Any]:
        """Get detailed availability status of the tool."""
        return {
            "is_available": self._is_available,
            "initialization_error": self._initialization_error,
            "api_type": self._api_type,
            "model_id": self._model_id,
        }

    def retry_initialization(self) -> bool:
        """Attempt to reinitialize the tool (useful if API keys were updated)."""
        try:
            if self._api_type == "CHATGPT":
                self._llm_client = AzureOpenAIClient(self._model_id, None, self.logger)
            elif self._api_type == "OPENROUTER":
                self._llm_client = OpenRouterClient(self._model_id, self.logger)
            elif self._api_type == "GEMINI":
                self._llm_client = GeminiClient(self._gemini_model_id, self.logger)
            elif self._api_type == "VLLM":
                # Server URL is optional - only needed for API-based inference, not batch
                server_url = os.getenv("VLLM_SERVER_URL")
                if (
                    self._max_new_tokens is not None
                    and isinstance(self._vllm_specific_args, dict)
                    and "max_model_len" not in self._vllm_specific_args
                ):
                    # Ensure remote engine requests mirror per-tool token cap when possible.
                    self._vllm_specific_args["max_model_len"] = self._max_new_tokens
                self._llm_client = VLLMClient(
                    self._model_id,
                    server_url,
                    self.logger,
                    self._vllm_specific_args,
                )
            else:
                raise ValueError(f"Unsupported API type: {self._api_type}")

            if self._validate_api_key:
                self._llm_client.test_api()
                self.logger.info(
                    f"Successfully reinitialized {self._api_type} model: {self._model_id}"
                )

            self._is_available = True
            self._initialization_error = None
            return True

        except Exception as e:
            self._initialization_error = str(e)
            self.logger.warning(
                f"Retry initialization failed for {self._api_type} model {self._model_id}: {str(e)}"
            )
            return False

    def get_prompt_template(self) -> str:
        return self._prompt_template

    def get_input_arguments(self) -> List[str]:
        return self._input_arguments.copy()

    def validate_configuration(self) -> Dict[str, Any]:
        validation_results = {"valid": True, "warnings": [], "errors": []}
        try:
            self._validate_model_config()
        except ValueError as e:
            validation_results["valid"] = False
            validation_results["errors"].append(str(e))
        if not self._prompt_template:
            validation_results["valid"] = False
            validation_results["errors"].append("Missing prompt template")
        return validation_results

    def estimate_token_usage(self, arguments: Dict[str, Any]) -> Dict[str, int]:
        prompt = self._format_prompt(arguments)
        estimated_input_tokens = len(prompt) // 4
        estimated_max_output_tokens = (
            self._max_new_tokens if self._max_new_tokens is not None else 2048
        )
        estimated_total_tokens = estimated_input_tokens + estimated_max_output_tokens
        return {
            "estimated_input_tokens": estimated_input_tokens,
            "max_output_tokens": estimated_max_output_tokens,
            "estimated_total_tokens": estimated_total_tokens,
            "prompt_length_chars": len(prompt),
        }
