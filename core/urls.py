from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_not_required

@login_not_required
def home(request):
	return render(request, 'pages/home/index.html')

urlpatterns = [
    path('', home, name = 'home'),
    path("admin==/", admin.site.urls),
    path('accounts/', include('account.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    