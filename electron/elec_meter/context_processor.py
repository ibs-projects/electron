from django.db.models import Sum

from .models import Machine, CreditCompteur
from .forms import RechargeForm, TransfererCreditForm, UploadExcelMeterFile, CreerAbonnementForm, EditerLocalCompteur


def display_infos(request):
    total_recharges = CreditCompteur.objects.aggregate(total=Sum('montant_recharge'))
    return total_recharges

def display_recharge_form(request):
    rechargeform = RechargeForm()
    return {"rechargeform":rechargeform}

def chargerFichierExcelPourCompteur(request):
    uploadExcelMeterFile = UploadExcelMeterFile()
    return {"uploadExcelMeterFile":uploadExcelMeterFile}

def creerAbonnementForm(request):
    return {"abonnementForm":CreerAbonnementForm()}

def formEditerLocalCompteur(request):
    return {"formEditerLocalCompteur":EditerLocalCompteur()}

def afficher_puissances(request):
    cp_puissances = [10,20,30]
    return {"cp_puissances":cp_puissances}

