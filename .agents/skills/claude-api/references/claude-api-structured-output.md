# Claude API — Structured Output (detailed reference)

Extracted verbatim from `claude-api/SKILL.md` on 2026-07-28 to keep the SKILL.md body under the 5k-token cap.

---

#### Primary: `output_config.format` (GA for Fable 5.1, Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5)

Claude now has native structured outputs via `output_config.format` with JSON Schema:

```python
response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract name and age from: John is 30"}],
    output_config={
        "format": {
            "type": "json_schema",
            "json_schema": {
                "name": "person",
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"}
                    },
                    "required": ["name", "age"]
                }
            }
        }
    }
)
# The text content block is guaranteed-valid JSON matching the schema.
structured_json = next(block.text for block in response.content if block.type == "text")
```

#### Alternative: tool use (still works on compatible models, useful when you also need tool execution)

Fable 5.1 does not support forced tool choice: `tool_choice` values `any` and `tool`
return HTTP 400. Keep `tool_choice` at `auto` (or `none`) and use a clear instruction
with `strict: true` when using Fable 5.1.

Define a tool whose `input_schema` matches your desired output schema and force Claude to call it:

```python
tools = [{
    "name": "extract_person",
    "description": "Extract person information from text",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "occupation": {"type": "string"}
        },
        "required": ["name", "age"]
    }
}]

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "extract_person"},
    messages=[{"role": "user", "content": "John is a 30-year-old engineer"}]
)

# The tool_use block's input is your structured data
tool_block = next(b for b in message.content if b.type == "tool_use")
structured_data = tool_block.input  # {"name": "John", "age": 30, "occupation": "engineer"}
```

Key: `tool_choice={"type": "tool", "name": "..."}` forces Claude to call that specific tool, guaranteeing structured output.
