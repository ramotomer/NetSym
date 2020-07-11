from pyglet.window import key

from consts import KEYBOARD
from exceptions import KeyActionAlreadyExistsError


class KeyWriter:
    """
    Gets key presses and translates them to text
    """

    TO_UPPERCASE = {
        '-': '_', '=': '+', '0': ')', '9': '(', '8': '*', '7': '&', '6': '^', '5': '%', '4': '$', '3': '#', '2': '@',
        '1': '!', '`': '~', '/': '?', ',': '<', '.': '>', '[': '{', ']': '}', ';': ':', '\'': '"', '\\': '|'
    }

    NUMPAD_KEYS = {**{numpad_key: str(i) for i, numpad_key in enumerate(range(key.NUM_0, key.NUM_9 + 1))},
                   **{
                       key.NUM_ADD: '+',
                       key.NUM_DECIMAL: '.',
                       key.NUM_DIVIDE: '/',
                       key.NUM_MULTIPLY: '*',
                       key.NUM_SUBTRACT: '-',
                   }}

    def __init__(self, append_function, delete_function, submit_action=lambda: None, exit_action=lambda: None):
        """
        Initiates the key_writer.
        :param append_function: append text to the writing. (must receive one string)
        :param delete_function: delete one char back
        :param submit_action: when the enter is pressed.
        :param exit_action: when escape is pressed.
        """
        self.write = append_function
        self.delete = delete_function
        self.submit = submit_action
        self.exit = exit_action

        self.key_dict = {
            key.ENTER: self.submit,
            key.ESCAPE: self.exit,
            key.BACKSPACE: self.delete,
        }

        self.key_combination_dict = {}  # {(key, modifiers): action}

    def add_key_mapping(self, symbol, action):
        """
        Adds a new action to occur when a given key is pressed.
        :param symbol: `key.*`
        :param action: function
        :return:
        """
        if symbol in self.key_dict:
            raise KeyActionAlreadyExistsError("you are overriding and action in the key dict!!!")

        self.key_dict[symbol] = action

    def add_key_combination(self, symbol, modifiers, action):
        """
        Adds a combination of key and modifiers to the mapping.
        This is checked first!
        :param symbol:
        :param modifiers:
        :param action:
        :return:
        """
        if (symbol, modifiers) in self.key_dict:
            raise KeyActionAlreadyExistsError("you are overriding and action in the key dict!!!")

        self.key_combination_dict[(symbol, modifiers)] = action

    def pressed(self, symbol, modifiers):
        """
        This is called when the user is typing the string into the `PopupTextBox`.
        :param symbol: a string of the key that was pressed.
        :param modifiers: a bitwise representation of what other button were also pressed
        (KEYBOARD.MODIFIERS.SHIFT, etc...)
        :return: None
        """
        if (symbol, modifiers) in self.key_combination_dict:
            self.key_combination_dict[(symbol, modifiers)]()

        elif symbol in self.key_dict:
            self.key_dict[symbol]()

        elif symbol in KEYBOARD.PRINTABLE_RANGE:
            char = chr(symbol).lower()
            if (modifiers & KEYBOARD.MODIFIERS.SHIFT) ^ (modifiers & KEYBOARD.MODIFIERS.CAPS):
                char = char.upper()
                char = self.TO_UPPERCASE.get(char, char)
            self.write(char)

        elif symbol in self.NUMPAD_KEYS:
            self.write(self.NUMPAD_KEYS[symbol])
