import re


def replace_names(input_string, old_name, new_name):
    return re.sub(
        r"\[" + re.escape(old_name) + r"\]", "[" + new_name + "]", input_string
    )


def replace_nickname(input_string, nickname_old, nickname_new):
    return re.sub(r"\b" + re.escape(nickname_old) + r"\b", nickname_new, input_string)


def get_guild_name(input_string, tagOrder):
    match = re.search(r"\[(.*?)\]", input_string)
    if match and tagOrder == 1:
        return match.group(1)
    elif match and tagOrder == 2:
        return match.group(0)
    else:
        return None
