from django.db.models.signals import post_save
from django.dispatch import  receiver
from elec_meter.models import InfoSignal,Notif
from datetime import date

@receiver(post_save,sender=InfoSignal)
def signal_deplacement_compteur(sender,instance,created,*args,**kwargs):
    if created:
        signal_precedent = InfoSignal.objects.filter(jour=date.today(),machine=instance.machine,id__lte=instance.id).last()
        if instance.gwid != signal_precedent.gwid and instance.gwid not in instance.liste_gateways.split():
            Notif.objects.create(
                type_notif="deplacmement_compteur",
                compteur=instance.machine
            )
        else:
            print("pas de probleme")