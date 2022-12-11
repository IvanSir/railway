from django.contrib import admin

from users.models import User, Discount, DiscountType

admin.site.register(User)
admin.site.register(Discount)
admin.site.register(DiscountType)
