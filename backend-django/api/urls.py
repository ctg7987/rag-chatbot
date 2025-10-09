"""
API URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sessions', views.SessionViewSet)
router.register(r'messages', views.MessageViewSet)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='health'),
    path('stats/', views.get_stats, name='stats'),
    path('ingest/', views.ingest_documents, name='ingest'),
    path('ask/', views.ask_question, name='ask'),
]

