from django.urls import path
from .views import EmpleadoListCreateAPIView, EmpleadoDetailAPIView

urlpatterns = [
    path('', EmpleadoListCreateAPIView.as_view(), name='empleado-list-create'),
    path('<int:pk>/', EmpleadoDetailAPIView.as_view(), name='empleado-detail'),
]
