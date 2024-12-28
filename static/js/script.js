function initMap() {
    // Latitude e Longitude do local
    var location = { lat: -7.1261, lng: -34.9857 };

    // Criação do mapa
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,  // Nível de zoom
        center: location  // Centraliza o mapa no local
    });

    // Adiciona o pin (marcador) no mapa
    var marker = new google.maps.Marker({
        position: location,
        map: map,
        title: 'Rua Edson de Queiroz, 129 - Centro, Santa Rita - PB'
    });
}

// A função initMap será chamada automaticamente quando o script da API do Google Maps for carregado.
