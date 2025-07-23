// The Front End Controls JS
var socket;
var msgIncoming;

var gateway = `ws://${window.location.hostname}/ws`;
socket = new WebSocket(gateway);
socket.onopen = () => {
  console.log('WebSocket connection opened');
};
socket.onclose = () => {
  console.log('WebSocket connection closed');
};
// Not a requirement now
socket.onmessage = (event) => {
  msgIncoming = event.data;
  console.log(msgIncoming);
};

document.addEventListener('DOMContentLoaded', () => {
  // Functions on clicks
  document.getElementById("highBeam").addEventListener("click", function(event) {
    sendMessage("hbeam");
  });

  document.getElementById("headLampOff").addEventListener("click", function(event) {
    sendMessage("floff");
  });

  document.getElementById("lowBeam").addEventListener("click", function(event) {
    sendMessage("lbeam");
  });

  document.getElementById("leftIndicator").addEventListener("click", function(event) {
    sendMessage("lftind");
  });

  document.getElementById("parkIndicator").addEventListener("click", function(event) {
    sendMessage("park");
  });

  document.getElementById("indicatorOff").addEventListener("click", function(event) {
    sendMessage("indoff");
  });

  document.getElementById("rightIndicator").addEventListener("click", function(event) {
    sendMessage("rgtind");
  });

  document.getElementById("leftDir").addEventListener("click", function(event) {
    sendMessage("left");
  });

  document.getElementById("fwdDir").addEventListener("click", function(event) {
    sendMessage("fwd");
  });

  document.getElementById("backDir").addEventListener("click", function(event) {
    sendMessage("bck");
  });

  document.getElementById("rightDir").addEventListener("click", function(event) {
    sendMessage("right");
  });

  document.getElementById("speed1").addEventListener("click", function(event) {
    sendMessage("speed1");
  });

  document.getElementById("speed2").addEventListener("click", function(event) {
    sendMessage("speed2");
  });

  document.getElementById("speed3").addEventListener("click", function(event) {
    sendMessage("speed3");
  });

  document.getElementById("speed4").addEventListener("click", function(event) {
    sendMessage("speed4");
  });

  document.getElementById("carStop").addEventListener("click", function(event) {
    sendMessage("stop");
  });

});

function sendMessage(msgTxt) {
  // Send the msg to control car operations
  socket.send(msgTxt.trim());
}
