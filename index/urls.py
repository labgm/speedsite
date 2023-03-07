from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('processament', views.processament, name='processament'),
    path('runSnakemake', views.run_snakemake, name='runSnakemake'),
    path('get_process_status/', views.get_process_status, name='get_process_status'),
    path('output_snakemake/', views.output_snakemake, name='output_snakemake'),
]