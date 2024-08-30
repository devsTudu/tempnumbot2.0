#Stores the models of Data Requests

class CallbackQuery:
    def __init__(self, data):
        self.update_id = data.get('update_id')

        callback_query = data.get('callback_query', {})
        self.callback_query_id = callback_query.get('id')
        self.from_user = callback_query.get('from', {})
        self.message = callback_query.get('message', {})
        self.chat_instance = callback_query.get('chat_instance')
        self.data = callback_query.get('data')

        # From user
        self.from_user_id = self.from_user.get('id')
        self.from_user_is_bot = self.from_user.get('is_bot')
        self.from_user_first_name = self.from_user.get('first_name')
        self.from_user_username = self.from_user.get('username')
        self.from_user_language_code = self.from_user.get('language_code')

        # Message
        self.message_id = self.message.get('message_id')
        self.message_from = self.message.get('from', {})
        self.message_chat = self.message.get('chat', {})
        self.message_date = self.message.get('date')
        self.message_text = self.message.get('text')
        self.reply_markup = self.message.get('reply_markup', {})

        # Message from
        self.message_from_id = self.message_from.get('id')
        self.message_from_is_bot = self.message_from.get('is_bot')
        self.message_from_first_name = self.message_from.get('first_name')
        self.message_from_username = self.message_from.get('username')

        # Message chat
        self.chat_id = self.message_chat.get('id')
        self.chat_first_name = self.message_chat.get('first_name')
        self.chat_username = self.message_chat.get('username')
        self.chat_type = self.message_chat.get('type')

        # Reply to message
        self.reply_to_message = self.message.get('reply_to_message', {})
        self.reply_to_message_id = self.reply_to_message.get('message_id')
        self.reply_to_message_text = self.reply_to_message.get('text')
        self.reply_to_message_entities = self.reply_to_message.get(
            'entities', [])

class Message:
    def __init__(self, data):
        self.update_id = data.get('update_id')
        message = data.get('message', {})
        self.message_id = message.get('message_id')
        self.from_user = message.get('from', {})
        self.chat = message.get('chat', {})
        self.date = message.get('date')
        self.text = message.get('text')
        self.entities = message.get('entities', [])

        self.chat_id = self.chat.get('id')
        self.user_id = self.from_user.get('id')
        self.user_first_name = self.from_user.get('first_name')
        self.user_username = self.from_user.get('username')
        self.user_language_code = self.from_user.get('language_code')

        self.is_mention = any(
            entity.get('type') == 'mention' for entity in self.entities)
        self.is_command = any(
            entity.get('type') == 'bot_command' for entity in self.entities)
        self.is_simple_message = not self.entities

class phoneNumberFlow:
    format     = "server_provider_servicename_price"
    format2    = "server_provider_sericename_price_phone_actcode"

    @staticmethod
    def querytextToVarService(text):
        return text.split('_')

    @staticmethod
    def varToQuerytextService(server,provider,servicename,price):
        return "_".join([server,provider,servicename,price])


    @staticmethod
    def querytextToVarPhone(text):
        
        return text.split('_')

    @staticmethod
    def varToQuerytextPhone(server,provider,servicename,price,phone,act_code):
        return "_".join([server,provider,servicename,price,phone,act_code])

    