from django.contrib import admin
from .models import UserToken

class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('user','token','expiration_date', 'expired')
    list_filter = ("expired", "expiration_date")
    search_fields = ['user']
    
admin.site.register(UserToken, UserTokenAdmin)
