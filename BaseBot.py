import os

from functools import wraps

from Utils import parse_message, sleep, config
from Thread import BotThreadManager, CountDownLatch

import telegram
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, Filters, MessageHandler, ConversationHandler, CallbackQueryHandler, BaseFilter)


# call singleton thread
thread = BotThreadManager()


def send_typing_action(func):
    """Sends typing action while processing func command."""
    @wraps(func)
    def command_func(bot, update, *args, **kwargs):
        bot.send_chat_action(chat_id=update.effective_chat.id)
        return func(bot, update, *args, **kwargs)
    return command_func

def restricted(func):
    """Restrict usage of func to allowed users only and replies if necessary"""
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        user_name = update.effective_user.username
        if user_id not in config.get('valid_ids', []) and user_name not in config.get('valid_users', []):
            print("WARNING: Unauthorized access denied for {}-{}.".format(user_id, user_name))
            parse_message(update).reply_text("WARNING: Unauthorized access denied for {}-{}.".format(user_id, user_name))
            return  # quit function
        return func(bot, update, *args, **kwargs)
    return wrapped



class BaseBot(object):

    def __init__(self, bot_name):
        self.config = config
        self.thread = thread
        self.secrets = self.config.get(bot_name, {})
        self.token = self.secrets.get('token')
        assert isinstance(self.token, str), 'Token must be of type string'

        self.bot_active = False  # currently not in use
        self.updater = None
        self.verbose  = False   # Automatic per epoch updates
        self.chat_id  = None

    def activate_bot(self):
        """ Function to initiate the Telegram bot """
        self.updater = Updater(self.token, use_context=True)  # setup updater
        dp = self.updater.dispatcher  # Get the dispatcher to register handlers
        dp.add_error_handler(self.error)  # log all errors

        dp.add_handler(CommandHandler(["help", "h"], self.help))  # /help
        dp.add_handler(CommandHandler(["status", "s"], self.status))  # /get status
        self.add_handlers(dp)

        # Start the Bot
        self.updater.start_polling()
        self.bot_active = True
        self.schedule_thread()
        # Uncomment next line while debugging
        self.updater.idle()

    def add_handlers(self, dp):
        pass

    def schedule_thread(self):
        pass

    def context(self):
        return self.updater

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.error('Update "%s" caused error "%s"', update, context.error)
        pass

    def stop_bot(self):
        """ Function to stop the bot """
        self.updater.stop()
        self.bot_active = False
        self.more_on_stop()
        self.thread.shutdown()
        pass

    def more_on_stop(self):
        pass

    @restricted
    @send_typing_action
    def status(self, update, context):
        """ Telegram bot callback for the /status command. Replies with the latest status"""
        parse_message(update).reply_text(
            self.get_status_message()
        )

    @restricted
    @send_typing_action
    def help(self, update, context):
        """ Telegram bot callback for the /help command. Replies the startup message"""
        parse_message(update).reply_text(self.startup_message, reply_markup=ReplyKeyboardRemove())


    def get_status_message(self):
        return "TailLogs not starting (paths {})".format(self.paths) if not self.verbose else \
            "Starting TailLOgs: \npaths {},\nnr. last lines {},\noffset {},\ninterval {}".format(self.paths, self.n, self.offset, self.interval)

    ###########################################################################
    ## common send ##

    def send_chat_action(self, chat_id, action=telegram.ChatAction.TYPING):
        try:
            if chat_id is not None:
                self.updater.bot.send_chat_action(chat_id=chat_id, action=action)
            else:
                self.logger.info('Send chat action failed, user did not send /start')
        except Exception as e:
            self.logger.error(e)

    def send_message(self, txt, chat_id=None, parse_mode=telegram.ParseMode.HTML):
        """ Function to send a Telegram message to user
         # Arguments
            txt: String, the message to be sent
        """
        assert isinstance(txt, str), 'Message text must be of type string'
        try:
            cid = chat_id if chat_id else self.chat_id
            if cid is not None:
                self.updater.bot.send_message(chat_id=cid, text=txt, parse_mode=parse_mode)
            else:
                self.logger.info('Send message failed, user did not send /start')
        except Exception as e:
            self.logger.error(e)


########################################################################################################
## Thread tasks ##

def autoupdate(bot):
    while bot.bot_active:
        while bot.verbose:
            tail_logs(bot)
            sleep(bot.interval)
        sleep("10s")


def tail_logs(bot, paths=[], offset=None, lastLines=None, chat_id=None):
    latch = CountDownLatch(1)

    def logs():
        try:
            ps = paths if paths else bot.paths
            if not ps:
                return

            n = lastLines if lastLines else bot.n
            o = offset if offset else bot.offset
            bot.logger.info("starting path {}, n {}, offset {}".format(ps,n,o))

            text = "\n\n"
            for p in ps:
                last_n = get_last_n_lines(p, n)
                last_n_offset = last_n[0:(len(last_n)-o)]
                text += "<b>Path</b> {}\n{}\n\n".format(p, ("\n".join(last_n_offset)).strip())

            message = "<b><u>Tail-Logs</u></b>:" \
                      "\n<b>Last lines</b> {}" \
                      "\n<b>Offset</b> {}" \
                      "{}".format(p, n, o, text)
            bot.send_message(message, chat_id=chat_id)
        except Exception as ex:
            bot.logger.error(ex)
        finally:
            latch.count_down()

    thread.submit(func=logs(), error=lambda err: latch.count_down())
    latch.wait()
    pass


def get_last_n_lines(file_name, N):
    # Create an empty list to keep the track of last N lines
    list_of_lines = []
    # Open file for reading in binary mode
    with open(file_name, 'rb') as read_obj:
        # Move the cursor to the end of the file
        read_obj.seek(0, os.SEEK_END)
        # Create a buffer to keep the last read line
        buffer = bytearray()
        # Get the current position of pointer i.e eof
        pointer_location = read_obj.tell()
        # Loop till pointer reaches the top of the file
        while pointer_location >= 0:
            # Move the file pointer to the location pointed by pointer_location
            read_obj.seek(pointer_location)
            # Shift pointer location by -1
            pointer_location = pointer_location -1
            # read that byte / character
            new_byte = read_obj.read(1)
            # If the read byte is new line character then it means one line is read
            if new_byte == b'\n':
                # Save the line in list of lines
                list_of_lines.append(buffer.decode()[::-1])
                # If the size of list reaches N, then return the reversed list
                if len(list_of_lines) == N:
                    return list(reversed(list_of_lines))
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)

        # As file is read completely, if there is still data in buffer, then its first line.
        if len(buffer) > 0:
            list_of_lines.append(buffer.decode()[::-1])

    # return the reversed list
    return list(reversed(list_of_lines))
