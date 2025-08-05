from django.contrib import admin
from .models import Product, Category, Material,Seller

class SellerAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_name', 'get_email', 'phone', 'business_name', 'address', 'gst_number']

    def get_name(self, obj):
        return obj.user.get_full_name()  # or obj.user.username
    get_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

admin.site.register(Seller, SellerAdmin)

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Material)
