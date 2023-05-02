import re
from abc import ABC, abstractmethod
from pydantic import BaseModel
from textbook_nvim.parser import ParsedCell, ParsedText
from typing import Dict, List, Tuple, Type
from rich.console import Console
from rich.syntax import Syntax
from rich.markdown import Markdown

class RenderedCell(BaseModel):
    text: str
    cell_range: Tuple[int, int]

RenderedText = List[RenderedCell]

class AbstractRender(ABC):
    def __init__(self, lexer: str = "python", comment_pattern: str="^#"):
        self.lexer = lexer
        self.comment_pattern = comment_pattern

    def setup(self, parsed_cell: ParsedCell, console: Console, init_pos: int) -> "AbstractRender":
        self.parsed_cell = parsed_cell
        self.console = console
        self.init_pos = init_pos
        return self

    @abstractmethod
    def render(self) -> RenderedCell:
        ...

class CodeRender(AbstractRender):

    def render(self) -> RenderedCell:
        lines = self.parsed_cell.text.split("\n")[1:]
        clean_text = "\n".join(lines)
        with self.console.capture() as capture:
            syntax = Syntax(clean_text, self.lexer)
            self.console.print(syntax)
        result = capture.get()
        return RenderedCell(
                text=result,
                cell_range=(self.init_pos, self.init_pos + len(result.split("\n")))
                )

class MarkdownRender(AbstractRender):

    def render(self) -> RenderedCell:
        lines = self.parsed_cell.text.split("\n")[1:]
        clean_lines = map(lambda line: re.sub(self.comment_pattern, "", line), lines)
        clean_text = "\n".join(clean_lines)
        with self.console.capture() as capture:
            md = Markdown(clean_text)
            self.console.print(md)
        rendered_lines = capture.get().split("\n")
        result = "\n".join(map(lambda line: self.comment_pattern[1:] + line, rendered_lines))
        return RenderedCell(
                text=result,
                cell_range=(self.init_pos, self.init_pos + len(rendered_lines))
                )

class Renderer:
    parsed_text : ParsedText
    rendered_text : RenderedText
    lexer: str
    pattern: re.Pattern
    renders: Dict[str, Type[AbstractRender]] = {
            "raw": CodeRender,
            "markdown": MarkdownRender
            }

    def __init__(self, console_kwargs: Dict = {}):
        self.console = Console(**console_kwargs)

    def setup(
            self,
            parsed_text: ParsedText,
            lexer: str = "python",
            pattern: re.Pattern = re.compile(r"^#")
            ) -> "Renderer":
        self.parsed_text = parsed_text
        self.lexer = lexer
        self.pattern = pattern
        return self
    
    def render(self) -> "Renderer":
        self.rendered_text = []
        init_pos = 0
        for cell in self.parsed_text:
            self.rendered_text.append(
                    self.renders[cell.cell_type](lexer=self.lexer)
                    .setup(cell, self.console, init_pos)
                    .render()
                    )
            init_pos += len(self.rendered_text[-1].text.split("\n"))
        return self

    def get_rendered_text(self) -> RenderedText:
        return self.rendered_text
