import random
import string
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TOKEN = '7012299918:AAFh8L7YN-2jTmCL23Ublj4nBHkGRMrsoOQ'

active_games = {}
user_games = {}
join_requests = {}


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

    if user_id in user_games:
        await query.answer("You already have an active game. Please close it before creating a new one.",
                           show_alert=True)
        return

    game_code = generate_game_code()
    active_games[game_code] = {'god_id': user_id, 'players': [user_id], 'pending_requests': []}
    user_games[user_id] = game_code

    await query.answer()
    await query.edit_message_text(
        f"The game with code `{game_code}` has been created. You are the game creator and the game is now in progress.")


async def join_game_prompt(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if user_id in user_games:
        await query.answer("You are already in a game. Please leave the current game before joining a new one.",
                           show_alert=True)
        return

    await query.answer()
    await query.message.reply_text("Please enter the game code to join:")


async def join_game(update: Update, context) -> None:
    user_id = update.message.from_user.id
    game_code = update.message.text.strip().upper()

    if user_id in user_games:
        await update.message.reply_text(
            "You are already in a game. Please leave the current game before joining a new one.")
        return

    if not game_code:
        await update.message.reply_text("Please enter a valid game code.")
        return

    if game_code not in active_games:
        await update.message.reply_text("Invalid game code.")
        return

    active_game = active_games[game_code]
    if user_id == active_game['god_id']:
        await update.message.reply_text(
            "You are the game creator. Please close the current game before joining a new one.")
        return

    active_game['pending_requests'].append(user_id)
    join_requests[user_id] = game_code

    await context.bot.send_message(active_game['god_id'],
                                   f"User with ID {user_id} wants to join your game. Use /permit or /deny followed by the user ID to respond.")
    await update.message.reply_text("Your join request has been sent to the game owner.")


async def leave_game(update: Update, context) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in user_games:
        await query.answer("You are not currently in any game.", show_alert=True)
        return

    games_to_leave = [game_code for game_code, game in active_games.items() if user_id in game['players']]

    for game_code in games_to_leave:
        active_game = active_games[game_code]

        if user_id == active_game['god_id']:
            for player_id in active_game['players']:
                await context.bot.send_message(player_id,
                                               "The game creator has closed the game. All players have been removed.")
                user_games.pop(player_id)
            active_games.pop(game_code)
        else:
            active_game['players'].remove(user_id)
            await context.bot.send_message(active_game['god_id'], f"User with ID {user_id} has left the game.")
            user_games.pop(user_id)

    keyboard = [
        [InlineKeyboardButton("Back to main menu", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text("You have successfully left the game(s).", reply_markup=reply_markup)


async def permit_join(update: Update, context) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_games:
        await update.message.reply_text("You are not the owner of any game.")
        return

    game_code = user_games[user_id]
    active_game = active_games[game_code]

    if user_id != active_game['god_id']:
        await update.message.reply_text("You are not the owner of the game.")
        return

    try:
        target_user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if target_user_id not in active_game['pending_requests']:
        await update.message.reply_text("This user has not requested to join your game.")
        return

    active_game['pending_requests'].remove(target_user_id)
    active_game['players'].append(target_user_id)
    user_games[target_user_id] = game_code

    await update.message.reply_text(f"User with ID {target_user_id} has been permitted to join the game.")
    await context.bot.send_message(target_user_id, "Your request to join the game has been accepted.")


async def deny_join(update: Update, context) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_games:
        await update.message.reply_text("You are not the owner of any game.")
        return

    game_code = user_games[user_id]
    active_game = active_games[game_code]

    if user_id != active_game['god_id']:
        await update.message.reply_text("You are not the owner of the game.")
        return

    try:
        target_user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if target_user_id not in active_game['pending_requests']:
        await update.message.reply_text("This user has not requested to join your game.")
        return

    active_game['pending_requests'].remove(target_user_id)

    await update.message.reply_text(f"User with ID {target_user_id} has been denied to join the game.")
    await context.bot.send_message(target_user_id, "Your request to join the game has been denied.")


async def kick_player(update: Update, context) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_games:
        await update.message.reply_text("You are not the owner of any game.")
        return

    game_code = user_games[user_id]
    active_game = active_games[game_code]

    if user_id != active_game['god_id']:
        await update.message.reply_text("You are not the owner of the game.")
        return

    try:
        target_user_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID.")
        return

    if target_user_id not in active_game['players']:
        await update.message.reply_text("This user is not in your game.")
        return

    if target_user_id == active_game['god_id']:
        await update.message.reply_text("You cannot kick yourself.")
        return

    active_game['players'].remove(target_user_id)
    user_games.pop(target_user_id)

    await update.message.reply_text(f"User with ID {target_user_id} has been kicked from the game.")
    await context.bot.send_message(target_user_id, "You have been kicked from the game.")


async def button(update: Update, context) -> None:
    query = update.callback_query
    data = query.data

    if data == 'create_game':
        await create_game(update, context)
    elif data == 'join_game':
        await join_game_prompt(update, context)
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, join_game))
    application.add_handler(CommandHandler("permit", permit_join))
    application.add_handler(CommandHandler("deny", deny_join))
    application.add_handler(CommandHandler("kick", kick_player))

    application.run_polling()


if __name__ == '__main__':
    main()
