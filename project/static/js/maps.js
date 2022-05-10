function initMap() {

    var directionsService = new google.maps.DirectionsService();

    calcRoute(directionsService);

    document.getElementById("button").addEventListener("click",() =>{
        calcRoute(directionsService)
    })
}
  
function calcRoute(directionsService) {
    var mapProp = {
        zoom:14,
        center : {lat:37.77,lng:-122.447},
    }
    var map = new google.maps.Map(document.getElementById("map"),mapProp);
    var start = document.getElementById('start').value;
    var end = document.getElementById('end').value;
    var request = {
      origin:start,
      destination:end,
      travelMode: 'WALKING',
      provideRouteAlternatives: true,
    };
    directionsService.route(request, function(response, status) {
        if (status == google.maps.DirectionsStatus.OK) {
            len = response.routes.length
            // color = ['red','green','blue']
            
            for (var i = 0; i < len; i++) {
            
                new google.maps.DirectionsRenderer({
                    map: map,
                    directions: response,
                    routeIndex: i,
                    polylineOptions: {
                        strokeColor: color[i]
                      }
                });
            }
        } else {
            console.log("Unable to retrieve your route<br />");
        }
    });
  }
