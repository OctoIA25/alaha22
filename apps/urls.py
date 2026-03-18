from django.urls import path

from apps.views import computer_use_view

urlpatterns = [
    path('computer-use/', computer_use_view, name='computer_use'),
]
