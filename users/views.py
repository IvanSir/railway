from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from users.models import User, Discount, DiscountType
from users.serializers import RetrieveUserSerializer, SignupUserSerializer, DiscountSerializer, DiscountTypeSerializer


class UserViewSet(viewsets.GenericViewSet,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  ):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = RetrieveUserSerializer
    serializer_action_classes = {
        'signup': SignupUserSerializer,
        'retrieve': RetrieveUserSerializer,
        'list': RetrieveUserSerializer
    }

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, super().serializer_class)

    @action(methods=('POST',), detail=False, permission_classes=(AllowAny,))
    def signup(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = DiscountSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset.filter(user=request.user), many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)


class DiscountTypeViewSet(viewsets.ModelViewSet):
    queryset = DiscountType.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = DiscountTypeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)