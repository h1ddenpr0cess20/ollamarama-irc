'''
ollamarama-irc
    An ollama chatbot for irc with infinite personalities
    written by Dustin Whyte

'''

import irc.bot
import time
import textwrap
import json
import asyncio
import httpx
import logging

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
        self.loop = None
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.log = logging.getLogger(__name__).info

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
    
    async def thinking(self, lines):
        """
        Handles separation of thinking process from responses of reasoning models like DeepSeek-R1.

        Args:
        lines (list): A list of lines of an LLM response.

        """
        try:
            thinking = ' '.join(lines[lines.index('<think>'):lines.index('</think>')+1])
        except:
            thinking = None

        if thinking != None:
            self.log(f"Thinking: {thinking}")
            lines = lines[lines.index('</think>')+2:]

        joined_lines = ' '.join(lines)

        return lines, joined_lines
    
    async def reset(self, c, sender, stock=False):
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
            await self.set_prompt(c, sender, persona=self.default_personality, respond=False)
            c.privmsg(self.channel, f"{self.nickname} reset to default for {sender}")
            self.log(f"{self.nickname} reset to default for {sender}")
        else:
            c.privmsg(self.channel, f"Stock settings applied for {sender}")
            self.log(f"Stock settings applied for {sender}")

    async def set_prompt(self, c, sender, persona=None, custom=None, respond=True):
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
            self.log(f"System prompt for {sender} set to persona: '{persona}'")
        if custom != None  and custom != "":
            prompt = custom
            self.log(f"System prompt for {sender} set to custom: '{custom}'")
        self.add_history("system", sender, prompt)
        if respond:
            self.add_history("user", sender, "introduce yourself")
            await self.respond(c, sender, self.messages[sender])
            await asyncio.sleep(2)

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

    async def respond(self, c, sender, message, sender2=None):
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
            
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                response = await client.post(self.api_url, json=data)
                response.raise_for_status()
                data = response.json()
            
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            
            lines = self.chop(response_text.strip())
            lines, joined_lines = await self.thinking(lines)
            
            self.add_history("assistant", sender, joined_lines)

            if sender2:
                self.log(f"Sending response to {sender2} in {self.channel}: '{joined_lines}'")
                c.privmsg(self.channel, sender2 + ":")
            else:
                self.log(f"Sending response to {sender} in {self.channel}: '{joined_lines}'")
                c.privmsg(self.channel, sender + ":")
            await asyncio.sleep(1)

            for line in lines:
                c.privmsg(self.channel, line)
                await asyncio.sleep(2)
        except Exception as e:
            c.privmsg(self.channel, "Something went wrong, try again.")
            self.log(f"Error in respond: {e}")
            print(e)   

    def on_welcome(self, c, e):
        """
        Handle the welcome event and join the configured channel.

        Args:
            c: IRC connection object.
            e: Event object.
        """
        self.log(f"Connected to {self.server}")
        
        if self.password != None:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            self.log("Identifying to NickServ")
            time.sleep(5)
        
        self.log(f"Joining channel: {self.channel}")
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
            response = httpx.post(self.api_url, json=data, timeout=30.0)
            response.raise_for_status()
            data = response.json()

            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
                
            lines = self.chop(response_text + f"  Type .help to learn how to use me.")
            lines, joined_lines = asyncio.run_coroutine_threadsafe(self.thinking(lines), self.loop).result()
            
            self.log(f"Sending welcome response to {self.channel}: '{joined_lines}'")
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except Exception as e:
            self.log(f"Error sending welcome message: {e}")
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

    async def ai(self, c, e, sender, message, x=False):
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
                await self.respond(c, name, self.messages[name], sender2=sender)
            else:
                pass
        else:
            message = ' '.join(message[1:])
            self.add_history("user", sender, message)
            await self.respond(c, sender, self.messages[sender])
        await asyncio.sleep(2)       

    async def help_menu(self, c, sender):
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
            await asyncio.sleep(1)
    
    async def change_model(self, c, channel=False, model=False):
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
                    self.log(f"Model set to {self.model}")
                    c.privmsg(self.channel, f"Model set to {self.model}")
                else:
                    self.log(f"Model {model} not found in available models")
                    c.privmsg(self.channel, f"Model {model} not found in available models.")
            except Exception as e:
                self.log(f"Error changing model: {e}")
                pass
        else:
            if channel:
                current_model = [f"Current model: {self.model}", f"Available models: {', '.join(sorted(list(self.models)))}"]
                for line in current_model:
                    c.privmsg(self.channel, line)
    
    async def handle_message(self, c, e, sender, message):
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
            self.log(f"Received message from {sender} in {self.channel}: '{' '.join(message)}'")
            action = user_commands[command]
            await action()
        if sender in self.admins and command in admin_commands:
            self.log(f"Received admin message from {sender} in {self.channel}: '{' '.join(message)}'")
            action = admin_commands[command]
            await action()

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
            asyncio.run_coroutine_threadsafe(self.handle_message(c, e, sender, message), self.loop)
            
    async def main(self):
        """
        Initializes and runs the ollamarama bot.
        """
        self.loop = asyncio.get_running_loop()
        await asyncio.to_thread(self.start)

if __name__ == "__main__":
    bot = ollamarama()
    asyncio.run(bot.main())
