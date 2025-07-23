// The JS file to work with this API trigger for Azure DevOps Pipeline
const pat = "<pat>";
const azureOrg = "daslearning";
const azDevOpsProj = "daslearningProject";

let pipelineId = "11";

function base64Encode(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const encodedData = btoa(data);
  return encodedData;
}

function sendPOSTRequest(url, data) {
  const xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.setRequestHeader('Authorization', 'Basic ' + pat);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.setRequestHeader('Cache-Control', 'no-cache');

  xhr.onload = function() {
    if (xhr.status === 200) {
      const response = JSON.parse(xhr.responseText);
      let opText = `Your request to create a bucket has been queued with RUN ID: ${response.id}, please note this ID for checking the status of for future referene. You can check the status from the button given on the console.`;
      alert(opText);
      const form = document.getElementById('bucketForm');
      form.querySelector('input[type="text"]').value = "";
      form.disabled = false;
    }
    else {
      console.error('Error:', xhr.status, xhr.statusText);
      alert("Some problem occurred, please try again");
      const form = document.getElementById('bucketForm');
      form.querySelector('input[type="text"]').value = "";
      form.disabled = false;
    }
  };
  xhr.send(JSON.stringify(data));
}

function apiCall() {
  // Get references to the form elements
  const form = document.getElementById('bucketForm');
  const textInput = form.querySelector('input[type="text"]');
  const selectDropdown = form.querySelector('select');

  // Extract the values from the form elements
  const bucketName = textInput.value;
  const region = selectDropdown.value;

  if(bucketName.length >= 1){
    const jsonBody = {
      resources: {
        repositories: {
          self: {
            refName: "refs/heads/master"
          }
        }
      },
      variables: {
        bucketName: {
          value: bucketName
        },
        bucketRegion: {
          value: region
        }
      }
    };

    form.disabled = true;
    const url = `https://dev.azure.com/${azureOrg}/${azDevOpsProj}/_apis/pipelines/${pipelineId}/runs?api-version=7.1-preview.1`;
    sendPOSTRequest(url, jsonBody);
  }
  else{
    alert("Bucket name cannot be empty!");
  }
}

function checkRunId() {
  // Get references to the form elements
  const form = document.getElementById('checkRunForm');
  const runId = form.querySelector('input[type="text"]').value;
  const paragraph = document.getElementById("runStatus");
  paragraph.textContent = "Checking..";
  if(runId.length >= 1){
    const url = `https://dev.azure.com/${azureOrg}/${azDevOpsProj}/_apis/build/builds/${runId}?api-version=7.1-preview.1`;
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.setRequestHeader('Authorization', 'Basic ' + pat);
    xhr.setRequestHeader('Cache-Control', 'no-cache');
    xhr.onload = function() {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        let runStatus = response.status;
        let opText = `Status for your run id ${runId} is: ${runStatus}. You can check status of another run from here.`
        const paragraph = document.getElementById("runStatus");
        paragraph.textContent = opText;
        paragraph.classList.remove("visually-hidden");
      }
      else {
        console.error('Error:', xhr.status, xhr.statusText);
        alert("Some error occurred, please try again");
      }
    };
    xhr.send();
  }
  else{
    alert("Run ID cannot be empty!");
  }
}
