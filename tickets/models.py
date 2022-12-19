from django.db import models


class Ticket(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seat_number = models.IntegerField()
    arrival_point = models.IntegerField()
    carriage = models.IntegerField()
    departure_point = models.IntegerField()
    order = models.IntegerField()


    def __str__(self):
        return f'{self.carriage}, Seat: {self.seat_number}'


class ArrivalPoint(models.Model):
    arrival_place = models.CharField(max_length=255)
    arrival_city = models.IntegerField()  # fk to city

    def __str__(self):
        return str(self.id)


class Route(models.Model):
    departure_time = models.DateTimeField(blank=False, null=False)
    departure_city = models.IntegerField()

    def __str__(self):
        return f'From {self.departure_city} at {self.departure_time}'


class RouteToArrivalPoint(models.Model):
    order = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    arrival_time = models.DateTimeField()
    arrival_point = models.IntegerField()
    route = models.IntegerField()


class CarriageType(models.Model):
    CARRIAGE_CHOICES = (
        ('seated', 'Seated'),
        ('coupe', 'Coupe'),
        ('platzkart', 'Platzkart')
    )
    carriage_type_name = models.CharField(max_length=25, choices=CARRIAGE_CHOICES)
    description = models.TextField(max_length=255, null=True, blank=True)


class Carriage(models.Model):
    seat_amount = models.IntegerField()
    carriage_type = models.IntegerField()
    route = models.IntegerField()

    def __str__(self):
        return f'{self.carriage_type}: {self.id}'


class Order(models.Model):
    STATUS_CHOICES = (
        ('fail', 'Fail'),
        ('success', 'Success'),
        ('pending', 'Pending'),
    )
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders')


class City(models.Model):
    city_name = models.CharField(max_length=32, unique=True)
    description = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.city_name
