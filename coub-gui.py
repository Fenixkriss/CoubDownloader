#!/usr/bin/env python3

"""
Copyright (C) 2018-2020 HelpSeeker <AlmostSerious@protonmail.ch>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
from textwrap import dedent

from gooey import Gooey, GooeyParser

import coub


class GuiDefaultOptions(coub.DefaultOptions):
    """Custom default option class to reflect the differences between CLI and GUI."""
    # Create special labels for dropdown menus
    # Some internally used values would cause confusion
    # Some menus also combine options
    QUALITY_LABEL = ["Worst quality", "Best quality"]
    AAC_LABEL = ["Only MP3", "No Bias", "Prefer AAC", "Only AAC"]
    RECOUB_LABEL = ["No Recoubs", "With Recoubs", "Only Recoubs"]
    SPECIAL_LABEL = {
        (False, False, False): "None",
        (True, False, False): "Share",
        (False, True, False): "Video only",
        (False, False, True): "Audio only",
    }

    def __init__(self):
        # Necessary as __file__ within coub.py would point to the extracted
        # PyInstaller archive for standalone coub-gui binaries
        config_dirs = [os.path.dirname(os.path.realpath(__file__))]
        super(GuiDefaultOptions, self).__init__(config_dirs=config_dirs)

        # There's no way for the user to enter input if a prompt occurs
        # So only "yes" or "no" make sense
        if self.PROMPT not in {"yes", "no"}:
            self.PROMPT = "no"

        # Outputting to the current dir (or any relative path) is a viable strategy for a CLI tool
        # Not so much for a GUI
        if not os.path.isabs(self.PATH):
            self.PATH = os.path.join(os.path.expanduser("~"), "coubs")

def translate_to_cli(options):
    """Make GUI-specific options object compatible with the main script."""
    # Special dropdown menu labels and what they translate to
    QUALITY_LABEL = {"Worst quality": 0, "Best quality": -1}
    AAC_LABEL = {"Only MP3": 0, "No Bias": 1, "Prefer AAC": 2, "Only AAC": 3}
    RECOUB_LABEL = {"No Recoubs": 0, "With Recoubs": 1, "Only Recoubs": 2}
    SPECIAL_LABEL = {
        "None": (False, False, False),
        "Share": (True, False, False),
        "Video only": (False, True, False),
        "Audio only": (False, False, True),
    }

    # Convert GUI labels to valid options for the main script
    options.v_quality = QUALITY_LABEL[options.v_quality]
    options.a_quality = QUALITY_LABEL[options.a_quality]
    options.aac = AAC_LABEL[options.aac]
    options.recoubs = RECOUB_LABEL[options.recoubs]
    options.share, options.v_only, options.a_only = SPECIAL_LABEL[options.special]

    return options


@Gooey(
    program_name="CoubDownloader",
    default_size=(800, 600),
    progress_regex=r"^\[\s*(?P<current>\d+)\/(?P<total>\d+)\](.*)$",
    progress_expr="current / total * 100",
    tabbed_groups=True,
    show_success_modal=False,
    show_failure_modal=False,
    hide_progress_msg=False,
    terminal_font_family="monospace", # didn't work when I tested it on Windows
    menu=[
        {
            'name': 'Help',
            'items': [
                {
                    'type': 'AboutDialog',
                    'menuTitle': 'About',
                    'name': 'CoubDownloader',
                    'description': 'A simple download script for coub.com',
                    'website': 'https://github.com/HelpSeeker/CoubDownloader',
                    'license': dedent(
                        """
                        Copyright (C) 2018-2020 HelpSeeker <AlmostSerious@protonmail.ch>

                        This program is free software: you can redistribute it and/or modify
                        it under the terms of the GNU General Public License as published by
                        the Free Software Foundation, either version 3 of the License, or
                        (at your option) any later version.

                        This program is distributed in the hope that it will be useful,
                        but WITHOUT ANY WARRANTY; without even the implied warranty of
                        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
                        GNU General Public License for more details.

                        You should have received a copy of the GNU General Public License
                        along with this program.  If not, see <https://www.gnu.org/licenses/>.
                        """
                    ),
                }
            ]
        }
    ]
)
def parse_cli():
    """Create Gooey GUI."""
    defs = GuiDefaultOptions()
    parser = GooeyParser(
        description="Download videos from coub.com",
        usage="%(prog)s [OPTIONS] INPUT [INPUT]..."
    )

    # Input
    input_ = parser.add_argument_group(
        "Input",
        description="Specify various input sources\n\n"
                    "All input fields support several items (i.e. names, IDs, "
                    "tags, etc.). Items must be comma-separated.",
        gooey_options={'columns': 1}
    )
    input_.add_argument("--urls", default="", metavar="Direct URLs",
                        help="Provide direct URL input")
    input_.add_argument("--ids", default="", metavar="Coub IDs",
                        help="Download coubs with the given IDs")
    input_.add_argument("--channels", default="", metavar="Channels",
                        help="Download channels with the given names")
    input_.add_argument("--recoubs", metavar="Recoubs",
                        default=defs.RECOUB_LABEL[defs.RECOUBS],
                        choices=["No Recoubs", "With Recoubs", "Only Recoubs"],
                        help="How to treat recoubs during channel downloads")
    input_.add_argument("--tags", default="", metavar="Tags",
                        help="Download coubs with at least one of the given tags")
    input_.add_argument("--searches", default="", metavar="Search Terms",
                        help="Download search results for the given terms")
    input_.add_argument("--communities", default="", metavar="Communities",
                        help="Download coubs from the given communities")
    input_.add_argument("--stories", default="", metavar="Stories",
                        help="Download coubs from the given stories")
    input_.add_argument("--lists", default="", widget="MultiFileChooser",
                        metavar="Link Lists", help="Read coub links from input lists",
                        gooey_options={'message': "Choose link lists"})
    input_.add_argument("--random", action="count", metavar="Random",
                        help="Download N*1000 randomly generated coubs")
    input_.add_argument("--hot", action="store_true", widget="BlockCheckbox",
                        metavar="Hot Section", help="Download coubs from the hot section")

    # Common Options
    common = parser.add_argument_group("General", gooey_options={'columns': 1})
    common.add_argument("--prompt", choices=["yes", "no"], default=defs.PROMPT,
                        metavar="Prompt Behavior", help="How to answer user prompts")
    common.add_argument("--repeat", type=coub.positive_int, default=defs.REPEAT,
                        metavar="Loop Count", help="How often to loop the video stream")
    common.add_argument("--duration", type=coub.valid_time, default=defs.DURATION,
                        metavar="Limit duration",
                        help="Max. duration of the output (FFmpeg syntax)")
    common.add_argument("--preview", default=defs.PREVIEW, metavar="Preview Command",
                        help="Command to invoke to preview each finished coub")
    common.add_argument("--archive", type=coub.valid_archive,
                        default=defs.ARCHIVE, widget="FileSaver",
                        metavar="Archive", gooey_options={'message': "Choose archive file"},
                        help="Use an archive file to keep track of already downloaded coubs")
    common.add_argument("--keep", action="store_const", const=True, default=defs.KEEP,
                        widget="BlockCheckbox", metavar="Keep streams",
                        help="Whether to keep the individual streams after merging")

    # Download Options
    download = parser.add_argument_group("Download", gooey_options={'columns': 1})
    download.add_argument("--connections", type=coub.positive_int,
                          default=defs.CONNECTIONS, metavar="Number of connections",
                          help="How many connections to use (>100 not recommended)")
    download.add_argument("--retries", type=int, default=defs.RETRIES,
                          metavar="Retry Attempts",
                          help="How often to reconnect to Coub after connection loss "
                               "(<0 for infinite retries)")
    download.add_argument("--max-coubs", type=coub.positive_int,
                          default=defs.MAX_COUBS, metavar="Limit Quantity",
                          help="How many coub links to parse")

    # Format Selection
    formats = parser.add_argument_group("Format", gooey_options={'columns': 1})
    formats.add_argument("--v-quality", choices=["Best quality", "Worst quality"],
                         default=defs.QUALITY_LABEL[defs.V_QUALITY],
                         metavar="Video Quality", help="Which video quality to download")
    formats.add_argument("--a-quality", choices=["Best quality", "Worst quality"],
                         default=defs.QUALITY_LABEL[defs.A_QUALITY],
                         metavar="Audio Quality", help="Which audio quality to download")
    formats.add_argument("--v-max", choices=["med", "high", "higher"],
                         default=defs.V_MAX, metavar="Max. Video Quality",
                         help="Cap the max. video quality considered for download")
    formats.add_argument("--v-min", choices=["med", "high", "higher"],
                         default=defs.V_MIN, metavar="Min. Video Quality",
                         help="Cap the min. video quality considered for download")
    formats.add_argument("--aac", default=defs.AAC_LABEL[defs.AAC],
                         choices=["Only MP3", "No Bias", "Prefer AAC", "Only AAC"],
                         metavar="Audio Format", help="How much to prefer AAC over MP3")
    formats.add_argument("--special", choices=["None", "Share", "Video only", "Audio only"],
                         default=defs.SPECIAL_LABEL[(defs.SHARE, defs.V_ONLY, defs.A_ONLY)],
                         metavar="Special Formats", help="Use a special format selection")

    # Output
    output = parser.add_argument_group("Output", gooey_options={'columns': 1})
    output.add_argument("--output-list", type=os.path.abspath, widget="FileSaver",
                        default=defs.OUTPUT_LIST, metavar="Output to List",
                        gooey_options={'message': "Save link list"},
                        help="Save all parsed links in a list (no download)")
    output.add_argument("--path", type=os.path.abspath, default=defs.PATH,
                        widget="DirChooser", metavar="Output Directory",
                        help="Where to save downloaded coubs",
                        gooey_options={
                            'message': "Pick output destination",
                            'default_path': defs.PATH,
                        })
    output.add_argument("--merge-ext", default=defs.MERGE_EXT,
                        metavar="Output Container",
                        choices=["mkv", "mp4", "asf", "avi", "flv", "f4v", "mov"],
                        help="What extension to use for merged output files "
                             "(has no effect if no merge is required)")
    output.add_argument("--name-template", default=defs.NAME_TEMPLATE,
                        metavar="Name Template",
                        help=dedent(f"""\
                            Change the naming convention of output files

                            Special strings:
                              %id%        - coub ID (identifier in the URL)
                              %title%     - coub title
                              %creation%  - creation date/time
                              %community% - coub community
                              %channel%   - channel title
                              %tags%      - all tags (separated by _)

                            Other strings will be interpreted literally
                            This option has no influence on the file extension
                            """))

    # Advanced Options
    parser.set_defaults(
        verbosity=1,
        ffmpeg_path=defs.FFMPEG_PATH,
        coubs_per_page=defs.COUBS_PER_PAGE,   # allowed: 1-25
        tag_sep=defs.TAG_SEP,
        fallback_char=defs.FALLBACK_CHAR,
        write_method=defs.WRITE_METHOD,       # w -> overwrite, a -> append
        chunk_size=defs.CHUNK_SIZE,
    )

    args = parser.parse_args()

    # Exit only after parsing to not hinder GUI creation
    if defs.error:
        sys.exit(coub.ExitCodes.OPT)

    args.input = []
    args.input.extend([coub.mapped_input(u) for u in args.urls.split(",") if u])
    args.input.extend([i for i in args.ids.split(",") if i])
    args.input.extend([coub.LinkList(l) for l in args.lists.split(",") if l])
    args.input.extend([coub.Channel(c) for c in args.channels.split(",") if c])
    args.input.extend([coub.Tag(t) for t in args.tags.split(",") if t])
    args.input.extend([coub.Search(s) for s in args.searches.split(",") if s])
    args.input.extend([coub.Community(c) for c in args.communities.split(",") if c])
    args.input.extend([coub.Story(s) for s in args.stories.split(",") if s])
    if args.hot:
        args.input.append(coub.HotSection())
    if args.random:
        for _ in range(args.random):
            args.input.append(coub.RandomCategory())

    # Read archive content
    if args.archive and os.path.exists(args.archive):
        with open(args.archive, "r") as f:
            args.archive_content = {l.strip() for l in f}
    else:
        args.archive_content = set()
    # The default naming scheme is the same as using %id%
    # but internally the default value is None
    if args.name_template == "%id%":
        args.name_template = None
    # Defining whitespace or an empty string in the config isn't possible
    # Instead translate appropriate keywords
    if args.tag_sep == "space":
        args.tag_sep = " "
    if args.fallback_char is None:
        args.fallback_char = ""
    elif args.fallback_char == "space":
        args.fallback_char = " "

    return translate_to_cli(args)


if __name__ == '__main__':
    coub.opts = parse_cli()
    coub.main()
