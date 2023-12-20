'''
ollamarama-irc
    An ollama chatbot for internet relay chat with infinite personalities
    written by Dustin Whyte
    December 2023

'''

import irc.bot
import time
import textwrap
import threading
from litellm import completion

class ollamarama(irc.bot.SingleServerIRCBot):
    def __init__(self, personality, channel, nickname, server, admins, password=None, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        
        self.personality = personality
        self.channel = channel
        self.server = server
        self.nickname = nickname
        self.password = password

        self.messages = {} #Holds chat history
        self.users = [] #List of users in the channel

        #prompt parts
        self.prompt = ("you are ", ". speak in the first person and never break character.")

        #put the models you want to use here
        self.models = {
            'zephyr': 'ollama/zephyr:7b-beta-q8_0',
            'solar': 'ollama/solar',
            'mistral': 'ollama/mistral',
            'llama2': 'ollama/llama2',
            'llama2-uncensored': 'ollama/llama2-uncensored',
            'openchat': 'ollama/openchat',
            'codellama': 'ollama/codellama:13b-instruct-q4_0',
            'dolphin-mistral': 'ollama/dolphin2.2-mistral:7b-q8_0',
            'deepseek-coder': 'ollama/deepseek-coder:6.7b',
            'orca2': 'ollama/orca2',
            'starling-lm': 'ollama/starling-lm',
            'vicuna': 'ollama/vicuna:13b-q4_0',
            'phi': 'ollama/phi',
            'orca-mini': 'ollama/orca-mini',
            'wizardcoder': 'ollama/wizardcoder:python',
            'stablelm-zephyr': 'ollama/stablelm-zephyr',
            'neural-chat': 'ollama/neural-chat',
        }
        #set model
        self.default_model = self.models['solar']
        self.model = self.default_model

        #authorized users for changing models
        self.admins = admins
        
    def chop(self, message):
        lines = message.splitlines()
        newlines = []  # Initialize an empty list to store wrapped lines

        for line in lines:
            if len(line) > 420:
                wrapped_lines = textwrap.wrap(line,
                                            width=420,
                                            drop_whitespace=False,
                                            replace_whitespace=False,
                                            fix_sentence_endings=True,
                                            break_long_words=False)
                newlines.extend(wrapped_lines)  # Extend the list with wrapped lines
            else:
                newlines.append(line)  # Add the original line to the list

        return newlines  # Return the list of wrapped lines
    
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

    #set a custom prompt (such as one from awesome-chatgpt-prompts)
    def custom(self, prompt, sender):
        #clear existing history
        if sender in self.messages:
            self.messages[sender].clear()
        self.add_history("system", sender, prompt)

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
            response = completion(
                        api_base="http://localhost:11434",
                        model=self.model,
                        temperature=.9,
                        top_p=.7,
                        repeat_penalty=1.5,
                        messages=message,
                        timeout=60)    
            response_text = response.choices[0].message.content
            
            # #removes any unwanted quotation marks from responses
            # if response_text.startswith('"') and response_text.endswith('"'):
            #     response_text = response_text.strip('"')

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

        except Exception as x: #improve this later with specific errors (token error, invalid request error etc)
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(x)

        #trim history for token size management
        if len(self.messages[sender]) > 30:
            del self.messages[sender][1:3]

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
        try:
            response = completion(
                            api_base="http://localhost:11434",
                            model=self.model,
                            temperature=.9,
                            top_p=.7,
                            repeat_penalty=1.5,
                            messages=
                            [
                                {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]},
                                {"role": "user", "content": greet}
                            ])
            response_text = response.choices[0].message.content
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
        # if user != self.nickname:
        #     try:
        #         response = completion(model=self.model, 
        #                 messages=[
        #                     {"role": "system", "content": self.prompt[0] + self.personality + self.prompt[1]}, 
        #                     {"role": "user", "content": greet}])
        #         response_text = response.choices[0].message.content
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
            if sender in self.admins:

                #model switching 
                if message.startswith(".model"):
                    if message == ".models":
                        c.privmsg(self.channel, f"Current model: {self.model.removeprefix('ollama/')}")
                        c.privmsg(self.channel, f"Available models: {', '.join(sorted(list(self.models)))}")
                    if message.startswith(".model "):
                        m = message.split(" ", 1)[1]
                        if m != None:
                            if m in self.models:
                                self.model = self.models[m]
                            elif m == 'reset':
                                self.model = self.default_model
                            c.privmsg(self.channel, f"Model set to {self.model.removeprefix('ollama/')}")
                
                #reset history for all users                
                if message == ".clear":
                    self.messages.clear()
                    self.model = self.default_model
                    c.privmsg(self.channel, "Bot has been reset for everyone")
                
                if sender == self.admins[0]:
                    #add admins
                    if message.startswith(".auth "):
                        nick = message.split(" ", 1)[1]
                        if nick != None:
                            self.admins.append(nick)
                            c.privmsg(self.channel, f"{nick} added to admins")
                    
                    #remove admins
                    if message.startswith(".deauth "):
                        nick = message.split(" ", 1)[1]
                        if nick != None:
                            self.admins.remove(nick)
                            c.privmsg(self.channel, f"{nick} removed from admins")                     

            #basic use
            if message.startswith(".ai") or message.startswith(self.nickname):
                m = message.split(" ", 1)
                m = m[1] + " [your response must be one paragraph or less]"

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
                            m = m[1] + " [your response must be one paragraph or less]"
                            
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
                m = m[1] + " [your response must be one paragraph or less]"
                
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
                help = [
                    "I am an AI chatbot.  I can have any personality you want me to have.  Each user has their own chat history and personality setting.",
                    f".ai <message> or {self.nickname}: <message> to talk to me.", ".x <user> <message> to talk to another user's history for collaboration.",
                    ".persona <personality> to change my personality. I can be any personality type, character, inanimate object, place, concept.", 
                    ".custom <prompt> to use a custom system prompt instead of a persona",
                    ".stock to set to stock settings.", f".reset to reset to my default personality, {self.personality}.",

                ]
                for line in help:
                    c.notice(sender, line)
                    time.sleep(1)
                
if __name__ == "__main__":
    # create the bot and connect to the server
    personality = "a helpful and thorough AI assistant who provides accurate and detailed answers without being too verbose"  #you can put anything here.  A character, person, personality type, object, concept, emoji, etc
    channel = "#CHANNEL"
    nickname = "NICKNAME"
    #password = "PASSWORD"
    server = "SERVER"
    
    #list of nicks allowed to change bot settings
    admins = ['admin_name1', 'admin_name2',]

    #checks if password variable exists (comment it out if unregistered)
    try:
      bot = ollamarama(personality, channel, nickname, server, admins, password)
    except:
      bot = ollamarama(personality, channel, nickname, server, admins)
      
    bot.start()

