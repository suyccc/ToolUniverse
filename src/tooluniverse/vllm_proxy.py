"""vLLM engine manager and proxy utilities.

This module provides a lightweight registry that keeps long-lived vLLM ``LLM``
instances in a dedicated Python process. Client code (for example the
``VLLMClient`` inside ToolUniverse) connects to the registry over a
``multiprocessing.managers`` channel and requests an engine by id. All agentic
Tools that share the same engine id therefore reuse the very same model
instance and GPU memory footprint.

Typical usage for a standalone launcher script::

    from tooluniverse.vllm_proxy import run_engine_server

    run_engine_server(
        engine_id="qwen3-32b-eval",
        model_name="Qwen/Qwen3-32B",
        engine_kwargs={"tensor_parallel_size": 4, "max_model_len": 131072},
        address=("127.0.0.1", 5317),
        authkey=b"tooluniverse",
    )

Environment variables read by clients when no explicit registry settings are
provided:

``TOOLUNIVERSE_VLLM_MANAGER_ADDR``  e.g. ``"127.0.0.1:5317"``
``TOOLUNIVERSE_VLLM_MANAGER_AUTHKEY``  e.g. ``"tooluniverse"``

Servers should keep running for the lifetime of the evaluation job. Clients
only block while a generation request is in flight.
"""

from __future__ import annotations

import json
import logging
import os
from multiprocessing.managers import BaseManager, BaseProxy
from threading import Lock
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

_logger = logging.getLogger(__name__)


def _detect_visible_gpu_count() -> Optional[int]:
    """Best-effort detection of available CUDA devices."""

    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return torch.cuda.device_count()
    except Exception:  # pragma: no cover - optional dependency
        pass

    cuda_visible = os.getenv("CUDA_VISIBLE_DEVICES")
    if cuda_visible is None:
        return None

    cleaned = [token for token in (part.strip() for part in cuda_visible.split(",")) if token]
    if not cleaned:
        return 0
    if cleaned == ["-1"]:
        return 0
    return len(cleaned)


def _normalize_engine_kwargs(engine_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce engine kwargs into safe values for this host."""

    normalized = dict(engine_kwargs)

    if "max_model_len" in normalized:
        try:
            normalized["max_model_len"] = int(normalized["max_model_len"])
        except (TypeError, ValueError):
            _logger.warning("Ignoring invalid max_model_len=%s", normalized["max_model_len"])
            normalized.pop("max_model_len", None)

    if "tensor_parallel_size" in normalized:
        try:
            requested = int(normalized["tensor_parallel_size"])
        except (TypeError, ValueError):
            _logger.warning(
                "Invalid tensor_parallel_size=%s; removing setting.",
                normalized["tensor_parallel_size"],
            )
            normalized.pop("tensor_parallel_size", None)
        else:
            if requested < 1:
                _logger.warning("tensor_parallel_size must be >=1; defaulting to 1.")
                requested = 1

            gpu_count = _detect_visible_gpu_count()
            if gpu_count == 0:
                raise RuntimeError(
                    "No CUDA devices detected for vLLM engine. "
                    "Ensure GPUs are visible before launching the server."
                )
            if gpu_count is not None and requested > gpu_count:
                _logger.info(
                    "Requested tensor_parallel_size=%s but only %s GPU(s) visible; using %s.",
                    requested,
                    gpu_count,
                    gpu_count,
                )
                requested = max(1, gpu_count)

            normalized["tensor_parallel_size"] = requested

    return normalized


def _standardize_engine_kwargs(engine_kwargs: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not engine_kwargs:
        return {}
    standardized = {str(key): engine_kwargs[key] for key in sorted(engine_kwargs)}
    return _normalize_engine_kwargs(standardized)


def make_engine_key(engine_id: Optional[str], model_name: str, engine_kwargs: Optional[Dict[str, Any]]) -> str:
    """Derive a stable key identifying a remotely hosted vLLM engine."""

    if engine_id:
        return engine_id
    parts = [model_name]
    for key, value in _standardize_engine_kwargs(engine_kwargs).items():
        parts.append(f"{key}={value}")
    return "|".join(parts)


class RemoteVLLMEngine:
    """Holds a concrete ``vllm.LLM`` instance and services generate calls."""

    def __init__(self, model_name: str, engine_kwargs: Optional[Dict[str, Any]] = None) -> None:
        engine_kwargs = _standardize_engine_kwargs(engine_kwargs)
        try:
            from vllm import LLM
        except Exception as exc:  # pragma: no cover - import error surfaced immediately
            raise RuntimeError("The 'vllm' package is required to host a RemoteVLLMEngine") from exc

        self._model_name = model_name
        self._engine_kwargs = engine_kwargs
        self._logger = logging.getLogger(f"RemoteVLLMEngine[{model_name}]")
        self._logger.info("Starting vLLM engine with kwargs: %s", engine_kwargs)
        self._llm = LLM(model=model_name, **engine_kwargs)

    def metadata(self) -> Dict[str, Any]:
        return {
            "model_name": self._model_name,
            "engine_kwargs": self._engine_kwargs,
        }

    @staticmethod
    def _build_sampling_params(sampling_kwargs: Optional[Dict[str, Any]]):
        if not sampling_kwargs:
            return None
        try:
            from vllm import SamplingParams
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("The 'vllm' package is required to host a RemoteVLLMEngine") from exc

        params: Dict[str, Any] = {}
        if "temperature" in sampling_kwargs and sampling_kwargs["temperature"] is not None:
            params["temperature"] = sampling_kwargs["temperature"]
        if "max_tokens" in sampling_kwargs and sampling_kwargs["max_tokens"] is not None:
            params["max_tokens"] = sampling_kwargs["max_tokens"]
        return SamplingParams(**params)

    @staticmethod
    def _apply_structured_outputs(sampling_params, return_json: bool, json_schema: Optional[Dict[str, Any]]):
        if not return_json:
            return sampling_params
        if not json_schema:
            _logger.warning("return_json=True without json_schema; ensure prompts enforce JSON format.")
            return sampling_params
        try:
            from vllm.sampling_params import StructuredOutputsParams
        except Exception:  # pragma: no cover
            _logger.warning("StructuredOutputsParams unavailable; falling back to prompt-only JSON guidance.")
            return sampling_params
        if sampling_params is None:
            from vllm import SamplingParams

            sampling_params = SamplingParams()
        sampling_params.structured_outputs = StructuredOutputsParams(json=json_schema)
        return sampling_params

    def generate(
        self,
        prompts: List[str],
        sampling_kwargs: Optional[Dict[str, Any]] = None,
        return_json: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> List[Optional[str]]:
        sampling_params = self._build_sampling_params(sampling_kwargs)
        sampling_params = self._apply_structured_outputs(sampling_params, return_json, json_schema)

        try:
            outputs = self._llm.generate(prompts, sampling_params) if sampling_params else self._llm.generate(prompts)
        except Exception as exc:  # pragma: no cover - surface engine errors to caller
            raise RuntimeError(f"vLLM generation failed: {exc}") from exc

        results: List[Optional[str]] = []
        for output in outputs:
            generated_text: Optional[str] = None
            candidates = getattr(output, "outputs", None)
            if candidates:
                candidate = candidates[0]
                generated_text = getattr(candidate, "text", None)
                if generated_text is None and isinstance(candidate, dict):
                    generated_text = candidate.get("text")

            if return_json and generated_text:
                try:
                    json.loads(generated_text)
                    results.append(generated_text)
                except json.JSONDecodeError:
                    self._logger.warning("Engine produced non-JSON output: %s", generated_text)
                    results.append(None)
            else:
                results.append(generated_text)
        return results


class RemoteVLLMEngineProxy(BaseProxy):
    """Proxy exposing safe methods of ``RemoteVLLMEngine`` to remote clients."""

    _exposed_ = ("metadata", "generate")

    def metadata(self) -> Dict[str, Any]:
        return self._callmethod("metadata")

    def generate(
        self,
        prompts: List[str],
        sampling_kwargs: Optional[Dict[str, Any]] = None,
        return_json: bool = False,
        json_schema: Optional[Dict[str, Any]] = None,
    ) -> List[Optional[str]]:
        return self._callmethod(
            "generate",
            (prompts,),
            {
                "sampling_kwargs": sampling_kwargs,
                "return_json": return_json,
                "json_schema": json_schema,
            },
        )


class EngineRegistry:
    """Tracks available RemoteVLLMEngine instances by key."""

    def __init__(self) -> None:
        self._engines: Dict[str, RemoteVLLMEngine] = {}
        self._lock = Lock()

    def register_engine(self, key: str, engine: RemoteVLLMEngine) -> None:
        with self._lock:
            if key in self._engines:
                raise ValueError(f"An engine with key '{key}' is already registered")
            self._engines[key] = engine
            _logger.info("Registered engine '%s'", key)

    def get_engine(self, key: str) -> Optional[RemoteVLLMEngine]:
        with self._lock:
            engine = self._engines.get(key)
            if engine is None:
                _logger.warning("Requested engine '%s' is not registered", key)
            return engine

    def list_keys(self) -> List[str]:
        with self._lock:
            return list(self._engines.keys())


class VLLMEngineManager(BaseManager):
    """Custom manager exposing the engine registry."""


def _register_manager_class(manager_cls: type[BaseManager], registry_factory: Callable[[], EngineRegistry]) -> None:
    manager_cls.register(
        "RemoteVLLMEngine",
        proxytype=RemoteVLLMEngineProxy,
    )
    manager_cls.register(
        "get_registry",
        callable=registry_factory,
        exposed=("register_engine", "get_engine", "list_keys"),
        method_to_typeid={"get_engine": "RemoteVLLMEngine"},
    )


_register_manager_class(VLLMEngineManager, lambda: EngineRegistry())


def parse_address(address: Optional[Any]) -> Tuple[str, int]:
    if address is None:
        raise ValueError("Registry address must be provided")
    if isinstance(address, (list, tuple)):
        host, port = address
        return str(host), int(port)
    if isinstance(address, str):
        host, port_str = address.split(":", 1)
        return host, int(port_str)
    raise ValueError(f"Unsupported address type: {type(address)}")


def connect_registry(address: Any, authkey: Any) -> Any:
    host, port = parse_address(address)
    auth = authkey.encode("utf-8") if isinstance(authkey, str) else authkey
    manager = VLLMEngineManager(address=(host, port), authkey=auth)
    manager.connect()
    return manager.get_registry()


def run_engine_server(
    *,
    engine_id: Optional[str],
    model_name: str,
    engine_kwargs: Optional[Dict[str, Any]] = None,
    address: Tuple[str, int] = ("127.0.0.1", 5317),
    authkey: bytes = b"tooluniverse",
) -> None:
    """Convenience helper to launch a registry hosting a single engine.
    
    This must be called from a non-daemon process to allow vLLM to spawn
    its tensor-parallel worker processes.
    """
    import multiprocessing
    
    # Ensure we can create child processes for vLLM's tensor parallelism
    if multiprocessing.current_process().daemon:
        raise RuntimeError(
            "run_engine_server cannot be called from a daemon process. "
            "Set daemon=False when creating the parent process."
        )

    key = make_engine_key(engine_id, model_name, engine_kwargs)
    
    # Create a local registry instance
    local_registry = EngineRegistry()
    
    # Create the engine FIRST (this will spawn vLLM's tensor parallel processes)
    # This must happen before manager.start() to avoid daemon process issues
    engine = RemoteVLLMEngine(model_name=model_name, engine_kwargs=engine_kwargs)
    local_registry.register_engine(key, engine)
    
    # Create a custom manager class that uses our pre-populated registry
    class LocalVLLMEngineManager(BaseManager):
        pass

    _register_manager_class(LocalVLLMEngineManager, lambda: local_registry)

    # Start the manager server
    manager = LocalVLLMEngineManager(address=address, authkey=authkey)
    server = manager.get_server()
    
    _logger.info("vLLM engine server running at %s with key '%s'", address, key)
    try:
        server.serve_forever()
    finally:  # pragma: no cover - server loops forever in normal operation
        server.shutdown()


def list_remote_engines(registry_proxy) -> Iterable[str]:
    return registry_proxy.list_keys()
