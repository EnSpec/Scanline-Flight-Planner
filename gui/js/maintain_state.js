var save_forms = function(){
    $('[type=text],select').each(function(){
        external.save_state($(this).attr('id'),$(this).val());
    });
};

var save_textareas = function(){
    $('textarea').each(function(){
        external.save_state($(this).attr('id'),$(this).html());
    });
};


var restore_textareas = function(){
    $('textarea').each(function(){
        var text = $(this);
        external.restore_state(text.attr('id'), function(saved_val){
           text.html(saved_val); 
        });
    });
};

var save_nodes = function(){
    var node_data = []; 
    $('.coord, .wait').each(function(){
        node_data.push($(this).val());
    });
    external.save_state('nodes',node_data);
};

var restore_nodes = function(callback){
    //this is super slow, I don't know why yet
    external.restore_state('nodes',function(saved_nodes){
        if(!saved_nodes) return;
        _.each(saved_nodes,function(node,i){
            if(i%2==0){
                callback();
                $('.coord').last().val(node);
            } else {
                $('.wait').last().val(node);
            }
        });
    });
    $('.coord').last().trigger('change');
};
//restores every form on the page
var restore_forms = function(){
    $('[type=text],option').each(function(){
        var form = $(this);
        external.restore_state(form.attr('id'),
        function(saved_val,py_callback){
           if(saved_val) form.val(saved_val); 
        });
    });
};
