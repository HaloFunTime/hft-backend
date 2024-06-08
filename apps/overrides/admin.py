from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


def linkify(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """

    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return "-"
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f"admin:{app_label}_{model_name}_change"
        link_url = reverse(view_name, args=[linked_obj.pk])
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name.replace("_", " ")
    return _linkify


class AutofillCreatorModelAdmin(admin.ModelAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        creator = request.GET.get("creator", None)
        if creator is None:
            g = request.GET.copy()
            g.update(
                {
                    "creator": request.user,
                }
            )
            request.GET = g
        return super().add_view(request, form_url, extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + (
                "creator",
                "verifier",
            )
        else:
            return self.readonly_fields
