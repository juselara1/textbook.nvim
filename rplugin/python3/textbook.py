from uuid import uuid4
from typing import Any, List, Optional
from pydantic import BaseModel
from pynvim import plugin, command
from pynvim.api import Nvim, Buffer
from textbook_nvim.parser import Parser
from textbook_nvim.render import Renderer
from pathlib import Path

Args = List[str]


class TextBookConfig(BaseModel):
    tmp_path: str
    cell_indicator: str
    cell_pattern: str
    cell_separator: str
    cell_text: str
    cell_color: str
    theme: str
    comment_pattern: str


@plugin
class TextBook:
    buffer: Buffer
    tb_buffer: Buffer
    tmp_path: Path
    active_cell: int = 0
    ns_id: int
    parsed_path: Path
    rendered_path: Path
    extmark_id: Any = None
    config: TextBookConfig

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.parser = Parser()
        self.renderer = Renderer()
        self.load_config()

    def load_config(self):
        self.config = TextBookConfig(
            tmp_path=self.nvim.vars.get("TextBookTmpPath") or "/tmp",
            cell_indicator=self.nvim.vars.get("TextBookCellIndicator") or "◆",
            cell_pattern=(
                self.nvim.vars.get("TextBookCellPattern") or
                r"^# \%\% \[(?P<cell_type>\w+)\]"
                ),
            cell_separator=self.nvim.vars.get("TextBookCellSeparator") or r"# %% [{}]",
            cell_text=self.nvim.vars.get("TextBookCellText") or " Cell: {}",
            cell_color=self.nvim.vars.get("TextBookCellColor") or r"\#5180e6",
            theme=self.nvim.vars.get("TextBookTheme") or "gruvbox-dark",
            comment_pattern=self.nvim.vars.get("TextBookCommentPattern") or r"^\#",
        )

    @command("TextBookConfig", nargs=0, range="")
    def textbook_config(self, args: Args, range=None):
        self.load_config()

    @command("TextBookBuffer", nargs=0, range="")
    def textbook_buffer(self, args: Args, range=None):
        self.buffer = self.nvim.current.buffer

    def parse(self, parsed_path: Optional[Path] = None):
        (self.parser.set_text(text=[str(i) for i in self.buffer]).set_pattern().parse())
        if parsed_path is not None:
            self.parser.save(parsed_path)

    @command("TextBookOpen", nargs=0, range="")
    def textbook_open(self, args: Args, range=None):
        idx = str(uuid4())
        self.parsed_path = Path(self.config.tmp_path) / (idx + "_parsed")
        self.rendered_path = Path(self.config.tmp_path) / (idx + "_rendered")
        self.parse(self.parsed_path)

        row = self.nvim.current.window.cursor[0] - 1
        for i, cell in enumerate(self.parser.parsed_text.values):
            if row >= cell.cell_range[0] and row < cell.cell_range[1]:
                self.active_cell = i

        lexer = self.nvim.call("nvim_buf_get_option", self.buffer.number, "filetype")
        self.tb_buffer = self.nvim.api.create_buf(False, True)
        self.nvim.api.set_current_buf(self.tb_buffer)
        self.nvim.command(
            f"ter tbcli --parsed_path '{str(self.parsed_path)}' "
            + f"--rendered_path '{str(self.rendered_path)}' "
            + f"--lexer '{lexer}' --theme '{self.config.theme}' "
            + f"--comment_pattern '{self.config.comment_pattern}' "
            + f"--cell_text '{self.config.cell_text}' "
            + f"--cell_color '{self.config.cell_color}'"
        )
        self.ns_id = self.nvim.api.create_namespace("cell_indicator")

    @command("TextBookSync", nargs="*", range="")  # type: ignore
    def textbook_sync(self, args: Args, range=None):
        self.select_cell()

    def select_cell(self):
        self.renderer.load(self.rendered_path)
        line = self.renderer.rendered_text.values[self.active_cell].cell_range[0]

        if self.extmark_id is not None:
            self.nvim.call(
                "nvim_buf_del_extmark",
                self.tb_buffer.number,
                self.ns_id,
                self.extmark_id,
            )
        self.extmark_id = self.nvim.call(
            "nvim_buf_set_extmark",
            self.tb_buffer.number,
            self.ns_id,
            line - 1,
            0,
            {"virt_text": [[self.config.cell_indicator]], "virt_text_pos": "overlay"},
        )
        self.nvim.current.window.cursor = (line, 1)

    @command("TextBookSelectCell", nargs="*", range="")  # type: ignore
    def textbook_select_cell(self, args: Args, range=None):
        self.renderer.load(self.rendered_path)

        if not args:
            row = self.nvim.current.window.cursor[0]
            for i, cell in enumerate(self.renderer.rendered_text.values):
                if row >= cell.cell_range[0] and row < cell.cell_range[1]:
                    self.active_cell = i
        else:
            self.active_cell = int(args[0]) - 1
        self.select_cell()

    @command("TextBookAddCell", nargs="*", range="") #type: ignore
    def textbook_add_cell(self, args: Args, range=None):
        if (
            hasattr(self, "tb_buffer")
            and self.nvim.current.buffer.number == self.tb_buffer.number
        ):
            self.select_cell()
            self.close()
        if not hasattr(self, "buffer"):
            self.buffer = self.nvim.current.buffer
        self.parse()

        after = int(args[1])
        row = self.nvim.current.window.cursor[0] - 1
        new_pos = 0
        for cell in self.parser.parsed_text.values:
            if row >= cell.cell_range[0] and row < cell.cell_range[1]:
                new_pos = cell.cell_range[after]
        prev_lines = self.buffer[:]
        cell_type = args[0]
        new_lines = prev_lines[:new_pos]
        new_lines.extend([self.config.cell_separator.format(cell_type), " "])
        new_lines.extend(prev_lines[new_pos:])
        self.buffer[:] = new_lines
        self.nvim.current.window.cursor = (new_pos + 2, 0)

    @command("TextBookSelectNextCell", nargs=0, range="")
    def textbook_select_next_cell(self, args: Args, range=None):
        self.renderer.load(self.rendered_path)
        if self.active_cell != len(self.renderer.rendered_text.values) - 1:
            self.active_cell += 1
        self.select_cell()

    @command("TextBookSelectPrevCell", nargs=0, range="")
    def textbook_select_prev_cell(self, args: Args, range=None):
        self.renderer.load(self.rendered_path)
        if self.active_cell != 0:
            self.active_cell -= 1
            self.select_cell()

    def close(self):
        self.nvim.api.set_current_buf(self.buffer)
        line = self.parser.parsed_text.values[self.active_cell].cell_range[0]
        self.nvim.current.window.cursor = (line + 1, 0)
        self.nvim.api.buf_delete(self.tb_buffer.handle, {"force": True, "unload": True})

    @command("TextBookClose", nargs=0, range="")
    def textbook_close(self, args: Args, range=None):
        self.close()

    @command("TextBookRender", nargs=0, range="")
    def textbook_render(self, args: Args, range=None):
        filename = self.buffer.name
        self.nvim.api.command(f"!jupytext -s {filename}")
