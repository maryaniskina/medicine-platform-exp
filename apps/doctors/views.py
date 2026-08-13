from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.doctors.models import Doctor
from apps.doctors.serializers import (
    DoctorDetailSerializer,
    DoctorListSerializer,
)


@extend_schema(
    tags=['Doctors'],
    summary='Получить список врачей',
    parameters=[
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Поиск по имени, фамилии и отчеству.',
            required=False,
        ),
        OpenApiParameter(
            name='clinic',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтрация по ID клиники.',
            required=False,
        ),
        OpenApiParameter(
            name='specialization',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Фильтрация по ID специализации.',
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=DoctorListSerializer(many=True),
            description='Страница со списком активных врачей.',
        ),
    },
)
class DoctorListView(ListAPIView):
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        queryset = Doctor.objects.filter(is_active=True)
        search = self.request.query_params.get('search', '').strip()
        clinic_id = self.request.query_params.get('clinic')
        specialization_id = self.request.query_params.get('specialization')

        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(middle_name__icontains=search)
            )

        if clinic_id:
            queryset = queryset.filter(
                clinic_assignments__clinic_id=clinic_id,
                clinic_assignments__is_active=True,
                clinic_assignments__clinic__is_active=True,
            )

        if specialization_id:
            queryset = queryset.filter(
                specializations__id=specialization_id,
                specializations__is_active=True,
            )

        return (
            queryset.prefetch_related(
                'specializations',
            )
            .distinct()
            .order_by('last_name', 'first_name', 'middle_name')
        )


@extend_schema(
    tags=['Doctors'],
    summary='Получить информацию о враче',
    responses={
        200: DoctorDetailSerializer,
        404: OpenApiResponse(
            description='Врач не найден или неактивен.',
        ),
    },
)
class DoctorDetailView(RetrieveAPIView):
    serializer_class = DoctorDetailSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = Doctor.objects.filter(is_active=True).prefetch_related(
        'specializations',
        'clinic_assignments__clinic',
    )
