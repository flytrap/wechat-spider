"""wechatspider URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from django.contrib import admin
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_swagger.views import get_swagger_view

from wechat import views_new

# Restful API 路由
router = DefaultRouter()
router.register(r'wechat', views_new.WechatViewSet)
router.register(r'topic', views_new.TopicViewSet)
router.register(r'keywords', views_new.WordViewSet)

schema_view = get_swagger_view(title='Wechat-Spider API')

urlpatterns = [
    path('', RedirectView.as_view(url='wechat/', permanent=False)),
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('wechat/', include('wechat.urls')),

    path('api/wechat/', include('wechat.api_urls')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-token-auth/', obtain_jwt_token),
    path('docs/', schema_view)
]
