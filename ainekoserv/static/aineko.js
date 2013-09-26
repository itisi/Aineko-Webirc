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
        this.topic = channel.topic || '';
        this.id = channel.id || 'anon' + $('.channelBtn').length;
        this.name = channel.name || null;
        this.users = channel.users || [];
        this.messageBody = $('<div class="channel" data-channel="' + channel.id + '" id=channel' + channel.id  + '"></div>');
        $('#messages').append(this.messageBody);
        this.link = $('<div data-channel="' + channel.id + '" id="channelLink_' + channel.id + '" class="channelBtn">' + 
                '<span class="hotkey">' + ($('#channels').children().length + 1) + '.</span>' + channel.name + '<i class="channelAlert icon-exclamation"></i><div class="clear"></div></div>');
        $('#channels').append(this.link);
    }

    Channel.prototype.printMessage = function (message, options) {
        var date, dateString, messageClasses, classesString, tag;
        if (options === undefined) {
            options = {};
        }
        messageClasses = ['message'];
        if (this.id === -1) {
            messageClasses.push('servermessage');
        }
        if (options.error) {
            messageClasses.push('errormessage');
        }
        classesString = messageClasses.join(' ');
        dateString = aineko.timestamp();
        if (aineko.curchannel !== this) {
            this.link.addClass('attention');
        }
        this.messageBody.append('<div class="' + classesString + '">' + dateString + message +'</div>');
    }

    Channel.prototype.activate = function () {
        if (aineko.curchannel) {
            aineko.curchannel.deactivate();
        }
        this.link.addClass('activechannel').removeClass('attention');
        this.messageBody.show();
        aineko.curchannel = this;
        $('#topic').text(this.topic);
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
    };

    Aineko.prototype.timestamp = function() {
        var date, hour, minute;
        date = new Date();
        minute = date.getMinutes();
        if (minute < 10) {
            minute = '0' + minute;
        }
        hour = date.getHours()
        if (hour < 10) {
            hour = '0' + hour;
        }
        return '<span class="timestamp">[' + hour + ':' + minute + ']</span> ';
    };

    Aineko.prototype.advanceChannel = function() {
        var channels = $('#channels').children();
        channels.each(function(i) {
            if ($(this).hasClass('activechannel')) {
                $(channels[(i + 1) % channels.length]).channel().activate();
                return false;
            }            
        });
    };

    Aineko.prototype.hotkeys = {
        'J': '#joinChannel',
        192: Aineko.prototype.advanceChannel //actually alt+`
    };

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
            message = $('<span>').text(message).html();
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

        socket.on('errormessage', errormessage);

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
        $('#joinChannel').click(function () {
            $('html').removeClass('showhotkeys'); //prompt keeps alt onkeyup from firing
            var channel = prompt('Please enter the channel name.');
            if (channel) {
                socket.emit('join', channel);
                $('#chatinput').focus();
            }
        });
        $('body').keydown(function(e) {
            var channelindex, channels, hotkey;
            if (e.keyCode === 18) { //alt
                e.preventDefault();
                $('html').addClass('showhotkeys');
            }
            if (e.keyCode >= 49 && e.keyCode <= 57 && e.altKey) { //switch channels with alt 1-9
                e.preventDefault();
                channelindex = e.keyCode - 49;
                channels = $('.channel');
                if (channels.length > channelindex) {
                    $(channels[channelindex]).channel().activate();
                }
            } else if(e.altKey) {
                hotkey = String.fromCharCode(e.keyCode);
                if (aineko.hotkeys[hotkey] || aineko.hotkeys[e.keyCode]) {
                    if (!aineko.hotkeys[hotkey]) {
                        hotkey = e.keyCode;
                    }
                    if (typeof aineko.hotkeys[hotkey] === 'function') {
                        aineko.hotkeys[hotkey]();
                    } else {
                        $(aineko.hotkeys[hotkey]).click();
                    }
                }
            }
        });
        $('body').keyup(function(e) {
            if (e.keyCode === 18) {
                $('html').removeClass('showhotkeys');
            }
        });
    });
    return aineko;
}());
