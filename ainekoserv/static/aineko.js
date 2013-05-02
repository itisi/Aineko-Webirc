/*jslint plusplus: true, browser: true, devel: true */
WEB_SOCKET_DEBUG = true;
var aineko = (function () {
    "use strict";
    var socket, aineko;
    function Aineko() {
    }
    aineko = new Aineko();
    $(function() {
        aineko.socket = io.connect('/aineko_serv');
    });
    return aineko;
}());
