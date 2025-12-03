from django.urls import path
from .views import SensorListCreateView, SensorDetailView, MeasurementCreateView
urlpatterns = [
    path('sensors/', SensorListCreateView.as_view(), name='sensor-list'),
    path('sensors/<int:pk>/', SensorDetailView.as_view(), name='sensor-detail'),
    path('measurements/', MeasurementCreateView.as_view(), name='measurement-create')
]
