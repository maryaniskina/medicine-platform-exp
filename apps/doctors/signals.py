from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.doctors.models import Specialization

SPECIALIZATIONS_CACHE_KEY = 'doctors:specializations:list'


@receiver(post_save, sender=Specialization)
@receiver(post_delete, sender=Specialization)
def invalidate_specializations_cache(sender, **kwargs):
    cache.delete(SPECIALIZATIONS_CACHE_KEY)
