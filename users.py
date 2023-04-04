import bcrypt
import uuid
from pymongo import MongoClient

# Using dotenv to load environment variables, development only
# from dotenv import load_dotenv
# load_dotenv()

# Using config.py to load environment variables, production
from config import ATLAS_URI

# Connect to the database
# atlas_url = os.getenv('ATLAS_URI') #! Development only, use config.py for production
atlas_url = ATLAS_URI
client = MongoClient(atlas_url)
db = client['openai-app']
users_collection = db['users']
  
class User:
    def __init__(self, first_name, last_name, email, username, password, role='user'):
        # self.db = Database()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.role = role
        self.balance: float = 0
        self.conversations = []
        self.user_id = self.generate_user_id()

        if role == 'user':
            self.balance = 1.00000
        elif role == 'guest':
            self.balance = 0.20000
        elif role == 'admin':
            self.balance = 100.00000

        try:
            self.password = self.hash_password(password)
        except AttributeError as e:
            # If the password is already hashed, set the password to the hashed password
            self.password = password


    @classmethod
    def check_username(cls, username):
        '''
        Check if the username is unique.

        Args:
            username (str): The username to check
        Returns:
            bool: True if the username is unique, False otherwise
        '''
        user = users_collection.find_one({'username': username})
        return user is None # If user is None, username is unique. Returns True

    def hash_password(self, password):
        '''
        Hash the password using bcrypt.

        Args:
            password (str): The password to hash
        Returns:
            str: The hashed password
        '''
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


    def check_password(self, password: str):
        ''' 
        Check if the password matches the hashed password in the database.
        
        Args:
            password (str): The password to check
        Returns:
            bool: True if the password matches, False otherwise
        '''   
        return bcrypt.checkpw(password.decode('utf-8'), self.password)
    
    def generate_user_id(self):
        '''
        Generate a unique user id for the user.

        Returns:
            str: A unique user id
        '''
        return str(uuid.uuid4())

    def __str__(self):
        '''
        Return a string representation of the user.
        '''
        return f'User: {self.username} {self.email} {self.user_id}'
    
    def __repr__(self):
        '''
        Return a string representation of the user.
        '''
        return f'User: {self.username} {self.email} {self.user_id}'
    
    def __eq__(self, other):
        '''
        Check if two users are equal.
        '''
        return self.user_id == other.user_id
    
    # Store the user data in a json file
    def to_json(self):
        '''
        Return a json representation of the user.
        '''
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "balance": self.balance,
            "conversations": self.conversations
        }

    # Store the user data in the database. On user creation, the user is saved to the database.
    def save2db(self):
        '''
        Save the user data to the database, and checks for unique username. Used on user creation.
        '''
        if self.check_username(self.username):
            users_collection.insert_one(self.to_json())
            # print(f'User {self.username} saved to database')
            return True
        else:
            print('\nError: Username already exists')
            return False


    def delete(self):
        '''
        Delete the user from the database.
        '''
        users_collection.delete_one({'user_id': self.user_id})
        print(f'User {self.username} deleted from database')


    def update(self, field, value):
        '''
        Update the user data in the database.

        Args:
            field (str): The field to update
            value (str): The value to update the field to
        '''
        users_collection.update_one({'user_id': self.user_id}, {'$set': {field: value}})
        # print(f'User {self.username} updated in database')


    @classmethod
    def authenticate(cls, username, password):
        '''
        Authenticate the user based on provided username and password.

        Args:
            username (str): The username to check
            password (str): The password to check

        Returns:
            User: The user if authenticated, None otherwise
        '''

        user_data = users_collection.find_one({'username': username})

        if user_data:
            # User exists, check password
            hashed_password = user_data['password']
            #if bcrypt.checkpw(password.decode('utf-8'), hashed_password):
            if bcrypt.checkpw(bytes(password, 'utf-8'), hashed_password):
                # Password matches, get the user and return
                user = cls(
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    email=user_data['email'],
                    username=user_data['username'],
                    password=hashed_password,
                    role=user_data['role']
                )
                user.user_id = user_data['user_id']
                user.balance = float(user_data['balance'])
                user.conversations = user_data['conversations']
                return user
            else:
                # Password does not match
                return None
        else:
            # User does not exist
            return None
        

    @classmethod    
    def guest(cls):
        '''
        Return a guest user.
        '''
        return cls(
            first_name='Guest',
            last_name='',
            email='',
            username='guest',
            password='',
            role='guest')


    def set_role(self, role: str):
        '''
        Set the user role.

        Args:
            role (str): The role to set
        '''
        if role in ['user', 'admin', 'guest']:
            self.role = role
        else:
            print('Error: Invalid role assignment')


    @classmethod
    def get_user_by_username(cls, username):
        '''
        Get a user from the database by username.

        Args:
            username (str): The username to search for
        Returns:
            User: The user if found, None otherwise
        '''
        user = users_collection.find_one({'username': username})
        return user
    
    def expense(self, amount):
        '''
        Reduce the user balance by the amount.

        Args:
            amount (float): The amount to reduce the balance by
        '''
        self.balance -= amount
        self.update('balance', self.balance)

    def save(self):
        '''
        Save the user to the database. Used on user update on application exit.
        '''
        users_collection.update_one({'user_id': self.user_id}, {'$set': self.to_json()})




