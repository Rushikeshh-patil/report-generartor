"""
URL configuration for report_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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

# This is the main URL configuration for the entire project.
urlpatterns = [
    path('admin/', admin.site.urls),
    # This line includes all the URLs from the 'report_generator' app.
    # Any request to the root URL will be forwarded to the app's urls.py.
    path('', include('report_generator.urls')),
    path('todo/', include('todo.urls')),
]