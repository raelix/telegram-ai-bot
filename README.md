# Telegram Document Bot 
This telegram bot allows to ask any question related to your personal documents. You should just upload a file to the bot chat, it will do the rest.

# Requirements
- OpenAI token
- AWS S3 Bucket
- Telegram Bot Token

# Tools
The application can be extended with any standard or custom tool. The bot is already built to allow:
- Dynamic configuration of the Tool from Telegram (parameters are exposed to the chat through their description in a "wizard" flow)
- Enabling/Disabling a specific Tool
- Check the current tools status

## Available Tools
The bot comes out with:
- Document extractor tool (explained in detail below)
- Home-Assistant tool (custom)
- DuckDuckGo tool (wrapped)

## Home Assistant
The bot allows to extract the entities from Home Assistant, store their information in a vectorstore and query them through the Home Assistant API
The main features are:
- know the entities status 
- change entity state

# How it works?

Document store:
- Once you send a document to the bot the file is uploaded to S3 bucket
- It uses AWS Textract to convert the content a readable format
- For each document it finds out possible questions and creates a summary (there information are then stored to ChromaDB)
- Each question and summary is associated to the document saved locally in a text format

Queries on uploaded documents:
- Every time a question is asked to the bot it searches in the home-document tool
- the tool creates first a set of possible questions related to the user question
- it applies the similarity search to the stored questions and summaries
- the result is then provided to openai and to the user

Queries on Home Assistant entities:
- Every time a question is asked to the bot it first finds out the entity_id and the available operations from the vectorstore
- It creates first a set of possible questions related to the user question
- it applies the similarity search to the stored entities to find the related ones
- Once all entity IDs are known it can get the status directly from Home Assistant or set the requested status


# Features
- MultiQuery: every time the user asks a question, it tries to create more related to the passed context
- MultiVector: to improve the results, each doc is associated to possible questions (Hypothetical Queries) and a summary
- ConversationBufferWindowMemory: a window of the three last messages is kept in memory
- Collection by user: every user will have a separate collection in Chroma

# Configuration file
A configuration file called ```configuration.json``` is required in order to start the bot:
```json
{
  "openai_api_key": "",
  "region_name": "",
  "aws_access_key_id": "",
  "aws_secret_access_key": "",
  "bucket_name": "",
  "telegram_bot_token": ""
}
```

# Dependencies
// TODO

# Missing features
- [x] Documents removal from S3
- [ ] Documents size check
- [ ] Documents type check
- [ ] Costs estimation
- [ ] Error handling
- [ ] Home Assistant allow delayed operation