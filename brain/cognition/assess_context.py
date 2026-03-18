import json
import os

from openai import OpenAI

from brain.identity import ALAHA_IDENTITY


SYSTEM_PROMPT = (
    "Você é o Alaha, um agente autônomo controlando um Ubuntu via noVNC. "
    "Analise a tela e retorne APENAS JSON:\n"
    "{\n"
    '  "action": "click|type|scroll|key|wait|done",\n'
    '  "x": 0,\n'
    '  "y": 0,\n'
    '  "text": "",\n'
    '  "key": "",\n'
    '  "ms": 0,\n'
    '  "reasoning": ""\n'
    "}"
)


class ModelResponseError(RuntimeError):
    pass


def _extract_json_payload(raw_text: str) -> dict:
    content = raw_text.strip()
    if content.startswith('```'):
        lines = [line for line in content.splitlines() if not line.strip().startswith('```')]
        content = '\n'.join(lines).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ModelResponseError(f'Resposta inválida do modelo: {raw_text}') from exc


def assess_context(task: str, screenshot_b64: str) -> dict:
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        raise ModelResponseError('OPENAI_API_KEY não configurada.')

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model='gpt-4o',
        input=[
            {
                'role': 'system',
                'content': [
                    {
                        'type': 'input_text',
                        'text': f'{ALAHA_IDENTITY.strip()}\n\n{SYSTEM_PROMPT}',
                    }
                ],
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'input_text',
                        'text': f'Tarefa atual: {task}',
                    },
                    {
                        'type': 'input_image',
                        'image_url': f'data:image/png;base64,{screenshot_b64}',
                    },
                ],
            },
        ],
    )
    raw_text = response.output_text
    payload = _extract_json_payload(raw_text)
    payload.setdefault('reasoning', '')
    return payload
