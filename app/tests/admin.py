from django.contrib import admin
from .models import Website, Test, UserManager
# Register your models here.

class TestInline(admin.TabularInline):
    model = Test
    extra = 0


@admin.action(description="Oznacz jako wygenerowane")
def make_generated(modeladmin, request, queryset):
    queryset.update(status="Wygenerowane")

class WebsiteAdmin(admin.ModelAdmin):
    model = Website
    inlines = [TestInline]
    action = [make_generated]
    readonly_fields = ("create_data", "load_data", "redirect_data", "end_data") 
    list_display = ("name", "status", "redirect", "create_data", "user_test")
    fields = ("name", ("status", "redirect"), \
    ("user", "user_test", "user_redirect"), 
    ("create_data", "load_data", "redirect_data", "end_data"),
        "ip_source", "ip_destination", "server_name",  
        "jira", "old_host_name", "description", \
        ("pingdom_org_file", "pingdom_dest_file"), \
        ("load_org_file", "load_dest_file", "load_redirect_file"), ("rtt_org_file", "rtt_dest_file", "rtt_redirect_file"))
    list_per_page = 20
    
    def save_model(self, request, obj, form, change):
        if getattr(obj, "user", None) is None:
            obj.user= request.user
        obj.save()
    



admin.site.register(Website, WebsiteAdmin)
admin.site.register(UserManager)
admin.site.add_action(make_generated)
