from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# Simulated in-memory database (replace with a persistent database like MongoDB)
database = {}

# Telegram API base URL
TELEGRAM_API_URL = "https://api.telegram.org/bot{}/{}"

# Function to set webhook
def set_webhook(bot_token, webhook_url):
    url = TELEGRAM_API_URL.format(bot_token, "setWebhook")
    response = requests.post(url, data={"url": webhook_url})
    return response.json()

# Function to remove webhook
def remove_webhook(bot_token):
    url = TELEGRAM_API_URL.format(bot_token, "deleteWebhook")
    response = requests.post(url)
    return response.json()

# API endpoint to retrieve the entire user database
@app.route('/getusers/<bot_token>', methods=['GET'])
def get_users(bot_token):
    if bot_token not in database:
        return jsonify({"error": "Invalid bot token"}), 403
    return jsonify(database[bot_token])

# Endpoint to set webhook and remove it after setting
@app.route('/setwebhook/<bot_token>', methods=['POST'])
def set_webhook_route(bot_token):
    # Construct the webhook URL (adjust to your Vercel deployment URL)
    base_url = request.host_url.rstrip('/')
    webhook_url = f"{base_url}/webhook/{bot_token}"
    
    # Set the webhook
    set_result = set_webhook(bot_token, webhook_url)
    if set_result.get("ok"):
        # Immediately remove the webhook after setting (as per your requirement)
        remove_result = remove_webhook(bot_token)
        return jsonify({
            "set_result": set_result,
            "remove_result": remove_result
        })
    return jsonify({"error": "Failed to set webhook"}), 500

# Endpoint to manually remove webhook (optional)
@app.route('/removewebhook/<bot_token>', methods=['POST'])
def remove_webhook_route(bot_token):
    result = remove_webhook(bot_token)
    return jsonify(result)

# Webhook handler to process incoming Telegram updates
@app.route('/webhook/<bot_token>', methods=['POST'])
def webhook(bot_token):
    update = request.json
    if 'message' in update:
        chat = update['message']['chat']
        chat_id = chat['id']
        chat_type = chat['type']
        
        # Initialize database entry for this bot token if not exists
        if bot_token not in database:
            database[bot_token] = []

        # Store user or chat data based on chat type
        if chat_type == 'private':
            user_data = {
                'user_id': chat_id,
                'username': chat.get('username', ''),
                'name': (chat.get('first_name', '') + ' ' + chat.get('last_name', '')).strip()
            }
            if user_data not in database[bot_token]:
                database[bot_token].append(user_data)
        else:
            chat_data = {
                'chat_id': chat_id,
                'username': chat.get('username', ''),
                'name': chat.get('title', '')
            }
            if chat_data not in database[bot_token]:
                database[bot_token].append(chat_data)
    return 'OK', 200

if __name__ == '__main__':
    app.run()