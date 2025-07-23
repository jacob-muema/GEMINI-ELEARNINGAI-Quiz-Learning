// JavaScript to controll the chat
// From: YouTube/DIY-Try
// Author: Somnath Das

let chatIncoming;
let chatOutgoing;
let inChatCount = 0;
let outChatCount = 0;
var socket;

var gateway = `ws://${window.location.hostname}/ws`;
socket = new WebSocket(gateway);
socket.onopen = () => {
  console.log('WebSocket connection opened');
};
socket.onclose = () => {
  console.log('WebSocket connection closed');
};
socket.onmessage = (event) => {
  chatIncoming = event.data;
  // Then add your data into the msg div
  updateMsg("in", chatIncoming);
};

document.addEventListener('DOMContentLoaded', () => {
  // Your code here
  document.getElementById("sendBtn").addEventListener("click", function(event) {
    sendMessage();
  });
});

function sendMessage() {
  const messageBox = document.getElementById("msgInput");
  const message = messageBox.value;
  const msgLen = message.length;
  if(msgLen <= 0){
    alert("Please input your message and then click Send");
    return;
  }
  socket.send(message.trim());
  messageBox.value = "";
  updateMsg("out", message);
}

function updateMsg(msgType, msgToAdd) {
  const targetElement = document.getElementById("scrollable-content");
  if(msgType == "in"){
    const sourceElement = document.getElementById("inChat");
    const clonedElement = sourceElement.cloneNode(true);
    inChatCount++;
    clonedElement.id = `in-msg-${inChatCount}`;
    const newParagraph = document.createElement("p");
    newParagraph.textContent = msgToAdd;
    newParagraph.classList.add("w3-left");
    clonedElement.appendChild(newParagraph);
    clonedElement.classList.remove("w3-hide");
    targetElement.appendChild(clonedElement);
  }
  else if (msgType == "out"){
    const sourceElement = document.getElementById("outChat");
    const clonedElement = sourceElement.cloneNode(true);
    outChatCount++;
    clonedElement.id = `in-msg-${outChatCount}`;
    const newParagraph = document.createElement("p");
    newParagraph.textContent = msgToAdd;
    newParagraph.classList.add("w3-right");
    clonedElement.appendChild(newParagraph);
    clonedElement.classList.remove("w3-hide");
    targetElement.appendChild(clonedElement);
  }
  targetElement.scrollTop = targetElement.scrollHeight;
}
