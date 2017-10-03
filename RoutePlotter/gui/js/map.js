
var map;
var searchBox;
var inDrawMode = false;
var loadFromDrawing = true;
var noFileLoadedText;
var cleanPyCoords = function(c){
    //CEF sometimes converts coords to strings, make sure they're numbers
    return {lat:Number(c.lat),lng:Number(c.lon)};

};

var toPyCoords = function(latLng){
    //convert google.maps.LatLng back to dict for CEF
    return{
        'lat':latLng.lat(),
        'lon':latLng.lng()
    }
}



var f2m = function(feet){
    return Number(feet)*0.3048
}

var km2mi = function(km){
    return Number(km)*0.621371
}

var ms2mph = function(ms){
    return Number(ms)*2.23694
}

vertex_url='http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png';
plus_url='http://maps.google.com/mapfiles/kml/paddle/grn-blank-lv.png';
minus_url='http://maps.google.com/mapfiles/kml/paddle/red-square-lv.png';

var userDrawnRegion = {
    drawnAreas: [],
    vertexMarkers: [],
    init:function(){
        //call this once map is initialized
        var self=this;
        this.vertexImage = new google.maps.MarkerImage(vertex_url,
            new google.maps.Size(30,30),
            new google.maps.Point(0,0),
            new google.maps.Point(15,15)
        );
        this.minusImage = new google.maps.MarkerImage(minus_url,
            new google.maps.Size(30,30),
            new google.maps.Point(0,0),
            new google.maps.Point(15,15)
        );
        this.centerPlus = new google.maps.Marker({
            icon: new google.maps.MarkerImage(plus_url,
                new google.maps.Size(30,30),
                new google.maps.Point(0,0),
                new google.maps.Point(15,15)
            )
        });
        this.centerPlus.addListener('dblclick',function(){
            self.closeVertices();
        });
        this.drawingManager = new google.maps.drawing.DrawingManager({
            drawingMode: google.maps.drawing.OverlayType.MARKER,
            drawingControl: true,
            drawingControlOptions: {
                position: google.maps.ControlPosition.TOP_CENTER,
                drawingModes:['polygon'],
            },
            polygonOptions: {
                strokeColor:'#0000ff',
                strokeOpacity:0.8,
                strokeWeight:2,
                fillColor: '#0000ff',
                fillOpacity: 0.35,
                draggable: true,
                editable:true
            },
        });    
        var self = this;
        google.maps.event.addListener(map,'click',function(){
            self.drawingManager.setOptions({drawingMode:'polygon'});
        });
        google.maps.event.addListener(this.drawingManager,'overlaycomplete',
                function(event){self.closeVertices(event)});
    },

    findCenter: function(){
        if(this.vertexMarkers.length < 3) return;

        var coords=_.map(this.vertexMarkers,(m)=>toPyCoords(m.getPosition()));
        var self = this;
        external.centerOfPoints(coords,function(center){
            self.centerPlus.setMap(map);
            self.centerPlus.setPosition(cleanPyCoords(center));
        });

    },

    addVertex: function(latLng){
    },
    closeVertices: function(event){
        //add the newly drawn poly to our list so that we can pass it to
        //gui.py once the user's done drawing
        var newPoly = event.overlay;
        //sometimes a poly doesn't get completed, in that case delete it
        if(newPoly.getPath().getLength() < 3){
            newPoly.setMap(null);
            return;
        }
        var self = this;
        newPoly.addListener('rightclick',function(event){
            if(!inDrawMode) return;
            //right click the area to delete it
            newPoly.setMap(null);
            self.drawnAreas.splice(self.drawnAreas.indexOf(newPoly),1);
            if(self.drawnAreas.length==0) external.setHome(null);
        });
        this.drawingManager.setOptions({drawingMode:null});
        this.drawnAreas.push(newPoly);
    },
    getCoords: function(){
        var self = this;
        var coords = [];
        _.each(self.drawnAreas,function(area){
            var len = area.getPath().getLength();
            var inner_coords = [];
            _.each(_.range(len),(i)=>{
                inner_coords.push(toPyCoords(area.getPath().getAt(i)));
            });
            coords.push(inner_coords);
        });

        return coords;
    },

    clearDrawing:function(){
        var self = this;
        _.each(self.vertexMarkers,(m)=>m.setMap(null));
        self.vertexMarkers=[];
        _.each(self.drawnAreas,(a)=>a.setMap(null));
        self.drawnAreas=[];
        self.vertexMarkers=[];
        self.centerPlus.setMap(null);

    },
    enterDrawMode:function(){
        if(scanPath) scanPath.setMap(null);
        if(homeMarker) homeMarker.setMap(null);
        if(scanLines.length)_.each(scanLines,(s)=>s.setMap(null));
        if(scanLineBounds.length)_.each(scanLineBounds,(s)=>s.setMap(null));
        _.each(this.drawnAreas,function(area){
            area.setOptions({
                fillOpacity: 0.35,
                draggable: true,
                editable:true
            });
        });
        this.drawingManager.setMap(map);
        this.drawingManager.setOptions({drawingMode:'polygon'});

    },
    exitDrawMode:function(){
        //this.closeVertices();
        _.each(this.drawnAreas,function(area){
            area.setOptions({
                fillOpacity: 0.0,
                draggable: false,
                editable:false
            });
        });
        $('#infile').html(noFileLoadedText);
        this.drawingManager.setMap(null);

    },
    hasDrawnRegions: function(){
        return this.drawnAreas.length > 0;
    },    


};


var homeMarker;
var resetHome = true;
var setHomeMarker = function(latlng){
    if(homeMarker) homeMarker.setMap(null);
    homeMarker = new google.maps.Marker({
        position:latlng,
        map: map,
        draggable:true
            
    });
    homeMarker.setMap(map);
    homeMarker.addListener('dragend',function(event){
        external.setHome(toPyCoords(event.latLng));   
        resetHome = false;
        generatePath()
    });

};

var scanLines=[];
var scanLineBounds=[];
var scanPath;

var setAirplaneScanPath = function(latlngs,scanlines){
    if(scanPath) scanPath.setMap(null);
    if(homeMarker) homeMarker.setMap(null);
    if(scanLines.length > 0){
        _.each(scanLines,(line)=>line.setMap(null));
        _.each(scanLineBounds,(box)=>box.setMap(null));
    };
    
    _.each(_.groupBy(latlngs,(ll,idx)=>Math.floor(idx/4)),function(lls,idx){
        scanLines.push(new google.maps.Polyline({
            path:lls,
            geodesic:true,
            strokeColor: '#FF0000',
            strokeOpacity:1.0,
            strokeWeight: 3,
            map:map,
            zIndex:999
        }));
        scanLineBounds.push(new google.maps.Polygon({
                paths:_.map(scanlines[idx],(c)=>cleanPyCoords(c)),
                strokeColor:'#0000ff',
                strokeOpacity:0,
                strokeWeight:0,
                fillColor: '#4B0082',
                fillOpacity: 0.40,
                map:map
        }));
    });

};

var setScanPath = function(latlngs){
    if(scanPath) scanPath.setMap(null);
    if(scanLines.length > 0){
        _.each(scanLines,(line)=>line.setMap(null));
        _.each(scanLineBounds,(box)=>box.setMap(null));
    };
    scanPath = new google.maps.Polyline({
        path:latlngs,
        geodesic:true,
        strokeColor: '#FF0000',
        strokeOpacity:1.0,
        strokeWeight: 2,
        zIndex:999
    });
    scanPath.setMap(map);
};

var setBoundBox = function(bounds){
    boundBox=new google.maps.LatLngBounds(bounds[0],bounds[1]);
    map.fitBounds(boundBox);
    map.setZoom(map.getZoom()-1);

}

function initMap() {
    var zerozero= {lat: 0, lng: 0};

    map = new google.maps.Map(document.getElementById('map'), {
      zoom: 3,
      center: zerozero,
      mapTypeId: 'satellite'
    });
    //code taken from 
    searchBox = new google.maps.places.SearchBox(
            document.getElementById('pac-input'));
        // Bias the SearchBox results towards current map's viewport.
    map.addListener('bounds_changed', function() {
        searchBox.setBounds(map.getBounds());
    });
    searchBox.addListener('places_changed', function() {
      var places = searchBox.getPlaces();

      if (places.length == 0) {
        return;
      }


      // For each place, get the icon, name and location.
      var bounds = new google.maps.LatLngBounds();
      places.forEach(function(place) {
        if (!place.geometry) {
          console.log("Returned place contains no geometry");
          return;
        }

        if (place.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(place.geometry.viewport);
        } else {
          bounds.extend(place.geometry.location);
        }
      });
      map.fitBounds(bounds);
    });
    
    //if we're in draw mode, double clicking should add a vertex rather than
    //zooming in the map
    map.addListener('dblclick',function(event){
        if(inDrawMode){
            console.log(event.latLng.lat(),event.latLng.lng());
            userDrawnRegion.addVertex(event.latLng);
        } else {
            console.log("not in draw mode!");
        } 
    });

    userDrawnRegion.init();
};

var setScanSpeed=function(speed){
    $('#scan_speed').html(Math.round(ms2mph(speed)));
    $('#scan_speed_ms').html(Math.round(speed));
    var seconds = Math.floor(1000*Number($('#scan_len').html())/Number(speed));
    var date = new Date(null);
    date.setSeconds(seconds);
    $('#scan_time').html(date.toISOString().substr(11,8));
};

var generatePath = function(){
    if(!($('#alt').val()&&$('#bearing').val())) return;
    if(!loadFromDrawing && $('#infile').html() == noFileLoadedText) return;
    var coords = (loadFromDrawing)?userDrawnRegion.getCoords():false;
    external.createPath(coords,function(coords,bounds,dist,speed,scanlines){
        coords = _.map(coords,(c)=>cleanPyCoords(c));
        bounds = _.map(bounds,(c)=>cleanPyCoords(c));
        $('#scan_len').html(Math.round(km2mi(dist)));
        $('#scan_len_km').html(Math.round(dist));
        setScanSpeed(speed);

        if($('#vehicle').val()=='fullscale')
            setAirplaneScanPath(coords,scanlines);
        else
            setScanPath(coords);

        if(resetHome){
            if($('#vehicle').val()=='quadcopter')
                setHomeMarker(coords[0]);
            if(!loadFromDrawing){
                setBoundBox(bounds);
            }
        }
        resetHome=true;
    
    });
}
$(document).ready(function(){
    noFileLoadedText = $('#infile').html();
    $('#infile').click(function(){
        external.loadFile(function(file){
            loadFromDrawing=false;
            resetHome=true;
            external.setHome(null);
            $('#infile').html("File: "+file);
            generatePath();
        });
    });

    //bind functions to buttons
    $('#clear_draw').click(function(){
        userDrawnRegion.clearDrawing();
        external.setHome(null);
    });    
    $('#start_draw').click(function(){
        if(!inDrawMode){
            inDrawMode = true;
            loadFromDrawing = true;
            $('#generate,#save,#infile').prop('disabled',true);
            $('#pac-input').prop('disabled',false);
            $(this).html("Finish Drawing");
            userDrawnRegion.enterDrawMode();
            map.setOptions({
                 disableDoubleClickZoom: true
            });
        } else {
            inDrawMode = false;
            $('#generate,#save,#infile').prop('disabled',false);
            $(this).html("Draw Area");
            userDrawnRegion.exitDrawMode();
            if(userDrawnRegion.hasDrawnRegions())
                generatePath();
            map.setOptions({
                 disableDoubleClickZoom: false
            });
        }
    });

    $('#spectrometer').change(function(){
        external.setSpectrometer($(this).val());
        generatePath();
    });
    $('#alt').change(function(){
        external.setAlt(f2m($(this).val()));
        $('#alt_m').html(Math.floor(f2m($(this).val())));
        generatePath();
    });
    $('#bearing').change(function(){
        console.log("Bearing!");
        external.setBearing($(this).val());
        generatePath();
    });
    $('#frame_pd').change(function(){
        external.setScanPeriod(Number($(this).val())/1000);
        external.getScanSpeed(function(speed){setScanSpeed(speed)});

    });
    $('#vehicle').change(function(){
        external.setVehicle($(this).val());
        generatePath();
    });
    $('#overshoot').change(function(){
        external.setOvershoot(f2m($(this).val()));
        $('#overshoot_m').html(Math.floor(f2m($(this).val())));
        generatePath();
    });
    $('#sidelap').change(function(){
        external.setSidelap($(this).val());
        generatePath();
    });
    $('#save').click(function(){
        external.savePath();
    });

    $('#summon_help').click(function(){
        $('#darken').height($(window).height());
        $('#darken').show();
        $(window).resize(function(){
            $('#darken').height($(this).height());
        });
    });
    $('#darken').click(function(){
        $(this).hide();
        $(window).unbind('resize');
    });
    $('#overshoot, #alt').change();
});
