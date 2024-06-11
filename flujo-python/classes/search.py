import requests

class VideoComplement:
    def __init__(self, bing_api_key, bing_endpoint, translator, lang_key, lang_val):
        self.headers = {'Ocp-Apim-Subscription-Key': bing_api_key}
        self.endpoint = bing_endpoint
        self.translator = translator
        self.lang_key = lang_key
        self.lang_val = lang_val

    def bing_search(self, words):

        query_pre = 'Aprender más sobre'
        query_pre = self.translator.translate(query_pre, self.lang_val)
        query = ', '.join(words)

        params = {
            'q': f"{query_pre} {query}",
            'count': 3,
            'mkt': self.lang_key
        }

        response = requests.get(self.endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json()
            values = data.get('value', [])

            keys = ['webSearchUrl', 'name', 'thumbnailUrl']
            result = [{key: value[key] for key in keys if key in value} for value in values]

        else:
            print(f"Error occurred during the search. Status Code: {response.status_code}")
            result = []

        return result