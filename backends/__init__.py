class BaseTranslationProvider:
    def __init__(self, languages, lang_opts=None):
        self.languages = languages
        self.lang_opts = lang_opts

    def get_translation(self, word):
        pass