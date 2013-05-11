/*jslint plusplus: true, browser: true, devel: true */
WEB_SOCKET_DEBUG = true;
var aineko = (function () {
    "use strict";
    var socket, aineko;
    function Channel(name) {
        this.name = name;
        this.users = {};
    }
    function Aineko() {
        this.chathistory = [];
        this.chatindex = 0;
        this.channels = {};
    }
    function activateChannel(channel) {
        var cLink = $(document.getElementById(channel)); //ids have # signs so pass jQuery the tag
        var channel = $(document.getElementById(channel));
        cLink.addClass('active');
    }
    function errormessage(message) {
        $('#servermessages').append('<div class="errormessage">' + message + '</div>');
    }
    aineko = new Aineko();
    $(function() {
        var socket;
        socket = io.connect('/aineko_serv');
        socket.on('initvars', function(vars) {
            for (var key in vars) {
                if (vars.hasOwnProperty(key)) {
                    aineko[key] = vars[key];
                }
            }
        });
        socket.on('servermessage', function(message) {
            $('#servermessages').append('<div class="message">' + message + '</div>');
        });
        socket.on('error', function(type, message) {
            if (type === 'method_access_denied') {
                errormessage('<b>Access Denied: </b>' + message);
            }
        });
        socket.on('join', function(user, channel) {            
            if (user == aineko.name) {
                $('#messages').append('<div class="channel" id="' + channel + '"></div>');
                aineko.channels[channel] = new Channel(channel);
                $('#channels').append('<div id="' + channel + '" class="channelBtn">' + channel + '</div>');
            } else {
            }
            activateChannel(channel);
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
