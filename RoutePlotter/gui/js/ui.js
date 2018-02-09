const ROUTE_NAME_LI = "<li id='route-name-{}' class='route-name-li'> "+
"<input class='route-name-in' type='text'>"+
"<a class='route-li-delete'> &#x274C;</a>"+
"</li>";

var greatest_id = 0;
var addRouteLi = function(id){
    if (id===undefined){
        greatest_id+=1;
        id=greatest_id;
    }
    $('#drawn-paths').append(ROUTE_NAME_LI.replace('{}',id));
    $('#route-name-'+id + ' > input').val('Path '+id);
    return $('#route-name-'+id);
};


$(document).ready(function(){
    /*$('#draw-panel').resizable({
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
    });*/
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
    $('.mbar-drop').find('a').click(function(){
        $(this).parent().parent().removeClass('mbar-drop-showing');

    });

    //lazy implement modals
    var help_menus = ['#draw-help','#spectrometer-help','#settings-help',
    '#parameters-help','#stats-help','#save-help','#paths-help','#darken'];
    var help_access = ['#show-help-draw,#info-draw',
        '#show-help-spectrometer,#info-spectrometer',
        '#show-help-settings,#info-settings',
        '#show-help-parameters,#info-parameters','#show-help-stats,#info-stats',
        '#show-help-save,#info-save','#show-help-paths,#info-paths'];

    $(help_menus.join(',')).click(function(){
        $(help_menus.join(',')).hide();
    });
    _.each(help_access,function(ids,idx){
        $(ids).click(function(){
            $('#darken').show();
            $(help_menus[idx]).show();
        })
    });

});
