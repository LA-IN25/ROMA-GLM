# Using z.ai GLM Models with ROMA

This guide explains how to configure ROMA to use z.ai's GLM-4.6 and GLM-4.5-air models.

## Quick Setup

1. **Set your z.ai API key:**
   ```bash
   export ZAI_API_KEY=your_zai_api_key
   ```

2. **Use the z.ai GLM profile:**
   ```bash
   roma --profile zai_glm "your task here"
   ```

## Available Configurations

### 1. Full Profile (`config/profiles/zai_glm.yaml`)
Complete configuration with all agents and task-specific mappings:
- **Atomizer**: GLM-4.5-air (fast decision making)
- **Planner**: GLM-4.6 (strategic planning)
- **Executor**: GLM-4.6 (general task execution)
- **Aggregator**: GLM-4.6 (result synthesis)
- **Verifier**: GLM-4.5-air (fast validation)

### 2. Example Configuration (`config/examples/zai/zai_glm_example.yaml`)
Simplified example for testing and customization:

```bash
# Using the example config
roma --config config/examples/zai/zai_glm_example.yaml "your task"
```

## Model Selection Guide

### GLM-4.6
- **Use for**: Complex reasoning, code interpretation, content creation
- **Strengths**: Higher capability, better for deep analysis
- **Configured for**: Planner, Executor, Aggregator, THINK, WRITE, CODE_INTERPRET

### GLM-4.5-air
- **Use for**: Fast tasks, retrieval, validation
- **Strengths**: Faster response time, cost-effective
- **Configured for**: Atomizer, Verifier, RETRIEVE

## Environment Variables

Add to your `.env` file:
```bash
ZAI_API_KEY=your_zai_api_key
```

## Running with z.ai Models

### Command Line
```bash
# Using the predefined profile
roma --profile zai_glm "analyze this code and suggest improvements"

# Using custom config
roma --config /path/to/your/zai_config.yaml "your task"
```

### Python API
```python
from roma_dspy import ROMA

# Initialize with z.ai profile
agent = ROMA(profile="zai_glm")
result = agent.run("your task here")
```

## Configuration Customization

You can create custom configurations by modifying the model assignments:

```yaml
agents:
  atomizer:
    llm:
      model: zai/glm-4.6  # Use more capable model for atomizer
      temperature: 0.0
      max_tokens: 8000
      api_key: ${oc.env:ZAI_API_KEY}
```

## Task-Specific Optimization

The configuration includes task-aware mapping:

- **RETRIEVE**: Uses GLM-4.5-air for fast information gathering
- **CODE_INTERPRET**: Uses GLM-4.6 for better code reasoning
- **THINK**: Uses GLM-4.6 for deep analysis
- **WRITE**: Uses GLM-4.6 for content creation

## Troubleshooting

1. **API Key Issues**: Ensure `ZAI_API_KEY` is properly set
2. **Model Availability**: Verify z.ai GLM models are accessible in your region
3. **Performance**: Adjust `max_tokens` and `temperature` based on your needs

## Mixing with Other Providers

You can mix z.ai models with other providers if needed:

```yaml
agents:
  atomizer:
    llm:
      model: zai/glm-4.5-air  # z.ai for speed
      api_key: ${oc.env:ZAI_API_KEY}
  executor:
    llm:
      model: openai/glm-4.6  # OpenRouter for capability
      api_key: ${oc.env:OPENROUTER_API_KEY}
```

Note: You'll need to configure API keys for all providers used.
