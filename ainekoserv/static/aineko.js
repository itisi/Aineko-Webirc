/*jslint plusplus: true, browser: true, devel: true */
WEB_SOCKET_DEBUG = true;
var aineko = (function () {
    "use strict";
    var socket, aineko;
    function Aineko() {
        this.chathistory = [];
        this.chatindex = 0;
    }
    function errormessage(message) {
        $('#servermessages').append('<div class="errormessage">' + message + '</div>');
    }
    aineko = new Aineko();
    $(function() {
        var socket;
        socket = io.connect('/aineko_serv');
        socket.on('servermessage', function(message) {
            $('#servermessages').append('<div class="message">' + message + '</div>');
        });
        socket.on('join', function(channel) {
            $('#messages').append('<div class="channel" id="channel"></div>');
            $(channel).append('Joined channel ' + channel);
        });
        socket.on('error', function(type, message) {
            if (type === 'method_access_denied') {
                errormessage('<b>Access Denied: </b>' + message);
            }
        });

        $('#chatform').submit(function(e) {
            var val, parts, func;
            e.preventDefault();
            val = $("#chatinput").val();
            aineko.chathistory.push(val);
            aineko.chatindex = 0;
            if (val.length > 1 && val[0] === '/') {
                parts = val.split(" ");
                func = socket.emit;
                parts[0] = parts[0].substr(1);
                func.apply(socket, parts);
            } else if (val !== '') {
                if (aineko.curchannel) {
                    socket.emit("privmsg", aineko.curchannel, val);
                } else {
                    socket.emit("global", val);
                }
            }
            $('#chatinput').val('');
        });
    });
    return aineko;
}());
