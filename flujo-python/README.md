## BrightPath - Server-side only usage (via Python)
Path: /flujo-python

### Technical details
* Azure AI services:
  * Speech Synthesizer & Recognizer.
  * Text analytics (Keywords) & Text Translation.
  * Conversational Language Understanding.
  * Azure OpenAI.
  * Bing search (Video)
* Langchain / OpenAI.
* Pyaudio.

### How to start
* Python `==3.12` is required.
* To obtain the repository and create the virtual environment.
    ```
    git clone [repository-url]
    cd brighpath-hackaton-microsoft/flujo-python
    python -m venv venv
    ```
* To activate virtual environment.
    ```
    # Mac/Linux commands
    source venv/bin/activate

    # Windows commands (Powershell & CMD)
    venv/Scripts/Activate.ps1
    venv/Scripts/Activate.bat
    ```
* Then dependencies should be installed.
    ```
    pip install -r requirements.txt
    ```
* Create environment variables from the copy and modify them.
    ```
    cp .copy.env .env
    ```

### Environment variables

For all resources created in Azure, the region used was "eastus"
Except, for the language resource (CLU), "eastus2" was used.

Variables obtained from an Azure AI Service (multi-service account) resource.
- AZUREAI_MULTISERVICE_KEY
- AZUREAI_MULTISERVICE_ENDPOINT
- AZUREAI_MULTISERVICE_REGION

Variables obtained when creating a language resource from https://language.cognitive.azure.com/:
A Conversational Language Understanding project must be created, and the name goes in AZUREAI_CLU_PROJECT_NAME.
Two intents "get_note" and "infer_text" must be generated.
Training was conducted with 50 Utterances in English (US), details in the PPT (slide 10).
Training is performed, followed by deployment, and the deployment name goes in AZUREAI_CLU_DEPLOYMENT_NAME.
The key and endpoint are obtained from the Language resource created through the Azure Portal.
- AZUREAI_CLU_KEY
- AZUREAI_CLU_ENDPOINT
- AZUREAI_CLU_PROJECT_NAME
- AZUREAI_CLU_DEPLOYMENT_NAME

Variables obtained from an Azure OpenAI resource:
After creating the resource, go to Azure OpenAI Studio.
Navigate to the Deployments section and create a new deployment with the model "gpt-35-turbo" and a name.
The name is placed in AZURE_OPENAI_DEPLOY, and the rest is obtained directly from the Azure OpenAI resource.
- AZURE_OPENAI_API_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_DEPLOY

Variables obtained from a Bing Search resource.
- BING_API_ENDPOINT
- BING_API_KEY

### Application's usage

Two files corresponding to the text to be read and the language the user desires must be modified.
They are located at:

- Modify language in static/config.json
- Modify text in static/text.txt

Finally, execute with:
```
python main.py
```

Remember: This experience is part of the "flujo-python" folder.