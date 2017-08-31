
var map;
function initMap() {
    var zerozero= {lat: 0, lng: 0};

    map = new google.maps.Map(document.getElementById('map'), {
      zoom: 3,
      center: zerozero,
      mapTypeId: 'satellite'
    });

}
var cleanPyCoords = function(c){
    return {lat:Number(c.lat),lng:Number(c.lon)};

}

var scanPath;
$(document).ready(function(){
    $('#infile').click(function(){
        external.loadFile(function(file){
            $('#fname').html(file);
            $('#generate').click();
        });
    });

    $('#generate').click(function(){
        if(!($('#alt').val()&&$('#bearing').val()))return;
        if($('#fname').html() == 'No Input File') return;
        external.createPath(function(coords,bounds){
            if(scanPath) scanPath.setMap(null);
            coords = _.map(coords,(c)=>cleanPyCoords(c));
            bounds = _.map(bounds,(c)=>cleanPyCoords(c));

            scanPath = new google.maps.Polyline({
                path:coords,
                geodesic:true,
                strokeColor: '#FF0000',
                strokeOpacity:1.0,
                strokeWeight: 2
            });

            boundBox=new google.maps.LatLngBounds(bounds[0],bounds[1]);
            scanPath.setMap(map);
            map.fitBounds(boundBox);
            map.setZoom(map.getZoom()-1);
        
        });
    });

    $('#alt').change(function(){
        external.setAlt($(this).val());
        $('#generate').click();
    });
    $('#bearing').change(function(){
        external.setBearing($(this).val());
        $('#generate').click();
    });
    $('#save').click(function(){
        external.savePath();
    });



});
