//re-number nodes after one is inserted or they are re-ordered
var update_nodenumbers = function(){
    var n_nodes = $('.path_node').length;
    if(n_nodes == 0){
        $('#no_nodes').show();
    }else{
        var count = 1;
        $('.node_num').each(function(){
            $(this).html(count+'.');
            count++;
        });
        var count = 1;
        $('.path_node').each(function(){
            $(this).attr('num',count);
            count++;
        });
    }
    draw_path();
};


var coord_keydown = function(event){
   if(event.keyCode == 13)
       $(this).siblings('.wait').focus();

   if((event.key == ' ' && $(this).val().indexOf(' ') != -1) ||
      (event.key == ',' && $(this).val().indexOf(',') !=-1)){
       event.preventDefault();
       $(this).siblings('.wait').focus();
   }
}

var wait_keydown = function(event){
  if(event.keyCode == 13 || event.key == ' ' ||
          (event.keyCode == 9 && !event.shiftKey)){
      event.preventDefault();
      var next_node = 1+Number($(this).siblings('.node_num').html());
      $('.node_num:contains("'+next_node+'")').siblings('.coord').focus();
      //check that the focus was moved off this
      if($(this).is(':focus')){
          append_node($(this).closest('.path_node'));
          var next_node = 1+Number($(this).siblings('.node_num').html());
          $('.node_num:contains("'+next_node+'")').siblings('.coord').focus();
      }
  }
};


var form_verify = function(form,regex){
    if(regex.test(form.val())){
        form.removeClass('alert-danger');
    } else {
        form.addClass('alert-danger');
    }
};

//use a template literal to create a new node
var get_node_template = function(){
    var n_nodes = $('.path_node').length+1;
    var coord_id = "coord_"+n_nodes;
    var wait_id = "wait_"+n_nodes;
    return new_node = $(`<li class="col-12 path_node" num=${n_nodes}>
          <div class="row">
            <div class="col-12">
                <span>
                <span class="node_num">${n_nodes}.</span>
                Go to <input class="coord" id=${coord_id} placeholder="0 , 0" type="text">,
                wait <input class="wait" id=${wait_id} placeholder="0" type="text">s
                </span>

                <span class='node_opts'>
                   <b class='node_add node-click'>+</b>
                   <span class='node_close node-click'>&#10006;</span>
                </span>
            </div>
           </div>
          </li>`
    );

};

//add on-click and on-change functions to all nodes
//kinda inefficient
var bind_actions_to_nodes = function(){
    //unbind previous function attachments so that things are
    //only called once
    $('.node_close, .node_add').unbind('click');

    $('.node_close').click(function(){
        $(this).closest('.path_node').remove();
        update_nodenumbers();
    });

    $('.node_add').click(function(){
        append_node($(this).closest('.path_node'));
    });

    //unbind previous function attachments so that things are
    //only called once
    $('.coord, .wait, .path_node')
        .unbind('keydown')
        .unbind('click')
        .unbind('change');

    $('.coord, .wait, .path_node').click(function(){
        set_active($(this).closest('.path_node').attr('num'));
    });
    $('.coord, .wait').focus(function(){
        $(this).trigger('click');
    });
    $('.coord').keydown(coord_keydown);
    $('.coord').change(function(){
        form_verify($(this),/^[\s*,*[0-9]+[,|\s]+[0-9]+\s*,*]?$/);
        update_active_node(set_active($(this).closest('.path_node').attr('num')));
    });
    $('.wait').keydown(wait_keydown);
    $('.wait').change(function(){
        form_verify($(this),/^[\s*,*[0-9]+\s*,*]?$/);
        update_active_node(set_active($(this).closest('.path_node').attr('num')));
    });
};

//add a new node at the node after idx
var append_node = function(idx,focus_new){
    console.log(idx);
    $('.path_node.active').removeClass('active');
    $('#no_nodes').hide();
    var n_nodes = $('.path_node').length+1;
    var coord_id = "coord_"+n_nodes;
    var wait_id = "wait_"+n_nodes;
    var new_node = get_node_template();
    if(idx == undefined){
        $('#path_nodes').append(new_node);
        new_node.find('.coord').val("0, 0");
    }else{
        idx.after(new_node);
        new_node.find('.coord').val(idx.find('.coord').val());
        new_node.find('.wait').val(idx.find('.wait').val());
    }

    update_nodenumbers();
    bind_actions_to_nodes();    

    if(!focus_new) return;
    if(idx === undefined){
        var to_focus;
        $($('.coord').get().reverse()).each(function(){
            if(!$(this).val()){
                to_focus = $(this);
            }
        });
        to_focus.focus();
    } else {
        var next_n = Number(idx.attr('num'))+1;
        $('[num="'+next_n+'"]').find('.coord').focus();
    }
};

/* Clears out the current route, then generates and plots
 * a new route based on the values of the grid-draw form
 * and a specified pattern function
 */
var set_node_pattern = function(pattern_func){
    var start = parse_coords($('#grid_orig').val());
    var height = Number($('#grid_h').val());
    var width = Number($('#grid_w').val());
    var step = Number($('#grid_s').val());
    var coords = pattern_func(start,height,width,step);
    //if a parameter from above is falsy, exit out
    if(!(start && height && width && step && coords)) return;
    $('#path_nodes').empty();
    //for each coordinate returned by pattern func,
    //add a new path node containing that coordinate
    _.each(coords,function(coord){
        var new_node = get_node_template();
        new_node.find('.coord').val(coord.x + ', '+ coord.y);
        $('#path_nodes').append(new_node);
    });
    bind_actions_to_nodes();
    draw_path();
};

var save_route_csv= function(){
    var csv_string = [];
    $('.coord,.wait').each(function(){
        var suffix =$(this).hasClass('coord')?', ':'%0A';
        var val = $(this).val() || $(this).attr('placeholder');
        csv_string.push(val+suffix);
    });
    csv_string = csv_string.join('');
    $('#dl_link').attr('href','data:application/csv;charset=utf-8,'+csv_string);
};

var load_route_from_csv = function(file){
    var reader = new FileReader();
    reader.readAsText(file);
    reader.onloadend=function(){
        var result = reader.result;
        $('#path_nodes').empty();
        _.each(result.split('\n'),function(line){
            console.log(line);
            var vals = line.split(',');
            if(vals.length == 3){
                var new_node = get_node_template();
                new_node.find('.coord').val(vals[0] + ', '+ vals[1]);
                new_node.find('.wait').val(vals[2]);
                $('#path_nodes').append(new_node);
            }
        });
        draw_path();
        bind_actions_to_nodes();
        draw_path();
    }
};

var setup_online_demo = function(){
    $('#send').prop('disabled',true);
    $('#send').html("Arduino interface disabled in online demo");
    $('nav a').attr('href','#');
    var isChrome = !!window.chrome && !!window.chrome.webstore;
    if(!isChrome){
        $('#route_plot_h4').append(
            "<h5 style='color:red'>For best user experience, use Google Chrome.</h5>"
        );
    };
};

$(document).ready(function(){
    $('#path_nodes').sortable({update:update_nodenumbers});
    $('#add_node').click(function(){append_node()});
    $('#clear_nodes').click(function(){
        $('#path_nodes').empty();
        $('#no_nodes').show();
        append_node();
    });

    $('#load_nodes').change(function(){
        load_route_from_csv($(this).prop('files')[0]);
        //clear my value so the user can load the same file multiple times
        $(this).val(undefined);
    });

    //toggle the displayed drawing panel when the draw mode select changes
    $('#draw-mode').change(function(){
        $('.draw-menu').hide();
        $('#'+$(this).val()).show();
        $(window).trigger('resize');
    });

    //add a zig zag movement pattern when #add_grid is clicked
    $('#add_grid').click(function(){
        set_node_pattern(grid_pattern);
    });

    
    $('#dl_link').mousedown(function(){
        save_route_csv();
    });
    //set the max height of the path-node div and make it scrollable
    $(window).resize(function(){
        var plot_end = $('#path_plot').offset().top+$('#path_plot').height();
        var max_node_height = plot_end - $('#path_nodes').offset().top;
        $('#path_nodes').css('max-height',max_node_height);

    }).trigger('resize');
     
    if(external.restore_state){
        //before we leave the page, save form info
        $(window).bind("beforeunload", function(){
            save_nodes();
            save_forms();
            save_textareas();
        });
        restore_forms(); 
        restore_textareas();

        setTimeout(function(){$('#draw-mode').change()},500);
        $('#send').click(function(){
            var tot_delay = 1;
            $('.coord').each(function(){
                var coord = $(this);
                setTimeout(function(){
                    external.send_coords(coord.val());
                }, (tot_delay++)*500);
            });
        });

        restore_nodes(append_node);
    } else {
        setup_online_demo();
    }
});
