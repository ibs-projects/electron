
$(document).ready(function(){
    $("#modiferInfoClient").on("click",function(){
        $.ajax({
            type: "post",
            url: "{% url 'elec_meter:modifier_infos_client' %}",
            data: {
                "csrfmiddlewaretoken" : "{{  csrf_token  }}",
                "num_compteur": "{{compteur.devEUI}}",
                "nom_client": $("#nom_client").val(),
                "prenom_client": $("#prenom_client").val(),
                "email_client": $("#email_client").val(),
                "tel_client": $("#tel_client").val(),
                "num_machine": $("#num_machine").val(),
            },
            success: function(reponse){
                if(reponse["statut"]=="echec"){
                    $("#reponse1").text(reponse["message"]);
                    $("#reponse1").show();
                }else{
                    location.reload();
                }
            },
            error: function(){alert("Erreur ajax !")}
        });
    });
    $("#modiferInfoCompteur").on("click",function(){
        $.ajax({
            type: "post",
            url: "{% url 'elec_meter:modifier_nom_compteur' %}",
            data: {
                "csrfmiddlewaretoken" : "{{  csrf_token  }}",
                "devName": $("#devName").val(),
                "num_machine": $("#num_machine").val(),
                "idcompteur":$("#idcompteur").val()
            },
            success: function(reponse){
                if(reponse["statut"]=="echec"){
                    $("#reponse").text(reponse["message"]);
                    $("#reponse").show();
                }else{
                    location.reload();
                }
            },
            error: function(){alert("Erreur ajax !")}
        })
    });
    $("#btnModifierPeriodePush").on("click",function(){
        $.ajax({
            type: "post",
            url: "{% url 'elec_meter:modifier_periode' %}",
            data: {
                "csrfmiddlewaretoken" : "{{  csrf_token  }}",
                "periode": $("input[name=example-radios]:checked","#periodeOptionForm").val(),
                "devEUI": "{{compteur.devEUI}}",
                "fPort": "{{donnees.infos_signal.fPort}}"
            },
            success: function(reponse){
                alert(reponse["message"]);
            },
            error: function(){alert("Erreur ajax");}
        });
    });
    $(".allumer_eteindre").on("click",function(){
        var action = $(this).attr("act");
        $.ajax({
            type: "post",
            url: "{% url 'elec_meter:modifier_etat_valve' %}",
            data:{
                "csrfmiddlewaretoken" : "{{  csrf_token  }}",
                "action": action,
                "devEUI": "{{compteur.devEUI}}",
                "fPort": "{{donnees.infos_signal.fPort}}"
            },
            success: function(reponse){
                alert(reponse["message"]);
                location.reload();
            },
            error: function(){alert("Erreur")}
        });

    });
});
$(document).ready(function(){
    $("#suppr_machine").on("click",function(){
     Swal.fire({
      title: 'Etes vous sur?',
      text: "Vous etes sur le point de supprimer ce compteur!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      cancelButtonText: 'Non',
      confirmButtonText: 'Oui'
    }).then((result) => {
      if (result.isConfirmed) {

        $.ajax({
            type: "post",
            url: "{% url 'elec_meter:suppression_compteur' %}",
            data: {
                "csrfmiddlewaretoken" : "{{  csrf_token  }}",
                "compteur": "{{compteur.devEUI}}"
            },
            success: function(){
                Swal.fire(
                  'Supprimé!',
                  'Compteur supprimé.',
                  'success'
                );
                window.location.href = "{% url  'elec_meter:liste_compteurs' %}";
            },
            error: function(){alert("Erreur ajax");}
        });
      }
    });

});
});
$("#achatCredit").click(function(){
    $.ajax({
        type: "post",
        url: "{% url 'elec_meter:acheter_credit_compteur' %}",
        data: {
            "csrfmiddlewaretoken" : "{{  csrf_token  }}",
            "devEUI": "{{compteur.devEUI}}",
            "montant_recharge": $("#montant_recharge").val()
        },
        success: function(reponse){
            alert(reponse["message"]);
            document.location.reload();
        },
        error: function(){alert("Erreur ajax !")}
    });
});
$("#btnRechergeUnites").click(function(){
    $.ajax({
        type: "post",
        url: "{% url 'elec_meter:recharge_unites' %}",
        data: {
            "csrfmiddlewaretoken" : "{{  csrf_token  }}",
            "compteur_a_crediter": "{{compteur.devEUI}}",
            "code_recharge": $("#code").val()
        },
        success: function(reponse){
            alert(reponse["message"]);
            document.location.reload();
        },
        error: function(){alert("Erreur ajax !")}
    });
});
$("#btnTransfertUnites").click(function(){
    $.ajax({
        type: "post",
        url: "{% url 'elec_meter:transfert' %}",
        data: {
            "csrfmiddlewaretoken" : "{{  csrf_token  }}",
            "compteur1": "{{compteur.devEUI}}",
            "compteur2": $("#beneficiaire").val(),
            "montant": $("#mtn_transfert").val()
        },
        success: function(reponse){
            alert(reponse["message"]);
            document.location.reload();
        },
        error: function(){alert("Erreur ajax !")}
    });
});