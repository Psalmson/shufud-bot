#!/usr/bin/env python3
"""
🍳 Shufud — Recipe Suggestion Telegram Bot
===================================
Uses Claude AI to suggest recipes based on ingredients you have.

Setup:
  1. pip install python-telegram-bot anthropic
  2. Get a Telegram bot token from @BotFather on Telegram
  3. Get an Anthropic API key from https://console.anthropic.com
  4. Set environment variables or edit the config below
  5. python telegram_bot.py

Commands:
  /start   - Welcome message
  /recipe  - Get recipe suggestions (e.g. /recipe eggs, tomatoes, cheese)
  /help    - Show usage guide
  /clear   - Clear your ingredient memory
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

# ─── CONFIG ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are Shufud, a friendly Telegram recipe assistant with deep knowledge of Nigerian and West African cuisine.
When given a list of ingredients, suggest 2 recipes. ALWAYS include at least 1 Nigerian or West African dish if the ingredients can support it.
Great Nigerian dishes to suggest: Jollof Rice, Egusi Soup, Pepper Soup, Efo Riro, Moi Moi, Suya, Akara, Puff Puff, Ofada Stew, Banga Soup, Ofe Onugbu, Fried Plantain (Dodo), Ogbono Soup, Oha Soup, Eba & Soup, Tuwo Shinkafa, Fried Rice (Nigerian style), Ofe Akwu, Abacha (African Salad), etc.
If the ingredients include palm oil, crayfish, stockfish, ugwu, ogiri, iru, yam, or plantain — lean into 2 Nigerian recipes.
Format your response in a clear, readable way for Telegram (use emojis, keep it concise).
Use this structure for each recipe:
🍽 *Recipe Name* 🇳🇬 (add flag for Nigerian dishes)
⏱ Time: X mins | 📊 Difficulty: Easy/Medium
📝 Description: One sentence.
🛒 You'll also need: [any extra ingredients not in their list]
👨‍🍳 Steps:
1. Step one
2. Step two
3. Step three
---
Be culturally authentic — use correct Yoruba/Igbo/Hausa names where appropriate, and describe techniques properly. Keep responses friendly and encouraging!"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👨‍🍳 *Welcome to Shufud!*\n\n"
        "Tell me what ingredients you have and I'll suggest delicious recipes — "
        "with a special touch of 🇳🇬 Nigerian & African cuisine!\n\n"
        "Try:\n"
        "• `/recipe palm oil, tomatoes, stockfish, crayfish`\n"
        "• `/recipe chicken, rice, onions, pepper`\n"
        "• `/recipe plantain, eggs, flour`\n\n"
        "Use /help for more options.",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍳 *Shufud Help* 🇳🇬\n\n"
        "*Commands:*\n"
        "`/recipe <ingredients>` — Get recipe suggestions\n"
        "`/clear` — Clear remembered ingredients\n"
        "`/help` — Show this message\n\n"
        "*Examples:*\n"
        "`/recipe palm oil, egusi, stockfish, crayfish`\n"
        "`/recipe chicken, tomatoes, onions, pepper`\n"
        "`/recipe yam, eggs, onions`\n"
        "`/recipe plantain, beans`\n\n"
        "*Nigerian ingredients I know well:*\n"
        "palm oil, egusi, stockfish, crayfish, ogiri, iru,\n"
        "ugwu (fluted pumpkin), oha, utazi, plantain, yam\n\n"
        "*Tips:*\n"
        "• Separate ingredients with commas\n"
        "• Add dietary needs: `/recipe tofu, spinach - make it vegan`",
        parse_mode="Markdown"
    )


async def get_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /recipe command"""
    if not context.args:
        await update.message.reply_text(
            "Please tell me your ingredients!\n"
            "Example: `/recipe eggs, tomatoes, cheese`",
            parse_mode="Markdown"
        )
        return

    ingredients_text = " ".join(context.args)
    await fetch_and_reply(update, ingredients_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle natural language messages"""
    text = update.message.text.strip()

    if any(char in text for char in [",", "and", "have", "ingredient"]) or len(text.split()) <= 8:
        await fetch_and_reply(update, text)
    else:
        await update.message.reply_text(
            "Hi! Tell me what ingredients you have and I'll find recipes for you 🍽\n"
            "Example: `palm oil, tomatoes, stockfish, crayfish`\n"
            "Or use `/recipe` followed by your ingredients.",
            parse_mode="Markdown"
        )


async def fetch_and_reply(update: Update, ingredients_text: str):
    """Core function: call Claude and send recipe suggestions"""
    await update.message.chat.send_action("typing")

    waiting_msg = await update.message.reply_text("🔍 Finding recipes for you...")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"I have these ingredients: {ingredients_text}\nSuggest 2 recipes I can make."
            }]
        )

        reply = message.content[0].text

        await waiting_msg.delete()
        await update.message.reply_text(
            f"🧑‍🍳 *Recipes for:* _{ingredients_text}_\n\n{reply}",
            parse_mode="Markdown"
        )

    except anthropic.APIError as e:
        await waiting_msg.edit_text(f"❌ API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
        await waiting_msg.edit_text(
            "😕 Something went wrong. Please try again!\n"
            "Make sure your ingredients are listed clearly."
        )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Cleared! Start fresh by sending new ingredients.",
    )


def main():
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Please set your TELEGRAM_TOKEN environment variable")
        return

    if ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
        print("❌ Please set your ANTHROPIC_API_KEY environment variable")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("recipe", get_recipes))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🍳 Shufud bot is running! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
```

---

Now create these 3 files in your GitHub repo:

**`telegram_bot.py`** — paste the code above

**`requirements.txt`**:
```
python-telegram-bot==20.7
anthropic
```

**`Procfile`**:
```
worker: python telegram_bot.py
