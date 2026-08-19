from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.clinics.models import Clinic
from apps.clinics.serializers import ClinicSerializer


@extend_schema(
    tags=['Clinics'],
    summary='Получить список клиник',
    parameters=[
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Поиск по названию клиники и адресу.',
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=ClinicSerializer(many=True),
            description='Страница со списком активных клиник.',
        ),
    },
)
class ClinicListView(ListAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = Clinic.objects.filter(is_active=True)
        search = self.request.query_params.get('search', '').strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(address__icontains=search)
            )

        return queryset.order_by('name')


@extend_schema(
    tags=['Clinics'],
    summary='Получить информацию о клинике',
    responses={
        200: ClinicSerializer,
        404: OpenApiResponse(
            description='Клиника не найдена или неактивна.',
        ),
    },
)
class ClinicDetailView(RetrieveAPIView):
    serializer_class = ClinicSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = Clinic.objects.filter(is_active=True)
