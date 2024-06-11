import ast
import json
import os
import random
import threading

from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pynput import keyboard

from classes.common import AudioPlayer, TextHandler, TextExtractor
from classes.search import VideoComplement
from classes.speech import SpeechSynthesizer, SpeechRecognizer
from classes.text import CLU, Translator, KeywordExtractor
from utils.ssml import make_ssml
from utils.control import on_press

_ = load_dotenv()

# Helper constants
FILE_NAME = "static/output.wav"
TEXT_PATH = "static/text.txt"
LANG_PATH = "static/config.json"

def main():

    help_intro = "Bienvenido a la lectura interactiva. Puedes usar 3 teclas: Barra espaciadora, Control y Enter. Con la barra espaciadora detienes la lectura y escucha atentamente para guardar notas del texto. Con el Control puedes reanudar la lectura. Y con Enter puedes finalizar y escuchar el análisis completo de la lectura. Comenzamos"
    help_note_1 = "La cantidad total de notas es "
    help_note_2 = "Te leeré hasta 3 notas de ejemplo y lo demás lo guardaré"
    help_note_3 = "Nota "
    help_video_1 = "He encontrado 3 videos complementarios que te pueden ayudar"
    help_video_2 = "Video "

    with open(TEXT_PATH, 'r', encoding='utf-8') as file:
        text = file.read()

    with open(LANG_PATH, 'r') as config_file:
        config = json.load(config_file)

    lang_str = config.get('lang')
    lang = ast.literal_eval(lang_str)

    lang_key = list(lang.keys())[0]
    lang_val = list(lang.values())[0]

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
    bing_endpoint = os.getenv("BING_API_ENDPOINT")

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

    # Changed values to desired language
    text = translator.translate(text, lang_val)
    help_intro = translator.translate(help_intro, lang_val)
    help_note_1 = translator.translate(help_note_1, lang_val)
    help_note_2 = translator.translate(help_note_2, lang_val)
    help_note_3 = translator.translate(help_note_3, lang_val)
    help_video_1 = translator.translate(help_video_1, lang_val)
    help_video_2 = translator.translate(help_video_2, lang_val)

    llm = AzureChatOpenAI(
        azure_endpoint = azure_openai_endpoint,
        openai_api_key = azure_openai_api_key,
        openai_api_version = "2024-02-01",
        deployment_name = azure_openai_deploy,
        temperature = 0.5,
        n = 1
    )

    # First, it will create a wav file
    text_ssml = make_ssml(text, lang_key)
    synthesizer.synthesize_to_file(text_ssml, FILE_NAME)

    # Some more supportive tools
    player = AudioPlayer(FILE_NAME)
    text_handler = TextHandler(text, translator, lang_key, lang_val)
    extractor = TextExtractor(llm, translator, lang_val)
    video_complement = VideoComplement(bing_api_key, bing_endpoint, translator, lang_key, lang_val)

    # An informative note: we are starting
    synthesizer.speak_text(make_ssml(help_intro, lang_key))

    # A useful set to update text position with the reading
    text_handler.set_total_bytes(player.wf.getnframes() * player.wf.getsampwidth())

    # This will start reading the audio
    threading.Thread(target=player.play_audio, args=(text_handler,), daemon=True).start()

    # An event driven function that will pause and restart the audio.
    # While in pause the person can save notes by directly say what he wants to save or by asking gpt to inference from the text
    listener = keyboard.Listener(on_press=lambda key: on_press(key, player, text_handler, translator, synthesizer, extractor, recognizer, clu))
    listener.start()
    input("Press Enter to exit...\n")
    listener.stop()
    clu.close()

    # All the notes are processed to get keywords
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

    # We'll get until 3 more recommended videos to improve the educational experience based on what they are learning
    videos = video_complement.bing_search(keywords)
    synthesizer.speak_text(make_ssml(help_video_1, lang_key))
    for (i, video) in enumerate(videos):
        synthesizer.speak_text(make_ssml(help_video_2 + str(i + 1) + " " + video['name'], lang_key))
    print(f"Videos: {videos}")

if __name__ == "__main__":
    main()