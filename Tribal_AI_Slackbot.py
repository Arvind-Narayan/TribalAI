SLACK_TOKEN = '' #retreive secrets from .env
SIGNING_SECRET = ''


import datetime
import logging
import slack
from flask import Flask
from slackeventsapi import SlackEventAdapter

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain



embedding = OpenAIEmbeddings()

#Read from local embeddings dir
persist_directory = './chroma2/'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)


current_date = datetime.datetime.now().date()
if current_date < datetime.date(2023, 9, 2):
    llm_name = "gpt-3.5-turbo-0301"
else:
    llm_name = "gpt-3.5-turbo"

llm = ChatOpenAI(model_name=llm_name, temperature=0)


#memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

#retriever
retriever=vectordb.as_retriever()
qa = ConversationalRetrievalChain.from_llm(
    llm,
    retriever=retriever,
    memory=memory,
    chain_type = 'stuff' #default = 'stuff'
)



app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SIGNING_SECRET,'/slack/events',app)

client = slack.WebClient(token = SLACK_TOKEN)
BOT_ID = client.api_call("auth.test")['user_id']



event_log = {}

@slack_event_adapter.on('message')
def message(payload):
    event_id = payload.get('event_id')
    print('on event ', event_id)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    
    if event_id not in event_log.keys():
        event_log[event_id] = 0
        
    event_log[event_id] += 1
    
    print(event_log)
    
    if event_log[event_id] == 1:
        if(BOT_ID != user_id):
            print('in if')
            result = qa({"question": text})
            client.chat_postMessage(channel=channel_id, text=result['answer'])
            # client.chat_postMessage(channel=channel_id, text='hey there')
    
    
    
if __name__ == '__main__':
    app.run(debug=True, port = 5003)