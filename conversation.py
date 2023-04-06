import uuid
import openai

from datetime import datetime

class Conversation:
    def __init__(self, messages):
        self.messages: list = messages
        self.name = str(uuid.uuid4())
        self.creation_time: str = datetime.now().isoformat()
        self.last_modified: str = datetime.now().isoformat()
    
    @property
    def messages(self):
        return self.__messages
    
    @messages.setter
    def messages(self, messages):
        for message in messages:
            if message['role'] == ['system']:
                messages.remove(message)

        self.__messages = messages

    def add_message(self, role, message):
        self.messages.append({"role": role, "content": message})
        self.last_modified = datetime.now().isoformat()

    def get_messages(self):
        return self.messages

    def get_name(self):
        prompt = "Come up with a simple name for this conversation, no more than 4 words: "

        self.messages.append({"role": "user", "content": prompt})

        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.messages)
        except Exception as e:
            print("Error: ", e)
        
        answer = response['choices'][0]['message']['content']

        self.name = answer

        return answer

    @classmethod
    def load(cls, conversation):

        convo = cls(
            messages=conversation['messages']
        )
        convo.creation_time = conversation['creation_time']
        convo.last_modified = conversation['last_modified']
        convo.name = conversation['name']
    
        return convo