import os
import secrets
import smtplib
import ssl
from email.message import EmailMessage

import bcrypt


class PasswordResetService:
    def __init__(self, connection, hash_password, send_code=None):
        self.connection = connection
        self.hash_password = hash_password
        self.send_code = send_code or send_smtp_code

    def request(self, email):
        email = email.strip()
        if not email or len(email) > 100 or "@" not in email:
            raise ValueError("Enter a valid email address.")

        code = f"{secrets.randbelow(100_000_000):08d}"
        digest = bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode()
        cursor = self.connection.cursor(dictionary=True)
        try:
            self.connection.start_transaction()
            cursor.execute(
                """SELECT userID, email FROM users
                   WHERE email = %s AND UPPER(role) = 'READER' AND account_status = 'Active'
                   FOR UPDATE""", (email,),
            )
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    """SELECT requested_at > UTC_TIMESTAMP() - INTERVAL 60 SECOND AS cooling_down
                       FROM password_reset_codes WHERE userID = %s""", (user["userID"],),
                )
                if not (cursor.fetchone() or {}).get("cooling_down"):
                    cursor.execute(
                        """INSERT INTO password_reset_codes (userID, code_hash, expires_at, requested_at, attempts)
                           VALUES (%s, %s, UTC_TIMESTAMP() + INTERVAL 10 MINUTE, UTC_TIMESTAMP(), 0)
                           ON DUPLICATE KEY UPDATE code_hash = %s,
                               expires_at = UTC_TIMESTAMP() + INTERVAL 10 MINUTE,
                               requested_at = UTC_TIMESTAMP(), attempts = 0""",
                        (user["userID"], digest, digest),
                    )
                    self.send_code(user["email"], code)
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def reset(self, email, code, password):
        if len(password) < 8 or len(password.encode("utf-8")) > 72:
            raise ValueError("Use at least 8 characters and no more than 72 UTF-8 bytes.")
        if len(code) != 8 or not code.isascii() or not code.isdigit():
            raise ValueError("Enter the eight-digit code.")
        cursor = self.connection.cursor(dictionary=True)
        verified = False
        try:
            self.connection.start_transaction()
            cursor.execute(
                """SELECT userID FROM users WHERE email = %s AND UPPER(role) = 'READER'
                   AND account_status = 'Active' FOR UPDATE""", (email.strip(),),
            )
            user = cursor.fetchone()
            if user:
                user_id = user["userID"]
                cursor.execute(
                    """SELECT code_hash FROM password_reset_codes
                       WHERE userID = %s AND attempts < 5 AND expires_at > UTC_TIMESTAMP()
                       FOR UPDATE""", (user_id,),
                )
                challenge = cursor.fetchone()
                if challenge:
                    verified = bcrypt.checkpw(code.encode(), challenge["code_hash"].encode())
                    if verified:
                        cursor.execute("UPDATE users SET password = %s WHERE userID = %s",
                                       (self.hash_password(password), user_id))
                        cursor.execute("DELETE FROM password_reset_codes WHERE userID = %s", (user_id,))
                    else:
                        cursor.execute("UPDATE password_reset_codes SET attempts = attempts + 1 WHERE userID = %s",
                                       (user_id,))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

        if not verified:
            raise ValueError("The code is incorrect or expired. Request a new code if needed.")


def send_smtp_code(email, code):
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        raise RuntimeError("Password recovery email has not been configured.")
    user = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = email
    message["Subject"] = "Library password reset"
    message.set_content(f"Your password reset code is {code}. It expires in 10 minutes.")
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as client:
            client.starttls(context=context)
            if user:
                client.login(user, password or "")
            client.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise RuntimeError("Email could not be sent. Try again later.") from error
