import logging
import json

from Utils import parse_message, split
from BaseBot import BaseBot, restricted, autoupdate

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (CommandHandler, ConversationHandler, CallbackQueryHandler)


def load(p=None):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception as ex:
        print(ex)
        return None


def write(p=None, verbose=False, chat_id=None, interval=None, path=None, n=0, offset=0):
    try:
        obj = {
            "verbose"  : verbose,
            "chat_id"  : chat_id,
            "interval" : interval,
            "path"     : None if not path else ",".join(path),
            "n"        : int(n) if isinstance(n, str) else n,
            "offset"   : int(offset)if isinstance(offset, str) else offset
        }
        with open(p, 'w') as out:
            json.dump(obj, out)
    except Exception as ex:
        print(ex)


# load persistent
persistent_path = 'persistent/persistent.json'
persistent = load(persistent_path)


class TailBot(BaseBot):

    def __init__(self):
        BaseBot.__init__(self, 'telegram')

        self.paths    = []
        self.interval = None
        self.n        = None
        self.offset   = None
        self.initParams(persistent=persistent, c=self.secrets)

        # Enable logging
        logging.basicConfig(format='%(asctime)s - (%(threadName)-10s) - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        # Message to display on /start and /help commands
        self.startup_message = "Hi, I'm the TailLogs bot! I will send you updates on Logs.\n" \
                               " Send /start [path] [lastlines] [offset] [interval] to activate automatic TailLogs every interval. " \
                               "\n\t\tIf args not defined, params in persistent or config will be used\n" \
                               " Send /startfromconfig(/sfc) to activate automatic TailLogs every interval. " \
                               "\n\t\tArgs from configs\n" \
                               " Send /stop to stop getting automatic TailLogs each epoch\n" \
                               " Send /status(/s) to get the latest results.\n" \
                               " send /help(/h) to see all options.\n\n"

    def initParams(self, persistent=None, c=None):
        if persistent:
            self.verbose  = persistent.get("verbose")   # Automatic per epoch updates
            self.chat_id  = persistent.get("chat_id")  # chat id, will be fetched during /start command
            self.paths    = split(persistent.get("path"), pattern=",")
            self.interval = persistent.get("interval")
            self.n        = persistent.get("n")
            self.offset   = persistent.get("offset")
        elif c:
            self.verbose  = False   # Automatic per epoch updates
            self.chat_id  = None  # chat id, will be fetched during /start command
            self.paths    = split(self.secrets.get("path"), pattern=",")
            self.interval = self.secrets.get("interval")
            self.n        = self.secrets.get("n")
            self.offset   = self.secrets.get("offset")
        else:
            self.verbose  = False   # Automatic per epoch updates
            self.chat_id  = None  # chat id, will be fetched during /start command
            self.paths    = None
            self.interval = None
            self.n        = None
            self.offset   = None

    def add_handlers(self, dp):
        dp.add_handler(CommandHandler("start", self.start))  # /help
        dp.add_handler(CommandHandler(["startfromconfig", "sfc"], self.start_from_config))  # /help

        dp.add_handler(self.stop_handler())  # stop
        pass

    def schedule_thread(self):
        self.thread.submit(name="TailLogs", func=autoupdate, args=(self,))


    ##############################################################################
    ## start/ stop updater ##

    # Start process callback
    @restricted
    def start(self, update, context):
        """ Telegram bot callback for the /start command.
        Fetches chat_id, activates automatic epoch updates and sends startup message"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        m = parse_message(update)
        args = context.args

        if self.verbose:
            m.reply_text("Already start TailLOgs: \npath {},\nn {},\noffset {},\ninterval {}.\nShould /stop at first!".format(self.paths, self.n, self.offset, self.interval))
            return

        if len(args) >= 4:
            self.paths    = split(args[0], pattern=",")
            self.n        = int(args[1])
            self.offset   = int(args[2])
            self.interval = args[3]

        if self.paths:
            self.chat_id = chat_id
            self.verbose = True

        m.reply_text(self.get_status_message())
        write(p=persistent_path, verbose=self.verbose, chat_id=self.chat_id, path=self.paths, interval=self.interval, n=self.n, offset=self.offset)

    @restricted
    def start_from_config(self, update, context):
        chat_id = update.effective_chat.id
        m = parse_message(update)

        self.initParams(c=self.secrets)
        self.chat_id = chat_id
        self.verbose = True

        m.reply_text(self.get_status_message())
        write(p=persistent_path, verbose=self.verbose, chat_id=self.chat_id, path=self.paths, interval=self.interval, n=self.n, offset=self.offset)

    # Stop process callbacks
    @restricted
    def stop(self, update, context):
        """ Telegram bot callback for the /stoptraining command. Displays verification message with buttons"""
        m = parse_message(update)

        reply_keyboard = [[InlineKeyboardButton("Yes", callback_data="Yes"),
                           InlineKeyboardButton("No", callback_data="No")]]
        m.reply_text(
            'Are you sure? '
            'This will stop the TailLogs!\n\n',
            reply_markup=InlineKeyboardMarkup(reply_keyboard, resize_keyboard=True))
        return 1

    @restricted
    def stop_verify(self, update, context):
        """ Telegram bot callback for the /stop command. Stops automatic epoch updates"""
        query = update.callback_query  # Get response
        if query.data == "Yes":
            self.initParams()

        query.edit_message_text(
            "Automatic updates turned off. Send /start [interval] [symbol] to turn TailLogs back on." if query.data == "Yes" else "OK, canceling stop request!"
        )
        write(p=persistent_path)
        return ConversationHandler.END

    @restricted
    def cancel_stop(self, update, context):
        """ Telegram bot callback for the /stop command. Handle user cancellation as part of conversation"""
        query = update.callback_query  # Get response
        query.edit_message_text('OK, canceling stop request!')
        return ConversationHandler.END

    def stop_handler(self):
        """ Function to setup the callbacks for the /stoptraining command. Returns a conversation handler """
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('stop', self.stop)],
            states={1: [CallbackQueryHandler(self.stop_verify, pattern=r'^(Yes)$')]},
            fallbacks=[CallbackQueryHandler(self.cancel_stop, pattern=r'^(No)$')])
        return conv_handler




