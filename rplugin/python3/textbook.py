from typing import Any, Iterable
from pynvim import plugin, command
from pynvim.api import Nvim, Buffer
from textbook_nvim.parser import Parser

Args = Iterable[Any]

@plugin
class TextBook:
    buffer : Buffer

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.parser = Parser()

    @command("TextBookBuffer", nargs=0, range="")
    def textbook_buffer(self, args: Args, range=None):
        self.buffer = self.nvim.current.buffer

    @command("TextBookOpen", nargs=0, range="")
    def textbook_render(self, args: Args, range=None):
        parsed_text = (
                self.parser.set_text(
                    text = [str(i) for i in self.buffer]
                    )
                .set_pattern()
                .parse()
                .get_parsed_text()
                )
        buf = self.nvim.api.create_buf(False, True)
        self.nvim.api.set_current_buf(buf)
        for cell in parsed_text:
            buf.append(str(cell))

    @command("TextBookClose", nargs=0, range="")
    def textbook_close(self, args: Args, range=None):
        self.nvim.api.set_current_buf(self.buffer)
