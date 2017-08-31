const X0 = 950;
const Y0 = 65;
const xScale = .185;
const yScale = .21;
var path_plot_svg;
var stepsToCanvasLoc=function(xsteps,ysteps){
    return{
        x:X0-xsteps/xScale,
        y:Y0+ysteps/yScale
    };
}

var closet_multiple = function(x,mul){
    if(x%mul > mul/2){
        return x - x%mul + mul;
    }else{
        return x - x%mul;
    }
};
var canvasLocToSteps = function(yloc,xloc){
    var grid = Number($('#grid_size').val());
    var x=(xScale*(X0-xloc))|0;
    var y=(yScale*(yloc-Y0))|0;
    x= closet_multiple(x,grid);
    y= closet_multiple(y,grid);
    return{
        x:x,
        y:y
    }; 
}
var parse_coords = function(coordstr){
    var splits=[", ",","," "];
    return _.filter(_.map(splits,function(split){
        if(coordstr.split(split).length == 2){
            return{
                x:Number(coordstr.split(split)[0]),
                y:Number(coordstr.split(split)[1]),
            };
        }else{
            return undefined;
        }
    }))[0];
}

var midpoint_marker = function(coord1,coord2){
    var midpt_x = (coord1.x+coord2.x)/2;
    var midpt_y = (coord1.y+coord2.y)/2;
    return (`<circle cx=${midpt_y} cy=${midpt_x} r=5 fill="white" stroke="black"/>`);
};

var edge_coords = [
    {x:0,y:0},
    {x:160,y:0},
    {x:160,y:140},
    {x:0,y:140}
];

var draw_gridlines = function(){
    //draw gridlines at every 5*step 
    _.each(_.range(0,Math.max(140,160)+1,5*parseInt($('#grid_size').val())),
            function(coord){
        var real_coords = stepsToCanvasLoc(coord,coord);
        path_plot_svg.append('line')
            .attr("class","svg-gridline")
            .attr("x1",0).attr("y1",real_coords.x)
            .attr("x2",800).attr("y2",real_coords.x)
        path_plot_svg.append('line')
            .attr("class","svg-gridline")
            .attr("x1",real_coords.y).attr("y1",0)
            .attr("x2",real_coords.y).attr("y2",1000)
    });
    //draw a boundary box for the valid x,y values
    var last_coords = stepsToCanvasLoc(edge_coords[0].x,edge_coords[0].y);
    _.each(_.rest(edge_coords).concat(edge_coords[0]),function(coords){
        coords = stepsToCanvasLoc(coords.x,coords.y);
        console.log(coords);
        path_plot_svg.append('line')
            .attr("class","svg-boundline")
            .attr("x1",last_coords.y).attr("y1",last_coords.x)
            .attr("x2",coords.y).attr("y2",coords.x);
        last_coords = coords;
    });

};
var label_edges = function(){
    _.each(edge_coords,function(coords){
        var move_coords = {
            x:coords.x,
            y:coords.y
        };
        real_coords = stepsToCanvasLoc(move_coords.x,move_coords.y);
        real_coords.x += (real_coords.x == X0)?25:-3;
        real_coords.y += (real_coords.y == Y0)?0:-13*(coords.x+'(,)'+coords.y).length;
        path_plot_svg.append('text')
            .attr('class','coord_label')
            .attr('x',real_coords.y).attr('y',real_coords.x)
            .attr('font-size',24).attr('font-family','monospace')
            .html('('+coords.x+','+coords.y+')');
    });

};

var set_active = function(key){
    key = Number(key);
    var node = path_plot_svg.selectAll('circle[key="'+key+'"]');
    var headline = path_plot_svg.selectAll('line[key="'+key+'"]');
    var footline = path_plot_svg.selectAll('line[key="'+(key+1)+'"]');
    //there's probably a cleaner way to determine this
    var isLastNode = footline._groups[0].length == 0;
    if(!node.classed('active')){
        path_plot_svg.selectAll('circle.node-end.active').
            classed('active',false);
        node.classed('active',true);
    }

    $('.path_node.active').removeClass('active'); 
    var coordbox = $('.path_node[num="'+key+'"] .coord');
    coordbox.closest('.path_node').addClass('active');
    return {
        isLastNode:isLastNode,
        key:key,
        node:node,
        headline:headline,
        footline:footline,
        coordbox:coordbox
    };
}


/* Takes an object with the following parameters:
 * coordbox is a jquery input text object,
 * node is a d3 svg circle object
 * headline and footline are d3 svg line objects
 * then updates the active node and any other svg elements
 * associated with it
 */
var update_active_node = function(active_info){
    var coords = parse_coords(active_info.coordbox.val());
    var coord = stepsToCanvasLoc(coords.x,coords.y);
    active_info.node.attr("cx",coord.y).attr("cy",coord.x);
    active_info.headline.attr("x2",coord.y).attr("y2",coord.x);
    active_info.footline.attr("x1",coord.y).attr("y1",coord.x);
}

var insert_node = function(active_info){

};
/*Basically reimplementing jquery-ui.draggable
 */
var DBL = false;
var node_click_func = function(node){

    var key = 0;
    if(DBL){
        DBL = false;
        append_node($('.path_node.active'),false);
        key = 1;
    }else{
        DBL=true;
        setTimeout(function(){DBL=false},400);
    }
    var vbstr = $('#path_plot').attr('viewBox');
    key += Number(node.attr('key'));
    var active_info = set_active(key);
    //we're using a weird mix of jQuery and d3, just deal with it for now
    var viewbox = {
        x0: Number(vbstr.split(' ')[0]),
        y0: Number(vbstr.split(' ')[1]),
        xspan: Number(vbstr.split(' ')[2]),
        yspan: Number(vbstr.split(' ')[3]),
    };
    
    var mouseinfo=new Object();
    var offset = $('#path_plot').offset();
    var offsetX = offset.left;
    var offsetY = offset.top;
    var width = $('#path_plot').width();
    var height= $('#path_plot').height();
    //glorious 30 fps
    var change_throttled = _.throttle(function(){
        update_active_node(active_info);
    },34);
    $(document).mousemove(function(event){
        mouseinfo.x = (viewbox.x0+viewbox.xspan*
                (event.pageX - offsetX)/width)|0;
        mouseinfo.y = Number(viewbox.y0+viewbox.yspan*
                (event.pageY - offsetY)/height)|0;
        var coords = canvasLocToSteps(mouseinfo.x,mouseinfo.y);
        active_info.coordbox.val(coords.x+', '+coords.y);
        change_throttled();
    });
    $(document).mouseup(function(){
        $(document).unbind('mousemove');
    });
}


var draw_path = function(){
    console.log("Redrawing canvas!");
    var coords= _.filter(_.map($('.coord'),function(coord){
        return parse_coords($(coord).val());    
    }));
    var active_key = Number($('.path_node.active').attr('num'));
    //$('.usr-draw').each(function(){$(this).remove()});
    var doForEachCoord = function(callback){
        var last_coords = stepsToCanvasLoc(0,0);
        _.each(coords,function(coord,idx){
            coord = stepsToCanvasLoc(coord.x,coord.y);
            callback(last_coords,coord,idx);
            last_coords = coord;
        });
    };
    path_plot_svg.selectAll('.usr-draw').remove();
    doForEachCoord(function(last_coords,coord,idx){
        path_plot_svg.append('line')
            .attr("class","usr-draw")
            .attr("x1",last_coords.y).attr("y1",last_coords.x)
            .attr("x2",coord.y).attr("y2",coord.x)
            .attr("stroke","red").attr("stroke-width",10)
            .attr("key",idx+1);
        
    });
    doForEachCoord(function(last_coords,coord,idx){
        var nodeclass = "node-end usr-draw";
        if(active_key == idx+1) nodeclass+=' active';
        path_plot_svg.append('circle')
            .attr("class",nodeclass)
            .attr("cx",coord.y).attr("cy",coord.x)
            .attr("key",idx+1)
            .attr("r",7);
    });
    $('.node-end').mousedown(function(){node_click_func($(this),true)});
}

$(document).ready(function(){
    path_plot_svg = d3.select('#path_plot');
    draw_gridlines();
    label_edges();
    $(window).keydown(function(event){
        //don't trigger key-based controls if the user is typing
        if($('input:focus').length > 0) return;
        if(!$('.path_node.active .coord').val()) return;
        
        var coords = parse_coords($('.path_node.active .coord').val());
       
        var step = Number($("#grid_size").val());
        switch(event.key){
            case "ArrowUp":
                $('.path_node.active .coord').val(coords.x+step+', '+coords.y);
                break;
            case "ArrowDown":
                $('.path_node.active .coord').val(coords.x-step+', '+coords.y);
                break;
            case "ArrowLeft":
                $('.path_node.active .coord').val(coords.x+', '+(coords.y-step));
                break;
            case "ArrowRight":
                $('.path_node.active .coord').val(coords.x+', '+(coords.y+step));
                break;
            case "Enter":
                append_node($('.path_node.active'),false);
                break;
            case "delete":
                $('.path_node.active .node_close').click();
                break;
        }
        draw_path();
        //$('.path_node.active').trigger('change');
    });
});
