# vLLM Batch Inference

Keep one GPU-bound model alive and let many agentic tools share it.

## Launch the engine

- Use a non-daemon process; vLLM needs to spawn workers.
- Minimal launcher:
  ```python
  from tooluniverse.vllm_proxy import run_engine_server

  run_engine_server(
      engine_id="medical-eval-qwen32b",
      model_name="Qwen/Qwen3-32B",
      engine_kwargs={"tensor_parallel_size": 4, "max_model_len": 131072},
      address=("0.0.0.0", 5317),
      authkey=b"tooluniverse",
  )
  ```
- Set `TOOLUNIVERSE_VLLM_MANAGER_ADDR="host:port"` and `TOOLUNIVERSE_VLLM_MANAGER_AUTHKEY="tooluniverse"` when clients should auto-discover the registry.

## Wire agentic tools

- Add `"api_type": "VLLM"` and point `"model_id"` at the shared checkpoint.
- Set per-tool sampling knobs such as `"temperature"` and `"max_new_tokens"`; `AgenticTool` forwards them to `VLLMClient.infer_batch`, so different evaluators can reuse the same engine with different decoding behavior.
- Connection details (engine launch, registry host/port, auth key) should be injected by whatever process boots the registry. Export `TOOLUNIVERSE_VLLM_MANAGER_*` before instantiating tools so their configs only need model-scoped options.
- Example:
  ```json
  {
    "type": "AgenticTool",
    "name": "ClinicalTaskAccuracyEvaluator",
    "configs": {
      "api_type": "VLLM",
      "model_id": "Qwen/Qwen3-32B",
      "temperature": 0.3,
      "max_new_tokens": 131072,
      "return_json": true,
      "vllm_specific_args": {
        "hf_overrides": {
          "rope_scaling": {
            "rope_type": "yarn",
            "factor": 4.0,
            "original_max_position_embeddings": 32768
          }
        }
      }
    }
  }
  ```
- Keep `vllm_specific_args` for optional runtime hints (for example `hf_overrides`). Leave connection metadata out of the tool config unless you are bypassing the orchestrator and managing registry discovery manually.

## Operate the fleet

- Start the server once per model; clients reconnect automatically.
- Use `tooluniverse.vllm_proxy.list_remote_engines` to confirm registration.
- Scale horizontally by launching more servers with distinct `engine_id` values.
- Shut things down: once inference jobs finish, connect to the registry (`vllm_proxy.connect_registry(...)`) and call `shutdown_engine("<engine_id>")` (or `shutdown_all()`) so each engine exits cleanly.
- After signalling shutdown, stop your launcher process (Ctrl+C for the simple script or `Process.join()` if you spawned it manually) to release the GPU workers and avoid orphan processes.
