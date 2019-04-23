# LangCluster
LangCluster is a tool to automatically visuallize the similarities 
between various languages. Given a word, LangCluster will send a request to various
translation backends (currently Microsoft and Google) and then compare the words by
edit distance. Afterwards, LangCluster will perform clustering on the words and group
words with common pronunciation together.

## Adding languages
Languages can be added by updating `language.json`.