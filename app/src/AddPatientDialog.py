import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QDateEdit, QMessageBox
from DB import insert_patient  # uses your 3-step insert (parties/persons/patients)

class AddPatientDialog(QDialog):
    def __init__(self):
        super().__init__()
        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "add_patient_dialog.ui"))
        uic.loadUi(ui_path, self)

        # Find widgets by objectName (Designer must match these names)
        self.btnSubmit = self.findChild(QPushButton,  "btnSubmit")
        self.btnCancel = self.findChild(QPushButton,  "btnCancel")
        self.lineEditFirstName = self.findChild(QLineEdit,    "lineEditFirstname")
        self.lineEditLastName = self.findChild(QLineEdit,    "lineEditLastname")
        self.lineEditNationalID  = self.findChild(QLineEdit,    "lineEditID")
        self.dateEditBirth = self.findChild(QDateEdit,    "dateEditBirth")
        self.comboGender = self.findChild(QComboBox,    "comboGender")
        self.lineEditPhone = self.findChild(QLineEdit,    "lineEditPhone")
        self.plainTextAddress = self.findChild(QPlainTextEdit, "plainTextAddress")



        self.btnSubmit.clicked.connect(self._on_submit)
        self.btnCancel.clicked.connect(self.reject)

        # calendar popup for better UX
        if self.dateEditBirth:
            self.dateEditBirth.setCalendarPopup(True)

    def _validate(self) -> bool:
        """Basic validation before hitting DB."""
        fn = (self.lineEditFirstName.text() if self.lineEditFirstName else "").strip()
        ln = (self.lineEditLastName.text() if self.lineEditLastName else "").strip()
        nid = (self.lineEditNationalID.text() if self.lineEditNationalID else "").strip()

        if not fn or not ln or not nid:
            QMessageBox.warning(self, "Validation", "First name, Last name and National ID are required.")
            return False

        # Simple phone/national id checks can be added as needed
        return True

    def _on_submit(self):
        """Collect form values, insert into DB, and close with Accepted."""
        if not self._validate():
            return

        data = {
            "FirstName": self.lineEditFirstName.text().strip(),
            "LastName": self.lineEditLastName.text().strip(),
            "NationalID": self.lineEditNationalID.text().strip(),
            "BirthDate": self.dateEditBirth.date().toPyDate() if self.dateEditBirth else None,
            "Gender": self.comboGender.currentText().strip() if self.comboGender else "",
            "Phone": self.lineEditPhone.text().strip() if self.lineEditPhone else "",
            "Address": self.plainTextAddress.toPlainText().strip() if self.plainTextAddress else "",
        }

        try:
            new_id = insert_patient(data)   # returns patient_id
            QMessageBox.information(self, "Success", f"Patient added (ID={new_id}).")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))
