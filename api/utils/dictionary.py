# Use dynamodb

class Dictionary:
    """A simple dictionary implementation that allows adding and looking up entries."""
    def __init__(self):
        self.definitions = {}

    def newentry(self, key, value):
        """Add a new entry to the dictionary."""
        self.definitions[key.capitalize()] = value

    def look(self, key):
        """Look up an entry in the dictionary."""
        key = key.capitalize()
        if key in self.definitions:
            return self.definitions[key]
        else:
            return f"Can't find entry for {key}"