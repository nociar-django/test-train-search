from django.urls import path
from testTrainApp import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('trains/', views.TrainList.as_view()),
    path('trains/<int:number>/', views.TrainDetail.as_view()),
    path('results/', views.TrainResultList.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
