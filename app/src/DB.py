import pyodbc
from contextlib import contextmanager

CONN_STR = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=.;"
    "Database=HMS_DB;"
    "Trusted_Connection=yes;"
)

# ---------- connections ----------
def get_connection():
    """Return a new DB connection (caller must close/commit)."""
    return pyodbc.connect(CONN_STR)

@contextmanager
def conn_cursor():
    conn = pyodbc.connect(CONN_STR)
    try:
        yield conn, conn.cursor()
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()

# ---------- patients ----------
def list_patients():
    """Returns: [(PatientID, FirstName, LastName, NationalID), ...]"""
    sql = """
    SELECT p.id AS PatientID
         , pr.first_name
         , pr.last_name
         , pr.national_id
    FROM dbo.patients AS p
    JOIN dbo.parties  AS pa ON pa.id = p.party_id
    JOIN dbo.persons  AS pr ON pr.id = pa.id
    ORDER BY p.id DESC;
    """
    with conn_cursor() as (_, cur):
        cur.execute(sql)
        rows = cur.fetchall()
        return [(r.PatientID, r.first_name, r.last_name, r.national_id) for r in rows]

def get_patient_by_id(patient_id: int):
    sql = """
    SELECT p.id AS PatientID
         , pr.first_name, pr.last_name, pr.national_id
         , pr.address, pr.gender, pr.date_of_birth, pr.phone_number
    FROM dbo.patients AS p
    JOIN dbo.parties  AS pa ON pa.id = p.party_id
    JOIN dbo.persons  AS pr ON pr.id = pa.id
    WHERE p.id = ?;
    """
    with conn_cursor() as (_, cur):
        cur.execute(sql, (patient_id,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "PatientID": r.PatientID,
            "FirstName": r.first_name,
            "LastName": r.last_name,
            "NationalID": r.national_id,
            "Address": (r.address or "").strip(),
            "Gender": (r.gender or "").strip(),
            "BirthDate": r.date_of_birth,
            "Phone": (r.phone_number or "").strip(),
        }

def insert_patient(data: dict) -> int:
    """
    data: { FirstName, LastName, NationalID, BirthDate(date), Gender, Phone, Address }
    return: patient_id
    """
    with conn_cursor() as (conn, cur):
        # 1) parties
        cur.execute("INSERT INTO dbo.parties(party_type) VALUES ('PERSON');")
        cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT);")
        party_id = cur.fetchone()[0]

        # 2) persons (id = party_id)
        cur.execute("""
            INSERT INTO dbo.persons
            (id, first_name, last_name, national_id, address, gender, date_of_birth, phone_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            party_id,
            data.get("FirstName"), data.get("LastName"), data.get("NationalID"),
            data.get("Address") or "",
            data.get("Gender") or "",
            data.get("BirthDate"),
            data.get("Phone") or "",
        ))

        # 3) patients
        cur.execute("INSERT INTO dbo.patients (party_id) VALUES (?);", (party_id,))
        cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT);")
        patient_id = cur.fetchone()[0]
        return patient_id

def update_patient(patient_id: int, data: dict) -> bool:
    """Update persons by patient_id."""
    with conn_cursor() as (_, cur):
        cur.execute("SELECT party_id FROM dbo.patients WHERE id = ?;", (patient_id,))
        row = cur.fetchone()
        if not row:
            return False
        party_id = row.party_id

    with conn_cursor() as (_, cur):
        cur.execute("""
            UPDATE dbo.persons
               SET first_name   = ?,
                   last_name    = ?,
                   national_id  = ?,
                   address      = ?,
                   gender       = ?,
                   date_of_birth= ?,
                   phone_number = ?
             WHERE id = ?;
        """, (
            data.get("FirstName"), data.get("LastName"), data.get("NationalID"),
            data.get("Address") or "", data.get("Gender") or "",
            data.get("BirthDate"), data.get("Phone") or "", party_id
        ))
        return cur.rowcount > 0

def insert_appointment(patient_id: int, doctor_id: int, when_dt, status="Scheduled") -> bool:
    with conn_cursor() as (_, cur):
        cur.execute("""
            INSERT INTO dbo.appointments (patient_id, doctor_id, appointment_at, status)
            VALUES (?, ?, ?, ?)
        """, (patient_id, doctor_id, when_dt, status))
        return True

# ---------- users (plain auth for testing) ----------
def get_user_by_username(username: str):
    """Fetch one user by username. Returns dict or None."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, password_hash, account_status, party_id
            FROM dbo.users
            WHERE username = ?
        """, (username,))
        r = cur.fetchone()
        if not r:
            return None
        return {
            "id": r.id,
            "username": r.username,
            "password_hash": r.password_hash,
            "status": r.account_status,
            "party_id": r.party_id
        }

def create_user_plain(username: str, password: str, party_id: int = None, status: str = "Active"):
    """Create a user with plain password (TEST ONLY)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO dbo.users (party_id, username, password_hash, account_status)
            VALUES (?, ?, ?, ?)
        """, (party_id, username, password, status))
        conn.commit()

def verify_user_password_plain(username: str, password: str):
    """
    Plain check: compares password directly with `password_hash`.
    Returns (ok: bool, user: dict|None, message: str).
    """
    user = get_user_by_username(username)
    if not user:
        return False, None, "User not found."
    if (user["status"] or "").strip().lower() != "active":
        return False, None, "Account is not active."
    if (user["password_hash"] or "") != password:
        return False, None, "Invalid username or password."
    return True, user, "OK"
