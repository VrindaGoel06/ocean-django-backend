from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import UserReport


@receiver(post_save, sender=UserReport)
def on_userreport_created(sender, instance: UserReport, created: bool, **kwargs):
    if not created:
        return

    transaction.on_commit(lambda: run_proccessing(instance))


def run_proccessing(userreport: UserReport):
    userreport.process()
