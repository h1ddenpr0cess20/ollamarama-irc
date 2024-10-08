'''
ollamarama-irc
    An ollama chatbot for irc with infinite personalities
    written by Dustin Whyte
    December 2023

'''

import irc.bot
import time
import textwrap
import threading
import json
import requests

class ollamarama(irc.bot.SingleServerIRCBot):
    def __init__(self, port=6667):
        #load config
        self.config_file = "config.json"
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            f.close()
        
        self.channel, self.nickname, self.password, self.server, self.admins = config["irc"].values()
        irc.bot.SingleServerIRCBot.__init__(self, [(self.server, port)], self.nickname, self.nickname)

        #load models, set default model
        self.models = config["ollama"]["models"]
        self.default_model = self.models[config["ollama"]["default_model"]]
        self.model = self.default_model
        #set personality and system prompt
        self.default_personality = config["ollama"]["personality"]
        self.personality = self.default_personality
        self.prompt = config["ollama"]["prompt"]

        self.temperature, self.top_p, self.repeat_penalty = config["ollama"]["options"].values()
        self.defaults = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repeat_penalty": self.repeat_penalty
        }
        self.api_url = config["ollama"]["api_base"] + "/api/chat"

        #chat history
        self.messages = {}

        #user list
        self.users = []

        #load help menu text
        with open("help.txt", "r") as f:
            self.help, self.admin_help = f.read().split("~~~")
            f.close()
    
    #chops up message for irc line length limit    
    def chop(self, message):
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
    
    #resets bot to preset personality per user    
    def reset(self, sender):
        if sender in self.messages:
            self.messages[sender].clear()
            self.persona(self.personality, sender)

    #sets the bot personality 
    def persona(self, persona, sender):
        #clear existing history
        if sender in self.messages:
            self.messages[sender].clear()
        personality = self.prompt[0] + persona + self.prompt[1]
        self.add_history("system", sender, personality)
        self.add_history("user", sender, "introduce yourself")
        

    #set a custom system prompt
    def custom(self, prompt, sender):
        #clear existing history
        if sender in self.messages:
            self.messages[sender].clear()
        self.add_history("system", sender, prompt)
        self.add_history("user", sender, "introduce yourself")

    #adds messages to self.messages    
    def add_history(self, role, sender, message):
        if sender in self.messages:
            self.messages[sender].append({"role": role, "content": message})
        else:
            if role == "system":
                self.messages[sender] = [{"role": role, "content": message}]
            else:
                self.messages[sender] = [
                    {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                    {"role": role, "content": message}]

    #respond with ai model           
    def respond(self, c, sender, message, sender2=None):
        try:
            data = {
                "model": self.model, 
                "messages": message, 
                "stream": False,
                "options": {
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "repeat_penalty": self.repeat_penalty
                    }
                }
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            data = response.json()
            
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            #add the response text to the history before breaking it up
            self.add_history("assistant", sender, response_text)

            #add username before response
            #if .x function used
            if sender2:
                c.privmsg(self.channel, sender2 + ":")
            #normal .ai usage
            else:
                c.privmsg(self.channel, sender + ":")
            time.sleep(1)

            #split up the response to fit irc length limit
            lines = self.chop(response_text.strip())
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except Exception as x:
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(x)   
        
        #trim history for token size management
        if len(self.messages[sender]) > 24:
            if self.messages[sender][0]['role'] == "system":
                del self.messages[sender][1:3]
            else:
                del self.messages[sender][0:2]

    #when bot joins network, identify and wait, then join channel   
    def on_welcome(self, c, e):
        #if nick has a password
        if self.password != None:
            c.privmsg("NickServ", f"IDENTIFY {self.password}")
            #wait for identify to finish
            time.sleep(5)
        
        #join channel
        c.join(self.channel)

        # get users in channel
        c.send_raw("NAMES " + self.channel)

        #optional join message
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
                "options": {
                    "top_p": self.top_p,
                    "temperature": self.temperature,
                    "repeat_penalty": self.repeat_penalty
                    }
                }
            response = requests.post(self.api_url, json=data)
            response.raise_for_status()
            data = response.json()
            response_text = data["message"]["content"]
            if response_text.startswith('"') and response_text.endswith('"') and response_text.count('"') == 2:
                response_text = response_text.strip('"')
            lines = self.chop(response_text + f"  Type .help {self.nickname} to learn how to use me.")
            for line in lines:
                c.privmsg(self.channel, line)
                time.sleep(2)
        except:
            pass
            
    def on_nicknameinuse(self, c, e):
        #add an underscore if nickname is in use
        c.nick(c.get_nickname() + "_")

    # actions to take when a user joins 
    def on_join(self, c, e):
        user = e.source
        user = user.split("!")
        user = user[0]
        if user not in self.users:
            self.users.append(user)

        # Optional greeting for when a user joins        
        # greet = f"come up with a unique greeting for the user {user}"
        # system = self.prompt[0] + self.personality + self.prompt[1]
        # if user != self.nickname:
        #     try:
        #         data = {
        #             "model": self.model, 
        #             "messages":[
        #                         {"role": "system", "content": system}, 
        #                         {"role": "user", "content": greet}], 
        #             "stream": False,
        #             "options": {
        #                 "top_p": self.top_p,
        #                 "temperature": self.temperature,
        #                 "repeat_penalty": self.repeat_penalty
        #                 }
        #             }
        #         response = requests.post(self.api_url, json=data)
        #         response.raise_for_status()
        #         data = response.json()
        #         response_text = data["message"]["content"].strip('"')
                
        #         time.sleep(5)
        #         lines = self.chop(response_text)
        #         for line in lines:
        #             c.privmsg(self.channel, line)
        #             time.sleep(2)
        #     except:
        #         pass
            
    # Get the users in the channel
    def on_namreply(self, c, e):
        symbols = {"@", "+", "%", "&", "~"} #symbols for ops and voiced
        userlist = e.arguments[2].split()
        for name in userlist:
            for symbol in symbols:
                if name.startswith(symbol):
                    name = name.lstrip(symbol)
            if name not in self.users:
                self.users.append(name)       

    #process chat messages
    def on_pubmsg(self, c, e):
        #message parts
        message = e.arguments[0]
        sender = e.source
        sender = sender.split("!")
        sender = sender[0]

        #if the bot didn't send the message
        if sender != self.nickname:
            #admin commands
            if message == ".admins":
                c.privmsg(self.channel, f"Bot admins: {', '.join(self.admins)}")
            if sender in self.admins:
                #model switching 
                if message.startswith(".model"):
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                        f.close()
                    self.models = config["ollama"]["models"]
                    if message == ".models":
                        c.privmsg(self.channel, f"Current model: {self.model}")
                        c.privmsg(self.channel, f"Available models: {', '.join(sorted(list(self.models)))}")
                    if message.startswith(".model "):
                        m = message.split(" ", 1)[1]
                        if m != None:
                            if m in self.models:
                                self.model = self.models[m]
                            elif m == 'reset':
                                self.model = self.default_model
                            c.privmsg(self.channel, f"Model set to {self.model}")
                
                #bot owner commands
                if sender == self.admins[0]:
                    #reset history for all users                
                    if message == ".clear":
                        self.messages.clear()
                        self.model = self.default_model
                        self.temperature, self.top_p, self.repeat_penalty = self.defaults
                        c.privmsg(self.channel, "Bot has been reset for everyone")
                        
                    #add admins
                    if message.startswith(".auth "):
                        nick = message.split(" ", 1)[1].strip()
                        if nick != None:
                            self.admins.append(nick)
                            c.privmsg(self.channel, f"{nick} added to admins")
                    
                    #remove admins
                    if message.startswith(".deauth "):
                        nick = message.split(" ", 1)[1].strip()
                        if nick != None:
                            self.admins.remove(nick)
                            c.privmsg(self.channel, f"{nick} removed from admins")

                    #set new global personality
                    if message.startswith(".gpersona "):
                        m = message.split(" ", 1)[1].strip()
                        if m != None:
                            if m == 'reset':
                                self.personality = self.default_personality
                            else:
                                self.personality = m
                            c.privmsg(self.channel, f"Global personality set to {self.personality}")

                    if message.startswith((".temperature ", ".top_p ", ".repeat_penalty ")):
                        attr_name = message.split()[0][1:]
                        min_val, max_val, default_val = {
                            "temperature": (0, 1, self.defaults["temperature"]),
                            "top_p": (0, 1, self.defaults["top_p"]),
                            "repeat_penalty": (0, 2, self.defaults["repeat_penalty"])
                        }[attr_name]

                        if message.endswith(" reset"):
                            setattr(self, attr_name, default_val)
                            c.privmsg(self.channel, f"{attr_name.capitalize()} set to {default_val}")
                        else:
                            try:
                                value = float(message.split(" ", 1)[1])
                                if min_val <= value <= max_val:
                                    setattr(self, attr_name, value)
                                    c.privmsg(self.channel, f"{attr_name.capitalize()} set to {value}")
                                else:
                                    c.privmsg(self.channel, f"Invalid input, {attr_name} is still {getattr(self, attr_name)}")
                            except:
                                c.privmsg(self.channel, f"Invalid input, {attr_name} is still {getattr(self, attr_name)}")
            
            #basic use
            if message.startswith(".ai") or message.startswith(self.nickname):
                m = message.split(" ", 1)
                m = m[1]

                #add to history and start respond thread
                self.add_history("user", sender, m)
                thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                thread.start()
                thread.join(timeout=30)
                time.sleep(2) #help prevent mixing user output (does not seem to be working very well for long responses, may need to adjust)

            #collborative use
            if message.startswith(".x "):
                m = message.split(" ", 2)
                m.pop(0)
                if len(m) > 1:
                    #get users in channel
                    c.send_raw("NAMES " + self.channel)

                    #check if the message starts with a name in the history
                    for name in self.users:
                        if type(name) == str and m[0] == name:
                            user = m[0]
                            m = m[1]
                            
                            #if so, respond, otherwise ignore
                            if user in self.messages:
                                self.add_history("user", user, m)
                                thread = threading.Thread(target=self.respond, args=(c, user, self.messages[user],), kwargs={'sender2': sender})
                                thread.start()
                                thread.join(timeout=30)
                                time.sleep(2)
                            
            #change personality    
            if message.startswith(".persona "):
                m = message.split(" ", 1)
                m = m[1]
                
                self.persona(m, sender)
                thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                thread.start()
                thread.join(timeout=30)
                time.sleep(2)

            #use custom system prompts 
            if message.startswith(".custom "):
                m = message.split(" ", 1)
                m = m[1]
                
                self.custom(m, sender)
                thread = threading.Thread(target=self.respond, args=(c, sender, self.messages[sender]))
                thread.start()
                thread.join(timeout=30)
                time.sleep(2)
                    
            #reset to default personality    
            if message.startswith(".reset"):
                self.reset(sender)
                c.privmsg(self.channel, f"{self.nickname} reset to default for {sender}.")

            #stock GPT settings    
            if message.startswith(".stock"):
                if sender in self.messages:
                    self.messages[sender].clear()
                else:
                    self.messages[sender] = []                    
                c.privmsg(self.channel, f"Stock settings applied for {sender}")

            #help menu    
            if message.startswith(f".help {self.nickname}"):
                for line in self.help.splitlines():
                    c.notice(sender, line)
                    time.sleep(1)
                if sender in self.admins:
                    for line in self.admin_help.splitlines():
                        c.notice(sender, line)
                        time.sleep(1)
                
if __name__ == "__main__":
    bot = ollamarama()

    bot.start()
