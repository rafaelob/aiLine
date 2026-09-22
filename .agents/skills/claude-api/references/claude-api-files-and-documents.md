# Claude API — PDF Document Blocks & Files API (detailed reference)

Supplementary code examples for the `claude-api` skill.  
Source: https://platform.claude.com/docs/en/build-with-claude/files  
Checked: 2026-06-29

---

## PDF input (document blocks) — full examples

Send PDFs as `document` content blocks alongside text messages.

```python
import base64
from anthropic import Anthropic

client = Anthropic()

# Option 1: base64 inline
with open("report.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "document", "source": {
            "type": "base64", "media_type": "application/pdf", "data": pdf_data
        }},
        {"type": "text", "text": "Summarize the key findings"}
    ]}]
)
print(next(block.text for block in message.content if block.type == "text"))

# Option 2: URL reference
message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "document", "source": {
            "type": "url", "url": "https://example.com/report.pdf"
        }},
        {"type": "text", "text": "Summarize the key findings"}
    ]}]
)

# Option 3: Files API file_id (see below)
# {"type": "document", "source": {"type": "file", "file_id": "file-abc123"}}
```

**Limits and notes:**
- Max pages: 600 (100 for 200K-context models like Haiku 4.5)
- Max file size: 32 MB per PDF
- Password-protected / encrypted PDFs are not accepted
- Token cost: approximately 1500–3000 tokens per page (text extraction + page images)
- Placement: put PDF document blocks **before** text content for best results
- Use the Files API for PDFs reused across multiple requests to avoid re-sending large payloads

---

## Files API (beta) — full examples

Upload files once and reference by `file_id` across multiple requests.  
**Beta header required:** `files-api-2025-04-14`

### Upload and use a PDF

```python
from anthropic import Anthropic

client = Anthropic()

# Upload once
with open("report.pdf", "rb") as f:
    uploaded = client.beta.files.upload(
        file=("report.pdf", f, "application/pdf")
    )
file_id = uploaded.id  # e.g. "file-abc123"
print(f"Uploaded: {file_id}")

# Reference by file_id in subsequent requests (no re-upload needed)
message = client.beta.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "document", "source": {"type": "file", "file_id": file_id}},
        {"type": "text", "text": "Summarize this document"}
    ]}],
    betas=["files-api-2025-04-14"]
)
print(next(block.text for block in message.content if block.type == "text"))
```

### Combine with prompt caching for maximum cost savings

```python
# Add cache_control to a reused file-backed document block
message = client.beta.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {
            "type": "document",
            "source": {"type": "file", "file_id": file_id},
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        },
        {"type": "text", "text": "What are the conclusions?"}
    ]}],
    betas=["files-api-2025-04-14"]
)
```

### File management operations

```python
# List uploaded files
files = client.beta.files.list()
for f in files.data:
    print(f.id, f.filename, f.size)

# Retrieve metadata
metadata = client.beta.files.retrieve_metadata(file_id)
print(metadata.filename, metadata.created_at)

# Download file content
content = client.beta.files.download(file_id)
with open("downloaded.pdf", "wb") as out:
    out.write(content)

# Delete a file
client.beta.files.delete(file_id)
```

**Supported file types:** PDF, JPEG, PNG, GIF, WebP, CSV, XLSX, DOCX, MD, TXT  
**Max file size:** 500 MB per file  
**SDK namespace:** `client.beta.files` — methods: `upload()`, `list()`, `retrieve_metadata()`, `download()`, `delete()`
