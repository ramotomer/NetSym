class MyStringIO:
    """
    I could not (for some reason) import or install StringIO, made a simple one myself.
    """
    def __init__(self):
        self.text = ''

    def write(self, string):
        if not self.text:
            self.text = string
        else:
            self.text += f"\n{string}"

    def getvalue(self):
        return self.text

    def close(self):
        pass
