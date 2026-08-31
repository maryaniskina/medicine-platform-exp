from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.doctors.models import DoctorClinic
from apps.scheduling.serializers import (
    AvailableSlotsResponseSerializer,
    SlotQuerySerializer,
)
from apps.scheduling.services.slots import generate_slots


class AvailableSlotsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Получить свободные слоты врача',
        parameters=[SlotQuerySerializer],
        responses={200: AvailableSlotsResponseSerializer},
    )
    def get(self, request):
        query_serializer = SlotQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        doctor_clinic_id = query_serializer.validated_data[
            'doctor_clinic_id'
        ]
        selected_date = query_serializer.validated_data['date']

        doctor_clinic = DoctorClinic.objects.select_related(
            'doctor',
            'clinic',
        ).filter(
            pk=doctor_clinic_id,
            is_active=True,
            doctor__is_active=True,
            clinic__is_active=True,
        ).first()

        if doctor_clinic is None:
            raise NotFound('Врач в указанной клинике не найден.')

        slots = generate_slots(
            doctor_clinic=doctor_clinic,
            selected_date=selected_date,
        )

        return Response({
            'doctor_clinic_id': doctor_clinic.pk,
            'date': selected_date,
            'slots': slots,
        })
