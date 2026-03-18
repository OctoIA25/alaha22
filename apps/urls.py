from django.urls import path

from apps.views import computer_use_view, healthz_view, index_view

urlpatterns = [
    path('', index_view, name='index'),
    path('healthz', healthz_view, name='healthz'),
    path('computer-use/', computer_use_view, name='computer_use'),
]
