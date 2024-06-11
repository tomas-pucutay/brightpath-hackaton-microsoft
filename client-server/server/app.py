import ast
import json
import os
import random
import threading

from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from langchain_openai import AzureChatOpenAI

from classes.common import AudioPlayer, TextHandler, TextExtractor
from classes.search import VideoComplement
from classes.speech import SpeechSynthesizer, SpeechRecognizer
from classes.text import CLU, Translator, KeywordExtractor
from utils.ssml import make_ssml

# All the constants
is_playing = False
enable_space = False
enable_control = False

text = ""
FILE_NAME = "static/output.wav"
LANG_PATH = "static/config.json"
help_intro = "Bienvenido a la lectura interactiva. Puedes usar 3 teclas: Barra espaciadora, Control y Enter. Con la barra espaciadora detienes la lectura y escucha atentamente para guardar notas del texto. Con el Control puedes reanudar la lectura. Y con Enter puedes finalizar y escuchar el análisis completo de la lectura. Comenzamos"
help_note_1 = "La cantidad total de notas es "
help_note_2 = "Te leeré hasta 3 notas de ejemplo y lo demás lo guardaré"
help_note_3 = "Nota "
help_video_1 = "He encontrado 3 videos complementarios que te pueden ayudar"
help_video_2 = "Video "

with open(LANG_PATH, 'r') as config_file:
    config = json.load(config_file)

lang_str = config.get('lang')
lang = ast.literal_eval(lang_str)

# All the env variables
subscription = os.getenv("AZUREAI_MULTISERVICE_KEY")
region = os.getenv("AZUREAI_MULTISERVICE_REGION")
endpoint = os.getenv("AZUREAI_MULTISERVICE_ENDPOINT")
clu_endpoint = os.getenv("AZUREAI_CLU_ENDPOINT")
clu_subscription = os.getenv("AZUREAI_CLU_KEY")
clu_project_name = os.getenv("AZUREAI_CLU_PROJECT_NAME")
clu_deploy_name = os.getenv("AZUREAI_CLU_DEPLOYMENT_NAME")
azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_deploy = os.getenv("AZURE_OPENAI_DEPLOY")
bing_api_key = os.getenv("BING_API_KEY")
bing_endpoint = os.getenv("BING_API_ENDPOINT") + "v7.0/videos/search"

# All the credentials
azure_speech_config = speechsdk.SpeechConfig(subscription, region)
azure_text_key_credential = AzureKeyCredential(subscription)
azure_clu_key_credential = AzureKeyCredential(clu_subscription)

# All the tools from MSFT are here
synthesizer = SpeechSynthesizer(azure_speech_config)
recognizer = SpeechRecognizer(azure_speech_config)
translator = Translator(endpoint, azure_text_key_credential, region)
keyword_extractor = KeywordExtractor(endpoint, azure_text_key_credential)
clu = CLU(clu_endpoint, azure_clu_key_credential, clu_project_name, clu_deploy_name)

llm = AzureChatOpenAI(
        azure_endpoint = azure_openai_endpoint,
        openai_api_key = azure_openai_api_key,
        openai_api_version = "2024-02-01",
        deployment_name = azure_openai_deploy,
        temperature = 0.5,
        n = 1
    )

# Changed values to desired language
lang_key = list(lang.keys())[0]
lang_val = list(lang.values())[0]
help_intro = translator.translate(help_intro, lang_val)
help_note_1 = translator.translate(help_note_1, lang_val)
help_note_2 = translator.translate(help_note_2, lang_val)
help_note_3 = translator.translate(help_note_3, lang_val)
help_video_1 = translator.translate(help_video_1, lang_val)
help_video_2 = translator.translate(help_video_2, lang_val)

# Supportive tools
player = None
text_handler = None
extractor = TextExtractor(llm, translator, lang_val)
video_complement = VideoComplement(bing_api_key, bing_endpoint, translator, lang_key, lang_val)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_audio')
def create_audio(data):
    global text, text_handler, player
    text = data.get('text')
    text = translator.translate(text, lang_val)
    text_handler = TextHandler(text, translator, lang_key, lang_val)
    synthesizer.synthesize_to_file(make_ssml(text, lang_key), FILE_NAME)
    player = AudioPlayer(FILE_NAME)
    emit('audio_created', {'message': 'Audio created'})

@socketio.on('start_audio')
def start_audio(data):
    global is_playing, enable_space, enable_control

    if not is_playing:
        is_playing = data.get('isPlaying')
        enable_space = data.get('enableSpace')
        enable_control = data.get('enableControl')

        synthesizer.speak_text(make_ssml(help_intro, lang_key))
        text_handler.set_total_bytes(player.wf.getnframes() * player.wf.getsampwidth())
        threading.Thread(target=player.play_audio, args=(text_handler,), daemon=True).start()
        emit('audio_started', {'message': 'Audio started'})

@socketio.on('space_pressed')
def space_pressed():
    global enable_space, enable_control
    if is_playing:
        if enable_space:
            print("Space pressed")
            enable_space = False
            enable_control = True

            player.set_pause(True, text_handler, translator, synthesizer, extractor, recognizer, clu)
            print(is_playing)

@socketio.on('control_pressed')
def control_pressed():
    global enable_space, enable_control
    if is_playing:
        if enable_control:
            print("Control pressed")
            enable_control = False
            enable_space = True

            player.set_pause(False, text_handler, translator, synthesizer, extractor, recognizer, clu)
            print(is_playing)

@socketio.on('enter_pressed')
def enter_pressed():
    global is_playing, enable_space, enable_control
    if is_playing:
        print("Enter pressed")
        is_playing = False
        enable_control = False
        enable_space = False

        clu.close()

        notes = text_handler.get_notes()

        if len(notes) >= 3:
            notes_sample = random.sample(notes, 3)
        else:
            notes_sample = notes

        synthesizer.speak_text(make_ssml(help_note_1 + str(len(notes)), lang_key))
        synthesizer.speak_text(make_ssml(help_note_2, lang_key))

        for (i, note) in enumerate(notes_sample):
            synthesizer.speak_text(make_ssml(help_note_3 + str(i + 1) + " " + note, lang_key))
        keywords = keyword_extractor.extract_notes_keywords(notes)
        print(f"Notes list: {notes}")
        print(f"Top 3 keywords: {keywords}")

        videos = video_complement.bing_search(keywords)
        synthesizer.speak_text(make_ssml(help_video_1, lang_key))
        for (i, video) in enumerate(videos):
            synthesizer.speak_text(make_ssml(help_video_2 + str(i + 1) + " " + video['name'], lang_key))
        print(f"Videos: {videos}")

if __name__ == '__main__':
    socketio.run(app)
