def get_string_embedding(string, word_model) -> list[float] or None:
    """Returns the vector representation of string according to the provided word embedding model. If the string has
    more than one word (separated by whitespace), the corresponding representation will be the sum of the vector
    representations of each word.

    Parameters
    ----------
    string : str
        String to be converted
    word_model : Any
        Gensim word embedding model

    Returns
    -------
    list[float] or None
        The corresponding full or partial vector representation depending on whether the tokens exist in the model
        or not. If no token is known by the model, None is returned.

    """
    tokens = string.split()
    embedded_tokens = []

    for token in tokens:
        try:
            embedded_tokens.append(word_model.get_vector(token))
        except KeyError:
            continue

    if len(embedded_tokens) == 0:
        return

    return sum(embedded_tokens)


def get_words_embedding(words, word_model) -> list[list[float]]:
    """Returns the list of the vector representation of the given strings according to the provided word embedding model.

    Parameters
    ----------
    words : list[str]
        List of strings to get the embedding vector representation
    word_model : Any
        Gensim word embedding model

    Returns
    -------
    list[list[float]]
        The embedding vector representation of the corresponding list of strings

    """
    embedded_words = []

    for word in words:
        embedding = get_string_embedding(word, word_model)

        if embedding is not None:
            embedded_words.append(embedding)

    return embedded_words
