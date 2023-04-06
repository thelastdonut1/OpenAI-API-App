import openai
import time
import requests
import json

from config import API_KEY
from exceptions import ModelError, ModelNotFound

openai.api_key = API_KEY

models = openai.Model.list()    # List of model objects

class CompletionRequest:
    ATTRIBUTES = {
        "model": "The ID of the model to use for completion.",
        "prompt": ("The prompt(s) to generate completions for. The API will "
                   "generate <n> completions for each prompt and return the "
                   "<n> ranked as the \"best\"."),
        "suffix": "The suffix that comes after a completion of inserted text.",
        "max_tokens": "The maximum number of tokens to generate.",
        "temperature": "What sampling temperature to use, between 0 and 2.",
        "top_p": ("An alternative to sampling with temperature, called nucleus "
                  "sampling, where the model considers the results of the tokens "
                  "with top_p probability mass. So 0.1 means only the tokens "
                  "comprising the top 10% probability mass are considered."),
        "n": "How many completions to generate for each prompt.",
        "stream": "Whether to stream back partial progress.",
        "logprobs": ("Include the log probabilities on the logprobs most likely "
                     "tokens, as well the chosen tokens."),
        "echo": "Echo back the prompt in addition to the completion.",
        "stop": "Up to 4 sequences where the API will stop generating further tokens.",
        "presence_penalty": ("Number between -2.0 and 2.0 that penalizes new tokens "
                             "based on whether they appear in the text so far, "
                             "increasing the model's likelihood to talk about new "
                             "topics."),
        "frequency_penalty": ("Number between -2.0 and 2.0 that penalizes new tokens "
                              "based on their existing frequency in the text so far, "
                              "decreasing the model's likelihood to repeat the same "
                              "line verbatim."),
        "best_of": ("Generates best_of completions server-side and returns the "
                    "\"best\" (the one with the lowest log probability per token). "
                    "Results cannot be streamed."),
        "logit_bias": ("Dict of tokens and their logit bias values that gets added "
                       "to the logits of the model. Logit bias values can range "
                       "from [-100, 100] where values > 0 increase the probability "
                       "of a token being sampled and values < 0 decrease the "
                       "probability."),
        "user": ("A unique identifier representing your end-user, which can help "
                 "OpenAI monitor and detect abuse.")
    }
    COMPATIBLE_MODELS = ["text-davinci-003", "text-davinci-002", "text-curie-001",
                         "text-babbage-001", "text-ada-001", "davinci", "curie",
                         "babbage", "ada"]
    def __init__(self, model: str, prompt: str, **kwargs):
        self.model: str = model
        self.prompt: str = prompt
        self.set_attributes(**kwargs)

    @property 
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model: str):
        if model.lower() not in self.COMPATIBLE_MODELS:
            raise ModelError(f"{model} is not available for completion."
                            "Please check the model endpoint compatibility guide on the"
                            "OpenAI API documentation.")

        self._model = model

    @classmethod
    def get_attributes(cls, attr=None):
        if attr:
            return cls.ATTRIBUTES[attr]
        
        return cls.ATTRIBUTES

    def set_attributes(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.ATTRIBUTES.keys():
                raise AttributeError(f"{key} is not a valid attribute.")
            setattr(self, key, value)

    def send(self):
        '''
        Sends the completion request to the OpenAI API. The response as well as
        the time it took to receive the response is returned.

        Returns:
            response (dict): The response from the OpenAI API.
            response_time (float): The time it took to receive the response.
        '''
        start = time.time()
        response = openai.Completion.create(**self.__dict__)
        end = time.time()
        response_time = end - start
        return response, response_time

class ChatCompletionRequest:
    ATTRIBUTES = {
        "model": "The ID of the model to use for completion.",
        "messages": ("The messages to generate completions for, in the"
                     "chat format"),
        "temperature": "What sampling temperature to use, between 0 and 2.",
        "top_p": ("An alternative to sampling with temperature, called nucleus "
                  "sampling, where the model considers the results of the tokens "
                  "with top_p probability mass. So 0.1 means only the tokens "
                  "comprising the top 10% probability mass are considered."),
        "n": "How many completions to generate for each prompt.",
        "stream": "Whether to stream back partial progress.",
        "stop": "Up to 4 sequences where the API will stop generating further tokens.",
        "max_tokens": "The maximum number of tokens to generate.",
        "presence_penalty": ("Number between -2.0 and 2.0 that penalizes new tokens "
                             "based on whether they appear in the text so far, "
                             "increasing the model's likelihood to talk about new "
                             "topics."),
        "frequency_penalty": ("Number between -2.0 and 2.0 that penalizes new tokens "
                              "based on their existing frequency in the text so far, "
                              "decreasing the model's likelihood to repeat the same "
                              "line verbatim."),
        "logit_bias": ("Dict of tokens and their logit bias values that gets added "
                       "to the logits of the model. Logit bias values can range "
                       "from [-100, 100] where values > 0 increase the probability "
                       "of a token being sampled and values < 0 decrease the "
                       "probability."),
        "user": ("A unique identifier representing your end-user, which can help "
                 "OpenAI monitor and detect abuse.")
        }
    COMPATIBLE_MODELS = ["gpt-4", "gpt-4-0314", "gpt-4-32k",
                         "gpt-4-32k-0314", "gpt-3.5-turbo",
                         "gpt-3.5-turbo-0301"]
    
    def __init__(self, model: str, messages: str, **kwargs):
        self.model: str = model
        self.messages: list = messages
        self.set_attributes(**kwargs)

    @property 
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model: str):
        if model.lower() not in self.COMPATIBLE_MODELS:
            raise ModelError(f"{model} is not available for completion."
                            "Please check the model endpoint compatibility guide on the"
                            "OpenAI API documentation.")

        self._model = model

    @classmethod
    def get_attributes(cls, attr=None):
        if attr:
            return cls.ATTRIBUTES[attr]
        
        return cls.ATTRIBUTES

    def set_attributes(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.ATTRIBUTES.keys():
                raise AttributeError(f"{key} is not a valid attribute.")
            setattr(self, key, value)

    def send(self):
        '''
        Sends the chat completion request to the OpenAI API. The response as well
        as the time it took to receive the response is returned.

        Returns:
            response (dict): The response from the OpenAI API.
            response_time (float): The time it took to receive the response.
        '''
        start = time.time()
        response = openai.ChatCompletion.create(**self.__dict__)
        end = time.time()
        response_time = end - start
        return response, response_time
    
class EditRequest:
    ATTRIBUTES = {
        "model": "The ID of the model to use for completion.",
        "input": "The input text to use as a starting point for the edit.",
        "instruction": ("The instruction that tells the model how to edit "
                        "the prompt."),
        "n": "How many completions to generate for each prompt.",
        "temperature": "What sampling temperature to use, between 0 and 2.",
        "top_p": ("An alternative to sampling with temperature, called nucleus "
                  "sampling, where the model considers the results of the tokens "
                  "with top_p probability mass. So 0.1 means only the tokens "
                  "comprising the top 10% probability mass are considered.")
        }
    COMPATIBLE_MODELS = ["text-davinci-edit-001", "code-davinci-edit-001"]
    def __init__(self, model: str, prompt: str, instruction: str, **kwargs):
        self.model: str = model
        self.prompt: str = prompt
        self.instruction: str = instruction
        self.set_attributes(**kwargs)

    @property 
    def model(self):
        return self._model
    
    @model.setter
    def model(self, model: str):
        if model.lower() not in self.COMPATIBLE_MODELS:
            raise ModelError(f"{model} is not available for completion."
                            "Please check the model endpoint compatibility guide on the"
                            "OpenAI API documentation.")

        self._model = model

    @classmethod
    def get_attributes(cls, attr=None):
        if attr:
            return cls.ATTRIBUTES[attr]
        
        return cls.ATTRIBUTES

    def set_attributes(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.ATTRIBUTES.keys():
                raise AttributeError(f"'{key}' is not a valid attribute.")
            setattr(self, key, value)

    def send(self):
        '''
        Sends the edit request to the OpenAI API. The response as well
        as the time it took to receive the response is returned.

        Returns:
            response (dict): The response from the OpenAI API.
            response_time (float): The time it took to receive the response.
        '''
        start = time.time()
        response = openai.Edit.create(**self.__dict__)
        end = time.time()
        response_time = end - start
        return response, response_time
    

#TODO: Image prompt request
# openai.Image.create()
#! Required: (prompt: str)
parameters = {
    "prompt": ("A text description of the desired image(s). The maximum "
               "length is 1000 characters."),
    "n": "The number of images to generate. Must be between 1 and 10.",
    "size": "The size of the image to generate. Must be one of 256x256, 512x512, or 1024x1024.",
    "response_format": "The format of the response. Must be one of 'url' or 'b64_json'.",
    "user": ("A unique identifier representing your end-user, which can help "
             "OpenAI monitor and detect abuse.")
    }

#TODO: Image edit request
# openai.Image.create_edit()
#! Required: (image: str, prompt: str)
parameters = {
    "image": ("The image to use as the basis for the variation(s)."
             "Must be a valid PNG file, less than 4MB, and square."),
    "mask": ("An additional image whose fully transparent areas indicate"
             "where the image should be edited. Must be a valid PNG file,"
             "less than 4MB, and have the same dimensions as the image."),
    "prompt": ("A text description of the desired image(s). The maximum "
               "length is 1000 characters."),
    "n": "The number of images to generate. Must be between 1 and 10.",
    "size": "The size of the image to generate. Must be one of 256x256, 512x512, or 1024x1024.",
    "response_format": "The format of the response. Must be one of 'url' or 'b64_json'.",
    "user": ("A unique identifier representing your end-user, which can help "
             "OpenAI monitor and detect abuse.")
    }


#TODO: Image variation request
#! Required: (image: str)
parameters = {
    "image": ("The image to use as the basis for the variation(s)."
             "Must be a valid PNG file, less than 4MB, and square."),
    "n": "The number of images to generate. Must be between 1 and 10.",
    "size": "The size of the image to generate. Must be one of 256x256, 512x512, or 1024x1024.",
    "response_format": "The format of the response. Must be one of 'url' or 'b64_json'.",
    "user": ("A unique identifier representing your end-user, which can help "
             "OpenAI monitor and detect abuse.")
    }


#? Embedding request. May implement later.

#TODO: Audio transcription request
# openai.Audio.transcribe()
#! Required: (file: str, model: str)
parameters = {
    "file": ("The audio file to transcribe, in one of these formats: "
             "mp3, mp4, mpeg, mpga, m4a, wav, or webm."),
    "model": ("The ID of the model to use. Only whisper-1 is currently "
              "available."),
    "prompt": ("An optional text to guide the model's style or continue "
               "a previous audio segment. The prompt should match the"
               "audio language."),
    "response_format": ("The format of the transcript output, in one of "
                        "these options: json, text, srt, verbose_json or vtt."),
    "temperature": "The sampling temperature to use, between 0 and 1.",
    "language": ("The language of the input audio. Supplying the input "
                 "language in ISO-639-1 format is recommended to improve "
                 "accuracy and latency.")
    }

#TODO: Audio Translation request
# openai.Audio.translate()
#! Required: (file: str, model: str)
parameters = {
    "file": ("The audio file to transcribe, in one of these formats: "
             "mp3, mp4, mpeg, mpga, m4a, wav, or webm."),
    "model": ("The ID of the model to use. Only whisper-1 is currently "
              "available."),
    "prompt": ("An optional text to guide the model's style or continue "
               "a previous audio segment. The prompt should be in English."),
    "response_format": ("The format of the transcript output, in one of "
                        "these options: json, text, srt, verbose_json or vtt."),
    "temperature": "The sampling temperature to use, between 0 and 1."
    }
