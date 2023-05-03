import re
from click import command, option
from textbook_nvim.render import Renderer
from textbook_nvim.parser import ParsedText
from pathlib import Path

@command
@option("--parsed_path", type=Path, help="Json file with the parsed text.")
@option("--rendered_path", type=Path, help="Json file to store the rendered text.")
@option("--lexer", type=str, help="Lexer for the programming language.")
@option("--theme", type=str, help="Theme for color highlighting.")
@option("--comment_pattern", type=str, help="Regex to identify comments.")
@option("--cell_text", type=str, help="Text to show as cell separator.")
@option("--cell_color", type=str, help="Color to display the cell separator.")
def main(
        parsed_path: Path,
        rendered_path: Path,
        lexer: str, theme: str,
        comment_pattern: str, cell_text: str,
        cell_color: str
        ) -> int:
    parsed_text = ParsedText.parse_file(parsed_path)
    (
        Renderer()
        .setup(
            parsed_text,
            lexer=lexer,
            pattern=re.compile(comment_pattern),
            theme=theme,
            cell_text=cell_text,
            cell_color=cell_color
            )
        .render()
        .save(rendered_path)
        )
    return 0
