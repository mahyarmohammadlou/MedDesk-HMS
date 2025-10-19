CREATE TABLE [parties] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [party_type] nvarchar(20) NOT NULL
)
GO

CREATE TABLE [persons] (
  [id] int PRIMARY KEY,
  [first_name] nvarchar(100) NOT NULL,
  [last_name] nvarchar(100) NOT NULL,
  [national_id] nvarchar(20) UNIQUE NOT NULL
)
GO

CREATE TABLE [organizations] (
  [id] int PRIMARY KEY,
  [name] nvarchar(255) NOT NULL
)
GO

CREATE TABLE [users] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [party_id] int UNIQUE NOT NULL,
  [username] nvarchar(50) UNIQUE NOT NULL,
  [password_hash] nvarchar(255) NOT NULL,
  [account_status] nvarchar(20) NOT NULL DEFAULT 'Active'
)
GO

CREATE TABLE [roles] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(50) UNIQUE NOT NULL
)
GO

CREATE TABLE [user_role_assignments] (
  [user_id] int,
  [role_id] int,
  PRIMARY KEY ([user_id], [role_id])
)
GO

CREATE TABLE [patients] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [party_id] int UNIQUE NOT NULL
)
GO

CREATE TABLE [employees] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [party_id] int UNIQUE NOT NULL
)
GO

CREATE TABLE [specializations] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(100) UNIQUE NOT NULL
)
GO

CREATE TABLE [professional_profiles] (
  [employee_id] int,
  [specialization_id] int,
  [license_number] nvarchar(50) UNIQUE NOT NULL,
  PRIMARY KEY ([employee_id], [specialization_id])
)
GO

CREATE TABLE [appointments] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [doctor_id] int NOT NULL,
  [appointment_at] datetime NOT NULL,
  [status] nvarchar(20) NOT NULL
)
GO

CREATE TABLE [medical_records] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [appointment_id] int,
  [diagnosis] nvarchar(max) NOT NULL,
  [treatment_plan] nvarchar(max),
  [created_by_user_id] int NOT NULL,
  [created_at] datetime DEFAULT (getdate())
)
GO

CREATE TABLE [lab_tests] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [test_type] nvarchar(100) NOT NULL,
  [result] nvarchar(max),
  [ordered_by_doctor_id] int NOT NULL
)
GO

CREATE TABLE [medicines] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(100) NOT NULL
)
GO

CREATE TABLE [medicine_batches] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [medicine_id] int NOT NULL,
  [batch_number] nvarchar(100) UNIQUE NOT NULL,
  [expiration_date] date NOT NULL,
  [quantity_on_hand] int NOT NULL DEFAULT (0)
)
GO

CREATE TABLE [inventory_movements] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [batch_id] int NOT NULL,
  [quantity_change] int NOT NULL,
  [movement_type] nvarchar(20) NOT NULL,
  [created_by_user_id] int NOT NULL
)
GO

CREATE TABLE [prescriptions] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [doctor_id] int NOT NULL,
  [medicine_id] int NOT NULL,
  [dosage_amount] decimal(10,2) NOT NULL,
  [dosage_unit] nvarchar(20) NOT NULL,
  [frequency_type] nvarchar(20),
  [frequency_value] int,
  [duration_unit] nvarchar(20),
  [duration_value] int,
  [instructions] nvarchar(max),
  [created_at] datetime DEFAULT (getdate())
)
GO

CREATE TABLE [invoices] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [invoice_date] date NOT NULL,
  [status] nvarchar(20) NOT NULL DEFAULT 'Unpaid'
)
GO

CREATE TABLE [invoice_line_items] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [invoice_id] int NOT NULL,
  [description] nvarchar(255) NOT NULL,
  [amount] decimal(18,2) NOT NULL,
  [source_service_type] nvarchar(50),
  [source_service_id] int
)
GO

CREATE TABLE [rooms] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [room_number] nvarchar(20) UNIQUE NOT NULL
)
GO

CREATE TABLE [room_assignments] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [patient_id] int NOT NULL,
  [room_id] int NOT NULL,
  [start_at] datetime NOT NULL,
  [end_at] datetime
)
GO

CREATE TABLE [audit_logs] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [user_id] int NOT NULL,
  [action] nvarchar(255) NOT NULL,
  [table_name] nvarchar(100),
  [record_id] int,
  [created_at] datetime DEFAULT (getdate())
)
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'REQUIRED: CHECK constraint (''PERSON'', ''ORGANIZATION'')',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'parties',
@level2type = N'Column', @level2name = 'party_type';
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = 'Consider nvarchar(4000) for performance unless unlimited text is a hard requirement.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'medical_records',
@level2type = N'Column', @level2name = 'diagnosis';
GO

EXEC sp_addextendedproperty
@name = N'Table_Description',
@value = 'NON-NEGOTIABLE REQUIREMENT: A DB-level Trigger (SQL Server) or Exclusion Constraint (PostgreSQL) is REQUIRED to prevent time-range overlaps for the same room_id.',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'room_assignments';
GO

ALTER TABLE [persons] ADD FOREIGN KEY ([id]) REFERENCES [parties] ([id])
GO

ALTER TABLE [organizations] ADD FOREIGN KEY ([id]) REFERENCES [parties] ([id])
GO

ALTER TABLE [users] ADD FOREIGN KEY ([party_id]) REFERENCES [parties] ([id])
GO

ALTER TABLE [user_role_assignments] ADD FOREIGN KEY ([user_id]) REFERENCES [users] ([id])
GO

ALTER TABLE [user_role_assignments] ADD FOREIGN KEY ([role_id]) REFERENCES [roles] ([id])
GO

ALTER TABLE [patients] ADD FOREIGN KEY ([party_id]) REFERENCES [parties] ([id])
GO

ALTER TABLE [employees] ADD FOREIGN KEY ([party_id]) REFERENCES [parties] ([id])
GO

ALTER TABLE [professional_profiles] ADD FOREIGN KEY ([employee_id]) REFERENCES [employees] ([id])
GO

ALTER TABLE [professional_profiles] ADD FOREIGN KEY ([specialization_id]) REFERENCES [specializations] ([id])
GO

ALTER TABLE [appointments] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [appointments] ADD FOREIGN KEY ([doctor_id]) REFERENCES [employees] ([id])
GO

ALTER TABLE [medical_records] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [medical_records] ADD FOREIGN KEY ([appointment_id]) REFERENCES [appointments] ([id])
GO

ALTER TABLE [medical_records] ADD FOREIGN KEY ([created_by_user_id]) REFERENCES [users] ([id])
GO

ALTER TABLE [lab_tests] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [lab_tests] ADD FOREIGN KEY ([ordered_by_doctor_id]) REFERENCES [employees] ([id])
GO

ALTER TABLE [medicine_batches] ADD FOREIGN KEY ([medicine_id]) REFERENCES [medicines] ([id])
GO

ALTER TABLE [inventory_movements] ADD FOREIGN KEY ([batch_id]) REFERENCES [medicine_batches] ([id])
GO

ALTER TABLE [inventory_movements] ADD FOREIGN KEY ([created_by_user_id]) REFERENCES [users] ([id])
GO

ALTER TABLE [prescriptions] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [prescriptions] ADD FOREIGN KEY ([doctor_id]) REFERENCES [employees] ([id])
GO

ALTER TABLE [prescriptions] ADD FOREIGN KEY ([medicine_id]) REFERENCES [medicines] ([id])
GO

ALTER TABLE [invoices] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [invoice_line_items] ADD FOREIGN KEY ([invoice_id]) REFERENCES [invoices] ([id])
GO

ALTER TABLE [room_assignments] ADD FOREIGN KEY ([patient_id]) REFERENCES [patients] ([id])
GO

ALTER TABLE [room_assignments] ADD FOREIGN KEY ([room_id]) REFERENCES [rooms] ([id])
GO

ALTER TABLE [audit_logs] ADD FOREIGN KEY ([user_id]) REFERENCES [users] ([id])
GO
