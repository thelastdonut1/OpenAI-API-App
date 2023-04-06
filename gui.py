import tkinter as tk
from tkinter import ttk
import threading
import openai
import os
import json
import uuid

from conversation import Conversation
from datetime import datetime
from config import API_KEY

class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("OpenAI Chat")
        self.geometry("500x650")

        # Set background color to light blue
        self.configure(bg="#def")

        self.create_widgets()
    
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.chat_page.save_conversation()
        # Standard close event
        self.destroy()


    def create_widgets(self):
        nav_style = ttk.Style()
        nav_style.configure("nav", background="#343434")

        nav_button_style = ttk.Style()
        nav_button_style.configure("Navbar.TButton", background="#5c5c5c", foreground="#fff", relief=tk.FLAT)
        nav_button_style.map("Navbar.TButton",
                   background=[("active", "#7c7c7c")],
                   relief=[("active", tk.FLAT)])

        self.navbar = ttk.Frame(self)
        self.navbar.pack(fill=tk.X)

        self.chat_button_nav = ttk.Button(self.navbar, text="Chat", command=self.show_chat, style="Navbar.TButton")
        self.chat_button_nav.pack(side=tk.LEFT)

        self.settings_button_nav = ttk.Button(self.navbar, text="Settings", command=self.show_settings, style="Navbar.TButton")
        self.settings_button_nav.pack(side=tk.LEFT)

        self.header_label = ttk.Label(self, text="OpenAI Chat", font=("Arial", 24))
        self.header_label.pack(pady=5)

        self.chat_page = ChatPage(self)
        self.chat_page.pack(fill=tk.BOTH, expand=True)

        self.settings_page = SettingsPage(self)
        self.settings_page.pack(fill=tk.BOTH, expand=True)
        self.settings_page.pack_forget()

        # Saved conversations listbox
        # ---------------------------------------------
        # Create the chat sessions frame
        self.conversations_frame = ttk.Frame(self)
        self.conversations_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create the scrollbar for the chat sessions listbox
        self.conversations_scrollbar = ttk.Scrollbar(self.conversations_frame)
        self.conversations_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the chat sessions listbox
        self.conversations_listbox = tk.Listbox(self.conversations_frame, yscrollcommand=self.conversations_scrollbar.set)
        self.conversations_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.conversations_scrollbar.config(command=self.conversations_listbox.yview)

        # Populate the chat sessions listbox
        # ---------------------------------------------
        self.list_saved_conversations()
        self.conversations_listbox.bind('<<ListboxSelect>>', self.load_conversation)
        self.conversations_listbox.selection_set(0)

        self.show_chat()

    def list_saved_conversations(self):
        # Get the path of the saved conversations folder
        saved_conversations_path = os.path.join(os.getcwd(), "conversations")

        # If the saved conversations folder does not exist, create it
        if not os.path.exists(saved_conversations_path):
            os.mkdir(saved_conversations_path)

        # Get the list of files in the saved conversations folder
        saved_conversations = os.listdir(saved_conversations_path)
        
        # List "New Conversation" for the empty window on app start
        self.conversations_listbox.insert(tk.END, "New Conversation")

        # Load the conversations from the files
        for conversation in saved_conversations:
            name = conversation.split(".")[0] # Removes the .json extension
            name = name.replace("-", " ") # Replaces underscores with spaces
            self.conversations_listbox.insert(tk.END, name)

    def show_chat(self):
        self.chat_page.pack(fill=tk.BOTH, expand=True)
        self.settings_page.pack_forget()
        self.chat_button_nav.configure(state=tk.DISABLED)
        self.settings_button_nav.configure(state=tk.NORMAL)

    def show_settings(self):
        self.settings_page.pack(fill=tk.BOTH, expand=True)
        self.chat_page.pack_forget()
        self.chat_button_nav.configure(state=tk.NORMAL)
        self.settings_button_nav.configure(state=tk.DISABLED)

    def load_conversation(self, event: tk.Event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            convo = event.widget.get(index)
            self.chat_page.load_conversation(convo)

class ChatPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.create_widgets()

        self.messages = []

        system_message = {"role": "system",
                          "content": "You are a helpful assistant!"}

        self.messages.append(system_message)

        self.conversation = Conversation(self.messages)


    def create_widgets(self):
        self.chat_frame = ttk.Frame(self)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_text = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        self.entry_frame = ttk.Frame(self)
        self.entry_frame.pack(fill=tk.X, padx=10, pady=10)

        self.prompt_entry = ttk.Entry(self.entry_frame)
        self.prompt_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)

        self.send_button = ttk.Button(self.entry_frame, text="Send", command=self.send_prompt)
        self.send_button.pack(side=tk.RIGHT)

    def send_prompt(self):
        prompt = self.prompt_entry.get()
        if prompt:
            self.append_message("user", prompt)
            self.prompt_entry.delete(0, tk.END)

            threading.Thread(target=self.get_response, args=(prompt,)).start()

    def append_message(self, role, message):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"{role}: {message}\n")
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def get_response(self, prompt):
        self.send_button.configure(state=tk.DISABLED)

        self.messages.append({"role": "user", "content": prompt})

        try:
            response = openai.ChatCompletion.create(model=model, messages=self.messages)
        except Exception as e:
            self.append_message("system", f"Error: {e}")
            self.send_button.configure(state=tk.NORMAL)
            return
        
        answer = response['choices'][0]['message']['content']
        self.append_message("assistant", answer)

        self.send_button.configure(state=tk.NORMAL)
    
    def load_conversation(self, name):
        '''
        Loads a former conversation into the chat text
        '''
        # ---- Save the current conversation ----
        if self.conversation.messages:
            self.save_conversation()

        # ---- Load the selected conversation ----
        convo_dir = os.path.join(os.getcwd(), "conversations")
        filepath = os.path.join(convo_dir, name + ".json")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Conversation {name} does not exist")
        
        with open(filepath, "r") as f:
            data = json.load(f)

        convo = Conversation.load(data)
        # Clear the chat text
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.configure(state=tk.DISABLED)

        # Load the session into the chat text
        for msg in convo.messages:
            for key, value in msg.items():
                self.append_message(key, value)
        
        self.conversation = convo
        self.messages = convo.messages


    def save_conversation(self):
            convo_dir = os.path.join(os.getcwd(), "conversations")
            if not os.path.exists(convo_dir):
                os.mkdir("conversations")

            # Remove the system message
            system_message = {"role": "system", "content": "You are a helpful assistant!"}
            content = self.messages.remove(system_message)

            # If there are no messages, do not save
            if not self.messages:
                return

            # There are messages, so name the conversation
            filename = self.conversation.get_name().replace(" ", "-") + ".json"

            file_path = os.path.join("conversations", filename)

            with open(file_path, "w") as f:
                json.dump(self.conversation.__dict__, f, indent=4)

    
class SettingsPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.create_widgets()

    def create_widgets(self):
        self.model_label = ttk.Label(self, text="Model:")
        self.model_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)

        self.model_combobox = ttk.Combobox(self, values=["davinci", "gpt-4-32k", "gpt-4", "gpt-3.5-turbo"])
        self.model_combobox.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)

        self.temp_slider_label = ttk.Label(self, text="Temperature:")
        self.temp_slider_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)

        self.temp_slider = ttk.Scale(self, from_=0.0, to=1.0, value=0.5, length=200, orient=tk.HORIZONTAL)
        self.temp_slider.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)



if __name__ == "__main__":
    openai.api_key = API_KEY
    model = "gpt-3.5-turbo"

    app = ChatApp()
    app.mainloop()