from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('processament', views.processament, name='processament'),
    path('get_process_status/', views.get_process_status, name='get_process_status'),
    path('outputs/', views.outputs, name='outputs'),
    path('download/', views.download_directory, name='download_directory'),
]