from __future__ import annotations

import os
from typing import Any

from brain.action.execute_task import ActionExecutionError, execute_task
from brain.cognition.assess_context import ModelResponseError, assess_context
from brain.memory.update_memory import get_redis_client, update_memory
from brain.sensors.screen import ScreenCaptureError, capture_screen_base64


MAX_STEPS = 20
MAX_STUCK_REPEATS = 3


def _state_key(task: str) -> str:
    return f'alaha:computer_use:{task}'


def _update_stuck_state(task: str, screen_hash: str) -> int:
    client = get_redis_client()
    key = _state_key(task)
    previous_hash = client.hget(key, 'last_hash')
    if previous_hash == screen_hash:
        repeat_count = client.hincrby(key, 'repeat_count', 1)
    else:
        client.hset(key, mapping={'last_hash': screen_hash, 'repeat_count': 1})
        repeat_count = 1
    return int(repeat_count)


def _reset_stuck_state(task: str) -> None:
    client = get_redis_client()
    client.delete(_state_key(task))


def run_computer_use(task: str) -> dict[str, Any]:
    display = os.getenv('DISPLAY', ':1')
    last_screenshot = None
    steps: list[dict[str, Any]] = []

    try:
        for index in range(1, MAX_STEPS + 1):
            screen = capture_screen_base64(display=display)
            last_screenshot = screen['base64']
            repeated_state_count = _update_stuck_state(task, screen['hash'])
            if repeated_state_count >= MAX_STUCK_REPEATS:
                result = {
                    'success': False,
                    'status': 'escalated_to_human',
                    'reason': 'Estado repetido 3 vezes consecutivas.',
                    'steps': steps,
                    'last_screenshot': last_screenshot,
                }
                update_memory(task, {'step': index, 'result': result})
                return result

            decision = assess_context(task=task, screenshot_b64=screen['base64'])
            decision['step'] = index
            execution = execute_task(decision, display=display)
            step_record = {
                'step': index,
                'decision': decision,
                'execution': execution,
            }
            steps.append(step_record)
            update_memory(task, step_record)

            if decision.get('action') == 'done':
                _reset_stuck_state(task)
                return {
                    'success': True,
                    'status': 'completed',
                    'steps': steps,
                    'last_screenshot': last_screenshot,
                }

        _reset_stuck_state(task)
        return {
            'success': False,
            'status': 'max_steps_reached',
            'reason': f'Loop encerrado após {MAX_STEPS} passos.',
            'steps': steps,
            'last_screenshot': last_screenshot,
        }
    except (ScreenCaptureError, ModelResponseError, ActionExecutionError) as exc:
        _reset_stuck_state(task)
        return {
            'success': False,
            'status': 'error',
            'reason': str(exc),
            'steps': steps,
            'last_screenshot': last_screenshot,
        }
