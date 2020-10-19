if os.path.isfile(verified_list_file):
    with open(verified_list_file, "r") as f:
        reader = csv.reader(f, delimiter=',', )
        for line in reader:
            if line:
                verified_list.append(line[0])
                verified_list_editors.append(line[1])
    f.close()
    print(verified_list)
@send_typing_action
def verified(update, context):
    if not update.message.from_user.is_bot:
        if update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id) and context.args:
            if context.args[0].lower() == 'help':
                update.message.reply_text(
                    "Use '/verified edit # [Updated services]' to edit. \n Use '/verified remove #' to remove.\n "
                    "Use '/verified [USER]: [List of services]' to add.")
            elif context.args[0].lower() == 'edit' or context.args[0].lower() == 'remove':
                if len(context.args) > 1:
                    if func.is_int(context.args[1]):
                        edit_number = int(context.args[1]) - 1
                        print(edit_number)
                        print(len(verified_list))
                        if context.args[0].lower() == 'remove':
                            verified_list.pop(edit_number)
                            verified_list_editors.pop(edit_number)
                        else:
                            verified_list[edit_number] = verified_list[edit_number].split(':')[0] + ':' + ' '.join(
                                context.args[2:])
                            if update.message.from_user.username:
                                verified_list_editors[edit_number] = update.message.from_user.username
                            else:
                                verified_list_editors[edit_number] = update.message.from_user.first_name
                        with open("verified.csv", 'w') as writeFile:
                            writer = csv.writer(writeFile, delimiter=',')
                            for number in range(0, len(verified_list)):
                                writer.writerow([verified_list[number], verified_list_editors[number]])
                        writeFile.close()
                    else:
                        update.message.reply_text("Not a valid integer")
                else:
                    update.message.reply_text("Missing required arguments")
            elif context.args[0].lower() == "marauder" or context.args[0].lower() == "marauder:" or ':' not in ' '.join(
                    context.args):
                update.message.reply_text("Either you're being a cheeky fat cunt, or you forgot to add a user!")
            elif len(' '.join(context.args)) < 60:
                verified_list.append(' '.join(context.args).strip('@'))
                with open("verified.csv", 'a') as writeFile:
                    writer = csv.writer(writeFile, delimiter=',')
                    if update.message.from_user.username is not None:
                        writer.writerow([' '.join(context.args).strip('@'), update.message.from_user.username])
                    else:
                        writer.writerow([' '.join(context.args).strip('@'), update.message.from_user.first_name])
                writeFile.close()
            else:
                update.message.reply_text("Too many characters")
        else:
            verified_string = '\n'.join(verified_list)
            update.message.reply_text(verified_string)


def welcome(update, context):
    for new_user_obj in update.message.new_chat_members:
        open("logs/logs_" + time.strftime('%d_%m_%Y') + ".txt", "w").write("\nupdate status: " + str(update))
        chat_id = update.message.chat.id
        new_user = ""
        message_rnd = random.choice(message_list)
        welcome_message = open('message/' + message_rnd, 'r').read().replace("\n", "")
        warn_message = open('warnmsg.html', 'r').read().replace("\n", "")
        try:
            new_user = "@" + new_user_obj['username']
        except Exception as e:
            new_user = new_user_obj['first_name']
        if not ad.only_alphabet_chars(new_user, "ARABIC"):
            context.bot.sendMessage(chat_id=chat_id, text=welcome_message.replace("{{username}}", str(new_user)),
                                    parse_mode='HTML')
        else:
            context.bot.sendMessage(chat_id=chat_id, text=warn_message.replace("{{username}}", str(new_user)),
                                    parse_mode='HTML')