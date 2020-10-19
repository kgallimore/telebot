import string
printable = set(string.printable)

def get_username_from_update(update):
    """Return the possible username or none if fails"""
    if update.message.from_user.username is not None:
        username = update.message.from_user.username
    elif update.message.from_user.first_name is not None:
        username = update.message.from_user.first_name
    else:
        username = None
    return username


def get_username_from_chat_id(chat_id):
    """Return the possible username or none if fails"""
    if chat_id.first_name is not None:
        username = chat_id.first_name
    elif chat_id.username is not None:
        username = chat_id.username
    else:
        username = None
    return username


def get_username_from_message(message):
    """Return the possible username or none if fails"""
    if message.from_user.username is not None:
        username = message.from_user.username
    elif message.from_user.first_name is not None:
        username = message.from_user.first_name
    else:
        username = None
    return username


def get_all_names(message):
    """Return array of both names"""
    clean_user = ""
    clean_first = ""
    if message.from_user.username is not None:
        username = str(message.from_user.username)
        clean_user = ''.join(filter(lambda x: x in printable, username))
    if message.from_user.first_name is not None:
        first_name = message.from_user.first_name
        clean_first = ''.join(filter(lambda x: x in printable, first_name))
    return [clean_user, clean_first]


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
