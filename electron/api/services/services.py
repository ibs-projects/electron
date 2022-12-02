import base64

from django.http import HttpResponse
from datetime import  datetime
from .utilities import inverser_bits, conversion_hex_base64, bcd_conversion, definir_credit_en_decimal, \
    definir_statut_alarme, definir_statut_equipemment, decimalToHexadecimal, montant_retrait_en_hexa, \
    definir_valeur_energie
from django.shortcuts import get_object_or_404
from elec_meter.models import InfoSignal, Reporting, Machine, Historique,Transac
import codecs

CREDIT = {}



def recuperer_periode_push(signal):
    data = signal.data
    payload = data[2:][:-2]


def conversion_montant_recharge_base64(unites):
    code_commande = "1C"
    frame_id = "01"
    unites_d = unites*100 #unités en decimal
    unites = decimalToHexadecimal(unites_d)
    if len(unites) % 2 != 0:
        unites = "0"+unites
    unites = inverser_bits(unites)
    requete = code_commande+unites+"0000"+frame_id
    return conversion_hex_base64(requete)

def charger_donnees_report(signal):
    payload = signal.data
    machine = signal.machine
    if len(payload) == 64:
        if payload[2:4] == "05":
            donnees = Reporting(
                infos_signal = signal,
                voltage=bcd_conversion(payload[4:8]) / 10,current = bcd_conversion(payload[8:14])/10,
                total_positive_active_energy = bcd_conversion(payload[14:22])/1000,
                active_power_rate_tip = bcd_conversion(payload[22:30]),
                active_power_rate_peak = bcd_conversion(payload[30:38]),
                active_power_rate_flat = bcd_conversion(payload[38:46]),
                active_power_rate_valley = bcd_conversion(payload[46:54]),
                equipment_statut = payload[54:56],alarm_statut = payload[56:58],
                downlink_signal_strength = payload[58:60],downlink_snr = payload[60:62],
                frame_identification = payload[62:64]
            )
            donnees.save()
            print(donnees)
        else:
            return "Type de compteur indefini"
    elif len(payload) == 84:
        if payload[2:4] == "07":
            donnees = Reporting(
                infos_signal = signal,
                voltage_a=bcd_conversion(payload[4:8]),voltage_b = bcd_conversion(payload[8:12]),
                voltage_c = bcd_conversion(payload[12:16]),current_phase_a = bcd_conversion(payload[16:22]),
                current_phase_b = bcd_conversion(payload[22:28]),current_phase_c = bcd_conversion(payload[28:34]),
                total_positive_active_enery = bcd_conversion(payload[34:42]),
                active_power_rate_tip = bcd_conversion(payload[42:50]),
                active_power_rate_peak = bcd_conversion(payload[50:58]),
                active_power_rate_flat = bcd_conversion(payload[58:66]),
                active_power_rate_valley = bcd_conversion(payload[66:74]),equipment_status = payload[74:76],
                alarm_status = payload[76:78],downlink_signal_strength = payload[78:80],
                downlink_signal_to_noise_ratio = payload[80:82],frame_identification = payload[82:84]
            )
            donnees.save()
        else:
            return "Type de compteur inconnu"
    else:
        return "Taille des données inconsistante"

def charger_historique(signal):
    infos_signal = signal
    machine = get_object_or_404(Machine,pk=signal.machine)
    payload = signal.data
    if len(payload) == 50:
        donnees = Historique(
            machine=machine,infos_signal=infos_signal,
            energie_active=bcd_conversion(payload[14:22])/1000,
            unites = definir_credit_en_decimal(payload[22:30]),
            tension = bcd_conversion(payload[30:34])/10,
            courant = bcd_conversion(payload[34:40]) / 1000,
            statut_equipement = definir_statut_equipemment(machine.devEUI,payload[40:42]),
            statut_alarme = definir_statut_alarme(payload[42:44]),
            intensite_downlink = payload[44:46],
            snr = bcd_conversion(payload[46:48])
        )
        donnees.save()
    elif len(payload) == 70:
        donnees = Historique(
            machine=machine,infos_signal=infos_signal,
            energie_active=bcd_conversion(payload[14:22]) / 1000,
            unites=definir_credit_en_decimal(payload[22:30]),
            tension_a=bcd_conversion(payload[30:34]) / 10,
            tension_b=bcd_conversion(payload[34:38]) / 10,
            tension_c=bcd_conversion(payload[38:42]) / 10,
            courant_a=bcd_conversion(payload[42:48]) / 1000,
            courant_b=bcd_conversion(payload[48:54]) / 1000,
            courant_c=bcd_conversion(payload[54:60]) / 1000,
            statut_equipement=payload[40:42],
            statut_alarme=payload[42:44],
            intensite_downlink=payload[44:46],
            snr=bcd_conversion(payload[46:48])
        )
        donnees.save()
    else:
        HttpResponse("Il y'a une erreur dans le format de données.")

def recuperer_credit(signal):
    infos_signal = signal
    machine = get_object_or_404(Machine,pk=signal.machine)
    payload = signal.data
    credit = signal.data[2:][:-2]
    if credit == "":
        return "";
    else:
        credit_en_hexa = inverser_bits(credit)
        credit_en_hexa = inverser_bits(credit[0:int(len(credit_en_hexa)/2)]) + inverser_bits(credit[int(len(credit_en_hexa)/2):int(len(credit_en_hexa)/2)])
        credit_decimal = int(credit_en_hexa,16) / 100
        return credit_decimal

def resume_conso_jour(signal):
    machine = get_object_or_404(Machine,pk=signal.machine)
    donnees = signal.data
    jour_conso = donnees[2:8]
    heure = int(donnees[8,10],16)
    t_energie_active = definir_valeur_energie(donnees[10,18])
    energie = donnees[18,22]
    cout = donnees[22,28]


def switch(id_signal):
    signal = get_object_or_404(InfoSignal,pk=id_signal)
    code_commande = signal.data[0:2]
    machine = signal.machine
    if code_commande == "02":
        charger_donnees_report(signal)
    elif code_commande == "04":
        recuperer_periode_push(signal)
    elif code_commande == "1c":
        recuperer_credit(signal)
    elif code_commande == "00":
        return HttpResponse("Echec de la requete")
    elif code_commande == "12":
        charger_historique(signal)
    elif code_commande == "13":
        resume_conso_jour(signal)







