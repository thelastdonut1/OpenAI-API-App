import tkinter as tk
from tkinter import ttk
import threading
import openai
import os
import json
import uuid
import themes
# import sv_ttk #! This is a custom ttk theme. May use in the future.

from PIL import Image, ImageTk
from conversation import Conversation
from datetime import datetime
from config import API_KEY


# Set the application color theme
#! Will need to implement a way to change the theme within the app
theme = themes.light_theme

BACKGROUND = theme["BACKGROUND"]
NAVBAR = theme["NAVBAR"]
NAVBAR_HIGHLIGHT = theme["NAVBAR_HIGHLIGHT"]
NAVBAR_TEXT = theme["NAVBAR_TEXT"]
FIELD_BACKGROUND = theme["FIELD_BACKGROUND"]
PROMPT_BACKGROUND = theme["PROMPT_BACKGROUND"]
#FIELD_BACKGROUND = theme["FIELD_BACKGROUND"]
TEXT = theme["TEXT"]
LISTBOX = theme["LISTBOX"]


class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # sv_ttk.set_theme("dark")

        self.title("OpenAI Chat")
        self.geometry("1000x700")
        self.minsize(400, 500)

        # Set background color
        self.configure(bg="#222831")
        
        # Set the icon
        png = Image.open("icons/gpt.png")
        photo = ImageTk.PhotoImage(png)
        self.iconphoto(False, photo)

        self.create_widgets()
    
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.chat_page.save_conversation()
        # Standard close event
        self.destroy()


    def create_widgets(self):
        style = ttk.Style()
        ttk.Style.theme_use(style, "clam")
        # For some reason, you have to set the style to clam before you can configure it. I don't know why.
        # If you do not, changing the background color will not work. It changes the color behind the
        # button, not the button itself.
        #! See docs on Styles: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html

        # Create the navbar frame
        self.navbar = ttk.Frame(self)
        style.configure("Navbar.TFrame", background=NAVBAR)
        self.navbar.configure(style="Navbar.TFrame")
        self.navbar.pack(fill=tk.X)

        # Create the navbar buttons
        # ---------------------------------------------
        # Define the style for the navbar buttons
        style.configure("Navbar.TButton", background=NAVBAR, foreground=TEXT, relief=tk.FLAT, font=("Arial", 10))
        style.map("Navbar.TButton",
                   background=[("active", NAVBAR_HIGHLIGHT)],
                   relief=[("active", tk.FLAT)])
        
        # Add "Profile" window button to navbar
        self.profile_button_nav = ttk.Button(self.navbar, text="Profile", style="Navbar.TButton")
        self.profile_button_nav.pack(side=tk.RIGHT)
        #TODO: Make profile page. Add command to profile button
        
        # Add "Settings" window button to navbar
        self.settings_button_nav = ttk.Button(self.navbar, text="Settings", command=self.show_settings, style="Navbar.TButton")
        self.settings_button_nav.pack(side=tk.RIGHT)

        # Add "Chat" window button to navbar
        self.chat_button_nav = ttk.Button(self.navbar, text="Chat", command=self.show_chat, style="Navbar.TButton")
        self.chat_button_nav.pack(side=tk.RIGHT)

        # Add "Welcome" label to navbar
        self.welcome_label = ttk.Label(self.navbar, text="Welcome, User", background=NAVBAR, foreground=TEXT,
                                        font=("Arial", 10))
        self.welcome_label.pack(side=tk.LEFT, padx=5)

        # # Add application title at the top of the window
        # self.header_label = ttk.Label(self, text="OpenAI Chat", font=("Arial", 12), background="#222831", foreground="#ececec")
        # self.header_label.pack(pady=5)
        
        # Create the chat page
        self.chat_page = ChatPage(self)
        self.chat_page.pack(fill=tk.BOTH, expand=True)

        # Create the settings page
        self.settings_page = SettingsPage(self)
        self.settings_page.pack(fill=tk.BOTH, expand=True)
        self.settings_page.pack_forget()

        # Show the chat page on app start
        self.show_chat()

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
        style = ttk.Style()
        style.configure("TFrame", background=BACKGROUND) #! Literally the only way I could get this to fkn work

        self.conversations_frame = ttk.Frame(self)
        self.conversations_frame.pack(side=tk.LEFT, fill=tk.Y)
        # Create the "Conversations" label
        self.conversations_label = ttk.Label(self.conversations_frame, text="Conversations", font=("Arial", 12), background=LISTBOX,
                                              foreground=TEXT)
        self.conversations_label.pack(side=tk.TOP, pady=(5, 5))

        style.configure("TScrollbar", background=BACKGROUND, foreground=NAVBAR)

        # Create the scrollbar for the chat sessions listbox
        self.conversations_scrollbar = ttk.Scrollbar(self.conversations_frame, orient=tk.VERTICAL, style="TScrollbar")
        self.conversations_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        self.conversations_listbox = tk.Listbox(self.conversations_frame, yscrollcommand=self.conversations_scrollbar.set,
                                                background=LISTBOX, borderwidth=0, highlightthickness=0, relief=tk.FLAT)
        self.conversations_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Configure the scrollbar to scroll the chat sessions listbox
        self.conversations_scrollbar.config(command=self.conversations_listbox.yview)

        style.configure("Convo.TButton", background=LISTBOX, foreground=TEXT, relief=tk.FLAT,
                        borderwidth=0, anchor=tk.W)
        style.map("Convo.TButton",
                   background=[("active", NAVBAR_HIGHLIGHT)],
                   relief=[("active", tk.FLAT)])

        # Add the "New Conversation" button to the conversations listbox
        self.new_convo_button = ttk.Button(self.conversations_listbox, text="New Conversation", style="Convo.TButton")
        self.new_convo_button.pack(side=tk.TOP, pady=(5, 1), padx=2, fill=tk.X)


        # Load the conversations listbox
        self.list_saved_conversations()
        self.conversations_listbox.bind('<<ListboxSelect>>', self.load_user_conversation)
        self.conversations_listbox.selection_set(0)


        # Frame that will house the chat dialog
        self.chat_frame = tk.Frame(self)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the chat dialog box
        self.chat_text = tk.Text(self.chat_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_text.configure(background=FIELD_BACKGROUND, foreground=TEXT, font=("Arial", 10),
                                 padx=10, pady=10, relief=tk.FLAT, borderwidth=0)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        #TODO: Create the scrollbar for the chat dialog box
        
        # Create the frame that will be under the chat dialog box, and house the entry field and send button
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create a container to house the entry field and send button
        # ---------------------------------------------
        # Allows for the send button to appear to be in the text entry field
        self.prompt_entry_container = tk.Frame(self.entry_frame)
        self.prompt_entry_container.configure(background=PROMPT_BACKGROUND, relief=tk.RAISED, bd=1, padx=5, pady=5)
        self.prompt_entry_container.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Create the text/prompt entry field
        self.prompt_entry = tk.Text(self.prompt_entry_container, height=5, width=30, wrap=tk.WORD,
                                    state=tk.NORMAL, font=("Arial", 10), background=PROMPT_BACKGROUND, bd=0,
                                    foreground=TEXT, padx=5, pady=5)
        self.prompt_entry.pack(fill=tk.X, expand=True, side=tk.LEFT)

        # Create the send button
        style.configure("SendButton.TButton", background=PROMPT_BACKGROUND, foreground=TEXT, relief=tk.FLAT)
        style.map("SendButton.TButton",
                   background=[("active", "#343541")],
                   relief=[("active", tk.SUNKEN)])

        image = Image.open("icons/send.png")
        image = image.resize(((12, 12)), Image.ANTIALIAS)
        send_button_image = ImageTk.PhotoImage(image)
        self.send_button = ttk.Button(self.prompt_entry_container, image=send_button_image, command=self.send_prompt
                                      , style="SendButton.TButton")
        self.send_button.image = send_button_image
        self.send_button.pack(anchor=(tk.S), side=tk.RIGHT)



    def send_prompt(self):
        # prompt = self.prompt_entry.get()
        prompt = self.prompt_entry.get("1.0", tk.END)
        if prompt:
            self.append_message("user", prompt)
            self.prompt_entry.delete("1.0", tk.END)

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
        filename = name.replace(" ", "-") + ".json"
        filepath = os.path.join(convo_dir, filename)

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
            try:
                self.messages.remove(system_message)
            except:
                pass

            # If there are no messages, do not save
            if not self.messages:
                return

            # There are messages, so name the conversation
            filename = self.conversation.get_name().replace(" ", "-") + ".json"

            file_path = os.path.join("conversations", filename)

            with open(file_path, "w") as f:
                json.dump(self.conversation.__dict__, f, indent=4)


    def list_saved_conversations(self):
        # Get the path of the saved conversations folder
        saved_conversations_path = os.path.join(os.getcwd(), "conversations")

        # If the saved conversations folder does not exist, create it
        if not os.path.exists(saved_conversations_path):
            os.mkdir(saved_conversations_path)

        # Get the list of files in the saved conversations folder
        saved_conversations = os.listdir(saved_conversations_path)
        
        for conversation in saved_conversations:
            name = conversation.split(".")[0] # Removes the .json extension
            name = name.replace("-", " ") # Replaces underscores with spaces
            new_button = ttk.Button(self.conversations_listbox, text=name, command=lambda convo=name: self.load_conversation(convo),
                                    style="Convo.TButton")
            new_button.pack(side=tk.TOP, fill=tk.X, pady=1, padx=2)


    def load_user_conversation(self, event: tk.Event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            convo = event.widget.get(index)
            self.load_conversation(convo)


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