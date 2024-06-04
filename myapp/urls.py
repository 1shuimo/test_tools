from django.urls import path
from . import views
from .views import process_folder, get_current_pdf, next_pdf, prev_pdf, process_pdf, annotate_data, export_json,get_annotation_status,save_labels_bulk,get_page_data,get_annotation_status
urlpatterns = [
    path('', views.home, name='home'),
    path('process_pdf', process_pdf, name='process_pdf'),
    path('load-json-data/', views.load_json_data, name='json_data'),
    path('process_folder', process_folder, name='process_folder'),
    path('current_pdf', get_current_pdf, name='current_pdf'),
    path('annotate_data', annotate_data, name='annotate_data'),
    path('next_pdf', next_pdf, name='next_pdf'),
    path('prev_pdf', prev_pdf, name='prev_pdf'),
    path('export_json/', export_json, name='export_json'),
    path('label_stats/', views.label_stats, name='label_stats'),
    path('get_label_stats', views.get_label_stats, name='get_label_stats'),
    path('get_annotation_status', get_annotation_status, name='get_annotation_status'),
    path('save_labels_bulk', save_labels_bulk, name='save_labels_bulk'),
    path('get_page_data', get_page_data, name='get_page_data'),    
    path('get_annotation_status', get_annotation_status, name='get_annotation_status'),

]