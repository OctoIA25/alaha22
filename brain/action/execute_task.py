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

    screen_meta = action_payload.get('_screen') or {}
    try:
        screen_width = float(screen_meta.get('width') or 0)
        screen_height = float(screen_meta.get('height') or 0)
        original_width = float(screen_meta.get('original_width') or 0)
        original_height = float(screen_meta.get('original_height') or 0)
    except (TypeError, ValueError):
        screen_width = screen_height = original_width = original_height = 0

    def _scale_coords(x: int, y: int) -> tuple[int, int]:
        if screen_width > 0 and screen_height > 0 and original_width > 0 and original_height > 0:
            scale_x = original_width / screen_width
            scale_y = original_height / screen_height
            return int(x * scale_x), int(y * scale_y)
        return x, y

    if action == 'click':
        x = int(action_payload.get('x', 0))
        y = int(action_payload.get('y', 0))
        real_x, real_y = _scale_coords(x, y)
        _run_xdotool(['mousemove', str(real_x), str(real_y), 'click', '1'], display_value)
        return {'status': 'executed', 'action': action, 'x': x, 'y': y, 'real_x': real_x, 'real_y': real_y}

    if action == 'type':
        text = str(action_payload.get('text', ''))
        _run_xdotool(['type', '--clearmodifiers', text], display_value)
        return {'status': 'executed', 'action': action, 'text': text}

    if action == 'scroll':
        x = int(action_payload.get('x', 0))
        y = int(action_payload.get('y', 0))
        button = '4' if y < 0 else '5'
        real_x, real_y = _scale_coords(x, y)
        _run_xdotool(['mousemove', str(real_x), str(real_y), 'click', button], display_value)
        return {'status': 'executed', 'action': action, 'x': x, 'y': y, 'real_x': real_x, 'real_y': real_y, 'button': button}

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
