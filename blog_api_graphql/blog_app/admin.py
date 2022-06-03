from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(Blog)

class TokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user')
admin.site.register(UserToken, TokenAdmin)