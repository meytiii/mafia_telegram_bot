import random
import string
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

TOKEN = 'YOUR_TOKEN'

active_games = {}

user_games = {}

def generate_game_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def start(update: Update, context) -> None:
    welcome_message = "Welcome to the Mafia game bot! Please choose an option from the menu."
    keyboard = [
        [
            InlineKeyboardButton("Create a Mafia game", callback_data='create_game'),
            InlineKeyboardButton("Join a game", callback_data='join_game')
        ],
        [InlineKeyboardButton("View rules", callback_data='view_rules')],
        [InlineKeyboardButton("Leave game", callback_data='leave_game')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = update.callback_query.message if update.callback_query else update.message
    await message.reply_text(welcome_message, reply_markup=reply_markup)

async def rules(update: Update, context) -> None:
    rules_text = (
        "Mafia Game Rules:\n"
        "1. There are two main teams: Mafia and Citizens.\n"
        "2. The game consists of two phases: Day and Night.\n"
        "3. During the Night, the Mafia secretly choose a Citizen to eliminate.\n"
        "4. During the Day, all players discuss and vote to eliminate a suspect.\n"
        "5. The game continues until either the Mafia is eliminated or the Mafia outnumber the Citizens.\n"
        "6. Additional roles and rules can be added to increase game complexity and enjoyment."
    )
    keyboard = [
        [InlineKeyboardButton("Back to main menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(rules_text, reply_markup=reply_markup)

async def create_game(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id in user_games.values():
        await query.answer("You are already in a game. Please leave the current game before creating a new one.", show_alert=True)
        return

    game_code = generate_game_code()
    active_games[game_code] = {'god_id': user_id, 'players': []}
    keyboard = [
        [InlineKeyboardButton("Back to main menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(f"The game with code `{game_code}` has been created. You can now invite others to join.", reply_markup=reply_markup)

async def join_game(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id in user_games.values():
        await query.answer("You are already in a game. Please leave the current game before joining a new one.", show_alert=True)
        return

    game_code = context.args[0] if context.args else None
    if not game_code:
        await query.answer("Please enter the game code.")
        return

    if game_code not in active_games:
        await query.answer("Invalid game code.")
        return

    active_game = active_games[game_code]
    if user_id == active_game['god_id']:
        await query.answer("You are the game creator. Please close the current game before joining a new one.", show_alert=True)
        return

    active_game['players'].append(user_id)
    user_games[user_id] = game_code

    god_id = active_game['god_id']
    await context.bot.send_message(god_id, f"User with ID {user_id} has joined your game.")

    keyboard = [
        [InlineKeyboardButton("Back to main menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text("You have joined the game.", reply_markup=reply_markup)

async def leave_game(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in user_games:
        await query.answer("You are not currently in any game.", show_alert=True)
        return

    game_code = user_games.pop(user_id)
    active_game = active_games[game_code]

    if user_id == active_game['god_id']:
        for player_id in active_game['players']:
            await context.bot.send_message(player_id, "The game creator has closed the game. All players have been removed.")
            user_games.pop(player_id)
        active_games.pop(game_code)
    else:
        active_game['players'].remove(user_id)
        await context.bot.send_message(active_game['god_id'], f"User with ID {user_id} has left the game.")

    keyboard = [
        [InlineKeyboardButton("Back to main menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text("You have successfully left the game.", reply_markup=reply_markup)

async def button(update: Update, context) -> None:
    query = update.callback_query
    data = query.data
    
    if data == 'create_game':
        await create_game(update, context)
    elif data == 'join_game':
        await query.answer()
        await query.message.reply_text("Please enter the game code.")
    elif data == 'view_rules':
        await rules(update, context)
    elif data == 'leave_game':
        await leave_game(update, context)
    elif data == 'main_menu':
        await start(update, context)
    else:
        await query.answer("Invalid command!")

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()