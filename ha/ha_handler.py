import json
import requests
from urllib.parse import urljoin
from typing import Dict, List
from langchain.schema import Document

# Tech debit - I don't really want to expose all the entities (e.g. the light of a wall switch)
# I have more than 1000 entities, select what to keep is a mess, would be nice, maybe, to add a prefix
# on the friendly_name and filter by prefix and/or domain
FILTERS = [
    "switch.bagno_interruttore",
    "switch.camera_da_letto_interruttore",
    "light.camera_da_letto_led",
    "light.soggiorno_tv_led",
    "light.studio_luci",
    "light.studio_led",
    "light.studio_luce_lampada",
    "light.corridoio_luci",
    "switch.cucina_interruttore",
    "light.cucina_led",
    "light.soggiorno_luci_camino",
    "light.soggiorno_led_camino",
    "switch.soggiorno_interruttore_divano",
    "switch.ingresso_interruttore",
    "light.luce_piccola"
    "binary_sensor.presenza_soggiorno_cucina",
    "binary_sensor.presenza_soggiorno_divano",
    "binary_sensor.presenza_soggiorno_tavolo",
    "binary_sensor.presenza_ingresso_zona_giorno",
    "binary_sensor.presenza_studio_fp2",
    "binary_sensor.presenza_studio_scrivania_fp2",
    "binary_sensor.presenza_camera_da_letto",
    "binary_sensor.presenza_bagno_all",
    "lock.nuki_lock",
    "alarm_control_panel.casa_alarm",
    "media_player.lg_tv_oled",
    "media_player.samsung_tv_q82"
]
ALLOWED_TYPES = [
    "person",
]


class HAHandler:
    _states = "api/states"
    _services = "api/services"

    def __init__(self, url: str, bearer_token: str, **kwargs):
        self.url = url
        self.bearer_token = bearer_token

    def get_summary(self) -> List[Document]:
        docs: List[Document] = []
        entities = self.get_entities()
        services = self.get_services_map()
        filtered_items = [item for item in entities if
                          item["entity_id"] in FILTERS or item['entity_id'].split('.')[0] in ALLOWED_TYPES]
        for item in filtered_items:
            d_type = item['entity_id'].split('.')[0]
            # d_type = ' '.join(d_type.split('_'))
            friendly_name = item['attributes']['friendly_name']
            entity_id = item['entity_id']
            content = (
                f"The entity with friendly name \"{friendly_name}\" is of type {d_type}, the identifier is {entity_id}"
                f" its type allow to get the current status")
            if d_type in services:
                content += f" and it also allow to execute the following actions: {', '.join(services[d_type])}"
            docs.append(Document(page_content=content))
        return docs

    def get_entity_status(self, entity_id: str) -> str:
        entities = self.get_entities()
        for entity in entities:
            if entity["entity_id"] == entity_id:
                return entity["state"]

    def get_entity_attributes(self, entity_id: str):
        entities = self.get_entities()
        for entity in entities:
            if entity["entity_id"] == entity_id:
                return str(entity["attributes"])

    def get_services_map(self) -> Dict[str, List[str]]:
        services = self.get_services()
        actions: Dict[str, List[str]] = dict()
        for service in services:
            actions[service["domain"]] = [k for k in service['services'].keys()]
        return actions

    def get_entities(self):
        return self.get_json_from_url(urljoin(self.url, self._states))

    def get_services(self):
        return self.get_json_from_url(urljoin(self.url, self._services))

    def get_json_from_url(self, url):
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                json_data = response.json()
                return json_data
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the request: {e}")
            return None

    def set_state(self, entity_type: str, action: str, entity_id: str) -> bool:
        url = urljoin(self.url, "{}/{}/{}".format(self._services, entity_type, action))
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            data = {
                "entity_id": entity_id
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                return True
            else:
                print(f"Request failed with status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the request: {e}")
            return False
