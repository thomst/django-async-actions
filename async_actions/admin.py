from django.contrib import admin


class ActionTaskModelAdmin(admin.ModelAdmin):
    class Media:
        js = ["admin/js/task-monitoring.js"]
