import openai
import json
import stdiomask
import uuid
import json
import os
import time

from exceptions import ChatError, ModelNotFound # Custom exceptions for rhe chat application
from datetime import datetime
from users import User
from pymongo import MongoClient

# Using dotenv to load environment variables, development only
# from dotenv import load_dotenv
# load_dotenv()


# Using config.py to load environment variables, production
from config import ATLAS_URI, API_KEY


# Connect to the database
# atlas_url = os.getenv('ATLAS_URI')    #! Development only, use config.py for production
# --- OR ---
atlas_url = ATLAS_URI
client = MongoClient(atlas_url)
db = client['openai-app']
users_collection = db['users']



# Set the OpenAI API key
# openai.api_key = os.getenv('API_KEY') #! Development only, use config.py for production
openai.api_key = API_KEY


DEFAULT_SETTINGS = {
    'model': 'gpt-3.5-turbo',
    'max_tokens': 1000,
    'temperature': 1.2,
    'top_p': 1,
    'frequency_penalty': 0.5,
    'presence_penalty': 0.5,
}

settings = DEFAULT_SETTINGS.copy()


def login_prompt():
    print("Would you like to login, or continue as a guest?")
    print("1. Login")
    print("2. Create an account")
    print("3. Continue as a guest")
    print("4. Exit")

    action = input("\nEnter a number: ")
    
    while action not in ['1', '2', '3', '4']:
        print("Error: Invalid input. Please try again.")
        action = input("\nEnter a number: ")

    if action == '1':
        user = login()
    elif action == '2':
        user = signup()
    elif action == '3':
        user = User.guest()
    elif action == '4':
        exit()

    return user


def login():
    incorrect_attempts = 0

    while incorrect_attempts < 3:
        username = input("\nEnter your username: ")
        password = stdiomask.getpass("Enter your password: ", mask='*')

        user = User.authenticate(username, password)

        if user:
            print("\nAuthentication successful!\n")
            return user
        else:
            print("\nError: Invalid username or password.")
            if incorrect_attempts == 1:
                print("Attempts Remaining: 1")
            print("Please try again.")
            incorrect_attempts += 1

    print("\nToo many incorrect attempts. Continuing as a guest.\n")
    return User.guest()


def signup():
    print("\nPlease enter the following information to create an account:")
    first_name = input("First name: ")
    last_name = input("Last name: ")
    email = input("Email: ")
    username = input("Username: ")
    password = input("Password: ")

    # Check if the username is unique
    while not User.check_username(username):
        print("Error: Username is already taken.")
        username = input("Username: ")

    user = User(first_name, last_name, email, username, password, role='user')
    if user.save2db():
        print("\nAccount created successfully!")
        return user
    else:
        print("\nPlease try again.")
        return None


def get_model_list(display: bool = False):
    # For the full list of models, use this:
    # models = openai.Model.list()
    # models = models['data']

    # Trimmed down list of models:
    with open('models.json') as f:
        models_json = json.load(f)

    models = models_json["models"]

    if display:
        model_list = [model['display'] for model in models]
    else:
        model_list = [model['id'] for model in models]

    return model_list


def print_model_list(model_list):
    print("Available Models:")
    for i, model in enumerate(model_list, start=1):
        print(f"{i}. {model}")


def list_admin_options():
    print("\nAdmin Options:")
    print("help -> View this help menu")
    print("users -> View all users")
    print("roles -> Set user roles")
    print("prompts -> Customize prompt parameters")
    print("chat -> Proceed to chat with the AI. Ends the admin session.\n")

def get_user_list():
    users = users_collection.find()
    user_list = [user for user in users]
    return user_list

def print_user_list(user_list):
    print("\nUsers:")
    for user in user_list:
        print(user.__str__())
    print()


def set_user_role():
    print("Enter the username of the user you would like to modify:")
    username = input("Username: ")

    user = User.get_user_by_username(username)

    if user:
        print(f"User found: {user}")
        print("Enter the new role for this user:")
        role = input("Role: ")

        while role not in ['user', 'admin']:
            print("Error: Invalid role. Please try again.")
            role = input("Role: ")

        user.role = role
        user.save2db()
        print("Role updated successfully!")
    else:
        print("Error: User not found.")

def list_prompt_options():
    print("\nPrompt Options:")
    print("temperature -> Set the temperature")
    print("max_tokens -> Set the maximum number of tokens")
    print("top_p -> Set the top p value")
    print("frequency_penalty -> Set the frequency penalty")
    print("presence_penalty -> Set the presence penalty")
    print()


def set_temperature():
    print("Enter a new temperature value:")
    temperature = float(input("Temperature: "))

    while temperature < 0 or temperature > 1:
        print("Error: Invalid temperature. Please try again.")
        temperature = float(input("Temperature: "))

    customTemp = temperature

    print("Temperature updated successfully!")
    return customTemp

def set_max_tokens():
    print("Enter a new max tokens value:")
    max_tokens = int(input("Max Tokens: "))

    while max_tokens < 0 and max_tokens > 8000:
        print("Error: Invalid max tokens value. Please try again.")
        max_tokens = int(input("Max Tokens: "))

    customMaxTokens = max_tokens

    print("Max tokens updated successfully!")
    return customMaxTokens

def set_top_p():
    print("Enter a new top p value:")
    top_p = float(input("Top p: "))

    while top_p < 0 or top_p > 1:
        print("Error: Invalid top p value. Please try again.")
        top_p = float(input("Top p: "))

    customTopP = top_p

    print("Top p updated successfully!")
    return customTopP

def set_frequency_penalty():
    print("Enter a new frequency penalty value:")
    frequency_penalty = float(input("Frequency Penalty: "))

    while frequency_penalty < 0 or frequency_penalty > 1:
        print("Error: Invalid frequency penalty value. Please try again.")
        frequency_penalty = float(input("Frequency Penalty: "))

    customFrequencyPenalty = frequency_penalty

    print("Frequency penalty updated successfully!")
    return customFrequencyPenalty

def set_presence_penalty():
    print("Enter a new presence penalty value:")
    presence_penalty = float(input("Presence Penalty: "))

    while presence_penalty < 0 or presence_penalty > 1:
        print("Error: Invalid presence penalty value. Please try again.")
        presence_penalty = float(input("Presence Penalty: "))

    customPresencePenalty = presence_penalty

    print("Presence penalty updated successfully!")
    return customPresencePenalty

def set_prompt_parameters():

    updating = True

    while updating:
        print("Enter the name of the parameter you would like to modify. Type '-list' to view all parameters. Type '-done' when all changes have been made.\n")
        parameter = input("Parameter: ")
        if parameter == '-list':
            list_prompt_options()
        elif parameter == '-done':
            break
        else:
            while parameter not in ['temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']:
                print("Error: Invalid parameter. Please try again.")
                parameter = input("Parameter: ")

            if parameter == 'temperature':
                temp = set_temperature()
                settings['temperature'] = temp
            elif parameter == 'max_tokens':
                max_t = set_max_tokens()
                settings['max_tokens'] = max_t
            elif parameter == 'top_p':
                top_p = set_top_p()
                settings['top_p'] = top_p
            elif parameter == 'frequency_penalty':
                fp = set_frequency_penalty()
                settings['frequency_penalty'] = fp
            elif parameter == 'presence_penalty':
                pp = set_presence_penalty()
                settings['presence_penalty'] = pp
    
    print("Proceeding with the following parameters:")
    print(f"Max Tokens: {settings['max_tokens']}")
    print(f"Temperature: {settings['temperature']}")
    print(f"Top P: {settings['top_p']}")
    print(f"Frequency Penalty: {settings['frequency_penalty']}")
    print(f"Presence Penalty: {settings['presence_penalty']}")


def handle_admin(user: User):
    print("Admin privileges enabled. Would you like to begin an admin session? (y/n)")
    admin_session = input("Admin: ")
    print()

    while admin_session not in ['y', 'n']:
        print("Error: Invalid input. Please try again.")
        admin_session = input("Admin: ")
        print()
    
    if admin_session == 'n':
        print("Proceeding to chatbot.\n")
        # End the function
        return
        
    elif admin_session == 'y':
        print("Admin session initiated.")
        print("To view a list of admin options, type 'help'.")
        print('To end the admin session and use the chatbot, type "chat".\n')

    # Begin admin session 
    admin = True
    while admin:
        admin_input = input(f'{user.username} > ')
        if admin_input == 'users':
            user_list = get_user_list()
            print_user_list(user_list)
        elif admin_input == 'roles':
            set_user_role()
        elif admin_input == 'prompts':
            set_prompt_parameters()
        elif admin_input == 'help':
            list_admin_options()
        elif admin_input == 'chat':
            admin = False
        else:
            print("Error: Invalid command. Please try again.")


def get_cost(response=None, model=None, num_of_tokens=None) -> float:
    if response:
        model = response['model']
        response_tokens = response['usage']['completion_tokens']
        prompt_tokens = response['usage']['prompt_tokens']
        total_tokens = response_tokens + prompt_tokens
    elif model and num_of_tokens:
        total_tokens = num_of_tokens
    else:
        raise ValueError("Error: Invalid parameters. Please try again.")

    # Get the model cost per token
    with open('models.json') as f:
        models_json = json.load(f)


    try:
        if model not in [model['id'] for model in models_json["models"]]:
            raise ModelNotFound(f"Error: Model ({model}) not found.")
        
        for m in models_json['models']:
            if m['id'] == model:
                # Calculate the cost of the response
                cpt = m['cpt']
                cost = round(total_tokens * cpt, 8)
                return cost
            
    except ModelNotFound as e:
        # Could not find the model
        # Search for the model family...
        for m in models_json['models']:
            if m['family'] in model:
                # Calculate the cost of the response
                cpt = m['cpt']
                cost = round(total_tokens * cpt, 8)
                return cost

    except Exception as e:
        print(e)
        print("Error: Could not find model cost. Please rerun the application and select a different model.")
        exit()


def check_balance(user: User) -> bool:
    # Call get_cost() with keyword arguments
    max_cost = get_cost(model=settings['model'], num_of_tokens=settings['max_tokens']) # Maximum possible cost of next response
    #TODO: Could adjust max_tokens for next request based on user balance

    if user.balance < max_cost:
        print("Error: Insufficient funds. Please add more funds to your account.")
        return False
    
    return True


def select_model():
    '''
    Prompts the user to select a model from the model list.
    Updated to accept model numbers or model names as input.
    '''
    model_display_list = get_model_list(display=True) # Get the model list with the display name
    print_model_list(model_display_list)
    print()

    model_id_list = get_model_list() # Get the model list with the id, what is stored in models.json
    
    # Create a dictionary to map model numbers to model names
    model_dict = {}
    for i, model in enumerate(model_id_list, start=1):
         model_dict[i] = model

    selected_model = input("Enter a model name/number. Press 'enter' to accept the default: ").lower()

    try:
        selected_model = int(selected_model)
        # User entered a number
        selected_model = model_dict[selected_model]
    except ValueError:
        # User entered a string
        pass

    if not selected_model:
        # Set default model
        selected_model = 'gpt-3.5-turbo'
        print('Using default model: gpt-3.5-turbo\n')

    while selected_model not in model_id_list:
        print('Error: Invalid model name. Please try again.')
        selected_model = input("Enter a model name: ").lower()

    # Store the selected model in the settings dictionary
    settings.update({'model': selected_model})


def converse(user: User, conversation: list, session: dict):
    # --------------Start conversation--------------
    print(f"Beginning conversation with {settings['model']}...")
    print("-" * 50)
    print("Instructions:")
    print("Enter a prompt to send to the chatbot (use '\\n' for a newline). Type '-end' to end the conversation.")
    print("At any time, you may enter a command. To view a full list of commands, type '-help'.")

    # --------------Start handling user input--------------

    # Run the loop until the user ends the conversation
    while True:
        # Check if the user has enough funds to continue the conversation
        if not check_balance(user):
            # End the conversation
            break

        # Get user input
        user_input = input(f'{user.username} > ').replace('\\n', '\n')
        result = interpret_request(user, session, user_input)
        response = None
        # Handle the result
        if result == True:
            # User entered a command
            continue
        elif result == False:
            # User ended the conversation
            break
        elif isinstance(result, str):
            # User entered a prompt
            prompt = result

            while True:
                try:
                    response = chat(prompt, conversation)
                except ChatError:
                    # Ask the user if they would like to try again
                    while True:
                        try_again = input("Would you like to try to send the message again? (y/n): ")
                        if try_again == 'y':
                            # Continue the conversation loop
                            break
                        elif try_again == 'n':
                            # Ends the conversation
                            break
                        else:
                            print("Error: Invalid input. Please try again.")
                            continue
                    if try_again == 'n':
                        break # End the inner while loop
                except Exception as e:
                    print(e)
                    break
                else:
                    # No exceptions were raised during error handling
                    break

            if not response:
                # Did not receive a response from the API
                break

            # Received response from API, now process it
            #TODO: Check response status code
            answer = response['choices'][0]['message']['content']
            print(f"{settings['model']} > {answer}")

            # Add the response to the conversation
            conversation.append({"role": "assistant", "content": answer})  

            # Deduct the cost of the response from the user's balance
            cost = get_cost(response=response)
            User.expense(user, cost)

            # Update the session details
            session['num_of_requests'] += 1
            session['expense'] += cost

        elif result is None:
            # User entered "-end"
            break

        else:
            print("Unknown response error. Please try again.")
            continue
    
    session['end_time'] = datetime.now().isoformat()

    return session


def chat(prompt: str, conversation: list):
    # Format the prompt
    message = {"role": "user", "content": prompt}

    # Redefining messages as conversation
    # This is how you get continuous conversation. Conversation is a list of messages
    #! Important: Stored as "conversation" locally, sent to API as "messages"
    conversation.append(message)

    # Settings + Prompt/Messages = Request
    settings.update({'messages': conversation})
    request = settings

    # Send request to API
    try:
        response = openai.ChatCompletion.create(**request)
    except Exception as e:
        # Most commonly returns: openai.error.APIError
        # Gives error when asking: "do you have a character or word limit?"
        print(e)
        conversation.remove(message)
        raise ChatError("Error: Could not connect to the API. Please try again.")

    return response


def interpret_request(user: User, session: dict, request: str):
    '''
    Interprets the user's request and handles commands.

    Returns:
        prompt (str): The prompt to send to the chatbot.
        True: The user entered a command. Continue the loop.
        False: The user ended the conversation. Break the loop.
    '''
    # Check if the user entered a command
    commands = {
        '-help': 'Display a list of commands',
        '-balance': 'Display the user\'s balance',
        '-model': 'Change the model',
        '-end': 'End the conversation',
        '-info': 'Show the session/conversation info'
    }
    
    if request.startswith('-'):
        # User entered a command
        if request == '-help':
            # Display a list of commands
            for command, description in commands.items():
                print(f"{command}: {description}")
        elif request == '-balance':
            # Display the user's balance
            print(f"Balance: {user.balance}")
        elif request == '-model':
            # Change the model
            select_model()
        elif request == '-end':
            # End the conversation
            print("Ending conversation...")
            print("-" * 50)
            return None
        elif request == '-info':
            # Show session info
            print("Not yet implemented.")
            show_info(session)
            #TODO: show_session_info()
            pass
        else:
            # Invalid command
            print("Error: Invalid command. Please try again.")
    else:
        # User entered a prompt
        # Send the prompt to the API
        prompt = request
        return prompt

    return True

def show_info(session: dict):
    '''
    Displays the session/conversation info.
    '''
    print("Would you like info on the last response received or the full session?")
    print("1. Last response")
    print("2. Full session")
    print("3. Cancel")
    user_input = input("Enter a number: ")

    while user_input not in ['1', '2', '3']:
        print("Error: Invalid input. Please try again.")
        user_input = input("Enter a number: ")

    if user_input == '1':
        # Show last response info.
        # I think because this is called in the loop, the response is in scope
        if response is None:
            print("Error: No response found. This feature is still in development.")
            return
        response_info = analyze_response(response)
        print("Response info:")
        for key, value in response_info.items():
            print(f"{key}: {value}")

    elif user_input == '2':
        # Show full session info
        # I think because this is called in the loop, the session is also in scope
        for key, value in session.items():
            print(f"{key}: {value}")

    elif user_input == '3':
        # Cancel
        return


def analyze_response(response):
    model = response['model']
    response_type = response['object']
    response_tokens = response['usage']['completion_tokens']
    prompt_tokens = response['usage']['prompt_tokens']
    total_tokens = response_tokens + prompt_tokens

    cost = get_cost(response)

    results = {}

    results['model'] = model
    results['response_type'] = response_type
    results['response_tokens'] = response_tokens
    results['prompt_tokens'] = prompt_tokens
    results['total_tokens'] = total_tokens
    results['cost'] = cost

    return results

def save_conversation(user: User, conversation: list, session: dict):
    '''
    Saves the conversation to the database.
    '''
    #TODO: Prevent saving the same conversation twice

    # Convert conversation list to dict
    conversation_dict = {
        'messages': [{'user': msg['role'], 'content': msg['content']} for msg in conversation],
        'session': session
        }

    # Save conversation to database
    user.conversations.append(conversation_dict)
    user.save()


def export_conversation(user: User, conversation: list, filename: str):
    '''
    Exports the conversation to a text file.
    '''
    # Get the user's first name
    first_name = user.first_name

    # Get the current date and time
    now = datetime.now()
    date = now.strftime("%m-%d-%Y")
    time = now.strftime("%H-%M-%S")

    # Create the filename
    if not filename:
        filename = f"{first_name}_{date}_{time}.txt"
    else:
        if not filename.endswith('.txt'):
            filename = f"{filename}.txt"

    # Create the filepath. Current directory/exports/filename
    cd = os.path.abspath(os.curdir)
    filepath = os.path.join(cd, 'exports', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Create the file
    with open(filepath, 'w') as f:
        # Write the conversation to the file
        for message in conversation:
            f.write(f"{message['role']}: {message['content']}\n")

    print(f"Conversation exported to {filepath}")


def main():
    print("-" * 50)
    print("\nWelcome to the OpenAI API Chatbot Test\n")

    user = login_prompt()

    if user:
        print(f"Welcome, {user.first_name}!\n")
    else:
        print("Unkown user error. Continuing as a guest.\n")
        user = User.guest()

    if user.role == 'admin':
        handle_admin(user)

    # Get users balance from the database
    balance = user.balance
    print(f"Your current balance is ${balance:.5f}\n")
    
    # if user.role == 'guest':
    #     #TODO: Implement guest class inheriting from User class.
    #     #TODO: Guest class will have uuid to make sure users on the same machine are not creating multiple guest accounts.
    #     print("You are currently using the guest account. Your session will end after $0.20.\n")
    #     print("Sign up for a free account to continue using the application to add funds.\n")

    # Select a model
    select_model()

    conversation = [] #TODO: Maybe make this a class

    #TODO: Need to add a way for admin to add system message before the chat starts. Don't want to ask admin for more input. Refactor later
    if user.role == 'admin':
        system = input ("Would you like to add a system message? (y/n): ")
        if system == 'y':
            system_message = input("Enter your message: ")
            message = {"role": "system", "content": system_message}
            conversation.append(message)

    # Begin the conversation
    conversation_loop = True

    while conversation_loop:
        # Initialize session details
        session_details = {
            'id': str(uuid.uuid4()),
            'user': user.username,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'num_of_requests': 0,
            'expense': 0.00,
        }

        # Begin the conversation
        info = converse(user, conversation, session_details) # Loops until user ends conversation. Info holds the session details

        # End the conversation
        # Post conversation actions loop
        while True:
            action = input("To start a new conversation, type 'chat', or select another option. Type 'options' to see a list of options: ").lower()

            commands = {
                'chat': 'Start a new conversation',
                'options': 'Show a list of options',
                'exit': 'Exit the program',
                'change': 'Change the model. Use chat after changing the model to start a new conversation.',
                'balance': 'Check your balance',
                'info': 'View the conversation info',
                'save': 'Save the conversation',
                'export': 'Export the conversation to a text file',
            }

            #TODO: Differentiate between session and conversation info. Users should be able to continue the conversation after viewing the session info
            #TODO: Add load conversation option

            while action not in ['chat', 'exit', 'options', 'change', 'balance', 'info', 'save', 'export']:
                print('Error: Invalid input. Please try again.')
                action = input("To start a new conversation, type 'chat', or select another option. Type 'options' to see a list of options: ").lower()

            if action == 'options':
                for command, description in commands.items():
                    print(f"{command}: {description}")
                    continue
            elif action == 'chat':
                # Start a new conversation
                # Exit the post-response actions loop. Continue the conversation loop.
                break
            elif action == 'exit':
                # Exit the post-response actions loop, and end the main loop
                conversation_loop = False
                break
            elif action == 'change':
                # Change the model
                select_model()
                print(f'{settings["model"]} will be used for the next conversation.')
                continue
            elif action == 'balance':
                # Display the user's balance
                print(f"Balance: {user.balance}")
                continue
            elif action == 'info':
                # Show session info
                for key, value in info.items():
                    print(f"{key}: {value}")
                continue
            elif action == 'save':
                # Save the conversation
                save_conversation(user=user, conversation=conversation, session=info)
                print('Conversation saved to user profile.')
                continue
            elif action == 'export':
                # Export the conversation to a file
                name = input("Enter a name for the file, or press enter to use the default name: ")
                if name:
                    filename = f"{name}.txt"
                    export_conversation(user, conversation, filename)
                else:
                    export_conversation(user, conversation, None)
                continue
            else:
                print('Error: Invalid input. Please try again.')
                continue

    # End of conversation loop, meaning the user has ended the conversation. Can choose to start a new conversation or exit the program in the post-response actions loop.

    # Save updated user information to the database
    user.save()

    # Application exit
    client.close()
    print('Thank you for using the OpenAi API Chatbot Test')


if __name__ == '__main__':
    main()



