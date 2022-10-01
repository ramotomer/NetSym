class MyStringIO:
    """
    I could not (for some reason) import or install StringIO, made a simple one myself.
    """
    def __init__(self) -> None:
        self.text: str = ''

    def write(self, string: str) -> None:
        if not self.text:
            self.text = string
        else:
            self.text += f"\n{string}"

    def getvalue(self) -> str:
        return self.text

    def close(self) -> None:
        pass
