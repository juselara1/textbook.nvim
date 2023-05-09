# textbook.nvim

<a href="https://pypi.python.org/pypi/textbook_nvim"><img src="https://img.shields.io/pypi/v/textbook_nvim.svg"/></a>
<a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg"/></a>

This plugin allows management and rendering of `jupyter` notebooks inside of `neovim` through the `jupytext` format and `rich` components.

Click on the following image to see a demo:

[![Alt text](https://img.youtube.com/vi/mC8kZa93uhg/0.jpg)](https://www.youtube.com/watch?v=mC8kZa93uhg)

## Installation

You'll need to install some utilities and dependencies through `pip`:

```sh
pip install textbook_nvim
```

After that, you can install the plugin using `packer`, for instance:

```lua
use {"juselara1/textbook.nvim", run = ":UpdateRemotePlugins"}
```

## Usage

The idea behind `textbook` is to offer a non-intrusive way to edit notebook files defined as plain text. By default, it uses the percent format as a cell separator, but you can define a regex to parse any kind of format.

For instance, the following text defines a Python notebook:

```python
# %% [markdown]
# Markdown code...

# %% [code]
print("Hello, world!")
```

To render this file, you should run the following command to specify the current buffer as the source:

```vim
:TextBookBuffer
```

Then, you should open the render view:

```vim
:TextBookOpen
```

This will spawn a new buffer with the rendered text. There, you will have the following options:

- `:TextBookSync`: syncs the cursor position in the same cell as the plain text file.
- `:TextBookSelectCell [cell_id]`: when no arguments are passed, selects the cell under the cursor. Otherwise, selects the cell of the `cell_id`.
- `:TextBookNextCell`: selects the next cell.
- `:TextBookPrevCell`: selects the previous cell.
- `:TextBookAddCell cell_type after`: creates a cell of type `cell_type` (`code` or `markdown`) and can be before (`0`) or after (`1`) the cell under the cursor.
- `:TextBookConfig`: reloads the configuration.
- `:TextBookRender`: syncs the current buffer with its paired `ipynb` file through `jupytext`.
- `:TextBookClose`: closes the rendered view and places the cursor in the same cell as the rendered view.

## Configuration

You can add the following lines to your `init.lua` configuration:

```lua
vim.g.TextBookTmpPath = "/tmp" -- config path.
vim.g.TextBookCellIndicator = ">" -- indicator for cell selection.
vim.g.TextBookCellPattern = "^# %% [(?P<cell_type>\\w+)]" -- regex to parse the cell separator.
vim.g.TextBookCellSeparator = "# %% {}" -- defines the cell separator.
vim.g.TextBookCellText = " Cell: {}" -- text to display the cells.
vim.g.TextBookCellColor = "\\#5180E6" -- cell to display the cell id.
vim.g.TextBookTheme = "vim" -- color highligthing theme.
vim.g.TextBookCommentPattern = "^\\#" -- defines the markdown comment pattern.

local mode = 'n'
local options = {noremap=true, silent=true}

local binds = {
    {bind="<Leader>to", command=":TextBookOpen<CR>"},
    {bind="<Leader>tr", command=":TextBookSync<CR>"},
    {bind="<Leader>ti", command=":TextBookBuffer<CR>"},
    {bind="<Leader>ts", command=":TextBookSelectCell<CR>"},
    {bind="<Leader>tg", command=":TextBookSelectCell"},
    {bind="<Leader>tj", command=":TextBookSelectNextCell<CR>"},
    {bind="<Leader>tk", command=":TextBookSelectPrevCell<CR>"},
    {bind="<Leader>tq", command=":TextBookClose<CR>"},
    {bind="<Leader>tma", command=":TextBookAddCell markdown 1<CR>"},
    {bind="<Leader>tmb", command=":TextBookAddCell markdown 0<CR>"},
    {bind="<Leader>tra", command=":TextBookAddCell code 1<CR>"},
    {bind="<Leader>trb", command=":TextBookAddCell code 0<CR>"},
}

for _, value in ipairs(binds) do
    vim.api.nvim_set_keymap(
            mode, value.bind, value.command, options
        )
end
```

> **Note**: all patterns must be implemented as Python regex.

> **Note**: the cell separator must have the named group `cell_type`, this is used for parsing.

> **Note**: `textbook.nvim` uses the `pygments` [styles](https://pygments.org/styles/).
