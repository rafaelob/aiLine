# claude-api examples

These examples are loaded only for the implementation path selected in the root skill.

## Example 1

Source section: ### 1. Set up SDK

```python
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env
```

## Example 2

Source section: ### 1. Set up SDK

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();  // reads ANTHROPIC_API_KEY from env
```

## Example 3

Source section: ### 3. Basic message

```python
message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}]
)
print(next(block.text for block in message.content if block.type == "text"))
```

## Example 4

Source section: ### 3. Basic message

```python
message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    system="You are a helpful assistant that responds in JSON.",
    messages=[{"role": "user", "content": "List 3 colors"}]
)
```

## Example 5

Source section: ### 4. Streaming

```python
with client.messages.stream(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Example 6

Source section: ### 5. Tool use

```python
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
}]

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Weather in London?"}]
)

# Process tool calls
if message.stop_reason == "tool_use":
    tool_block = next(b for b in message.content if b.type == "tool_use")
    # Execute tool_block.name with tool_block.input, then send result back:
    result_message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "Weather in London?"},
            {"role": "assistant", "content": message.content},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_block.id,
                 "content": "15°C, partly cloudy"}
            ]}
        ]
    )
```

## Example 7

Source section: ### 8. Vision (image input)

```python
import base64

with open("image.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {
            "type": "base64", "media_type": "image/png", "data": image_data
        }},
        {"type": "text", "text": "Describe this image"}
    ]}]
)
```

## Example 8

Source section: ### 11. Agent Skills in the code execution container (beta)

```json
"tools": [{"type": "code_execution_20260521", "name": "code_execution"}],
"container": {"skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]}
```

## Example 9

Source section: ### 12. Prompt caching (`cache_control`)

```python
message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a legal analyst. Here is the full policy manual: ...",
            "cache_control": {"type": "ephemeral", "ttl": "1h"}  # "5m" (default) or "1h"
        }
    ],
    messages=[{"role": "user", "content": "Question 1"}]
)
# Inspect cache usage: message.usage.cache_creation_input_tokens / cache_read_input_tokens
```

## Example 10

Source section: ### 13. Batches API

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "request-1",
            "params": {
                "model": "claude-sonnet-5",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Summarize: ..."}]
            }
        }
    ]
)
# Poll batch.id for completion, then retrieve results
```

