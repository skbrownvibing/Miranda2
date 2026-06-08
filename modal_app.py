import modal

app = modal.App(
    "reply-or-die-ai",
    image=modal.Image.debian_slim().pip_install("anthropic", "fastapi"),
)

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_OUTPUT_TOKENS = 512
SYSTEM_PROMPT = "You draft short, sendable text replies. Return only the reply text."

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
}


@app.function(secrets=[modal.Secret.from_name("anthropic-api-key")])
@modal.fastapi_endpoint(method="POST")
def suggest_reply(payload: dict):
    from fastapi.responses import JSONResponse
    import anthropic

    def respond(body, status=200):
        return JSONResponse(content=body, status_code=status, headers=CORS_HEADERS)

    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        return respond({"ok": False, "error": "Missing prompt"}, status=400)

    model = str(payload.get("model") or "").strip() or DEFAULT_MODEL

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.9,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        reply = "".join(
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        ).strip()

        if not reply:
            return respond(
                {"ok": False, "error": "AI provider returned empty reply"},
                status=502,
            )

        return respond({"ok": True, "reply": reply, "model": model})
    except Exception:
        return respond(
            {"ok": False, "error": "AI provider request failed"}, status=502
        )
