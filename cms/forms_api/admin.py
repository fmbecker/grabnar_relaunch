from django.contrib import admin

from forms_api.models import ApplicationSubmission, ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "company", "service", "email", "notified")
    list_filter = ("notified", "created_at")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = [f.name for f in ContactSubmission._meta.fields]


@admin.register(ApplicationSubmission)
class ApplicationSubmissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "job_title", "email", "notified")
    list_filter = ("notified", "created_at")
    search_fields = ("name", "email", "job_title")
    readonly_fields = [f.name for f in ApplicationSubmission._meta.fields]
