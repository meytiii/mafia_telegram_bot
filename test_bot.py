import requests
import time

TOKEN = 'YOUR_TOKEN'
BASE_URL = f'https://api.telegram.org/bot{TOKEN}'

def send_message(chat_id, text):
    url = f'{BASE_URL}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    response = requests.post(url, json=payload)
    return response.json()

def send_start_command(chat_id):
    return send_message(chat_id, '/start')

def get_updates(offset=None):
    url = f'{BASE_URL}/getUpdates'
    params = {'offset': offset} if offset else {}
    response = requests.get(url, params=params)
    return response.json()

def simulate_button_press(chat_id, message_id, callback_data):
    url = f'{BASE_URL}/answerCallbackQuery'
    payload = {
        'callback_query_id': callback_data,
        'text': "Button pressed",
    }
    response = requests.post(url, json=payload)
    return response.json()

def main():
    chat_id = 'YOUR_CHAT_ID'  # Replace with your chat ID
    print("Sending /start command...")
    start_response = send_start_command(chat_id)
    print(start_response)

    time.sleep(2)

    print("Getting updates...")
    updates = get_updates()
    print(updates)

    for update in updates.get('result', []):
        message = update.get('message')
        if message and 'reply_markup' in message:
            chat_id = message['chat']['id']
            message_id = message['message_id']
            inline_keyboard = message['reply_markup']['inline_keyboard']
            callback_data = inline_keyboard[0][0]['callback_data']

            print(f"Simulating button press with callback_data: {callback_data}")
            button_response = simulate_button_press(chat_id, message_id, callback_data)
            print(button_response)

            break

if __name__ == '__main__':
    main()
