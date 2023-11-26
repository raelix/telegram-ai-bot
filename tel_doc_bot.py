import io
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.ext import MessageHandler, filters
from pathlib import Path
import gettext
import locale
import json
from ai_manager import AIManager
from text_extractor import AWSTextExtractor

# process all for dir in $(ls -d locales/*);
# do msgfmt $dir/LC_MESSAGES/tel_doc_bot.po -o $dir/LC_MESSAGES/tel_doc_bot.mo; done

locale.setlocale(locale.LC_ALL, '')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

config_file_path = 'configuration.json'


class TelDocBot:
    def __init__(self, configuration):
        self.application = self.setup_application(configuration['telegram_bot_token'])
        self.ai_manager = AIManager(configuration['openai_api_key'])
        self.aws_text_extractor = AWSTextExtractor(configuration['region_name'],
                                                   configuration['aws_access_key_id'],
                                                   configuration['aws_secret_access_key'], configuration
                                                   ['bucket_name'])
        self.application.run_polling()

    def setup_application(self, bot_token: str):
        application = ApplicationBuilder().token(bot_token).build()
        start_handler = CommandHandler('start', self.start)
        doc_handler = MessageHandler(filters.Document.ALL, self.docs)
        questions_handler = MessageHandler(filters.ALL, self.questions)
        application.add_handler(start_handler)
        application.add_handler(doc_handler)
        application.add_handler(questions_handler)
        return application

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(len(context.user_data))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=self.get_message(update, "welcome", name=update.effective_user.username))

    async def docs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
        file = await context.bot.get_file(update.message.document)
        memory_buffer = io.BytesIO(await file.download_as_bytearray())
        f_name = Path(file.file_path).name
        docs = self.aws_text_extractor.process_document(memory_buffer, f_name)
        self.ai_manager.process_document(update.effective_user.username, docs)
        await update.message.reply_text("👍", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=update.message.id)

    async def questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message.text
        response = self.ai_manager.ask(update.effective_user.username, msg)
        await update.message.reply_text(response)

    def get_message(self, update: Update, key: str, **kwargs):
        loc = self.get_locale(update)
        lang = gettext.translation('tel_doc_bot', localedir='locales', languages=[loc])
        lang.install()
        return lang.gettext(key).format(**kwargs)

    def get_locale(self, update: Update):
        return update.message.from_user.language_code


def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        raise


if __name__ == '__main__':
    config_data = load_config(config_file_path)
    print("Configuration loaded successfully")
    TelDocBot(config_data)
