import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from brain.computer_use import run_computer_use


def index_view(request):
    return render(
        request,
        'dashboard.html',
        {
            'novnc_url': settings.NOVNC_URL,
        },
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

    if settings.WORKER_URL:
        try:
            response = requests.post(
                f"{settings.WORKER_URL.rstrip('/')}/computer-use/",
                json={'task': task},
                timeout=600,
            )
            try:
                result = response.json()
            except ValueError:
                preview = (response.text or '')[:800]
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'Worker remoto retornou resposta não-JSON.',
                        'worker_status_code': response.status_code,
                        'worker_content_type': response.headers.get('content-type', ''),
                        'worker_response_preview': preview,
                    },
                    status=502,
                )

            return JsonResponse(result, status=response.status_code)
        except requests.RequestException as exc:
            return JsonResponse({'success': False, 'error': f'Falha ao chamar worker remoto: {exc}'}, status=502)

    result = run_computer_use(task)
    status_code = 200 if result.get('success') else 500 if result.get('status') == 'error' else 200
    return JsonResponse(result, status=status_code)
