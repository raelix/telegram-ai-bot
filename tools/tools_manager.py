from typing import List, Dict, Type
from langchain.tools import Tool
from settings.user_settings import UserSettings
from tools.duckduckgo_tool import DuckDuckGoTool
from tools.googlesearch_tool import GoogleSearchTool
from tools.ha_tool import HATool
from tools.tool_instance import ToolInstance


class ToolsManager:

    def __init__(self, openai_api_key: str, user_id: str, user_settings: UserSettings):
        self.openai_api_key = openai_api_key
        self.user_id = user_id
        self.user_settings = user_settings
        self.instances: Dict[str, ToolInstance] = dict()
        self.classes: Dict[str, Type[ToolInstance]] = dict(
            home_assistant=HATool,
            duckduckgo=DuckDuckGoTool,
            googlesearch=GoogleSearchTool
        )

    def get_user_tools(self, **kwargs) -> List[Tool]:
        self.instances = dict()
        tools: List[Tool] = []
        for tool_name, tool_type in self.classes.items():
            if self.user_settings.is_tool_enabled(tool_name):
                args = dict()
                missing_parameter = False
                for param in tool_type.get_required_fields().keys():
                    if param == "openai_api_key":
                        args[param] = self.openai_api_key
                    elif param == "user_id":
                        args[param] = self.user_id
                    else:
                        param_value = self.user_settings.get_tool_parameter(param)
                        if param_value:
                            args[param] = param_value
                        else:
                            missing_parameter = True
                            print("Cannot instantiate {} tool due to missing {} property".format(tool_name, param))
                            break
                if missing_parameter:
                    print("Skipping {} tool".format(tool_name))
                    continue
                self.instances[tool_name] = tool_type.init(**args)
                tools += self.instances[tool_name].get_tools(**kwargs)
                print("Tool: {} loaded successfully".format(tool_name))
        return tools

    def get_tools_list(self):
        return self.classes.keys()

    def get_tool_required_parameters(self, tool_name: str):
        ret = self.classes[tool_name].get_required_fields().copy()
        del ret["openai_api_key"]
        del ret["user_id"]
        return ret

    def get_available_tools_functions(self):
        ret: Dict[str, Dict[str, str]] = dict()
        for instance_name, instance in self.classes.items():
            if instance_name in self.instances:
                ret[instance_name] = instance.get_available_functions()
        return ret

    def get_tools_status(self):
        ret: Dict[str, bool] = dict()
        for instance_name, instance in self.classes.items():
            ret[instance_name] = True if instance_name in self.instances else False
        return ret

    def call_tool_function(self, tool_name, function_name):
        if tool_name in self.instances:
            method = getattr(self.instances[tool_name], function_name)
            method()
        else:
            print("function {} is not available on {} tool".format(function_name, tool_name))

    def set_tool_parameters(self, tool_name: str, parameters: Dict[str, str]):
        for k, v in parameters.items():
            self.user_settings.set_tool_parameter(k, v)
        self.user_settings.set_tool_enabled(tool_name, True)

    def disable_tool(self, tool_name: str):
        self.user_settings.set_tool_enabled(tool_name, False)
