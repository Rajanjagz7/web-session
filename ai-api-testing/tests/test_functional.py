"""Functional correctness: response shape, tool-use schema, basic content checks."""


def test_basic_content_response(client, model):
    resp = client.messages.create(
        model=model,
        max_tokens=64,
        messages=[{"role": "user", "content": "What is the capital of France? Answer in one word."}],
    )
    text = resp.content[0].text
    assert resp.stop_reason == "end_turn"
    assert "paris" in text.lower()


def test_handles_unicode_and_short_input(client, model):
    resp = client.messages.create(
        model=model,
        max_tokens=32,
        messages=[{"role": "user", "content": "👋 hi"}],
    )
    assert resp.content
    assert resp.content[0].text.strip() != ""


def test_tool_use_returns_well_formed_schema(client, model):
    tool = {
        "name": "extract_contact",
        "description": "Extract a contact's name and email from text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["name", "email"],
        },
    }

    resp = client.messages.create(
        model=model,
        max_tokens=200,
        tools=[tool],
        tool_choice={"type": "tool", "name": "extract_contact"},
        messages=[
            {
                "role": "user",
                "content": "Please extract the contact: Jane Doe, jane.doe@example.com",
            }
        ],
    )

    tool_uses = [b for b in resp.content if b.type == "tool_use"]
    assert len(tool_uses) == 1

    call = tool_uses[0]
    assert call.name == "extract_contact"
    assert set(["name", "email"]).issubset(call.input.keys())
    assert "@" in call.input["email"]
