import json
import os
import urllib.error
import urllib.request

from django.core.management.base import CommandError


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"


SYSTEM_PROMPT = """You generate structured content for a Django brochure-site CMS.

Rules:
- Return only schema-valid JSON through structured outputs.
- Do not write raw HTML.
- Do not write Markdown.
- Use plain text in body fields, with blank lines for paragraph breaks when useful.
- Use concise, editor-friendly copy that a human can review in Django admin.
- Create pages and sections that match the requested client site and page templates.
- Keep slugs lowercase, hyphenated, and URL-safe.
- Use internal page slug references for CTAs/navigation when linking to generated pages.
- Generated pages will be saved as drafts for editor review, so write publish-ready draft content."""


def generate_content_with_openai(job, content_schema):
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    raise CommandError("OPENAI_API_KEY is not set.")

  payload = {
    "model": job.model,
    "input": [
      {
        "role": "system",
        "content": SYSTEM_PROMPT,
      },
      {
        "role": "user",
        "content": job.brief,
      },
    ],
    "text": {
      "format": {
        "type": "json_schema",
        "name": content_schema.name,
        "description": content_schema.description,
        "schema": content_schema.schema,
        "strict": True,
      },
    },
  }

  request = urllib.request.Request(
    os.getenv("OPENAI_RESPONSES_URL", OPENAI_RESPONSES_URL),
    data=json.dumps(payload).encode("utf-8"),
    headers={
      "Authorization": f"Bearer {api_key}",
      "Content-Type": "application/json",
    },
    method="POST",
  )

  try:
    with urllib.request.urlopen(request, timeout=120) as response:
      response_data = json.loads(response.read().decode("utf-8"))
  except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    raise CommandError(f"OpenAI API error {exc.code}: {detail}") from exc
  except urllib.error.URLError as exc:
    raise CommandError(f"OpenAI API request failed: {exc}") from exc

  output_text = extract_output_text(response_data)
  try:
    return json.loads(output_text)
  except json.JSONDecodeError as exc:
    raise CommandError(f"OpenAI returned non-JSON output: {output_text[:500]}") from exc


def extract_output_text(response_data):
  if response_data.get("output_text"):
    return response_data["output_text"]

  chunks = []
  for output in response_data.get("output", []):
    for content in output.get("content", []):
      if content.get("type") in {"output_text", "text"} and content.get("text"):
        chunks.append(content["text"])
      if content.get("type") == "refusal":
        raise CommandError(f"OpenAI refused the request: {content.get('refusal', '')}")

  if chunks:
    return "".join(chunks)

  raise CommandError(f"OpenAI response did not contain output text: {json.dumps(response_data)[:1000]}")
