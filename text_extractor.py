import time
from typing import List

import boto3
from langchain.document_loaders import AmazonTextractPDFLoader
from langchain.schema import Document


class AWSTextExtractor:

    def __init__(self, region_name, aws_access_key_id, aws_secret_access_key, bucket_name):
        self.session = boto3.Session(region_name=region_name,
                                     aws_access_key_id=aws_access_key_id,
                                     aws_secret_access_key=aws_secret_access_key)
        self.bucket_name = bucket_name

    def process_document(self, data, filename: str) -> List[Document]:
        self._upload_document(data, filename)
        docs = self._to_documents(filename)
        self._delete_document(filename)
        return docs

    def _upload_document(self, data, filename: str):
        print("uploading {}".format(filename))
        session = self.session.client('s3')
        session.upload_fileobj(data, self.bucket_name, filename)
        session.get_waiter('object_exists').wait(Bucket=self.bucket_name, Key=filename)
        session.close()
        print("upload of {} completed".format(filename))

    def _to_documents(self, filename: str) -> list[Document]:
        print("extracting {}".format(filename))
        session = self.session.client('textract')
        loader = AmazonTextractPDFLoader('s3://{bucket_name}/{filename}'.format(
            bucket_name=self.bucket_name,
            filename=filename,
        ), client=session)
        session.close()
        print("extract of {} completed".format(filename))
        return loader.load()

    def _delete_document(self, filename: str):
        uri = 's3://{bucket_name}/{filename}'.format(bucket_name=self.bucket_name, filename=filename)
        # TODO:
        # missing implementation
        pass
