import re
from typing import Any, List, Match

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

from zerver.lib.markdown.priorities import PREPROCESSOR_PRIORITES

# There is a lot of duplicated code between this file and
# help_settings_links.py. So if you're making a change here consider making
# it there as well.

REGEXP = re.compile(r"\{relative\|(?P<link_type>.*?)\|(?P<key>.*?)\}")

gear_info = {
    # The pattern is key: [name, link]
    # key is from REGEXP: `{relative|gear|key}`
    # name is what the item is called in the gear menu: `Select **name**.`
    # link is used for relative links: `Select [name](link).`
    "manage-streams": ["Manage streams", "/#streams/subscribed"],
    "settings": ["Personal Settings", "/#settings/profile"],
    "organization-settings": ["Organization settings", "/#organization/organization-profile"],
    "integrations": ["Integrations", "/integrations"],
    "stats": ["Usage statistics", "/stats"],
    "plans": ["Plans and pricing", "/plans"],
    "billing": ["Billing", "/billing"],
    "invite": ["Invite users", "/#invite"],
    "about-zulip": ["About Zulip", "/#about-zulip"],
}

gear_instructions = """
1. Click on the **gear** (<i class="fa fa-cog"></i>) icon in the upper
   right corner of the web or desktop app.

1. Select {item}.
"""


def gear_handle_match(key: str) -> str:
    if relative_help_links:
        item = f"[{gear_info[key][0]}]({gear_info[key][1]})"
    else:
        item = f"**{gear_info[key][0]}**"
    return gear_instructions.format(item=item)


stream_info = {
    "all": ["All streams", "/#streams/all"],
    "subscribed": ["Subscribed streams", "/#streams/subscribed"],
}

stream_instructions_no_link = """
1. Click on the **gear** (<i class="fa fa-cog"></i>) icon in the upper
   right corner of the web or desktop app.

1. Click **Manage streams**.
"""


def stream_handle_match(key: str) -> str:
    if relative_help_links:
        return f"1. Go to [{stream_info[key][0]}]({stream_info[key][1]})."
    if key == "all":
        return stream_instructions_no_link + "\n\n1. Click **All streams** in the upper left."
    return stream_instructions_no_link


LINK_TYPE_HANDLERS = {
    "gear": gear_handle_match,
    "stream": stream_handle_match,
}


class RelativeLinksHelpExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:
        """Add RelativeLinksHelpExtension to the Markdown instance."""
        md.registerExtension(self)
        md.preprocessors.register(
            RelativeLinks(), "help_relative_links", PREPROCESSOR_PRIORITES["help_relative_links"]
        )


relative_help_links: bool = False


def set_relative_help_links(value: bool) -> None:
    global relative_help_links
    relative_help_links = value


class RelativeLinks(Preprocessor):
    def run(self, lines: List[str]) -> List[str]:
        done = False
        while not done:
            for line in lines:
                loc = lines.index(line)
                match = REGEXP.search(line)

                if match:
                    text = [self.handleMatch(match)]
                    # The line that contains the directive to include the macro
                    # may be preceded or followed by text or tags, in that case
                    # we need to make sure that any preceding or following text
                    # stays the same.
                    line_split = REGEXP.split(line, maxsplit=0)
                    preceding = line_split[0]
                    following = line_split[-1]
                    text = [preceding, *text, following]
                    lines = lines[:loc] + text + lines[loc + 1 :]
                    break
            else:
                done = True
        return lines

    def handleMatch(self, match: Match[str]) -> str:
        return LINK_TYPE_HANDLERS[match.group("link_type")](match.group("key"))


def makeExtension(*args: Any, **kwargs: Any) -> RelativeLinksHelpExtension:
    return RelativeLinksHelpExtension(*args, **kwargs)
