import json
import time
from datetime import date
from django.http import HttpResponse,JsonResponse

from .services import services
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from elec_meter.models import GWS, InfoSignal, User, Historique, Province, Abonnement, Agent, Ville, \
    Transac, CreditCompteur, Retrait, Machine, Transfert, Client, CompteurAssocie, Emprunt, Identifiants, Achat, \
    RechargeEtTransfert
from rest_framework.response import Response
from datetime import datetime
import base64
from .serializers import *
from .services.utilities import definir_mois, set_data, montant_retrait_en_hexa, payload_recharge
from django.shortcuts import get_object_or_404
from rest_framework.permissions import  IsAuthenticated
from rest_framework.authentication import TokenAuthentication

import requests
headers = requests.utils.default_headers()
url = "http://3.19.22.2:7070/openapi/device/downlink/create"
token = "0h2PPw2AlcKM0R1xXymkFA=="
headers.update({
    "Accept-Encoding": "gzip", "Content-Length": "286", "Content-Type": "application/json",
    'X-Access-Token': '{0}'.format(token),
    "User-Agent": "python-requests/2.26.0"
})
fPORT = 8

def retrait_unites(deveui,montant):
    montant_hexa = montant_retrait_en_hexa(montant)
    montant_hexa = montant_hexa.replace("\n", "").strip()
    data = {
        "devEUI": deveui,
        "confirmed": False,
        "fPort": 8,
        "data": montant_hexa
    }
    data = json.dumps(data)
    req = requests.post(url, headers=headers, data=data)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def liste_provinces(request):
    """Lister toutes les provinces ou en créer un"""
    if request.method == "GET":
        provinces = Province.objects.all()
        serializer = ProvinceSerializer(provinces,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = ProvinceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def historique_donnees(request):
    if request.method == "GET":
        donnees = Historique.objects.order_by("-infos_signal__date_creation")
        serializer = HistoriqueSerializer(donnees,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = HistoriqueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_province(request):
    """Recupere, met à jour ou supprime une province"""
    try:
        province = Province.objects.get(pk=request.data["id_province"])
    except province.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        serializer = ProvinceSerializer(province)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = ProvinceSerializer(province,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_villes(request):
    """Lister toutes les villes ou en créer une"""
    if request.method == "GET":
        villes = Ville.objects.all()
        serializer = ProvinceSerializer(villes,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = VilleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT","DELETE","POST"])
#@authentication_classes([TokenAuthentication])
def details_ville(request):
    """Recupere, met à jour ou supprime une province"""
    print(Ville.objects.get(pk=request.data["id_ville"]))
    try:
        ville = Ville.objects.get(pk=request.data["id_ville"])
    except ville.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        serializer = VilleSerializer(ville)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = VilleSerializer(ville,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_users(request):
    """Lister tous les utilisateurs ou en créer un"""
    if request.method == "GET":
        users = User.objects.all()
        serializer = UserSerializer(users,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_user(request,pk):
    """Recupere, met à jour ou supprime un user"""
    try:
        user = User.objects.get(pk=pk)
    except user.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        serializer = UserSerializer(user)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = UserSerializer(user,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_agents(request):
    """Lister tous les agents ou en créer un"""
    if request.method == "GET":
        agents = Agent.objects.all()
        serializer = AgentSerializer(agents,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = AgentSerializer(data=request.data)
        if Agent.objects.filter(**request.data).exists():
            raise serializers.ValidationError("Cet element existe déja")
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_agent(request,pk):
    """Recupere, met à jour ou supprime un agent"""
    try:
        agent = Agent.objects.get(pk=pk)
    except agent.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        serializer = AgentSerializer(agent)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = AgentSerializer(agent,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_clients(request):
    """Lister tous les clients ou en créer un"""
    if request.method == "GET":
        clients = Client.objects.all()
        serializer = ClientSerializer(clients,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_client(request):
    """Recupere, met à jour ou supprime un client"""
    try:
        client = Client.objects.get(pk=request.data["id_client"])
    except client.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        serializer = ClientSerializer(client)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = ClientSerializer(client,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_abonnements(request):
    """Lister tous les abonnements ou en créer un"""
    if request.method == "GET":
        abonnements = Abonnement.objects.all()
        serializer = AbonnementSerializer(abonnements,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = AbonnementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_abonnement(request):
    """Recupere, met à jour ou supprime un abonnement"""
    try:
        abonnement = Abonnement.objects.get(pk=request.data["id_client"])
    except abonnement.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        serializer = AbonnementSerializer(abonnement)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = AbonnementSerializer(abonnement,data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def transfert(request):
    if request.method == "GET":
        transferts = Transfert.objects.all()
        serializers = TransfertSerializer(transferts,many=True)
        return Response(serializers.data)
    elif request.method == "POST":
        serializer = TransfertSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_gws(request):
    """Lister toutes les gateways ou en créer un"""
    if request.method == "GET":
        gws = GWS.objects.all()
        serializer = GWSSerializer(gws,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = GWSSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def details_transac(request):
    id_transac = request.data["id_transac"]
    if not Transac.objects.filter(id=id_transac):
        return Response({"statut":"echec","msg":"Un transfert avec {0} n'existe pas"})
    else:
        transac = Transac.objects.get(id=id_transac)
        serializer = TransacSerializer(transac)
        return Response(serializer.data)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_machines(request):
    """Lister toutes les gateways ou en créer un"""
    if request.method == "GET":
        machines = Machine.objects.all()
        serializer = MachineSerializer(machines,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = MachineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST","PUT","DELETE"])
#@authentication_classes([TokenAuthentication])
def details_compteur(request):
    try:
        compteur = Machine.objects.get(devEUI=request.data["deveui"])
    except compteur.DoesNotExis:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        serializer = MachineSerializer(compteur)
        return Response(serializer.data)
    elif request.method == "PUT":
        serializer = MachineSerializer(compteur, data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def liste_compteur_client(request,pk):
     try:
         client = get_object_or_404(Client, pk=pk)
     except Exception as e:
         print(e)
         # code 00: methode non authorisée
         return JsonResponse({"statut":"echec","code":"00"})
     if request.method == "GET":
         machines = Machine.objects.filter(client=client)
         serializer = MachineSerializer(machines,many=True)
         return HttpResponse(json.dumps({"statut":"echec","code":"00"}),mimetype="application/json")
     else:
         #code 01: methode non authorisée
         return HttpResponse(json.dumps({"statut":"echec","code":"01"}),mimetype="application/json")

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def derniere_donnees(request):
    compteur = get_object_or_404(Machine,)

@api_view(["GET","POST"])
#@authentication_classes([TokenAuthentication])
def publication_donnees(request):
    """Liste des publications"""
    if request.method == "GET":
        pubs = InfoSignal.objects.filter(date_creation__contains=date.today()).order_by("-id")
        serializer = InfoSignalSerializer(pubs,many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        if Machine.objects.filter(devEUI=request.data["devEUI"]).exists() and GWS.objects.filter(gw_id=request.data["data"]["gwid"]).exists():
            date_heure = datetime.fromtimestamp(int(request.data["time"])/1000)

            #conversion du champ data en hexa
            payload = request.data["data"]["data"]
            payload = payload.encode("ascii")  # getting ascii
            payload = base64.b64decode(payload)  # getting bit format
            payload = payload.hex()  # converting payload into hexadecimal

            #recuperation du code de la commande
            code_commande = payload[0:2]

            #recuperation des gateways qui ont recu le signal
            liste_gateways = ""
            gws = request.data["data"]["gws"]
            i = 0
            while i < len(gws):
                liste_gateways = liste_gateways + " " + gws[i]["id"]
                i = i + 1
            #Enregistrement des données du signal
            indice = int(date_heure.month)
            data = {
                "jour":date_heure.date(),"heure":date_heure.time(),"rssi": request.data["data"]["rssi"],
                "snr": request.data["data"]["snr"],"freq":request.data["data"]["freq"],
                "dr": request.data["data"]["dr"],"adr": request.data["data"]["adr"],
                "classe": request.data["data"]["class"], "fCnt": request.data["data"]["fCnt"],
                "fPort": request.data["data"]["fPort"], "confirmed": request.data["data"]["confirmed"],
                "data":payload,"gwid":request.data["data"]["gwid"],"machine":request.data["devEUI"],
                "liste_gateways":liste_gateways,"mois":definir_mois(indice)

            }
            serializer = InfoSignalSerializer(data=data)
            if serializer.is_valid():
                donnees = serializer.save()
                try:
                    services.switch(donnees.id)
                except Exception as e:
                    print(e)
                    donnees.delete()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return HttpResponse("Le compteur ou la gateway n'est pas enregistré")
    else:
        return HttpResponse("Requete non authorisée")

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def activation_compteur(request):
    if request.method == "POST":
        nom_client = request.data["nom_client"]
        prenom_client = request.data["prenom_client"]
        num_client = request.data["num_client"]
        if Client.objects.filter(nom_client=nom_client,prenom_client=prenom_client,code_client=num_client).exists():
            client = get_object_or_404(Client,code_client=num_client)
            if client.etat_compte == False:
                client.etat_compte = True
                client.save()
            serializer = ClientSerializer(client)
            return Response(serializer.data)
        else:
            return Response({"statut":"echec","msg":"Echec de l'activation. Utilisateur inconnu"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def auth_compteur(request):
    if request.method == "POST":
        num_compteur = request.data["numero"]
        code_compteur = request.data["code"]
        if Machine.objects.filter(devEUI=num_compteur,code_secret=code_compteur).exists():
            compteur = get_object_or_404(Machine,devEUI=num_compteur)
            serializer = MachineSerializer(compteur)
            return Response(serializer.data)
        else:
            return Response({"echec": "Echec"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def afficher_donnees_instantanees(request):
    if request.method == "POST":
        deveui = request.data["deveui"]
        donnees = Historique.objects.filter(infos_signal__machine=deveui,date_creation__contains=date.today()).first()
        serializer = HistoriqueSerializer(donnees)
        return Response(serializer.data)
    else:
        return Response({"echec": "echec"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
#@authentication_classes([TokenAuthentication])
def recuperer_compteurs(request):
    if request.method == "POST":
        id_user = request.data["id_user"]
        if Client.objects.filter(id=id_user).exists():
            client = get_object_or_404(Client,pk=id_user)
            if Machine.objects.filter(client=client).exists():
                compteurs = Machine.objects.filter(client=client)
                serializer = MachineSerializer(compteurs,many=True)
                return Response(serializer.data)
            else:
                return Response({"echec":"Pas de compteur"})
        else:
            return Response({"echec":"Utilisateur inexistant"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def envoi_unites(request):
    if request.method == "POST":
        deveui = request.data["deveui"]
        montant = request.data["montant"]
        if deveui == "":
            return Response({"statut":"echec","msg":"Veuillez renseigner l'expediteur"})
        elif montant == "":
            return Response({"statut": "echec", "msg": "Veuillez renseigner le nombre d'unités à transferer"})
        elif int(montant) < 10:
            return Response({"statut": "echec", "msg": "Impossible de transferer moins de 10 unités"})
        else:
            if not Machine.objects.filter(devEUI=deveui):
                return Response({"statut": "echec", "msg": "Il n'existe pas un compteur avec le numéro {0}".format(deveui)})
            else:
                machine = get_object_or_404(Machine,pk=deveui)
                eq = machine.contrat
                coeff = eq.coeff
                montant_transfert = int(montant) / coeff
                payload = "1201"
                history_data = set_data(fport=8, payload=payload, machine=deveui)
                unites = Historique.objects.filter(machine=machine, date_creation__contains=date.today()).values("unites").first()["unites"]
                transac = Transac(jour=datetime.today(), heure=datetime.now().strftime("%H:%M:%S"),expediteur=machine,unites_expediteur=unites, montant=montant_transfert,
                                  equivalence_unites=int(montant))
                transac.save()
                if montant >= unites:
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                    return Response({"statut": "echec", "msg": "Transaction impossible. Vous ne pouvez pas transferer plus de {0} !".format(unites)})
                elif unites - 10 < int(montant):
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                    return Response({"statut":"echec","msg":"Transaction impossible. Vous ne pouvez pas transferer plus de {0} unités !".format(int(montant-10))})
                else:
                    reste_unites = unites - float(montant)
                    mnt_retrait = montant_retrait_en_hexa(montant_transfert)
                    mnt_retrait = mnt_retrait.replace("\n", "").strip()
                    data = {
                        "devEUI": deveui,
                        "confirmed": False,
                        "fPort": 8,
                        "data": mnt_retrait
                    }
                    data = json.dumps(data)
                    try:
                        i = 0
                        req = requests.post(url, headers=headers, data=data)
                        if req.json()["code"] != 0:
                            while i < 3:
                                req = requests.post(url, headers=headers, data=data)
                                if req.json()["code"] == 0:
                                    break
                                else:
                                    time.sleep(2)
                                    i += 1
                    except Exception as e:
                        print(e)
                        return Response({"statut":"erreur","msg":"Une erreur s'est produite lors du transfert"})
                    transac.etat = "succes"
                    transac.comment = "Transfert effectué avec succès"
                    transac.save()
                    requests.post(url, headers=headers, data=history_data)
                    h = Historique.objects.filter(date_creation__contains=date.today(), infos_signal__machine=machine).first()
                    print(reste_unites)
                    h.unites = reste_unites
                    h.save()
                    return Response({"statut":"succes","msg":"Envoi de {0} unités éffectuée avec succès".format(montant),"id_transac":transac.id,"credit":reste_unites})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def reception(request):
    if request.method == "POST":
        deveui_client = request.data["deveui_client"]
        deveui_fournisseur = request.data["deveui_fournisseur"]
        montant = request.data["montant"]
        id_transac = request.data["id_transac"]
        if deveui_client == "":
            return Response({"statut": "echec", "msg": "Veuillez renseigner le bénéficiaire"})
        elif montant == "":
            return Response({"statut": "echec", "msg": "Veuillez renseigner le nombre d'unités à transferer"})
        else:
            if not Machine.objects.filter(devEUI=deveui_client):
                return Response({"statut": "echec", "msg": "Il n'existe pas un compteur avec le numéro {0}".format(deveui_client)})
            else:
                fournisseur = get_object_or_404(Machine,pk=deveui_fournisseur)
                c_beneficiaire = get_object_or_404(Machine,pk=deveui_client)
                eq = fournisseur.contrat
                coeff = eq.coeff
                montant_transfert = int(montant) / coeff
                unites = Historique.objects.filter(machine=c_beneficiaire, date_creation__contains=date.today()).values("unites").first()["unites"]
                transac = get_object_or_404(Transac,pk=int(id_transac))
                transac.beneficiaire = c_beneficiaire
                transac.save()
                if Emprunt.objects.filter(c_emprunteur=c_beneficiaire,dette_solde=False):
                    dette = Emprunt.objects.filter(c_emprunteur=c_beneficiaire, dette_solde=False)[0]
                    c_fournisseur = dette.c_preteur
                    montant_dette = dette.montant / coeff
                    if montant_dette >= montant_transfert:
                        reste_dette = montant_dette - montant_transfert
                        dette.montant = reste_dette
                        if reste_dette == 0:
                            dette.dette_solde = True
                            dette.etat = "soldé"
                            msg = "Votre dette de {0} unités à été soldé".format(montant_transfert * coeff)
                        elif montant_dette > montant_transfert:
                            dette.dette_solde = False
                            dette.etat = "Non soldé"
                            msg = "Votre dette de {0} unités à été avancé à hauteur de {1}".format(
                                montant_dette * coeff, montant_transfert * coeff)
                        montant_remboursement = payload_recharge(montant_transfert)
                        montant_remboursement = montant_remboursement.replace("\n", "").strip()
                        data = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})
                        try:
                            requests.post(url, headers=headers, data=data)
                            dette.save()
                            transac.etat = "succes"
                            transac.comment = "Transfert effectué avec succès"
                            transac.save()
                            return Response({"statut": "succes", "msg": msg})
                        except Exception as e:
                            print(e)
                            return Response({"statut": "erreur", "msg": "Un problème est survenu lors du transfert"})
                    else:
                        reste = montant_transfert - montant_dette
                        montant_recharge = payload_recharge(reste)
                        montant_recharge = montant_recharge.replace("\n", "").strip()

                        montant_remboursement = payload_recharge(montant_dette)
                        montant_remboursement = montant_remboursement.replace("\n", "").strip()

                        data0 = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8, "data": montant_recharge})
                        data1 = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})

                        try:
                            requests.post(url, headers=headers, data=data0)
                            requests.post(url, headers=headers, data=data1)
                            dette.montant = 0.00
                            dette.dette_solde = True
                            dette.save()
                            transac.etat = "succes"
                            transac.comment = "Transfert effectué avec succès"
                            transac.save()
                            return Response({"statut": "succes","msg": "Votre dette de {0} a été soldé et vous avez rechargé de {1} unités".format(montant_dette * coeff, reste * coeff)})
                        except Exception as e:
                            print(e)
                            return Response({"statut": "erreur", "msg": "Un problème est survenu lors du transfert"})
                else:
                    mnt_ajout = payload_recharge(montant_transfert)
                    mnt_ajout = mnt_ajout.replace("\n", "").strip()
                    try:
                        data = {
                            "devEUI": deveui_client,
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_ajout
                        }
                        data = json.dumps(data)
                        r = requests.post(url, headers=headers, data=data)
                        print(r.json())
                    except Exception as e:
                        print(e)
                        return Response({"statut": "erreur", "msg": "Une erreur système s'est produite"})
                    transac.etat = "succes"
                    transac.comment = "Transfert effectué avec succès"
                    transac.save()
                    #requests.post(url, headers=headers, data=history_data)
                    nouveau_solde = unites+float(montant)
                    Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=c_beneficiaire).update(unites=nouveau_solde)
                    return Response({"statut": "succes","msg": "Transfert de {0} vers le compteur {0} effectué avec succès".format(montant,deveui_fournisseur)})
    else:
        return Response({"statut": "mauvaise requete", "msg": "Requete non authorisée"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def transfert_credit(request):
    commande = "12"
    frame_id = "01"
    if request.method == "POST":
        compteur1 = request.data["compteur1"]
        compteur2 = request.data["compteur2"]
        montant = request.data["montant"]
        if compteur1 == "":
            return Response({"statut":"echec","msg":"Veuillez renseigner l'expediteur"})
        elif compteur2 == "":
            return Response({"statut":"echec","msg":"Veuillez renseigner le beneficiaire"})
        elif compteur1 == compteur2:
            return Response({"msg":"Impossible de transferer le credit à vous-meme"})
        elif montant == "":
                return Response({"statut":"echec","msg": "Veuillez renseigner un montant"})
        elif request.data["montant"] < 10:
            return Response({"statut":"echec","msg": "Impossible de transferer moins de 10 unités"})
        else:
            if not Machine.objects.filter(devEUI=compteur1).exists():
                return Response({"msg":"Un compteur avec le numero {0} n'existe pas".format(compteur1)})
            elif not Machine.objects.filter(devEUI=compteur2).exists():
                return Response({"msg": "Un compteur avec le numero {0} n'existe pas".format(compteur2)})
            else:
                machine1 = get_object_or_404(Machine,pk=compteur1)
                eq = machine1.contrat
                coeff = eq.coeff
                montant_transfert = int(montant) / coeff
                payload_test = commande + frame_id
                data = set_data(fport=8, payload=payload_test, machine=compteur1)
                try:
                    requests.post(url, headers=headers, data=data)
                except Exception as e:
                    print(e)
                    return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
                unites = Historique.objects.filter(machine=compteur1,date_creation__contains=date.today()).values("unites").first()["unites"]
                transac = Transac(jour=datetime.today(), heure=datetime.now().strftime("%H:%M:%S"),
                                  expediteur=Machine.objects.get(devEUI=compteur1),
                                  beneficiaire=Machine.objects.get(devEUI=compteur2),
                                  unites_expediteur=unites, montant=montant_transfert,
                                  equivalence_unites=int(montant))
                transac.save()
                if montant >= unites:
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                    return Response({"statut": "echec", "msg": "Transaction impossible. Vous ne pouvez pas transferer plus de {0} !".format(unites)})
                if unites - 10 < int(montant):
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                    return Response({"statut":"echec","msg":"Transaction impossible. Nombre d'unités insuffisant !"})
                else:
                    nb_initial_data = Historique.objects.filter(date_creation__contains=date.today(),machine=get_object_or_404(Machine,pk=compteur1)).count()
                    c_beneficiaire = get_object_or_404(Machine, pk=compteur2)
                    if Emprunt.objects.filter(c_emprunteur=c_beneficiaire,dette_solde=False):
                        dette = Emprunt.objects.filter(c_emprunteur=c_beneficiaire, dette_solde=False)[0]
                        c_fournisseur = dette.c_preteur
                        montant_dette = dette.montant / coeff
                        if montant_dette >= montant_transfert:
                            reste_dette = montant_dette - montant_transfert
                            dette.montant = reste_dette
                            if reste_dette == 0:
                                dette.dette_solde = True
                                dette.etat = "soldé"
                                msg = "Votre dette de {0} unités à été soldé".format(montant_transfert * coeff)
                            elif montant_dette > montant_transfert:
                                dette.dette_solde = False
                                dette.etat = "Non soldé"
                                msg = "Votre dette de {0} unités à été avancé à hauteur de {1}".format(montant_dette*coeff,montant_transfert * coeff)
                            montant_remboursement = payload_recharge(montant_transfert)
                            montant_remboursement = montant_remboursement.replace("\n", "").strip()
                            data = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})
                            try:
                                requests.post(url, headers=headers, data=data)
                                dette.save()
                                transac.etat = "succes"
                                transac.comment = "Transfert effectué avec succès"
                                transac.save()
                                t = enregistrer_transaction(origine=compteur1,destinataire=compteur2,montant=montant/coeff)
                                t.transfert = transac
                                t.save()
                                return Response({"statut":"succes","msg":msg})
                            except Exception as e:
                                print(e)
                                return Response({"statut":"erreur","msg":"Un problème est survenu lors du transfert"})
                        else:
                            reste = montant_transfert - montant_dette
                            montant_recharge = payload_recharge(reste)
                            montant_recharge = montant_recharge.replace("\n", "").strip()

                            montant_remboursement = payload_recharge(montant_dette)
                            montant_remboursement = montant_remboursement.replace("\n", "").strip()

                            data0 = json.dumps({"devEUI": compteur1, "confirmed": False, "fPort": 8,"data": montant_recharge})
                            data1 = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})

                            try:
                                requests.post(url, headers=headers, data=data0)
                                requests.post(url, headers=headers, data=data1)
                                dette.montant = 0.00
                                dette.dette_solde = True
                                dette.save()
                                transac.etat = "succes"
                                transac.comment = "Transfert effectué avec succès"
                                transac.save()
                                t = enregistrer_transaction(origine=compteur1, destinataire=compteur2, montant=montant/coeff)
                                t.transfert = transac
                                t.save()
                                return Response({"statut":"succes","msg":"Votre dette de {0} a été soldé et vous avez rechargé de {1} unités".format(montant_dette*coeff,reste*coeff)})
                            except Exception as e:
                                print(e)
                                return Response({"statut":"erreur","msg":"Un problème est survenu lors du transfert"})
                    else:
                        mnt_ajout = payload_recharge(montant_transfert)
                        mnt_ajout = mnt_ajout.replace("\n", "").strip()
                        try:
                            retrait_unites(compteur1, montant_transfert)
                        except Exception as e:
                            print(e)
                            return Response({"statut": "erreur", "msg": "Une erreur système s'est produite"})
                        try:
                            data = {
                                "devEUI": compteur2,
                                "confirmed": False,
                                "fPort": 8,
                                "data": mnt_ajout
                            }
                            data = json.dumps(data)
                            requests.post(url, headers=headers, data=data)
                        except Exception as e:
                            print(e)
                            return Response({"statut": "erreur", "msg": "Une erreur système s'est produite"})
                        transac.etat = "succes"
                        transac.comment = "Transfert effectué avec succès"
                        transac.save()
                        t = enregistrer_transaction(origine=compteur1, destinataire=compteur2, montant=montant/coeff)
                        t.transfert = transac
                        t.save()
                        payload = set_data(fport=8, payload=payload_test, machine=compteur1)
                        requ = requests.post(url, headers=headers, data=payload)
                        nb = 0
                        if requ.json()["code"] == 0:
                            while nb < nb_initial_data:
                                requests.post(url, headers=headers, data=payload)
                                time.sleep(2)
                                nb = Historique.objects.filter(date_creation__contains=date.today(),machine=get_object_or_404(Machine,pk=compteur1)).count()
                        return Response({"statut": "succes","msg": "Transfert de {0} vers le compteur {0} effectué avec succès".format(montant, compteur2)})
    else:
        return Response({"statut": "mauvaise requete","msg":"Requete non authorisée"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def retransher_unites(request):
    if request.method == "POST":
        deveui = request.data["deveui"]
        montant = request.data["montant"]
        if not Machine.objects.filter(devEUI=deveui):
            return Response({"statut":"echec","msg":"Compteur inexistant"})
        else:
            montant_hexa = montant_retrait_en_hexa(montant)
            montant_hexa = montant_hexa.replace("\n", "").strip()
            try:
                data = {
                    "devEUI": deveui,
                    "confirmed": True,
                    "fPort": 8,
                    "data": montant_hexa
                }
                data = json.dumps(data)
                req = requests.post(url, headers=headers, data=data)
                return Response({"statut": "ok", "msg": "Succes"})
            except Exception as e:
                print(e)
                return Response({"statut":"Erreur","msg":"Une erreur est survenue"})

#
# @api_view(["POST"])
# #@authentication_classes([TokenAuthentication])
# def retrait_argent(request):
#     commande = "12"
#     frame_id = "01"
#     if request.method == "POST":
#         deveui_client = request.data["deveui_client"]
#         deveui_trader = request.data["deveui_trader"]
#         montant = request.data["montant"]
#         if deveui_client == "":
#             return Response({"statut":"echec","msg":"Veuillez renseigner le client"})
#         elif deveui_trader == "":
#             return Response({"statut":"echec","msg":"Veuillez renseigner le vendeur"})
#         elif deveui_trader == deveui_trader:
#             return Response({"msg":"Impossible d'acheter un article à vous-meme'"})
#         elif montant == "":
#                 return Response({"statut":"echec","msg": "Veuillez renseigner un montant"})
#         elif request.data["montant"] < 1000:
#             return Response({"statut":"echec","msg": "Impossible d'acheter un article de moins de 1000 frs'"})
#         else:
#             if not Machine.objects.filter(devEUI=deveui_client).exists():
#                 return Response({"statut":"echec","msg":"Un compteur avec le numero {0} n'existe pas".format(deveui_client)})
#             elif not Machine.objects.filter(devEUI=deveui_trader).exists():
#                 return Response({"statut":"echec","msg": "Un compteur avec le numero {0} n'existe pas".format(deveui_trader)})
#             else:
#                 payload_test = commande + frame_id
#                 data = set_data(fport=8, payload=payload_test, machine=deveui_client)
#                 try:
#                     requests.post(url, headers=headers, data=data)
#                 except Exception as e:
#                     print(e)
#                     return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
#                 trader = get_object_or_404(Machine,pk=deveui_trader)
#                 eq = trader.contrat
#                 coeff = eq.coeff
#                 unites = Historique.objects.filter(machine=get_object_or_404(Machine,devEUI=deveui_client)).values("unites").first()["unites"]
#                 transac = Transac(jour=datetime.today(), heure=datetime.now().strftime("%H:%M:%S"),
#                                   expediteur=get_object_or_404(Machine, pk=deveui_client), \
#                                   beneficiaire=get_object_or_404(Machine, pk=deveui_trader),
#                                   unites_expediteur=unites, montant=montant,
#                                   equivalence_unites=int(montant) * coeff)
#                 achat = Achat(trader=get_object_or_404(Machine, pk=deveui_trader),client=get_object_or_404(Machine, pk=deveui_client),montant=float(montant))
#                 transac.save()
#                 if unites-10 < int(request.POST["montant"])*coeff :
#                     transac.etat = "echec"
#                     transac.comment = "Unités insuffisantes"
#                     transac.save()
#                     return Response({"etat":"echec","msg":"Echec de l'achat. Unités insuffisantes."})
#                 else:
#                     mnt_retrait = montant_retrait_en_hexa(int(montant))
#                     mnt_retrait = mnt_retrait.replace("\n", "").strip()
#                     mnt_ajout = payload_recharge(montant)
#                     mnt_ajout = mnt_ajout.replace("\n", "").strip()
#                     try:
#                         data = {
#                             "devEUI": deveui_client,
#                             "confirmed": False,
#                             "fPort": 8,
#                             "data": mnt_retrait
#                         }
#                         data = json.dumps(data)
#                         requests.post(url, headers=headers, data=data)
#                     except Exception as e:
#                         print(e)
#                         return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
#                     try:
#                         data = {
#                             "devEUI": deveui_trader,
#                             "confirmed": False,
#                             "fPort": 8,
#                             "data": mnt_ajout
#                         }
#                         data = json.dumps(data)
#                         requests.post(url, headers=headers, data=data)
#                     except Exception as e:
#                         print(e)
#                         return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
#                     transac.etat = "succes"
#                     transac.comment = "Transaction effectuée avec succès"
#                     transac.save()
#                     achat = achat.save()
#                     return Response({"statut":"succes","msg":"Achat effectué avec succès","idAchat":achat.id})
#     else:
#         return Response({"statut": "mauvaise requete","msg":"Requete non authorisée"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recharge_credit(request):
    montant_recharge = request.data["montant_recharge"]
    code_compteur = request.data["code_compteur"]
    if montant_recharge == "" or int(montant_recharge)<1000:
        return Response({"statut":"echec","msg":"Le montant minimum de recharge est 1000 fcfa"})
    elif code_compteur == "":
        return Response({"statut":"echec","msg":"Veuillez renseigner le code du compteur"})
    else:
        if not Machine.objects.filter(devEUI=code_compteur).exists():
            return Response({"statut":"echec","msg":"Ce code compteur n'existe pas"})
        else:
            machine = get_object_or_404(Machine, pk=code_compteur)
            solde_compteur = Historique.objects.filter(date_creation__contains=date.today(), machine=machine).values("unites").first()["unites"]
            credit = CreditCompteur(compteur=machine,montant_recharge=montant_recharge)
            contrat = machine.contrat
            coeff = contrat.coeff
            credit.generer_code_recharge()
            credit.save()
            payload = payload_recharge(int(round(montant_recharge)))
            payload = payload.replace("\n", "").strip()
            data = {
                "devEUI": machine.devEUI,
                "confirmed": False,
                "fPort": 8,
                "data": payload
            }
            data = json.dumps(data)
            try:
                requests.post(url, headers=headers, data=data)
                credit.code_utilise = True
                credit.save()
                donnees_uplink = Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=machine).first()
                donnees_uplink.unites = solde_compteur+float(montant_recharge)*coeff
                donnees_uplink.save()
                transaction = enregistrer_transaction(origine=code_compteur,destinataire=code_compteur,montant=montant_recharge)
                transaction.recharge = credit
                transaction.save()
                return Response({"statut":"succes","msg":"Recharge de {0} fca effectuée avec succès".format(montant_recharge)})
            except Exception as e:
                print(e)
                return Response({"statut":"echec","msg":"Un problème est survenu lors de la recharge"})
    return Response({"statut":"echec","msg":"Operation non valide"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_recharges(request):
    deveui = request.data["deveui"]
    recharges = CreditCompteur.objects.filter(devEUI=deveui)
    serializer = RechargeSerializer(recharges,many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recharges_effectuees(request):
    deveui = request.data["deveui"]
    recharges = CreditCompteur.objects.filter(compteur=get_object_or_404(Machine,pk=deveui),code_utilise=True).order_by('-date_recharge')
    serializer = RechargeSerializer(recharges, many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recharges_non_effectuees(request):
    deveui = request.data["deveui"]
    recharges = CreditCompteur.objects.filter(compteur=get_object_or_404(Machine,pk=deveui),code_utilise=False)
    serializer = RechargeSerializer(recharges, many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_transferts_effectues(request):
    deveui = request.data["deveui"]
    transferts = Transac.objects.filter(expediteur=deveui)
    serializer = TransacSerializer(transferts,many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_transferts_entrants(request):
    deveui = request.data["deveui"]
    transferts = Transac.objects.filter(beneficiaire=deveui)
    serializer = TransacSerializer(transferts,many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_retraits_effectues(request):
    deveui = request.data["deveui"]
    retraits = Retrait.objects.filter(compteur_client=deveui)
    serializer = AchatSerializer(retraits,many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_dernier_transfert(request):
    deveui = request.data["deveui"]
    dernier_transfert = Transac.objects.filter(expediteur=deveui,etat="succes").first()
    serializer = TransacSerializer(dernier_transfert)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_derniere_recharge(request):
    deveui = request.data["deveui"]
    derniere_recharge = CreditCompteur.objects.filter(compteur=deveui).last()
    serializer = RechargeSerializer(derniere_recharge)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def details_achat(request):
    idachat = request.data["idachat"]
    achat = Achat.objects.get(id=idachat)
    serializer = AchatSerializer(achat)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def details_retrait(request):
    idretrait = request.data["idretrait"]
    retrait = Retrait.objects.get(id=idretrait)
    serializer = RetraitSerializer(retrait)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def details_emprunt(request):
    idemprunt = request.data["idemprunt"]
    emprunt = Emprunt.objects.get(id=idemprunt)
    serializer = EmpruntSerializer(emprunt)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def verifier_code_compteur(request):
    code_compteur = request.data["code_compteur"]
    deveui = request.data["deveui"]
    if Machine.objects.filter(devEUI=deveui,code_secret=code_compteur).exist():
        return Response({"reponse":0})
    else:
        return Response({"reponse": 1})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def associer_compteur(request):
    serializer = CompteurAssocieSerialier(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def liste_compteurs_lies(request):
    id_user = request.data["id_user"]
    client = get_object_or_404(Client,pk=id_user)
    if CompteurAssocie.objects.filter(client=client).exists():
        compteurs = CompteurAssocie.objects.filter(client=client)
        serializer = CompteurAssocieSerialier(compteurs,many=True)
        return Response(serializer.data)
    else:
        return  Response({"msg":"Pas de compteurs asocies"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def supprimer_compteur_associe(request):
    deveui = request.data["num_compteur"]
    if not CompteurAssocie.objects.filter(num_compteur=deveui).exists():
        return Response({"etat":"echec","msg":"Ce compteur n'existe plus sur votre liste"})
    else:
        compteur = CompteurAssocie.objects.get(num_compteur=deveui)
        compteur.delete()
        return Response({"etat":"succes","msg":"Un compteur supprimé de la liste"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def equivalence_unite_prix(request):
    if request.method == "POST":
        deveui = request.data["deveui"]
        try:
            compteur = Machine.objects.get(devEUI=deveui)
            equiv = compteur.contrat
            serializer = ContratSerializer(equiv)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return Response({"etat":"erreur","msg":"Un compteur avec ce numéro n'est pas enregistré"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def authentifier_compteur_client(request):
    if request.method == "POST":
        id_client = request.data["id_client"]
        code_compteur = request.data["code_compteur"]
        num_compteur = request.data["num_compteur"]
        try:
            client = Client.objects.get(id=id_client)
        except Exception as e:
            print(e)
            return Response({"etat":"erreur","msg":"Une erreur s'est produite lors de la recupération du client"})
        if Machine.objects.filter(client=client,devEUI=num_compteur,code_secret=code_compteur):
            return Response({"etat":"succes","msg":"operation reussie"})
        else:
            return Response({"etat":"echec","msg":"Compteur inexistant"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def nombre_compteurs_utilisateur(request):
    if request.method == "POST":
        id_client = request.data["id"]
        try:
            client = Client.objects.get(id=id_client)
            nb_machines = Machine.objects.filter(client=client).count()
            nb_machines_actives = Machine.objects.filter(client=client,actif=True).count()
            nb_machines_inactives = Machine.objects.filter(client=client,actif=False).count()
            return Response({"total":nb_machines,"inactives":nb_machines_inactives,"actives":nb_machines_actives})
        except Exception as e:
            return Response({"etat":"erreur","msg":"echec de la recuperation du client"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def supprimer_favoris(request):
    id_client = request.data["id_client"]
    deveui_favoris = request.data["num_favoris"]
    try:
        client = Client.objects.get(id=id_client)
    except Exception as e:
        return Response({"statut":"echec","msg":"Client inexistant"})
    if not Machine.objects.filter(devEUI=deveui_favoris):
        return Response({"statut": "echec", "msg": "Compteur inexistant"})
    else:
        if CompteurAssocie.objects.filter(client=client,num_compteur=deveui_favoris):
            favoris = CompteurAssocie.objects.get(client=client,num_compteur=deveui_favoris)
            favoris.delete()
            return Response({"statut": "succes", "msg": "Favoris supprimé !"})
        else:
            return Response({"statut": "echec", "msg": "Veuillez verifier les champs"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def rapport_dernier_transfert(request):
    expediteur = request.data["expediteur"]
    beneficiaire = request.data["beneficiaire"]
    if Transac.objects.filter(expediteur=expediteur,beneficiaire=beneficiaire).exists():
        transfert = Transac.objects.filter(expediteur=beneficiaire,beneficiaire=beneficiaire).last()
        serializer = TransacSerializer(transfert)
        return Response(serializer.data)
    else:
        return Response({"statut": "echec", "msg": "Echec du rapport"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def activer_compteur(request):
    #import twilio.rest
    if request.method == "POST":
        nom_user = request.data["nom"]
        prenom_user = request.data["prenom"]
        code_user = request.data["code"]
        compteur = request.data["deveui"]
        if Client.objects.filter(nom_client=nom_user, prenom_client=prenom_user, code_client=code_user):
            client = Client.objects.get(code_client=code_user)
            if Machine.objects.filter(client=client, devEUI=compteur):
                machine = Machine.objects.get(devEUI=compteur)
                # account_sid = "AC2ea8e26fa3ab7a9419fc3db1d0d66a84"
                # auth_token = "007d00eabc0f777e49caaf5f7287da5f"
                # twilio_client = twilio.rest.Client(account_sid, auth_token)
                # print(twilio_client)
                #
                # message = twilio_client.messages.create(
                #     body="Le code secret de votre compteur est: {0}".format(machine.code_secret),
                #     to='+24165638018',
                #     from_="+24177901087"
                # )
                #print(message.sid)
                return Response({"etat": "succes", "msg": "Compte activé"})
            else:
                return Response({"etat":"ecec","msg":"Les informations que vous ave renseigner ne sont pas correctes"})
        else:
            return Response({"etat": "echec", "msg": "Il n'existe aucun client avec ces information"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def ajout_favoris(request):
    if request.method == "POST":
        id_client = request.data["client"]
        nom_favoris = request.data["nom_favoris"]
        deveui_favoris = request.data["deveui_favoris"]
        try:
            client = get_object_or_404(Client,pk=id_client)
        except Exception as e:
            print(e)
            return Response({"statut":"erreur","msg":"Une erreur s'est produite lors la création du favoris"})
        if CompteurAssocie.objects.filter(client=client,num_compteur=deveui_favoris):
            return Response({"statut":"echec","msg":"Favoris déjà enregistré"})
        else:
            favoris = CompteurAssocie(client=client,nom_compteur=nom_favoris,num_compteur=deveui_favoris)
            favoris.save()
            print("ca marche")
            return Response({"statut": "succes", "msg": "Favoris enregistré avec succès"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def retrait_argent(request):
    commande = "12"
    frame_id = "01"
    if request.method == "POST":
        deveui_client = request.data["deveui_client"]
        deveui_trader = request.data["deveui_trader"]
        montant = request.data["montant"]
        type_retrait = request.data["type_retrait"]
        if deveui_client == "":
            return Response({"statut":"echec","msg":"Veuillez renseigner l'expediteur"})
        elif deveui_trader == "":
            return Response({"statut":"echec","msg":"Veuillez renseigner le beneficiaire"})
        elif deveui_client == deveui_trader:
            return Response({"statut":"echec","msg":"Impossible de transferer de l'argent à vous-meme"})
        elif montant == "":
                return Response({"statut":"echec","msg": "Veuillez renseigner un montant"})
        elif int(montant) < 1000:
            return Response({"statut":"echec","msg": "Impossible de transferer moins de 1000 francs"})
        else:
            if not Machine.objects.filter(devEUI=deveui_client).exists():
                return Response({"statut":"echec","msg":"Un compteur avec le numero {0} n'existe pas".format(deveui_client)})
            elif not Machine.objects.filter(devEUI=deveui_trader).exists():
                return Response({"statut":"echec","msg": "Un compteur avec le numero {0} n'existe pas".format(deveui_trader)})
            else:
                trader = get_object_or_404(Machine,pk=deveui_trader)
                client = get_object_or_404(Machine,pk=deveui_client)
                eq = trader.contrat
                coeff = eq.coeff
                unites = Historique.objects.filter(machine=client, date_creation__contains=date.today()).values("unites").first()["unites"]
                retrait = Retrait(jour_retrait=datetime.today(), heure_retrait=datetime.now().strftime("%H:%M:%S"),
                                  compteur_client=get_object_or_404(Machine, pk=deveui_client), \
                                  compteur_trader=get_object_or_404(Machine, pk=deveui_trader),montant=montant,
                                  type_retrait=type_retrait,equivalent_montant_unites=int(montant)*coeff)
                retrait.save()
                if unites-10 < int(montant)*coeff :
                    retrait = retrait.etat = "echec"
                    retrait.save()
                    return Response({"etat":"echec","msg":"Echec de l'opération. Unités insuffisantes."})
                else:
                    mnt_retrait = montant_retrait_en_hexa(int(montant))
                    mnt_retrait = mnt_retrait.replace("\n", "").strip()
                    mnt_ajout = payload_recharge(montant)
                    mnt_ajout = mnt_ajout.replace("\n", "").strip()
                    try:
                        data = {
                            "devEUI": deveui_client,
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_retrait
                        }
                        data = json.dumps(data)
                        requests.post(url, headers=headers, data=data)
                    except Exception as e:
                        print(e)
                        return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
                    try:
                        data = {
                            "devEUI": deveui_trader,
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_ajout
                        }
                        data = json.dumps(data)
                        requests.post(url, headers=headers, data=data)
                    except Exception as e:
                        print(e)
                        return Response({"statut":"erreur","msg":"Une erreur système s'est produite"})
                    retrait.etat = "succes"
                    retrait.save()
                    nouveau_solde = unites - float(montant)*coeff
                    payload_test = commande + frame_id
                    h_data = set_data(fport=8, payload=payload_test, machine=deveui_client)
                    time.sleep(2)
                    req = requests.post(url, headers=headers, data=h_data)
                    h = Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=get_object_or_404(Machine,devEUI=deveui_client)).first()
                    h.unites = nouveau_solde
                    h.save()
                    return Response({"statut":"succes","msg":"Transfert de {0} vers le compteur {0} effectué avec succès".format(montant,deveui_trader),"idretrait":retrait.id,"nouveau_solde":nouveau_solde})
    else:
        return Response({"statut": "mauvaise requete","msg":"Requete non authorisée"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def afficher_retraits(request):
    deveui = request.data["deveui"]
    retraits = Retrait.objects.filter(compteur_client=deveui)
    serializer = RetraitSerializer(retraits,many=True)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def changer_etat_compteur(request):
    etat = request.data["etat"]
    deveui = request.data["deveui"]
    machine = get_object_or_404(Machine,pk=deveui)
    if etat == "eteint":
        payload = "A1UB"
        data = {
            "devEUI": deveui,
            "confirmed": False,
            "fPort": 8,
            "data": payload
        }
        data = json.dumps(data)
        try:
            requests.post(url, headers=headers, data=data)
            machine.est_allume = True
            machine.false()
            return Response({"statut":"succes","msg":"Compteur mis en service"})
        except:
            return Response({"statut": "erreur", "msg": "Une erreur s'est produite"})
    else:
        if etat == "allume":
            payload = "A5kB"
            data = {
                "devEUI": deveui,
                "confirmed": False,
                "fPort": 8,
                "data": payload
            }
            data = json.dumps(data)
            try:
                req = requests.post(url, headers=headers, data=data)
                machine.est_allume = False
                machine.save()
                return Response({"statut":"succes","msg":"Compteur mis hors service"})
            except Exception as ex:
                print(ex)
                return Response({"statut": "erreur", "msg": "Une erreur s'est produite"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recuperer_client(request):
    code_client = request.data["code_client"]
    client = get_object_or_404(Client,code_client=code_client)
    serializer = ClientSerializer(client)
    return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def emprunter_unites(request):
    montant_emprunt = request.data["montant_emprunt"]
    deveui_client = request.data["deveui_client"]
    if montant_emprunt == "":
        return Response({"statut":"echec","msg":"Veuillez renseigner le nombre d'unités à emprunter"})
    elif deveui_client == "":
        return Response({"statut": "echec", "msg": "Veuillez renseigner le numéro du compteur"})
    elif not Machine.objects.filter(devEUI=deveui_client):
        return Response({"statut": "echec", "msg": "Un client avec ce numéro n'existe pas "})
    elif Emprunt.objects.filter(c_emprunteur=deveui_client,dette_solde=False):
        return Response({"statut": "echec", "msg": "Opération impossible! Vous avez une dette non encore soldée "})
    if float(montant_emprunt) < 1000:
        return Response({"statut": "echec", "msg": "Opération impossible! Vous ne pouvez pas emprunter moins de 1000 frs"})
    payload_donnees = "1201"
    fournisseur = Machine.objects.get(devEUI="8cf957200000c4a6")
    client = Machine.objects.get(devEUI=deveui_client)
    d_fournisseur = set_data(fport=8, payload=payload_donnees, machine=fournisseur.devEUI)
    d_client = set_data(fport=8, payload=payload_donnees, machine=deveui_client)
    try:
        requests.post(url, headers=headers, data=d_fournisseur)
        requests.post(url, headers=headers, data=d_client)
    except Exception as e:
        print(e)
        return Response({"statut":"erreur","msg":"Une erreur s'est produite "})
    unites_fournisseur = Historique.objects.filter(date_creation__contains=date.today(), machine=fournisseur.devEUI).values("unites").first()["unites"]
    solde_client = Historique.objects.filter(machine=client, date_creation__contains=date.today()).values("unites").first()["unites"]
    if deveui_client == fournisseur.devEUI:
        return Response({"statut":"echec","msg":"Un compteur fournisseur ne peut pas faire un emprunt"})
    eq = fournisseur.contrat
    coeff = eq.coeff
    unites_client = int(montant_emprunt)*coeff
    if int(unites_client) > unites_fournisseur:
        return Response({"statut":"echec","msg":"Echec de l'opération"})
    elif int(unites_client) < 0:
        return Response({"statut":"echec","msg":"Opération impossible"})
    else:
        eq = fournisseur.contrat
        coeff = eq.coeff
        montant_emprunt = int(montant_emprunt)
        mnt_retrait = montant_retrait_en_hexa(montant_emprunt)
        mnt_retrait = mnt_retrait.replace("\n", "").strip()
        mnt_ajout = payload_recharge(montant_emprunt)
        mnt_ajout = mnt_ajout.replace("\n", "").strip()
        emprunt = Emprunt(c_emprunteur=client, c_preteur=fournisseur, montant=float(montant_emprunt)*coeff)
        emprunt.save()
        try:
            data = {
                "devEUI": fournisseur.devEUI,
                "confirmed": False,
                "fPort": 8,
                "data": mnt_retrait
            }
            data = json.dumps(data)
            requests.post(url, headers=headers, data=data)
            data = {
                "devEUI": client.devEUI,
                "confirmed": False,
                "fPort": 8,
                "data": mnt_ajout
            }
            data = json.dumps(data)
            requests.post(url, headers=headers, data=data)
        except Exception as e:
            print(e)
            emprunt.etat = "echec"
            emprunt.save()
            return Response({"statut":"error","msg":"Une erreur s'est produite"})
        emprunt.etat = "succes"
        emprunt.save()
        h = Historique.objects.filter(date_creation__contains=date.today(), infos_signal__machine=client).first()
        h.unites = solde_client + float(montant_emprunt)*coeff
        h.save()
        return Response({"statut":"succes","msg":"Opération éffectuée avec succès. Vous venez d'emprunter {0}".format(montant_emprunt*coeff),\
                         "idemprunt":emprunt.id,"nouveau_solde":h.unites})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recuperer_abonnemnt(request):
    pass

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def deleteC(request):
    d = request.data["comp"]
    c = get_object_or_404(Machine,pk=d)
    c.delete()
    return Response({"ok":"ok"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def deleteEmprunts(request):
    d = request.data["deveui"]
    c = get_object_or_404(Machine,pk=d)
    if Emprunt.objects.filter(c_emprunteur=c):
        for i in Emprunt.objects.filter(c_emprunteur=c):
            i.delete()
        return Response({"ok":"ok"})
    else:
        return Response({"erreur":"erreur"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def envoi_sms(request):
    from twilio import rest
    account_sid = 'ACbd3a149067b6ed55ec759d88e7d345c2'
    auth_token = '627194e6b03879ff17fa830612c1c93a'
    cl = rest.Client(account_sid, auth_token)
    numeroclient = request.data["numeroclient"]
    message = cl.messages.create(
        messaging_service_sid='MG21ccd498ceb27ccf37d7221e1d407455',
        to='+24177901087',
        body="Ok"
    )
    m = cl.messages.get(message.sid)
    print(message.sid)
    return Response({"statut":"succes","msg":"message envoyé"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def liste_compteurs(request):
    if request.method == "POST":
        id_client = request.data["id_client"]
        client = get_object_or_404(Client, pk=id_client)
        compteurs = Machine.objects.filter(abonnement__client=client)
        serializer = MachineSerializer(compteurs, many=True)
        return Response(serializer.data)
    else:
        return Response({"statut":"erreur","msg":"Requete non authorisée"})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def verification_du_client(request):
    if request.method == "POST":
        numeroclient = request.data["numero_client"]
        if not Client.objects.filter(code_client=numeroclient).exists():
            return Response({"etat":"echec","msg":"echec de la verification"})
        else:
            client = Client.objects.get(code_client=numeroclient)
            if not Identifiants.objects.filter(client=client):
                identifiants = Identifiants(client=client)
                identifiants.save()
            else:
                identif = Identifiants.objects.get(client=client)
                identif.delete()
                identifiants = Identifiants(client=client)
                identifiants.save()
            return Response({"etat":"succes","msg":"Vérification réussi","id_client":client.id,"ident":identifiants.code})

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def authentifier_code(request):
    id_client = request.data["id_client"]
    code = request.data["code"]
    if request.method == "POST":
        if not Client.objects.filter(id=id_client):
            return Response({"statut":"echec","msg":"Client inexistant"})
        else:
            client = Client.objects.get(id=id_client)
            if not Identifiants.objects.filter(client=client,code=code):
                return Response({"statut":"echec","msg":"Code invalide"})
            else:
                return Response({"statut": "succes", "msg": "Client authentifié"})
    else:
        return HttpResponse("Requete non authorisée")

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def modifier_mot_de_passe(request):
    if request.method == "POST":
        id_client = request.data["id_client"]
        pwd1 = request.data["pwd1"]
        pwd2 = request.data["pwd2"]
        if not Client.objects.filter(id=id_client):
            return Response({"statut":"echec","msg":"Client inexistant"})
        else:
            client = Client.objects.get(id=id_client)
            if pwd1 != pwd2:
                return Response({"statut":"echec","msg":"Les champs saisis ne sont pas identiques"})
            else:
                if len(pwd1)<4:
                    return Response({"statut":"echec","msg":"Le mot de passe doit contenir au moins 4 caracteres"})
                identifiants = Identifiants.objects.get(client=client)
                identifiants.pdw = pwd1
                identifiants.save()
                return Response({"statut":"succes","msg":"Mot de passe modifié"})
    else:
        return HttpResponse("Requete non authorisée")

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def recuperer_mot_de_passe_client(request):
    deveui = request.data["deveui"]
    id_client = request.data["id_client"]
    if not Client.objects.filter(id=id_client):
        return Response({"statut":"echec","msg":"Client inexistant"})
    elif not Machine.objects.filter(devEUI=deveui):
        return Response({"statut": "echec", "msg": "Compteur inexistant"})
    elif not Abonnement.objects.filter(client=Client.objects.get(id=id_client),compteur=Machine.objects.get(devEUI=deveui)):
        return Response({"statut": "echec", "msg": "Abonnement inexistant"})
    else:
        client = Client.objects.get(id=id_client)
        identifiants = Identifiants.objects.get(client=client)
        pwd = identifiants.pdw
        return Response({"statut":"succes","msg":"Utilisateur authentifié","pwd":pwd})


@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def historique_retraits(request):
    deveui = request.data["deveui"]
    type_retrait = request.data["type_retrait"]
    if not Machine.objects.filter(devEUI=deveui):
        return Response({"statut":"echec","msg":"Compteur inexistant"})
    else:
        mois = datetime.now().month
        compteur = get_object_or_404(Machine,pk=deveui)
        achats = Retrait.objects.filter(compteur_client=compteur,jour_retrait__month=mois,type_retrait=type_retrait).order_by('-jour_retrait')
        serializer = RetraitSerializer(achats, many=True)
        return Response(serializer.data)

@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def changer_mot_de_passe(request):
    if request.method == "POST":
        id_client = request.data["id_client"]
        ancien_pwd = request.data["ancien_pwd"]
        nouveau_pwd = request.data["nouveau_pwd"]
        if not Client.objects.filter(id=id_client):
            return Response({"statut":"echec","msg":"Client inexistant"})
        else:
            client = Client.objects.get(id=id_client)
            identifiants = Identifiants.objects.get(client=client)
            if ancien_pwd != identifiants.pdw:
                return Response({"statut":"echec","msg":"Ancien mot de passe incorrect"})
            identifiants.pdw = nouveau_pwd
            identifiants.save()
            return Response({"statut":"succes","msg":"Mot de passe modifié"})
    else:
        return HttpResponse("Requete non authorisée")


@api_view(["POST"])
#@authentication_classes([TokenAuthentication])
def changer_telephone(request):
    if request.method == "POST":
        id_client = request.data["id_client"]
        nv_num = request.data["telephone"]
        if not Client.objects.filter(id=id_client):
            return Response({"statut":"echec","msg":"Client inexistant"})
        else:
            client = Client.objects.get(id=id_client)
            pass

@api_view(["POST"])
def supprimer_dette(request):
    if request.method=="POST":
        c_preteur = get_object_or_404(Machine,pk=request.data["deveui"])
        dette = Emprunt.objects.filter(c_preteur=c_preteur).last()
        dette.delete()
        return Response({"statut": "ok"})
    else:
        return HttpResponse("Erreur")

def enregistrer_transaction(origine="",destinataire="",montant=0):
    transaction = RechargeEtTransfert(
        compteur=get_object_or_404(Machine,pk=origine),
        benef=get_object_or_404(Machine,pk=destinataire),
        montant=montant
    )
    transaction.save()
    return transaction

@api_view(["POST"])
def emprunts(request):
    compteur = get_object_or_404(Machine,pk=request.data["deveui"])
    emprunts = Emprunt.objects.filter(c_emprunteur=compteur).order_by("-date_emprunt")
    serializer = EmpruntSerializer(emprunts, many=True)
    return Response(serializer.data)
