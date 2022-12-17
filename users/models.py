from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class User(AbstractUser):
    email = models.EmailField(max_length=64, unique=True, blank=False)
    is_blocked = models.BooleanField(default=False)
    username = models.CharField(max_length=128, unique=False, blank=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f'{self.id} - {self.username}'


class DiscountType(models.Model):
    DISCOUNT_CHOICES = (
        ('limited', 'Limited'),
        ('permanent', 'Permanent')
    )
    discount_type_name = models.CharField(max_length=25, choices=DISCOUNT_CHOICES)
    discount_percent = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    discount_limit = models.IntegerField(null=True, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.discount_type_name == 'limited' and not self.discount_limit:
            raise ValidationError('When discount is limited you need to provide the limit')
        return super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if self.discount_type_name == 'limited':
            return f'{self.discount_type_name}({self.id}) - limit {self.discount_limit}'
        else:
            return f'{self.id} - {self.discount_type_name}'


class Discount(models.Model):
    discount_type = models.ForeignKey('users.DiscountType', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    usage_amount = models.IntegerField(null=False, blank=False, default=0)

    def __str__(self):
        if self.discount_type.discount_type_name == 'limited':
            if self.discount_type.discount_limit - self.usage_amount > 0:
                return f'{self.id} - {self.user.username} {self.discount_type.discount_type_name} - left {self.discount_type.discount_limit - self.usage_amount}'
            else:
                return f'{self.id} - {self.user.username} {self.discount_type.discount_type_name} - expired'

        else:
            return f'{self.id} - {self.user.username} {self.discount_type.discount_type_name}'

