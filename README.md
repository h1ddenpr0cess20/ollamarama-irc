# ollamarama-irc
Ollamarama is an AI chatbot for IRC which uses local LLMs with Ollama.  It can roleplay as almost anything you can think of.  You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.

Also available for the Matrix chat protocol at [ollamarama-matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix/).  Terminal-based version at [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)


## Setup
Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run local LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the config.json file.  If you want to use the ones I've included, just run ollama pull _modelname_ for each.


You also need to install the irc module

```
pip3 install irc
```

Fill in the values for channel, nickname, password and server in config.json 
Password is optional, but registration is required for some channels.

## Use

```
python3 ollamarama.py
```

**.ai _message_ or botname: _message_**  
Basic usage.  

**.x _user message_**  
This allows you to talk to another user's chat history.  
_user_ is the display name of the user whose history you want to use
     
**.persona _personality_**  
Changes the personality.  It can be a character, personality type, object, idea.  Don't use a custom system prompt here.

**.custom _prompt_**  
    Set a custom system prompt istead of the roleplay prompt
        
**.reset**  
    Reset to preset personality
    
**.stock**  
    Remove personality and set to standard model settings

**.help**  
    Display the help menu

**.model**  
    Show current model and available models (admin only)

**.model _name_**  
    Set a model (admin only)
