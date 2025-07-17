from django.urls import path
from .views import ReportGeneratorView

# This defines the URL patterns for the 'report_generator' app.
urlpatterns = [
    # The root path of this app will be handled by the ReportGeneratorView.
    # The .as_view() method is used for class-based views.
    path('', ReportGeneratorView.as_view(), name='report_form'),
]