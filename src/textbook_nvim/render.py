import re
from abc import ABC, abstractmethod
from pydantic import BaseModel
from textbook_nvim.parser import ParsedCell, ParsedText
from typing import Dict, List, Tuple, Type
from rich.console import Console
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from pathlib import Path

class RenderedCell(BaseModel):
    text: str
    cell_range: Tuple[int, int]

class RenderedText(BaseModel):
    values: List[RenderedCell]

class AbstractRender(ABC):
    def __init__(self, lexer: str, comment_pattern: re.Pattern, cell_id:int, theme: str, cell_text: str, cell_color: str):
        self.lexer = lexer
        self.comment_pattern = comment_pattern
        self.cell_id = cell_id
        self.theme = theme
        self.cell_text = cell_text
        self.cell_color = cell_color

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
        syntax = Syntax(clean_text, self.lexer)
        text = Text(self.cell_text.format(self.cell_id))
        text.stylize(self.cell_color)
        with self.console.capture() as capture:
            self.console.print(text)
            self.console.print(syntax)
            self.console.print(" ")
        result = capture.get()
        self.console.print(text)
        self.console.print(syntax)
        self.console.print(" ")
        return RenderedCell(
                text=result,
                cell_range=(self.init_pos, self.init_pos + len(result.split("\n")) - 2)
                )

class MarkdownRender(AbstractRender):

    def render(self) -> RenderedCell:
        lines = self.parsed_cell.text.split("\n")[1:]
        clean_lines = map(lambda line: re.sub(self.comment_pattern, "", line), lines)
        clean_text = "\n".join(clean_lines)
        md = Panel(Markdown(clean_text), title="markdown")
        text = Text(self.cell_text.format(self.cell_id))
        text.stylize(self.cell_color)
        with self.console.capture() as capture:
            self.console.print(text)
            self.console.print(md)
        rendered_lines = capture.get().split("\n")
        self.console.print(text)
        self.console.print(md)
        return RenderedCell(
                text="\n".join(rendered_lines),
                cell_range=(self.init_pos, self.init_pos + len(rendered_lines) - 2)
                )

class Renderer:
    parsed_text : ParsedText
    rendered_text : RenderedText
    lexer: str
    pattern: re.Pattern
    theme: str
    cell_text: str
    cell_color: str
    renders: Dict[str, Type[AbstractRender]] = {
            "raw": CodeRender,
            "markdown": MarkdownRender
            }

    def __init__(self, console_kwargs: Dict = {}):
        self.console = Console(**console_kwargs)

    def setup(
            self,
            parsed_text: ParsedText,
            lexer: str,
            pattern: re.Pattern,
            theme: str,
            cell_text: str,
            cell_color: str
            ) -> "Renderer":
        self.parsed_text = parsed_text
        self.lexer = lexer
        self.pattern = pattern
        self.theme = theme
        self.cell_text = cell_text
        self.cell_color = cell_color
        return self
    
    def render(self) -> "Renderer":
        self.rendered_text = RenderedText(values=[])
        init_pos = 1
        for i, cell in enumerate(self.parsed_text.values):
            self.rendered_text.values.append(
                    self.renders[cell.cell_type](
                        lexer=self.lexer, cell_id=i + 1,
                        comment_pattern=self.pattern,
                        cell_text=self.cell_text,
                        cell_color=self.cell_color,
                        theme=self.theme
                        )
                    .setup(cell, self.console, init_pos)
                    .render()
                    )
            init_pos = self.rendered_text.values[-1].cell_range[1] + 1
        return self

    def get_rendered_text(self) -> RenderedText:
        return self.rendered_text

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            f.write(self.rendered_text.json())

    def load(self, path: Path) -> None:
        self.rendered_text = RenderedText.parse_file(path)
