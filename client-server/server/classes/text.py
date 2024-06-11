from azure.ai.textanalytics import TextAnalyticsClient
from azure.ai.language.conversations import ConversationAnalysisClient
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem

class CLU:

    def __init__(self, endpoint, credential, project_name, deploy_name):
        self.client = ConversationAnalysisClient(endpoint, credential)
        self.project_name = project_name
        self.deploy_name = deploy_name

    def analyze(self, query):
        result = self.client.analyze_conversation(
            task={
                "kind": "Conversation",
                "analysisInput": {
                    "conversationItem": {
                        "participantId": "1",
                        "id": "1",
                        "modality": "text",
                        "language": "en",
                        "text": query
                    },
                    "isLoggingEnabled": False
                },
                "parameters": {
                    "projectName": self.project_name,
                    "deploymentName": self.deploy_name,
                    "verbose": True
                }
            }
        )
        intent = result["result"]["prediction"]["topIntent"]
        return intent

    def close(self):
        self.client.close()

class Translator:

    def __init__(self, endpoint, credential, region):
        self.client = TextTranslationClient(endpoint=endpoint, credential=credential, region=region)

    def translate(self, text, lang):
        body = [InputTextItem(text=text)]
        to_language = [lang]
        result = self.client.translate(body=body, to_language=to_language)
        new_text = result[0].get('translations',[])[0].get('text','')
        return new_text

class KeywordExtractor:

    def __init__(self, endpoint, credential):
        self.client = TextAnalyticsClient(endpoint=endpoint, credential = credential)

    def extract_keywords(self, text):
        response = self.client.extract_key_phrases(documents=[text])[0]
        return response.key_phrases

    def extract_notes_keywords(self, notes):
        all_keywords = []
        for note in notes:
            keywords = self.extract_keywords(note)
            all_keywords.extend(keywords)
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        sorted_keywords = sorted(keyword_counts.keys(), key=lambda kw: -keyword_counts[kw])
        return sorted_keywords[:3]