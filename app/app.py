from flask import Flask, render_template, request, redirect
import json
import urllib.request
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
import os


app  = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    input_data = request.form
    for key in input_data:
        if input_data[key] is None or input_data[key] == '':
            return redirect('/')
    data = {
        "input_data": {
            "columns": list(input_data.keys()),
            "index": [1],
            "data": [[float(x) for x in list(input_data.values())]]
            }
    }
    body = bytes(json.dumps(data), 'utf-8')
    
    load_dotenv()
    
    url = os.getenv("MODEL_END_POINT")

    keyVaultName = os.getenv("KEY_VAULT_NAME")
    KVUri = f"https://{keyVaultName}.vault.azure.net"

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KVUri, credential=credential)
        secretName = "diabetes-app-key"
        api_key = client.get_secret(secretName)
    except Exception as e:
        print("Error: ", e)

    headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key.value), 'azureml-model-deployment': 'diabetes-model-deployment' }

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        result_decoded = result.decode("utf8", 'ignore')
        print("result_decoded: ", type(result_decoded))
        if result_decoded == '[0]':
            result = 'No Diabetes'
        elif result_decoded == '[1]':
            result = 'Diabetes'
        else:
            result = 'Error'
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the request ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))


    return render_template('result.html', result=result)
