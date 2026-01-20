from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('chat/', views.chat, name='chat'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/chat/', views.chat_stream_api, name='chat_stream_api'),
]