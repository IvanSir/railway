from django.contrib import admin

from tickets.models import Ticket, Order, ArrivalPoint, Route, City, Carriage, RouteToArrivalPoint, CarriageType

admin.site.register(Ticket)
admin.site.register(Order)
admin.site.register(ArrivalPoint)
admin.site.register(Route)
admin.site.register(City)
admin.site.register(Carriage)
admin.site.register(CarriageType)
admin.site.register(RouteToArrivalPoint)



