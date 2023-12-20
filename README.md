# ollamarama-irc
Ollamarama is an AI chatbot for IRC which uses offline LLMs with LiteLLM and Ollama.  It can roleplay as almost anything you can think of.  You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.

Also available for the Matrix chat protocol at [ollamarama-matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix/)

Based on my earlier project, InfiniGPT, which uses OpenAI, available at [infinigpt-irc](https://github.com/h1ddenpr0cess20/infinigpt-irc)

## Setup
Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the self.models dictionary.


You also need to install the irc and litellm modules

```
pip3 install litellm irc
```
Get an [OpenAI API](https://platform.openai.com/signup) key 

Fill in the variables for channel, nickname, password and server in launcher.py.  
Password is optional, but registration is required for some channels.

## Use

```
python3 launcher.py
```

**.ai _message_ or botname: _message_**
    Basic usage.
    Personality is preset by bot operator.
    
**.x _user message_**
    This allows you to talk to another user's chat history.
    _user_ is the display name of the user whose history you want to use
     
**.persona _personality_**
    Changes the personality.  It can be a character, personality type, object, idea.
    Don't use a custom system prompt here.

**.custom _prompt_**
    Set a custom system prompt istead of the roleplay prompt
        
**.reset**
    Reset to preset personality
    
**.stock**
    Remove personality and set to standard model settings

**.help _botname_**
    Display the help menu

**.models**
    Show current model and available models

**.model _name_**
    Set a model

**.model _reset_**
    Reset to default model