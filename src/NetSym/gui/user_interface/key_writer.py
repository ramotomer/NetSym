from __future__ import annotations

from typing import List, Union, Callable, Tuple, Dict

from pyglet.window.key import BACKSPACE, ENTER, NUM_ADD, NUM_DECIMAL, NUM_DIVIDE, NUM_MULTIPLY, NUM_SUBTRACT, NUM_0, NUM_9

from NetSym.consts import KEYBOARD, T_PressedKeyModifier, T_PressedKey
from NetSym.exceptions import KeyActionAlreadyExistsError


class KeyWriter:
    """
    Gets key presses and translates them to text
    """

    TO_UPPERCASE = {
        '-': '_', '=': '+', '0': ')', '9': '(', '8': '*', '7': '&', '6': '^', '5': '%', '4': '$', '3': '#', '2': '@',
        '1': '!', '`': '~', '/': '?', ',': '<', '.': '>', '[': '{', ']': '}', ';': ':', '\'': '"', '\\': '|'
    }

    NUMPAD_KEYS = {**{numpad_key: str(i) for i, numpad_key in enumerate(range(NUM_0, NUM_9 + 1))},
                   **{
                       NUM_ADD: '+',
                       NUM_DECIMAL: '.',
                       NUM_DIVIDE: '/',
                       NUM_MULTIPLY: '*',
                       NUM_SUBTRACT: '-',
                   }}

    def __init__(self,
                 append_function: Callable[[str], None],
                 delete_function: Callable[[], None],
                 submit_action:   Callable[[], None] = lambda: None,
                 exit_action:     Callable[[], None] = lambda: None) -> None:
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

        self.key_combination_dict: Dict[Tuple[T_PressedKey, T_PressedKeyModifier], Callable] = {
            (ENTER,     KEYBOARD.MODIFIERS.NONE): self.submit,
            (BACKSPACE, KEYBOARD.MODIFIERS.NONE): self.delete,
        }

    def add_key_mapping(self, symbol: int, action: Callable[[], None]) -> None:
        """
        Adds a new action to occur when a given key is pressed.
        :param symbol: `key.*` or a list of them
        :param action: what to do when that key is inserted
        :return:
        """
        self.add_key_combination(symbol, KEYBOARD.MODIFIERS.NONE, action)

    def add_key_combination(self, symbol: Union[int, List[int]], modifiers: int, action: Callable) -> None:
        """
        Adds a combination of key and modifiers to the mapping.
        This is checked first!
        :param symbol: `key.*` or a list of them
        :param modifiers:
        :param action:
        :return:
        """
        if isinstance(symbol, list):
            for inner_symbol in symbol:
                self.add_key_combination(inner_symbol, modifiers, action)
            return

        if (symbol, modifiers) in self.key_combination_dict:
            raise KeyActionAlreadyExistsError("you are overriding and action in the key dict!!!")

        self.key_combination_dict[(symbol, modifiers)] = action

    def pressed(self, symbol: int, modifiers: int) -> bool:
        """
        This is called when the user is typing the string into the `PopupTextBox`.
        :param symbol: `key.*` of what key was pressed
        :param modifiers: a bitwise representation of what other button were also pressed
        (KEYBOARD.MODIFIERS.SHIFT, etc...)
        :return: whether or not the pressed key had any effect
        """
        if (symbol, modifiers) in self.key_combination_dict:
            self.key_combination_dict[(symbol, modifiers)]()
            return True

        if symbol in KEYBOARD.PRINTABLE_RANGE:
            char = chr(symbol).lower()
            if (modifiers & KEYBOARD.MODIFIERS.SHIFT) ^ (modifiers & KEYBOARD.MODIFIERS.CAPS):
                char = char.upper()
                char = self.TO_UPPERCASE.get(char, char)
            self.write(char)
            return True

        if symbol in self.NUMPAD_KEYS:
            self.write(self.NUMPAD_KEYS[symbol])
            return True

        return False
