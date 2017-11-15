const ROUTE_NAME_LI = "<li class='route-name-li'> "+
"<input id='route-name-{}' class='route-name-in' type='text'>"+
"</li>";

var greatest_id = 0;
var addRouteLi = function(id){
    if (id===undefined){
        greatest_id+=1;
        id=greatest_id;
    }
    $('#drawn-paths').append(ROUTE_NAME_LI.replace('{}',id).replace('{}',id));
    $('#route-name-'+id).val('Path '+id);
    return $('#route-name-'+id);
};


$(document).ready(function(){
    $('#draw-panel').resizable({
        handles: 'e',
        alsoResize:'#control-panel'
    });
    $('#control-panel').resizable({
        handles: 'e',
        alsoResize:'#draw-panel'
    });
    $('#poly-list-panel').resizable({
        handles: 'w'
    });
    $('#map-panel').resizable({
        handles:'e, w, n, s'
    });
    $('.mbar-item').click(function(){

        var my_dropdown = $('#'+$(this).attr('id')+'-drop');
        var my_showing = my_dropdown.hasClass('mbar-drop-showing');
        $('.mbar-drop').each(function(){
            $(this).removeClass('mbar-drop-showing');
        });

        if(my_showing){
            my_dropdown.removeClass('mbar-drop-showing');
        }else{
            my_dropdown.css({left:$(this).offset().left});
            my_dropdown.addClass('mbar-drop-showing');
        }
    });
    $('.mbar-drop a').click(function(){
        $(this).parent().removeClass('mbar-drop-showing');

    });

});
