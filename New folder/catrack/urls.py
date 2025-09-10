"""
URL configuration for catrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from projects.views import ProjectViewSet
from submittals.views import SubmittalViewSet
from rfis.views import RFIViewSet
from reports.views import OverviewView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'submittals', SubmittalViewSet, basename='submittal')
router.register(r'rfis', RFIViewSet, basename='rfi')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ui.urls', namespace='ui')),
    path('api/', include(router.urls)),
    path('api/reports/overview', OverviewView.as_view(), name='reports-overview'),
]
