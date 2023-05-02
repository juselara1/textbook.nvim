from click import command, option
from textbook_nvim.render import Renderer
from textbook_nvim.parser import ParsedText
from pathlib import Path

@command
@option("--parsed_path", type=Path, help="Json file with the parsed text.")
@option("--rendered_path", type=Path, help="Json file to store the rendered text.")
def main(parsed_path: Path, rendered_path: Path) -> int:
    parsed_text = ParsedText.parse_file(parsed_path)
    (
        Renderer()
        .setup(parsed_text)
        .render()
        .save(rendered_path)
        )
    return 0
