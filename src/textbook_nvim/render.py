from enum import Enum
import re
from abc import ABC, abstractmethod
from flatlatex.latexfuntypes import LatexSyntaxError
from pydantic import BaseModel
from textbook_nvim.parser import ParsedCell, ParsedText
from typing import Dict, List, Tuple, Type, Union
from rich.console import Console, Group
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from pathlib import Path
from flatlatex import converter as Converter


class RenderedCell(BaseModel):
    text: str
    cell_range: Tuple[int, int]


class RenderedText(BaseModel):
    values: List[RenderedCell]


class AbstractRender(ABC):
    def __init__(
        self,
        lexer: str,
        comment_pattern: re.Pattern,
        cell_id: int,
        theme: str,
        cell_text: str,
        cell_color: str,
    ):
        self.lexer = lexer
        self.comment_pattern = comment_pattern
        self.cell_id = cell_id
        self.theme = theme
        self.cell_text = cell_text
        self.cell_color = cell_color

    def setup(
        self, parsed_cell: ParsedCell, console: Console, init_pos: int
    ) -> "AbstractRender":
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
            cell_range=(self.init_pos, self.init_pos + len(result.split("\n")) - 2),
        )


class MarkdownEnum(Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"


class MarkdownRow(BaseModel):
    text: str
    idx: int
    md_type: MarkdownEnum


class MarkdownRender(AbstractRender):
    table_pattern = re.compile(r"\|.+\|")
    eq_pattern = re.compile(r"\$(?P<equation>[^\n]+)\$")
    eq_block_pattern = re.compile(r"\$\$\n(?P<equation>[^\$]+)\$\$")
    eq_converter = Converter()
    sep_validator = re.compile(r"[\-\s]+")

    def render_table(self, group: List[MarkdownRow]) -> Union[Markdown, Table]:
        if re.search(self.sep_validator, "".join(group[1].text.split("|"))) is None:
            return Markdown("\n".join(line.text for line in group))
        table = Table()
        headers = group[0].text.strip().split("|")
        n_cols = len(headers)
        [table.add_column(col) for col in headers]
        for row in group[2:]:
            cells = row.text.strip().split("|")
            if len(cells) != n_cols:
                return Markdown("\n".join(line.text for line in group))
            table.add_row(*cells)
        return table

    def render_equations(self, lines: List[str]) -> List[str]:
        text = "\n".join(lines)

        def parse_line_eq(match: re.Match):
            text = match.group("equation")
            try:
                render = f" `{self.eq_converter.convert(text)}` "
            except LatexSyntaxError:
                render = f" ${text}$ "
            return render

        line_eq = re.sub(self.eq_pattern, parse_line_eq, text)

        def parse_block_eq(match: re.Match):
            text = match.group("equation")
            try:
                render = f"\n`{self.eq_converter.convert(text)}`\n"
            except LatexSyntaxError:
                render = f"$$\n{text}$$\n"
            return render

        block_eq = re.sub(self.eq_block_pattern, parse_block_eq, line_eq)
        return block_eq.split("\n")

    def generate_components(
        self, groups: List[List[MarkdownRow]]
    ) -> List[Union[Markdown, Table]]:
        components = []
        for group in groups:
            if group[0].md_type == MarkdownEnum.TEXT or len(group) < 3:
                components.append(Markdown("\n".join(line.text for line in group)))
            else:
                components.append(self.render_table(group))
        return components

    def render_lines(self, lines: List[str]) -> Group:
        if len(lines) < 2:
            return Group(Markdown("\n".join(lines)))
        parsed_lines = []
        for i, line in enumerate(lines):
            if re.search(self.table_pattern, line) is not None:
                md_type = MarkdownEnum.TABLE
            else:
                md_type = MarkdownEnum.TEXT
            parsed_lines.append(MarkdownRow(text=line, idx=i, md_type=md_type))

        groups = [[parsed_lines[0]]]
        for i in range(1, len(parsed_lines)):
            if parsed_lines[i].md_type == parsed_lines[i - 1].md_type:
                groups[-1].append(parsed_lines[i])
            else:
                groups.append([parsed_lines[i]])

        components = self.generate_components(groups)
        return Group(*components)

    def render(self) -> RenderedCell:
        lines = self.parsed_cell.text.split("\n")[1:]
        (*clean_lines,) = map(
            lambda line: re.sub(self.comment_pattern, "", line), lines
        )
        eq_lines = self.render_equations(clean_lines)
        md = Panel(self.render_lines(eq_lines), title="markdown")
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
            cell_range=(self.init_pos, self.init_pos + len(rendered_lines) - 2),
        )


class Renderer:
    parsed_text: ParsedText
    rendered_text: RenderedText
    lexer: str
    pattern: re.Pattern
    theme: str
    cell_text: str
    cell_color: str
    renders: Dict[str, Type[AbstractRender]] = {
        "code": CodeRender,
        "markdown": MarkdownRender,
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
        cell_color: str,
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
                    lexer=self.lexer,
                    cell_id=i + 1,
                    comment_pattern=self.pattern,
                    cell_text=self.cell_text,
                    cell_color=self.cell_color,
                    theme=self.theme,
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
