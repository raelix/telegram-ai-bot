from settings.user_settings_database import UserSettingsDatabase


class UserSettings:
    def __init__(self, user_id):
        self.user_id = user_id
        self.db = UserSettingsDatabase(user_id)

    def is_tool_enabled(self, tool_name: str) -> bool:
        return self.db.is_enabled_feature(tool_name)

    def set_tool_enabled(self, tool_name: str, enabled: bool):
        return self.db.set_feature(tool_name, enabled)

    def set_tool_parameter(self, key: str, value: str):
        return self.db.set_setting(key, value)

    def get_tool_parameter(self, key: str) -> str:
        return self.db.get_setting(key)

