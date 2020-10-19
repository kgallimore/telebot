import re
# import git
from threading import Timer
from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from alphabet_detector import AlphabetDetector
from emoji import UNICODE_EMOJI
from functools import wraps
import mysql.connector as db
import logging
import os
import random
import func

ad = AlphabetDetector()
if not os.path.exists("config"):
    os.makedirs("config")
    File_object = open("config/db.conf", "a+")
    host = input("Database host: ")
    File_object.write("host=" + host + "\n")
    user = input("Database user: ")
    File_object.write("user=" + user + "\n")
    passwd = input("Database passwd: ")
    File_object.write("passwd=" + passwd + "\n")
    database = input("Database name: ")
    File_object.write("database=" + database)
    File_object.close()
    File_object = open("config/token.conf", "w+")
    token = input("Telegram token: ")
    while not re.match("[0-9]{9}:[a-zA-Z0-9_-]{35}", token):
        token = input("Invalid token. Telegram token: ")
    File_object.write(token)
    File_object.close()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = open('config/token.conf', 'r').read().replace("\n", "")
if not re.match("[0-9]{9}:[a-zA-Z0-9_-]{35}", TOKEN):
    input("The token seems to be an invalid format")
    exit(0)
message_counter = 0
users_talking = {}
cleared_users = []
recent_messages = {'verified': {}, 'enter': {}, 'giveaways': {}, "welcome": {}}
active_giveaway = False
site_tld = ''

File_object = open("config/db.conf", "r+")
db_lines = File_object.readlines()
db_host = db_lines[0].split("=", 1)[1].replace("\n", "").strip()
db_user = db_lines[1].split("=", 1)[1].replace("\n", "").strip()
db_pass = db_lines[2].split("=", 1)[1].replace("\n", "").strip()
db_db = db_lines[3].split("=", 1)[1].replace("\n", "").strip()
print("<" + db_host + ">")
print("<" + db_user + ">")
print("<" + db_pass + ">")
print("<" + db_db + ">")

if not os.path.exists("logs"):
    os.makedirs("logs")


def create_connection():
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = db.connect(
            host=db_host,
            user=db_user,
            passwd=db_pass,
            database=db_db
        )
    except error as e:
        print(e)
    return conn


def send_typing_action(function):
    """Sends typing action while processing func command."""

    @wraps(function)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return function(update, context, *args, **kwargs)

    return command_func


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    open("logs/error.txt", "w").write("\nupdate status: " + str(update) + "\nerror: " + str(context.error))


def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def delete_message(bot, chat_id, message_id):
    """Deletes a message"""
    try:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        print("[ERROR] Could not delete message " + str(message_id))


def send_message_delayed_delete(update, context, message, time):
    """Send a message and delete after 30 seconds"""
    msg = update.message.reply_text(message)
    # print('[INFO] Thirty second delete message and message id')
    Timer(time, delete_message, args=[context.bot, update.message.chat_id, msg.message_id]).start()


def delayed_delete(update, context, time):
    """Send a message and delete after 30 seconds"""
    # print('[INFO] Thirty second delete message and message id')
    Timer(time, delete_message, args=[context.bot, update.message.chat_id, update.message.message_id]).start()


def kick_user(update, context):
    if update.effective_user.id not in cleared_users:
        context.bot.kick_chat_member(chat_id=update.message.chat_id, user_id=update.effective_user.id)
    context.bot.send_message(chat_id=update.message.chat_id, text="User id `" + update.effective_user.id + "` has been banned", parse_mode="MarkdownV2")


def delayed_kick(update, context, time):
    Timer(time, kick_user, args=[update, context]).start()


def limit_messages(update, context, send_message, message_type, reply):
    chat_id = update.message.chat_id
    if str(chat_id) in recent_messages[message_type].keys() and recent_messages[message_type][str(chat_id)] is not None:
        # print("[INFO] Deleting message: " + str(recent_messages[message_type][str(chat_id)]))
        try:
            delete_message(context.bot, chat_id, recent_messages[message_type][str(chat_id)])
        except:
            print("Error deleting " + str(recent_messages[message_type][str(chat_id)]) + " in chat " + str(chat_id))
    if reply:
        message = update.message.reply_text(send_message)
    else:
        message = context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
    recent_messages[message_type][str(chat_id)] = message.message_id


def add_giveaway(update, context):
    """Function to add, remove, and participate in give aways"""
    if context.args and len(context.args) > 0:
        names = func.get_all_names(update.effective_message)
        user_id = update.effective_user.id
        chat_id = update.message.chat_id
        conn = create_connection()
        db_cursor = conn.cursor()
        details = ' '.join(context.args)[:100]
        sql = "SELECT * FROM giveaways WHERE user_id = %s AND chat_id = %s AND status = 'active'"
        db_cursor.execute(sql, (user_id, chat_id,))
        myresult = db_cursor.fetchall()
        if len(myresult) > 0:
            sql = "UPDATE giveaways SET giveaway_details = %s WHERE user_id = %s AND chat_id = %s AND status = 'status'"
            db_cursor.execute(sql, (details, user_id, chat_id,))
            send_message = 'Giveaway updated'
        else:
            sql = "INSERT INTO giveaways (user_id, chat_id, username, first_name, giveaway_details) VALUES (%s,%s,%s," \
                  "%s,%s) "
            db_cursor.execute(sql, (user_id, chat_id, names[0], names[1], details))
            send_message = 'Giveaway added'
        conn.commit()
        conn.close()
        update.message.reply_text(send_message)
    else:
        send_message_delayed_delete(update, context, 'Missing giveaway details', 30)
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def accept_user(update, context):
    global cleared_users
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        reply = update.message.reply_to_message
        if reply is not None:
            cleared_users += reply.from_user.id
            update.message.reply_text("User id `" + reply.from_user.id + "` will not be kicked", parse_mode="MarkdownV2")
        elif context.args is not None and check_int(context.args[0]):
            cleared_users += context.args[0]
            update.message.reply_text("User id `" + context.args[0] + "` will not be kicked", parse_mode="MarkdownV2")
        else:
            update.message.reply_text("Please either provide their user id or reply to one of their messages.")


def end_giveaway(update, context):
    """Choose 1 or more winners from a giveaway"""
    send_message = "The winner\(s\) is\(are\)"
    winners = []
    to_choose = 1
    x = 0
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    conn = create_connection()
    db_cursor = conn.cursor()
    sql = "SELECT participants.user_id FROM participants JOIN giveaways ON giveaways.giveaway_id = " \
          "participants.giveaway_id WHERE giveaways.user_id = %s AND giveaways.chat_id = %s and giveaways.status = " \
          "'active' ORDER BY RAND()"
    db_cursor.execute(sql, (user_id, chat_id,))
    participants_result = db_cursor.fetchall()
    if participants_result is None or len(participants_result) < 1:
        print(participants_result)
        update.message.reply_text('No active giveaway or no participants found')
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
        return
    if context.args and context.args is not [] and ''.join(context.args).strip().isdigit() and 1 < int(
            ''.join(context.args).strip()) < len(participants_result):
        to_choose = int(''.join(context.args).strip())
    print('[INFO] Choosing ' + str(to_choose) + 'winner(s)')
    while x < to_choose:
        print("[INFO] Choosing Winner " + str(x + 1))
        chosen = participants_result[random.randrange(len(participants_result))][0]
        if chosen not in winners:
            winners += [chosen]
            x += 1
    print('[INFO] Winners: ')
    print(winners)
    send_message += " \(out of " + str(len(participants_result)) + "\):"
    for winner in winners:
        name = func.get_username_from_chat_id(context.bot.getChat(winner))
        print(name)
        send_message += '\n[' + name + '](tg://user?id=' + str(winner) + ')'
        print(send_message)
    sql = "UPDATE giveaways SET status = %s WHERE status = 'active' AND chat_id = %s and user_id = %s"
    db_cursor.execute(sql, (str(winners), chat_id, user_id,))
    conn.commit()
    conn.close()
    context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message,
                             parse_mode="MarkdownV2")


def enter(update, context):
    """Quickly enter last giveaway"""
    global users_talking
    user_id = update.effective_user.id
    chat_id = update.message.chat_id
    users_talking[str(chat_id)] = []
    names = func.get_all_names(update.message)
    conn = create_connection()
    db_cursor = conn.cursor()
    sql = "SELECT giveaway_id, user_id, giveaway_details FROM giveaways WHERE status = 'active' and chat_id = %s"
    db_cursor.execute(sql, (chat_id,))
    giveaways_result = db_cursor.fetchall()
    if len(giveaways_result) == 0:
        send_message_delayed_delete(update, context, "No active giveaways", 30)
        return
    if context.args and len(context.args) > 0 and ''.join(context.args).isdigit():
        number = int(''.join(context.args)) - 1
        if 0 <= number < len(giveaways_result):
            giveaway_id = giveaways_result[number][0]
            giveaway_name = str(func.get_username_from_chat_id(context.bot.getChat(giveaways_result[number][1])))
            giveaway_details = giveaways_result[number][2]
        else:
            send_message_delayed_delete(update, context, "I don't think that giveaway exists.", 30)
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
            return
    else:
        sql = "SELECT settings.last_giveaway, giveaways.user_id, giveaway_details FROM settings join giveaways ON " \
              "settings.last_giveaway = giveaway_id WHERE settings.chat_id = %s AND giveaways.status = 'active' "
        db_cursor.execute(sql, (chat_id,))
        result = db_cursor.fetchone()
        if result is None or result[0] is None:
            send_message_delayed_delete(update, context, "No recent giveaway, or most recent giveaway closed.", 30)
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
            return
        giveaway_id = result[0]
        giveaway_name = str(func.get_username_from_chat_id(context.bot.getChat(result[1])))
        giveaway_details = result[2]
    sql = "SELECT * FROM participants WHERE giveaway_id = %s and chat_id = %s and user_id = %s"
    db_cursor.execute(sql, (giveaway_id, chat_id, user_id,))
    giveaways_result = db_cursor.fetchall()
    if len(giveaways_result) == 0:
        sql = "UPDATE settings SET last_giveaway = %s WHERE chat_id = %s"
        db_cursor.execute(sql, (giveaway_id, chat_id))
        conn.commit()
        sql = "INSERT INTO participants (giveaway_id, user_id, chat_id, username, first_name) VALUES (%s,%s,%s,%s,%s)"
        db_cursor.execute(sql, (giveaway_id, user_id, chat_id, names[0], names[1]))
        conn.commit()

        if names[0] is not None and names[0] is not '':
            name = names[0]
        else:
            name = names[1]
        sql = "SELECT * FROM participants WHERE giveaway_id = %s and chat_id = %s"
        db_cursor.execute(sql, (giveaway_id, chat_id,))
        giveaways_result = db_cursor.fetchall()
        message = "Use /enter to join " + name + " and " + str(len(
            giveaways_result)) + "others for a chance to win " + giveaway_name + "'s giveaway of " + giveaway_details
        limit_messages(update, context, message, 'enter', True)
    else:
        send_message_delayed_delete(update, context,
                             "Pretty sure you're already in this giveaway. (Or maybe one of us made a mistake!)", 30)
    conn.close()
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def new_message(update, context):
    """Run certain functions on new message"""
    if update.effective_user.id not in get_admin_ids(context.bot, update.message.chat_id):
        global users_talking
        user_id = str(update.effective_user.id)
        chat_id = str(update.effective_message.chat_id)
        if chat_id not in users_talking:
            users_talking[chat_id] = [user_id]
        elif user_id not in users_talking[chat_id]:
            users_talking[chat_id] += [user_id]
        if len(users_talking[chat_id]) > 7:
            users_talking[chat_id] = []
            send_message = get_giveaways(update, context)
            if send_message != "No active giveaways":
                limit_messages(update, context, send_message, 'giveaways', False)
    elif str(update.effective_user.id) == "649704620":
        delayed_delete(update, context, 120)


def giveaways(update, context):
    message = get_giveaways(update, context)
    if message == "No active giveaways":
        send_message_delayed_delete(update, context, message, 30)
    else:
        limit_messages(update, context, message, 'giveaways', True)
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def get_giveaways(update, context):
    """Returns a string with all current giveaways"""
    global users_talking
    number = 1
    # print('[INFO] Getting giveaways')
    chat_id = update.message.chat_id
    conn = create_connection()
    db_cursor = conn.cursor()
    users_talking[str(chat_id)] = []
    sql = "SELECT user_id, giveaway_details FROM giveaways WHERE status = 'active' and chat_id = %s"
    db_cursor.execute(sql, (chat_id,))
    myresult = db_cursor.fetchall()
    if len(myresult) > 0:
        send_message = "Current giveaways!\nUse '/enter [# of giveaway]' to enter!\n"
        for x in myresult:
            send_message += str(number) + '. ' + str(
                func.get_username_from_chat_id(context.bot.getChat(x[0]))) + ': ' + str(x[1]) + '\n'
            number += 1
    else:
        send_message = "No active giveaways"
    return send_message


def ban_user(update, context):
    """Bans the replied user with or without a reason"""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id) and reply is not None and \
            reply.from_user.id not in get_admin_ids(context.bot, update.message.chat_id):
        user_id_number = int(reply.from_user.id)
        try:
            context.bot.kick_chat_member(chat_id=reply.chat_id, user_id=user_id_number)
            send_message = func.get_username_from_message(reply) + " has been banned."
        except:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Cannot kick member")
            send_message = func.get_username_from_message(reply) + " has not been banned."
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def advert_warning(update, context):
    """Gives warning and deletes message if user is advertising without permission. Bans on second warning."""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id) and reply is not None and \
            reply.from_user.id not in get_admin_ids(context.bot, update.message.chat_id):
        conn = create_connection()
        db_cursor = conn.cursor()
        user_id_number = int(reply.from_user.id)
        chat_id = int(reply.chat_id)
        db_cursor.execute("SELECT services FROM verified WHERE chat_id = %s AND user_id = %s",
                          (update.message.chat_id, int(reply.from_user.id)))
        fetch = db_cursor.fetchone()
        if fetch is None:
            names = func.get_all_names(reply)
            db_cursor.execute("SELECT * FROM warnings WHERE user_id = %s AND chat_id = %s",
                              (user_id_number, chat_id))
            result_set = db_cursor.fetchall()
            if len(result_set) < 1:
                send_message = "@" + func.get_username_from_message(
                    reply) + ". You must be /verified in order to advertise. This is your ONLY warning!"
                db_cursor.execute("INSERT INTO warnings (chat_id, user_id, username, first_name, reason) VALUES (%s,"
                                  "%s,%s,%s, 'advert')",
                                  (chat_id, user_id_number, names[0], names[1]))
                conn.commit()
            else:
                try:
                    db_cursor.execute("INSERT INTO warnings (chat_id, user_id, username, first_name, reason) VALUES ("
                                      "%s,%s,%s,%s, 'advert')",
                                      (chat_id, user_id_number, names[0], names[1]))
                    conn.commit()
                    context.bot.kick_chat_member(chat_id=reply.chat_id, user_id=user_id_number)
                    send_message = func.get_username_from_message(reply) + " has been banned."
                except:
                    context.bot.send_message(chat_id=update.effective_message.chat_id, text="Cannot kick member")
                    send_message = func.get_username_from_message(reply) + " has not been banned."
            try:
                context.bot.delete_message(chat_id=reply.chat_id, message_id=reply.message_id)
            except:
                context.bot.send_message(chat_id=update.effective_message.chat_id, text="Cannot delete message")
        else:
            send_message = "User is verified"
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
        conn.close()
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def verify(update, context):
    """Adds user from reply message to verified list"""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if reply is not None:
            conn = create_connection()
            db_cursor = conn.cursor()
            user_id_number = int(reply.from_user.id)
            chat_id = int(reply.chat_id)
            db_cursor.execute("SELECT services FROM verified WHERE chat_id = %s and user_id = %s",
                              (chat_id, user_id_number))
            result = db_cursor.fetchall()
            details = ''
            if context.args and context.args[0] != '':
                details = ' '.join(context.args)
            if result is None or len(result) == 0:
                names = func.get_all_names(reply)
                input_names = func.get_all_names(update.message)
                db_cursor.execute(
                    "INSERT INTO verified (chat_id, user_id, services, username, first_name, input_id, "
                    "input_username, input_first_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        chat_id, user_id_number, details[:25], names[0], names[1], update.effective_user.id,
                        input_names[0],
                        input_names[1]))
                conn.commit()
                update.message.reply_text("Verified services: " + details[:25] + "\n Feel free to sign up to be a "
                                                                                 "merchant on https://" + site_tld)
            else:
                if 'remove' in details.lower().strip():
                    db_cursor.execute("DELETE FROM verified where chat_id = %s and user_id = %s",
                                      (chat_id, user_id_number))
                    conn.commit()
                    conn.close()
                    update.message.reply_text("Removed verified user")
                else:
                    db_cursor.execute("UPDATE verified SET services = %s where chat_id = %s and user_id = %s",
                                      (details[:25], chat_id, user_id_number))
                    conn.commit()
                    conn.close()
                    update.message.reply_text("Updated services: " + details[:25] + "\n Feel free to sign up to be a "
                                                                                    "merchant on "
                                                                                    "https://" + site_tld)
    else:
        if context.args[0].lower() == "help":
            send_message = "In a reply to the user in question list the services they are verified for."
        else:
            send_message = "For security please use this command in a reply to the user in question"
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def verified(update, context):
    reply = update.message.reply_to_message
    conn = create_connection()
    db_cursor = conn.cursor()
    if reply is None:
        db_cursor.execute("SELECT user_id, services FROM verified WHERE chat_id = %s", (update.message.chat_id,))
        result = db_cursor.fetchall()
        if context.args and context.args[0] is not None and context.args[0] is not "" and func.is_int(context.args[0]):
            adjusted_number = int(context.args[0]) - 1
            if len(result) > adjusted_number >= 0:
                name = func.get_username_from_chat_id(context.bot.getChat(result[adjusted_number][0]))
                send_message = "[" + name + "](tg://user?id=" + str(result[adjusted_number][0]) + ")"
                context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message,
                                         parse_mode="MarkdownV2")
            else:
                update.message.reply_text("Out of range")
        else:
            send_message = "**Use '/verified [#]' to mention the user to be sure it's not an impostor**  \n"
            number = 1
            for row in result:
                username = func.get_username_from_chat_id(context.bot.getChat(row[0]))
                send_message += str(number) + "." + username + ": " + row[1] + "  \n"
                number += 1
            if send_message is not "":
                pass
            else:
                send_message = "No one is verified. Get started with /verify help"
            limit_messages(update, context, send_message, 'verified', True)
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    else:
        if reply.from_user.id in get_admin_ids(context.bot, update.message.chat_id):
            update.message.reply_text("User is admin")
        else:
            db_cursor.execute("SELECT services, user_id FROM verified WHERE chat_id = %s AND user_id = %s",
                              (update.message.chat_id, int(reply.from_user.id)))
            fetch = db_cursor.fetchone()
            if fetch is not None:
                name = func.get_username_from_chat_id(context.bot.getChat(fetch[1]))
                send_message_delayed_delete(update, context, name + "'s services: " + fetch[0], 30)
            else:
                send_message_delayed_delete(update, context, "User is not verified", 30)
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    conn.close()


def removed_user(update, context):
    conn = create_connection()
    db_cursor = conn.cursor()
    chat_id = update.message.chat_id
    user_id = update.message.left_chat_member.id
    db_cursor.execute("DELETE FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
    db_cursor.execute('DELETE FROM participants WHERE chat_id = %s and user_id = %s', (chat_id, user_id))
    db_cursor.execute('DELETE FROM telegram.verified WHERE chat_id = %s and user_id = %s', (chat_id, user_id))
    conn.commit()
    conn.close()


def set_store(update, context):
    """Sets the output of /stores /list and /store"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        conn = create_connection()
        db_cursor = conn.cursor()
        if context.args and context.args[0] is not None:
            details = ' '.join(context.args)[:1450]
            db_cursor.execute("SELECT * FROM settings WHERE chat_id = %s",
                              (update.message.chat_id,))
            fetch = db_cursor.fetchone()
            if fetch is None:
                db_cursor.execute("INSERT INTO settings (chat_id, store) VALUES (%s,%s)",
                                  (update.message.chat_id, details,))
            else:
                db_cursor.execute("UPDATE settings SET store = %s WHERE chat_id = %s",
                                  (details, update.message.chat_id,))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Store set")
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")
        conn.close()


def show_store(update, context):
    """Shows store"""
    conn = create_connection()
    db_cursor = conn.cursor()
    db_cursor.execute("SELECT store FROM settings WHERE chat_id = %s",
                      (update.message.chat_id,))
    fetch = db_cursor.fetchone()
    if fetch is not None and fetch[0] is not None:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=fetch[0])
    else:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text="Admin has yet to use /setstore")
    conn.close()


def set_rules(update, context):
    """Sets the output of /rules"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if context.args and context.args[0] is not None:
            conn = create_connection()
            db_cursor = conn.cursor()
            details = ' '.join(context.args)[:1450]
            db_cursor.execute("SELECT * FROM settings WHERE chat_id = %s",
                              (update.message.chat_id,))
            fetch = db_cursor.fetchone()
            if fetch is None:
                db_cursor.execute("INSERT INTO settings (chat_id, rules) VALUES (%s,%s)",
                                  (update.message.chat_id, details,))
            else:
                db_cursor.execute("UPDATE settings SET rules = %s WHERE chat_id = %s",
                                  (details, update.message.chat_id,))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Rules set")
            conn.close()
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")


def show_rules(update, context):
    """Sets the output of /rules"""
    conn = create_connection()
    db_cursor = conn.cursor()
    db_cursor.execute("SELECT rules FROM settings WHERE chat_id = %s",
                      (update.message.chat_id,))
    fetch = db_cursor.fetchone()
    if fetch is not None and fetch[0] is not None:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=fetch[0])
    else:
        context.bot.send_message(chat_id=update.effective_message.chat_id, text="Admin has yet to use /setrules")
    conn.close()


def server_giveaway(update, context):
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        conn = create_connection()
        db_cursor = conn.cursor()
        chat_id = update.message.chat_id
        db_cursor.execute("SELECT user_id FROM users WHERE chat_id = %s ORDER BY RAND() LIMIT 1", (chat_id,))
        fetch = db_cursor.fetchone()
        if fetch is not None:
            winner = fetch[0]
            name = func.get_username_from_chat_id(context.bot.getChat(winner))
            send_message = "The winner is: [" + name + "](tg://user?id=" + str(winner) + ")\!"
            context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message,
                                     parse_mode="MarkdownV2")
        conn.close()
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def set_welcome(update, context):
    """Sets the welcome message"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if context.args and context.args[0] is not None:
            conn = create_connection()
            db_cursor = conn.cursor()
            details = update.message.text[12:]
            # details.replace('/n', )
            db_cursor.execute("SELECT * FROM settings WHERE chat_id = %s",
                              (update.message.chat_id,))
            fetch = db_cursor.fetchone()
            if fetch is None:
                db_cursor.execute("INSERT INTO settings (chat_id, welcome) VALUES (%s,%s)",
                                  (update.message.chat_id, details,))
            else:
                db_cursor.execute("UPDATE settings SET welcome = %s WHERE chat_id = %s",
                                  (details, update.message.chat_id,))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Welcome set")
            conn.close()
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")


def new_user(update, context):
    """Shows welcome message"""
    for new_user_obj in update.message.new_chat_members:
        chat_id = update.message.chat_id
        user_id = new_user_obj['id']
        new_user = ''
        username = ''
        first_name = ''
        if new_user_obj['username'] and not ad.is_latin(new_user_obj['username']):
            for letter in new_user_obj['username']:
                try:
                    if not is_emoji(letter) and not ad.is_latin(letter):
                        delayed_kick(update,context, 30)
                        send_message_delayed_delete(update,context,new_user_obj['username'] +" you will be banned in 30 seconds due to having foreign characters in your username. An admin must /accept you.", 30)
                        return
                except:
                    print("Had trouble detecting letter")
            username = "@" + new_user_obj['username']
            new_user = username
        if new_user_obj['first_name'] and not ad.is_latin(new_user_obj['first_name']):
            for letter in new_user_obj['first_name']:
                try:
                    if not is_emoji(letter) and not ad.is_latin(letter):
                        delayed_kick(update, context, 30)
                        send_message_delayed_delete(update, context, new_user_obj[
                            'first_name'] + " you will be banned in 30 seconds due to having foreign characters in your first name. An admin must /accept you.",
                                                    30)
                        return
                except:
                    print("Had trouble detecting letter")
            first_name = new_user_obj['first_name']
            new_user = first_name
        conn = create_connection()
        db_cursor = conn.cursor()
        db_cursor.execute("SELECT welcome, store FROM settings WHERE chat_id = %s",
                          (chat_id,))
        fetch = db_cursor.fetchone()
        if fetch is not None and fetch and fetch[0] is not None and str(fetch[0]).lower() is not 'false':
            welcome = fetch[0].replace("{username}", new_user).replace("{store}", fetch[1]).replace("{id}", user_id)
            limit_messages(update, context, welcome, "welcome", False)
            # context.bot.sendMessage(chat_id=chat_id,text=welcome,parse_mode='Markdown')
        if not new_user_obj.is_bot:
            db_cursor.execute("INSERT INTO users (chat_id, user_id, username, first_name) values (%s,%s,%s,%s)",
                              (chat_id, user_id, username, first_name))
            conn.commit()
        conn.close()


def show_welcome(update, context):
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        chat_id = update.message.chat_id
        conn = create_connection()
        db_cursor = conn.cursor()
        db_cursor.execute("SELECT welcome, store FROM settings WHERE chat_id = %s",
                          (chat_id,))
        fetch = db_cursor.fetchone()
        if fetch is not None and fetch and fetch[0] is not None and str(fetch[0]).lower() is not 'false':
            welcome = fetch[0].replace("{store}", fetch[1])
            limit_messages(update, context, welcome, "welcome", False)
        else:
            limit_messages(update, context, "No welcome set", "welcome", False)
        conn.close()


def show_help(update, context):
    """"Lists commands and gives short summaries"""
    if context.args and context.args[0].lower == "setwelcome":
        send_message = "{username}: new username.\n{store}: adds output of /store.\nSet to 'false' to disable"
    else:
        send_message = "/addgiveaway <args>: Add a giveaway\n"
        send_message += "/endgiveaway <args>: Choose a <args> number of winners, default 1\n"
        send_message += "/enter <args>: Enter a giveaway, default most recently entered giveaway\n"
        send_message += "/giveways : List all active givaways\n"
        send_message += "/servergiveaway: Randomly selects a chat member.\n"
        send_message += "/help : Shows the command list\n"
        send_message += "/list | /store | /stores : Links or lists a list of services / store page.\n"
        send_message += "/verified : Lists verified sellers, aloso checks if user in replied message is verified.\n"
        if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
            send_message += "~~For admins only~~\n"
            send_message += "/ad : Warns user for advertising w/o permission. Bans on second warning.\n"
            send_message += "/accept <args>: Prevents user from getting kicked. Reply to their message or provide their id\n"
            send_message += "/ban : Bans user\n"
            send_message += "/setrules <args>: Sets output for /rules\n"
            send_message += "/setstore <args>: Sets output for /list /store /stores\n"
            send_message += "/setwelcome <args>: Sets the welcome message. /help setwelcome for special notes\n"
            send_message += "/showwelcome <args>: Shows the welcome message.\n"
            send_message += "/update: WIP Pulls latest update from github\n"
            send_message += "/verify <args>: Adds replied user to verified list, arguments are their services.\n"
    context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)


def warn(update, context):
    """Assigns warning to user and kicks after 3 warnings"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        reply = update.message.reply_to_message
        reason = ""
        send_message = "@" + func.get_username_from_message(
            reply)
        if context.args and context.args[0] is not None:
            reason = ' '.join(context.args)[:150]
        if reply is not None and reply.from_user.id not in get_admin_ids(context.bot, update.message.chat_id):
            conn = create_connection()
            db_cursor = conn.cursor()
            user_id_number = int(reply.from_user.id)
            chat_id = int(reply.chat_id)
            names = func.get_all_names(reply)
            db_cursor.execute("SELECT * FROM warnings WHERE user_id = %s AND chat_id = %s", (user_id_number, chat_id))
            fetch = db_cursor.fetchall()
            print(len(fetch))
            if len(fetch) == 0:
                send_message += " has been warned 1/3 times."
            elif len(fetch) == 1:
                send_message += " has been warned 2/3 times."
            elif len(fetch) == 2:
                try:
                    context.bot.kick_chat_member(chat_id=reply.chat_id, user_id=user_id_number)
                    send_message = func.get_username_from_message(reply) + " has 3/3 warnings and has been banned."
                except:
                    context.bot.send_message(chat_id=update.effective_message.chat_id, text="Cannot kick member")
                    send_message = func.get_username_from_message(reply) + " has 3/3 warnings but could not be banned."
            if reason is not "":
                send_message += " Reason: " + reason
            db_cursor.execute(
                "INSERT INTO warnings (chat_id, user_id, username, first_name, reason) VALUES (%s,%s,%s,%s,%s)",
                (chat_id, user_id_number, names[0], names[1], reason))
            conn.commit()
            context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
            conn.close()
    context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)


def update_self(update, context):
    pass
    """if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if os.path.isdir('./temp/'):
            shutil.rmtree('./temp')
        git.Repo.clone_from('https://github.com/trenchguns/telebot.git', './temp')
        for f in os.listdir('./temp/'):
            if os.path.isfile(f) and f is not '.gitignore':
                print("Moving " + str(f))
                shutil.move(os.path.join('./temp/', f), os.path.join('./', f))
            elif os.path.isdir(f) and f is not '.git':
                print("In directory: " + f)
                for rf in os.listdir('./temp/' + f):
                    print('./temp/' + str(f) + str(rf))
                    if os.path.isfile('./temp/' + f + '/' + rf):
                        print("Moving " + str(rf))
                        shutil.move(os.path.join('./temp/' + f, rf), os.path.join('./' + f, rf))
        shutil.rmtree('./temp')
        os.execl("run.sh", "run.sh")"""


def exec_sql_file(cursor, sql_file):
    print("[INFO] Executing SQL script file: " + sql_file)
    statement = ""
    for line in open(sql_file):
        if re.match(r'--', line):  # ignore sql comment lines
            continue
        if not re.search(r';$', line):  # keep appending lines that don't end in ';'
            statement = statement + line
        else:  # when you get a line ending in ';' then exec statement and reset for next statement
            statement = statement + line
            # print "\n\n[DEBUG] Executing SQL statement:\n%s" % (statement)
            try:
                cursor.execute(statement)
            except Exception as e:
                print("[WARN] MySQLError during execute statement \n\tArgs:" + str(e.args))

            statement = ""


def is_emoji(s):
    count = 0
    for emoji in UNICODE_EMOJI:
        count += s.count(emoji)
        if count > 1:
            return False
    return bool(count)

def check_int(s):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()


def main():
    conn = create_connection()
    db_cursor = conn.cursor()
    exec_sql_file(db_cursor, 'database.sql')
    conn.commit()
    conn.close()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("addgiveaway", add_giveaway))
    dp.add_handler(CommandHandler("accept", accept_user))
    dp.add_handler(CommandHandler("servergiveaway", server_giveaway))
    dp.add_handler(CommandHandler("endgiveaway", end_giveaway))
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(CommandHandler("giveaways", giveaways))
    dp.add_handler(CommandHandler("help", show_help))
    dp.add_handler(CommandHandler("rules", show_rules))
    dp.add_handler(CommandHandler("list", show_store))
    dp.add_handler(CommandHandler("store", show_store))
    dp.add_handler(CommandHandler("stores", show_store))
    dp.add_handler(CommandHandler("showwelcome", show_welcome))
    dp.add_handler(CommandHandler("verified", verified))
    dp.add_handler(CommandHandler("ad", advert_warning))
    dp.add_handler(CommandHandler("ban", ban_user))
    dp.add_handler(CommandHandler("setrules", set_rules))
    dp.add_handler(CommandHandler("setstore", set_store))
    dp.add_handler(CommandHandler("setwelcome", set_welcome))
    dp.add_handler(CommandHandler("update", update_self))
    dp.add_handler(CommandHandler("verify", verify))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_user))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, removed_user))
    dp.add_handler(MessageHandler(Filters.text, new_message))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
