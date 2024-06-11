import threading
import time
import wave
import pyaudio
from utils.ssml import make_ssml

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class AudioPlayer:

    def __init__(self, file_name):
        self.wf = wave.open(file_name, 'rb')
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                                  channels=self.wf.getnchannels(),
                                  rate=self.wf.getframerate(),
                                  output=True)

        self.is_paused = False
        self.lock = threading.Lock()
        self.chunk_size = 128

    def play_audio(self, text_handler):
        data = self.wf.readframes(self.chunk_size)
        while data:
            with self.lock:
                if not self.is_paused:
                    self.stream.write(data)
                    text_handler.update_text_position(len(data))
                    data = self.wf.readframes(self.chunk_size)
                else:
                    time.sleep(0.1)
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def set_pause(self, pause, text_handler, *args):
        with self.lock:
            self.is_paused = pause
            if pause:
                text_handler.print_and_extract_chunk_text(*args)

class TextHandler:

    def __init__(self, text, translator, lang_key, lang_val):
        self.text = text
        self.translator = translator
        self.lang_key = lang_key
        self.lang_val = lang_val
        self.chars_read = 0
        self.text_position = 0
        self.last_pause_position = 0
        self.total_bytes = None
        self.notes = []

    def set_total_bytes(self, total_bytes):
        self.total_bytes = total_bytes

    def update_text_position(self, bytes_read):
        bytes_per_char = self.total_bytes / len(self.text)
        chars_read = float(bytes_read / bytes_per_char)
        self.chars_read += chars_read

    def print_and_extract_chunk_text(self, translator, synthesizer, extractor, recognizer, clu):

        help_text = "Qué deseas realizar? Guardar una nota o hacer una pregunta sobre el texto?"
        help_text_no_understand = "No te he entendido, esta vez guardaremos una nota"
        help_text_saved_note = "Nota guardada con éxito, presiona la tecla Control para continuar"

        self.text_position = int(self.chars_read)
        text_position_offset = min(self.text_position + 15, len(self.text))
        last_pause_position_offset = max(self.last_pause_position - 515, 0)
        chunk_text = self.text[last_pause_position_offset:text_position_offset]
        print("Text read so far:", chunk_text)

        help_text = self.translator.translate(help_text, self.lang_val)
        synthesizer.speak_text(make_ssml(help_text, self.lang_key))
        query = recognizer.get_prompt_from_voice()

        if query:
            query_tr = translator.translate(query, 'en')
            intent = clu.analyze(query_tr)
        else:
            help_text_no_understand = self.translator.translate(help_text_no_understand, self.lang_val)
            synthesizer.speak_text(make_ssml(help_text_no_understand, self.lang_key))
            intent = "get_note"

        result = self.handle_intent(intent, query, chunk_text, translator, synthesizer, recognizer, extractor)
        print("Note saved: ", result)
        if result is not None:
            self.notes.append(result)
        self.last_pause_position = self.text_position
        help_text_saved_note = self.translator.translate(help_text_saved_note, self.lang_val)
        synthesizer.speak_text(make_ssml(help_text_saved_note, self.lang_key))

    def handle_intent(self, intent, query, chunk_text, translator, synthesizer, recognizer, extractor):

        help_text_note = "Bien, indícame que nota quieres guardar"
        help_text_question = "Realiza una pregunta sobre el texto que estamos leyendo"
        help_text_no_understand = "No te he entendido, esta vez guardaremos una nota"

        if intent == "get_note":
            help_text_note = self.translator.translate(help_text_note, self.lang_val)
            synthesizer.speak_text(make_ssml(help_text_note, self.lang_key))
            return recognizer.get_prompt_from_voice()
        elif intent == "infer_text":
            help_text_question = self.translator.translate(help_text_question, self.lang_val)
            synthesizer.speak_text(make_ssml(help_text_question, self.lang_key))
            query = recognizer.get_prompt_from_voice()
            if not query:
                query = "Devuelve un resumen del texto"
                query = self.translator.translate(query, self.lang_val)
            return extractor.extract_note(chunk_text, query)
        else:
            help_text_no_understand = self.translator.translate(help_text_no_understand, self.lang_val)
            synthesizer.speak_text(make_ssml(help_text_no_understand, self.lang_key))
            return recognizer.get_prompt_from_voice()

    def get_notes(self):
        return self.notes

class TextExtractor:

    def __init__(self, llm, translator, lang_val):
        self.llm = llm
        self.translator = translator
        self.lang_val = lang_val

    def extract_note(self, chunk_text, query):
        system_template = '''Eres un asistente de educación cuyo objetivo es ayudar a una persona a guardar notas de \
            corta extensión. El usuario te hará una pregunta sobre un texto, siempre le debes entregar una respuesta. \
            Si la pregunta no es clara realiza un inferencia para crear un pregunta que sea muy similar. Tu objetivo es \
            procesar la pregunta y responderla con el contexto de 'chunk_text', si el contexto no es suficiente puedes usar \
            el contexto con el que fuiste entrenado; sin embargo, no debe ser mucho, la proporción en la respuesta debe ser \
            más del 75% en base al 'chunk_text'. La respuesta debe ser un texto breve con la respuesta relevante. '''

        system_template = self.translator.translate(system_template, self.lang_val)

        system_message_prompt_template = SystemMessagePromptTemplate.from_template(system_template)

        human_template = "User give {query} and text {chunk_text}"
        human_message_prompt_template = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt_template = ChatPromptTemplate.from_messages(
            [system_message_prompt_template, human_message_prompt_template])

        final_prompt = chat_prompt_template.format_prompt(query=query, chunk_text=chunk_text).to_messages()
        response = self.llm.invoke(final_prompt)
        content = response.content

        return content