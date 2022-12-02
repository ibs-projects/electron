from django.db import models
from elec_meter.models import Machine
from django.utils import timezone

class Notification(models.Model):
    compteur = models.ForeignKey(Machine,on_delete=models.DO_NOTHING)
    type_notif = models.CharField(max_length=100)
    date_notif = models.DateTimeField(default=timezone.now)
    motif = models.CharField(max_length=100)

# Create your models here.
