import random

from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Cast
from django.utils import timezone
from django.contrib.auth.models import (AbstractUser, BaseUserManager)
from datetime import datetime



class Application(models.Model):
    nom_app = models.CharField(max_length=50)


class Client(models.Model):
    photo_client = models.ImageField(blank=True, null=True)
    nom_client = models.CharField(max_length=70)
    prenom_client = models.CharField(max_length=70)
    tel_regex = RegexValidator(regex=r'^\+?1?\d{9}$', message="Le numéro renseigné n'est pas valide")
    tel_client = models.CharField(max_length=15,validators=[tel_regex])
    email = models.EmailField(max_length=50, null=True, blank=True)
    ville_client = models.ForeignKey("Ville",on_delete=models.SET_NULL,null=True,blank=True)
    etat_compte = models.BooleanField(default=False)
    est_bloque = models.BooleanField(default=True)
    adresse_client = models.CharField(max_length=200,blank=True,null=True)
    code_client = models.CharField(max_length=20,null=True,blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def generer_code_client(self):
        import string
        taille_code = 8
        caracts = string.ascii_uppercase + string.digits
        code_client = ''.join(random.choice(caracts) for _ in range(taille_code))
        if Client.objects.filter(code_client=code_client).exists():
            self.code_client = ''.join(random.choice(caracts) for _ in range(taille_code))
        else:
            try:
                self.code_client = code_client
            except Exception as e:
                print(e)

    class Meta:
        db_table = "CLIENT"

    def __str__(self):
        return self.nom_client

class Identifiants(models.Model):
    client = models.OneToOneField(Client,on_delete=models.CASCADE,related_name='identifiants')
    pdw = models.CharField(max_length=100,null=True,blank=True)
    code = models.CharField(max_length=6,null=True,blank=True)
    date_gen = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "IDENTIFIANTS"

    def save(self, *args, **kwargs):
        import random
        number = random.randint(1000,9999)
        self.code = str(number)
        super(Identifiants, self).save(*args, **kwargs)

class Connexion(models.Model):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    date_connexion = models.DateTimeField(null=True, blank=True)
    date_deconnexion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "CONNEXION"


class GWS(models.Model):
    gw_id = models.CharField(max_length=50, primary_key=True)
    nom_gateway = models.CharField(max_length=50,null=True,blank=True)
    ville_gw = models.ForeignKey('Ville', on_delete=models.SET_NULL, blank=True, null=True)
    adr_gw = models.CharField(max_length=200, blank=True, null=True)
    lat_gw = models.FloatField(default=0.0)
    lon_gw = models.FloatField(default=0.0)
    description = models.TextField(null=True, blank=True)
    date_creation = models.DateField(auto_now_add=True)
    derniere_modif = models.DateField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta:
        db_table = "GATEWAY"


class Machine(models.Model):
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True,related_name="compteurs")
    contrat = models.ForeignKey('Contrat', on_delete=models.SET_NULL,blank=True,null=True,related_name='meters')
    devName = models.CharField(max_length=50,null=True,blank=True)
    devEUI = models.CharField(max_length=50, primary_key=True)
    type_machine = models.CharField(max_length=30, default="Mono phasé")
    code_secret = models.CharField(max_length=10,null=True,blank=True)
    ville_machine = models.ForeignKey('Ville', on_delete=models.SET_NULL, blank=True, null=True,related_name="machines")
    date_creation = models.DateField(auto_now_add=True)
    derniere_modif = models.DateField(auto_now=True)
    actif = models.BooleanField(default=True)
    est_fournisseur = models.BooleanField(default=False)

    def test_abonnement(self):
        if self.objects.filter(abonnementscompteurs=None).count==0:
            return False
        return True
    class Meta:
        db_table = "MACHINE"

    def modifier_etat(self):
        if self.est_allume:
            self.est_allume = False
        else:
            self.est_allume = True
        self.save()

    def generer_code_machine(self):
        self.code_secret = str(random.randint(10000, 99999))
        if Machine.objects.filter(code_secret=self.code_secret).exists():
            self.code_secret = str(random.randint(10000, 99999))
        return self.code_secret

    def __str__(self):
        return self.devEUI

class EtatCompteur(models.Model):
    ETATS_COMPTEUR = [("nouveau", "nouveau"),("bon", "bon"),("mauvais", "mauvais"),("defectueux", "defectueux")]
    ETAT_VALVE = [("on", "on"),("off", "off"),("indefini", "indefini")]
    ETAT_ABONNEMENT = [("libre", "libre"),("lie", "lie")]
    compteur = models.OneToOneField(Machine,on_delete=models.CASCADE,related_name="etat")
    etat_physique = models.CharField(max_length=30,default="nouveau",choices=ETATS_COMPTEUR)
    etat_abonnement = models.CharField(max_length=30,default="libre",choices=ETAT_ABONNEMENT)
    etat_valve = models.CharField(max_length=20,default="indefini",choices=ETAT_VALVE)
    date_enregistre = models.DateField(auto_now_add=True,null=True,blank=True)

    class Meta:
        db_table = "ETATCOMPTEUR"

class InfoSignal(models.Model):
    jour = models.DateField()
    mois = models.CharField(max_length=12,null=True,blank=True)
    heure = models.TimeField()
    rssi = models.FloatField()
    snr = models.FloatField()
    freq = models.FloatField()
    dr = models.IntegerField()
    adr = models.BooleanField()
    classe = models.CharField(max_length=2, verbose_name="class")
    fCnt = models.IntegerField()
    fPort = models.IntegerField()
    confirmed = models.BooleanField()
    data = models.CharField(max_length=100)
    gwid = models.ForeignKey(GWS, on_delete=models.CASCADE, related_name="donnees")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="signaux")
    date_creation = models.DateTimeField(default=timezone.now)
    liste_gateways = models.CharField(max_length=200)

    def save(self,*args,**kwargs):
        super(InfoSignal,self).save(*args,**kwargs)


    def definir_mois(self):
        les_mois = [
            "Jan","Fev","Mar","Avr","Mai","Juin","Juil",
            "Aout","Sept","Oct","Nov","Dec"
            ]
        now = datetime.date.now()
        indice_mois = int(now.month)
        self.mois = les_mois[indice_mois]

    class Meta:
        db_table = "INFOSIGNAL"
        ordering = ("jour","heure",)


class Reporting(models.Model):
    infos_signal = models.ForeignKey(InfoSignal, on_delete=models.SET_NULL, null=True, blank=True,related_name="reporting_data")
    command_code = models.CharField(max_length=4, null=True, blank=True)
    total_positive_active_energy = models.FloatField(default=0.0)
    active_power_rate_tip = models.FloatField(default=0.0)
    active_power_rate_peak = models.FloatField(default=0.0)
    active_power_rate_flat = models.FloatField(default=0.0)
    active_power_rate_valley = models.FloatField(default=0.0)
    voltage = models.FloatField(default=0.0, blank=True, null=True)
    voltage_a = models.FloatField(default=0.0, blank=True, null=True)
    voltage_b = models.FloatField(default=0.0, blank=True, null=True)
    voltage_c = models.FloatField(default=0.0, blank=True, null=True)
    current = models.FloatField(default=0.0, blank=True, null=True)
    current_a = models.FloatField(default=0.0, blank=True, null=True)
    current_b = models.FloatField(default=0.0, blank=True, null=True)
    current_c = models.FloatField(default=0.0, blank=True, null=True)
    equipment_statut = models.CharField(max_length=4, null=True, blank=True)
    alarm_statut = models.CharField(max_length=4, null=True, blank=True)
    downlink_signal_strength = models.CharField(max_length=4, null=True, blank=True)
    downlink_signal_to_noise_ratio = models.FloatField(default=0.0, null=True, blank=True)
    downlink_snr = models.CharField(max_length=4, null=True, blank=True)
    frame_identification = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        db_table = "REPORTING"

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail donnée doit etre definie")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    tel_regex = RegexValidator(regex=r'^\+?1?\d{9}$',message="Le numéro renseigné n'est pas valide")
    email = models.EmailField('adresse email', unique=True)
    telephone = models.CharField(max_length=20,validators=[tel_regex])
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        db_table = "USER"


class Agent(models.Model):
    PROFILES = [
        ("administrateur", "Administrateur"),
        ("operateur", "operateur"),
        ("super_admin", "super_admin")
    ]
    photo_agent = models.ImageField(upload_to='agents', blank=True, null=True)
    nom_agent = models.CharField(max_length=70, blank=True, null=True)
    prenom_agent = models.CharField(max_length=70, blank=True, null=True)
    ville_agent = models.ForeignKey('Ville', on_delete=models.SET_NULL, blank=True, null=True)
    adr_agent = models.CharField(max_length=200, null=True, blank=True)
    profile = models.CharField(max_length=15, choices=PROFILES, blank=True, null=True)
    matricule = models.CharField(max_length=30, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="agent")

    class Meta:
        db_table = "AGENT"

    def generer_matricule(self):
        self.matricule = random.randint(1000000, 9999999)
        if Agent.objects.filter(matricule=self.matricule).exists():
            self.matricule = random.randint(1000000, 9999999)
        return self.matricule

class Province(models.Model):
    nom_province = models.CharField(max_length=50)
    code_province = models.CharField(max_length=10)

    class Meta:
        db_table = "PROVINCE"

    def __str__(self):
        return self.nom_province


class Ville(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    nom_ville = models.CharField(max_length=100)

    def operations(self):
        for compteur in Machine.objects.filter(ville_id=self.id):
            pass
    class Meta:
        db_table = "VILLE"

    def __str__(self):
        return self.nom_ville


class Abonnement(models.Model):
    num_abonnement = models.CharField(max_length=20,null=True)
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name="abonnements")
    compteur = models.OneToOneField(Machine, on_delete=models.CASCADE,related_name="abonnement")
    adresse = models.CharField(max_length=200, blank=True, null=True)
    point_service = models.CharField(max_length=200, null=True, blank=True)
    lat_machine = models.FloatField(default=0.0)
    lon_machine = models.FloatField(default=0.0)
    date_creation = models.DateField(default=timezone.now)
    derniere_modif = models.DateField(auto_now=True)

    class Meta:
        db_table = "ABONNEMENT"

    def __str__(self):
        return self.num_abonnement

    def generer_num_abonnement(self):
        import string
        taille_code = 5
        caracts = string.ascii_uppercase + string.digits
        num_abonnement = ''.join(random.choice(caracts) for _ in range(taille_code))
        if Abonnement.objects.filter(num_abonnement=num_abonnement).exists():
            num_abonnement = ''.join(random.choice(caracts) for _ in range(taille_code))
        else:
            self.num_abonnement = num_abonnement


class Transfert(models.Model):
    exp_transfert = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="exp_transferts")
    dest_transfert = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name="dest_transferts")
    montant_transfert = models.FloatField()
    date_transfert = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "TRANSFERT"


class CreditSEEG(models.Model):
    credit_total = models.FloatField(default=0.00)
    montant_recharge = models.FloatField(default=0.00)
    date_recharge = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "CREDITSEEG"


class CreditCompteur(models.Model):
    tuple_mois = ("Jan","Fev","Mar","Avr","Mai","Juin","Juil","Aout","Sept","Oct","Nov","Dec")
    compteur = models.ForeignKey(Machine, on_delete=models.CASCADE, default="8cf9572000023509",related_name="credits")
    montant_recharge = models.FloatField(default=0.00)
    code_recharge = models.CharField(max_length=30, default="jffgfyuee", unique=True)
    date_recharge = models.DateTimeField(auto_now_add=True)
    code_utilise = models.BooleanField(default=False)

    class Meta:
        db_table = "CREDITCOMPTEUR"

    def generer_code_recharge(self):
        self.code_recharge = str(random.randint(10000, 99999))
        if CreditCompteur.objects.filter(code_recharge=self.code_recharge).exists():
            self.code_recharge = str(random.randint(10000, 99999))
        return self.code_recharge

class Contrat(models.Model):
    numero_contrat = models.CharField(max_length=50)
    date_eq = models.DateField(auto_now_add=True)
    type_compteur = models.CharField(max_length=15)
    puissance = models.FloatField(default=10)
    unites = models.FloatField(default=1.00)
    valeur_en_cfa = models.IntegerField()
    coeff = models.FloatField()

    def save(self,*args,**kwargs):
        if self.puissance == 10:
            self.valeur_en_cfa = 1000
            self.unites = 10
        elif self.puissance == 20:
            self.valeur_en_cfa = 1000
            self.unites = 12
        elif self.puissance == 30:
            self.valeur_en_cfa = 1000
            self.unites = 15
        self.coeff = self.unites / self.valeur_en_cfa
        self.coeff = round(self.coeff, 4)
        super(Contrat,self).save(*args,**kwargs)

    class Meta:
        db_table = "CONTRAT"
        ordering = ("-date_eq",)

class Historique(models.Model):
    machine = models.ForeignKey(Machine,on_delete=models.SET_NULL,blank=True,null=True,related_name="historiques")
    infos_signal = models.ForeignKey(InfoSignal,on_delete=models.SET_NULL,blank=True,null=True)
    energie_active = models.FloatField()
    unites = models.FloatField(default=0.00)
    tension = models.FloatField(default=0.00)
    tension_a = models.FloatField(default=0.00)
    tension_b = models.FloatField(default=0.00)
    tension_c = models.FloatField(default=0.00)
    courant = models.FloatField(default=0.00)
    courant_a = models.FloatField(default=0.00)
    courant_b = models.FloatField(default=0.00)
    courant_c = models.FloatField(default=0.00)
    statut_equipement = models.CharField(max_length=15,blank=True,null=True)
    statut_alarme = models.CharField(max_length=15,blank=True,null=True)
    intensite_downlink = models.CharField(max_length=15,blank=True,null=True)
    snr = models.CharField(max_length=15,blank=True,null=True)
    frame_identification = models.CharField(max_length=15,blank=True,null=True)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "HISTORIQUE"
        ordering = ("-infos_signal__heure",)


class Transac(models.Model):
    jour = models.DateField()
    heure = models.TimeField()
    expediteur = models.ForeignKey(Machine,on_delete=models.SET_NULL,blank=True,null=True,related_name="transactions")
    beneficiaire = models.ForeignKey(Machine,on_delete=models.SET_NULL,null=True,blank=True)
    unites_expediteur = models.FloatField(default=0.00)
    montant = models.FloatField(default=0.00)
    equivalence_unites = models.FloatField(default=0.00)
    etat = models.CharField(max_length=10,default="")
    comment = models.CharField(max_length=50,null=True,blank=True)

    class Meta:
        db_table = "TRANSACTION"
        #ordering = ("-jour",)

class CompteurAssocie(models.Model):
    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    nom_compteur = models.CharField(max_length=100)
    num_compteur = models.CharField(max_length=100)

    class Meta:
        db_table = "COMPTEURASSOCIE"
        ordering = ("nom_compteur",)

class Emprunt(models.Model):
    c_emprunteur = models.ForeignKey(Machine,on_delete=models.SET_NULL,blank=True,null=True,related_name="emprunteur")
    c_preteur = models.ForeignKey(Machine,on_delete=models.SET_NULL,null=True,blank=True,related_name="preteur")
    montant = models.FloatField()
    montant_en_cfa = models.FloatField(default=0.00)
    avance = models.FloatField(default=0.00)
    reste = models.FloatField(default=0.00)
    dette_solde = models.BooleanField(default=False)
    etat = models.CharField(max_length=10,default="echec")
    date_emprunt = models.DateTimeField(auto_now_add=True)


class PorteMonaie(models.Model):
    compteur = models.ForeignKey(Machine,on_delete=models.DO_NOTHING)
    devise = models.FloatField()

class Retrait(models.Model):
    compteur_client = models.ForeignKey(Machine,on_delete=models.CASCADE)
    compteur_trader = models.ForeignKey(Machine,on_delete=models.CASCADE,default=1,related_name="trader")
    montant = models.FloatField(default=0.00)
    jour_retrait = models.DateField(default=timezone.now)
    heure_retrait = models.TimeField(default=datetime.now().strftime(("%H:%M:%S")))
    etat = models.CharField(max_length=10,null=True,blank=True)
    equivalent_montant_unites = models.FloatField(default=0.00)
    type_retrait = models.IntegerField() # si 1 retrait classique. si 2 achat.

    class Meta:
        db_table = "RETRAIT"
        ordering = ("-jour_retrait",)

class Notif(models.Model):
    type_notif = models.CharField(max_length=50)
    compteur = models.ForeignKey(Machine,on_delete=models.SET_NULL,null=True,blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "NOTIF"

class RechargeEtTransfert(models.Model):
    compteur = models.ForeignKey(Machine,on_delete=models.SET_NULL,null=True,blank=True)
    recharge = models.ForeignKey(CreditCompteur,on_delete=models.SET_NULL,blank=True,null=True)
    transfert = models.ForeignKey(Transac,on_delete=models.SET_NULL,null=True,blank=True)
    benef = models.ForeignKey(Machine,on_delete=models.SET_NULL,null=True,blank=True,related_name="beneficiare_transac")
    montant = models.FloatField(default=0.00)
    effectue_le = models.DateTimeField(auto_now_add=True)
    type_transaction = models.CharField(max_length=30,default="Inconnu")

    def save(self,*args, **kwargs):
        if self.compteur == self.benef:
            self.type_transaction = "recharge"
        else:
            self.type_transaction = "transfert"
        super(RechargeEtTransfert, self).save(*args, **kwargs)

    class Meta:
        db_table = "RECHARGEETTRANSFERT"

class Achat(models.Model):
    trader = models.ForeignKey(Machine,on_delete=models.DO_NOTHING,null=True,blank=True,related_name="vendeur")
    client = models.ForeignKey(Machine,on_delete=models.DO_NOTHING,null=True,blank=True,related_name="acheteur")
    montant = models.FloatField(default=0.00)
    date_achat = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ACHAT"















