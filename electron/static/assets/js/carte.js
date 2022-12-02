//console.log('ok');
function init(){
    var coordGabon = {
        lat: -0.803689,
        lng: 11.609444
    }

    var map = L.map('mapid').setView([coordGabon.lat, coordGabon.lng],13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19,attribution: '© OpenStreetMap'}).addTo(mymap);
}