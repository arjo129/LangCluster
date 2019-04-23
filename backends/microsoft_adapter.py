import uuid
import requests

from backends import BaseTranslationProvider


def configure_ms_translator():
    with open("/home/arjo/Documents/SEED/LanguageClustering/api_keys/ms.key", "r") as f:
        return f.readline()


class MSTranslationProvider(BaseTranslationProvider):

    def __init__(self, languages, lang_opts):
        super().__init__(languages, lang_opts=lang_opts)
        self.headers = {
            'Ocp-Apim-Subscription-Key': configure_ms_translator(),
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

    def __build_translation_string(self):
        with_transliterate = ""
        without_transliterate =""
        for lang in self.languages:
            if lang in self.lang_opts and "transliterate" in self.lang_opts[lang] and self.lang_opts[lang]["transliterate"] == "ms":
                with_transliterate += "&to="+lang+"&toScript=Latn"
            else:
                without_transliterate += "&to="+lang
        return with_transliterate, without_transliterate

    def get_translation(self, word):
        base_url = 'https://api.cognitive.microsofttranslator.com'
        path = '/translate?api-version=3.0'
        params_w_transliterate, params_wo_transliterate = self.__build_translation_string()

        results = {}

        constructed_url = base_url + path + params_w_transliterate
        body = [{
            'text': word
        }]
        request = requests.post(constructed_url, headers=self.headers, json=body)
        response = request.json()
        for res in response:
            for translation in res["translations"]:
                results[translation["to"]] = translation["transliteration"]["text"]

        constructed_url = base_url + path + params_wo_transliterate
        body = [{
            'text': word
        }]
        request = requests.post(constructed_url, headers=self.headers, json=body)
        response = request.json()
        for res in response:
            for translation in res["translations"]:
                results[translation["to"]] = translation["text"]
        return results


