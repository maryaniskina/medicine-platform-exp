from rest_framework.permissions import BasePermission


class IsDoctor(BasePermission):
    message = 'Доступ разрешён только врачам.'

    def has_permission(self, request, view):
        user = request.user

        return (
            user
            and user.is_authenticated
            and user.role == user.Role.DOCTOR
            and hasattr(user, 'doctor_profile')
        )


class IsPatient(BasePermission):
    message = 'Доступ разрешён только пациентам.'

    def has_permission(self, request, view):
        user = request.user

        return (
            user
            and user.is_authenticated
            and user.role == user.Role.PATIENT
        )
