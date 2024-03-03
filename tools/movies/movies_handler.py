import requests
from typing import List
from langchain.schema import Document
import json


class MoviesHandler:

    def __init__(self, movies_filename: str, webhook_url: str, **kwargs):
        self.movies_filename = movies_filename
        self.webhook_url = webhook_url

    def get_docs(self) -> List[Document]:
        f = open(self.movies_filename)
        data = json.load(f)
        documents = []
        for titleId, item in data.items():
            if item['type'] == 'movie' and 'description' in item:
                if 'genreName' in item and 'genres' in item:
                    item['genres'].append(item['genreName'])
                base_text = f"Title: {item['title']} - ID: {titleId} - Description: {item['description']}"
                if 'watched' in item:
                    base_text = f"{base_text} - Watched: {'Yes' if item['watched'] == True else 'No'}"
                if 'genres' in item:
                    base_text = f"{base_text} - Genres: {','.join(item['genres'])}"
                if 'releaseYear' in item:
                    base_text = f"{base_text} - Year: {item['releaseYear']}"
                if 'matchScore' in item:
                    base_text = f"{base_text} - Affinity: {item['matchScore']}"
                if 'tags' in item:
                    base_text = f"{base_text} - Tags: {','.join(item['tags'])}"
                if 'cast' in item:
                    base_text = f"{base_text} - Cast: {','.join(item['cast'])}"
                if 'directors' in item:
                    base_text = f"{base_text} - Directors: {','.join(item['directors'])}"
                if 'writers' in item:
                    base_text = f"{base_text} - Writers: {','.join(item['writers'])}"

                base_text = f"{base_text} - Poster URL: {item['boxArt']['url']}"
                documents.append(Document(page_content=base_text))
        return documents

    def watch(self, movie_id: str) -> bool:
        # e.g. https://ha.raelix.com/api/webhook/my-webhook-id
        url = f"{self.webhook_url}?id={movie_id}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Request failed with status code: {response.status_code}")
            return False
        return True
