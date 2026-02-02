import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    filters,
    CallbackQueryHandler
)

# ===================== CONFIGURATION =====================
BOT_TOKEN = "8564742601:AAE443rYAWxLmIITweoGWNSlXD7nXvne4Fo"
CHANNEL_ID = -1003872857468  # আপনার চ্যানেল ID
CHANNEL_USERNAME = "@Cinaflixsteem"  # আপনার চ্যানেল username
ADMIN_ID = 1858324638  # আপনার Telegram User ID
MINI_APP_URL = "https://cinaflix-streaming.vercel.app/"  # আপনার Mini App URL

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== STATISTICS =====================
stats = {
    'total_users': set(),
    'videos_sent_today': 0,
    'total_videos_sent': 0
}


# ===================== START COMMAND =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - supports deep linking for video playback"""
    user = update.effective_user
    stats['total_users'].add(user.id)
    
    # Check if this is a video request (deep link)
    if context.args and len(context.args) > 0:
        video_id = context.args[0]
        await handle_video_request(update, context, video_id)
        return
    
    # Normal start - show welcome message with Mini App
    keyboard = [
        [InlineKeyboardButton("🎬 Open CINEFLIX App", web_app={"url": MINI_APP_URL})],
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎬 **Welcome to CINEFLIX!**

Hello **{user.first_name}**! 👋

আপনার সব পছন্দের Movies, Series এবং Exclusive Content এক জায়গায়!

**🚀 How to Use:**
1️⃣ নিচে "Open CINEFLIX App" ক্লিক করুন
2️⃣ যেকোনো video select করুন
3️⃣ Watch Now ক্লিক করুন
4️⃣ Enjoy! 🍿

**📢 Important:**
- সব content unlock করতে আমাদের channel join করুন
- Premium quality HD videos
- Regular updates

Happy Streaming! 🎉
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


# ===================== VIDEO REQUEST HANDLER =====================
async def handle_video_request(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str):
    """
    Handle video playback request from Mini App
    Video ID format: Message ID from channel
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Video request from {user.id} for video ID: {video_id}")
    
    try:
        # Check if user is member of channel
        try:
            member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
            is_member = member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            is_member = False
        
        if is_member:
            # User is member - send video
            try:
                # Forward message from channel
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=CHANNEL_ID,
                    message_id=int(video_id)
                )
                
                # Update stats
                stats['videos_sent_today'] += 1
                stats['total_videos_sent'] += 1
                
                # Send success message
                keyboard = [[InlineKeyboardButton("🔙 Back to App", web_app={"url": MINI_APP_URL})]]
                await update.message.reply_text(
                    "✅ **Enjoy Watching!**\n\n"
                    "Want more content? Browse CINEFLIX App! 🎬",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                logger.info(f"Successfully sent video {video_id} to user {user.id}")
                
            except Exception as e:
                logger.error(f"Error forwarding video {video_id}: {e}")
                await update.message.reply_text(
                    "❌ **Video Not Found!**\n\n"
                    "This video might have been removed or the link is incorrect.\n"
                    "Please try another video from the app.",
                    parse_mode='Markdown'
                )
        else:
            # User is NOT member - show join prompt
            keyboard = [
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
                [InlineKeyboardButton("✅ I Joined - Retry", callback_data=f"verify_{video_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🔒 **Content Locked!**\n\n"
                f"Join our channel **{CHANNEL_USERNAME}** to unlock this video!\n\n"
                "**Steps:**\n"
                "1️⃣ Click 'Join Channel' below\n"
                "2️⃣ Join the channel\n"
                "3️⃣ Click 'I Joined - Retry'\n\n"
                "After joining, you'll get instant access! 🎉",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_video_request: {e}")
        await update.message.reply_text(
            "❌ **Something went wrong!**\n\n"
            "Please try again or contact admin.",
            parse_mode='Markdown'
        )


# ===================== CALLBACK QUERY HANDLER =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        help_text = """
🎬 **CINEFLIX Help**

**User Commands:**
/start - Start bot & open app
/help - Show help message

**How to Watch:**
1. Open CINEFLIX App from /start
2. Browse videos
3. Click on any video
4. Click "Watch Now"
5. Bot will send you the video!

**Troubleshooting:**
❓ Video not playing? Join our channel first!
❓ App not loading? Check your internet connection
❓ Other issues? Contact admin

**Need Support?**
Contact: @YourSupportUsername

Enjoy streaming! 🍿
        """
        await query.message.reply_text(help_text, parse_mode='Markdown')
    
    elif data.startswith("verify_"):
        # User claims they joined - verify and send video
        video_id = data.replace("verify_", "")
        
        # Create a fake update object for the handler
        update.message = query.message
        await handle_video_request(update, context, video_id)


# ===================== ADMIN: MESSAGE ID EXTRACTOR =====================
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    When admin posts/forwards video to channel, 
    bot automatically replies with Message ID for Google Sheet
    """
    message = update.channel_post
    
    # Only respond to channel posts (not comments)
    if not message or message.chat.id != CHANNEL_ID:
        return
    
    # Check if this is a video/document
    if message.video or message.document or message.animation:
        message_id = message.message_id
        
        # Create formatted message for admin
        info_text = f"""
🎬 **New Video Uploaded!**

📋 **Message ID:** `{message_id}`
📝 **For Google Sheet:** `EP1:{message_id}`

**Quick Copy Formats:**
• Single Video: `Full:{message_id}`
• Episode 1: `EP1:{message_id}`
• Episode 2: `EP2:{message_id}`

💡 **Tip:** Copy the format you need and paste in Google Sheet!

✅ Video is now live in channel!
        """
        
        try:
            # Send to admin
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=info_text,
                parse_mode='Markdown'
            )
            logger.info(f"Sent Message ID {message_id} info to admin")
        except Exception as e:
            logger.error(f"Error sending Message ID to admin: {e}")


# ===================== ADMIN COMMANDS =====================
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ This command is for admin only!")
        return
    
    stats_text = f"""
📊 **CINEFLIX Bot Statistics**

👥 **Total Users:** {len(stats['total_users'])}
📹 **Videos Sent Today:** {stats['videos_sent_today']}
📊 **Total Videos Sent:** {stats['total_videos_sent']}
🤖 **Bot Status:** ✅ Running Perfectly

🎬 **Channel:** {CHANNEL_USERNAME}
🌐 **Mini App:** Active
⚡ **Server:** Railway

Keep creating amazing content! 🚀
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ This command is for admin only!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Usage:**\n\n"
            "`/broadcast Your message here`\n\n"
            "Example:\n"
            "`/broadcast নতুন সিরিজ আপডেট হয়েছে! এখনই দেখুন 🎬`",
            parse_mode='Markdown'
        )
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    status_msg = await update.message.reply_text("📤 Broadcasting message... Please wait.")
    
    for user_id in stats['total_users']:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 **Broadcast from CINEFLIX:**\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✔️ Sent: {success}\n"
        f"❌ Failed: {failed}\n\n"
        f"Total Reached: {success}/{len(stats['total_users'])} users",
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
🎬 **CINEFLIX Bot Help**

**Commands:**
/start - Start bot & open app
/help - Show this message

**Features:**
✅ Watch unlimited movies & series
✅ Download HD quality content
✅ Auto-sync with Google Sheet
✅ Premium user experience

**How to Watch:**
1. Click /start and open CINEFLIX App
2. Browse our collection
3. Click on any video
4. Enjoy! 🍿

**Support:**
Need help? Contact admin or join our channel!

{CHANNEL_USERNAME}
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get channel/user ID (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        f"**IDs:**\n\n"
        f"User ID: `{user_id}`\n"
        f"Chat ID: `{chat_id}`",
        parse_mode='Markdown'
    )


# ===================== ERROR HANDLER =====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")


# ===================== MAIN FUNCTION =====================
def main():
    """Start the bot"""
    logger.info("🚀 Starting CINEFLIX Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("getid", getid_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Channel post handler (for Message ID extraction)
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL & (filters.VIDEO | filters.Document.ALL | filters.ANIMATION),
        channel_post
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("✅ CINEFLIX Bot is now running!")
    logger.info(f"📢 Channel: {CHANNEL_USERNAME}")
    logger.info(f"🌐 Mini App: {MINI_APP_URL}")
    logger.info(f"👑 Admin: {ADMIN_ID}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
  
