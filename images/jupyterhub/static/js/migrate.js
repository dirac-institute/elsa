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
      updateStatus("Waiting for server to stop, please wait.");
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
    updateStatus("Starting a new server.");
    window.location.replace(url);
  }

  function redirectoHome() {
    var url = "home";
    if (redirect) {
      url += "?next=" + redirect;
    }
    updateStatus("Done.");
    window.location.replace(url);
  }

  function startServerAndGoto(next) {
    return function() {
      updateStatus("Starting server on " + migrate_to + ".");
      api.start_server(
        user, {
          data: JSON.stringify({
            // TODO: hit /hub/migrate/sizes and match to current size object?
            //       would include description and other info. Right now, slug is
            //       the only import data used during spawning
            "size" : {
              "slug" : migrate_to
            }
          })
        }
      );
      // goto next instead of waiting for successful api call
      setTimeout(next, 500);
    }
  }

  function checkpointServerAndGoto(next) {
    return function() {
        updateStatus("Checkpointing server, please wait.");
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

// **************************************************
// **                                              **
// **           countdown timer code               **
// **                                              **
// **************************************************


// Credit: Mateusz Rybczonec
// Based on https://css-tricks.com/how-to-create-an-animated-countdown-timer-with-html-css-and-javascript/

const FULL_DASH_ARRAY = 283;
const WARNING_THRESHOLD = 10;
const ALERT_THRESHOLD = 5;

const COLOR_CODES = {
  info: {
    color: "green"
  },
  warning: {
    color: "orange",
    threshold: WARNING_THRESHOLD
  },
  alert: {
    color: "red",
    threshold: ALERT_THRESHOLD
  }
};

const TIME_LIMIT = 30;
let timePassed = 0;
let timeLeft = TIME_LIMIT;
let timerInterval = null;
let remainingPathColor = COLOR_CODES.info.color;

document.getElementById("app").innerHTML = `
<div class="base-timer">
  <svg class="base-timer__svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g class="base-timer__circle">
      <circle class="base-timer__path-elapsed" cx="50" cy="50" r="45"></circle>
      <path
        id="base-timer-path-remaining"
        stroke-dasharray="283"
        class="base-timer__path-remaining ${remainingPathColor}"
        d="
          M 50, 50
          m -45, 0
          a 45,45 0 1,0 90,0
          a 45,45 0 1,0 -90,0
        "
      ></path>
    </g>
  </svg>
  <span id="base-timer-label" class="base-timer__label">${formatTime(
    timeLeft
  )}</span>
</div>
`;

startTimer();

function onTimesUp() {
  clearInterval(timerInterval);
}

function startTimer() {
  timerInterval = setInterval(() => {
    timePassed = timePassed += 1;
    timeLeft = TIME_LIMIT - timePassed;
    document.getElementById("base-timer-label").innerHTML = formatTime(
      timeLeft
    );
    setCircleDasharray();
    setRemainingPathColor(timeLeft);

    if (timeLeft === 0) {
      onTimesUp();
    }
  }, 1000);
}

function formatTime(time) {
  const minutes = Math.floor(time / 60);
  let seconds = time % 60;

  if (seconds < 10) {
    seconds = `0${seconds}`;
  }

  return `${minutes}:${seconds}`;
}

function setRemainingPathColor(timeLeft) {
  const { alert, warning, info } = COLOR_CODES;
  if (timeLeft <= alert.threshold) {
    document
      .getElementById("base-timer-path-remaining")
      .classList.remove(warning.color);
    document
      .getElementById("base-timer-path-remaining")
      .classList.add(alert.color);
  } else if (timeLeft <= warning.threshold) {
    document
      .getElementById("base-timer-path-remaining")
      .classList.remove(info.color);
    document
      .getElementById("base-timer-path-remaining")
      .classList.add(warning.color);
  }
}

function calculateTimeFraction() {
  const rawTimeFraction = timeLeft / TIME_LIMIT;
  return rawTimeFraction - (1 / TIME_LIMIT) * (1 - rawTimeFraction);
}

function setCircleDasharray() {
  const circleDasharray = `${(
    calculateTimeFraction() * FULL_DASH_ARRAY
  ).toFixed(0)} 283`;
  document
    .getElementById("base-timer-path-remaining")
    .setAttribute("stroke-dasharray", circleDasharray);
}
