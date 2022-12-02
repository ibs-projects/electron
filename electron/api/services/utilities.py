import base64
import codecs
import json
import requests

from elec_meter.models import Machine


def payload_to_base64(payload):
    payload_in_bytes = payload.encode("ascii")
    base64_bytes = base64.b64encode(payload_in_bytes)
    payload_in_base64 = base64_bytes.decode("ascii")
    return payload_in_base64


def inverser_bits(data):
    taille_data = len(data)
    return data[int(taille_data / 2):taille_data] + data[0:int(taille_data / 2)]

def set_data(fport="",payload="",machine=""):
    payload = conversion_hex_base64(payload)
    data = {
        "devEUI":machine,
        "confirmed":False,
        "fPort":fport,
        "data":payload
    }
    data = json.dumps(data)
    return data

# function which converts decimal value
# to hexadecimal value
def decimalToHexadecimal(decimal):
    decimal = int(decimal)
    # tableau correspondance decimal -hexa
    conversion_table = {
        0: '0', 1: '1', 2: '2', 3: '3', 4: '4',
        5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
        10: 'A', 11: 'B', 12: 'C', 13: 'D', 14: 'E',
        15: 'F'
    }
    hexadecimal = ''
    while (decimal > 0):
        remainder = decimal % 16
        hexadecimal = conversion_table[remainder] + hexadecimal
        decimal = decimal // 16
    return hexadecimal

def conversion_hex_base64(donnee):
    return codecs.encode(codecs.decode(donnee, 'hex'), 'base64').decode()

def interroger_donnees(deveui_compteur):
    payload = "1201"
    data = set_data(fport=8, payload=payload, machine=deveui_compteur)
    requests.post(url, headers=headers, data=data)

def definir_credit_en_decimal(credit_en_hexa):
    bits_poids_fort = credit_en_hexa[0:4]
    bits_poids_faible = credit_en_hexa[4:8]
    bits_poids_fort = inverser_bits(bits_poids_fort)
    bits_poids_faible = inverser_bits(bits_poids_faible)
    credit_en_hexa = bits_poids_faible + bits_poids_fort
    return int(credit_en_hexa, 16) / 100

def definir_valeur_energie(energie_en_hexa):
    bits_poids_fort = energie_en_hexa[0:4]
    bits_poids_faible = energie_en_hexa[4:8]
    bits_poids_fort = inverser_bits(bits_poids_fort)
    bits_poids_faible = inverser_bits(bits_poids_faible)
    energie_en_hexa = bits_poids_faible + bits_poids_fort
    return int(energie_en_hexa, 16) / 100

def montant_retrait_en_hexa(nombre):
    nombre_en_bin = bin(int(nombre))
    n_4_octet = nombre_en_bin[2:].zfill(32)
    n = ''
    un = '01'.zfill(32)
    #complement à 1
    for i in range(len(n_4_octet)):
        if n_4_octet[i] == '0':
            n=n+'1'
        else:
            n=n+'0'
    n,un = bin(int(n,2)),bin(int(un,2))
    s = bin(int(n,2)+int(un,2))
    if len(s) == 35:
        s = s[3:]
    elif len(s) == 34:
        s = s[2:]
    s_hexa = hex(int(s,2))[2:] #obtention de la valeur en hexa
    #inversion des bits de poids forts et faibles
    s_hexa = inverser_bits(s_hexa[int(len(s_hexa) /2 ):int(len(s_hexa))])+inverser_bits(s_hexa[0:int(len(s_hexa) / 2)])
    payload = "1C{0}01".format(s_hexa)
    return conversion_hex_base64(payload)

def payload_recharge(montant):
    nombre_en_bin = bin(int(montant))
    n_4_octet = nombre_en_bin[2:].zfill(32)
    hexa = hex(int(n_4_octet,2))[2:]
    hexa = hexa.zfill(8)
    hexa = inverser_bits(hexa[int(len(hexa) / 2):int(len(hexa))]) + inverser_bits(hexa[0:int(len(hexa) / 2)])
    payload = "1C{0}01".format(hexa)
    return conversion_hex_base64(payload)



def definir_statut_equipemment(deveui,statut):
    machine = Machine.objects.get(devEUI=deveui)
    if statut == "01":
        etat = machine.etat
        etat.etat_valve="off"
        etat.save()
        print(machine.etat.etat_valve)
        return "Etteint"
    elif statut == "00":
        etat = machine.etat
        etat.etat_valve = "on"
        etat.save()
        return "Allume"
    else:
        return "Anormal"


def definir_statut_alarme(statut):
    if statut == "01":
        return "Alarme"
    elif statut == "00":
        return "Normal"
    elif statut == "D2":
        return "Echec"
    else:
        return "Echec"


def bcd_conversion(gandeur_electrique):
    taille = len(gandeur_electrique)
    grandeur_electrique = gandeur_electrique[int(taille / 2):taille] + gandeur_electrique[0:int(taille / 2)]
    return float(grandeur_electrique)


def definir_mois(indice):
    liste_mois = [
        "Jan", "Fev", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Aout", "Sept", "Oct", "Nov", "Dec"
    ]
    try:
        return liste_mois[indice - 1]
    except:
        return None


def definir_jour(indice):
    liste_jours = [
        "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"
    ]
    try:
        return liste_jours[indice - 1]
    except:
        return None
