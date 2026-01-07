import os
import logging
import subprocess
import glob
import time
import sys
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیمات
BOT_TOKEN = "8153826365:AAHajypwFzT1V9FTWf7FVsLs5Ei93P2fYzs"
ADMIN_ID = 7980934803
ADMINS = {ADMIN_ID}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دکمه‌های گاد
main_keyboard = [
    ["📁 لیست فایل‌ها", "🟢 وضعیت اجرا"],
    ["▶️ اجرای فایل", "⏹ توقف اجرا"], 
    ["📊 مشاهده گزارش‌ها", "📚 مدیریت کتابخانه"],
    ["👥 مدیریت ادمین", "🐍 نسخه پایتون"]
]

admin_keyboard = [
    ["➕ افزودن ادمین", "➖ حذف ادمین"],
    ["📋 لیست ادمین‌ها", "🔙 بازگشت"]
]

pip_keyboard = [
    ["📥 نصب کتابخانه", "🗑 حذف کتابخانه"],
    ["📃 لیست کتابخانه‌ها", "🔙 بازگشت"]
]

python_keyboard = [
    ["🐍 python3", "🐍 python3.11"],
    ["🐍 python3.12", "🔙 بازگشت"]
]

back_keyboard = [["🔙 بازگشت"]]

def is_admin(user_id):
    return user_id in ADMINS

class BotManager:
    def __init__(self):
        self.active_bots = {}
        self.python_version = "python3"  # نسخه پیش‌فرض
        
    def set_python_version(self, version):
        """تعیین نسخه پایتون برای اجرا"""
        self.python_version = version
        return f"✅ نسخه پایتون به {version} تغییر کرد"
        
    def run_python_script(self, file_path):
        try:
            project_name = os.path.basename(file_path).replace('.py', '')
            
            install_result = self.auto_install_requirements(file_path)
            if not install_result[0]:
                return False, f"خطا در نصب کتابخانه‌ها: {install_result[1]}"
            
            process = subprocess.Popen(
                [self.python_version, file_path],
                stdout=open(f'{project_name}_output.log', 'w'),
                stderr=open(f'{project_name}_error.log', 'w')
            )
            
            self.active_bots[project_name] = process
            
            time.sleep(3)
            if process.poll() is None:
                return True, f"فایل {project_name} با {self.python_version} اجرا شد (PID: {process.pid})"
            else:
                error_msg = "خطای ناشناخته"
                try:
                    with open(f'{project_name}_error.log', 'r') as f:
                        error_msg = f.read()[:500]
                except:
                    pass
                return False, f"اجرا ناموفق. خطا: {error_msg}"
            
        except Exception as e:
            return False, f"خطا در اجرا: {str(e)}"

    def auto_install_requirements(self, file_path):
        try:
            dir_path = os.path.dirname(file_path)
            req_file = os.path.join(dir_path, "requirements.txt")
            
            if os.path.exists(req_file):
                result = subprocess.run(
                    [self.python_version, '-m', 'pip', 'install', '-r', req_file],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    return True, "کتابخانه‌ها نصب شدند"
                else:
                    return False, result.stderr
            return True, "فایل requirements.txt پیدا نشد"
        except Exception as e:
            return False, str(e)

    def install_package(self, package_name):
        try:
            result = subprocess.run(
                [self.python_version, '-m', 'pip', 'install', package_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return True, f"کتابخانه {package_name} نصب شد"
            else:
                return False, f"خطا در نصب: {result.stderr}"
        except Exception as e:
            return False, f"خطا: {str(e)}"

    def uninstall_package(self, package_name):
        try:
            result = subprocess.run(
                [self.python_version, '-m', 'pip', 'uninstall', '-y', package_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                return True, f"کتابخانه {package_name} حذف شد"
            else:
                return False, f"خطا در حذف: {result.stderr}"
        except Exception as e:
            return False, f"خطا: {str(e)}"

    def list_packages(self):
        try:
            result = subprocess.run(
                [self.python_version, '-m', 'pip', 'list'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, f"خطا: {str(e)}"

bot_manager = BotManager()

async def show_main_menu(update: Update, text: str = "منوی اصلی:"):
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    current_dir = os.getcwd()
    await update.message.reply_text(
        f"🤖 ربات مدیریت فایل‌های پایتون\n\n"
        f"📁 مسیر جاری: {current_dir}\n"
        f"🐍 نسخه پایتون فعلی: {bot_manager.python_version}\n\n"
        "💡 از دکمه‌های زیر استفاده کن:",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    )

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    py_files = glob.glob("*.py")
    
    if not py_files:
        await update.message.reply_text("❌ هیچ فایل پایتونی پیدا نشد")
        return
    
    message = "📁 فایل‌های پایتون:\n\n"
    for file in py_files:
        status = "🟢 فعال" if file.replace('.py', '') in bot_manager.active_bots else "🔴 غیرفعال"
        message += f"{file} - {status}\n"
    
    await update.message.reply_text(message)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if not bot_manager.active_bots:
        await update.message.reply_text("❌ هیچ فایلی در حال اجرا نیست")
        return
    
    message = "🟢 فایل‌های در حال اجرا:\n\n"
    for name, process in bot_manager.active_bots.items():
        if process.poll() is None:
            message += f"{name} - PID: {process.pid} - فعال\n"
        else:
            message += f"{name} - متوقف شده\n"
    
    await update.message.reply_text(message)

async def show_specific_logs(update, bot_name):
    error_log = f"{bot_name}_error.log"
    output_log = f"{bot_name}_output.log"
    
    message = f"📊 گزارش‌های {bot_name}:\n\n"
    
    if os.path.exists(error_log):
        with open(error_log, 'r') as f:
            error_content = f.read().strip()
        if error_content:
            message += f"❌ خطاها:\n{error_content[:1000]}\n\n"
        else:
            message += "✅ فایل خطا خالی است\n\n"
    else:
        message += "❌ فایل خطا وجود ندارد\n\n"
        
    if os.path.exists(output_log):
        with open(output_log, 'r') as f:
            output_content = f.read().strip()
        if output_content:
            message += f"📄 خروجی:\n{output_content[:1000]}"
        else:
            message += "📄 فایل خروجی خالی است"
    else:
        message += "❌ فایل خروجی وجود ندارد"
    
    await update.message.reply_text(message)

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if context.args:
        bot_name = context.args[0]
        await show_specific_logs(update, bot_name)
    else:
        await update.message.reply_text("لطفا نام را وارد کنید: /logs name")

async def run_script(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if context.args:
        file_name = context.args[0]
        if os.path.exists(file_name) and file_name.endswith('.py'):
            os.chmod(file_name, 0o755)
            success, message = bot_manager.run_python_script(file_name)
            await update.message.reply_text(f"{message}" if success else f"❌ خطا: {message}")
            await show_specific_logs(update, file_name.replace('.py', ''))
        else:
            await update.message.reply_text("❌ فایل پیدا نشد یا فرمت اشتباه است")
    else:
        await update.message.reply_text("لطفا نام فایل را وارد کنید: /run filename.py")

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if context.args:
        bot_name = context.args[0]
        if bot_name in bot_manager.active_bots:
            bot_manager.active_bots[bot_name].terminate()
            del bot_manager.active_bots[bot_name]
            await update.message.reply_text(f"⏹ اجرای {bot_name} متوقف شد")
        else:
            await update.message.reply_text("❌ اجرای فعالی با این نام پیدا نشد")
    else:
        await update.message.reply_text("لطفا نام را وارد کنید: /stop name")

async def pip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if not context.args:
        await update.message.reply_text(
            f"دستورات مدیریت کتابخانه (نسخه: {bot_manager.python_version}):\n\n"
            "/pip install نام_کتابخانه\n"
            "/pip uninstall نام_کتابخانه\n"
            "/pip list"
        )
        return
    
    command = context.args[0]
    
    if command == "install" and len(context.args) > 1:
        package_name = context.args[1]
        success, message = bot_manager.install_package(package_name)
        await update.message.reply_text(message)
        
    elif command == "uninstall" and len(context.args) > 1:
        package_name = context.args[1]
        success, message = bot_manager.uninstall_package(package_name)
        await update.message.reply_text(message)
        
    elif command == "list":
        success, message = bot_manager.list_packages()
        if success:
            if len(message) > 4000:
                message = message[:4000] + "\n\n... (ادامه دارد)"
            await update.message.reply_text(f"کتابخانه‌های نصب شده ({bot_manager.python_version}):\n```\n{message}\n```", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"خطا: {message}")
    else:
        await update.message.reply_text("دستور نامعتبر!\nمثال: /pip install requests")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if context.args:
        try:
            new_admin_id = int(context.args[0])
            ADMINS.add(new_admin_id)
            await update.message.reply_text(f"ادمین با آیدی {new_admin_id} اضافه شد")
        except ValueError:
            await update.message.reply_text("آیدی باید عدد باشد")
    else:
        await update.message.reply_text("لطفا آیدی عددی کاربر را وارد کنید: /addadmin 123456789")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if context.args:
        try:
            admin_id = int(context.args[0])
            if admin_id in ADMINS:
                ADMINS.remove(admin_id)
                await update.message.reply_text(f"ادمین با آیدی {admin_id} حذف شد")
            else:
                await update.message.reply_text("این آیدی در لیست ادمین‌ها نیست")
        except ValueError:
            await update.message.reply_text("آیدی باید عدد باشد")
    else:
        await update.message.reply_text("لطفا آیدی عددی کاربر را وارد کنید: /removeadmin 123456789")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    if ADMINS:
        admins_list = "\n".join([str(admin_id) for admin_id in ADMINS])
        await update.message.reply_text(f"لیست ادمین‌ها:\n{admins_list}")
    else:
        await update.message.reply_text("لیست ادمین‌ها خالی است")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return

    document = update.message.document
    
    if document.file_name.endswith('.py'):
        await update.message.reply_text("📥 دریافت فایل...")
        
        file = await context.bot.get_file(document.file_id)
        file_path = document.file_name
        
        await file.download_to_drive(file_path)
        os.chmod(file_path, 0o755)
        
        success, message = bot_manager.run_python_script(file_path)
        await update.message.reply_text(f"{message}" if success else f"❌ خطا: {message}")
        
        await show_specific_logs(update, document.file_name.replace('.py', ''))
        
    else:
        await update.message.reply_text("❌ فقط فایل‌های پایتون (.py) پشتیبانی می‌شوند")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دسترسی ندارید!")
        return
    
    text = update.message.text
    
    if text == "📁 لیست فایل‌ها":
        await list_files(update, context)
    elif text == "🟢 وضعیت اجرا":
        await status(update, context)
    elif text == "▶️ اجرای فایل":
        await update.message.reply_text(
            f"نام فایل رو بفرست (مثلاً: bot.py)\n\nنسخه پایتون فعلی: {bot_manager.python_version}",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'run_file'
    elif text == "⏹ توقف اجرا":
        await update.message.reply_text(
            "نام فایل در حال اجرا رو بفرست:",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'stop_file'
    elif text == "📊 مشاهده گزارش‌ها":
        await update.message.reply_text(
            "نام فایل رو بفرست (بدون .py):",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'show_logs'
    elif text == "📚 مدیریت کتابخانه":
        await update.message.reply_text(
            f"مدیریت کتابخانه‌ها (نسخه: {bot_manager.python_version}):",
            reply_markup=ReplyKeyboardMarkup(pip_keyboard, resize_keyboard=True)
        )
    elif text == "👥 مدیریت ادمین":
        await update.message.reply_text(
            "مدیریت ادمین‌ها:",
            reply_markup=ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)
        )
    elif text == "🐍 نسخه پایتون":
        await update.message.reply_text(
            f"نسخه پایتون فعلی: {bot_manager.python_version}\n\nیکی از نسخه‌ها را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(python_keyboard, resize_keyboard=True)
        )
    elif text == "📥 نصب کتابخانه":
        await update.message.reply_text(
            f"نام کتابخانه رو بفرست (مثلاً: requests)\n\nنسخه پایتون: {bot_manager.python_version}",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'install_package'
    elif text == "🗑 حذف کتابخانه":
        await update.message.reply_text(
            "نام کتابخانه رو بفرست:",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'uninstall_package'
    elif text == "📃 لیست کتابخانه‌ها":
        success, message = bot_manager.list_packages()
        if success:
            if len(message) > 4000:
                message = message[:4000] + "\n\n... (ادامه دارد)"
            await update.message.reply_text(f"📚 کتابخانه‌های نصب شده ({bot_manager.python_version}):\n```\n{message}\n```", 
                                          parse_mode='Markdown',
                                          reply_markup=ReplyKeyboardMarkup(pip_keyboard, resize_keyboard=True))
        else:
            await update.message.reply_text(f"خطا: {message}")
    elif text in ["🐍 python3", "🐍 python3.11", "🐍 python3.12"]:
        version = text.replace("🐍 ", "")
        message = bot_manager.set_python_version(version)
        await update.message.reply_text(message)
        await show_main_menu(update, f"{message}\n\nمنوی اصلی:")
    elif text == "➕ افزودن ادمین":
        await update.message.reply_text(
            "آیدی عددی کاربر رو بفرست:",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'add_admin'
    elif text == "➖ حذف ادمین":
        await update.message.reply_text(
            "آیدی عددی ادمین رو بفرست:",
            reply_markup=ReplyKeyboardMarkup(back_keyboard, resize_keyboard=True)
        )
        context.user_data['waiting_for'] = 'remove_admin'
    elif text == "📋 لیست ادمین‌ها":
        if ADMINS:
            admins_list = "\n".join([f"👤 {admin_id}" for admin_id in ADMINS])
            await update.message.reply_text(f"📋 لیست ادمین‌ها:\n{admins_list}",
                                          reply_markup=ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True))
        else:
            await update.message.reply_text("لیست ادمین‌ها خالی است")
    elif text == "🔙 بازگشت":
        await show_main_menu(update)
    elif 'waiting_for' in context.user_data:
        waiting_for = context.user_data['waiting_for']
        
        if waiting_for == 'run_file':
            file_name = text
            if os.path.exists(file_name) and file_name.endswith('.py'):
                os.chmod(file_name, 0o755)
                success, message = bot_manager.run_python_script(file_name)
                await update.message.reply_text(f"{message}" if success else f"❌ خطا: {message}")
                await show_specific_logs(update, file_name.replace('.py', ''))
            else:
                await update.message.reply_text("❌ فایل پیدا نشد یا فرمت اشتباه است")
                
        elif waiting_for == 'stop_file':
            bot_name = text
            if bot_name in bot_manager.active_bots:
                bot_manager.active_bots[bot_name].terminate()
                del bot_manager.active_bots[bot_name]
                await update.message.reply_text(f"⏹ اجرای {bot_name} متوقف شد")
            else:
                await update.message.reply_text("❌ اجرای فعالی با این نام پیدا نشد")
                
        elif waiting_for == 'show_logs':
            await show_specific_logs(update, text)
            
        elif waiting_for == 'install_package':
            success, message = bot_manager.install_package(text)
            await update.message.reply_text(message)
            
        elif waiting_for == 'uninstall_package':
            success, message = bot_manager.uninstall_package(text)
            await update.message.reply_text(message)
            
        elif waiting_for == 'add_admin':
            try:
                new_admin_id = int(text)
                ADMINS.add(new_admin_id)
                await update.message.reply_text(f"✅ ادمین با آیدی {new_admin_id} اضافه شد")
            except ValueError:
                await update.message.reply_text("❌ آیدی باید عدد باشد")
                
        elif waiting_for == 'remove_admin':
            try:
                admin_id = int(text)
                if admin_id in ADMINS:
                    ADMINS.remove(admin_id)
                    await update.message.reply_text(f"✅ ادمین با آیدی {admin_id} حذف شد")
                else:
                    await update.message.reply_text("❌ این آیدی در لیست ادمین‌ها نیست")
            except ValueError:
                await update.message.reply_text("❌ آیدی باید عدد باشد")
        
        context.user_data.pop('waiting_for', None)
        await show_main_menu(update)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("run", run_script))
    application.add_handler(CommandHandler("list", list_files))
    application.add_handler(CommandHandler("stop", stop_bot))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("logs", show_logs))
    application.add_handler(CommandHandler("pip", pip_command))
    application.add_handler(CommandHandler("addadmin", add_admin))
    application.add_handler(CommandHandler("removeadmin", remove_admin))
    application.add_handler(CommandHandler("listadmins", list_admins))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 ربات مدیریت فایل‌های پایتون شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()