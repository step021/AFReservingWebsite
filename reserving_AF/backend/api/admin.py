from django.contrib import admin
from .models import DataLoss, Client, UserClientHistoricalData

# Register your models here.
admin.site.register(DataLoss)
admin.site.register(Client)
admin.site.register(UserClientHistoricalData)
