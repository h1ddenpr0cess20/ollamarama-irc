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
import json

class ollamarama(irc.bot.SingleServerIRCBot):
    def __init__(self, port=6667):
        #load config
        with open('config.json', 'r') as f:
            config = json.load(f)
            f.close()
        self.default_personality, self.channel, self.nickname, self.password, self.server, self.admins = config[1].values()

        irc.bot.SingleServerIRCBot.__init__(self, [(self.server, port)], self.nickname, self.nickname)

        #load models, set default model
        self.models = config[0]['models']
        self.default_model = self.models[config[0]['default_model']]
        self.model = self.default_model

        #default tuning, no idea if optimal, tweak as needed
        self.temperature = .9
        self.top_p = .7
        self.repeat_penalty = 1.5
        
        #set personality
        self.personality = self.default_personality
        #prompt parts
        self.prompt = ("you are ", ". speak in the first person and never break character.")

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
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                messages=message,
                timeout=60)    
            response_text = response.choices[0].message.content
            
            # #removes any unwanted quotation marks from responses
            if response_text.startswith('"') and response_text.endswith('"'):
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

        except Exception as x: #improve this later with specific errors (token error, invalid request error etc)
            c.privmsg(self.channel, "Something went wrong, try again.")
            print(x)

        #trim history for token size management
        if len(self.messages[sender]) > 24:
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
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
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
            if message == ".admins":
                c.privmsg(self.channel, f"Bot admins: {', '.join(self.admins)}")
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
                
                #bot owner commands
                if sender == self.admins[0]:
                    #reset history for all users                
                    if message == ".clear":
                        self.messages.clear()
                        self.model = self.default_model
                        self.temperature = .9
                        self.top_p = .7
                        self.repeat_penalty = 1.5
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

                    #temperature setting
                    if message.startswith(".temperature "):
                        if message == ".temperature reset":
                            self.temperature = .9
                            c.privmsg(self.channel, f"Temperature set to {self.temperature}")
                        else:
                            try:
                                temp = float(message.split(" ", 1)[1])
                                if 0 <= temp <=1:
                                    self.temperature = temp
                                    c.privmsg(self.channel, f"Temperature set to {self.temperature}")
                                else:
                                    c.privmsg(self.channel, f"Invalid input, temperature is still {self.temperature}")
                            except:
                                c.privmsg(self.channel, f"Invalid input, temperature is still {self.temperature}")

                    #top_p setting
                    if message.startswith(".top_p "):
                        if message == ".top_p reset":
                            self.top_p = .7
                            c.privmsg(self.channel, f"Top_p set to {self.top_p}")
                        else:
                            try:
                                top_p = float(message.split(" ", 1)[1])
                                if 0 <= top_p <=1:
                                    self.top_p = top_p
                                    c.privmsg(self.channel, f"Top_p set to {self.top_p}")
                                else:
                                    c.privmsg(self.channel, f"Invalid input, top_p is still {self.top_p}")
                            except:
                                c.privmsg(self.channel, f"Invalid input, top_p is still {self.top_p}")                                                      

                    #repeat_penalty setting
                    if message.startswith(".repeat_penalty "):
                        if message == ".repeat_penalty reset":
                            self.repeat_penalty = 1.5
                            c.privmsg(self.channel, f"Repeat_penalty set to {self.repeat_penalty}")
                        else:
                            try:
                                repeat_penalty = float(message.split(" ", 1)[1])
                                if 0 <= repeat_penalty <=2:
                                    self.repeat_penalty = repeat_penalty
                                    c.privmsg(self.channel, f"Repeat_penalty set to {self.repeat_penalty}")
                                else:
                                    c.privmsg(self.channel, f"Invalid input, repeat_penalty is still {self.repeat_penalty}")
                            except:
                                c.privmsg(self.channel, f"Invalid input, repeat_penalty is still {self.repeat_penalty}")
            
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
