require(["jquery", "jhapi"], function(
  $,
  JHAPI
) {
  "use strict";  
  function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split('&');
    for (var i = 0; i < vars.length; i++) {
      var pair = vars[i].split('=');
      if (decodeURIComponent(pair[0]) == variable) {
        return decodeURIComponent(pair[1]);
      }
    }
    return null;
  }     
  var base_url = window.jhdata.base_url;
  var user = window.jhdata.user;
  var api = new JHAPI(base_url);

  // handle query arguments
  var checkpoint = getQueryVariable("checkpoint");
  var migrate_to = getQueryVariable("migrate_to");
  var redirect = getQueryVariable("next");
  
  function updateStatus(msg) {
    console.log(msg);
    $("#update").html(
      msg
    );
  }

  function waitUntilSoppedAndGoto(next) {
    function _wait() {
      updateStatus("waiting for server to stop...");
      api.api_request(
        "users/" + user,
        {
          "success": function(data) {
            var servers  = data['servers'];
            var no_servers = $.isEmptyObject(servers);
            if (no_servers) {
              next()
            } else {
              setTimeout(_wait, 100)
            }
          }
        }
      );
    }
    return _wait;
  }

  function redirectToSpawn() {
    var url = "spawn/" + user;
    if (redirect) {
      url += "?next=" + redirect;
    }
    updateStatus("redirecting to spawn page");
    window.location.replace(url);
  }

  function redirectoHome() {
    var url = "home";
    if (redirect) {
      url += "?next=" + redirect;
    }
    updateStatus("redirecting to home page");
    window.location.replace(url);
  }

  function startServerAndGoto(next) {
    return function() {
      updateStatus("starting server on " + migrate_to + "...");
      api.start_server(
        user, {
          data: JSON.stringify({
            "size" : migrate_to
          })
        }
      );
      // goto next instead of waiting for successful api call
      setTimeout(next, 500);
    }
  }

  function checkpointServerAndGoto(next) {
    return function() {
        updateStatus("checkpointing server...");
        api.stop_server(
          user, {
            "success": next
          }
        );
    };
  }

  if (checkpoint) {
    var todo = null;
    if (migrate_to) {
      todo = checkpointServerAndGoto(
        waitUntilSoppedAndGoto(
          startServerAndGoto(
            redirectToSpawn
          )
        )
      );
    } else {
      todo = checkpointServerAndGoto(
        redirectoHome
      );
    }
    todo();
  }
})
