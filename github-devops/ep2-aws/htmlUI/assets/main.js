// The JS file to work with this API trigger for Azure DevOps Pipeline
const pat = "<pat>";
const gitOwner = "daslearning-org";
const repoName = "devops-youtube";

const pipelineId = "gh-act-ep2.yml";

function sendPOSTRequest(url, data) {
  const xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.setRequestHeader('Authorization', 'Bearer ' + pat);
  xhr.setRequestHeader('Accept', 'application/vnd.github+json');
  xhr.setRequestHeader('X-GitHub-Api-Version', '2022-11-28');

  xhr.onload = function() {
    if (xhr.status === 204) {
      let opText = `Your request to create a bucket has been queued.`;
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
  const textInput = document.getElementById('bucketName');
  const selectDropdown = document.getElementById('region');

  // Extract the values from the form elements
  const bucketName = textInput.value;
  const region = selectDropdown.value;

  if(bucketName.length >= 1){
    const jsonBody = {
      ref: "main", // your branch
      inputs: {
        bucket: bucketName,
        region: region
      }
    };

    form.disabled = true;
    const url = `https://api.github.com/repos/${gitOwner}/${repoName}/actions/workflows/${pipelineId}/dispatches`;
    sendPOSTRequest(url, jsonBody);
  }
  else{
    alert("Bucket name cannot be empty!");
  }
}
