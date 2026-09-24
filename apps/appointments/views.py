from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.appointments.models import Appointment
from apps.appointments.permissions import IsDoctor, IsPatient
from apps.appointments.serializers import (
    AppointmentCancelSerializer,
    AppointmentCreateSerializer,
    DoctorAppointmentSerializer,
    PatientAppointmentSerializer,
)
from apps.appointments.services import cancel_appointment, create_appointment


class DoctorAppointmentListView(generics.ListAPIView):
    serializer_class = DoctorAppointmentSerializer
    permission_classes = [IsDoctor]

    @extend_schema(
        summary='Получение записей врача',
        description=(
            'Возвращает записи текущего авторизованного врача. '
            'Можно фильтровать по дате, периоду и статусу.'
        ),
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Дата приёма в формате YYYY-MM-DD.',
            ),
            OpenApiParameter(
                name='date_from',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Начало периода в формате YYYY-MM-DD.',
            ),
            OpenApiParameter(
                name='date_to',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Конец периода в формате YYYY-MM-DD.',
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=Appointment.Status.values,
                description='Фильтр по статусу записи.',
            ),
        ],
        responses={
            200: DoctorAppointmentSerializer(many=True),
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=['Appointments'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Appointment.objects.filter(
            doctor_clinic__doctor=self.request.user.doctor_profile,
        ).select_related(
            'patient',
            'doctor_clinic__clinic',
        )

        date_value = self.request.query_params.get('date')
        date_from_value = self.request.query_params.get('date_from')
        date_to_value = self.request.query_params.get('date_to')
        status = self.request.query_params.get('status')

        if date_value and (date_from_value or date_to_value):
            raise ValidationError(
                {
                    'date': 'Укажи дату или диапазон дат, но не оба варианта.',
                }
            )

        if date_value:
            selected_date = parse_date(date_value)
            if selected_date is None:
                raise ValidationError(
                    {
                        'date': 'Используй формат YYYY-MM-DD.',
                    }
                )
            queryset = queryset.filter(start_at__date=selected_date)

        if date_from_value or date_to_value:
            date_from = parse_date(date_from_value or '')
            date_to = parse_date(date_to_value or '')

            if date_from is None or date_to is None:
                raise ValidationError(
                    {
                        'date_from': 'Укажи корректные date_from и date_to.',
                    }
                )

            if date_from > date_to:
                raise ValidationError(
                    {
                        'date_to': 'Дата окончания раньше даты начала.',
                    }
                )

            queryset = queryset.filter(
                start_at__date__gte=date_from,
                start_at__date__lte=date_to,
            )

        if status:
            if status not in Appointment.Status.values:
                raise ValidationError(
                    {
                        'status': 'Неизвестный статус записи.',
                    }
                )
            queryset = queryset.filter(status=status)

        return queryset


class AppointmentCreateView(generics.GenericAPIView):
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsPatient]

    @extend_schema(
        summary='Создание записи на приём',
        description=(
            'Создаёт запись для текущего авторизованного пациента. '
            'Время должно соответствовать расписанию врача и быть свободным.'
        ),
        request=AppointmentCreateSerializer,
        responses={
            201: PatientAppointmentSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=['Appointments'],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = create_appointment(
            patient=request.user,
            doctor_clinic_id=serializer.validated_data['doctor_clinic'].pk,
            start_at=serializer.validated_data['start_at'],
            patient_comment=serializer.validated_data['patient_comment'],
        )

        response_serializer = PatientAppointmentSerializer(appointment)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentCancelView(generics.GenericAPIView):
    serializer_class = AppointmentCancelSerializer
    permission_classes = [IsPatient]

    @extend_schema(
        summary='Отмена записи на приём',
        description=(
            'Отменяет собственную будущую запись пациента. '
            'Завершённые, отменённые и начавшиеся приёмы отменить нельзя.'
        ),
        request=AppointmentCancelSerializer,
        responses={
            200: PatientAppointmentSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=['Appointments'],
    )
    def post(self, request, appointment_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = cancel_appointment(
            patient=request.user,
            appointment_id=appointment_id,
            reason=serializer.validated_data['reason'],
        )

        return Response(
            PatientAppointmentSerializer(appointment).data,
            status=status.HTTP_200_OK,
        )


class PatientAppointmentListView(generics.ListAPIView):
    serializer_class = PatientAppointmentSerializer
    permission_classes = [IsPatient]

    @extend_schema(
        summary='Просмотр собственных записей пациента',
        description=(
            'Возвращает записи текущего пациента. '
            'Доступны фильтры по дате, периоду и статусу.'
        ),
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Дата приёма в формате YYYY-MM-DD.',
            ),
            OpenApiParameter(
                name='date_from',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Начало периода.',
            ),
            OpenApiParameter(
                name='date_to',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Конец периода.',
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                enum=Appointment.Status.values,
                description='Статус записи.',
            ),
        ],
        responses={
            200: PatientAppointmentSerializer(many=True),
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=['Appointments'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Appointment.objects.filter(
            patient=self.request.user,
        ).select_related(
            'doctor_clinic__doctor',
            'doctor_clinic__clinic',
        )

        date_value = self.request.query_params.get('date')
        date_from_value = self.request.query_params.get('date_from')
        date_to_value = self.request.query_params.get('date_to')
        status_value = self.request.query_params.get('status')

        if date_value and (date_from_value or date_to_value):
            raise ValidationError(
                {
                    'date': 'Укажи дату или диапазон дат, но не оба варианта.',
                }
            )

        if date_value:
            selected_date = parse_date(date_value)
            if selected_date is None:
                raise ValidationError(
                    {
                        'date': 'Используй формат YYYY-MM-DD.',
                    }
                )
            queryset = queryset.filter(start_at__date=selected_date)

        if date_from_value or date_to_value:
            date_from = parse_date(date_from_value or '')
            date_to = parse_date(date_to_value or '')

            if date_from is None or date_to is None:
                raise ValidationError(
                    {
                        'date_from': 'Укажи корректные date_from и date_to.',
                    }
                )

            if date_from > date_to:
                raise ValidationError(
                    {
                        'date_to': 'Дата окончания раньше даты начала.',
                    }
                )

            queryset = queryset.filter(
                start_at__date__gte=date_from,
                start_at__date__lte=date_to,
            )

        if status_value:
            if status_value not in Appointment.Status.values:
                raise ValidationError(
                    {
                        'status': 'Неизвестный статус записи.',
                    }
                )
            queryset = queryset.filter(status=status_value)

        return queryset
