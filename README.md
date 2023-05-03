# textbook.nvim

This plugin allows management and rendering of `jupyter` notebooks inside of `neovim` through `jupytext` format and `rich` components.

![example1](docs/example1.gif)

## Installation

You'll have to install some utilities and dependencies through `pip`:

```sh
pip install textbook_nvim
```

Then you can install the plugin, for instance, with `packer`:

```lua
use {"juselara1/textbook.nvim", run = ":UpdateRemotePlugins"}
```

## Usage

The idea of `textbook` is to offer a non-intrusive way to edit notebook files defined as plain text. By default it uses the percent format as a cell separator but you can define a regex to parse any kind of format.

For instance, the following text defines python notebook:

```python
# %% [markdown]
# Markdown code...

# %% [raw]
print("hello world")
```

Where `# %% [markdown]` represents a markdown cell and `# %% [raw]` a code cell. To render this file you should run the following command to specify the current buffer as the source:

```vim
:TextBookBuffer
```

Then you should open the render view:

```vim
:TextBookOpen
```

This will spawn a new buffer with the rendered text, there you have the following options:

- `:TextBookSync`: syncs the cursor position in the same cell as the plain text file.
- `:TextBookSelectCell [cell_id]`: when no arguments are passed selects the cell under the cursor, otherwise, selects the cell of the `cell_id`.
- `:TextBookNextCell`: selects the next cell.
- `:TextBookPrevCell`: selects the previous cell.
- `:TextBookClose`: closes the rendered view and places the cursor in the same cell as the rendered view.

## Configuration

**TODO**
