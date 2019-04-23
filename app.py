from flask import Flask
from json import load
from flask_googlecharts import GoogleCharts
from google.cloud import translate
from backends.microsoft_adapter import MSTranslationProvider
import numpy as np
app = Flask(__name__)
#charts = GoogleCharts(app)
#translate_client = translate.Client()


class Configuration:
    def __init__(self):
        self.config = {}
        self.read_config()

    def read_config(self):
        with open("languages.json") as f:
            self.config = load(f)

    def get_languages_by_property(self, prop, value):
        res = {}
        for language in self.config:
            if prop in self.config[language] and self.config[language][prop] == value:
                res[language] = self.config[language]
        return res

    def get_languages_if_property_exists(self, prop):
        res = {}
        for language in self.config:
            if prop in self.config[language]:
                res[language] = self.config[language]
        return res

    def get_languages_by_backend(self, backend):
        return self.get_languages_by_property("provider", backend)

    def get_language(self, lang):
        return self.config[lang]

config = Configuration()
ms_languages = config.get_languages_by_backend("ms")
MSBackend = MSTranslationProvider(ms_languages.keys(), lang_opts=ms_languages)


def get_levenshtein_distance(word1, word2):
    """
    https://en.wikipedia.org/wiki/Levenshtein_distance
    :param word1:
    :param word2:
    :return:
    """
    word2 = word2.lower()
    word1 = word1.lower()
    matrix = [[0 for x in range(len(word2) + 1)] for x in range(len(word1) + 1)]

    for x in range(len(word1) + 1):
        matrix[x][0] = x
    for y in range(len(word2) + 1):
        matrix[0][y] = y

    for x in range(1, len(word1) + 1):
        for y in range(1, len(word2) + 1):
            if word1[x - 1] == word2[y - 1]:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,
                    matrix[x - 1][y - 1],
                    matrix[x][y - 1] + 1
                )
            else:
                matrix[x][y] = min(
                    matrix[x - 1][y] + 1,
                    matrix[x - 1][y - 1] + 1,
                    matrix[x][y - 1] + 1
                )

    return matrix[len(word1)][len(word2)]


def generate_edit_matrix(word, distance_metric=get_levenshtein_distance):
    translations = MSBackend.get_translation(word)
    translations["en"] = word
    lang_order = []
    distance_matrix = np.zeros(shape=(len(translations), len(translations)))
    i = 0
    for lang in translations:
        j = 0
        lang_order.append(lang)
        for lang2 in translations:
            distance_matrix[i, j] = distance_metric(translations[lang], translations[lang2])
            j += 1
        i += 1
    return distance_matrix

@app.route('/')
def home_page():
    return str(MSBackend.get_translation("tea"))


if __name__ == '__main__':
    app.run()
