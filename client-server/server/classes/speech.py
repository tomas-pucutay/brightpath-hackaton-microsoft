import azure.cognitiveservices.speech as speechsdk
import time

class SpeechSynthesizer:
    def __init__(self, speech_config):
        self.synthesizer_save = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        self.audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        self.synthesizer_speak = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=self.audio_config)

    def synthesize_to_file(self, ssml, file_name):
        result = self.synthesizer_save.speak_ssml(ssml)
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            stream = speechsdk.AudioDataStream(result)
            stream.save_to_wav_file(file_name)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Speech synthesis failed due to an internal error.")
                print(f"Error details: {cancellation_details.error_details}")
            else:
                print(f"Speech synthesis was canceled: {cancellation_details.reason}")
        else:
            print(f"Speech synthesis failed: {result.reason}")

    def speak_text(self, ssml):
        result = self.synthesizer_speak.speak_ssml(ssml)
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesis succesful!")
        else:
            print(f"Speech synthesis failed: {result.reason}")

class SpeechRecognizer:
    def __init__(self, speech_config):
        source_languages = [
            speechsdk.languageconfig.SourceLanguageConfig(language="es-ES"),
            speechsdk.languageconfig.SourceLanguageConfig(language="en-US"),
            speechsdk.languageconfig.SourceLanguageConfig(language="fr-FR"),
            speechsdk.languageconfig.SourceLanguageConfig(language="pt-BR"),
        ]
        auto_detect_language = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(sourceLanguageConfigs=source_languages)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, auto_detect_source_language_config=auto_detect_language)

    def get_prompt_from_voice(self):
        print("Please say your prompt...")
        result = self.recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Texto reconocido: {}".format(result.text))
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No se ha podido reconocer el habla.")
            return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Reconocimiento cancelado: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error: {}".format(cancellation_details.error_details))
        return None