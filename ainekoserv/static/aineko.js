/*jslint plusplus: true, browser: true, devel: true */
WEB_SOCKET_DEBUG = true;
var aineko = (function () {
    "use strict";
    var socket, aineko;
    $.fn.channel = function() {
        var channelID = parseInt($(this).attr('data-channel'), 10);
        return aineko.channels[channelID];
    };
    function Channel(channel) {
        if (channel === undefined) {
            channel = {};
        }
        this.id = channel.id || 'anon' + $('.channelBtn').length;
        this.name = channel.name || null;
        this.users = channel.users || [];
        this.messageBody = $('<div class="channel" data-channel="' + channel.id + '" id=channel' + channel.id  + '"></div>');
        $('#messages').append(this.messageBody);
        this.link = $('<div data-channel="' + channel.id + '" id="channelLink_' + channel.id + '" class="channelBtn">' + channel.name + '</div>');
        $('#channels').append(this.link);
    }

    Channel.prototype.printMessage = function (message, options) {
        var date, dateString, messageClasses, classesString, tag;
        if (options === undefined) {
            options = {};
        }
        date = new Date().toLocaleString();
        dateString = '<span class="timestamp">[' + date + ']</span> ';
        messageClasses = ['message'];
        if (this.id === -1) {
            messageClasses.push('servermessage');
        }
        if (options.error) {
            messageClasses.push('errormessage');
        }
        classesString = messageClasses.join(' ');
        message = $('<span></span>').text(message);
        this.messageBody.append('<div class="' + classesString + '">' + dateString + message.html() +'</div>');
    }

    Channel.prototype.activate = function () {
        if (aineko.curchannel) {
            aineko.curchannel.deactivate();
        }
        this.link.addClass('activechannel');
        this.messageBody.show();
        aineko.curchannel = this;
    }
    Channel.prototype.deactivate = function() {
        this.link.removeClass('activechannel');
        this.messageBody.hide();
    }

    function Aineko() {
        this.chathistory = [];
        this.chatindex = 0;
        this.channels = {};
        this.curchannel = null;
        this.channels[-1] = new Channel({id: -1, name: 'server'});
    }
    Aineko.prototype.nick = function(name) {
        var nickClasses = ['nick'];
        if (name === aineko.name) {
            nickClasses.push('isme');
        }
        return '<span class="' + nickClasses.join(' ') +'">&lt;' + name + '&gt;</span>';
    }

    function errormessage(message) {
        aineko.channels[-1].printMessage(message, {error: true})
    }

    $(function() {
        aineko = new Aineko();
        aineko.channels[-1].activate();
        var socket;
        socket = io.connect('/aineko_serv');
        socket.on('initvars', function(vars) {
            for (var key in vars) {
                if (vars.hasOwnProperty(key)) {
                    aineko[key] = vars[key];
                }
            }
        });
        socket.on('privmsg', function(channel, name, message) {
            var channel = aineko.channels[channel];
            channel.printMessage(aineko.nick(name) + message);
        });
        socket.on('servermessage', function(message) {
            aineko.channels[-1].printMessage(message);
        });
        socket.on('error', function(type, message) {
            if (type === 'method_access_denied') {
                errormessage('<b>Access Denied: </b>' + message);
            }
        });
        socket.on('join', function(user, channel) {
            if (user == aineko.name) {
                channel = new Channel(channel);
                aineko.channels[channel.id] = channel;
                channel.activate();
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
                if (aineko.curchannel && aineko.curchannel.id > 0) {
                    socket.emit("privmsg", aineko.curchannel.id, val);
                } else {
                    socket.emit("global", val);
                }
            }
            $('#chatinput').val('');
        });
        $('#channels').on('click', '.channelBtn', function() {
            $(this).channel().activate();
        });

    });
    return aineko;
}());
