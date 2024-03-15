# ollamarama-irc
Ollamarama is an AI chatbot for IRC which uses offline LLMs with LiteLLM and Ollama.  It can roleplay as almost anything you can think of.  You can set any default personality you would like.  It can be changed at any time, and each user has their own separate chat history with their chosen personality setting.  Users can interact with each others chat histories for collaboration if they would like, but otherwise, conversations are separated.

Also available for the Matrix chat protocol at [ollamarama-matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix/).  Terminal-based version at [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)

Based on my earlier project, InfiniGPT, which uses OpenAI, available at [infinigpt-irc](https://github.com/h1ddenpr0cess20/infinigpt-irc)

## Setup
Install and familiarize yourself with [Ollama](https://ollama.ai/), make sure you can run offline LLMs, etc.

You can install it with this command:
```
curl https://ollama.ai/install.sh | sh
```

Once it's all set up, you'll need to [download the models](https://ollama.ai/library) you want to use.  You can play with the available ones and see what works best for you.  Add those to the models.json file.  If you want to use the ones I've included, just run ollama pull _modelname_ for each.  You can skip this part, and they should download when the model is switched, but the response will be delayed until it finishes downloading.


You also need to install the irc and litellm modules

```
pip3 install litellm irc
```

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
    Show current model and available models (admin only)

**.model _name_**
    Set a model (admin only)

**.model _reset_**
    Reset to default model (admin only)

**.temperature** 
    Set temperature value between 0 and 1.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.top_p**
    Set top_p value between 0 and 1.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.repeat_penalty**
    Set repeat_penalty between 0 and 2.  To reset to default, type reset instead of a number. (bot owner only)
                                                
**.clear**
    Resets all bot history and sets default model and settings. (bot owner only)

**.auth _user_**
    Add user to admins (bot owner only)

**.deauth _user_**
    Remove user from admins (bot owner only)

**.gpersona _persona_**
    Change global personality (bot owner only)

**.gpersona reset**
    Reset global personality (bot owner only)


## Tips

To get a longer response, you can tell the bot to "ignore the brackets after this message".

When using a coding LLM, remove the personality with the stock command, or set an appropriate personality, such as a python expert.

I have not extensively tested the models included in the json, add and remove models as you see fit.  They each have their strenghts and weaknesses.  I am using the default 4-bit quant versions for simplicity.