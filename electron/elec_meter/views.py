import datetime
import json
import sys
import time
from datetime import datetime,date

from django.forms import model_to_dict

from api.serializers import HistoriqueSerializer

from rest_framework.response import Response

sys.path.append('./env/lib/python3.8/site-packages')

import openpyxl
import requests
from django.db.models import Avg, Count, Q,F
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .metier import PROFILES
from api.services.utilities import definir_mois, definir_jour, set_data, payload_to_base64, decimalToHexadecimal, \
    montant_retrait_en_hexa, payload_recharge
from api.services.services import conversion_montant_recharge_base64
from .api_connexion import url, headers, fPORT
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core import serializers

from .forms import RegisterForm, LoginForm, ClientForm, MachineForm, EditPwdAgentForm, \
    CreerAbonnementForm, AddGateWayForm, ClientLoginForm, TransfererCreditForm, UploadExcelMeterFile, \
    EditerLocalCompteur
from .models import Agent, User, Province, Ville, Machine, GWS, Client, CreditSEEG, CreditCompteur, InfoSignal, \
    Reporting, Connexion, Historique, Transac, Abonnement, Emprunt, Contrat, EtatCompteur, RechargeEtTransfert

TYPE_COMPTEUR = ["Mono phasé","Tri phasé"]


# views permettant de lister les objets
#@login_required(login_url='/connexion')

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

#@login_required(login_url='/connexion')
def liste_villes(request):
    context = {"villes": Ville.objects.all()}
    return render(request, "elec_meter/liste_villes.html", context)


#@login_required(login_url='/connexion')
def liste_province(request):
    context = {"provinces": Province.objects.all()}
    return render(request, "elec_meter/liste_provinces.html", context)


#@login_required(login_url='/connexion')
def liste_compteurs(request):
    context = {"machines": Machine.objects.filter(actif=True)}
    return render(request, "elec_meter/liste_compteurs.html", context)


#@login_required(login_url='/connexion')
def liste_gateways(request):
    context = {"gateways": GWS.objects.all()}
    return render(request, "elec_meter/liste_gateways.html", context)


#@login_required(login_url='/connexion')
def liste_agents(request):
    #if "profile" in request.session:
        #profile = request.session["profile"]
    context = {"agents": Agent.objects.all()}
    return render(request, "elec_meter/liste_agents.html", context)


# Views relatives au login et l'enregistrement des utilisateurs
def connexion(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            matricule = form.cleaned_data["matricule"]
            user = authenticate(email=email, password=password)
            if user is not None:
                user = User.objects.get(email=email)
                if Agent.objects.filter(user=user, matricule=matricule).exists():
                    agent = get_object_or_404(Agent, user=user)
                    profile = agent.profile
                    if user.is_active:
                        login(request, user)
                        request.session["profile"] = profile
                        return redirect(reverse("elec_meter:home"))
                    else:
                        messages.add_message(request,messages.WARNING,"Votre profile n'est pas "
                                    "encore activé! Veuillez contacter l'administrateur.")
                        return render(request, "elec_meter/login.html", {"form": form})
                else:
                    messages.add_message(request,messages.ERROR,"Utilisateur non existant !")
                    return render(request, "elec_meter/login.html", {"form": form})
            else:
                messages.add_message(request,messages.ERROR,"Utilisateur non existant !")
                return render(request, "elec_meter/login.html", {"form": form})
    else:
        form = LoginForm(initial={"matricule":"3189760","email":"leauramejill@gmail.com","password":"c5WUc8Kmxa"})
        return render(request, "elec_meter/login.html", {"form": form})


#@login_required(login_url='/connexion')
def creer_utilisateur(request):
    form = RegisterForm(initial={})
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            password = User.objects.make_random_password()
            try:
                if User.objects.filter(email=form.cleaned_data["email"]).exists():
                    messages.add_message(request, messages.ERROR,'Un compte avec la meme adresse existe déjà !')
                    return render(request, "elec_meter/register.html", {"form": form})
                else:
                    user = User(email=form.cleaned_data["email"])
                    user.set_password(password)
                    user.is_active = True
                    user.save()
            except Exception as e:
                print(e)
                messages.add_message(request, messages.ERROR, 'Un problème est survenu lors de la creation de l\'utilisateur !')
                return render(request,"elec_meter/register.html",{"form":form})
            try:
                agent = Agent(nom_agent=form.cleaned_data["nom_agent"], prenom_agent=form.cleaned_data["prenom_agent"], user=user)
                agent.generer_matricule()
                agent.profile = "Opérateur"
                agent.save()
                message = render_to_string("elec_meter/activate_email.html",
                     {"user": user, "domaine": request.META['HTTP_HOST'],
                     "uid": urlsafe_base64_encode(force_bytes(user.id)),
                     "token": default_token_generator.make_token(user),"password": password,
                     "matricule": agent.matricule })
                email_to_send = EmailMessage("Activation du compte", message, to=[form.cleaned_data["email"]])
                email_to_send.send(fail_silently=False)
                messages.add_message(request,messages.INFO,"Un méssage a été envoyé é l'adresse %s pour confirmation" % form.cleaned_data["email"])
                return render(request,"elec_meter/register.html",{"form":form})
            except Exception as e:
                user.delete()
                messages.add_message(request,messages.ERROR,"Echec de création du compte")
                return redirect(reverse("elec_meter:register"))
        else:
            form = RegisterForm(request.POST)
            if form.errors:
                error_exists = "yes"
            return render(request,"elec_meter/register.html",{"form":form,"error_exists":error_exists})
    return render(request,"elec_meter/register.html",{"form":form})


#@login_required(login_url='/connexion')
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None:
        if user.is_active == False:
            user.is_active = True
        return render(request, "elec_meter/activation_compte.html")
    else:
        return HttpResponse("Lien d'activation invalide.")


#@login_required(login_url='/connexion')
def validate(request):
    if request.is_ajax and request.method == "POST":
        reponse = {}
        input = request.POST.get("input")
        if input == "oui":
            if not request.user.is_active:
                request.user.is_active = True
                reponse["input"] = input
            else:
                reponse["input"] = input
        else:
            reponse["input"] = "non"
    else:
        return JsonResponse({'statut': 'Echec', 'msg': 'Requete non valide'})
    reponse = json.dumps(reponse)
    mimetype = 'application/json'
    return HttpResponse(reponse, mimetype)


#@login_required(login_url='/connexion')
def deconnexion(request):
    logout(request)
    print("Deconnexion")
    return redirect(reverse("elec_meter:login"))


#@login_required(login_url='/connexion')
def index(request):
    #request.session["profile"] = request.user.agent.profile
    nb_agents = Agent.objects.aggregate(
        total_users=Count("user"),
        actifs=Count("user",filter=Q(user__is_active=True)),
        inactifs=Count('user', filter=Q(user__is_active=False))
    )
    if nb_agents["total_users"] != 0:
        p_actifs = round(nb_agents["actifs"] / nb_agents["total_users"] * 100,2)
        p_inactifs = round(nb_agents["inactifs"] / nb_agents["total_users"] * 100,2)
    else:
        p_inactifs = 0
        p_actifs = 0
    nb_agents = [nb_agents["actifs"],nb_agents["inactifs"],p_actifs,p_inactifs]
    context = {
        "c_deffectuex": Machine.objects.filter(etat__etat_physique="defectueux").count(),
        "c_avec_abonnement":Abonnement.objects.count(),
        "c_sans_abonnement":Machine.objects.filter(abonnement=None).count(),
        "total_compteurs": Machine.objects.count(),
        "total_clients": Client.objects.count(),
        "nb_agents": nb_agents
    }
    return render(request, "elec_meter/index.html", context)

#@login_required(login_url='/connexion')
def graphe_conso_semaine_passee(request):
    if is_ajax(request=request):
        nom_ville = "infos_signal__machine__ville_machine__nom_ville"
        jour = "infos_signal__jour"
        week_dict = {"Lun": 0, "Mar": 0, "Mer": 0, "Jeu": 0, "Ven": 0, "Sam": 0, "Dim": 0}
        data_dict = {}
        jours_semaine_passee = timezone.now().date() - timedelta(days=7)
        lundi_passe = jours_semaine_passee - timedelta(days=(jours_semaine_passee.isocalendar()[2] - 1))
        lundi_cette_semaine = lundi_passe + timedelta(days=7)
        donnees = Reporting.objects.values(jour, nom_ville).filter(infos_signal__jour__gte=lundi_passe, \
                               infos_signal__jour__lt=lundi_cette_semaine).annotate(tension=Avg("voltage"))

        for i in range(len(donnees)):
            date_jour = donnees[i]["infos_signal__jour"]
            jour = definir_jour(date_jour.weekday())
            data_dict[jour] = donnees[i]["tension"]
        for key, value in week_dict.items():
            if key in data_dict:
                week_dict[key] = data_dict[key]
        reponse = {
            "labels": list(week_dict.keys()),
            "data": list(week_dict.values())
        }
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

def graphe_conso_actuelle_par_ville(request):
    pass

#@login_required(login_url='/connexion')
def recharge_credit_par_province(request):
    if is_ajax(request=request) and request.POST["periode"]:
        periode = request.POST["periode"]
        jours_semaine_passee = timezone.now().date() - timedelta(days=7)
        lundi_passe = jours_semaine_passee - timedelta(days=(jours_semaine_passee.isocalendar()[2] - 1))
        lundi_cette_semaine = lundi_passe + timedelta(days=7)
        data_dict = {}
        if periode == "semaine":
            donnees = Machine.objects.prefetch_related("historiques", "credits").filter(credits__date_recharge__gte=lundi_passe, credits__date_recharge__lt=lundi_cette_semaine).values("ville_machine__province__nom_province") \
                .annotate(cred=Avg("credits__montant_recharge"), tens=Avg("historiques__tension"))
        elif periode == "jour":
            donnees = Machine.objects.prefetch_related("historiques", "credits").filter(credits__date_recharge=datetime.today()).values("ville_machine__province__nom_province") \
                .annotate(cred=Avg("credits__montant_recharge"), tens=Avg("historiques__tension"))

        for prov in Province.objects.all():
            nom_province = prov.nom_province
            for i in range(len(donnees)):
                if nom_province in donnees[i]["ville_machine__province__nom_province"]:
                    data_dict[nom_province] = donnees[i]["cred"]
                else:
                    data_dict[nom_province] = 0
        reponse = {
            "labels": list(data_dict.keys()),
            "data": list(data_dict.values())
        }
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def graphe_analyse(request):
    if is_ajax(request=request):
        v_dict = {}
        c_dict = {}
        e_dict = {}
        liste_mois = {
            "Janv": 0, "Fev": 0, "Mar": 0, "Avr": 0, "Mai": 0, "Jui": 0,
            "Juil": 0, "Aout": 0, "Sept": 0, "Oct": 0, "Nov": 0, "Dec": 0
        }
        dict1 = liste_mois.copy()
        dict2 = liste_mois.copy()
        dict3 = liste_mois.copy()
        donnees = Reporting.objects.values("infos_signal__mois", "current", "voltage", "total_positive_active_energy"). \
            annotate(tension=Avg("voltage"), courant=Avg("current"), energy=Avg("total_positive_active_energy"))
        for i in range(len(donnees)):
            v_dict[donnees[i]["infos_signal__mois"]] = donnees[i]["tension"]
            c_dict[donnees[i]["infos_signal__mois"]] = donnees[i]["courant"]
            e_dict[donnees[i]["infos_signal__mois"]] = donnees[i]["energy"]
        for key, value in dict1.items():
            if key in v_dict:
                dict1[key] = v_dict[key]
                dict2[key] = c_dict[key] / 100
                dict3[key] = e_dict[key] / 100

        reponse = {
            "labels": list(dict1.keys()),
            "data1": list(dict1.values()),
            "data2": list(dict2.values()),
            "data3": list(dict2.values()),
        }
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def graphe_credit_par_mois(request):
    if is_ajax(request=request):
        m_credit_dict = {}
        dict_mois = {
            "Janv": 0, "Fev": 0, "Mar": 0, "Avr": 0, "Mai": 0, "Jui": 0,
            "Juil": 0, "Aout": 0, "Sept": 0, "Oct": 0, "Nov": 0, "Dec": 0
        }
        moy_credit = CreditCompteur.objects.values("date_recharge").annotate(
            moy_credit=Avg("montant_recharge")
        )
        for i in range(len(moy_credit)):
            ind = moy_credit[i]["date_recharge"].month
            mois = definir_mois(ind)
            m_credit_dict[mois] = moy_credit[i]["moy_credit"]

        for key, value in dict_mois.items():
            if key in m_credit_dict:
                dict_mois[key] = m_credit_dict[key]
        reponse = {
            "labels": list(dict_mois.keys()),
            "data": list(dict_mois.values())
        }
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")


# views relatives au profile
#@login_required(login_url='/connexion')
def details_agent(request, id):
    utilisateur = get_object_or_404(Agent, pk=id)
    context = {"utilisateur": utilisateur}
    return render(request, "elec_meter/profile.html", context)

def supprimer_compteur(request):
    if is_ajax(request=request) and request.method == "POST":
        compteur = Machine.objects.get(devEUI=request.POST["compteur"])
        reponse = {}
        try:
            compteur.delete()
            reponse["statut"] = "succes"
            reponse["message"] = "Suppression effective"
        except Exception as e:
            print(e)
            reponse["statut"] = "echec"
            reponse["message"] = "Un problème est survenu lors de la suppression du compteur"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return  HttpResponse(reponse,mimetype)
    else:
        return HttpResponse("Requete non authorisée.")


#@login_required(login_url='/connexion')
def modifier_image_profile(request):
    reponse = {}
    extensions = ["jpg", "png", "jpeg"]
    if request.method == "POST" and is_ajax(request=request):
        if request.POST != "":
            ext = request.FILES["image"].name.split(".")[-1]
            if ext in extensions:
                agent = request.user.agent
                agent.photo_agent = request.FILES["image"]
                agent.save()
                reponse["statut"] = "succes"
                reponse["message"] = "Votre photo de profilr a bien été modifiée !"
            else:
                reponse["statut"] = "echec"
                reponse["message"] = "Format de fichier invalide !"
        else:
            reponse["statut"] = "echec"
            reponse["message"] = "Erreur lors du chargement de votre image !"
    else:
        return HttpResponse("Erreur ajax")
    reponse = json.dumps(reponse)
    mimetype = 'application/json'
    return HttpResponse(reponse, mimetype)


# views relatives aux ajouts des models

#@login_required(login_url='/connexion')
def ajax_ajouter_province(request):
    reponse = {}
    if is_ajax(request=request):
        if request.method == "POST":
            print(request.POST.get("code_province"))
            if request.POST.get("code_province") == "":
                reponse["message"] = "Veuillez renseigner le code de la province"
            elif request.POST.get("nom_province") == "":
                reponse["message"] = "Veuillez renseigner le nom de la province"
            else:
                if Province.objects.filter(code_province=request.POST.get("code_province")).exists():
                    reponse["message"] = "La province avec ce code existe déjà !"
                elif Province.objects.filter(nom_province=request.POST.get("nom_province")).exists():
                    reponse["message"] = "La province avec ce nom existe déja"
                else:
                    try:
                        Province.objects.create(
                            code_province=request.POST.get("code_province"),
                            nom_province=request.POST.get("nom_province")
                        )
                        reponse["statut"] = "succes"
                        reponse["message"] = "Province ajoutée avec succès !"
                    except:
                        reponse["message"] = "Erreur lors de la création de l'élement !"
        reponse = json.dumps(reponse)
        mimetype = 'application/json'
        return HttpResponse(reponse, mimetype)
    return HttpResponse("Erreur ajax !")


#@login_required(login_url='/connexion')
def ajax_ajouter_ville(request):
    reponse = {}
    if is_ajax(request=request):
        if request.method == "POST":
            if request.POST.get("nom_ville") == "":
                reponse["statut"] = "echec"
                reponse["message"] = "Veuillez renseigner le nom de la ville"
            elif request.POST.get("province") == "":
                reponse["statut"] == "echec"
                reponse["message"] = "Veuillez enregistrer une province"
            else:
                if Ville.objects.filter(province=request.POST.get("province"),
                                        nom_ville=request.POST.get("nom_ville")).exists():
                    reponse["statut"] = "echec"
                    reponse["message"] = "Une ville avec le meme nom existe déja dans la meme province"
                elif Ville.objects.filter(nom_ville=request.POST.get("nom_ville")).exists():
                    reponse["statut"] = "echec"
                    reponse["message"] = "Une ville de meme nom existe déjà"
                else:
                    province = get_object_or_404(Province, pk=request.POST.get("province"))
                    Ville.objects.create(
                        province=province,
                        nom_ville=request.POST.get("nom_ville")
                    )
                    reponse["statut"] = "succes"
                    reponse["message"] = "Ville enregistrée avec succès"
            reponse = json.dumps(reponse)
            mimetype = 'application/json'
            return HttpResponse(reponse, mimetype)
        else:
            return HttpResponse("Recquete non authorisée")
    else:
        return HttpResponse("Erreue ajax !")


#@login_required(login_url='/connexion')
def nouveau_compteur(request):
    types_compteur = ["Mono phasé"]
    context = {
        "types_compteur": types_compteur,
        "villes": Ville.objects.all(),
        "contrats": Contrat.objects.all(),
        "clientform": ClientForm(),
        "machineform": MachineForm(),
    }
    if request.method == "POST":
        machineform = MachineForm(request.POST)
        if request.POST["ville_compteur"] == "":
            messages.add_message(request, messages.ERROR, 'Veuillez renseigner la ville du client !')
            return redirect(reverse("elec_meter:nouveau_compteur"))
        elif request.POST["contrat"] == "":
            messages.add_message(request, messages.ERROR, 'Veuillez renseigner le contrat !')
            return redirect(reverse("elec_meter:nouveau_compteur"))
        else:

            if machineform.is_valid():
                ville = get_object_or_404(Ville, pk=request.POST["ville_compteur"])
                if Machine.objects.filter(devEUI=machineform.cleaned_data["devEUI"]):
                    messages.add_message(request, messages.WARNING, 'Un compteur avec ce numéro existe déja !')
                    return redirect(reverse("elec_meter:nouveau_compteur"))
                else:
                    machine = Machine.objects.create(
                        devName=machineform.cleaned_data["devName"],
                        devEUI=machineform.cleaned_data["devEUI"], ville_machine=ville,
                        contrat=get_object_or_404(Contrat,numero_contrat=request.POST["contrat"]),
                        type_machine=request.POST["type_compteur"]
                    )
                    machine.generer_code_machine()
                    machine.save()
                    EtatCompteur.objects.create(compteur=machine)
                    return redirect(reverse("elec_meter:liste_compteurs_libres"))
            else:
                print("ok0000000000")
                context["machineform"] = MachineForm(request.POST)
                if machineform.errors:
                    print(machineform.errors)
                    context["error_value1"] = "erreur1"
                message = "Une erreur s'est produite lors du chargement des données"
                return render(request, "elec_meter/ajout_compteur.html", context)
    return render(request, "elec_meter/ajout_compteur.html", context)


#@login_required(login_url='/connexion')
def ajax_charger_provinces(request):
    prov = {}
    prov_liste = []
    if request.method == "GET" and is_ajax(request=request):
        if Province.objects.all():
            for province in Province.objects.all():
                prov = {"id": province.id, "code_province": province.code_province,
                        "nom_province": province.nom_province}
                prov_liste.append(prov)
            provinces = json.dumps(prov_liste)
            mimetype = 'application/json'
            return HttpResponse(provinces, mimetype)
    else:
        return HttpResponse("Erreur ajax !")

#@login_required(login_url='/connexion')
def recharge_unites(request):
    reponse = {}
    if is_ajax(request=request) and request.method=="POST":
        if request.POST["compteur_a_crediter"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir le numéro du compteur svp."
        elif request.POST["code_recharge"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir le code de recharge."
        else:
            if not Machine.objects.filter(devEUI=request.POST["compteur_a_crediter"]).exists():
                reponse["statut"] = "echec"
                reponse["message"] = "Ce numéro de compteur n'existe pas."
            elif not CreditCompteur.objects.filter(code_recharge=request.POST["code_recharge"],code_utilise=False).exists():
                reponse["statut"] = "echec"
                reponse["message"] = "Veuillez saisir un code de recharge valide svp."
            else:
                machine = get_object_or_404(Machine,pk=request.POST["compteur_a_crediter"])
                credit = get_object_or_404(CreditCompteur,code_recharge=request.POST["code_recharge"])
                solde_compteur = Historique.objects.filter(date_creation__contains=date.today(), machine=machine).values("unites").first()["unites"]
                contrat = machine.contrat
                coeff = contrat.coeff
                montant = credit.montant_recharge
                payload = payload_recharge(int(round(montant)))
                payload = payload.replace("\n","").strip()
                data = {
                    "devEUI":machine.devEUI,
                    "confirmed":False,
                    "fPort":8,
                    "data": payload
                }
                data = json.dumps(data)
                try:
                    req = requests.post(url, headers=headers, data=data)
                    credit.code_utilise = True
                    credit.save()
                    reponse["statut"] = "succes"
                    reponse["message"] = "Recharge éffectuée avec succès"
                except Exception as e:
                    print(e)
                    reponse["statut"] = "echec"
                    reponse["message"] = "Un problème est survenu lors de la recharge."
                donnees_uplink = Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=machine).first()
                donnees_uplink.unites = solde_compteur+float(montant)*coeff
                donnees_uplink.save()
        reponse = json.dumps(reponse)
        mimetype = 'application/json'
        return HttpResponse(reponse,mimetype)
    return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def transfer_credit(request):
    commande = "12"
    frame_id = "01"
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["compteur1"] == "" or request.POST["compteur2"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir le numéro du compteurbénéficiaire."
        elif request.POST["montant"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir un montant svp !"
        elif float(request.POST["montant"]) <1000:
            reponse["statut"] = "echec"
            reponse["message"] = "Vous ne pouvez pas transferer un montant inferieur à 1000 !"
        elif request.POST["compteur1"] == request.POST["compteur2"]:
            reponse["statut"] = "echec"
            reponse["message"] = "Vous ne pouvez pas envoyer de crédits à vous meme."
        else:
            if not Machine.objects.filter(devEUI=request.POST["compteur1"]).exists():
                reponse["statut"] = "echec"
                reponse["message"] = "Un compteur avec le numero {0} n'existe pas".format(request.POST["compteur1"])
            elif not Machine.objects.filter(devEUI=request.POST["compteur2"]).exists():
                reponse["statut"] = "echec"
                reponse["message"] = "Un compteur avec le numero {0} n'existe pas".format(request.POST["compteur2"])
            else:
                machine1 = get_object_or_404(Machine,pk=request.POST["compteur1"])
                machine2 = get_object_or_404(Machine,pk=request.POST["compteur2"])
                payload_test = commande + frame_id
                data = set_data(fport=8,payload=payload_test,machine=machine1)
                try:
                    requests.post(url, headers=headers, data=data)
                except Exception as e:
                    print(e)
                eq = machine1.contrat
                coeff = eq.coeff
                unites = Historique.objects.filter(date_creation__contains=date.today(),machine=machine1).values("unites").first()["unites"]
                transac = Transac(jour=datetime.today(),heure=datetime.now().strftime("%H:%M:%S"),expediteur=machine1, \
                          beneficiaire=machine2,unites_expediteur=unites,montant=request.POST["montant"],equivalence_unites=int(request.POST["montant"])*coeff)
                transac.save()
                if int(request.POST["montant"])*coeff >= unites:
                    reponse["statut"] = "echec"
                    reponse["message"] = "Transfert impossible. Ce compteur ne possede que {}.".format(unites)
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                if unites-10 < int(request.POST["montant"])*coeff:
                    reponse["statut"] = "echec"
                    reponse["message"] = "Echec du transfert. Vous ne pouvez pas transferer plus de {0}.".format(unites-10)
                    transac.etat = "echec"
                    transac.comment = "Unités insuffisantes"
                    transac.save()
                else:
                    mnt_retrait = montant_retrait_en_hexa(int(request.POST["montant"]))
                    mnt_retrait = mnt_retrait.replace("\n","").strip()
                    mnt_ajout = payload_recharge(request.POST["montant"])
                    mnt_ajout = mnt_ajout.replace("\n","").strip()
                    try:
                        data = {
                            "devEUI":request.POST["compteur1"],
                            "confirmed":False,
                            "fPort":8,
                            "data":mnt_retrait
                        }
                        data = json.dumps(data)
                        req = requests.post(url, headers=headers, data=data)
                        data = {
                            "devEUI": request.POST["compteur2"],
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_ajout
                        }
                        data = json.dumps(data)

                        req = requests.post(url, headers=headers, data=data)
                        transac.etat = "succes"
                        transac.comment = "Transaction effectuée avec succès"
                        transac.save()
                        reponse["statut"] = "succes"
                        reponse["message"] = "Transfert de {0} effectué vers le compteur {1}".format(request.POST["montant"], request.POST["compteur2"])
                    except Exception as e:
                        print(e)
                        transac.etat = "echec"
                        transac.comment = "Un problème au niveau du serveur"
                        transac.save()
                        reponse["statut"] = "echec"
                        reponse["message"] = "Echec ! Un problème est survenu lors du transfert de credit"

        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse,mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

def emprunter_unites(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.method == "POST":
            if request.POST["montant_emprunt"] == "" or request.POST["deveui_client"] == "":
                reponse["statut"] = "echec"
                reponse["message"] = "Veuillez remplir tous les champs du formulaire puis réessayez."
            elif not Machine.objects.filter(devEUI=request.POST["deveui_client"]):
                reponse["statut"] = "echec"
                reponse["message"] = "Un compteur avec ce numéro n'existe pas"
            elif Emprunt.objects.filter(c_emprunteur=Machine.objects.get(devEUI=request.POST["deveui_client"]),dette_solde=False):
                reponse["statut"] = "echec"
                reponse["message"] = "Impossible d'emprunter du crédit ! Vous avez une dette non encore soldée."
            else:
                payload_donnees = "1201"
                fournisseur = Machine.objects.get(devEUI="8cf957200000c4a6")
                client = Machine.objects.get(devEUI=request.POST["deveui_client"])
                d_fournisseur = set_data(fport=8, payload=payload_donnees, machine=fournisseur.devEUI)
                d_client = set_data(fport=8, payload=payload_donnees, machine=request.POST["deveui_client"])
                try:
                    requests.post(url,headers=headers,data=d_fournisseur)
                    requests.post(url,headers=headers,data=d_client)
                except Exception as e:
                    reponse["statut"] = "erreur"
                    reponse["message"] = "Une erreur s'est produite"
                    print(e)
                unites_fournisseur = Historique.objects.filter(date_creation__contains=date.today(), machine=fournisseur.devEUI).values("unites").first()["unites"]
                unites_client = Historique.objects.filter(date_creation__contains=date.today(), machine=client.devEUI).values("unites").first()["unites"]
                if request.POST["deveui_client"] == fournisseur.devEUI:
                    reponse["statut"] = "echec"
                    reponse["message"] = "Un compteur fournisseur ne pas faire un emprunt d'unités"
                elif int(request.POST["montant_emprunt"]) >= unites_fournisseur:
                    reponse["statut"] = "echec"
                    reponse["message"] = "Echec de l'operation"
                elif int(request.POST["montant_emprunt"])<0:
                    reponse["statut"] = "echec"
                    reponse["message"] = "Opération impossible."
                else:
                    eq = fournisseur.contrat
                    coeff = eq.coeff
                    montant_emprunt = int(request.POST["montant_emprunt"]) / coeff
                    mnt_retrait = montant_retrait_en_hexa(montant_emprunt)
                    mnt_retrait = mnt_retrait.replace("\n", "").strip()
                    mnt_ajout = payload_recharge(montant_emprunt)
                    mnt_ajout = mnt_ajout.replace("\n", "").strip()
                    emprunt = Emprunt.objects.create(c_emprunteur=client,c_preteur=fournisseur,
                          montant=float(request.POST["montant_emprunt"]),montant_en_cfa=float(request.POST["montant_emprunt"])/coeff)
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
                        emprunt.etat = "echec"
                        emprunt.save()
                        reponse["statut"] = "erreur"
                        reponse["message"] = "Une erreur s'est produite pendant l'opération"
                    emprunt.etat = "succes"
                    emprunt.save()
                    reponse["statut"] = "succes"
                    reponse["message"] = "Opération éffectuée avec succès. Vous venez d'emprunter {0} unités".format(request.POST["montant_emprunt"])
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def envoi_unites(request):
    commande = "12"
    frame_id = "01"
    form = TransfererCreditForm()
    if request.method == "POST":
        form = TransfererCreditForm(request.POST)
        if form.is_valid():
            payload_test = commande + frame_id
            expediteur = get_object_or_404(Machine,pk=request.POST["expediteur"])
            receveur = get_object_or_404(Machine,pk=request.POST["beneficiaire"])
            eq = expediteur.contrat
            coeff = eq.coeff
            montant_transfert = int(form.cleaned_data["unites_a_transferer"])/coeff
            solde_expediteur = Historique.objects.filter(date_creation__contains=date.today(),machine=expediteur).values("unites").first()["unites"]
            solde_beneficiaire = Historique.objects.filter(date_creation__contains=date.today(),machine=receveur).values("unites").first()["unites"]
            transac = Transac(jour=datetime.today(), heure=datetime.now().strftime("%H:%M:%S"),expediteur=expediteur,beneficiaire=receveur,
                              unites_expediteur=solde_expediteur, montant=montant_transfert,equivalence_unites=int(form.cleaned_data["unites_a_transferer"]))
            transac.save()
            if form.cleaned_data["unites_a_transferer"] >= solde_expediteur:
                transac.etat = "echec"
                transac.comment = "Unités insuffisantes"
                transac.save()
                messages.add_message(request, messages.WARNING,"Transaction impossible. Vous ne pouvez pas transfere plus de {0} !".format(solde_expediteur-10))
                return render(request, "elec_meter/transfert_credit.html", {"form": form})
            if solde_expediteur-10 < int(form.cleaned_data["unites_a_transferer"]):
                transac.etat = "echec"
                transac.comment = "Unités insuffisantes"
                transac.save()
                messages.add_message(request,messages.WARNING,"Transaction impossible. Nombre d'unités insuffisante !")
                return render(request,"elec_meter/transfert_credit.html",{"form":form})
            elif int(form.cleaned_data["unites_a_transferer"]) > solde_expediteur:
                messages.add_message(request, messages.WARNING, "Transaction impossible. Vous ne pouvez pas transferer plus de {0} unités!".format(solde_expediteur))
                return render(request, "elec_meter/transfert_credit.html", {"form": form})
            else:
                uplink_expediteur = Historique.objects.filter(date_creation__contains=date.today(), infos_signal__machine=expediteur).first()
                uplink_beneficiaire = Historique.objects.filter(date_creation__contains=date.today(), infos_signal__machine=receveur).first()
                if Emprunt.objects.filter(c_emprunteur=receveur,dette_solde=False):
                    dette = Emprunt.objects.filter(c_emprunteur=receveur,dette_solde=False)[0]
                    c_fournisseur = dette.c_preteur
                    montant_dette = dette.montant / coeff
                    if montant_dette >= montant_transfert:
                        reste_dette = montant_dette - montant_transfert
                        dette.montant = reste_dette
                        if reste_dette == 0:
                            dette.dette_solde = True
                            dette.etat = "soldé"
                            msg = "Votre dette de {0} unités a été soldée".format(montant_transfert*coeff)
                        elif montant_dette > montant_transfert:
                            dette.dette_solde = False
                            dette.etat = "Non soldé"
                            msg = "La dette du compteur {0} de {1} unités a été remboursée à hauteur de {2} unités".format(request.POST["beneficiaire"],round(montant_dette*coeff,0),montant_transfert * coeff)
                        montant_remboursement = payload_recharge(montant_transfert)
                        montant_remboursement = montant_remboursement.replace("\n", "").strip()
                        data = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})
                        try:
                            requests.post(url, headers=headers, data=data)
                            dette.save()
                            transac.etat = "succes"
                            transac.comment = "Transfert effectué avec succès"
                            transac.save()
                            messages.add_message(request, messages.INFO, msg)
                            uplink_expediteur.unites = solde_expediteur-montant_transfert * coeff
                            uplink_expediteur.save()
                            return render(request, "elec_meter/transfert_credit.html", {"form": form})
                        except Exception as e:
                            print(e)
                            messages.add_message(request, messages.ERROR, "Un problème est survenu lors du transfert")
                            return render(request, "elec_meter/transfert_credit.html", {"form": form})
                    else:
                        reste = montant_transfert - montant_dette
                        montant_recharge = payload_recharge(reste)
                        montant_recharge = montant_recharge.replace("\n", "").strip()

                        montant_remboursement = payload_recharge(montant_dette)
                        montant_remboursement = montant_remboursement.replace("\n", "").strip()

                        data0 = json.dumps({"devEUI": form.cleaned_data["beneficiaire"], "confirmed": False, "fPort": 8,"data": montant_recharge})
                        data1 = json.dumps({"devEUI": c_fournisseur.devEUI, "confirmed": False, "fPort": 8,"data": montant_remboursement})

                        try:
                            requests.post(url, headers=headers, data=data0)
                            r = requests.post(url, headers=headers, data=data1)
                            dette.montant = 0.00
                            dette.dette_solde = True
                            dette.save()
                            transac.etat = "succes"
                            transac.comment = "Transfert effectué avec succès"
                            transac.save()
                            #form = TransfererCreditForm(initial={"expediteur": request.POST["expediteur"],"beneficiaire": request.POST["beneficiaire"]})
                            messages.add_message(request, messages.INFO, "La dette du compteur {0} de {1} a été soldée et a été rechargé de {2} unités".format(form.cleaned_data["beneficiaire"],montant_dette*coeff,reste*coeff))
                            uplink_expediteur.unites = solde_expediteur+montant_dette*coeff
                            uplink_beneficiaire.unites = solde_beneficiaire+reste*coeff
                            uplink_beneficiaire.save()
                            uplink_expediteur.save()
                            return render(request, "elec_meter/transfert_credit.html", {"form": form})
                        except Exception as e:
                            print(e)
                            messages.add_message(request, messages.ERROR, "Un problème est survenu lors du transfert")
                            return render(request, "elec_meter/transfert_credit.html", {"form": form})
                else:
                    mnt_retrait = montant_retrait_en_hexa(montant_transfert)
                    mnt_retrait = mnt_retrait.replace("\n", "").strip()
                    mnt_ajout = payload_recharge(montant_transfert)
                    mnt_ajout = mnt_ajout.replace("\n", "").strip()
                    try:
                        data = {
                            "devEUI": form.cleaned_data["expediteur"],
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_retrait
                        }
                        data = json.dumps(data)
                        requests.post(url, headers=headers, data=data)
                    except Exception as e:
                        print(e)
                        messages.add_message(request, messages.ERROR, "Une erreur système s'est produite")
                        return render(request, "elec_meter/transfert_credit.html", {"form": form})
                    try:
                        data = {
                            "devEUI": form.cleaned_data["beneficiaire"],
                            "confirmed": False,
                            "fPort": 8,
                            "data": mnt_ajout
                        }
                        data = json.dumps(data)
                        requ = requests.post(url, headers=headers, data=data)
                    except Exception as e:
                        print(e)
                        messages.add_message(request, messages.ERROR, "Une erreur système s'est produite")
                        return render(request, "elec_meter/transfert_credit.html", {"form": form})
                    messages.add_message(request, messages.INFO,"Transfert de {0} vers le compteur {1} effectué avec succès".format(
                                             form.cleaned_data["unites_a_transferer"],
                                             form.cleaned_data["beneficiaire"]))
                    transac.etat = "succes"
                    transac.comment = "Transfert effectué avec succès"
                    transac.save()
                    form = TransfererCreditForm(initial={"expediteur": request.POST["expediteur"], "beneficiaire": request.POST["beneficiaire"]})
                    # payload = set_data(fport=8, payload=payload_test, machine=request.POST["beneficiaire"])
                    # requests.post(url, headers=headers, data=payload)
                    uplink_expediteur.unites = solde_expediteur-montant_transfert*coeff
                    uplink_beneficiaire.unites = solde_beneficiaire+montant_transfert*coeff
                    uplink_expediteur.save()
                    uplink_beneficiaire.save()
                    time.sleep(2)
                    payload = set_data(fport=8, payload=payload_test, machine=request.POST["expediteur"])
                    r = requests.post(url, headers=headers, data=payload)
                    RechargeEtTransfert.objects.create(
                        compteur=get_object_or_404(Machine,pk=request.POST["expediteur"]),
                        montant=montant_transfert,transfert=transac,type_transaction="transfert",
                        benef=get_object_or_404(Machine,pk=request.POST["expediteur"])
                    )
                    return render(request, "elec_meter/transfert_credit.html", {"form": form})
        else:
            message_derreur = list(form.errors.values())[0]
            return render(request, "elec_meter/transfert_credit.html", {"form":form,"message_derreur":message_derreur})
    else:
        return render(request, "elec_meter/transfert_credit.html", {"form":form})



#@login_required(login_url='/connexion')
def transactions(request,num_compteur):
    transferts = Transac.objects.filter(expediteur=get_object_or_404(Machine,pk=num_compteur)).order_by("-jour")
    toutes = RechargeEtTransfert.objects.filter(compteur=get_object_or_404(Machine,pk=num_compteur))
    recharges = CreditCompteur.objects.filter(compteur=num_compteur).order_by("-date_recharge")
    return render(request,"elec_meter/transactions.html",{"recharges":recharges,"transferts":transferts,"compteur":num_compteur,"toutes":toutes})

#@login_required(login_url='/connexion')
def liste_clients(request):
    clients = Client.objects.all().distinct("nom_client","prenom_client")
    return render(request,"elec_meter/liste_clients.html",{"clients":clients})

#@login_required(login_url='/connexion')
def ajout_gateway(request):
    form = AddGateWayForm()
    context = {
        "form": form,
        "villes": Ville.objects.all()
    }
    if request.method == "POST":
        form = AddGateWayForm(request.POST)
        if form.is_valid():
            gateway = GWS(
                gw_id=form.cleaned_data["num_gw"],nom_gateway=form.cleaned_data["nom_gw"],
                ville_gw=get_object_or_404(Ville,pk=request.POST["ville_gw"]),adr_gw=form.cleaned_data["adr_gw"],
                lat_gw=form.cleaned_data["latitude"],lon_gw=form.cleaned_data["longitude"],
                description=form.cleaned_data["desc_gw"]
            )
            gateway.save()
            return redirect(reverse("elec_meter:liste_gateways"))
        else:
            context["form"] = AddGateWayForm(request.POST)
            if form.errors:
                context["error"] = "yes"
            return render(request,"elec_meter/ajout_gateway.html",context)
    return render(request,"elec_meter/ajout_gateway.html",context)

#@login_required(login_url='/connexion')
def editer_donnees_personnelles(request):
    if is_ajax(request=request) and request.method=="POST":
        reponse = {}
        if request.POST["nom_agent"] == "":
            reponse["statut"],reponse["message"] = "echec","Le nom est obligatoire"
        elif request.POST["prenom_agent"] == "":
            reponse["statut"], reponse["message"] = "echec", "Le prénom est obligatoire"
        elif request.POST["email"] == "":
            reponse["statut"], reponse["message"] = "echec", "L'adresse email est obligatoire"
        elif request.POST["email"] == "":
            reponse["statut"], reponse["message"] = "echec", "Le profile est obligatoire"
        else:
            print(request.POST.get("adr_agent"))
            print(request.POST.get("ville_agent"))
            ville = get_object_or_404(Ville,pk=request.POST.get("ville_agent"))
            agent = get_object_or_404(Agent,pk=request.POST["id_agent"])
            user = User.objects.get(agent=agent)
            print("dsfgh")
            agent.nom_agent = request.POST["nom_agent"]
            agent.prenom_agent = request.POST["prenom_agent"]
            agent.adr_agent = request.POST.get("adr_agent")
            agent.user.email = request.POST["email"]
            agent.profile = request.POST["profile"]
            agent.ville_agent = ville
            user.telephone = request.POST.get("tel")
            user.save()
            agent.save()
            reponse["statut"], reponse["message"] = "succes", "Profile modifié avec succès"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    return HttpResponse("requete non authorisé")

#@login_required(login_url='/connexion')
def creer_client(request):
    form = ClientForm()
    message_derreur = ""
    villes = Ville.objects.all()
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid() and request.POST["ville_client"] != "":
            client = Client(
                nom_client=form.cleaned_data["nom_client"].upper(),
                prenom_client=form.cleaned_data["prenom_client"].title(),
                tel_client=form.cleaned_data["tel_client"],
                email=form.cleaned_data["email_client"],
                adresse_client=form.cleaned_data["adr_client"],
                ville_client=get_object_or_404(Ville,pk=request.POST["ville_client"]),
            )
            client.generer_code_client()
            client.save()
            messages.add_message(request, messages.INFO, 'Client enregistré avec succès !')
            return redirect(reverse("elec_meter:liste_clients"))
        if form.errors:
            message_derreur = list(form.errors.values())[0]
    return render(request, "elec_meter/ajout_client.html", {"form": form,"villes":villes,"message_derreur":message_derreur })

#@login_required(login_url='/connexion')
def regenerer_code_client(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        client = get_object_or_404(Client,pk=request.POST["id_client"])
        try:
            client.generer_code_client()
            client.save()
            reponse["message"] = "Nouveau code client: %s" % client.code_client
        except Exception as e:
            print(e)
            reponse["message"] = "Echec de la génération du code"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def details_client(request,id):
    client = get_object_or_404(Client,pk=id)
    abonnements = Abonnement.objects.filter(client=client)
    return render(request,"elec_meter/details_client.html",{"client":client,"abonnements":abonnements})

def retour_abonnement(request,param1,param2,form):
    print("dfghjklmùsdfghjklm")
    if param1 != "compteur" or param1 != "client":
        return render(request,"elec_meter/creer_abonnement.html",{"form":form,"param":param1})
    else:
        return redirect(reverse("elec_meter:nouvel_abonnement",kwargs={"param1":param1,"param1":param2}),kwargs={"form":form,"param":param1})

#@login_required(login_url='/connexion')
def creer_abonnement(request,param1,param2):
    if param1 == 'compteur':
        form = CreerAbonnementForm(initial={"numero_compteur":param2})
    elif param1 == 'client':
        form = CreerAbonnementForm(initial={"numero_client": param2})
    else:
        form = CreerAbonnementForm()
    if request.method == "POST":
        form = CreerAbonnementForm(request.POST)
        if form.is_valid():
            if not Client.objects.filter(code_client=form.cleaned_data["numero_client"]).exists():
                messages.add_message(request, messages.ERROR,"Ce client n'existe pas dans la base de données")
                return redirect(reverse("elec_meter:nouvel_abonnement",kwargs={"param1":param1,"param2":param2}),kwargs={"param":param1,"form":form})
            elif not Machine.objects.filter(devEUI=get_object_or_404(Machine,pk=form.cleaned_data["numero_compteur"])):
                messages.add_message(request, messages.WARNING, "Le numéro de compteur renseigné n'existe pas")
                return retour_abonnement(request,param1,param2,form)
            else:
                client = get_object_or_404(Client,code_client=form.cleaned_data["numero_client"])
                compteur = get_object_or_404(Machine,pk=form.cleaned_data["numero_compteur"])
                if Abonnement.objects.filter(compteur=compteur).exists():
                    messages.add_message(request, messages.WARNING, "Ce compteur est déja enregistré pour un autre client")
                    return retour_abonnement(request,param1,param2,form)
                try:
                    abonnement = Abonnement.objects.create(
                        client=client, compteur=compteur, adresse=form.cleaned_data["adresse"],
                        point_service=form.cleaned_data["pointservice"], lat_machine=form.cleaned_data["latitude"],
                        lon_machine=form.cleaned_data["longitude"]
                    )
                    abonnement.generer_num_abonnement()
                    abonnement.save()
                except Exception as e:
                    print(e)
                    messages.add_message(request, messages.ERROR,'Un problème est survenu lors de la création de l\'abonnement !')
                    return retour_abonnement(request,param1,param2,form)
                etat = EtatCompteur.objects.get(compteur=compteur)
                etat.etat_abonnement = "lie"
                etat.save()
                compteur.client = client
                compteur.save()
                return redirect(reverse("elec_meter:donnees_compteur",kwargs={"num_compteur":form.cleaned_data["numero_compteur"]}))
        else:
            print(form.errors)
    return render(request,"elec_meter/creer_abonnement.html",{"form":form,"param":param1})

#@login_required(login_url='/connexion')
def code_client_autocomplete(request):
    if "term" in request.GET:
        qs = Client.objects.filter(code_client__startswith=request.GET.get('term'))
        codes = list()
        for client in qs:
            codes.append(client.code_client)
        return JsonResponse(codes,safe=False)

#@login_required(login_url='/connexion')
def deveui_autocomplete(request):
    if "term" in request.GET:
        qs = Machine.objects.filter(abonnement=None,devEUI__startswith=request.GET.get('term'))
        deveuis = list()
        for compteur in qs:
            deveuis.append(compteur.devEUI)
        return JsonResponse(deveuis, safe=False)

#@login_required(login_url='/connexion')
def editer_profile(request,id_agent):
    form = EditPwdAgentForm()
    villes = Ville.objects.all()
    agent = Agent.objects.get(id=id_agent)
    if agent.ville_agent is not None:
        ville_est_null = False
    else:
        ville_est_null = True
    context = {"agent":agent,"villes":villes,"ville_est_null":ville_est_null,"profiles":PROFILES,"form":form}
    return render(request, "elec_meter/editer_profile.html",context)

def creation_abonnement(request):
    if is_ajax(request=request) and request.method == "POST":
        reponse = {}
        print(request.POST["compteur"])
        print(request.POST["num_client"])
        if request.POST["num_client"] == "" or request.POST["compteur"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner tous les champs."
        elif not Machine.objects.filter(devEUI=request.POST["compteur"]):
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner un numéro de compteur existant."
        elif Abonnement.objects.filter(compteur=get_object_or_404(Machine,pk=request.POST["compteur"])):
            reponse["statut"] = "echec"
            reponse["message"] = "Ce compteur est déja associé à un client."
        else:
            compteur = get_object_or_404(Machine,pk=request.POST["compteur"])
            client = get_object_or_404(Client,code_client=request.POST["num_client"])
            Abonnement.objects.create(
                compteur=compteur,
                client=client
            )
            compteur.client = client
            compteur.save()
            reponse["statut"] = "succès"
            reponse["message"] = "Abonnement crée avec succès"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Non authorisé")


#@login_required(login_url='/connexion')
def edition_mot_de_passe(request):
    if is_ajax(request=request) and request.method=="POST":
        reponse = {}
        form = EditPwdAgentForm(request.POST)
        if form.is_valid():
            ancien_mot_de_passe = form.cleaned_data["ancien_mot_de_passe"]
            nouveau_mot_de_passe = form.cleaned_data["nouveau_mot_de_passe"]
            confirm_mot_de_passe = form.cleaned_data["confirm_mot_de_passe"]
            user = authenticate(request, email=request.user.email, password=ancien_mot_de_passe)
            if user is None:
                reponse["statut"],reponse["message"] = "echec","Les mots de passe renseignés sont differents"
            elif nouveau_mot_de_passe != confirm_mot_de_passe:
                reponse["statut"], reponse["message"] = "echec", "Les mots de passe renseignés sont differents"
            else:
                user.set_password(nouveau_mot_de_passe)
                reponse["statut"], reponse["message"] = "succes", "Vous avez un nouveau mot de passe"
            reponse = json.dumps(reponse)
            mimetype = "application/json"
            return HttpResponse(reponse, mimetype)
        else:
            return HttpResponse("Erreur !")
    else:
        return HttpResponse("Non authorisé")

#@login_required(login_url='/connexion')
def page_not_found_view(request, exception):
    return render(request, 'elec_meter/404.html', status=404)


#@login_required(login_url='/connexion')
def supprimer_province(request):
    if is_ajax(request=request) and request.method == "POST":
        reponse = {}
        prov = Province.objects.get(id=request.POST["id_prov"])
        prov.delete()
        reponse["statut"] = "succes"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Erreur ajax")


#@login_required(login_url='/connexion')
def donnees_compteur(request, num_compteur):
    payload_test = "1201"
    history_data = set_data(fport=8, payload=payload_test, machine=num_compteur)
    r = requests.post(url, headers=headers, data=history_data)
    data = {"devEUI":num_compteur,"confirmed":False,"fPort":8,"data":"EgE="}
    nb_data = Historique.objects.filter(date_creation__contains=date.today()).count()
    if nb_data == 0:
        requests.post(url, headers=headers, data=json.dumps(data))
    periodes = [{"labelle": "10 minutes", "valeur": 10}, {"labelle": "30 minutes", "valeur": 30},
                {"labelle": "1 heure", "valeur": 60}]
    compteur = get_object_or_404(Machine,pk=num_compteur)
    donnees = Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=compteur,infos_signal__jour=datetime.today()).order_by("-id").first()
    context = {
        "donnees":donnees,
        "periodes":periodes,
        "compteur":compteur,
    }
    if donnees is not None:
        context["date_creation"] = donnees.date_creation
    return render(request, "elec_meter/donnees_compteur.html", context)

#@login_required(login_url='/connexion')
def modifier_infos_client(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["nom_client"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner le nom du client"
        elif request.POST["prenom_client"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner le prénom du client"
        elif request.POST["tel_client"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Le numéro de téléphone est obligatoire"
        else:
            machine = get_object_or_404(Machine, pk=request.POST["num_machine"])
            client = machine.client
            client.nom_client = request.POST["nom_client"]
            client.prenom_client = request.POST["prenom_client"]
            client.tel_client = request.POST["tel_client"]
            client.email = request.POST["email_client"]
            try:
                client.save()
                reponse["statut"] = "succes"
                reponse["message"] = "Client modifié !"
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Echec de la modification"
            reponse = json.dumps(reponse)
            mimetype = "application/json"
            return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def modifier_nom_compteur(request):
    if is_ajax(request=request) and request.method=="POST":
        reponse = {}
        try:
            machine = get_object_or_404(Machine, pk=request.POST["num_machine"])
            machine.devName = request.POST["devName"]
            if request.POST["optionFournisseur"] == "1":
                machine.est_fournisseur = True
            else:
                machine.est_fournisseur = False
            machine.save()
            reponse["statut"] = "succes"
            reponse["message"] = "Le nom du compteur a été modifié !"
        except Exception as e:
            print(e)
            reponse["statut"] = "echec"
            reponse["message"] = "Echec de la modification !"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée !")

#@login_required(login_url='/connexion')
def creer_contrat(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["numerocontrat"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner le numéro du contrat"
        elif Contrat.objects.filter(numero_contrat=request.POST["numerocontrat"]).exists():
            reponse["statut"] = "echec"
            reponse["message"] = "Un contrat avec ce numéro existe déja."
        elif request.POST["puissance"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Le champ 'credits' ne peut pas etre vide. Vueillez le renseigner"
        else:
            Contrat.objects.create(
                numero_contrat=request.POST["numerocontrat"],
                type_compteur=request.POST["type_compteur"],
                puissance=float(request.POST["puissance"])
            )
            reponse["statut"] = "succes"
            reponse["message"] = "Contrat enregistré avec succès."
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")

# fonctions relative aux recharges

#@login_required(login_url='/connexion')
def recharger_credit_seeg(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["montant_recharge"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir un montant !"
        elif not float(request.POST["montant_recharge"]):
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir un montant valide !"
        elif float(request.POST["montant_recharge"]) == 0.00 or float(request.POST["montant_recharge"]) < 0 or float(
                request.POST["montant_recharge"]) < 10000:
            reponse["statut"] = "echec"
            reponse["message"] = "Le montant de la recharge doit etre au moins superieur à 10000 !"
        else:
            if CreditSEEG.objects.last():
                derniere_recharge = CreditSEEG.objects.last()
                credit_total = derniere_recharge.credit_total + float(request.POST["montant_recharge"])
            else:
                credit_total = request.POST["montant_recharge"]
            try:
                CreditSEEG.objects.create(credit_total=credit_total, montant_recharge=request.POST["montant_recharge"])
                reponse["statut"] = "succes"
                reponse["message"] = "Recharge éffectuée avec succès"
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Il y a eu un probleme lors de la recharge"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")

#@login_required(login_url='/connexion')
def recharger_compteur(request):
    reponse ={}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["compteur"] == "" or not Machine.objects.filter(devEUI=request.POST["compteur"]):
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir un numero de compteur valide"
        elif request.POST["montant_recharge"] == "" or float(request.POST["montant_recharge"]) < 1000:
            reponse["statut"] = "echec"
            reponse["message"] = "Vous ne pouvez recharger un montant inferieur à 1000"
        else:
            compteur = get_object_or_404(Machine,pk=request.POST["compteur"])
            solde_compteur = Historique.objects.filter(date_creation__contains=date.today(), machine=compteur).values("unites").first()["unites"]
            contrat = compteur.contrat
            coeff = contrat.coeff
            try:
                charge = CreditCompteur(compteur=compteur,montant_recharge=request.POST["montant_recharge"],)
                charge.generer_code_recharge()
                charge.save()
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Il y a eu un probleme lors de la recharge"
            montant_recharge = float(request.POST["montant_recharge"])
            payload = payload_recharge(int(round(montant_recharge)))
            payload = payload.replace("\n", "").strip()
            data = {
                "devEUI": compteur.devEUI,
                "confirmed": False,
                "fPort": 8,
                "data": payload
            }
            data = json.dumps(data)
            try:
                req = requests.post(url, headers=headers, data=data)
                charge.code_utilise = True
                charge.save()
                reponse["statut"] = "succes"
                reponse["message"] = "Recharge éffectuée avec succès"
                RechargeEtTransfert.objects.create(
                    compteur=get_object_or_404(Machine,pk=request.POST["compteur"]),montant=request.POST["montant_recharge"],
                    type_transaction="recharge",recharge=charge,benef=get_object_or_404(Machine,pk=request.POST["compteur"])
                )
                print(RechargeEtTransfert.objects.all())
                payload = set_data(fport=8, payload="1201", machine=request.POST["compteur"])
                donnees_uplink = Historique.objects.filter(date_creation__contains=date.today(),infos_signal__machine=compteur).first()
                donnees_uplink.unites = solde_compteur + float(montant_recharge) * coeff
                donnees_uplink.save()
                requests.post(url,headers=headers,data=payload)
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Un problème est survenu lors de la recharge."
        reponse = json.dumps(reponse)
        mimetype = 'application/json'
        return HttpResponse(reponse, mimetype)
    return HttpResponse("Requete non authorisée !")


#@login_required(login_url='/connexion')
def acheter_credit_compteur(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["devEUI"] == "" or not Machine.objects.filter(devEUI=request.POST["devEUI"]).exists():
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez saisir un numero de compteur valide"
        elif request.POST["montant_recharge"] == "" or float(request.POST["montant_recharge"]) == 0.00 or float(
                request.POST["montant_recharge"]) < 1000:
            reponse["statut"] = "echec"
            reponse["message"] = "Vous ne pouvez recharger un montant inferieur à 1000"
        else:
            total_credit = float(request.POST["montant_recharge"])
            try:
                charge = CreditCompteur(
                    compteur=get_object_or_404(Machine, pk=request.POST["devEUI"]),
                    montant_recharge=request.POST["montant_recharge"],
                )
                charge.generer_code_recharge()
                charge.save()
                reponse["statut"] = "succes"
                reponse["message"] = "Achat des unités effecutée avec succès"
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Il y a eu un probleme lors de la recharge"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")

#@login_required(login_url='/connexion')
def editer_client(request,id_client):
    client = get_object_or_404(Client, pk=id_client)
    ville_client = client.ville_client
    villes = Ville.objects.all()
    form = ClientForm({
        "nom_client":client.nom_client,"prenom_client":client.prenom_client,
        "adr_client":client.adresse_client,"tel_client":client.tel_client,"email_client":client.email
    })
    if request.method == "POST":
        if form.is_valid():
            client.nom_client = form.cleaned_data["nom_client"]
            client.prenom_client = form.cleaned_data["prenom_client"]
            client.ville_client = get_object_or_404(Ville,pk=request.POST["ville_client"])
            client.adresse_client = form.cleaned_data["adr_client"]
            client.tel_client = form.cleaned_data["tel_client"]
            client.email = form.cleaned_data["email_client"]
            client.save()
            return redirect(reverse("elec_meter:liste_clients"))
    return render(request,"elec_meter/editer_client.html",{"form":form,"villes":villes,"ville_client":ville_client,"client":client})


#@login_required(login_url='/connexion')
def historique_compteur(request, num_compteur):
    machine = get_object_or_404(Machine, pk=num_compteur)
    donnees = Historique.objects.filter(infos_signal__machine=machine).order_by("-infos_signal__date_creation")
    jj = datetime.today()
    context = {"donnees": donnees, "machine": machine,"jj":jj}
    return render(request, "elec_meter/historique.html", context)

#@login_required(login_url='/connexion')
def afficher_donnees_historique(request):
    if is_ajax(request=request) and request.method == "POST":
        machine = Machine.objects.get(devEUI=request.POST["num_machine"])
        donnees = Reporting.objects.filter(infos_signal__machine=machine,infos_signal__jour=request.POST["inputd_date"]). \
            order_by("-infos_signal__date_creation")
        pass


#@login_required(login_url='/connexion')
def donnees_infos(request):
    if is_ajax(request=request):
        nb_machines = Machine.objects.count()
        nb_gateways = GWS.objects.count()
        donnees = {"nb_machines": nb_machines, "nb_gateways": nb_gateways}
        donnees = json.dumps(donnees)
        mimetype = "application/json"
        return HttpResponse(donnees, mimetype)
    else:
        return HttpResponse("Ce lien que vous tenter de joindre n'existe pas")


#@login_required(login_url='/connexion')
def crediter_compteur(request):
    if is_ajax(request=request) and request.method == "POST":
        reponse = {}
        if request.POST["devEUI"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez renseigner le numero du compteur"
        elif request.POST["code_recharge"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Entrez le code de recharge svp !"
        else:
            type(request.POST["code_recharge"])
            if not CreditCompteur.objects.filter(compteur=request.POST["devEUI"],
                                                 code_recharge=request.POST["code_recharge"]).exists():
                reponse["statut"] = "echec"
                reponse["message"] = "Numero de compteur ou code de recharge incorrect"
            else:
                credit = CreditCompteur.objects.get(compteur=request.POST["devEUI"],
                                                    code_recharge=request.POST["code_recharge"])
                montant = credit.montant_recharge
                # Ici on convertira le montant en hexadecimal
                payload = "HDB1AAAB"
                data = {
                    "devEUI": request.POST["devEUI"],
                    "confirmed": False,
                    "fPort": 8,
                    "data": payload

                }
                data = json.dumps(data)
                try:
                    req = requests.post(url, headers=headers, data=data)
                    rep = req.json()
                    reponse["statut"] = "succes"
                    reponse["reponse"] = "Recherge de credit effectuée avec succès"
                    credit.code_utilise = True
                except Exception as e:
                    print(e)
                    reponse["statut"] = "echec"
                    reponse["reponse"] = "Il y a eu un problème lors de la recharge"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non autorisée")


#@login_required(login_url='/connexion')
def stats_donnees_compteur(request, devEUI):
    machine = get_object_or_404(Machine, pk=devEUI)
    donnees = Reporting.objects.values("infos_signal__date_creation__date").filter(infos_signal__machine=machine).annotate(avg_t=Avg("voltage"))
    return render(request, "elec_meter/stats_donnees_compteur.html")

#@login_required(login_url='/connexion')
def graphes_compteur(request):
    return render(request, "elec_meter/graphe_compteur.html")

##@login_required(login_url='/connexion')
def gestion_droits(request):
    agents = Agent.objects.all()
    profiles = ["Administrateur","Opérateur"]
    return render(request,"elec_meter/gestion_droits.html",{"agents":agents,"profiles":profiles})

def modifier_profile_agent(request):
    if is_ajax(request=request) and request.method == "POST":
        agent = get_object_or_404(Agent,pk=request.POST["user"])
        agent.profile = request.POST["profile"]
        agent.save()
        return JsonResponse({"statut":"succès","msg":"Profile modifé"})
    else:
        return JsonResponse({"statut": "echec", "msg": "Echec de la modification du profile"})


##@login_required(login_url='/connexion')
def changer_etat_activite(request):
    if is_ajax(request=request) and request.method == "POST":
        element = request.POST["element"]
        dict_elmnt = element.split("-")
        id_agent = int(dict_elmnt[1])
        agent = get_object_or_404(Agent,pk=id_agent)
        user = agent.user
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse({"statut":"succès"})
    else:
        return HttpResponse("Erreur ajax !")

"""
    Ce qui suit concerne exclusivement les vues du coté client.
"""

def client_home(request):
    if "context" in request.session:
        context = request.session["context"]
        machine = get_object_or_404(Machine, pk=context["devEUI"])
        context["donnees"] = Reporting.objects.filter(infos_signal__machine=machine).last()
        r = Reporting.objects.filter(infos_signal__machine=machine).last()
        return render(request, "elec_meter/client/home.html", context)
    else:
        return redirect(reverse("elec_meter:client_login"))


def client_deconnexion(request):
    connexion = get_object_or_404(Connexion, pk=request.session["context"]["id_connexion"])
    connexion.date_deconnexion = datetime.datetime.now()
    connexion.save()
    del request.session["context"]
    return redirect(reverse("elec_meter:client_login"))


def client_stat_par_mois(request, devEUI):
    machine = get_object_or_404(Machine, pk=devEUI)
    voltage_data = {}
    energ_data = {}
    if "context" in request.session:
        dict_mois = {
            "Janvier": 0, "Fevrier": 0, "Mars": 0, "Avril": 0, "Mai": 0, "Juin": 0,
            "Juillet": 0, "Aout": 0, "Septembre": 0, "Octobre": 0, "Novembre": 0, "Decembre": 0
        }
        dict1 = dict_mois.copy()
        dict2 = dict_mois.copy()
        if is_ajax(request=request) and request.method == "GET":
            donnees = Reporting.objects.values("infos_signal__mois").filter(infos_signal__machine=machine). \
                annotate(voltage=Avg("voltage"), energ=Avg("total_positive_active_energy"))
            for i in range(len(donnees)):
                voltage_data[donnees[i]["infos_signal__mois"]] = donnees[i]["voltage"]
                energ_data[donnees[i]["infos_signal__mois"]] = donnees[i]["energ"]
            for key, value in dict1.items():
                if key in voltage_data:
                    dict1[key] = voltage_data[key]
            for key, value in dict2.items():
                if key in energ_data:
                    dict2[key] = energ_data[key]
            reponse = {
                "labels1": list(dict1.keys()),
                "data1": list(dict1.values()),
                "labels2": list(dict2.keys()),
                "data2": list(dict2.values())
            }
            reponse = json.dumps(reponse)
            mimetype = "application/json"
            return HttpResponse(reponse, mimetype)
        else:
            return render(request, "elec_meter/client/stat_par_mois.html")
    else:
        return redirect(reverse("elec_meter:client_login"))


def client_login(request):
    form = ClientLoginForm()
    if request.method == "POST":
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            numero_compteur = form.cleaned_data["numero_compteur"]
            code_compteur = form.cleaned_data["code_compteur"]
            if not Machine.objects.filter(devEUI=numero_compteur,code_secret=code_compteur).exists():
                messages.add_message(request,messages.ERROR,"Numéro de compteur ou code incorrect.")
                return render(request,"elec_meter/client/login.html",{"form":form})
            else:
                machine = get_object_or_404(Machine,pk=numero_compteur)
                client = machine.client
                context = {
                    "nom_client": machine.client.nom_client,
                    "prenom_client": machine.client.prenom_client,
                    "code_secret": machine.code_secret,
                    "devEUI": machine.devEUI
                }
                connexion = Connexion.objects.create(client=client, date_connexion=datetime.now())
                context["id_connexion"] = connexion.id
                request.session["context"] = context
                return redirect(reverse("elec_meter:client_home"))
    return render(request,"elec_meter/client/login.html",{"form":form})

def details_ville(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    context = {"nb_machines": Machine.objects.filter(ville_machine=ville).count(),
               "nb_gateways": GWS.objects.filter(ville_gw=ville).count(),
               "machines": Machine.objects.filter(ville_machine=ville),
               "ville": ville
               }
    return render(request, "elec_meter/details_ville.html", context)

def details_province(request, pk):
    province = get_object_or_404(Province, pk=pk)
    context = {
        "nb_machines": Machine.objects.filter(ville_machine__province=province).count(),
        "nb_gateways": GWS.objects.filter(ville_gw__province=province).count(),
        "machines": Machine.objects.filter(ville_machine__province=province),
        "province": province
    }
    return render(request, "elec_meter/details_province.html", context)

def modifier_periode_push(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        if request.POST["periode"] == "":
            reponse["statut"] = "echec"
            reponse["message"] = "Veuillez choisir une option"
        else:
            if request.POST["periode"] == "10":
                payload = "BAoAAQ=="
            elif request.POST["periode"] == "30":
                payload = "BB4AAQ=="
            else:
                payload = "BDwAAQ=="
            data = {
                "devEUI": request.POST["devEUI"],
                "confirmed": False,
                "fPort": int(request.POST["fPort"]),
                "data": payload
            }
            data = json.dumps(data)
            try:
                req = requests.post(url, headers=headers, data=data)
                reponse["statut"] = "succes"
                reponse["message"] = "Période de push modifiée avec succès"
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Quelque chose n'a pas bien fonctionner"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")


def modifier_etat_valve(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        machine = get_object_or_404(Machine, pk=request.POST["devEUI"])
        if request.POST["action"] == "allumer":
            payload = "A1UB"
            data = {
                "devEUI": request.POST["devEUI"],
                "confirmed": False,
                "fPort": 8,
                "data": payload
            }
            data = json.dumps(data)
            try:
                req = requests.post(url, headers=headers, data=data)
                reponse["statut"] = "succes"
                reponse["message"] = "Compteur remis en service"
                etat = machine.etat
                etat.etat_valve = "on"
                etat.save()
            except Exception as e:
                print(e)
                reponse["statut"] = "echec"
                reponse["message"] = "Quelque chose n'a pas bien fonctionné"
            history_data = set_data(fport=8, payload="1201", machine=request.POST["devEUI"])
            requests.post(url, headers=headers, data=history_data)
        elif request.POST["action"] == "eteindre":
            payload = "A5kB"
            data = {
                "devEUI": request.POST["devEUI"],
                "confirmed": False,
                "fPort": 8,
                "data": payload
            }
            data = json.dumps(data)
            try:
                req = requests.post(url, headers=headers, data=data)
                reponse["statut"] = "succes"
                reponse["message"] = "Compteur mis hors service"
                etat = machine.etat
                etat.etat_valve = "off"
                etat.save()
            except Exception as e:
                reponse["statut"] = "echec"
                reponse["message"] = "Quelque chose n'a pas bien fonctionné"
            history_data = set_data(fport=8, payload="1201", machine=request.POST["devEUI"])
            requests.post(url, headers=headers, data=history_data)
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")

##@login_required(login_url='/connexion')
def telecharger_fichier_compteur(request):
    reponse = {}
    if is_ajax(request=request) and request.method == "POST":
        extensions = ["xls","xlsx"]
        form = UploadExcelMeterFile(request.POST,request.FILES)
        if form.is_valid():
            fichier_excel = request.FILES["fichier_excel"]
            extension = request.FILES["fichier_excel"].name.split(".")[-1]
            if not extension in extensions:
                reponse["statut"] = "echec"
                reponse["message"] = "Type de fichier invalide"
            else:
                wb = openpyxl.load_workbook(fichier_excel)
                worksheet = wb.active
                excel_data = list()
                for row in worksheet.iter_rows():
                    row_data = list()
                    for cell in row:
                        row_data.append(str(cell.value))
                    excel_data.append(row_data)
                for i in range(1,len(excel_data)):
                    if Machine.objects.filter(devEUI=excel_data[i][1]).exists:
                        continue
                    else:
                        try:
                            machine = Machine.objects.create(
                                devName= excel_data[i][0],devEUI=excel_data[i][1],type_machine=excel_data[i][2],
                                ville_machine=Ville.objects.get(nom_ville=excel_data[i][3]),adr_machine=excel_data[i][4],
                                lat_machine=excel_data[i][5],lon_machine=excel_data[i][6],
                            )
                            EtatCompteur.objects.create(compteur=machine)
                            reponse["statut"] = "succes"
                            reponse["message"] = "{0} Nouveaux compteurs enregistrés dans la base".format(len(excel_data)-1)
                        except Exception as e:
                            print(e)
                            print("Un problème est survenu lors de l'enregistrement du compteur {0}".format(excel_data[i][1],))
                            reponse["statut"] = "erreur"
                            reponse["message"] = "Erreur survenu lors de l'enregistrement des compteurs"
            reponse = json.dumps(reponse)
            mimetype = "application/json"
            return HttpResponse(reponse, mimetype)
        else:
            return HttpResponse("Erreur")
    else:
        return HttpResponse("Requete non authorisée")

##@login_required(login_url='/connexion')
def liste_compteurs_libres(request):
    context = {"compteurs":Machine.objects.filter(abonnement=None)}
    return render(request,"elec_meter/compteurs_libres.html",context)

##@login_required(login_url='/connexion')
def precharger_contrats(request):
    if is_ajax(request=request) and request.method == "POST":
        liste_contrats = []
        if Contrat.objects.filter(type_compteur=request.POST["typeSelected"]):
            for t in Contrat.objects.filter(type_compteur=request.POST["typeSelected"]):
                contrat = {"id":t.id,"numero":t.numero_contrat}
                liste_contrats.append(contrat)
        contrats = json.dumps(liste_contrats)
        mimetype = 'application/json'
        return HttpResponse(contrats, mimetype)

def voir_carte_compteur(request):
    return render(request,"elec_meter/carte_compteurs.html")

def voir_carte_getways(request):
    return render(request,"elec_meter/carte_getways.html")

def charger_carte(request):
    if is_ajax(request=request) and request.method == "GET":
        points = []
        for c in Machine.objects.all():
            etat = EtatCompteur.objects.get(compteur=c)
            if etat.etat_valve == "on":
                etat_valve = "Allumé"
            elif etat.etat_valve:
                etat_valve = "Eteint"
            else:
                etat_valve = "Déconnecté"
            point = {"lat":c.abonnement.lat_machine,"lng":c.abonnement.lon_machine,
                     "adr":c.abonnement.adresse,"poitservice":c.abonnement.point_service,
                     "etat_valve":etat_valve}
            points.append(point)
        points = json.dumps(points)
        mimetype = "application/json"
        return HttpResponse(points,mimetype)
    else:
        return HttpResponse("Requete non authorisée")

def charger_carte_getways(request):
    if is_ajax(request=request) and request.method == "GET":
        points = []
        for getway in GWS.objects.all():
            point = {"lat":getway.lat_gw,"lng":getway.lon_gw,
                     "adr":getway.adr_gw}
            points.append(point)
        points = json.dumps(points)
        mimetype = "application/json"
        return HttpResponse(points,mimetype)
    else:
        return HttpResponse("Requete non authorisée")

def contrats(request):
    return render(request,"elec_meter/contrats.html",{"contrats":Contrat.objects.all()})

#@login_required(login_url='/connexion')
def supprimer_contrat(request):
    if is_ajax(request=request) and request.method == "POST":
        reponse = {}
        contrat = Contrat.objects.get(id=request.POST["id_contrat"])
        contrat.delete()
        reponse["statut"] = "succes"
        reponse = json.dumps(reponse)
        mimetype = "application/json"
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Erreur ajax")

def details_contrat(request):
    if is_ajax(request=request) and request.method == "POST":
        instance = get_object_or_404(Contrat,pk=request.POST["contrat"])
        contrat = model_to_dict(instance)
        contrat = json.dumps(contrat)
        mimetype = "application/json"
        return HttpResponse(contrat, mimetype)
    else:
        return HttpResponse("Erreur ajax")

def emprunts(request,deveui):
    compteur = get_object_or_404(Machine,pk=deveui)
    contrat = compteur.contrat
    nb = Emprunt.objects.filter(c_emprunteur=compteur).count()
    dettes = Emprunt.objects.filter(c_emprunteur=compteur).order_by('-date_emprunt')
    return render(request,"elec_meter/emprunts.html",{"dettes":dettes,"compteur":compteur,"nb":nb,"coeff":contrat.coeff})

def compteur_libre(request):
    return render(request,"elec_meter/compteur_libre.html")

def refresh_data(request):
    if is_ajax(request=request) and request.method == "POST":
        compteur = get_object_or_404(Machine,pk=request.POST["deveui"])
        donnees = Historique.objects.filter(date_creation__contains=date.today(), infos_signal__machine=compteur,\
                                  infos_signal__jour=datetime.today()).order_by("-id").values().first()
        print(donnees)
        date_creation = donnees["date_creation"]
        date_creation = date_creation.strftime("%d/%m/%Y, %H:%M:%S")
        del donnees["date_creation"]
        donnees["date_creation"] = date_creation
        donnees = json.dumps(donnees)
        mimetype = "application/json"
        return HttpResponse(donnees,mimetype)
    else:
        return HttpResponse("Requete non authorisée")

def localisation_compteur(request,deveui,getway):
    context = {
        "compteur":get_object_or_404(Machine,pk=deveui),
        "getway":GWS.objects.get(gw_id=getway)
    }
    return render(request,"elec_meter/localisation_compteur.html",context)

def modifier_localisation_compteur(request):
    if is_ajax(request=request) and request.method == "POST":
        form = EditerLocalCompteur(request.POST)
        reponse = {}
        if request.POST["deveui"] == "":
            reponse["statut"] = "echec"
            reponse["msg"] = "Numéro de compteur vide"
        elif not form.is_valid():
            if form.errors:
                print(request.POST["deveui"])
            reponse["statut"] = "echec"
            reponse["msg"] = "Un ou plusiseurs champs du formulaire manquent ou sont invalides"
        else:
            print(request.POST["latitude"])
            print(request.POST["longitude"])
            compteur = get_object_or_404(Machine,pk=request.POST["deveui"])
            a = Abonnement.objects.get(compteur=compteur)
            a.point_service = form.cleaned_data["pointservice"]
            a.lat_machine = form.cleaned_data["latitude"]
            a.lon_machine = form.cleaned_data["longitude"]
            a.save()
            print(a.lat_machine)
            reponse["statut"] = "succes"
            reponse["msg"] = "Coordonnées du compteur modifiées"
        reponse = json.dumps(reponse)
        mimetype = 'application/json'
        return HttpResponse(reponse, mimetype)
    else:
        return HttpResponse("Requete non authorisée")

def notifications(request):
    nb_c_arretes = EtatCompteur.objects.filter(etat_valve="off").count()
    return render(request,"elec_meter/notifications.html",{"nb_c_arretes":nb_c_arretes})

def compteur_arretes_par_villes(request):
    context = {"compteurs_en_arret":EtatCompteur.objects.values("compteur__ville_machine").filter(etat_valve="off").annotate(compteurs=Count("compteur"))}
    print(context["compteurs_en_arret"].query)
    print(context["compteurs_en_arret"])
    return render(request,"elec_meter/compteurs_arretes_par_villes.html",context)

def details_gateway(request):
    return render(request,"elec_meter/details_gateway.html")










