from django.urls import path
from . import views


app_name = 'base'

urlpatterns = [
    # path('', views.home, name='home'),
    path('', views.HomeView.as_view(), name='home'),
    path('checker', views.CheckerView.as_view(), name='checker'),
]
