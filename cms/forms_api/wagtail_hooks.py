"""Show submissions inside the Wagtail admin (Snippets) so editors don't need /django-admin/."""

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from forms_api.models import ApplicationSubmission, ContactSubmission


class ContactSubmissionViewSet(SnippetViewSet):
    model = ContactSubmission
    icon = "mail"
    list_display = ["created_at", "name", "company", "service", "email"]
    list_filter = ["created_at"]
    search_fields = ["name", "email", "company"]
    inspect_view_enabled = True
    add_to_admin_menu = False


class ApplicationSubmissionViewSet(SnippetViewSet):
    model = ApplicationSubmission
    icon = "user"
    list_display = ["created_at", "name", "job_title", "email"]
    list_filter = ["created_at"]
    search_fields = ["name", "email", "job_title"]
    inspect_view_enabled = True
    add_to_admin_menu = False


class SubmissionsGroup(SnippetViewSetGroup):
    menu_label = "Formulareingänge"
    menu_icon = "mail"
    menu_order = 300
    items = (ContactSubmissionViewSet, ApplicationSubmissionViewSet)


register_snippet(SubmissionsGroup)
