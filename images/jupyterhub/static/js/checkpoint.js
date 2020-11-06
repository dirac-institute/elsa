require(["jquery", "jhapi"], function(
  $,
  JHAPI
) {
  "use strict";

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
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

  var server_stopped = false;
  // handle query arguments
  var checkpoint = getQueryVariable("checkpoint");
  var migrate_to = getQueryVariable("migrate_to");

  // function to call after stop
  var _after_stop = function() {
    $("#stop").hide();
    $("#start")
      .text("Start My Server")
      .attr("title", "Start your default server")
      .attr("disabled", false)
      .attr("href", base_url + "spawn/" + user)
      .off("click");
  }
  var after_stop = null;
  if (migrate_to) {
    var after_start = function() {
      window.location.replace("spawn/" + user);
    }
    // workflow:
    // _after_stop() 
    // wait_for_stop: make api call to user/<username> to check if the server still exists
    // - if it does, repeat the api call
    // - if it doesn't, start new server
    // start_server: make api call to user/<username>/server
    // - when the start call is accepted, forward user to hub/spawn
    after_stop = function() {
      _after_stop();
      if (checkpoint === null) {
        throw "Must checkpoint if intending to migrate";
      }
      // wait until server is stopped
      var _wait_for_stop = function() {
        var done = false;
        var next = true;
        // make api request one at a time and then sleep
        var do_request = function() {
          api.api_request(
            "users/" + user, {
              // when api call returns, check if there are still servers running
              success: function(data) { 
                console.log("servers:" + JSON.stringify(data['servers']));
                if (! $.isEmptyObject(data['servers'])) {
                  next = true;
                } else { 
                  next = false;
                }
                done = true;
              },
              // terminate on error
              error: function() {
                done = true;
                next = false;
              }
            }
          )
        }
        while (next) {
          do_request();
          while (!done) {
            sleep(100);
          }
          done = false;
        }
      }
      _wait_for_stop();

      // start the server with the requested size
      api.start_server(user, {
        "size": migrate_to,
        "error": function() {},
        "statusCode": {
          400: function() {
            console.log("got 400 code starting server")
            setTimeout(after_stop, 100);
          }
        }
      });
      // redirect user to spawn page
      setTimeout(after_start, 100);
    }
  } else {
    after_stop = _after_stop;
  }

  if (checkpoint === "true") {
    // default stop button functionality
    $("#stop").click(function() {
      $("#start")
        .attr("disabled", true)
        .attr("title", "Your server is stopping")
        .click(function() {
          return false;
        });
      api.stop_server(user, {
        'success': after_stop
      });
    });
    $("#stop").trigger("click");
  }
})
