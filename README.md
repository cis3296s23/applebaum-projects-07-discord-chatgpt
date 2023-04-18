# ChatD&D

## Features

* `/chat [message]` Send a message to ChatGPT! This is the main DnD entrypoint.
* `/private` ChatGPT switch to private mode
* `/public`  ChatGPT switch to public  mode
* `/replyall`  ChatGPT switch between replyall mode and default mode
* `/reset` Clear ChatGPT conversation history
* `/help`  Show basic info on commands

### Chat

![image](https://user-images.githubusercontent.com/89479282/206497774-47d960cd-1aeb-4fba-9af5-1f9d6ff41f00.gif)

### Mode

* `public mode (default)`  the bot directly reply on the channel

  ![image](https://user-images.githubusercontent.com/89479282/206565977-d7c5d405-fdb4-4202-bbdd-715b7c8e8415.gif)

* `private mode` the bot's reply can only be seen by the person who used the command

  ![image](https://user-images.githubusercontent.com/89479282/206565873-b181e600-e793-4a94-a978-47f806b986da.gif)

* `replyall mode` the bot will reply to all messages in the server without using slash commands

   > **Warning**
   > The bot will easily be triggered in `replyall` mode, which could cause program failures

# Setup

## Install

1. **Paste the invite link into a browser `https://discord.com/api/oauth2/authorize?client_id=1075678176883249242&permissions=277025589248&scope=bot`**
2. **Choose a server you are an admin of to add it to with the correct permissions**
3. **Use `/initialize` to set up some basic info with the bot `WIP - NOT IMPLEMENTED`**

### Have a good chat!

## Optional: Setup starting prompt

* A starting prompt would be invoked when the bot is first started or reset
* You can set it up using the `/initialize` command
* All the text in the file will be fired as a prompt to the bot

   1. Right-click the channel you want to recieve the message, `Copy  ID`
   
        ![channel-id](https://user-images.githubusercontent.com/89479282/207697217-e03357b3-3b3d-44d0-b880-163217ed4a49.PNG)
    
   2. Pase it into `\intialize` under `channel_id`
