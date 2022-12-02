from rest_framework import serializers
from elec_meter import models


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Agent
        fields = '__all__'


class AchatSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Achat
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = '__all__'

class InfoSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InfoSignal
        fields = '__all__'

class AbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Abonnement
        fields = '__all__'

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Province
        fields = '__all__'

class VilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Ville
        fields = '__all__'


class GWSSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GWS
        fields = '__all__'

class ReportingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Reporting
        fields = '__all__'

class MachineSerializer(serializers.ModelSerializer):
    #data = DataSerializer(many=True)
    ville_machine = serializers.StringRelatedField()

    class Meta:
        model = models.Machine
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    abonnements = AbonnementSerializer(many=True,read_only=True)

    class Meta:
        model = models.Client
        fields = '__all__'

class HistoriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Historique
        fields = '__all__'

class TransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transfert
        fields = '__all__'

class RechargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CreditCompteur
        fields = '__all__'

class TransacSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Transac
        fields = '__all__'

class CompteurAssocieSerialier(serializers.ModelSerializer):
    class Meta:
        model = models.CompteurAssocie
        fields = '__all__'

class ContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contrat
        fields = '__all__'

class RetraitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Retrait
        fields = '__all__'

class EmpruntSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Emprunt
        fields = '__all__'

