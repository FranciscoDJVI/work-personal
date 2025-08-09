from django.contrib import admin

# MODELS

from . import models

# DASHBOARD
admin.site.site_header = "Dashboard"
admin.site.site_title = "Dashboard"
admin.site.index_title = "Administration"

admin.site.register(models.Products)
admin.site.register(models.Sell)
admin.site.register(models.SellProducts)
admin.site.register(models.Stock)
admin.site.register(models.RegistersellDetail)
admin.site.register(models.Clients)
