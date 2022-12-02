from django import forms
from django.core.exceptions import ValidationError
from validate_email import validate_email
from .models import *

error_messages = {"required":"Veuillez renseigner ce champ","invalid":"Valeur de champ invalide"}
error_edit_pwd = {"required":"Veuillez renseigner ce champ","invalid":"Les mots de passe ne correspondent pas"}

class ClientForm(forms.Form):
    nom_client = forms.CharField(max_length=70,error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control","placeholder": "Nom du client"}))
    prenom_client = forms.CharField(max_length=70, error_messages=error_messages, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom du client"}))
    adr_client = forms.CharField(label="Adresse client",max_length=70, error_messages=error_messages, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse du client"}))
    tel_client = forms.CharField(label="Téléphone client",max_length=70, error_messages=error_messages, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Téléphone du client"}))
    email_client = forms.CharField(max_length=70,required=False, widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email du client"}))

    # def clean(self):
    #     cleaned_data = super().clean()
    #     nom_client = cleaned_data.get("nom_client")
    #     prenom_client = cleaned_data.get("prenom_client")
    #     tel_client = cleaned_data.get("tel_client")
    #     if Client.objects.filter(nom_client=nom_client,prenom_client=prenom_client,tel_client=tel_client).exists():
    #         raise ValidationError("Un client avec ce nom,prénom et numéro de téléphone existe déja !")

    def clean_tel_client(self):
        data = self.cleaned_data["tel_client"]
        if data[0:2] != "06" and data[0:2] != "07":
            raise ValidationError("Le numéro doit comencer par 06 ou 07")
        elif len(data) != 9:
            raise ValidationError("Numéro incorect !")
        else:
            if not data.isdecimal():
                raise ValidationError("Le numéro de téléphone ne doit contenir que des chiffres.")
        return data;

class MachineForm(forms.Form):
    devEUI = forms.CharField(label= "Numéro du compteur", max_length=70,error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control","placeholder": "devEUI"}))
    devName = forms.CharField(label= "Nom du compteur",required=False,max_length=70, error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "devName"}))
    def clean_devEUI(self):
        data = self.cleaned_data["devEUI"]
        if Machine.objects.filter(devEUI=self.cleaned_data["devEUI"]).exists():
            raise ValidationError("Un compteur avec ce numéro existe déja !")
        return data


class RegisterForm(forms.Form):
    nom_agent = forms.CharField(max_length=70,error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}, ))
    prenom_agent = forms.CharField(max_length=70,error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom"}))
    email = forms.EmailField(max_length=50,widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))

    def cleaned_email(self):
        data = self.cleaned_data["email"]
        if User.objects.filter(email=data).exists():
            raise ValidationError("Cet email est déja utilisé !")
        return data

class RechargeForm(forms.Form):
    compteur = forms.CharField(max_length=50,label="Numéro du compteur",error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control","placeholder":"Numéro du compteur"}))
    code = forms.CharField(max_length=50,label="Code de recharge",error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control","placeholder":"Numéro du compteur"}))


class LoginForm(forms.Form):
    matricule = forms.CharField(max_length=50, error_messages={"required": "Veuillez renseigner votre matricule"},widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Votre matricule"}))
    email = forms.EmailField(max_length=50, error_messages=error_messages,widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))
    password = forms.CharField(max_length=50, error_messages=error_messages,widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}))

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not validate_email(email):
            raise forms.ValidationError("Veuillez saisir une adresse email correcte !")
        return email

class UploadExcelMeterFile(forms.Form):
    fichier_excel = forms.FileField(label="Fichier excel",error_messages=error_messages,required=True,widget=forms.FileInput({"class": "form-control"}))

class EditPwdAgentForm(forms.Form):
    ancien_mot_de_passe = forms.CharField(label="Ancien mot de passe",max_length=50,error_messages=error_edit_pwd,widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Ancien mot de passe"}))
    nouveau_mot_de_passe = forms.CharField(label="Nouveau mot de passe",max_length=50,error_messages=error_edit_pwd,widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Nouveau mot de passe"}))
    confirm_mot_de_passe = forms.CharField(label="Confirmation",max_length=50,error_messages=error_edit_pwd,widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmation mot de passe"}))

class CreerAbonnementForm(forms.Form):
    numero_client = forms.CharField(max_length=50,error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Numéro du client"}))
    numero_compteur = forms.CharField(max_length=50,error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Numéro du compteur"}))
    adresse = forms.CharField(label="Adresse", max_length=200, error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse"}))
    pointservice = forms.CharField(label="Point de service", max_length=70, error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Point de service"}))
    latitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0,widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Latitude", "step": "0.000000001"}))
    longitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0,widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Longitude", "step": "0.000000001"}))


class EditerLocalCompteur(forms.Form):
    deveui = forms.CharField(label= "Numéro du compteur", max_length=70,error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control","placeholder": "devEUI"}))
    pointservice = forms.CharField(label="Point de service", max_length=70, error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Point de service"}))
    latitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Latitude", "step": "0.000000001"}))
    longitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Longitude", "step": "0.000000001"}))

class AddGateWayForm(forms.Form):
    num_gw = forms.CharField(max_length=50,label="Numéro gateway",error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Numéro de la gateway"}))
    nom_gw = forms.CharField(max_length=50,label="Nom gateway",error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom de la gateway"}))
    adr_gw = forms.CharField(max_length=50,label="Adresse gateway",error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse de la gateway"}))
    latitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0,widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Latitude", "step": "0.0"}))
    longitude = forms.FloatField(required=True, error_messages=error_messages, min_value=0,widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Longitude", "step": "0.01"}))
    desc_gw = forms.CharField(max_length=50,required=False,label="Description",widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Description","rows":4}))

    def clean_num_gw(self):
        data = self.cleaned_data["num_gw"]
        if GWS.objects.filter(gw_id=data).exists():
            raise ValidationError("Une gateway avec ce numéro est déja enregistrée !")
        return data

class TransfererCreditForm(forms.Form):
    erreur = False
    err_msg = ""
    expediteur = forms.CharField(required=True,max_length=50,label="Compteur à débiter",error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control", "placeholder": "Compteur à débiter"}))
    beneficiaire = forms.CharField(required=True,max_length=50,label="Compteur à créditer",error_messages=error_messages,widget=forms.TextInput(attrs={"class":"form-control", "placeholder": "Compteur à créditer"}))
    unites_a_transferer = forms.FloatField(required=True,label="Unités à transferer", error_messages=error_messages, min_value=10,widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Nombre d'unités à transférer"}))

    def clean(self):
        cleaned_data = super().clean()
        if not Machine.objects.filter(devEUI=cleaned_data["expediteur"]):
            raise ValidationError("Ce compteur n'existe pas ou n'est pas enregistré.")
        elif not Machine.objects.filter(devEUI=cleaned_data["beneficiaire"]):
            raise ValidationError("Ce compteur n'existe pas ou n'est pas enregistré.")
        else:
            if cleaned_data["expediteur"] == cleaned_data["beneficiaire"]:
                raise ValidationError("Opération impossible ! Vous ne pouvez pas envoyer des unités à vous-même.")

    def reitUnites(self):
        cleaned_data = super().clean()
        cleaned_data["unites_a_transferer"] = None



class ClientLoginForm(forms.Form):
    numero_compteur = forms.CharField(max_length=50,label="Numéro du compteur",error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Numéro du compteur"}))
    code_compteur = forms.CharField(max_length=50,label="Code du compteur",error_messages=error_messages,widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Code du compteur"}))

class AgentForm(forms.ModelForm):
    model = Agent
    fields = '__all__'


class AgentForm(forms.ModelForm):
    model = Agent
    fields = "__all__"

class VilleForm(forms.ModelForm):
    model = Ville
    fields = '__all__'

class ProvinceForm(forms.ModelForm):
    model = Province
    fields = '__all__'

class UserForm(forms.ModelForm):
    model = User
    fields = '__all__'

class AbonnementForm(forms.ModelForm):
    model = Abonnement
    fields = '__all__'



