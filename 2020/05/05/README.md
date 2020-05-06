# Sudoku Tools
This directory contains tools for generating, solving, and formatting Sudoku
boards of arbitrary size. While the authoritative source code is maintained in
`index.org`, for convenience I have "tangled" the individual files and provided
them here.

## Installation
A simple `./setup.py install` should suffice. The formatting tools depend on
Latex and ImageMagick, but the others require only Python 3 (tested with Python
3.7.3).

The library in `sudoku` contains the core logic for generating and solving
boards; the scripts in `bin/` are based on this library.

## Usage
Each tool (sudokugen, sudoku, sudoku2tex, sudoku2img) gives a help message when
a `-h` or `--help` is passed as an argument.

## Further Discussion
Detailed information on the principles of operation, as well as additional
information regarding usage, performance, etc., is available at
[[https://reindeereffect.github.io/2020/05/05/index.html]], also derived from
`index.org`.
