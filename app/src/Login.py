import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton, QMessageBox
)
from DB import verify_user_password_plain, get_user_by_username, create_user_plain, get_connection


class LoginDialog(QDialog):
    """Simple login dialog using findChild and plain password check (TEST)."""

    def __init__(self):
        super().__init__()
        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "login.ui"))
        uic.loadUi(ui_path, self)

        # Add widget
        self.txtUsername: QLineEdit = self.findChild(QLineEdit, "txtUsername")
        self.txtPassword: QLineEdit = self.findChild(QLineEdit, "txtPassword")
        self.btnLogin: QPushButton = self.findChild(QPushButton, "btnLogin")

        # Connect btn

        self.txtPassword.setEchoMode(QLineEdit.Password)
        self.txtPassword.returnPressed.connect(self._on_login)

        self.btnLogin.clicked.connect(self._on_login)

        # seed a test user if table is empty
        self._ensure_test_user()

        self._auth_user = None

    def _ensure_test_user(self):
        """Create a test user 'admin'/'admin123' if users table is empty."""
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT TOP(1) 1 FROM dbo.users")
                has_any = cur.fetchone() is not None
            if not has_any and not get_user_by_username("admin"):
                create_user_plain("admin", "admin123", party_id=None, status="Active")
        except Exception:
            # If something fails, just skip seeding silently.
            pass

    def _on_login(self):
        username = (self.txtUsername.text() if self.txtUsername else "").strip()
        password = (self.txtPassword.text() if self.txtPassword else "").strip()
        if not username or not password:
            QMessageBox.warning(self, "Login", "Username and password are required.")
            return
        ok, user, msg = verify_user_password_plain(username, password)
        if not ok:
            QMessageBox.warning(self, "Login", msg)
            return
        self._auth_user = user
        self.accept()

    def auth_user(self):
        """Return user dict after success."""
        return self._auth_user


# run alone for quick test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = LoginDialog()
    if dlg.exec_() == QDialog.Accepted:
        print("Logged in as:", dlg.auth_user()["username"])
    sys.exit(0)
