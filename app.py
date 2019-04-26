from flask import Flask, send_from_directory
from json import load, dumps
from sklearn.cluster import DBSCAN
from backends.microsoft_adapter import MSTranslationProvider
import cyrtranslit
import unidecode
import numpy as np

app = Flask(__name__)

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

def post_process(word, language):
    """
    Post Processing steps
    TODO: Clean up and modularize
    :param word:
    :param language:
    :return:
    """
    if language in config.get_languages_by_property("transliterate", "cyr"):
        word = cyrtranslit.to_latin(word, language).casefold()
    if language in config.get_languages_if_property_exists("accents"):
        word = unidecode.unidecode(word).casefold()
    if language in config.get_languages_if_property_exists("stopwords"):
        res = word.casefold().split()
        res = list(filter(lambda x: x not in config.get_language(language)["stopwords"], res))
        word = " ".join(res)
    return word


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


def translate_all_backends(word):
    translations = MSBackend.get_translation(word)
    translations["en"] = word
    cleaned = {}
    for language in translations:
        cleaned[language] = post_process(translations[language], language)
    return cleaned


def generate_edit_matrix(word, distance_metric=get_levenshtein_distance):
    translations = translate_all_backends(word)
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
    return distance_matrix, lang_order, translations


def cluster_matrix(distance_matrix):
    dbscan = DBSCAN(eps=1, min_samples=2, metric="precomputed")
    return dbscan.fit_predict(distance_matrix)

@app.route('/static')
def send_js(path):
    return send_from_directory('static', path)

@app.route('/api/backend')
def home_page():
    word = "tea"
    edit_matrix, lang_order, translations = generate_edit_matrix(word)
    clusters = cluster_matrix(edit_matrix)
    dct = {}
    for language, cluster in zip(lang_order, clusters):
        for region in config.get_language(language)["regions"]:
            dct[region] = int(cluster)
    return dumps(dct)


if __name__ == '__main__':
    app.run()
