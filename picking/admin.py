from django.contrib import admin
from .models import PickingDetail, PickingOrder

admin.site.register(PickingOrder)
admin.site.register(PickingDetail)
# Register your models here.
