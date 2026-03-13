from django.urls import include, path

urlpatterns = [
    path('dis/', include('identifiers.urls_di')),
    path('ais/', include('identifiers.urls_ai')),
    path('udidipi/', include('identifiers.urls_udidipi')),
]
