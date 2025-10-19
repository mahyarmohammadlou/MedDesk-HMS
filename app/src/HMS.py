import sys
import os
from datetime import datetime, timedelta
from Login import LoginDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QMessageBox, QDialog, QHeaderView
)

from DB import (
    list_patients,  # returns [(PatientID, first_name, last_name, national_id), ...]
    get_patient_by_id,  # returns dict for one patient
    insert_patient,  # inserts party/person/patient and returns new patient_id
    update_patient,  # updates persons data by patient_id
    insert_appointment  # inserts an appointment
)
from AddPatientDialog import AddPatientDialog


class MainWindow(QMainWindow):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user  # keep the logged-in user
        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "HMS.ui"))
        uic.loadUi(ui_path, self)

        # Add widget
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.page_5 = self.findChild(QWidget, "page_5")
        self.lineEditSearch = self.findChild(QLineEdit, "lineEditSearch")
        self.btnSearch = self.findChild(QPushButton, "btnSearch")
        self.btnPatients = self.findChild(QPushButton, "btnPatients")
        self.btnAddPatient = self.findChild(QPushButton, "btnAddPatient")
        self.btnView = self.findChild(QPushButton, "btnView")
        self.btnEdit = self.findChild(QPushButton, "btnEdit")
        self.btnReserve = self.findChild(QPushButton, "btnReserve")
        self.tablePatients = self.findChild(QTableWidget, "tablePatients")

        # Connect btn
        self.btnPatients.clicked.connect(self.go_to_patients_page)
        self.btnAddPatient.clicked.connect(self.open_add_patient_dialog)
        # Enable/disable action buttons based on selection
        self.tablePatients.itemSelectionChanged.connect(self._toggle_actions)
        # Double-click to open View
        self.tablePatients.itemDoubleClicked.connect(lambda *_: self.view_patient())
        self.btnView.clicked.connect(self.view_patient)
        self.btnEdit.clicked.connect(self.edit_patient)
        self.btnReserve.clicked.connect(self.reserve_visit)
        self.btnSearch.clicked.connect(self.search_patients)

        # Initially, action buttons are disabled (until a row is selected)
        for b in (self.btnView, self.btnEdit, self.btnReserve):
            if b:
                b.setEnabled(False)

        # Start app with that page
        self.stackedWidget.setCurrentIndex(0)
        # Initial data load from DB
        self.load_patients_from_db()

    # Navigation
    def go_to_patients_page(self):
        """Show the patient page using the widget reference (safer than hard index)."""
        if self.stackedWidget and self.page_5:
            self.stackedWidget.setCurrentWidget(self.page_5)
        else:
            QMessageBox.warning(self, "Navigation", "stackedWidget or page_5 not found.")

    # Helpers for table selection

    def _selected_patient_id(self):
        """Return currently selected patient ID from the table (assumes col 0 = ID)."""
        if not self.tablePatients:
            return None
        sel = self.tablePatients.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        it = self.tablePatients.item(row, 0)
        return it.text() if it else None

    def _toggle_actions(self):
        """Enable/disable action buttons based on whether a row is selected."""
        has = self._selected_patient_id() is not None
        for b in (self.btnView, self.btnEdit, self.btnReserve):
            if b:
                b.setEnabled(has)

    # Data loading / searching
    def load_patients_from_db(self):
        """Fetch patients from DB and populate the table."""
        if not self.tablePatients:
            return

        try:
            rows = list_patients()  # [(PatientID, first_name, last_name, national_id), ...]
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to load patients:\n{e}")
            return

        self.tablePatients.clear()
        self.tablePatients.setColumnCount(4)
        self.tablePatients.setHorizontalHeaderLabels(["ID", "First Name", "Last Name", "National ID"])
        self.tablePatients.setRowCount(len(rows))

        for r, (pid, fn, ln, nid) in enumerate(rows):
            self.tablePatients.setItem(r, 0, QTableWidgetItem(str(pid)))
            self.tablePatients.setItem(r, 1, QTableWidgetItem(fn or ""))
            self.tablePatients.setItem(r, 2, QTableWidgetItem(ln or ""))
            self.tablePatients.setItem(r, 3, QTableWidgetItem(nid or ""))

        # After reload, disable actions until use selects a row again
        self._toggle_actions()

        # Table style
        header = self.tablePatients.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        for row in range(self.tablePatients.rowCount()):
            for col in range(self.tablePatients.columnCount()):
                item = self.tablePatients.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

    def search_patients(self):
        """Very basic in-memory filter on the already loaded table (optional).
        For large datasets, implement server-side filtering in DB instead."""
        if not (self.tablePatients and self.lineEditSearch):
            return

        q = (self.lineEditSearch.text() or "").strip().lower()
        # Simple row-visibility filter on table items
        for row in range(self.tablePatients.rowCount()):
            # Concatenate all visible columns for a quick contains check
            row_text = " ".join(
                (self.tablePatients.item(row, c).text() if self.tablePatients.item(row, c) else "")
                for c in range(self.tablePatients.columnCount())
            ).lower()
            self.tablePatients.setRowHidden(row, q not in row_text)

    def open_add_patient_dialog(self):
        dlg = AddPatientDialog()
        if dlg.exec_() == QDialog.Accepted:
            self.load_patients_from_db()  # refresh table from DB
            self.go_to_patients_page()  # optional: ensure patients page is visible

    def view_patient(self):
        """Show a simple read-only summary for the selected patient."""
        pid = self._selected_patient_id()
        if not pid:
            return
        try:
            p = get_patient_by_id(int(pid))
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to fetch patient:\n{e}")
            return
        if not p:
            QMessageBox.warning(self, "Not Found", "Patient not found.")
            return

        # Basic info dialog (you can replace with a custom view dialog)
        msg = (
            f"ID: {p['PatientID']}\n"
            f"Name: {p['FirstName']} {p['LastName']}\n"
            f"NationalID: {p['NationalID']}\n"
            f"DOB: {p['BirthDate']}\n"
            f"Gender: {p['Gender']}\n"
            f"Phone: {p['Phone']}\n"
            f"Address: {p['Address']}"
        )
        QMessageBox.information(self, "Patient", msg)

    def edit_patient(self):
        """Open AddPatientDialog as an edit form, then update DB."""
        pid = self._selected_patient_id()
        if not pid:
            return

        try:
            p = get_patient_by_id(int(pid))
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to fetch patient:\n{e}")
            return
        if not p:
            QMessageBox.warning(self, "Not Found", "Patient not found.")
            return

        # Open dialog and pre-fill fields
        dlg = AddPatientDialog()
        dlg.setWindowTitle("Edit Patient")
        dlg.lineEditFirstName.setText(p["FirstName"] or "")
        dlg.lineEditLastName.setText(p["LastName"] or "")
        dlg.lineEditNationalID.setText(p["NationalID"] or "")
        if p["BirthDate"]:
            dlg.dateEditBirth.setDate(dlg.dateEditBirth.date().fromString(str(p["BirthDate"]), "yyyy-MM-dd"))
        # Set gender
        idx = dlg.comboGender.findText((p["Gender"] or "").strip(), Qt.MatchFixedString)
        if idx >= 0:
            dlg.comboGender.setCurrentIndex(idx)
        dlg.lineEditPhone.setText(p["Phone"] or "")
        dlg.plainTextAddress.setPlainText(p["Address"] or "")

        if dlg.exec_() == QDialog.Accepted:
            try:
                data = {
                    "FirstName": dlg.lineEditFirstName.text().strip(),
                    "LastName": dlg.lineEditLastName.text().strip(),
                    "NationalID": dlg.lineEditNationalID.text().strip(),
                    "BirthDate": dlg.dateEditBirth.date().toPyDate(),
                    "Gender": dlg.comboGender.currentText().strip(),
                    "Phone": dlg.lineEditPhone.text().strip(),
                    "Address": dlg.plainTextAddress.toPlainText().strip(),
                }
                ok = update_patient(int(pid), data)
                if ok:
                    QMessageBox.information(self, "Updated", "Patient updated successfully.")
                    self.load_patients_from_db()
                else:
                    QMessageBox.warning(self, "No Change", "No rows were updated.")
            except Exception as e:
                QMessageBox.critical(self, "DB Error", f"Failed to update patient:\n{e}")

    def reserve_visit(self):
        """Quick reservation example (replace with a real reservation dialog)."""
        pid = self._selected_patient_id()
        if not pid:
            return

        # Demo: reserve an appointment 3 days from now with doctor_id=1
        when_dt = datetime.now() + timedelta(days=3)
        try:
            ok = insert_appointment(int(pid), doctor_id=1, when_dt=when_dt, status="Scheduled")
            if ok:
                QMessageBox.information(self, "Reserved", "Appointment reserved.")
            else:
                QMessageBox.warning(self, "Not Reserved", "No reservation was made.")
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to reserve appointment:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1) Show login first
    login = LoginDialog()
    if login.exec_() != LoginDialog.Accepted:
        sys.exit(0)

    # 2) Open main window with current user
    user = login.auth_user()
    win = MainWindow(current_user=user)
    win.show()

    sys.exit(app.exec_())
