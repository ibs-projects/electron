from django.db.models.signals import post_save
from datetime import date
from elec_meter.models import InfoSignal
from notif.models import Notification
from django.dispatch import  receiver


@receiver(post_save,sender=InfoSignal)
def signal_deplacement_compteur(sender,instance,created,*args,**kwargs):
    if created:
        signal_precedent = InfoSignal.objects.filter(jour=date.today(),machine=instance.machine,id__lte=instance.id).last()
        if instance.gwid != signal_precedent.gwid and instance.gwid not in instance.liste_gateways.split():
            Notification.objects.create(
                type_notif="deplacmement_compteur",
                compteur=instance.machine,
                motif="Deplacement du compteur"
            )
        else:
            print("pas de probleme")