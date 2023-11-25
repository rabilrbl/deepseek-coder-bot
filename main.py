import json
import os
import random
import time

# import uvloop
from pyrogram import Client, filters, errors
from pyrogram.types import Message

from pyrogram import enums

from deepseek_coder_api import login, register, newchat, chat


# uvloop.install()

app = Client(
    "Deepseek Coder Bot",
    bot_token=os.environ.get("BOT_TOKEN"),
    api_hash=os.environ.get("API_HASH"),
    api_id=os.environ.get("API_ID"),
)

user_credentials = {}

@app.on_message(filters.private & ~filters.me & ~filters.command("ping"))
async def set_typing_status(client, message: Message):
    """Set typing status while processing a message."""
    # Set typing status
    await client.send_chat_action(message.chat.id, enums.chat_action.ChatAction.TYPING)
    # Continue processing current message
    await message.continue_propagation()
    # Set typing status to False after processing current message
    await client.send_chat_action(message.chat.id, enums.chat_action.ChatAction.CANCEL)
    
    
@app.on_message(filters.command("start"))
async def start(_, message):
    welcome_text = "Welcome to TG-BOT"
    await message.reply_text(welcome_text)
    
@app.on_message(filters.command("help"))
async def help(_, message):
    help_text = """**Help**

**Available Commands:**
/start - Check if bot alive
/help - Show this help message
/ping - Check ping status

**Deepseek Coder**
/register - Register your account at Deepseek Coder
/login - Login to your account at Deepseek Coder
/newchat - Create a new chat conversation

Send any message to receive response from Deepseek Coder
"""
    await message.reply_text(help_text)


@app.on_message(filters.command("ping"))
async def ping(_, message):
    await message.reply_text("Pong")
    

@app.on_message(filters.command("info"))
async def info(_, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user
    text = f"""
**Your ID**: `{user.id}`
**Chat ID**: `{message.chat.id}`
"""
    await message.reply_text(text)
    
    
# Command to give details of replied message
@app.on_message(filters.command("msginfo"))
async def msginfo(_, message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to get details")
        return
    msg = message.reply_to_message
    text = f"""
**Message ID**: `{msg.id}`
**From**: `{msg.from_user.id}`
**Chat ID**: `{msg.chat.id}`
**Date**: `{msg.date}`
"""
    await message.reply_text(text)
    

# Command to login to Deepseek Coder
@app.on_message(filters.command("login"))
async def login_command(client: Client, message: Message):
    """Command to login to Deepseek Coder

    The function shall ask user for username and password
    and login to Deepseek Coder using the credentials.
    
    /login <email> <password>
    """
    # Check if user is already logged in
    if user_credentials.get(message.from_user.id):
        await message.reply_text("You are already logged in")
        return
    # Check if user has provided username and password
    if len(message.command) != 3:
        await message.reply_text("Please provide email and password. /login <email> <password>")
        return
    # Get email and password
    email = message.command[1]
    password = message.command[2]
    # Login to Deepseek Coder
    try:
        response_json = login.do_login(email, password)
        if response_json["code"] != 0:
            raise Exception(response_json["msg"])
        user_credentials[message.from_user.id] = response_json["data"]
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return
    # Send success message
    await message.reply_text("Successfully logged in")
    

# Command to register to Deepseek Coder
@app.on_message(filters.command("register"))
async def register_command(client: Client, message: Message):
    """Command to register to Deepseek Coder

    The function shall ask user for username and password
    and register to Deepseek Coder using the credentials.
    
    /register <email> <password>
    """
    # Check if user is already logged in
    if user_credentials.get(message.from_user.id):
        await message.reply_text("You are already logged in")
        return
    # Check if user has provided username and password
    if len(message.command) < 3:
        await message.reply_text("Please provide email and password. /register email password")
        return
    
    email_verification_code = None
    if len(message.command) == 4:
        email_verification_code = message.command[3]
        
    # Get email and password
    email = message.command[1]
    password = message.command[2]
    
    # Check if email verification code is provided
    if not email_verification_code:
        register.create_email_verification_code(email=message.command[1])
        await message.reply_text("Email verification code sent to your email. Please check your email and run /register email password verification_code")
        return
    
    # Register to Deepseek Coder
    try:
        # Register
        register.register(email=email, email_verification_code=email_verification_code, password=password)
    except Exception as e:
        await message.reply_text(f"Error: {e}. Please manually signup at https://coder.deepseek.com")
        return
    # Send success message
    await message.reply_text("Successfully registered. Now login using /login <email> <password>")
    

# Command to logout from Deepseek Coder
@app.on_message(filters.command("logout"))
async def logout_command(client: Client, message: Message):
    """Command to logout from Deepseek Coder

    The function shall logout from Deepseek Coder
    and remove the user credentials.
    
    /logout
    """
    # Check if user is logged in
    if not user_credentials.get(message.from_user.id):
        await message.reply_text("You are not logged in")
        return
    # Logout from Deepseek Coder
    try:
        # Logout
        user_credentials.pop(message.from_user.id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return
    # Send success message
    await message.reply_text("Successfully logged out")
    
    
# Command to create a new chat conversation
@app.on_message(filters.command("newchat"))
async def newchat_command(client: Client, message: Message):
    """Command to create a new chat conversation

    The function shall create a new chat conversation
    and return the chat id.
    
    /newchat
    """
    # Check if user is logged in
    if not user_credentials.get(message.from_user.id):
        await message.reply_text("You are not logged in. Please login using /login <email> <password>")
        return
    # Create a new chat conversation
    try:
        # Create a new chat conversation
        response = newchat.new_chat(user_credentials[message.from_user.id]["user"]["token"])
        if response["code"] != 0:
            raise Exception(response["msg"])
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return
    # Send success message
    await message.reply_text(f"Successfully created a new chat conversation.")


@app.on_message(filters.create(lambda _, __, m: m.text and m.text.startswith("/")))
async def unknown(_, message):
    # Generate random funny response
    random_responses = [
        "I don't know that command",
        "What?",
        "Excuse me?",
        "I don't understand",
        "What are you talking about?",
        "I don't know what you mean",
        "I don't know what to say",
        "Go away",
        "Fall in a hole",
        "I don't care",
        "I'm not listening",
        "Are you talking to me?",
    ]
    await message.reply_text(random.choice(random_responses))


# Send all other messages to Deepseek Coder
@app.on_message()
async def send_message(client: Client, message: Message):
    """Send all other messages to Deepseek Coder"""
    # Check if user is logged in
    if not user_credentials.get(message.from_user.id):
        await message.reply_text("You are not logged in. Please login using /login <email> <password>")
        return
    # Send message to Deepseek Coder
    try:
        # Send initial message and store the chat id
        chat_info = await message.reply_text("Sending message to Deepseek Coder...")
        # edit message timer to send message every 500ms
        timer = time.time()
        # stream messages by iterating over the chunks and editing the message
        for chunk in chat.chat(message.text, user_credentials[message.from_user.id]["user"]["token"]):
            chunk = chunk.strip().decode("utf-8").replace("data: ", "")
            json_chunk = json.loads(chunk)
            try:
                # keep printing in one line
                chat_info = await chat_info.edit(chat_info.text + json_chunk["choices"][0]["delta"]["content"], disable_web_page_preview=True)
            except KeyError:
                pass
            except errors.MessageNotModified:
                pass
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return
    # Send success message
    await message.reply_text(f"Successfully sent message to Deepseek Coder")

app.run()