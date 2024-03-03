# Telegram AI Bot 
This telegram bot will assist you on multiple tasks:
- Allows to ask any question related to your personal documents - just upload a file to the bot chat, it will do the rest. 
- Allows to manage any device entity within your home-assistant instance.
- Allows to ask for movies suggestion based on the scraped data from your Netflix account.
- Allows to play a specific movie directly on your smart tv without touching any key on the remote control :)

The great feature behind this project is that it is extensible and every new tool added will automatically inherit a configuration wizard on the telegram bot.

It leverages [LangChain](https://www.langchain.com/) and [LangGraph](https://python.langchain.com/docs/langgraph).

# Requirements
- Conda (Required).
- OpenAI token (Required).
- Telegram Bot Token (Required).
- AWS S3 Bucket - Only needed for the document assistant.
- Home Assistant endpoint and bearer-token - Only needed for the HA assistant.

# Quick start

### Create the configuration file
Create the configuration file called ```configuration.json``` in the root project folder. Here's how it should look like:
```json
{
  "openai_api_key": "", /* required */
  "region_name": "",
  "aws_access_key_id": "",
  "aws_secret_access_key": "",
  "bucket_name": "",
  "telegram_bot_token": ""  /* required */
}
```
### Create the python environment
```shell
conda create -n telegram-document-bot python=3.9
conda activate telegram-document-bot
```
### Install the dependencies
```shell
pip install -r requirements.txt
```
### Run it!
```shell
python3 tel_doc_bot.py
```
# Available Tools
As of today these tools are built-in:
- Document assistant
- Home-Assistant tool
- DuckDuckGo tool
- GoogleSearch tool
- Netflix tool

# Dynamic Tools Management
The application can be extended with any standard or custom tool. The bot is already built to allow to manage them through the telegram bot:
- Dynamic configuration (parameters are exposed to the chat in a "wizard" format)
- Enabling/Disabling a specific Tool
- Check the current Tools status 

# Deep-dive - document assistant tool
Document store:
- Once you upload a document to the telegram bot the file is uploaded to an S3 bucket
- It uses AWS Textract to convert the content to a readable format
- For each document it finds out possible questions and a summary (documents are then stored into ChromaDB)
- Each question and summary will be associated to the original document

Queries on uploaded documents:
- Every time a question is asked, it searches in the document assistant tool
- the tool creates a set of possible questions related to the main user question
- They are searched by using the similarity search to the stored questions and summaries
- the result is then provided to openai and then back to the user

## Features
- MultiQuery: every time the user asks a question, it tries to create more related to the passed context
- MultiVector: to improve the results, each doc is associated to possible questions (Hypothetical Queries) and a summary
- ConversationBufferWindowMemory: a window of the three last messages is kept in memory
- Collection by user: every user will have a separate collection in Chroma

# Deep-dive - home-assistant tool
This tool allows to extract the entities from Home Assistant, store their information in a vectorstore and query them through the Home Assistant API
The main features are:
- Entities status
- Manage entities
Which means you can ask any question like:
- Is kitchen light turned on? 
- Could you please turn off all lights?
- Is Gianmarco at home?

## What is does
- Every time a question related to home-assistant devices is asked it first finds out the entity_id and the available operations from the vectorstore
- It creates a set of possible questions related to the user question
- it applies the similarity search to the stored entities to find the related ones
- Once all entity IDs are known it can get the status directly from Home Assistant or set the requested status

# Deep-dive - Netflix tool
As of today the netflix tool works only if the ```netflix.json``` file is present in the root folder. Unfortunately I didn't have enough time to fully integrate the scraper within the bot.

In order to make it working you should first produce this file by running the application located in the ```./scraper``` folder. 


# Missing features
- [ ] Containerize it
- [ ] Fully integrate the Netflix scraper
- [ ] Documents size check
- [ ] Documents type check
- [ ] Merge and combine the databases
- [ ] Costs estimation
- [ ] Home Assistant allow delayed operation