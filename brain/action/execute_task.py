import os
import subprocess
import time


class ActionExecutionError(RuntimeError):
    pass


def _run_xdotool(args: list[str], display: str) -> None:
    env = os.environ.copy()
    env['DISPLAY'] = display
    result = subprocess.run(
        ['xdotool', *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ActionExecutionError(result.stderr.strip() or 'Falha ao executar xdotool.')


def execute_task(action_payload: dict, display: str | None = None) -> dict:
    display_value = display or os.getenv('DISPLAY', ':1')
    action = action_payload.get('action')

    if action == 'click':
        x = int(action_payload.get('x', 0))
        y = int(action_payload.get('y', 0))
        _run_xdotool(['mousemove', str(x), str(y), 'click', '1'], display_value)
        return {'status': 'executed', 'action': action, 'x': x, 'y': y}

    if action == 'type':
        text = str(action_payload.get('text', ''))
        _run_xdotool(['type', '--clearmodifiers', text], display_value)
        return {'status': 'executed', 'action': action, 'text': text}

    if action == 'scroll':
        x = int(action_payload.get('x', 0))
        y = int(action_payload.get('y', 0))
        button = '4' if y < 0 else '5'
        _run_xdotool(['mousemove', str(x), str(y), 'click', button], display_value)
        return {'status': 'executed', 'action': action, 'x': x, 'y': y, 'button': button}

    if action == 'key':
        key = str(action_payload.get('key', ''))
        _run_xdotool(['key', key], display_value)
        return {'status': 'executed', 'action': action, 'key': key}

    if action == 'wait':
        ms = int(action_payload.get('ms', 1000))
        time.sleep(ms / 1000)
        return {'status': 'executed', 'action': action, 'ms': ms}

    if action == 'done':
        return {'status': 'completed', 'action': action}

    raise ActionExecutionError(f'Ação inválida recebida: {action}')
