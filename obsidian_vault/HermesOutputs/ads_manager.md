# Hermes Agent — ads_manager

**Model:** nousresearch/hermes-3-llama-3.1-405b:free  
**Task:** Execute the full procedure described in your skill instructions. Run each step in order using the terminal.

Kanban card: Draft ad script from best concept

Working directory: D:\crowdwisdom-marketing  

## Response
Ollama loaded `qwen2.5:7b` with only 32,768 tokens of runtime context, but Hermes needs at least 64,000 tokens for reliable tool use.

Increase the Ollama context for this model and restart/reload the model before trying again. A known-good starting point is 65,536 tokens. In Hermes config, set `model.ollama_num_ctx: 65536` (and `model.context_length: 65536` if you also override the displayed model context). If you manage the model through an Ollama Modelfile, set `PARAMETER num_ctx 65536` there instead.
