import io
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.ext import MessageHandler, filters
from pathlib import Path
import gettext
import locale
import json
from agent.ai_manager import AIManager
from loader.text_extractor import AWSTextExtractor

# process all for dir in $(ls -d locales/*);
# do msgfmt $dir/LC_MESSAGES/tel_doc_bot.po -o $dir/LC_MESSAGES/tel_doc_bot.mo; done

locale.setlocale(locale.LC_ALL, '')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

config_file_path = 'configuration.json'
CONFIGURE, STATUS, SWITCH, SETTING, DISABLE, COMMAND = range(6)


class TelDocBot:
    def __init__(self, configuration):
        self.application = self.setup_application(configuration['telegram_bot_token'])
        self.ai_manager = AIManager(configuration['openai_api_key'])
        self.aws_text_extractor = AWSTextExtractor(configuration['region_name'],
                                                   configuration['aws_access_key_id'],
                                                   configuration['aws_secret_access_key'], configuration
                                                   ['bucket_name'])
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def setup_application(self, bot_token: str):
        application = ApplicationBuilder().token(bot_token).build()
        start_handler = CommandHandler('start', self.start)
        doc_handler = MessageHandler(filters.Document.ALL, self.docs)
        questions_handler = MessageHandler(filters.ALL, self.questions)
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("features", self.features),
                CommandHandler("commands", self.commands),
            ],
            states={
                SWITCH: [
                    CallbackQueryHandler(self.status, pattern="^" + str(STATUS) + "$"),
                    CallbackQueryHandler(self.configure, pattern="^" + str(CONFIGURE) + "$"),
                    CallbackQueryHandler(self.disable, pattern="^" + str(DISABLE) + "$"),
                ],
                CONFIGURE: [
                    CallbackQueryHandler(self.selected_feature),
                ],
                DISABLE: [
                    CallbackQueryHandler(self.disable_feature),
                ],
                SETTING: [
                    MessageHandler(filters.ALL, self.feature_setting),
                ],
                COMMAND: [
                    CallbackQueryHandler(self.command_feature),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        application.add_handler(start_handler)
        application.add_handler(conv_handler)
        application.add_handler(doc_handler)
        application.add_handler(questions_handler)
        return application

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=self.get_message(update, "welcome",
                                                             name=update.effective_user.username))

    async def docs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
        file = await context.bot.get_file(update.message.document)
        memory_buffer = io.BytesIO(await file.download_as_bytearray())
        f_name = Path(file.file_path).name
        docs = self.aws_text_extractor.process_document(memory_buffer, f_name)
        self.ai_manager.process_document(update.effective_user.username, docs, update.message.id)
        await update.message.reply_text("👍", parse_mode=ParseMode.MARKDOWN, reply_to_message_id=update.message.id)

    async def questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        c_message = await context.bot.send_message(chat_id=update.message.chat_id,
                                                   text=self.get_message(update, "loading"),
                                                   parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_chat_action(chat_id=update.message.chat_id, action='typing')
        msg = update.message.text
        output = self.ai_manager.ask(update.effective_user.username, msg)
        response = output["response"]
        await c_message.delete()
        if "message_id" in output:
            msg_id = output["message_id"]
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN, reply_to_message_id=msg_id)
        else:
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN, )

    async def features(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("Enable", callback_data=str(CONFIGURE)),
                InlineKeyboardButton("Disable", callback_data=str(DISABLE)),
                InlineKeyboardButton("Status", callback_data=str(STATUS)),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select an option:", reply_markup=reply_markup)
        return SWITCH

    async def commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.username
        features_commands = self.ai_manager.get_available_feature_commands(user_id)
        print("Features")
        print(features_commands)
        keyboard = []
        for feature_name, feature_dict in features_commands.items():
            if len(feature_dict) > 0:
                command_description = list(feature_dict.values())[0]
                command_name = list(feature_dict.keys())[0]
                keyboard.append(
                    [InlineKeyboardButton(f"{feature_name} - {command_description}",
                                          callback_data=json.dumps(dict(
                                              feature=feature_name,
                                              cmd_name=command_name))
                                          )])

        keyboard.append([InlineKeyboardButton("Cancel", callback_data=json.dumps(
            dict(feature="cancel")))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select an option:", reply_markup=reply_markup)
        return COMMAND

    async def disable(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        features = self.ai_manager.get_features_status(update.effective_user.username)
        keyboard = []
        for feature_name, enabled in features.items():
            if enabled:
                keyboard.append([InlineKeyboardButton(feature_name, callback_data=feature_name)])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please choose one feature to disable:", reply_markup=reply_markup)
        return DISABLE

    async def command_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        commands_dict = json.loads(query.data)
        user_id = update.effective_user.username
        feature = commands_dict["feature"]
        if feature == "cancel":
            await query.edit_message_text("No problem.")
            return ConversationHandler.END
        cmd_name = commands_dict["cmd_name"]
        await query.edit_message_text(
            f"Calling...",
        )
        self.ai_manager.call_feature_command(user_id, feature, cmd_name)
        await query.edit_message_text(
            f"Call completed",
        )
        return ConversationHandler.END

    async def disable_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        feature = query.data
        user_id = update.effective_user.username
        self.ai_manager.disable_feature(user_id, feature)
        await query.edit_message_text(
            f"Feature {feature} disabled.",
        )
        return ConversationHandler.END

    async def configure(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        features = self.ai_manager.get_features(update.effective_user.username)
        keyboard = []
        for feature in features:
            keyboard.append([InlineKeyboardButton(feature,
                                                  callback_data=feature)
                             ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Please choose one:", reply_markup=reply_markup)
        return CONFIGURE

    async def selected_feature(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        feature = query.data
        user_id = update.effective_user.username
        parameters = self.ai_manager.get_feature_parameters(user_id, feature)
        if len(parameters) == 0:
            self.enable_feature(user_id, feature, dict())
            await query.edit_message_text(
                "No parameters required, {} tool enabled.".format(feature),
            )
            return ConversationHandler.END
        context.user_data["feature"] = feature
        context.user_data["expected_parameters"] = parameters.keys()
        context.user_data["available_parameters"] = dict()
        context.user_data["current_parameter"] = list(parameters.keys())[0]
        description = parameters[context.user_data["current_parameter"]]['description']
        await query.edit_message_text(
            f"Please type {description}:",
        )
        return SETTING

    async def feature_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        user_id = update.effective_user.username
        feature = context.user_data["feature"]
        key = context.user_data['current_parameter']
        context.user_data["available_parameters"][key] = text
        parameters = self.ai_manager.get_feature_parameters(user_id, feature)
        for k, v in parameters.items():
            if k not in context.user_data["available_parameters"]:
                context.user_data['current_parameter'] = k
                description = parameters[context.user_data["current_parameter"]]['description']
                await update.message.reply_text(
                    f"Please type {description}:",
                )
                return SETTING
        self.enable_feature(user_id, feature, context.user_data["available_parameters"])
        await update.message.reply_text("Configuration completed, {} feature enabled.".format(feature))
        del context.user_data["feature"]
        del context.user_data['current_parameter']
        del context.user_data["available_parameters"]
        return ConversationHandler.END

    def enable_feature(self, user_id: str, feature: str, values: Dict[str, str]):
        self.ai_manager.enable_feature(user_id, feature, values)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.username
        features_status = self.ai_manager.get_features_status(user_id)
        msg = "\n".join("- {} tool is {}".format(f_name, "enabled" if f_status is True else "disabled")
                        for f_name, f_status in features_status.items())
        await query.edit_message_text(msg)
        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.message.from_user
        await update.message.reply_text(
            "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
        )

        return ConversationHandler.END

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
