#!/usr/bin/env python

import re
import shlex
import subprocess
from os.path import expandvars
from typing import NoReturn, Optional

import pymupdf


def merge_strings(*strings: str) -> Optional[str]:
    """
    Merge strings which might be None.
    """
    filtered_strings = [s for s in strings if s is not None]
    return " ".join(filtered_strings) if filtered_strings else None


def send_error(error: str) -> NoReturn:
    print(error)
    try:
        subprocess.run(["notify-send", error])
    except FileNotFoundError:
        pass
    exit(1)


def try_running_subprocess(
    cmd: list[str],
    not_found_error: str = "Command not found!",
    input: Optional[str] = None,
) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, input=input
        )
    except FileNotFoundError:
        send_error(not_found_error)
    return result


def search_pdfs(
    base_directory: str, cmd: Optional[str] = None, hidden: bool = False
) -> list[str]:
    """
    Search for PDFs in the specified base directory. By default, we
    try to use `fd`. If it is not installed, we fall back to `find`.

    Alternatively, the specific search command to be used can be
    supplied as `cmd`.
    """
    if cmd is not None:
        pdfs = try_running_subprocess(shlex.split(cmd)).stdout.split("\n")[:-1]
    else:
        cmd = ["fd", "-I", "-t", "f", "-e", "pdf", "-a", ".", base_directory]
        if hidden:
            cmd += ["-H"]
        try:
            pdfs = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            ).stdout.split("\n")[:-1]
        except FileNotFoundError:
            pdfs = subprocess.run(
                ["find", base_directory, "-type", "f", "-name", "*.pdf"],
                capture_output=True,
                text=True,
            ).stdout.split("\n")[:-1]

    return pdfs


def select(
    items: list[str],
    cmd: Optional[str],
    indices: bool = False,
    check: bool = True,
) -> int:
    """
    Launch a user-selection for the list `items` using for example
    fzf (this is the default), fuzzel or rofi. The precise command
    can be supplied using `cmd`.

    Make sure that the subprocess returns the index, not the string
    of the selection or use `indices=True` in order to add indices
    at the front of each item.
    """
    # fzf as the default selector
    if cmd is None:
        cmd = "fzf --with-nth 2.."
        indices = True
    if indices:
        for i in range(len(items)):
            items[i] = f"{i}\t{items[i]}"
    selection = try_running_subprocess(
        shlex.split(cmd),
        not_found_error=f"Selector ({cmd}) not found!",
        input="\n".join(items),
    ).stdout
    if indices:
        selection = re.search(r"\d*", selection).group(0)
    if not selection or selection == "":
        if check:
            send_error("Nothing selected!")
            exit(1)
        else:
            selection = -1
    return int(selection)


def get_toc(path: str, mupdf_coordinate_space: bool = False) -> list:
    """
    Extract the table of contents from a PDF file.
    """
    with pymupdf.open(path) as doc:
        toc = []
        for t in doc.get_toc(simple=False):
            page = doc.load_page(t[0])
            # We try to access the coordinates of the entries at least
            # once, even if we don't need to transform them to mupdf
            # coordinates since this enables us to ensure that every
            # entry has them.
            try:
                coords = t[3]["to"]
            except KeyError:
                coords = pymupdf.Point()

            if mupdf_coordinate_space:
                coords *= page.transformation_matrix
            t[3]["to"] = coords
            toc.append(t)
    return toc


def open_pdf(
    path: str,
    cmd: str,
    position_args: Optional[str] = None,
    position: Optional[list[int]] = None,
) -> None:
    """
    Open a PDF, optionally at a specific position (consisting of a list
    including the page number, x position and y position, in that order),
    with the by `cmd` specified viewer.

    The string `position_args` specifies how the position parameters will
    be passed to the pdf viewer, by replacing the substrings "$page", "$xloc",
    "$yloc" with the corresponding values.

    The default viewer is zathura.
    """
    if cmd is None:
        cmd = "zathura"
        position_args = "-P $page"
    pos_strings = [r"\$page", r"\$xloc", r"\$yloc"]
    if position is None:
        try_running_subprocess(
            shlex.split(cmd) + [path],
            not_found_error=f"PDF viewer ({cmd}) not found!",
        )
    else:
        if position_args:
            for i in range(3):
                position_args = re.sub(
                    pos_strings[i], str(position[i]), position_args
                )
        else:
            position_args = ""
        try_running_subprocess(
            shlex.split(cmd) + [path] + shlex.split(position_args),
            not_found_error=f"PDF viewer ({cmd}) not found!",
        )


def main():
    # A bit of argument parsing
    import argparse

    epilog = """example usage:
    # Use rofi as the selector with custom prompts
    %(prog)s -s 'rofi -dmenu -i -format i' -psa='-p PDF' -tsa='-p TOC'

    # Use fuzzel as a selector and sioyek as the pdf viewer
    # Also show full paths and only search within the Documents directory
    %(prog)s -f -b ~/Documents  \\
        -s 'fuzzel -d --counter --index -w 100' \\
        -p 'sioyek' -mc -pa '--page $page --xloc $xloc --yloc $yloc'

Have fun reading! :D"""
    desc = "Interactively open a PDF file, optionally at a specific TOC entry."
    parser = argparse.ArgumentParser(
        description=desc,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--full-path",
        help="show full paths of the pdf files during selection",
        action="store_true",
    )
    parser.add_argument(
        "-nt",
        "--no-toc",
        help="never ask for the preferred table of contents entry",
        action="store_true",
    )
    parser.add_argument(
        "-hi",
        "--hidden",
        help="""also search for hidden files (only relevant if `fd` is
        installed and `--search-cmd` is not used)""",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--base-directory",
        help="base directory for searching pdf files",
    )
    parser.add_argument(
        "-s",
        "--selector",
        help="""command to launch for selecting items. It needs to return the
        index of the selection, not the selection itself. If this is not
        possible, please refer to `--selector-indices`.
        (default: `fzf`)
        """,
    )
    parser.add_argument(
        "-si",
        "--selector-indices",
        help="preceed selection items by their indices",
        action="store_true",
    )
    parser.add_argument(
        "-psa",
        "--pdf-selector-args",
        help="""additional arguments to pass to the selector during pdf
        selection (if your arguments start with a dash, make sure to add
        a equal sign, i.e. `-psa="-option"`)""",
    )
    parser.add_argument(
        "-tsa",
        "--toc-selector-args",
        help="""additional arguments to pass to the selector during toc
        entry selection (please take the same caveat as for `-psa` into
        account)""",
    )
    parser.add_argument(
        "-p",
        "--pdf-viewer",
        help="command to launch for viewing pdf files (default: `zathura`)",
    )
    parser.add_argument(
        "-pa",
        "--pdf-viewer-args",
        help="""arguments to optionally provide to the pdf viewer for opening
        at a specific position. These can contain the strings '$page', '$xloc'
        and '$yloc' which will be replaced accordingly, cp. "example usage"
        below.""",
    )
    parser.add_argument(
        "-mc",
        "--mupdf-coordinate-space",
        help="""pass coordinates in mupdf coordinate space to the pdf viewer
        instead of default pdf coordinate space""",
        action="store_true",
    )
    parser.add_argument(
        "--search-cmd",
        help="""command to launch for searching pdf files
        (overrides `--base-directory` and `--hidden`)""",
    )
    args = parser.parse_args()

    # Find all PDFs in the specified directory
    if (b := args.base_directory) is not None:
        search_dir = b
    else:
        search_dir = expandvars("$HOME")
    pdfs = search_pdfs(search_dir, cmd=args.search_cmd, hidden=args.hidden)

    # Let the user select a specific file
    pdf_items = [p if args.full_path else re.sub(r".*/", "", p) for p in pdfs]
    selected_pdf = pdfs[
        select(
            pdf_items,
            cmd=merge_strings(args.selector, args.pdf_selector_args),
            indices=args.selector_indices,
        )
    ]

    # Extract the TOC
    toc = get_toc(selected_pdf, args.mupdf_coordinate_space)

    # If the PDF has no TOC, simply open it, otherwise ask the user for the
    # desired entry and open the file at the corresponding page.
    # Also respect the users choice via the relevant flag.
    if len(toc) == 0 or args.no_toc:
        open_pdf(selected_pdf, cmd=args.pdf_viewer)
    else:
        # If the selection does not work properly, e.g. because the user
        # cancels it, we simply open the PDF, without specifying a page.
        toc_index = select(
            [t[1] for t in toc],
            cmd=merge_strings(args.selector, args.toc_selector_args),
            indices=args.selector_indices,
            check=False,
        )
        if toc_index >= 0:
            toc_point = toc[toc_index][3]["to"]
            toc_position = [toc[toc_index][2], toc_point.x, toc_point.y]
            open_pdf(
                selected_pdf,
                cmd=args.pdf_viewer,
                position_args=args.pdf_viewer_args,
                position=toc_position,
            )
        else:
            open_pdf(selected_pdf, cmd=args.pdf_viewer)


if __name__ == "__main__":
    main()
