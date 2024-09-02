# Music Tutor Assistant Bot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot-API-blue)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)

## Overview

The **Music Tutor Assistant Bot** is a Telegram bot designed to assist in managing a music tutoring service. It allows tutors to register students, schedule classes, mark attendance, and handle other administrative tasks through simple commands.

## Link to Telegram

[Click Here to Open the Telegram Bot](https://t.me/MusicTutorBot)

## Features

- **Tutor and Student Registration:** Register as a tutor or student.
- **Class Scheduling:** Schedule classes and makeup sessions.
- **Attendance Management:** Mark and reset attendance for sessions.
- **Payment Confirmation:** Manage student registration and confirm payment receipts.
- **Session Management:** Cancel sessions and reschedule classes.
- **Absence Requests:** Allow students to request excused absences every three months.
- **Automated Cleanup:** Remove students who haven't completed registration within 7 days.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start interacting with the Music Tutor Assistant bot. |
| `/register_tutor <name> <password>` | Register as a tutor by providing your name and password. |
| `/register_student <name>` | Register as a student by providing your name. |
| `/schedule_class <student_name> <day_of_week> <YYYY-MM-DD> <HH:MM> <payment_amount>` | Schedule a class for a student. |
| `/mark_attendance` | Mark attendance for the current session. |
| `/cancel_session` | Cancel a session for a student (only for tutors). |
| `/makeup_session <name> <day_of_week> <YYYY-MM-DD> <HH:MM>` | Schedule a makeup session for a student (only for tutors). |
| `/cleanup_non_registered` | Remove students who have not completed registration within 7 days (only for tutors). |
| `/request_absence` | Request an excused absence (only available once every 3 months). |
| `/help` | Show a list of available commands and their descriptions. |

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RaDmAn2222/MusicTutorBot.git
   cd MusicTutorBot
   ```

2. **Install dependencies:**
   Ensure you have Python 3.8+ installed, and then install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MySQL Database:**
   - Create a MySQL database and configure the connection settings in the code.
   - Run the SQL scripts to create necessary tables (e.g., `Students`, `Sessions`, `Attendance`).

4. **Configure the bot:**
   - Replace `"TOKEN_BOT"` in the code with your actual Telegram Bot API token.

5. **Run the bot:**
   ```bash
   python MusicTutorBot.py
   ```

## Usage

After the bot is running, you can interact with it through Telegram by sending commands. Start by using the `/start` command to begin the interaction.

## Contributing

If you'd like to contribute, feel free to fork the repository and submit a pull request. Contributions are welcome!

## License

This project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for more details.
EOL
