from django.contrib import admin


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
