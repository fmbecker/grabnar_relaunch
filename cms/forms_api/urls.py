from django.urls import path

from forms_api.views import ApplicationView, ContactView

urlpatterns = [
    path("contact/", ContactView.as_view(), name="forms_contact"),
    path("application/", ApplicationView.as_view(), name="forms_application"),
]
