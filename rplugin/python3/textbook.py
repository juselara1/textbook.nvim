from uuid import uuid4
from typing import Any, List
from pydantic import BaseModel
from pynvim import plugin, command
from pynvim.api import Nvim, Buffer
from textbook_nvim.parser import Parser
from textbook_nvim.render import Renderer
from pathlib import Path

Args = List[str]

class TextBookConfig(BaseModel):
    tmp_path : str 
    cell_indicator : str
    cell_pattern : str
    cell_text: str
    cell_color: str
    theme: str
    comment_pattern : str

@plugin
class TextBook:
    buffer : Buffer
    tb_buffer : Buffer
    tmp_path : Path
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
                cell_pattern=self.nvim.vars.get("TextBookCellPattern") or r"^# \%\% \[(?P<cell_type>\w+)\]",
                cell_text=self.nvim.vars.get("TextBookCellText") or " Cell: {}",
                cell_color=self.nvim.vars.get("TextBookCellColor") or r"\#5180e6",
                theme=self.nvim.vars.get("TextBookTheme") or "gruvbox-dark",
                comment_pattern=self.nvim.vars.get("TextBookCommentPattern") or r"^\#"
                )

    @command("TextBookBuffer", nargs=0, range="")
    def textbook_buffer(self, args: Args, range=None):
        self.buffer = self.nvim.current.buffer

    @command("TextBookOpen", nargs=0, range="")
    def textbook_render(self, args: Args, range=None):
        idx = str(uuid4()) 
        self.parsed_path = Path(self.config.tmp_path) / (idx + "_parsed")
        self.rendered_path = Path(self.config.tmp_path) / (idx + "_rendered")
        (
                self.parser.set_text(
                    text = [str(i) for i in self.buffer]
                    )
                .set_pattern()
                .parse()
                .save(self.parsed_path)
                )

        row = self.nvim.current.window.cursor[0] - 1
        for i, cell in enumerate(self.parser.parsed_text.values):
            if row >= cell.cell_range[0] and row < cell.cell_range[1]:
                self.active_cell = i

        lexer = self.nvim.call("nvim_buf_get_option", self.buffer.number, "filetype")
        self.tb_buffer = self.nvim.api.create_buf(False, True)
        self.nvim.api.set_current_buf(self.tb_buffer)
        self.nvim.command(
                f"ter tbcli --parsed_path '{str(self.parsed_path)}' " +
                f"--rendered_path '{str(self.rendered_path)}' " +
                f"--lexer '{lexer}' --theme '{self.config.theme}' " +
                f"--comment_pattern '{self.config.comment_pattern}' " +
                f"--cell_text '{self.config.cell_text}' " +
                f"--cell_color '{self.config.cell_color}'"
                )
        self.ns_id = self.nvim.api.create_namespace("cell_indicator")

    @command("TextBookSync", nargs="*", range="") #type: ignore
    def textbook_sync(self, args: Args, range=None):
        self.select_cell()

    def select_cell(self):
        self.renderer.load(self.rendered_path)
        line = self.renderer.rendered_text.values[self.active_cell].cell_range[0]
        
        if self.extmark_id is not None:
            self.nvim.call("nvim_buf_del_extmark", self.tb_buffer.number, self.ns_id, self.extmark_id)
        self.extmark_id = self.nvim.call(
                "nvim_buf_set_extmark",
                self.tb_buffer.number,
                self.ns_id, line - 1, 0,
                {"virt_text": [[self.config.cell_indicator]], "virt_text_pos": "overlay"}
                )
        self.nvim.current.window.cursor = (line, 1)

    @command("TextBookSelectCell", nargs="*", range="") #type: ignore
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

    @command("TextBookClose", nargs=0, range="")
    def textbook_close(self, args: Args, range=None):
        self.nvim.api.set_current_buf(self.buffer)
        line = self.parser.parsed_text.values[self.active_cell].cell_range[0]
        self.nvim.current.window.cursor = (line + 1, 1)
        self.nvim.api.buf_delete(self.tb_buffer.handle, {"force": True, "unload": True})
