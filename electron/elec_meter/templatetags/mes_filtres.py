from django import template

from elec_meter.models import Abonnement

register = template.Library()

@register.filter()
def to_int(value):
    return int(value)

@register.filter()
def etat_compteur(compteur):
    if Abonnement.objects.filter(compteur=compteur):
        return True
    else:
        return False