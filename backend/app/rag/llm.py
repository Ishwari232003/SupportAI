
import json
import re

from app.core import config

_client = None


def chat(messages, temperature=0.0, json_mode=False):
    global _client

    if _client is None:
        from openai import OpenAI

        _client = OpenAI(
            api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

    kw = {"response_format": {"type": "json_object"}} if json_mode else {}

    r = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        **kw
    )

    return r.choices[0].message.content


def chat_json(messages):
    txt = chat(messages, json_mode=True)

    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {}
