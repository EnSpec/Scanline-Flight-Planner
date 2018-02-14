var map; // the global google maps api map object
var searchBox; // the global google maps searchbar object
var resetBounds = false; //whether to set google maps bounds to newly drawn areas
var MODE = 'pan'; //'pan' or 'draw';
var UNITS = "US";


/*
 * The python side is implemented with a {lat,lon} dict, while google
 * maps uses {lat,lng}. These functions convert between the two.
 *
 */
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




/*
 * Unit conversion functions. Imperial units used for display only.
 */

var km2mi = function(km){ return Number(km)*0.621371 }
var mi2km = function(mi){ return Number(mi)/0.621371 }

var m2ft = function(m){ return Number(m)*3.28084 }
var ft2m = function(feet){ return Number(feet)/3.28084 }

var ms2kts = function(ms){ return Number(ms)*1.94384 }
var kts2ms = function(kts){ return Number(kts)/1.94384 }



/*
 * This object manages a collection of polygons created by the google maps
 * drawing api
 */
var userDrawnRegion = {
    drawnAreas: [], // areas drawn by the user
    deletedAreas: [], //keep track of deleted areas for undo feature
    init:function(){
        //call this once map is initialized
        var self=this;

        //set up a google maps drawingManager to draw blue polygons
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
        //bind the completion of a polygon drawing to self.closeVertices
        google.maps.event.addListener(this.drawingManager,'overlaycomplete',
                function(event){self.closeVertices(event)});

    },

    /*
     * Pop the latest deleted polygon and add it back to drawnAreas
     */
    undoDelete: function(){
        if(this.deletedAreas.length == 0){
            $('#undo_button').prop('disabled',true);
        } else {
            var poly_info = this.deletedAreas.pop();
            this.closeVertices(undefined,poly_info[0],poly_info[1]);
            poly_info[0].setMap(map);
        }
    },

    /*
     * When loading from a file, we recieve a list of coordinates. Turn that 
     * list into a polygon and add it to drawnAreas
     */
    addPolyFromCoords: function(coords,name){
        var newPoly = new google.maps.Polygon({
            paths:coords,
            strokeColor:'#0000ff',
            strokeOpacity:0.8,
            strokeWeight:2,
            fillColor: '#0000ff',
            fillOpacity: (MODE=='draw')?0.35:0,
            draggable: MODE=='draw',
            editable: MODE=='draw'
        });
        newPoly.setMap(map);
        this.closeVertices(undefined,newPoly,name);
    },

    /*
     * Bind functions to a newly drawn polygon and add it to drawnAreas
     */
    closeVertices: function(event,newPoly,name){
        //if newPoly wasn't passed as a parameter, try to get it from event
        if(newPoly === undefined)
            newPoly = event.overlay;

        //sometimes a poly doesn't get completed, in that case delete it
        if(newPoly.getPath().getLength() < 3){
            newPoly.setMap(null);
            return;
        }

        newPoly.setOptions({zIndex:1999});
        var self = this;

        //add a name box for the new polygon in the sidebar
        var my_label = addRouteLi();
        my_label.mouseenter(function(){ self.highlight(newPoly);});
        my_label.mouseleave(function(){ self.unhighlight(newPoly); });
        if(name)
            my_label.find('input').eq(0).val(name);
        newPoly.name_label = my_label;
        //move the cursor into the name box for easy typing
        my_label.focus();
        my_label.select();
        
        /* remove newPoly from the map and add it to the deletedAreas list
         */
        var removeMe = function(event){
            //remove the poly from the map and splice it from the poly list
            $('#undo_button').prop('disabled',false);
            newPoly.name_label.remove();
            newPoly.setMap(null);
            self.drawnAreas.splice(self.drawnAreas.indexOf(newPoly),1);
            self.deletedAreas.push([newPoly,
                newPoly.name_label.find('input').eq(0).val()]);
            if(self.drawnAreas.length==0){
                self.hideScanLines();
                external.setHome(null);
            }
        }

        //bind removeMe to the 'X' button next to the poly's name box
        my_label.find('a').eq(0).click(function(){
            removeMe();
            if(MODE=='pan')
                generatePath();
        });

        //turn the polygon darker and highlight its label on mouseover
        newPoly.addListener('mouseover',function(event){
            self.highlight(newPoly);
        });
        newPoly.addListener('mouseout',function(event){
            self.unhighlight(newPoly); 
        });

        //set the drawingManager back to pan mode
        this.drawingManager.setOptions({drawingMode:null});
        this.drawnAreas.push(newPoly);
    
    },

    /*
     * Turn a polygon darker and make its outline thicker
     */
    highlight:function(area){
        area.name_label.find('input').eq(0).addClass('highlighted');
        area.setOptions({
            strokeColor:'#0000aa',
            strokeWeight:4,
            fillColor: '#0000aa',
        });
    },
    
    /*
     * Turn a polygon back to unhighlighted style
     */
    unhighlight:function(area){
        area.name_label.find('input').eq(0).removeClass('highlighted');
        area.setOptions({
            strokeColor:'#0000ff',
            strokeWeight:2,
            fillColor: '#0000ff',
        });
    },

    /*
     * Return a nested list of the coordinates of each polygon in drawnAreas
     * Coordinates are converted to python format
     */
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

    /*
     * Return a list of the value in the name box of each polygon in drawnAreas
     */
    getNames: function(){
        return _.map(this.drawnAreas,function(area){
            return area.name_label.find('input').eq(0).val();
        });
    },


    /*
     * hide each scanline while user is drawing
     */
    hideScanLines:function(){
        if(scanLines.length)_.each(scanLines,(s)=>s.setMap(null));
        if(scanLineBounds.length)_.each(scanLineBounds,(s)=>s.setMap(null));
        _.each(this.drawnAreas,function(area){
            area.setOptions({
                fillOpacity: 0.35,
                draggable: true,
                editable:true
            });
        });
    },

    /*
     * hide scanlines and re-enable editing of polygons
     */
    enterDrawMode:function(){
        if(scanPath) scanPath.setMap(null);
        if(homeMarker) homeMarker.setMap(null);
        this.hideScanLines();
        this.drawingManager.setMap(map);
        this.drawingManager.setOptions({drawingMode:'polygon'});
    },

    /*
     * Make polygons uneditable
     */
    exitDrawMode:function(){
        //this.closeVertices();
        _.each(this.drawnAreas,function(area){
            area.setOptions({
                fillOpacity: 0.0,
                draggable: false,
                editable:false
            });
        });
        this.drawingManager.setMap(null);

    },

    hasDrawnRegions: function(){
        return this.drawnAreas.length > 0;
    },    


};


var homeMarker; //google maps marker, used to set starting location for uav
var resetHome = true; //whether to move the home icon when the path is changed

/*
 * create a new home marker if one doesn't exist
 */

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
      mapTypeId: 'satellite',
      fullScrenControl: false,
      mapTypeControlOptions:{
        position: google.maps.ControlPosition.TOP_RIGHT,
      }
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
        if(MODE=='draw'){
            console.log(event.latLng.lat(),event.latLng.lng());
            userDrawnRegion.addVertex(event.latLng);
        } else {
            console.log("not in draw mode!");
        } 
    });

    userDrawnRegion.init();
};

var setScanSpeed=function(speed){
    if(UNITS=="US")
        $('#scan_speed').html(Math.round(ms2kts(speed)));
    else
        $('#scan_speed').html(Math.round(speed));
    if(speed > 0){
        var seconds = Math.floor(1000*Number($('#scan_len').html())/Number(speed));
        var date = new Date(null);
        date.setSeconds(Math.abs(seconds));
        console.log(seconds);
        $('#scan_time').html(date.toISOString().substr(11,8));
    }
};

var createPathCallback= function(coords,bounds,dist,speed,pxsize,scanlines){
    coords = _.map(coords,cleanPyCoords);
    bounds = _.map(bounds,cleanPyCoords);
    if(UNITS=='US'){
        $('#scan_len').html(Math.round(km2mi(dist)));
        $('#px_size').html(m2ft(pxsize).toFixed(2));
    }else{
        $('#scan_len').html(Math.round(dist));
        $('#px_size').html(Number(pxsize).toFixed(2));
    }
    setScanSpeed(speed);
    if($('#vehicle').val()=='fullscale')
        setAirplaneScanPath(coords,scanlines);
    else
        setScanPath(coords);

    if(resetHome){
        if($('#vehicle').val()=='quadcopter')
            setHomeMarker(coords[0]);
        if(resetBounds){
            setBoundBox(bounds);
            resetBounds=false;
        }
    }
    resetHome=true;
}

var createPathFailedCallback = function(){
    alert("Scan Region too large to compute. Please select a smaller region.");
}

var loadFileCallback = function(coords,vehicle,alt,bearing,sidelap,
                                overshoot,fov,ifov,px,s_name,p_names){
    if(UNITS=='US'){
        alt = m2ft(alt);
        overshoot = km2mi(overshoot/1000);
    }else{
        overshoot /= 1000; 
    }
    //using jQuery didn't seem like a mistake until now
    $('#vehicle').val(vehicle);
    $('#alt').val(alt.toFixed(0));
    $('#bearing').val(bearing);
    $('#sidelap').val(sidelap);
    $('#overshoot').val(overshoot.toFixed(2));
    $('#fov').val(fov);
    $('#ifov').val(ifov);
    $('#ifov').val(ifov);
    $('#px').val(px);
    $('#spectrometer').val(s_name);
    _.each(coords,function(perim,idx){
        perim = _.map(perim,cleanPyCoords);
        userDrawnRegion.addPolyFromCoords(perim,p_names[idx]);
    });
    resetBounds = true;
    generatePath();
}

var generatePath = function(){
    if(!($('#alt').val()&&$('#bearing').val())) return;
    var coords = userDrawnRegion.getCoords();
    if(coords) external.setNames(userDrawnRegion.getNames());
    external.createPath(coords,createPathCallback,createPathFailedCallback);
}

var toggle_draw_mode = function(){
    if(MODE=='pan'){
        MODE = 'draw';
        $('#generate,#save,#infile').prop('disabled',true);
        $('#pac-input').prop('disabled',false);
        $('#start_draw').html("Finish");
        $('#on-map-draw').html("&#10003;");
        userDrawnRegion.enterDrawMode();
        map.setOptions({
             disableDoubleClickZoom: true
        });
    } else {
        MODE = 'pan';
        $('#generate,#save,#infile').prop('disabled',false);
        $('#start_draw').html("Draw Area");
        $('#on-map-draw').html("&#128393;");
        userDrawnRegion.exitDrawMode();
        if(userDrawnRegion.hasDrawnRegions())
            generatePath();
        map.setOptions({
             disableDoubleClickZoom: false
        });
    }
};

$(document).ready(function(){
    $(document).keydown(function(event){
        if(event.ctrlKey && event.which == 90){
            userDrawnRegion.undoDelete();
            generatePath();
        }
    });
    $('#undo,#undo_button').click(function(){
        userDrawnRegion.undoDelete();
        generatePath();

    });

    //bind functions to buttons
    $('#start_draw').click(toggle_draw_mode);
    $('#on-map-draw').click(toggle_draw_mode);

    $('#spectrometer').change(function(){
        external.setSpectrometer($(this).val(),function(fov,ifov,pix){
            $('#fov').val(fov);
            $('#ifov').val(ifov);
            $('#px').val(pix);
        });
        generatePath();
    });

    $('#fov, #ifov, #px').change(function(){
        $('#spectrometer').val('Custom');
        external.setCustomSpectrometer($('#fov').val(),$('#ifov').val(),
                $('#px').val());
        generatePath();

    });
    $('#alt').change(function(){
        if(UNITS=='US')
            external.setAlt(ft2m($(this).val()));
        else
            external.setAlt($(this).val());
        generatePath();
    });
    $('#bearing').change(function(){
        console.log("ch-ch-ch-ch-changes!");
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
	if(UNITS=='US')
            external.setOvershoot(5280*ft2m($(this).val()));
	else
            external.setOvershoot(1000*$(this).val());
        generatePath();
    });
    $('#sidelap').change(function(){
        external.setSidelap($(this).val());
        generatePath();
    });
    $('#save,#on-map-save').click(function(){
        external.savePath($('#fmt').val());
    });

    $('#save_native').click(function(){
        external.savePath('Project');
    });
    $('#load').click(function(){
        external.loadFile(loadFileCallback);
    });

    $('#summon_help').click(function(){
        $('#darken').height($(window).height());
        $('#darken').show();
    });



    $('#us').click(function(){
        if(UNITS=="US")return;
        $('#alt_label').html('Altitude (ft):');
        $('#appr_label').html('Approach (mi):');
        $('#dist_label').html('Distance (km):');
        $('#speed_label').html('Velocity (kts):');
        $('#px_label').html('Pixel Size (ft):');

        $('#alt').val(Math.round(m2ft($('#alt').val())));
        $('#overshoot').val(km2mi($('#overshoot').val()).toFixed(2));

        UNITS = 'US';
        generatePath();
    });

    $('#metric').click(function(){
        if(UNITS=="metric")return;
        $('#alt_label').html('Altitude (m):');
        $('#appr_label').html('Approach (km):');
        $('#dist_label').html('Distance (km):');
        $('#speed_label').html('Velocity (m/s):');
        $('#px_label').html('Pixel Size (m):');

        $('#alt').val(Math.round(ft2m($('#alt').val())));
        $('#overshoot').val(mi2km($('#overshoot').val()).toFixed(2));
            
        UNITS = 'metric';
        generatePath();
    });
    $('#overshoot, #alt').change();
});
