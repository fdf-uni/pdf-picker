# PDF Picker

## What is this?
This repository contains a relatively short and simple Python script which searches for all PDF files in a specified directory (by default `$HOME`) and then asks the user which one they want to open.
If the selected PDF file has a table of contents in its metadata, the user is asked for a specific entry (unless disabled, see [below](#Usage)) at which the document is then opened.
Otherwise, or if the selection is canceled, the document is simply opened directly without specifying any particular position.

Personally, I have bound the execution of this script to a shortcut through my window manager (cp. "example usage" [below](#Usage)), so that I can always jump to any PDF rather quickly, but by default, it runs completely on the command line.

## Caveats
The extraction of the table of contents relies entirely on its existence within the metadata of the PDF.
One can easily verify, whether any given document has one, by for example simply opening it in one's preferred PDF viewer and checking, whether there is a TOC in the sidebar or any other appropriate place within the UI (for `zathura` users, simply press `Tab`).

In case that you have some documents which don't satisfy this requirement, but to which you'd like to add a table of contents, I can highly recommend [pdf.tocgen](https://github.com/Krasjet/pdf.tocgen)! :)

## Installation and Dependencies

Simply save the file `pdf_picker.py` wherever you want and install `pymupdf` using for example `pip install pymupdf`.

### Hard Dependencies
- Python 3.9+
- `pymupdf` library (mainly used for extraction of TOC)

### Soft Dependencies

> Note: All these programs can be customized using command line arguments, see [Usage](#Usage), which is why I refer to them as soft dependencies.

- `fd` (used for slightly faster search and mainly the ability to skip hidden files)  
    If `fd` is not found, the script automatically falls back to `find`, so if you prefer the latter, there's nothing you need to do. :D
- `fzf`, the default selection command
- `zathura`, the default PDF viewer

## Usage

```
usage: pdf_picker.py [-h] [-f] [-nt] [-hi] [-b BASE_DIRECTORY] [-s SELECTOR]
                     [-si] [-psa PDF_SELECTOR_ARGS] [-tsa TOC_SELECTOR_ARGS]
                     [-p PDF_VIEWER] [-pa PDF_VIEWER_ARGS] [-mc]
                     [--search-cmd SEARCH_CMD]

Interactively open a PDF file, optionally at a specific TOC entry.

options:
  -h, --help            show this help message and exit
  -f, --full-path       show full paths of the pdf files during selection
  -nt, --no-toc         never ask for the preferred table of contents entry
  -hi, --hidden         also search for hidden files (only relevant if `fd` is
                        installed and `--search-cmd` is not used)
  -b, --base-directory BASE_DIRECTORY
                        base directory for searching pdf files
  -s, --selector SELECTOR
                        command to launch for selecting items. It needs to
                        return the index of the selection, not the selection
                        itself. If this is not possible, please refer to
                        `--selector-indices`.
  -si, --selector-indices
                        preceed selection items by their indices
  -psa, --pdf-selector-args PDF_SELECTOR_ARGS
                        additional arguments to pass to the selector during
                        pdf selection (if your arguments start with a dash,
                        make sure to add a equal sign, i.e. `-psa="-option"`)
  -tsa, --toc-selector-args TOC_SELECTOR_ARGS
                        additional arguments to pass to the selector during
                        toc entry selection (please take the same caveat as
                        for `-psa` into account)
  -p, --pdf-viewer PDF_VIEWER
                        command to launch for viewing pdf files
  -pa, --pdf-viewer-args PDF_VIEWER_ARGS
                        arguments to optionally provide to the pdf viewer for
                        opening at a specific position. These can contain the
                        strings '$page', '$xloc' and '$yloc' which will be
                        replaced accordingly, cp. "example usage" below.
  -mc, --mupdf-coordinate-space
                        pass coordinates in mupdf coordinate space to the pdf
                        viewer instead of default pdf coordinate space
  --search-cmd SEARCH_CMD
                        command to launch for searching pdf files (overrides
                        `--base-directory` and `--hidden`)

example usage:
    # Use rofi as the selector with custom prompts
    python pdf_picker.py -s 'rofi -dmenu -i -format i' -psa='-p PDF' -tsa='-p TOC'

    # Use fuzzel as a selector and sioyek as the pdf viewer
    # Also show full paths and only search within the Documents directory
    python pdf_picker.py -f -b ~/Documents  \
        -s 'fuzzel -d --counter --index -w 100' \
        -p 'sioyek' -mc -pa '--page $page --xloc $xloc --yloc $yloc'

Have fun reading! :D
```

Please note the described requirement for the equals sign when providing `-psa` or `-tsa` with strings that start with a dash.
This sadly seems to be a [limitation of Python's argparse library](https://github.com/python/cpython/issues/53580).

`-si`/`--selection-indices` might seem a bit weird, but it is mainly used since file names without their full path might not be unique.
Hence, we cannot rely only on the selected file name.
This script alleviates this problem, by instead storing the PDF files with their full path in a list and asking for the index of the selection instead of the file name, so the selector needs to be able to return the index of the selection (this can be seen in the above example usages, where we add `-format i` to `rofi` and `--index` to `fuzzel`).
However, some commands such as `fzf` might not provide this feature.
When `-si` is used, all file names are passed to the selection command together with the corresponding indices preceding them.
After a selection has occurred, the file name is then again stripped from the result, leaving only the wanted index.
Especially for `fzf` this provides a satisfactory solution, since we can use `fzf --with-nth 2..` to hide the indices during selection.
