/* Script for index.html, contains functions that pass form data into
 * Python controller, which then parses it into serial data for arduino
 */
var val_or_placeholder = function(elem){
    return elem.val() || elem.attr('placeholder');
};
var write_to_out = function(py_text,py_callback){
    if(py_text != KEY_CODES.EMPTY_BUFFSTR){
        $('#outdiv').html($('#outdiv').html()+py_text+'\n');
        //might eventually stop working
            if(!$('#outdiv').is(':focus'))
                $('#outdiv').scrollTop(9999999);
    }
};
var update_tty_options = function(reconnect){
    external.get_tty_options(function(py_data){
        $('#tty>option').each(function(){$(this).remove()});
        _.each(py_data,function(item){
            $('#tty').append('<option>'+item+'</option>');
        });
        if(reconnect) $('#tty').trigger('change'); 
    });
}
$(document).ready(function(){
    setInterval(function(){
        //send a no-op byte to the arduino so SerialInts knows it's connected
        if(document.hasFocus()) external.send('n',false);
        //poll the arduino's serial port for a response once every .5 seconds
        //TODO: Move this to the python module - it will be a lot of work
        external.echo(write_to_out);
    },500);

    external.set_serial_err(_.throttle(function(err_msg,py_callback){
        //assume that the error comes from a disconnect
        //TODO make this more intelligent
        $('#connected').html('Connected to: None');
        write_to_out('ERROR: ' + err_msg);
    },3000));

    $('#tty').change(function(){
        external.set_serial_port($(this).val());
        $('#connected').html('Connected to: '+($(this).val()||'None'));
    });


    //Set up 'Scan' button to scan devices that probably match an Arduino
    $('#scan').click(function(){
        update_tty_options(true);
    });
    update_tty_options(true);
    
    //Clicking 'Send' or pressing enter in form send a series of coordinates
    $('#send').click(function(){
        external.send_coords(val_or_placeholder($('#instr')));
    });

    $('#instr').keydown(function(event){
        if(event.keyCode == 13) $('#send').trigger('click');
    });


    //Clicking 'Set Delay' or pressing enter in form sets delay
    $('#set_delay').click(function(){
        external.send_delay(val_or_placeholder($('#delay_val')));
    });
    $('#delay_val').keydown(function(event){
        if(event.keyCode == 13) $('#set_delay').trigger('click');
    });
    
    $('#stop').click(function(){
        external.send('s',false);
    });

    $('#go_home').click(function(){
        $('#stop').trigger('click');
        setTimeout(function(){external.send_coords('0,0');},100);
    });
    
    $('#clear_out').click(function(){
        $('#outdiv').html('');
    });
    

    $(window).bind("beforeunload", function(){
        save_forms();
        save_textareas();
    });
    restore_forms(); 
    restore_textareas();

    $('#up').click(function(){ external.send_coords('-5,0',3); });
    $('#dn').click(function(){ external.send_coords('5,0',3); });
    $('#left').click(function(){ external.send_coords('0,-5',3); });
    $('#right').click(function(){ external.send_coords('0,5',3); });
    $(window).keydown(function(event){
        //don't trigger key-based controls if the user is typing
        if($('[type=text], textarea').is(':focus'))return;
        switch(event.key){
            case "ArrowUp":
                $('#up').addClass('active').trigger('click');
                setTimeout(function(){$('#up').removeClass('active')},500);
                break;
            case "ArrowDown":
                $('#dn').addClass('active').trigger('click');
                setTimeout(function(){$('#dn').removeClass('active')},500);
                break;
            case "ArrowLeft":
                $('#left').addClass('active').trigger('click');
                setTimeout(function(){$('#left').removeClass('active')},500);
                break;
            case "ArrowRight":
                $('#right').addClass('active').trigger('click');
                setTimeout(function(){$('#right').removeClass('active')},500);
                break;
        }
    });
});
