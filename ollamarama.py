'''
ollamarama-irc
    An ollama chatbot for irc with infinite personalities
    written by Dustin Whyte

'''

import irc.bot
import time
import textwrap
import threading
import json
import requests

class ollamarama(irc.bot.SingleServerIRCBot):
    """
    An IRC bot that integrates with the Ollama chatbot API, allowing interaction 
    with customizable personalities and models.

    Attributes:
        config_file (str): Path to the configuration file.
        channel (str): The IRC channel the bot will join.
        nickname (str): The bot's nickname.
        password (str): Password for NickServ identification.
        server (str): The IRC server address.
        admins (list): List of admin usernames.
        api_url (str): URL of the Ollama chatbot API.
        options (dict): Options for the API requests.
        models (dict): Available models for the chatbot.
        default_model (str): Default model to use.
        prompt (list): Default system prompt structure.
        default_personality (str): Default personality for the chatbot.
        model (str): Current chatbot model in use.
        personality (str): Current personality in use.
        messages (dict): History of conversations per user.
    """
    def __init__(self, port=6667):
        """
        Initialize the bot with configuration and setup.

        Args:
            port (int): Port to connect to the IRC server. Defaults to 6667.
        """
        self.config_file = "config.json"
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            f.close()
        
        self.channel, self.nickname, self.password, self.server, self.admins = config["irc"].values()
        irc.bot.SingleServerIRCBot.__init__(self, [(self.server, port)], self.nickname, self.nickname)
        self.api_url, self.options, self.models, self.default_model, self.prompt, self.default_personality = config["ollama"].values()

        self.model = self.default_model
        self.personality = self.default_personality

        self.messages = {}

    def chop(self, message):
        """
        Break a message into lines of at most 420 characters, preserving whitespace.

        Args:
            message (str): The message to be chopped.

        Returns:
            list: A list of strings, each within the 420-character limit.
        """
        lines = message.splitlines()
        newlines = [] 
        for line in lines:
            if len(line) > 420:
                wrapped_lines = textwrap.wrap(
                    line,
                    width=420,
                    drop_whitespace=False,
                    replace_whitespace=False,
                    fix_sentence_endings=True,
                    break_long_words=False)
                newlines.extend(wrapped_lines)
            else:
                newlines.append(line) 
        return newlines  
    
    def reset(self, c, sender, stock=False):
        """
        Reset the chat history for a user and optionally apply default settings.

        Args:
            c: IRC connection object.
            sender (str): The user initiating the reset.
            stock (bool): Whether to apply stock settings. Defaults to False.
        """
        if sender in self.messages:
            self.messages[sender].clear()
        else:
            self.messages[sender] = []
        if not stock:
            self.set_prompt(c, sender, persona=self.default_personality, respond=False)
            c.privmsg(self.channel, f"{self.nickname} reset to default for {sender}")
        else:
            c.privmsg(self.channel, f"Stock settings applied for {sender}")

    def set_prompt(self, c, sender, persona=None, custom=None, respond=True):
        """
        Set a custom or personality-based prompt for a user.

        Args:
            c: IRC connection object.
            sender (str): The user for whom the prompt is being set.
            persona (str): Predefined personality. Defaults to None.
            custom (str): Custom prompt. Defaults to None.
            respond (bool): Whether to initiate a response. Defaults to True.
        """
        if sender in self.messages:
            self.messages[sender].clear()
        if persona != None and persona != "":
            prompt = self.prompt[0] + persona + self.prompt[1]
        if custom != None  and custom != "":
            prompt = custom
        self.add_history("system", sender, prompt)
        if respond:
            self.add_history("user", sender, "introduce yourself")
            thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
            thread.start()
            thread.join(timeout=30)
            time.sleep(2)

    def add_history(self, role, sender, message):
        """
        Append a message to the user's conversation history.

        Args:
            role (str): The role of the message sender (e.g., 'user', 'assistant', 'system').
            sender (str): The user for whom the message is being added.
            message (str): The message content.
        """
        if sender in self.messages:
            self.messages[sender].append({"role": role, "content": message})
        else:
            if role == "system":
                self.messages[sender] = [{"role": role, "content": message}]
            else:
                self.messages[sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]
        if len(self.messages[sender]) > 24:
            if self.messages[sender][0]["role"] == "system":
                del self.messages[sender][1:3]
            else:
                del self.messages[sender][0:2]

    def respond(self, c, sender, message, sender2=None):
        """
        Generate and send a response to a user.

        Args:
            c: IRC connection object.
            sender (str): The user to respond to.
            message (list): The conversation history.
            sender2 (str): Recipient for the response if the .x function was used.  Defaults to None.
        """
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": self.options
                }
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            data = response.json()
            
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            self.add_history("assistant", sender, response_text)

            if sender2:
                c.privmsg(self.channel, sender2 + ":")
            else:
                c.privmsg(self.channel, sender + ":")
            time.sleep(1)

            lines = self.chop(response_text.strip())
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except Exception as e:
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(e)   

    def on_welcome(self, c, e):
        """
        Handle the welcome event and join the configured channel.

        Args:
            c: IRC connection object.
            e: Event object.
        """
        if self.password != None:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            time.sleep(5)
        
        c.join(self.channel)

        greet = "introduce yourself"
        system = self.prompt[0] + self.personality + self.prompt[1]

        try:
            data = {
                "model": self.model, 
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": greet}
                ], 
                "stream": False,
                "timeout": 30,
                "options": self.options
                }
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            data = response.json()

            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
                
            lines = self.chop(response_text + f"  Type .help to learn how to use me.")
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except:
            pass
            
    def on_nicknameinuse(self, c, e):
        """
        Handle the nickname-in-use event by appending an underscore to the nickname.

        Args:
            c: IRC connection object.
            e: Event object.
        """
        c.nick(c.get_nickname() + "_")

    def on_join(self, c, e):
        """
        Handle the join event to extract and possibly use the username.

        Args:
            c: IRC connection object.
            e: Event object.
        """
        user = e.source
        user = user.split("!")[0]

    def ai(self, c, e, sender, message, x=False):
        """
        Process AI-related commands for generating responses.

        Args:
            c: IRC connection object.
            e: Event object.
            sender (str): The user initiating the command.
            message (list): The command and arguments.
            x (bool): Whether to address the command to another user. Defaults to False.
        """
        if x and message[2]:
            name = message[1]
            message = ' '.join(message[2:])
            if name in self.messages:
                self.add_history("user", name, message)
                thread = threading.Thread(target=self.respond, args=(c, name, self.messages[name],), kwargs={'sender2': sender})
                thread.start()
                thread.join(timeout=30)
            else:
                pass
        else:
            message = ' '.join(message[1:])
            self.add_history("user", sender, message)
            thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
            thread.start()
            thread.join(timeout=30)      
        time.sleep(2)       

    def help_menu(self, c, sender):
        """
        Display the help menu by sending lines to the user.

        Args:
            c: IRC connection object.
            sender (str): The user requesting help.
        """
        with open("help.txt", "r") as f:
            self.help = f.readlines()
        for line in self.help:
            c.notice(sender, line.strip())
            time.sleep(1)
    
    def change_model(self, c, channel=False, model=False):
        """
        Change the chatbot model or list available models.

        Args:
            c: IRC connection object.
            channel (bool): Whether to send messages to the channel. Defaults to False.
            model (str): The model to switch to. Defaults to False.
        """
        if model:
            try:
                if model in self.models:
                    self.model = self.models[model]
                    c.privmsg(self.channel, f"Model set to {self.model}")
            except:
                pass
        else:
            if channel:
                current_model = [f"Current model: {self.model}", f"Available models: {', '.join(sorted(list(self.models)))}"]
                for line in current_model:
                    c.privmsg(self.channel, line)
    
    def handle_message(self, c, e, sender, message):
        """
        Handle user and admin commands by executing the corresponding actions.

        Args:
            c: IRC connection object.
            e: Event object.
            sender (str): The user issuing the command.
            message (list): The command and its arguments.
        """
        user_commands = {
            ".ai": lambda: self.ai(c, e, sender, message),
            f"{self.nickname}:": lambda: self.ai(c, e, sender, message),
            ".x": lambda: self.ai(c, e, sender, message, x=True),
            ".persona": lambda: self.set_prompt(c, sender, persona=' '.join(message[1:])),
            ".custom": lambda: self.set_prompt(c, sender, custom=' '.join(message[1:])),
            ".reset": lambda: self.reset(c, sender),
            ".stock": lambda: self.reset(c, sender, stock=True),
            ".help": lambda: self.help_menu(c, sender)
        }
        admin_commands = {
            ".model": lambda: self.change_model(c, channel=True, model=message[1] if len(message) > 1 else False)
        }

        command = message[0]
        if command in user_commands:
            action = user_commands[command]
            action()
        if sender in self.admins and command in admin_commands:
            action = admin_commands[command]
            action()

    def on_pubmsg(self, c, e):
        """
        Handles public messages sent in the channel.
        Parses the message to identify commands or content directed at the bot
        and delegates to the appropriate handler.

        Args:
            c: IRC connection object.
            e: Event object.
        """
        message = e.arguments[0].split(" ")
        sender = e.source.split("!")[0]

        if sender != self.nickname:
            self.handle_message(c, e, sender, message)
            

if __name__ == "__main__":
    bot = ollamarama()

    bot.start()
