from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# from alphabet_detector import AlphabetDetector
from tempfile import NamedTemporaryFile
from functools import wraps
import logging
import os
import random
import func
import sqlite3
from _sqlite3 import Error

# ad = AlphabetDetector()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = open('config/token.conf', 'r').read().replace("\n", "")
tempfile = NamedTemporaryFile(delete=False)
giveaways = {}
most_recent_giveaway = ''
message_counter = 0
users_talking = []
active_giveaway = False
main_db_file = "db.db"

if not os.path.exists("logs"):
    os.makedirs("logs")


def create_connection(db_file):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    open("logs/error.txt", "w").write("\nupdate status: " + str(update) + "\nerror: " + str(context.error))


def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def giveaway(update, context):
    """Function to add, remove, and participate in give aways"""
    pass


"""    global most_recent_giveaway
    send_message = ''
    username = 'Error'
    if update.message.from_user.username is not None:
        username = update.message.from_user.username
    elif update.message.from_user.first_name is not None:
        username = update.message.from_user.first_name
    if context.args and context.args[0] != '':
        if username in giveaways and context.args[0].lower().strip() == 'done':
            winner = random.randrange(len(giveaways[username]['participants']))
            update.message.reply_text('The winner is: @' + giveaways[username]['participants'][winner])
            del giveaways[username]
        elif context.args[0] in giveaways:
            if username not in giveaways[context.args[0]]['participants']:
                giveaways[context.args[0]]['participants'] += [username]
                most_recent_giveaway = context.args[0]
                sql = "INSERT INTO participants (name, giveaway_name, giveaway_id) VALUES (%s, %s, %s)"
                val = (username, context.args[0], giveaways[context.args[0]])
                #mycursor.execute(sql, val)
                #db.commit()
                update.message.reply_text(
                    "Added\nUse /enter to join " + username + ' in ' + context.args[0] + "'s giveaway!")
            else:
                update.message.reply_text("Already participating")
        else:
            details = ' '.join(context.args)
            sql = "INSERT INTO giveaways (host, name) VALUES (%s, %s)"
            val = (username, details[:20])
            mycursor.execute(sql, val)
            db.commit()
            giveaways[username] = {'giveawayname': details[:20], 'participants': []}
    else:
        send_message = 'Current giveaways!\nUse /giveaways [Giveaway host name] to enter!\n'
        for item in giveaways:
            send_message += item + ':' + giveaways[item]['giveawayname'] + '\n'
        update.message.reply_text(send_message)"""


def enter(update, context):
    """Quickly enter last giveaway"""
    username = func.get_username_from_update(update)
    if username is not None:
        if username not in giveaways[most_recent_giveaway]['participants']:
            giveaways[most_recent_giveaway]['participants'] += [username]
            update.message.reply_text("Added")
        else:
            update.message.reply_text("Already participating")


def new_message(update, context):
    """Run certain functions on new message"""
    if active_giveaway:
        global message_counter, users_talking
        username = func.get_username_from_update(update)
        if username is not None:
            if username not in users_talking:
                users_talking += [username]
            if len(users_talking) > 7:
                users_talking = []
                send_message = get_giveaways()
                context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
            else:
                message_counter += 1


def get_giveaways():
    """Returns a string with all current giveaways"""
    """number = 1
    sql = "SELECT * FROM giveaways WHERE status = active"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if len(myresult) > 0:
        send_message = "Current giveaways!\nUse '/enter [# of giveaway]' to enter!\n"
        for x in myresult:
            send_message += str(number) + '. ' + x[1] + ': ' + x[2] + '\n'
            number += 1
    else:
        send_message = "No active giveaways"
    db.commit()
    return send_message"""
    pass


def ban_user(update, context):
    """Bans the replied user with or without a reason"""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot,
                                                 update.message.chat_id) and reply is not None and reply.from_user.id not in get_admin_ids(
        context.bot, update.message.chat_id):
        user_id_number = int(reply.from_user.id)
        chat_id = int(reply.chat_id)
        try:
            context.bot.kick_chat_member(chat_id=reply.chat_id, user_id=user_id_number)
            send_message = func.get_username_from_message(reply) + " has been banned."
        except:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Cannot kick member")
            send_message = func.get_username_from_message(reply) + " has not been banned."
        context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)


def advert_warning(update, context):
    """Gives warning and deletes message if user is advertising without permission. Bans on second warning."""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot,
                                                 update.message.chat_id) and reply is not None and reply.from_user.id not in get_admin_ids(
        context.bot, update.message.chat_id):
        with create_connection(main_db_file) as conn:
            mycursor = conn.cursor()
            user_id_number = int(reply.from_user.id)
            chat_id = int(reply.chat_id)
            mycursor.execute("SELECT services FROM verified WHERE chat_id = %s AND user_id = %s" %
                             (update.message.chat_id, int(reply.from_user.id)))
            fetch = db.fetchone()
            if fetch is None:
                names = func.get_all_names(reply)
                db.execute("SELECT * FROM warnings WHERE user_id = %s AND chat_id = %s" % (user_id_number, chat_id,))
                result_set = db.fetchall()
                if len(result_set) < 1:
                    send_message = "@" + func.get_username_from_message(
                        reply) + ". You must be /verified in order to advertise. This is your ONLY warning!"
                    db.execute("INSERT INTO warnings (chat_id, user_id, username, first_name) VALUES (%s,%s,%s,%s)" %
                               (chat_id, user_id_number, names[0], names[1]))
                    db.commit()
                else:
                    try:
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


def verify(update, context):
    """Adds user from reply message to verified list"""
    reply = update.message.reply_to_message
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if reply is not None:
            with create_connection(main_db_file) as conn:
                mycursor = conn.cursor()
                user_id_number = int(reply.from_user.id)
                chat_id = int(reply.chat_id)
                mycursor.execute("SELECT services FROM verified WHERE chat_id = %s and user_id = %s" %
                                 (chat_id, user_id_number))
                result = mycursor.fetchall()
                details = ''
                if context.args and context.args[0] != '':
                    details = ' '.join(context.args)
                if result is None or len(result) == 0:
                    names = func.get_all_names(reply)
                    input_names = func.get_all_names(update.message)
                    mycursor.execute(
                        "INSERT INTO verified (chat_id, user_id, services, username, first_name, input_id, input_username, input_first_name) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)" %
                        (chat_id, user_id_number, details[:25], names[0], names[1], update.effective_user.id,
                         input_names[0],
                         input_names[1]))
                    db.commit()
                    update.message.reply_text("Verified services: " + details[:25])
                else:
                    mycursor.execute("UPDATE verified SET services = %s where chat_id = %s and user_id = %s" %
                                     (details[:25], chat_id, user_id_number))
                    db.commit()
                    update.message.reply_text("Updated services: " + details[:25])
        else:
            if context.args[0].lower() == "help":
                send_message = "In a reply to the user in question list the services they are verified for."
            else:
                send_message = "For security please use this command in a reply to the user in question"
            context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)


def verified(update, context):
    reply = update.message.reply_to_message
    with create_connection(main_db_file) as conn:
        mycursor = conn.cursor()
        if reply is None:
            mycursor.execute("SELECT user_id, services FROM verified WHERE chat_id = %s" % (update.message.chat_id,))
            result = mycursor.fetchall()
            if context.args and context.args[0] is not None and context.args[0] is not "" and func.is_int(
                    context.args[0]):
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
                context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)
        else:
            if reply.from_user.id in get_admin_ids(context.bot, update.message.chat_id):
                update.message.reply_text("User is admin")
            else:
                mycursor.execute("SELECT services FROM verified WHERE chat_id = %s AND user_id = %s" %
                                 (update.message.chat_id, int(reply.from_user.id)))
                fetch = mycursor.fetchone()
                if fetch is not None:
                    update.message.reply_text("Services: " + fetch[0])
                else:
                    update.message.reply_text("User is not verified")


def set_store(update, context):
    """Sets the output of /stores /list and /store"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if context.args and context.args[0] is not None:
            with create_connection(main_db_file) as conn:
                mycursor = conn.cursor()
                details = ' '.join(context.args)[:1450]
                mycursor.execute("SELECT * FROM settings WHERE chat_id = %s" %
                                 (update.message.chat_id,))
                fetch = mycursor.fetchone()
                if fetch is None:
                    mycursor.execute("INSERT INTO settings (chat_id, store) VALUES (%s,%s)" %
                                     (update.message.chat_id, details,))
                else:
                    mycursor.execute("UPDATE settings SET store = %s WHERE chat_id = %s" %
                                     (details, update.message.chat_id,))
                db.commit()
                context.bot.send_message(chat_id=update.effective_message.chat_id, text="Store set")
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")


def show_store(update, context):
    """Shows store"""
    with create_connection(main_db_file) as conn:
        mycursor = conn.cursor()
        mycursor.execute("SELECT store FROM settings WHERE chat_id = %s" %
                         (update.message.chat_id,))
        fetch = mycursor.fetchone()
        if fetch is not None and fetch[0] is not None:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text=fetch[0])
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Admin has yet to use /setstore")


def set_rules(update, context):
    """Sets the output of /rules"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if context.args and context.args[0] is not None:
            with create_connection(main_db_file) as conn:
                mycursor = conn.cursor()
                details = ' '.join(context.args)[:1450]
                mycursor.execute("SELECT * FROM settings WHERE chat_id = %s" %
                                 (update.message.chat_id,))
                fetch = mycursor.fetchone()
                if fetch is None:
                    mycursor.execute("INSERT INTO settings (chat_id, rules) VALUES (%s,%s)" %
                                     (update.message.chat_id, details,))
                else:
                    mycursor.execute("UPDATE settings SET rules = %s WHERE chat_id = %s" %
                                     (details, update.message.chat_id,))
                db.commit()
                context.bot.send_message(chat_id=update.effective_message.chat_id, text="Rules set")
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")


def show_rules(update, context):
    """Sets the output of /rules"""
    with create_connection(main_db_file) as conn:
        mycursor = conn.cursor()
        mycursor.execute("SELECT rules FROM settings WHERE chat_id = %s" %
                         (update.message.chat_id,))
        fetch = mycursor.fetchone()
        if fetch is not None and fetch[0] is not None:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text=fetch[0])
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Admin has yet to use /setrules")


def set_welcome(update, context):
    """Sets the welcome message"""
    if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        if context.args and context.args[0] is not None:
            with create_connection(main_db_file) as conn:
                mycursor = conn.cursor()
                details = ' '.join(context.args)[:1450]
                mycursor.execute("SELECT * FROM settings WHERE chat_id = %s" %
                                 (update.message.chat_id,))
                fetch = mycursor.fetchone()
                if fetch is None:
                    mycursor.execute("INSERT INTO settings (chat_id, welcome) VALUES (%s,%s)" %
                                     (update.message.chat_id, details,))
                else:
                    mycursor.execute("UPDATE settings SET welcome = %s WHERE chat_id = %s" %
                                     (details, update.message.chat_id,))
                db.commit()
                context.bot.send_message(chat_id=update.effective_message.chat_id, text="Welcome set")
        else:
            context.bot.send_message(chat_id=update.effective_message.chat_id, text="Please provide arguments")


def show_welcome(update, context):
    with create_connection(main_db_file) as conn:
        mycursor = conn.cursor()
        for new_user_obj in update.message.new_chat_members:
            chat_id = update.message.chat_id
            mycursor.execute("SELECT welcome, store FROM settings WHERE chat_id = %s"
                             % (chat_id,))
            fetch = mycursor.fetchone()
            if fetch is not None and fetch[0] is not None and fetch[0].lower() is not 'false':
                try:
                    new_user = "@" + new_user_obj['username']
                except Exception as e:
                    new_user = new_user_obj['first_name']
                context.bot.sendMessage(chat_id=chat_id,
                                        text=fetch[0].replace("{username}", new_user).replace("{store}", fetch[1]),
                                        parse_mode='Markdown')
            # else:
            # context.bot.send_message(chat_id=update.effective_message.chat_id, text="Welcome " + inline + "!")


def show_help(update, context):
    """"Lists commands and gives short summaries"""
    if context.args and context.args[0].lower == "setwelcome":
        send_message = "{username}: new username.\n{store}: adds output of /store.\nSet to 'false' to disable"
    else:
        send_message = "/enter : WIP\n"
        send_message += "/giveways : WIP\n"
        send_message += "/help : Shows the command list\n"
        send_message += "/list | /store | /stores : Links or lists a list of services / store page.\n"
        send_message += "/verified : Lists verified sellers, aloso checks if user in replied message is verified.\n"
        if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
            send_message += "~~For admins only~~\n"
            send_message += "/ad : Warns user for advertising w/o permission. Bans on second warning.\n"
            send_message += "/ban : Bans user\n"
            send_message += "/setrules <args>: Sets output for /rules\n"
            send_message += "/setstore <args>: Sets output for /list /store /stores\n"
            send_message += "/setwelcome <args>: Sets the welcome message. /help setwelcome for special notes\n"
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
            with create_connection(main_db_file) as conn:
                mycursor = conn.cursor()
                user_id_number = int(reply.from_user.id)
                chat_id = int(reply.chat_id)
                names = func.get_all_names(reply)
                mycursor.execute("SELECT * FROM warnings WHERE user_id = %s AND chat_id = %s"
                                 % (user_id_number, chat_id))
                fetch = mycursor.fetchall()
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
                        send_message = func.get_username_from_message(
                            reply) + " has 3/3 warnings but could not be banned."
                if reason is not "":
                    send_message += " Reason: " + reason
                mycursor.execute(
                    "INSERT INTO warnings (chat_id, user_id, username, first_name, reason) VALUES (%s,%s,%s,%s,%s)" %
                    (chat_id, user_id_number, names[0], names[1], reason))
                db.commit()
                context.bot.send_message(chat_id=update.effective_message.chat_id, text=send_message)


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(CommandHandler("giveaways", get_giveaways))
    dp.add_handler(CommandHandler("help", show_help))
    dp.add_handler(CommandHandler("rules", show_rules))
    dp.add_handler(CommandHandler("list", show_store))
    dp.add_handler(CommandHandler("store", show_store))
    dp.add_handler(CommandHandler("stores", show_store))
    dp.add_handler(CommandHandler("verified", verified))
    dp.add_handler(CommandHandler("ad", advert_warning))
    dp.add_handler(CommandHandler("ban", ban_user))
    dp.add_handler(CommandHandler("setrules", set_rules))
    dp.add_handler(CommandHandler("setstore", set_store))
    dp.add_handler(CommandHandler("setwelcome", set_welcome))
    dp.add_handler(CommandHandler("verify", verify))
    dp.add_handler(CommandHandler("warn", warn))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, show_welcome))
    dp.add_handler(MessageHandler(Filters.text, new_message))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    # Create verified table if not exist
    sql_create_verified_table = """ CREATE TABLE IF NOT EXISTS verified (
                                    [generated_id] INTEGER PRIMARY KEY,
                                    chat_id INTEGER NOT NULL,
                                    user_id INTEGER NOT NULL,
                                    username text,
                                    first_name text,
                                    services text,
                                    input_id INTEGER,
                                    input_username text,
                                    input_first_name text
                                    ); """
    # Create warnings table if not exist
    sql_create_warnings_table = """CREATE TABLE IF NOT EXISTS warnings (
                                    [generated_id] INTEGER PRIMARY KEY,
                                    chat_id INTEGER NOT NULL,
                                    user_id INTEGER NOT NULL,
                                    username text,
                                    first_name text,
                                    reason text
                                );"""
    # Create settings table if not exist
    sql_create_settings_table = """CREATE TABLE IF NOT EXISTS settings (
                                    chat_id INTEGER PRIMARY KEY,
                                    welcome text,
                                    rules text,
                                    store text
                                );"""

    with create_connection(main_db_file) as db:
        if db is not None:
            create_table(db, sql_create_verified_table)
            create_table(db, sql_create_warnings_table)
            create_table(db, sql_create_settings_table)
    main()
