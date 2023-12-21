from ollamarama import ollamarama

# create the bot and connect to the server
personality = "a helpful and thorough AI assistant who provides accurate and detailed answers without being too verbose"  #you can put anything here.  A character, person, personality type, object, concept, emoji, etc
channel = "#channel"
nickname = "nickname"
#password = "PASSWORD"
server = "irc.server.net"

#list of nicks allowed to change bot settings
admins =['USERNAME',]

#checks if password variable exists (comment it out if unregistered)
try:
    bot = ollamarama(personality, channel, nickname, server, admins, password)
except:
    bot = ollamarama(personality, channel, nickname, server, admins)
    
bot.start()
