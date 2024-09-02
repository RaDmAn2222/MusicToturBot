from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import mysql.connector
from datetime import datetime, timedelta

# connecting to the database
db = mysql.connector.connect(
    host="",
    user="",
    password="",
    database=""
)

cursor = db.cursor()

# starting the bot
def start(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Register as Tutor", callback_data='register_tutor'),
            InlineKeyboardButton("Register as Student", callback_data='register_student')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome to the Music Tutor Assistant Bot! How can I assist you?", reply_markup=reply_markup)

# button handler for commands
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'register_tutor':
        query.edit_message_text(text="Please enter your details in the format: /register_tutor <name> <password>")
    elif query.data == 'register_student':
        query.edit_message_text(text="Please enter your details in the format: /register_student <name>")
    
    elif query.data.startswith('confirm_'):
        student_id = query.data.split('_', 1)[1]

        cursor.execute("UPDATE Students SET status = 'Active' WHERE telegram_id = %s", (student_id,))
        db.commit()

        # Notify the student about the confirmation
        context.bot.send_message(chat_id=student_id, text="Your registration has been confirmed. Welcome to the class!")

        # Send a new message to the tutor confirming the action
        context.bot.send_message(chat_id=query.message.chat_id, text="Student registration confirmed.")

        context.bot.send_message(chat_id=query.message.chat_id, text="Please schedule the student's first class and payment amoun by using the command:\n/schedule_class <student_name> <day> <YYYY-MM-DD> <HH:MM> <paymount amount>")
                                 

    
    elif query.data.startswith('attendance_'):
        student_name = query.data.split('_', 1)[1]
        telegram_id = query.from_user.id  # Use the from_user ID to identify the student

        cursor.execute("SELECT student_id FROM Students WHERE telegram_id = %s AND status = %s", (telegram_id, "Active"))
        result = cursor.fetchone()

        if result:
            student_id = result[0]  # Extract the student_id from the fetched result

            # Fetch the current attendance record for the student
            cursor.execute("""
                SELECT session_1, session_2, session_3, session_4
                FROM Attendance
                WHERE student_id = %s AND month_year = %s
            """, (student_id, datetime.now().strftime("%Y-%m")))
            attendance = cursor.fetchone()

            if attendance:
                # Check if all sessions have been marked
                if all(session != 'Not Checked' for session in attendance):
                    # Reset the attendance if all sessions have been marked
                    cursor.execute("""
                        UPDATE Attendance 
                        SET session_1 = 'Not Checked', session_2 = 'Not Checked',
                            session_3 = 'Not Checked', session_4 = 'Not Checked'
                        WHERE student_id = %s AND month_year = %s
                    """, (student_id, datetime.now().strftime("%Y-%m")))
                    db.commit()
                    query.edit_message_text(text=f"All sessions have been checked. Resetting the attendance for {student_name}. Please /mark_attendace again.")
                    return

                # Determine the next session to mark
                next_session = None
                if attendance[0] == 'Not Checked':
                    next_session = 'session_1'
                elif attendance[1] == 'Not Checked':
                    next_session = 'session_2'
                elif attendance[2] == 'Not Checked':
                    next_session = 'session_3'
                elif attendance[3] == 'Not Checked':
                    next_session = 'session_4'

                if next_session:
                    # Here, we assume you're marking "Present" by default; this can be changed based on user input
                    cursor.execute(f"""
                        UPDATE Attendance 
                        SET {next_session} = %s
                        WHERE student_id = %s AND month_year = %s
                    """, ('Present', student_id, datetime.now().strftime("%Y-%m")))
                    db.commit()
                    session_number = next_session[-1]  # Extract the session number (1, 2, 3, or 4)
                    query.edit_message_text(text=f"Attendance marked for {student_name}. Session: {session_number}")
                    
                    if session_number == '4':
                        cursor.execute("""
                            UPDATE Students
                            SET status = "Pending"
                            WHERE student_id = %s
                        """, (student_id,))
                        db.commit()
                        query.edit_message_text(text=f"Attendance marked for {student_name}. Session: {session_number}. Your fourth session is over. Please register for the next course.")
            else:
                # If there's no attendance record for this month, create one starting with session_1
                cursor.execute("""
                    INSERT INTO Attendance (student_id, session_1, month_year)
                    VALUES (%s, %s, %s)
                """, (student_id, 'Present', datetime.now().strftime("%Y-%m")))
                db.commit()
                query.edit_message_text(text=f"Attendance marked for {student_name}. Session: 1")
        else:
            query.edit_message_text(text="Student not found or the name is incorrect.")

    elif query.data.startswith("cancel_"):
        student_name = query.data.split("cancel_")[1]
        
        query.edit_message_text(f"Session for {student_name} has been cancelled. Please provide the makeup session details in the format:\n/makeup_session name <day_of_week> <YYYY-MM-DD> <HH:MM>")

# tutor registration
def register_tutor(update: Update, context: CallbackContext):
    password = ""
    if update.message.text.split(' ', 2)[2] == password:
        tutor_name = update.message.text.split(' ', 2)[1]
        telegram_id = update.message.chat_id

        cursor.execute("INSERT INTO Students (name, telegram_id, role, registered_date, status) VALUES (%s, %s, %s, %s, %s)",
                       (tutor_name, telegram_id, 'tutor', datetime.now().date(), 'Active'))
        db.commit()

        update.message.reply_text("Tutor registration completed.")
    else:
        update.message.reply_text("Incorrect password.")

# registering the student(by the student)
def register_student(update: Update, context: CallbackContext):
    student_name = update.message.text.split(' ', 1)[1]
    telegram_id = update.message.chat_id

    cursor.execute("INSERT INTO Students (name, telegram_id, registered_date, status) VALUES (%s, %s, %s, %s)",
                   (student_name, telegram_id, datetime.now().date(), 'Pending'))
    db.commit()

    cursor.execute("SELECT telegram_id FROM Students WHERE role = 'tutor'")
    tutor_id = cursor.fetchone()[0]
    context.bot.send_message(chat_id=tutor_id, text=f"New registration request from {student_name}. Please check the payment receipt")

    update.message.reply_text("Your temporary registration is complete. Please send your payment receipt.")

# sending payment photo
def handle_photo(update: Update, context: CallbackContext):
    student_id = update.message.chat_id
    
    cursor.execute("SELECT name FROM Students WHERE telegram_id = %s", (student_id,))
    student_name = cursor.fetchone()[0]

    # recieving payment photo
    photo = update.message.photo[-1]

    # sending the photo to the tutor
    cursor.execute("SELECT telegram_id FROM Students WHERE role = 'tutor'")
    tutor_id = cursor.fetchone()[0]
    
    # confirming student registration
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm Registration",
                callback_data=f'confirm_{student_id}'
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(chat_id=tutor_id, photo=photo.file_id, caption=f"Payment receipt from {student_name}.", reply_markup=reply_markup)
    update.message.reply_text("Your receipt has been sent. Please wait for the teacher's confirmation.")

def schedule_class(update: Update, context: CallbackContext):
    try:
        student_name = context.args[0]
        class_day_of_week = context.args[1]
        class_date = datetime.strptime(context.args[2], "%Y-%m-%d").date()
        class_time = datetime.strptime(context.args[3], "%H:%M").time()
        payment_amount = context.args[4]

        # Find the student's ID
        cursor.execute("SELECT student_id FROM Students WHERE name = %s", (student_name,))
        student_id = cursor.fetchone()

        if student_id:
            # Insert or update the scheduled class in the Sessions table
            cursor.execute("""
                INSERT INTO Sessions (student_id, session_date, session_time, day_of_week, status)
                VALUES (%s, %s, %s, %s, 'Scheduled')
                ON DUPLICATE KEY UPDATE
                    session_date = VALUES(session_date),
                    session_time = VALUES(session_time),
                    day_of_week = VALUES(day_of_week),
                    status = 'Scheduled'
            """, (student_id[0], class_date, class_time, class_day_of_week))
            db.commit()

            # Update last payment information in the Students table
            cursor.execute("""
                UPDATE Students 
                SET last_payment_amount = %s, last_payment_date = %s
                WHERE student_id = %s
            """, (payment_amount, datetime.now().date(), student_id[0]))
            db.commit()

            # Notify the student about the scheduled class
            cursor.execute("SELECT telegram_id FROM Students WHERE student_id = %s", (student_id[0],))
            student_telegram_id = cursor.fetchone()[0]
            context.bot.send_message(chat_id=student_telegram_id, text=f"Your class has been scheduled on {class_date} at {class_time}.")

            update.message.reply_text(f"Class for {student_name} scheduled on {class_date} at {class_time}.")
        else:
            update.message.reply_text("Student not found.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /schedule_class <student_name> <YYYY-MM-DD> <HH:MM:SS>")


# marking attendance
def mark_attendance(update: Update, context: CallbackContext):
    student_id = update.message.chat_id

    # Correct the tuple formatting for the parameter
    cursor.execute("SELECT name FROM Students WHERE telegram_id = %s", (student_id,))
    student_name = cursor.fetchone()[0]

    # Generate the attendance button with the student's name in the callback data
    keyboard = [
        [
            InlineKeyboardButton("Mark Attendance", callback_data=f'attendance_{student_name}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f"Please click the button to mark your attendance for {student_name}:", reply_markup=reply_markup)


# canceling a session (only the tutor)
def cancel_session(update: Update, context: CallbackContext):
    if not is_tutor(update):
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Fetch active students from the database except Radman
    cursor.execute("SELECT name FROM Students WHERE name != 'Radman' AND status = 'Active'")
    students = cursor.fetchall()
    
    # Create a list of InlineKeyboardButton objects
    keyboard = [
        [InlineKeyboardButton(name[0], callback_data=f"cancel_{name[0]}")]
        for name in students
    ]
    
    # Create InlineKeyboardMarkup object
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message with the keyboard
    update.message.reply_text("Please select a student to cancel their session.", reply_markup=reply_markup)

# scheduling for makeup session
def makeup_session(update: Update, context: CallbackContext):
    if not is_tutor(update):
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    student_name = context.args[0]    
    makeup_day_of_week = context.args[1]
    makeup_date = datetime.strptime(context.args[2], "%Y-%m-%d").date()
    makeup_time = datetime.strptime(context.args[3], "%H:%M").time()

    cursor.execute("""
        UPDATE Sessions 
        SET makeup_session_date = %s, makeup_session_time = %s, makeup_day_of_week = %s
        WHERE student_id = (SELECT student_id FROM Students WHERE name = %s)
    """, (makeup_date, makeup_time, makeup_day_of_week, student_name))
    db.commit()

    # informing the student
    cursor.execute("SELECT telegram_id FROM Students WHERE name = %s", (student_name,))
    student_id = cursor.fetchone()[0]
    context.bot.send_message(chat_id=student_id, text=f"Your class has been rescheduled to {makeup_date}.")

    update.message.reply_text(f"The class for {student_name} has been rescheduled to {makeup_date}.")

# cleaning up students who haven't registered
def cleanup_non_registered(update: Update, context: CallbackContext):
    if not is_tutor(update):
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    cursor.execute("""
        DELETE FROM Students 
        WHERE status = "Pending" OR status = "Inactive" 
        AND DATEDIFF(NOW(), registered_date) > 7
    """)
    db.commit()

    update.message.reply_text("Non-registered students have been cleaned up.")

# request for absence every 3 month
def request_absence(update: Update, context: CallbackContext):
    student_id = update.message.chat_id

    # Fetch student name
    cursor.execute("SELECT name FROM Students WHERE telegram_id = %s", (student_id,))
    student_name = cursor.fetchone()
    student_name = student_name[0] if student_name else None

    # Fetch last absence date
    cursor.execute("SELECT last_absence FROM Students WHERE telegram_id = %s", (student_id,))
    last_absence = cursor.fetchone()
    last_absence = last_absence[0] if last_absence else None

    # Fetch tutor ID
    cursor.execute("SELECT telegram_id FROM Students WHERE name = 'Radman'")
    tutor_id = cursor.fetchone()
    tutor_id = tutor_id[0] if tutor_id else None

    # Check if absence can be granted
    if last_absence is None or datetime.now().date() >= last_absence + timedelta(days=90):
        cursor.execute("""
            UPDATE Students 
            SET last_absence = %s, excused_absences = excused_absences + 1
            WHERE name = %s
        """, (datetime.now().date(), student_name))
        db.commit()

        update.message.reply_text("Your absence has been granted.")
        if tutor_id:
            context.bot.send_message(chat_id=tutor_id, text=f"{student_name} has requested an excused absence for this session.")
    else:
        next_absence_date = last_absence + timedelta(days=90)
        update.message.reply_text(f"You can request the next absence after {next_absence_date}.")

# making sure that some commands only runs for the tutor
def is_tutor(update: Update):
    telegram_id = update.message.chat_id
    cursor.execute("SELECT COUNT(*) FROM Students WHERE telegram_id = %s AND role = 'tutor'", (telegram_id,))
    return cursor.fetchone()[0] > 0

# help command
def help_command(update: Update, context: CallbackContext):
    help_text = """
Here are the commands you can use:

/start - Start interacting with the Music Tutor Assistant bot.
/register_tutor <name> <password> - Register as a tutor by providing your name and password.
/register_student <name> - Register as a student by providing your name.
/schedule_class <student_name> <day_of_week> <YYYY-MM-DD> <HH:MM> <payment_amount> - Schedule a class for a student.
/mark_attendance - Mark attendance for the current session.
/cancel_session - Cancel a session for a student (only for tutors).
/makeup_session <name> <day_of_week> <YYYY-MM-DD> <HH:MM> - Schedule a makeup session for a student (only for tutors).
/cleanup_non_registered - Remove students who have not completed registration within 7 days (only for tutors).
/request_absence - Request an excused absence (only available once every 3 months).
/help - Show this help message.
"""
    update.message.reply_text(help_text)

# setting up the bot
def main():
    updater = Updater("TOKEN_BOT", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))  # buttons handler
    dp.add_handler(CommandHandler("register_tutor", register_tutor))
    dp.add_handler(CommandHandler("register_student", register_student))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(CommandHandler("schedule_class", schedule_class, pass_args=True))
    dp.add_handler(CommandHandler("mark_attendance", mark_attendance))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("cancel_session", cancel_session, pass_args=True))
    dp.add_handler(CommandHandler("makeup_session", makeup_session, pass_args=True))
    dp.add_handler(CommandHandler("cleanup_non_registered", cleanup_non_registered))
    dp.add_handler(CommandHandler("request_absence", request_absence, pass_args=True))
    dp.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
