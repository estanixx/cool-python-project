def word_trick(sentence: str) -> str:
    """
    Returns a string consisting of the i-th character of the i-th word in the input sentence,
    where i starts from 0. If a word does not have an i-th character, it is skipped.
    """
    words_and_indices = list(enumerate(sentence.split()))
    selected_characters = [word[i] for i, word in words_and_indices if i < len(word)]
    return ''.join(selected_characters)