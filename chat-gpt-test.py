import openai
import json
import getpass
import uuid
import time

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
        password = getpass.getpass("Enter your password: ")

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
    for model in model_list:
        print(f" - {model}")


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

#TODO: Add async functionality
# async def call_openai_api(request):
#     print("Sent request to API. Waiting for response...")

#     # Start timer
#     start_time = time.time()
    
#     # Make async request to API
#     response = await openai.Completion.create(**request)

#     # End timer
#     end_time = time.time()
#     total_time = end_time - start_time
#     print(f"Received response in {total_time} seconds.\n")

#     return response

def handle_chat(user: User, conversation: list):
    print("Beginning chat session....")
    print("-" * 50)
    print("Enter a prompt (use '\\n' for a newline): ")
    prompt = input(f'{user.username} > ').replace('\\n', '\n')

    message = {"role": "user", "content": prompt}
    # messages = [{"role": "user", "content": prompt}]

    # Redefining messages as conversation
    # This is how you get continuous conversation. Conversation is a list of messages
    #! Important: Stored as "conversation" locally, sent to API as "messages"
    conversation.append(message)

    # Settings + Prompt/Messages = Request
    settings.update({'messages': conversation})
    request = settings

    #TODO: Add async functionality
    # response = await call_openai_api(request)

    # Send request to API
    try:
        response = openai.ChatCompletion.create(**request)
    except Exception as e:
        # Print the error
        print(f'Error: Could not complete request. \n {e}')
        # Ask the user if they would like to try again
        while True:
            try_again = input("Would you like to try again? (y/n): ")
            if try_again == 'y':
                handle_chat()
            elif try_again == 'n':
                # End the function
                return
            else:
                print("Error: Invalid input. Please try again.")
    
    status = response['choices'][0]['finish_reason']

    if status != 'stop':
        # Print the error
        print('Error: Could not complete request. Please try again.')
        # Ask the user if they would like to try again
        while True:
            try_again = input("Would you like to try again? (y/n): ")
            if try_again == 'y':
                handle_chat()
            elif try_again == 'n':
                # End the function
                return
            else:
                print("Error: Invalid input. Please try again.")

    # Print the response
    answer = response['choices'][0]['message']['content']
    print(f"{settings['model']} > {answer}")
    print('-' * 50)

    # Add the response to the conversation
    conversation.append({"role": "assistant", "content": answer})  

    #! May need to return conversation as well
    return response
 
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


def get_cost(response) -> float:
    model = response['model']
    response_tokens = response['usage']['completion_tokens']
    prompt_tokens = response['usage']['prompt_tokens']
    total_tokens = response_tokens + prompt_tokens

    # Get the model cost per token
    with open('models.json') as f:
        models_json = json.load(f)
    
    class ModelNotFound(Exception):
        def __init__(self, message):
            super().__init__(message)
            self.message = message

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


def select_model():
    model_list = get_model_list(display=True) # Get the model list with the display name
    print_model_list(model_list)
    print()

    selected_model = input("Enter a model name: ").lower()

    model_list = get_model_list() # Get the model list with the id

    if not selected_model:
        # Set default model
        selected_model = 'gpt-3.5-turbo'
        print('Using default model: gpt-3.5-turbo\n')

    while selected_model not in model_list:
        print('Error: Invalid model name. Please try again.')
        selected_model = input("Enter a model name: ").lower()

    # Store the selected model in the settings dictionary
    settings.update({'model': selected_model})


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


    # Initialize session details
    session_details = {
        'id': str(uuid.uuid4()),
        'user': user,
        'start_time': datetime.now(),
        'end_time': None,
        'num_of_requests': 0,
        'expense': 0.00,
        'conversation': conversation
    }

    app_loop = True

    while app_loop:
        # Get the prompt from the user
        try:
            response = handle_chat(user, conversation)
        except Exception as e:
            print(f'Error: {str(e)}')
            
        # Add to session cost
        cost = get_cost(response)
        
        # Update the user's balance
        user.expense(cost) #TODO: Actually already updates DB so don't need to do it again

        # Update the session details
        session_details['num_of_requests'] += 1
        session_details['expense'] += cost

        # Check if the user has enough funds to continue
        if user.balance <= 0:
            user.balance = 0 # If they overspent, set their balance to 0. Need to add a check to make sure they don't go negative.
            print("You have run out of funds. Please contact an administrator to add more funds to your account.")
            print("Exiting the application...")
            exit()

        #TODO: Refactor to look for options during the conversation instead of after each response
        # Post-response actions loop
        while True:

            # Ask the user if they want if they want more information
            action = input("Press enter to ask another question, or select another option. Type 'options' to see a list of options: ").lower()

            while action not in ['info', 'exit', 'options', 'change','balance','']:
                print('Error: Invalid input. Please try again.')
                action = input("Press enter to ask another question, or select another option. Type 'options' to see a list of options: ").lower()

            if action == 'options':
                print('info: Get more information about the response.')
                print('change: Change the model.')
                print('balance: Check your balance.')
                print('exit: Exit the program.')
                print('Press enter to continue.')
                continue

            if action == 'exit':
                # Exit the post-response actions loop, and end the main loop
                app_loop = False
                break
            elif action == '':
                # Exit the post-response actions loop, and return to the main loop
                break
            elif action == 'balance':
                print(f'Your current balance is ${user.balance}.')
                continue
            elif action == 'info':
                results = analyze_response(response)

                print(f'Model: {results["model"]}')
                print(f'Response Type: {results["response_type"]}')
                print(f'Response Tokens: {results["response_tokens"]}')
                print(f'Prompt Tokens: {results["prompt_tokens"]}')
                print(f'Total Tokens: {results["total_tokens"]}')
                print(f'Cost: ${results["cost"]:.5f}')

                # Continue the post-response actions loop
                continue
            elif action == 'change':
                # Change the model
                select_model()
                print(f'{settings["model"]} will be used for the next request.')
                continue
            else:
                # Continue the post-response actions loop
                print('Error: Invalid input. Please try again.')
                continue
    
    #TODO: Add a way to save the conversation to the database. Ask the user if they want to save it.
    #TODO: Add a way to export the conversation to a text file

    # Update the session details
    session_details['end_time'] = datetime.now()

    # Save the session details to the database
    #TODO: Save the session details to the database. Need to create a session model and link it to the user model.

    # Save updated user information to the database
    user.save()

    print('Thank you for using the OpenAi API Chatbot Test')


if __name__ == '__main__':
    main()



