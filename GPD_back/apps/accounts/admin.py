from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'role', 'status', 'is_staff')
    list_filter = ('role', 'status')
    search_fields = ('email', 'name')