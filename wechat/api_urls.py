# -*- coding: utf-8 -*-
# __author__ = 'yijingping'
from django.urls import path

from . import views

urlpatterns = [
    path('add/', views.api_add, name="wechat.api_add"),
    path('topic/add/', views.api_topic_add, name="wechat.api_topic_add"),
    path('search/', views.api_search, name="wechat.api_search"),

]
