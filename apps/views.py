import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from brain.computer_use import run_computer_use


def index_view(request):
    return JsonResponse(
        {
            'service': 'alaha22',
            'status': 'ok',
            'routes': {
                'health': '/healthz',
                'computer_use': '/computer-use/',
            },
        }
    )


def healthz_view(request):
    return JsonResponse({'status': 'healthy'})


@csrf_exempt
@require_POST
def computer_use_view(request):
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido.'}, status=400)

    task = str(payload.get('task', '')).strip()
    if not task:
        return JsonResponse({'success': False, 'error': 'Campo task é obrigatório.'}, status=400)

    result = run_computer_use(task)
    status_code = 200 if result.get('success') else 500 if result.get('status') == 'error' else 200
    return JsonResponse(result, status=status_code)
