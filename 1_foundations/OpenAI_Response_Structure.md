# OpenAI API Response Structure

## Simple Chat — e.g. `"How are you?"`

When there are **no tools involved**, `finish_reason` is `"stop"` and `message.content` holds the reply.

```json
{
  "id": "chatcmpl-abc123xyz",
  "object": "chat.completion",
  "created": 1714123456,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "I'm doing great, thanks for asking! How can I help you today?",
        "tool_calls": null
      }
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 15,
    "total_tokens": 27
  }
}
```

---

## Tool Calling — e.g. `"My name is Alice, email alice@example.com"`

When the model wants to invoke a function, `finish_reason` is `"tool_calls"`, `message.content` is `null`, and `message.tool_calls` contains the function to run.

```json
{
  "id": "chatcmpl-abc123xyz",
  "object": "chat.completion",
  "created": 1714123456,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "finish_reason": "tool_calls",
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "record_user_details",
              "arguments": "{\"name\": \"Alice\", \"email\": \"alice@example.com\"}"
            }
          }
        ]
      }
    }
  ],
  "usage": {
    "prompt_tokens": 85,
    "completion_tokens": 23,
    "total_tokens": 108
  }
}
```

> [!NOTE]
> `function.arguments` is a **JSON string**, not a dict. You must call `json.loads(arguments)` before using `**` to unpack it.

---

## Side-by-side Comparison

| Field | Simple Chat | Tool Calling |
|---|---|---|
| `finish_reason` | `"stop"` | `"tool_calls"` |
| `message.content` | ✅ Text string | ❌ `null` |
| `message.tool_calls` | ❌ `null` | ✅ List of tool calls |

---

## Accessing the Response in Code

```python
# Get the finish reason
finish_reason = response.choices[0].finish_reason

if finish_reason == "stop":
    # Simple reply — get the text
    reply = response.choices[0].message.content

elif finish_reason == "tool_calls":
    # Tool call — get the function name and arguments
    tool_call = response.choices[0].message.tool_calls[0]
    func_name  = tool_call.function.name
    arguments  = json.loads(tool_call.function.arguments)  # str → dict
    result = record_user_details(**arguments)               # unpack dict as kwargs
```

