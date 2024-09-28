import requests

class HAAgentQuery:

    def __init__(self, url: str, bearer_token: str, **kwargs):
        self.url = url
        self.bearer_token = bearer_token

    def get_entity_status(self, sentence: str) -> str:
        return self.query_sentence(self.url, sentence=sentence)


    def query_sentence(self, sentence):
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(f"{self.url}/api/conversation/process", 
                                     json={
                                         "text": sentence,
                                         "conversation_id": "tel-doc-bot",
                                         "agent_id": "conversation.chatgpt"
                                     },
                                     headers=headers)
            if response.status_code == 200:
                json_data = response.json()
                return json_data
            else:
                print(f"Request failed with status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the request: {e}")
            return None
