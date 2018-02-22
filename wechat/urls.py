# -*- coding: utf-8 -*-
__author__ = 'yijingping'
from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name="wechat.index"),
    path('add/', views.add, name="wechat.add"),
    path('<int:id_>/edit/', views.edit, name="wechat.edit"),
    path('<int:id_>/delete/', views.wechat_delete, name="wechat.wechat_delete"),
    path('<int:id_>/topics/', views.WechatTopicView.as_view(), name="wechat.wechat_topics"),
    path('topic/<int:id_>/', views.topic_detail, name="wechat.topic_detail"),
    path('topic/<int:id_>/edit/', views.topic_edit, name="wechat.topic_edit"),
    path('topic/', views.TopicView.as_view(), name="wechat.topic_list"),
    path('topic/available/', views.TopicAvailableView.as_view(), name="wechat.topic_available_list"),

    path('topic/add/', views.topic_add, name="wechat.topic_add"),
    path('search/', views.search, name="wechat.search"),

    path('keywords/', views.KeywordsView.as_view(), name="wechat.keywords_list"),

    path('proxy/<int:id_>/edit/', views.proxy_edit, name="wechat.proxy_edit"),
    path('proxy/status/', views.proxy_status, name="wechat.proxy_status"),
]
