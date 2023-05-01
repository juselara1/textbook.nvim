import re
from typing import List, Tuple
from pydantic import BaseModel

Text = List[str]

class ParsedCell(BaseModel):
    text: str
    cell_type: str
    cell_range: Tuple[int, int]

ParsedText = List[ParsedCell]

class Parser:
    text : Text
    parsed_text : ParsedText
    pattern : re.Pattern

    def set_text(self, text: Text) -> "Parser":
        self.text = text
        return self

    def set_pattern(self, pattern: re.Pattern = re.compile(r"^# \%\% \[(?P<cell_type>\w+)\]")) -> "Parser":
        self.pattern = pattern
        return self

    def parse(self) -> "Parser":
        separator_positions = []
        cell_types = []
        for i, line in enumerate(self.text):
            match = re.match(self.pattern, line)
            if match is not None:
                separator_positions.append(i)
                cell_types.append(match.group("cell_type"))
        if separator_positions[-1] != len(self.text):
            separator_positions.append(len(self.text))

        self.parsed_text = []
        for initial_pos, end_pos, cell_type in zip(separator_positions, separator_positions[1:], cell_types):
            self.parsed_text.append(
                    ParsedCell(
                        text="\n".join(self.text[initial_pos: end_pos]),
                        cell_type=cell_type,
                        cell_range=(initial_pos, end_pos)
                        )
                    )
        return self

    def get_parsed_text(self) -> ParsedText:
        return self.parsed_text
