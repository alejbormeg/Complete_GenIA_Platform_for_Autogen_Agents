-- Demo database for IberConsulting fiscal & labor advisory platform
-- Compatible with NL->SQL queries provided

DROP SCHEMA IF EXISTS fiscal_consulting_demo CASCADE;
CREATE SCHEMA fiscal_consulting_demo;
SET search_path TO fiscal_consulting_demo;

-- Enumerated types for controlled vocabularies
CREATE TYPE client_category AS ENUM ('corporate', 'sme', 'individual', 'public');
CREATE TYPE engagement_status AS ENUM ('planning', 'active', 'on_hold', 'completed', 'cancelled');
CREATE TYPE case_status AS ENUM ('scheduled', 'in_progress', 'waiting_client', 'submitted', 'closed');
CREATE TYPE case_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE invoice_status AS ENUM ('draft', 'issued', 'paid', 'overdue', 'void');
CREATE TYPE statement_kind AS ENUM ('monthly', 'quarterly', 'annual');
CREATE TYPE tax_kind AS ENUM ('CIT', 'VAT', 'IRPF', 'SOCIAL_SECURITY', 'WITHHOLDING');

-- Master data
CREATE TABLE offices (
    office_id      SERIAL PRIMARY KEY,
    id             INTEGER GENERATED ALWAYS AS (office_id) STORED,
    name           TEXT NOT NULL,
    region         TEXT NOT NULL,
    city           TEXT NOT NULL,
    address        TEXT NOT NULL,
    phone          TEXT,
    email          TEXT UNIQUE,
    opened_date    DATE,
    headcount_cap  INTEGER DEFAULT 50,
    CONSTRAINT chk_headcount_cap CHECK (headcount_cap > 0)
);

CREATE TABLE service_lines (
    service_line_id SERIAL PRIMARY KEY,
    id              INTEGER GENERATED ALWAYS AS (service_line_id) STORED,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,
    description     TEXT
);

CREATE TABLE employees (
    employee_id     SERIAL PRIMARY KEY,
    id              INTEGER GENERATED ALWAYS AS (employee_id) STORED,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    phone           TEXT,
    role            TEXT NOT NULL,
    grade           TEXT NOT NULL,
    is_manager      BOOLEAN DEFAULT FALSE,
    hire_date       DATE NOT NULL,
    office_id       INTEGER REFERENCES offices(office_id) ON DELETE SET NULL,
    service_line_id INTEGER REFERENCES service_lines(service_line_id) ON DELETE SET NULL,
    salary_band     NUMERIC(10,2)
);

CREATE TABLE clients (
    client_id            SERIAL PRIMARY KEY,
    id                   INTEGER GENERATED ALWAYS AS (client_id) STORED,
    legal_name           TEXT NOT NULL,
    trade_name           TEXT,
    name                 TEXT GENERATED ALWAYS AS (COALESCE(trade_name, legal_name)) STORED,
    tax_id               TEXT UNIQUE NOT NULL,
    category             client_category NOT NULL,
    industry             TEXT,
    headquarters_city    TEXT,
    headquarters_region  TEXT,
    contact_name         TEXT,
    contact_email        TEXT,
    contact_phone        TEXT,
    onboarding_date      DATE NOT NULL,
    account_manager_id   INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    risk_rating          TEXT DEFAULT 'Medium',
    billing_currency     TEXT DEFAULT 'EUR'
);

CREATE TABLE client_offices (
    client_office_id SERIAL PRIMARY KEY,
    client_id        INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    site_name        TEXT NOT NULL,
    city             TEXT NOT NULL,
    address          TEXT NOT NULL,
    employees_count  INTEGER,
    lead_contact     TEXT,
    lead_email       TEXT
);

CREATE TABLE engagements (
    engagement_id        SERIAL PRIMARY KEY,
    id                   INTEGER GENERATED ALWAYS AS (engagement_id) STORED,
    client_id            INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    service_line_id      INTEGER NOT NULL REFERENCES service_lines(service_line_id) ON DELETE RESTRICT,
    lead_consultant_id   INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    start_date           DATE NOT NULL,
    end_date             DATE,
    status               engagement_status NOT NULL DEFAULT 'planning',
    retainer_fee         NUMERIC(12,2),
    billing_frequency    TEXT CHECK (billing_frequency IN ('monthly', 'quarterly', 'annual', 'one-off')),
    description          TEXT,
    renewal_probability  NUMERIC(5,2) CHECK (renewal_probability BETWEEN 0 AND 100)
);

CREATE TABLE engagement_offices (
    engagement_id INTEGER REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    office_id     INTEGER REFERENCES offices(office_id) ON DELETE CASCADE,
    PRIMARY KEY (engagement_id, office_id)
);

CREATE TABLE compliance_cases (
    case_id            SERIAL PRIMARY KEY,
    id                 INTEGER GENERATED ALWAYS AS (case_id) STORED,
    engagement_id      INTEGER NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    case_code          TEXT UNIQUE NOT NULL,
    case_type          TEXT NOT NULL,
    fiscal_year        INTEGER NOT NULL,
    fiscal_period      TEXT,
    due_date           DATE,
    status             case_status NOT NULL,
    priority           case_priority NOT NULL DEFAULT 'medium',
    assigned_lead_id   INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    notes              TEXT
);

CREATE TABLE case_tasks (
    task_id        SERIAL PRIMARY KEY,
    case_id        INTEGER NOT NULL REFERENCES compliance_cases(case_id) ON DELETE CASCADE,
    task_name      TEXT NOT NULL,
    assigned_to_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    due_date       DATE,
    status         TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),
    completed_at   TIMESTAMP,
    comments       TEXT
);

CREATE TABLE documents (
    document_id   SERIAL PRIMARY KEY,
    case_id       INTEGER REFERENCES compliance_cases(case_id) ON DELETE CASCADE,
    uploaded_by   INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    doc_type      TEXT NOT NULL,
    file_name     TEXT NOT NULL,
    storage_path  TEXT NOT NULL,
    uploaded_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    is_signed     BOOLEAN DEFAULT FALSE
);

CREATE TABLE tax_returns (
    tax_return_id SERIAL PRIMARY KEY,
    client_id     INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    case_id       INTEGER REFERENCES compliance_cases(case_id) ON DELETE SET NULL,
    fiscal_year   INTEGER NOT NULL,
    tax_type      tax_kind NOT NULL,
    period        TEXT,
    amount_due    NUMERIC(12,2),
    amount_paid   NUMERIC(12,2),
    filing_date   DATE,
    status        TEXT CHECK (status IN ('draft', 'filed', 'accepted', 'rejected'))
);

CREATE TABLE payroll_reports (
    payroll_report_id SERIAL PRIMARY KEY,
    client_id         INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    engagement_id     INTEGER REFERENCES engagements(engagement_id) ON DELETE SET NULL,
    reporting_month   DATE NOT NULL,
    employees_processed INTEGER NOT NULL,
    total_gross_pay   NUMERIC(12,2) NOT NULL,
    social_security_contrib NUMERIC(12,2) NOT NULL,
    submitted_by_id   INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    submission_date   DATE NOT NULL
);

CREATE TABLE financial_statements (
    statement_id   SERIAL PRIMARY KEY,
    client_id      INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    engagement_id  INTEGER REFERENCES engagements(engagement_id) ON DELETE SET NULL,
    statement_type statement_kind NOT NULL,
    period_start   DATE NOT NULL,
    period_end     DATE NOT NULL,
    revenue        NUMERIC(14,2),
    expenses       NUMERIC(14,2),
    payroll_costs  NUMERIC(14,2),
    tax_provision  NUMERIC(14,2),
    prepared_by_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    approved_by_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    approval_date  DATE
);

CREATE TABLE invoices (
    invoice_id      SERIAL PRIMARY KEY,
    id              INTEGER GENERATED ALWAYS AS (invoice_id) STORED,
    engagement_id   INTEGER NOT NULL REFERENCES engagements(engagement_id) ON DELETE CASCADE,
    issued_by_id    INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    invoice_number  TEXT UNIQUE NOT NULL,
    issue_date      DATE NOT NULL,
    issued_at       DATE GENERATED ALWAYS AS (issue_date) STORED,
    due_date        DATE NOT NULL,
    amount_total    NUMERIC(12,2) NOT NULL,
    status          invoice_status NOT NULL,
    notes           TEXT
);

CREATE TABLE invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    id              INTEGER GENERATED ALWAYS AS (invoice_item_id) STORED,
    invoice_id      INTEGER NOT NULL REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    item_description TEXT NOT NULL,
    quantity        INTEGER NOT NULL DEFAULT 1,
    unit_price      NUMERIC(12,2) NOT NULL,
    line_total      NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- Helpful indexes for reporting flows
CREATE INDEX idx_employees_office ON employees(office_id);
CREATE INDEX idx_clients_account_manager ON clients(account_manager_id);
CREATE INDEX idx_cases_due_date ON compliance_cases(due_date);
CREATE INDEX idx_payroll_reports_month ON payroll_reports(reporting_month);
CREATE INDEX idx_financial_statements_period ON financial_statements(period_start, period_end);

-- Seed data ---------------------------------------------------------------
INSERT INTO offices (name, region, city, address, phone, email, opened_date, headcount_cap) VALUES
    ('Madrid', 'Centro', 'Madrid', 'Paseo de la Castellana 120', '+34 91 555 0101', 'madrid@iberconsulting.es', '2005-03-01', 120),
    ('Oficina Barcelona', 'Cataluña', 'Barcelona', 'Avinguda Diagonal 640', '+34 93 555 0145', 'barcelona@iberconsulting.es', '2010-06-15', 80),
    ('Oficina Valencia', 'Levante', 'Valencia', 'Carrer de Colón 34', '+34 96 555 0890', 'valencia@iberconsulting.es', '2015-02-20', 60),
    ('Oficina Sevilla', 'Andalucía', 'Sevilla', 'Avenida de la Palmera 25', '+34 95 555 0670', 'sevilla@iberconsulting.es', '2018-09-03', 50);

INSERT INTO service_lines (name, category, description) VALUES
    ('Fiscal',   'Fiscal',   'Asesoría Fiscal Integral'),
    ('Laboral',  'Laboral',  'Consultoría Laboral y Seguridad Social'),
    ('Contable', 'Contable', 'Contabilidad y Reporting'),
    ('Legal',    'Legal',    'Gobierno Corporativo y Riesgos');

INSERT INTO employees (full_name, email, phone, role, grade, is_manager, hire_date, office_id, service_line_id, salary_band) VALUES
    ('Laura Martín', 'laura.martin@iberconsulting.es', '+34 600 111 201', 'Socia Fiscal', 'Partner', TRUE, '2010-05-15', 1, 1, 95000.00),
    ('Javier López', 'javier.lopez@iberconsulting.es', '+34 600 111 202', 'Director Laboral', 'Director', TRUE, '2012-09-01', 1, 2, 82000.00),
    ('Anna Puig', 'anna.puig@iberconsulting.es', '+34 600 111 305', 'Consultora Senior Laboral', 'Senior', FALSE, '2017-02-10', 2, 2, 54000.00),
    ('Diego Herrera', 'diego.herrera@iberconsulting.es', '+34 600 111 410', 'Manager Contable', 'Manager', TRUE, '2016-11-28', 3, 3, 62000.00),
    ('Carmen Ruiz', 'carmen.ruiz@iberconsulting.es', '+34 600 111 512', 'Consultora Fiscal', 'Senior', FALSE, '2019-04-18', 4, 1, 52000.00),
    ('Marta Gómez', 'marta.gomez@iberconsulting.es', '+34 600 111 613', 'Analista Fiscal', 'Associate', FALSE, '2021-01-12', 1, 1, 42000.00),
    ('Sergio Vidal', 'sergio.vidal@iberconsulting.es', '+34 600 111 714', 'Especialista Nóminas', 'Associate', FALSE, '2020-03-23', 2, 2, 38000.00),
    ('Isabel Torres', 'isabel.torres@iberconsulting.es', '+34 600 111 815', 'Controller Senior', 'Senior', FALSE, '2018-07-09', 3, 3, 56000.00);

INSERT INTO clients (legal_name, trade_name, tax_id, category, industry, headquarters_city, headquarters_region, contact_name, contact_email, contact_phone, onboarding_date, account_manager_id, risk_rating, billing_currency) VALUES
    ('Tecnologías Nova S.L.', 'TechNova', 'B12345678', 'sme', 'Tecnología', 'Madrid', 'Comunidad de Madrid', 'Luis Ortega', 'luis.ortega@technova.es', '+34 91 700 9001', '2019-01-15', 1, 'Low', 'EUR'),
    ('Grupo Andaluz de Servicios S.A.', 'GASER', 'A87654321', 'corporate', 'Servicios Integrales', 'Sevilla', 'Andalucía', 'María Ángeles Robles', 'mar.robles@gaser.es', '+34 95 600 8200', '2017-09-05', 2, 'Medium', 'EUR'),
    ('Clínica Mediterránea S.L.', 'Climed', 'B99887766', 'sme', 'Sanidad Privada', 'Valencia', 'Comunidad Valenciana', 'Dr. Carlos Falcó', 'cfalco@climed.es', '+34 96 300 4500', '2020-03-21', 4, 'Low', 'EUR'),
    ('Consorcio Público Norte', 'CP Norte', 'Q1239874D', 'public', 'Administración Pública', 'Burgos', 'Castilla y León', 'Ana Belén Lora', 'ana.lora@cpnorte.es', '+34 947 550 112', '2018-11-02', 1, 'Medium', 'EUR'),
    ('Estudio Creativo Brío S.Coop.', 'Brío', 'F44556677', 'sme', 'Marketing y Diseño', 'Barcelona', 'Cataluña', 'Núria Pons', 'nuria@briocreativo.com', '+34 93 200 1122', '2022-06-17', 3, 'Medium', 'EUR');

INSERT INTO client_offices (client_id, site_name, city, address, employees_count, lead_contact, lead_email) VALUES
    (1, 'Sede Central', 'Madrid', 'Calle Alcalá 45', 120, 'Beatriz Ramos', 'beatriz.ramos@technova.es'),
    (1, 'Centro de Innovación', 'Bilbao', 'Gran Vía Don Diego López de Haro 30', 45, 'Iñigo Arriaga', 'iarriaga@technova.es'),
    (2, 'Servicios Integrales', 'Sevilla', 'Polígono La Negrilla nave 6', 200, 'Pedro Galván', 'pedro.galvan@gaser.es'),
    (2, 'Delegación Málaga', 'Málaga', 'Avenida de Andalucía 25', 75, 'Isabel Cuevas', 'isabel.cuevas@gaser.es'),
    (3, 'Hospital Privado', 'Valencia', 'Av. Blasco Ibáñez 60', 90, 'Sara Font', 'sara.font@climed.es'),
    (4, 'Sede Norte', 'Burgos', 'Plaza Mayor 1', 300, 'Julián Cascos', 'julian.cascos@cpnorte.es'),
    (5, 'Oficina Creativa', 'Barcelona', 'Carrer de la Lluna 14', 25, 'Núria Pons', 'nuria@briocreativo.com');

INSERT INTO engagements (client_id, service_line_id, lead_consultant_id, start_date, end_date, status, retainer_fee, billing_frequency, description, renewal_probability) VALUES
    (1, 1, 1, '2023-01-01', NULL, 'active', 4500.00, 'monthly', 'Cumplimiento fiscal recurrente y planificación de incentivos I+D', 85.00),
    (1, 2, 3, '2023-04-01', NULL, 'active', 2500.00, 'monthly', 'Gestión integral de nóminas y altas en Seguridad Social', 90.00),
    (2, 2, 2, '2022-07-01', '2024-06-30', 'active', 3800.00, 'monthly', 'Outsourcing laboral multi-centro y auditoría salarial', 75.00),
    (2, 4, 1, '2023-09-01', NULL, 'planning', 5200.00, 'quarterly', 'Proyecto de gobernanza y canal de denuncia', 65.00),
    (3, 3, 4, '2021-02-01', NULL, 'active', 1800.00, 'monthly', 'Reporting financiero y conciliaciones mensuales', 80.00),
    (4, 1, 6, '2022-10-01', NULL, 'on_hold', 6000.00, 'quarterly', 'Asistencia fiscal en fondos europeos', 55.00),
    (5, 1, 5, '2023-06-15', NULL, 'active', 900.00, 'monthly', 'Soporte fiscal para cooperativa creativa', 92.00);

INSERT INTO engagement_offices (engagement_id, office_id) VALUES
    (1, 1), (1, 2),
    (2, 1), (2, 2),
    (3, 1), (3, 4),
    (4, 1), (4, 4),
    (5, 3),
    (6, 1), (6, 3),
    (7, 2);

INSERT INTO compliance_cases (engagement_id, case_code, case_type, fiscal_year, fiscal_period, due_date, status, priority, assigned_lead_id, notes) VALUES
    (1, 'TN-VAT-2023Q4', 'Declaración IVA Trimestral', 2023, 'Q4', '2024-01-20', 'submitted', 'high', 6, 'Presentada con deducción por inversión tecnológica'),
    (1, 'TN-CIT-2023', 'Impuesto de Sociedades', 2023, 'Anual', '2024-07-25', 'in_progress', 'critical', 1, 'Pendiente información sobre amortizaciones aceleradas'),
    (2, 'TN-PAY-2024M01', 'Ciclo Nómina Mensual', 2024, 'Enero', '2024-02-01', 'closed', 'medium', 3, 'Proceso automatizado con incidencias resueltas'),
    (3, 'GA-AUD-2023', 'Auditoría laboral multi-centro', 2023, 'Especial', '2024-03-15', 'waiting_client', 'high', 2, 'Pendiente de documentación de delegación Málaga'),
    (5, 'CM-REP-2023Q4', 'Informe financiero trimestral', 2023, 'Q4', '2024-01-31', 'submitted', 'medium', 4, 'Estado remitido al consejo médico'),
    (7, 'BR-IVA-2023Q4', 'Declaración IVA Trimestral', 2023, 'Q4', '2024-01-20', 'submitted', 'medium', 5, 'Aplicadas exenciones por operaciones intracomunitarias'),
    (6, 'CP-FEU-2024', 'Justificación fondos europeos', 2024, 'Convocatoria FEDER', '2024-09-30', 'scheduled', 'high', 6, 'A la espera de reactivación del proyecto por parte del cliente');

INSERT INTO case_tasks (case_id, task_name, assigned_to_id, due_date, status, completed_at, comments) VALUES
    (1, 'Conciliar libros de IVA', 6, '2024-01-10', 'completed', '2024-01-09 16:30', 'Conciliación con ERP finalizada sin diferencias'),
    (1, 'Revisar facturas intracomunitarias', 1, '2024-01-12', 'completed', '2024-01-11 11:00', 'Validada aplicación del artículo 62 LIVA'),
    (2, 'Actualizar amortizaciones por I+D', 6, '2024-06-30', 'in_progress', NULL, 'Pendiente de cifras definitivas de laboratorio IA'),
    (3, 'Calcular nóminas y retenciones', 3, '2024-01-28', 'completed', '2024-01-27 18:45', 'Cerrado periodo con incidencias mínimas'),
    (4, 'Revisar convenios colectivos', 7, '2024-02-29', 'in_progress', NULL, 'Dudas sobre plus transporte en Málaga'),
    (5, 'Generar informe de ratios médicos', 4, '2024-01-12', 'completed', '2024-01-12 09:20', 'Ratios entregados al consejero delegado'),
    (6, 'Clasificar tickets gastos UE', 5, '2024-01-14', 'completed', '2024-01-14 13:15', 'Tickets cargados en gestor documental'),
    (7, 'Actualizar cronograma de hitos', 6, '2024-06-01', 'pending', NULL, 'A la espera de confirmación de fechas del ministerio');

INSERT INTO documents (case_id, uploaded_by, doc_type, file_name, storage_path, uploaded_at, is_signed) VALUES
    (1, 6, 'Libro registro IVA', 'TN_Q4_2023_libro_iva.xlsx', '/files/technova/iva/2023Q4/libro.xlsx', '2024-01-08 09:42', TRUE),
    (2, 1, 'Modelo 200 borrador', 'TN_2023_modelo200.pdf', '/files/technova/is/2023/modelo200.pdf', '2024-05-10 12:05', FALSE),
    (3, 3, 'Resumen nómina', 'TN_enero2024_nominas.zip', '/files/technova/payroll/2024-01.zip', '2024-01-27 19:00', TRUE),
    (4, 2, 'Checklist auditoría', 'GASER_aud_checklist.xlsx', '/files/gaser/auditorias/2023/checklist.xlsx', '2024-02-05 10:15', FALSE),
    (5, 4, 'Informe financiero', 'Climed_Q4_2023.pdf', '/files/climed/reporting/Q4_2023.pdf', '2024-01-11 17:50', TRUE),
    (6, 5, 'Justificante IVA', 'Brio_iva_modelo303.pdf', '/files/brio/iva/2023Q4_modelo303.pdf', '2024-01-15 08:20', TRUE);

INSERT INTO tax_returns (client_id, case_id, fiscal_year, tax_type, period, amount_due, amount_paid, filing_date, status) VALUES
    (1, 1, 2023, 'VAT', 'Q4', 24500.34, 24500.34, '2024-01-18', 'accepted'),
    (1, 2, 2023, 'CIT', 'Anual', 132000.00, 0.00, NULL, 'draft'),
    (5, 6, 2023, 'VAT', 'Q4', 4850.00, 4850.00, '2024-01-17', 'accepted'),
    (4, NULL, 2023, 'SOCIAL_SECURITY', 'Anual', 76000.00, 76000.00, '2024-02-05', 'filed');

INSERT INTO payroll_reports (client_id, engagement_id, reporting_month, employees_processed, total_gross_pay, social_security_contrib, submitted_by_id, submission_date) VALUES
    (1, 2, '2024-01-01', 165, 382500.75, 118575.23, 3, '2024-01-30'),
    (1, 2, '2024-02-01', 168, 388120.10, 120317.24, 7, '2024-02-28'),
    (2, 3, '2024-01-01', 245, 512840.60, 160020.88, 2, '2024-01-29'),
    (3, 5, '2024-01-01', 92, 198450.30, 61919.59, 4, '2024-01-27');

INSERT INTO financial_statements (client_id, engagement_id, statement_type, period_start, period_end, revenue, expenses, payroll_costs, tax_provision, prepared_by_id, approved_by_id, approval_date) VALUES
    (1, 1, 'quarterly', '2023-10-01', '2023-12-31', 2150000.00, 1760000.00, 485000.00, 162000.00, 4, 1, '2024-01-12'),
    (3, 5, 'quarterly', '2023-10-01', '2023-12-31', 1485000.00, 1125000.00, 315000.00, 84500.00, 4, 1, '2024-01-10'),
    (2, 3, 'annual', '2023-01-01', '2023-12-31', 6850000.00, 5620000.00, 1890000.00, 354000.00, 8, 2, '2024-02-20');

-- Facturas originales (enero-feb 2024)
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    (1, 1, 'INV-2024-001', '2024-01-05', '2024-01-31', 4500.00, 'paid',   'Retainer mensual enero 2024'),
    (2, 3, 'INV-2024-015', '2024-01-05', '2024-01-31', 2500.00, 'paid',   'Servicio nómina enero 2024'),
    (3, 2, 'INV-2024-027', '2024-02-01', '2024-02-28', 4250.00, 'issued', 'Outsourcing laboral febrero 2024'),
    (5, 4, 'INV-2024-041', '2024-01-12', '2024-02-10', 1800.00, 'overdue','Reporting financiero Q4 2023'),
    (7, 5, 'INV-2024-052', '2024-01-20', '2024-02-20', 900.00,  'paid',   'Retainer fiscal cooperativa');

INSERT INTO invoice_items (invoice_id, item_description, quantity, unit_price) VALUES
    (1, 'Retainer asesoría fiscal mes enero', 1, 4500.00),
    (2, 'Gestión nóminas enero (165 empleados)', 1, 2500.00),
    (3, 'Honorarios outsourcing laboral febrero', 1, 3800.00),
    (3, 'Bonificación ITSS Málaga', 1, 450.00),
    (4, 'Informe financiero Q4 2023', 1, 1500.00),
    (4, 'Reunión extraordinaria consejo médico', 1, 300.00),
    (5, 'Retainer fiscal mensual', 1, 900.00);

-- NUEVAS facturas 2025 para que el TOP-5 últimos 12 meses devuelva datos (hoy 2025-10-10)
-- Nota: Asumiendo invoice_id autoincremental, estas serán 6..10
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    (1, 1, 'INV-2025-101', '2025-01-15', '2025-02-15', 4700.00, 'paid',   'Retainer enero 2025'),
    (2, 3, 'INV-2025-115', '2025-03-01', '2025-03-31', 2600.00, 'paid',   'Nóminas marzo 2025'),
    (3, 2, 'INV-2025-203', '2025-06-10', '2025-07-10', 4250.00, 'issued', 'Outsourcing junio 2025'),
    (5, 4, 'INV-2025-305', '2025-09-20', '2025-10-20', 2000.00, 'paid',   'Reporting trimestral Q3 2025'),
    (7, 5, 'INV-2025-402', '2025-04-20', '2025-05-20', 900.00,  'paid',   'Retainer fiscal abril 2025');

INSERT INTO invoice_items (invoice_id, item_description, quantity, unit_price) VALUES
    (6, 'Retainer asesoría fiscal mes enero 2025', 1, 4700.00),
    (7, 'Gestión nóminas marzo (168 empleados)',   1, 2600.00),
    (8, 'Honorarios outsourcing laboral junio',    1, 3800.00),
    (8, 'Ajuste auditoría Málaga',                 1, 450.00),
    (9, 'Reporting trimestral Q3 2025',            1, 2000.00),
    (10,'Retainer fiscal mensual',                 1, 900.00);

--------------------------------------------------------------------------------
-- COBERTURA ADICIONAL: asegurar datos en TODAS las tablas y cubrir enums
--------------------------------------------------------------------------------

-- 1) Cliente 'individual' + su oficina
INSERT INTO clients (legal_name, trade_name, tax_id, category, industry, headquarters_city, headquarters_region,
                     contact_name, contact_email, contact_phone, onboarding_date, account_manager_id, risk_rating, billing_currency)
VALUES ('Alejandro Pérez Autónomo', NULL, 'Z1234567X', 'individual', 'Servicios profesionales', 'Palma', 'Islas Baleares',
        'Alejandro Pérez', 'alejandro.perez@example.com', '+34 600 222 333', '2024-05-01',
        (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'Low', 'EUR');

INSERT INTO client_offices (client_id, site_name, city, address, employees_count, lead_contact, lead_email)
VALUES (
    (SELECT client_id FROM clients WHERE tax_id='Z1234567X'),
    'Estudio Palma', 'Palma', 'Carrer de Sindicat 12', 3, 'Alejandro Pérez', 'alejandro.perez@example.com'
);

-- 2) Engagements con estados 'completed' y 'cancelled'
INSERT INTO engagements (client_id, service_line_id, lead_consultant_id, start_date, end_date, status, retainer_fee, billing_frequency, description, renewal_probability)
VALUES
(
    (SELECT client_id FROM clients WHERE tax_id='Z1234567X'),
    (SELECT service_line_id FROM service_lines WHERE name='Fiscal'),
    (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'),
    '2024-01-01','2024-06-30','completed', 1200.00,'one-off','Regularización fiscal 2023', 0.00
),
(
    (SELECT client_id FROM clients WHERE tax_id='A87654321'), -- GASER
    (SELECT service_line_id FROM service_lines WHERE name='Legal'),
    (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'),
    '2024-04-01','2024-05-15','cancelled', 0.00,'one-off','Proyecto cancelado por alcance', 0.00
);

-- 3) Caso de cumplimiento con prioridad 'low' + tarea 'blocked'
INSERT INTO compliance_cases (engagement_id, case_code, case_type, fiscal_year, fiscal_period, due_date, status, priority, assigned_lead_id, notes)
VALUES (
    (SELECT MIN(engagement_id) FROM engagements e
     JOIN clients c ON c.client_id=e.client_id
     WHERE c.tax_id='Z1234567X' AND e.status='completed'),
    'AP-IRPF-2024', 'Declaración IRPF', 2024, 'Anual', '2025-06-30', 'scheduled', 'low',
    (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'),
    'Caso sencillo para autónomo individual'
);

INSERT INTO case_tasks (case_id, task_name, assigned_to_id, due_date, status, completed_at, comments)
VALUES (
    (SELECT case_id FROM compliance_cases WHERE case_code='AP-IRPF-2024'),
    'Solicitar certificados de retenciones', (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'),
    '2025-05-15', 'blocked', NULL, 'Bloqueado a la espera de certificado del banco'
);

-- 4) Documentos del nuevo caso
INSERT INTO documents (case_id, uploaded_by, doc_type, file_name, storage_path, uploaded_at, is_signed)
VALUES (
    (SELECT case_id FROM compliance_cases WHERE case_code='AP-IRPF-2024'),
    (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'),
    'Justificante retenciones', 'retenciones_2024.pdf', '/files/ap_autonomo/irpf/retenciones_2024.pdf', '2025-04-10 10:00', FALSE
);

-- 5) Tax returns para cubrir IRPF y WITHHOLDING
INSERT INTO tax_returns (client_id, case_id, fiscal_year, tax_type, period, amount_due, amount_paid, filing_date, status)
VALUES
(
    (SELECT client_id FROM clients WHERE tax_id='Z1234567X'),
    (SELECT case_id FROM compliance_cases WHERE case_code='AP-IRPF-2024'),
    2024, 'IRPF', 'Anual', 3200.00, 0.00, NULL, 'draft'
),
(
    (SELECT client_id FROM clients WHERE tax_id='B12345678'), -- TechNova
    NULL,
    2024, 'WITHHOLDING', 'Q3', 7800.00, 7800.00, '2024-10-15', 'filed'
);

-- 6) Estado de cuenta 'monthly'
INSERT INTO financial_statements (client_id, engagement_id, statement_type, period_start, period_end, revenue, expenses, payroll_costs, tax_provision, prepared_by_id, approved_by_id, approval_date)
VALUES (
    (SELECT client_id FROM clients WHERE tax_id='B12345678'),           -- TechNova
    (SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B12345678')
            AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
    'monthly','2025-08-01','2025-08-31', 720000.00, 560000.00, 145000.00, 54000.00,
    (SELECT employee_id FROM employees WHERE email='isabel.torres@iberconsulting.es'),
    (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'),
    '2025-09-10'
);

-- 7) Factura con estado 'void' y líneas con quantity>1
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes)
VALUES (
    (SELECT engagement_id FROM engagements WHERE status='cancelled' ORDER BY engagement_id DESC LIMIT 1),
    (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'),
    'INV-2025-VOID-001','2025-05-05','2025-06-05', 600.00,'void','Factura anulada por cancelación del proyecto'
);

INSERT INTO invoice_items (invoice_id, item_description, quantity, unit_price) VALUES
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-VOID-001'), 'Horas legales (pack)', 3, 200.00);

-- 8) Payroll extra para diversidad temporal (opcional, ya había datos)
INSERT INTO payroll_reports (client_id, engagement_id, reporting_month, employees_processed, total_gross_pay, social_security_contrib, submitted_by_id, submission_date)
VALUES (
    (SELECT client_id FROM clients WHERE tax_id='A87654321'),  -- GASER
    (SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A87654321') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
    '2024-03-01', 252, 525300.00, 163000.00, (SELECT employee_id FROM employees WHERE email='sergio.vidal@iberconsulting.es'), '2024-03-29'
);

-- 9) Vincular oficinas al engagement 'completed' (para que engagement_offices tenga cobertura)
INSERT INTO engagement_offices (engagement_id, office_id)
SELECT e.engagement_id, 1
FROM engagements e
JOIN clients c ON c.client_id=e.client_id
WHERE c.tax_id='Z1234567X' AND e.status='completed'
ON CONFLICT DO NOTHING;

-- FIN COBERTURA ADICIONAL

--------------------------------------------------------------------------------
-- DATOS COMPLEMENTARIOS PARA ANÁLISIS (más clientes, 12 meses, estados variados)
-- Objetivo: cubrir consultas NL->SQL de facturación mensual, TOP-10 trimestre,
-- ticket medio, estados por mes (overdue/paid/issued) y tiempo a 1ª factura.
--------------------------------------------------------------------------------

-- Nuevos clientes para alcanzar >10 con actividad en el trimestre actual (Q4-2025)
INSERT INTO clients (legal_name, trade_name, tax_id, category, industry, headquarters_city, headquarters_region,
                     contact_name, contact_email, contact_phone, onboarding_date, account_manager_id, risk_rating, billing_currency) VALUES
    ('Logística Atlántica S.L.', 'LogAtlántica', 'B11223344', 'sme', 'Logística y Transporte', 'A Coruña', 'Galicia',
     'Andrea Vila', 'andrea.vila@logatlantica.es', '+34 981 123 456', '2024-09-15',
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'Medium', 'EUR'),
    ('BioFarma Iberia S.A.', 'BioFarma', 'A11221122', 'corporate', 'Farmacéutica', 'Madrid', 'Comunidad de Madrid',
     'Jorge Molina', 'jmolina@biofarma.es', '+34 91 111 2222', '2025-01-05',
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'High', 'EUR'),
    ('Retail Ciudad S.L.', 'RetailCiudad', 'B55667788', 'sme', 'Retail', 'Zaragoza', 'Aragón',
     'Elena Ruiz', 'eruiz@retailciudad.es', '+34 976 222 333', '2024-07-10',
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'Medium', 'EUR'),
    ('EnerGreen Renovables S.L.', 'EnerGreen', 'B66778899', 'sme', 'Energías Renovables', 'Pamplona', 'Navarra',
     'Pablo Larrarte', 'pablo.larrarte@energreen.es', '+34 948 333 444', '2025-03-01',
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'Low', 'EUR'),
    ('AIStart Iberia S.L.', 'AIStart', 'B77889900', 'sme', 'Tecnología', 'Madrid', 'Comunidad de Madrid',
     'Sofía Álvarez', 'sofia@aistart.es', '+34 91 444 5555', '2025-02-15',
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'High', 'EUR'),
    ('Hoteles Sol y Mar S.L.', 'Sol y Mar', 'B99001122', 'sme', 'Hospitalidad', 'Alicante', 'Comunidad Valenciana',
     'Víctor Prats', 'vprats@solymar.es', '+34 965 555 666', '2024-11-01',
     (SELECT employee_id FROM employees WHERE email='isabel.torres@iberconsulting.es'), 'Medium', 'EUR'),
    ('Construcciones Norte S.A.', 'ConsNorte', 'A33445566', 'corporate', 'Construcción', 'Oviedo', 'Asturias',
     'Noelia Treviño', 'noelia@consnorte.es', '+34 984 777 888', '2025-05-01',
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'Medium', 'EUR');

-- Oficinas de los nuevos clientes
INSERT INTO client_offices (client_id, site_name, city, address, employees_count, lead_contact, lead_email) VALUES
    ((SELECT client_id FROM clients WHERE tax_id='B11223344'), 'Sede A Coruña', 'A Coruña', 'Rúa Real 10', 85, 'Andrea Vila', 'andrea.vila@logatlantica.es'),
    ((SELECT client_id FROM clients WHERE tax_id='A11221122'), 'Sede Madrid',  'Madrid',   'Calle Velázquez 128', 650, 'Jorge Molina', 'jmolina@biofarma.es'),
    ((SELECT client_id FROM clients WHERE tax_id='B55667788'), 'Sede Zaragoza','Zaragoza', 'Av. César Augusto 22', 110, 'Elena Ruiz', 'eruiz@retailciudad.es'),
    ((SELECT client_id FROM clients WHERE tax_id='B66778899'), 'Sede Pamplona','Pamplona', 'C. Estafeta 5', 60, 'Pablo Larrarte', 'pablo.larrarte@energreen.es'),
    ((SELECT client_id FROM clients WHERE tax_id='B77889900'), 'Sede Madrid',  'Madrid',   'C. Hermosilla 9', 24, 'Sofía Álvarez', 'sofia@aistart.es'),
    ((SELECT client_id FROM clients WHERE tax_id='B99001122'), 'Hotel Central','Alicante', 'Av. de la Estación 7', 180, 'Víctor Prats', 'vprats@solymar.es'),
    ((SELECT client_id FROM clients WHERE tax_id='A33445566'), 'Sede Oviedo',  'Oviedo',   'C. Uría 18', 240, 'Noelia Treviño', 'noelia@consnorte.es');

-- Engagements de nuevos clientes (variedad de líneas y frecuencias)
INSERT INTO engagements (client_id, service_line_id, lead_consultant_id, start_date, end_date, status, retainer_fee, billing_frequency, description, renewal_probability) VALUES
    ((SELECT client_id FROM clients WHERE tax_id='B11223344'), (SELECT service_line_id FROM service_lines WHERE name='Contable'),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), '2024-10-01', NULL, 'active', 1500.00, 'monthly', 'Contabilidad general y conciliaciones', 80.00),
    ((SELECT client_id FROM clients WHERE tax_id='A11221122'), (SELECT service_line_id FROM service_lines WHERE name='Fiscal'),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), '2025-02-01', NULL, 'active', 5200.00, 'monthly', 'Asesoría fiscal para multinacional', 90.00),
    ((SELECT client_id FROM clients WHERE tax_id='B55667788'), (SELECT service_line_id FROM service_lines WHERE name='Laboral'),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), '2024-08-15', NULL, 'active', 2100.00, 'monthly', 'Gestión de nóminas y altas', 88.00),
    ((SELECT client_id FROM clients WHERE tax_id='B66778899'), (SELECT service_line_id FROM service_lines WHERE name='Legal'),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), '2025-01-15', NULL, 'active', 4000.00, 'quarterly', 'Cumplimiento normativo y contratos', 70.00),
    ((SELECT client_id FROM clients WHERE tax_id='B77889900'), (SELECT service_line_id FROM service_lines WHERE name='Fiscal'),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), '2025-02-20', NULL, 'active', 1100.00, 'monthly', 'Startup fiscal y modelos 303/111', 85.00),
    ((SELECT client_id FROM clients WHERE tax_id='B99001122'), (SELECT service_line_id FROM service_lines WHERE name='Laboral'),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), '2024-11-05', NULL, 'active', 3500.00, 'monthly', 'Gestión de nóminas hotel', 80.00),
    ((SELECT client_id FROM clients WHERE tax_id='A33445566'), (SELECT service_line_id FROM service_lines WHERE name='Contable'),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), '2025-05-01', NULL, 'active', 2400.00, 'monthly', 'Contabilidad de proyectos de obra', 75.00);

-- Asociar engagements a oficina Madrid (1) para cobertura
INSERT INTO engagement_offices (engagement_id, office_id)
SELECT e.engagement_id, 1
FROM engagements e
JOIN clients c ON c.client_id=e.client_id
WHERE c.tax_id IN ('B11223344','A11221122','B55667788','B66778899','B77889900','B99001122','A33445566')
ON CONFLICT DO NOTHING;

-- Facturación últimos 12 meses (nov-2024 .. oct-2025) con mezcla de estados
-- NOVIEMBRE 2024
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2024-110', '2024-11-05', '2024-12-05', 1500.00, 'paid',   'Retainer contable noviembre 2024'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2024-111', '2024-11-28', '2024-12-28', 2100.00, 'paid',   'Nóminas noviembre 2024'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2024-112', '2024-11-10', '2024-12-10', 3500.00, 'paid',   'Nóminas hotel noviembre 2024');

-- DICIEMBRE 2024
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2024-120', '2024-12-05', '2025-01-05', 1500.00, 'paid',   'Retainer contable diciembre 2024'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2024-121', '2024-12-27', '2025-01-27', 2100.00, 'paid',   'Nóminas diciembre 2024'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2024-122', '2024-12-10', '2025-01-10', 3500.00, 'overdue','Nóminas hotel diciembre 2024');

-- ENERO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-501', '2025-01-05', '2025-02-05', 1500.00, 'paid',   'Retainer contable enero 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-502', '2025-01-27', '2025-02-27', 2100.00, 'paid',   'Nóminas enero 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2025-503', '2025-01-10', '2025-02-10', 3500.00, 'paid',   'Nóminas hotel enero 2025');

-- FEBRERO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-520', '2025-02-05', '2025-03-05', 5200.00, 'paid',   'Retainer fiscal febrero 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-521', '2025-02-25', '2025-03-25', 1100.00, 'issued', 'Retainer fiscal febrero 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-522', '2025-02-05', '2025-03-05', 1500.00, 'paid',   'Retainer contable febrero 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-523', '2025-02-26', '2025-03-26', 2100.00, 'paid',   'Nóminas febrero 2025');

-- MARZO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-530', '2025-03-05', '2025-04-05', 5200.00, 'paid',   'Retainer fiscal marzo 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-531', '2025-03-25', '2025-04-25', 1100.00, 'paid',   'Retainer fiscal marzo 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2025-532', '2025-03-10', '2025-04-10', 3500.00, 'issued', 'Nóminas hotel marzo 2025');

-- ABRIL 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B66778899') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Legal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-540', '2025-04-05', '2025-05-05', 4000.00, 'paid',   'Honorarios legales Q2 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-541', '2025-04-05', '2025-05-05', 5200.00, 'paid',   'Retainer fiscal abril 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-542', '2025-04-26', '2025-05-26', 2100.00, 'paid',   'Nóminas abril 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-543', '2025-04-25', '2025-05-25', 1100.00, 'paid',   'Retainer fiscal abril 2025');

-- MAYO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-550', '2025-05-05', '2025-06-05', 5200.00, 'paid',   'Retainer fiscal mayo 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-551', '2025-05-05', '2025-06-05', 1500.00, 'paid',   'Retainer contable mayo 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2025-552', '2025-05-10', '2025-06-10', 3500.00, 'paid',   'Nóminas hotel mayo 2025');

-- JUNIO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-560', '2025-06-05', '2025-07-05', 5200.00, 'paid',   'Retainer fiscal junio 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-561', '2025-06-26', '2025-07-26', 2100.00, 'overdue','Nóminas junio 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-563', '2025-06-05', '2025-07-05', 1500.00, 'paid',   'Retainer contable junio 2025');

-- JULIO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B66778899') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Legal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-570', '2025-07-05', '2025-08-05', 4000.00, 'paid',   'Honorarios legales Q3 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-571', '2025-07-05', '2025-08-05', 5200.00, 'paid',   'Retainer fiscal julio 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-572', '2025-07-25', '2025-08-25', 1100.00, 'paid',   'Retainer fiscal julio 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A33445566') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-573', '2025-07-01', '2025-08-01', 2400.00, 'paid',   'Contabilidad mensual julio 2025');

-- AGOSTO 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2025-580', '2025-08-10', '2025-09-10', 3500.00, 'paid',   'Nóminas hotel agosto 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-581', '2025-08-05', '2025-09-05', 1500.00, 'overdue','Retainer contable agosto 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-582', '2025-08-26', '2025-09-26', 2100.00, 'paid',   'Nóminas agosto 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-583', '2025-08-05', '2025-09-05', 5200.00, 'paid',   'Retainer fiscal agosto 2025');

-- SEPTIEMBRE 2025
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-590', '2025-09-05', '2025-10-05', 5200.00, 'paid',   'Retainer fiscal septiembre 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-591', '2025-09-25', '2025-10-25', 1100.00, 'issued', 'Retainer fiscal septiembre 2025'),
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-592', '2025-09-05', '2025-10-05', 1500.00, 'paid',   'Retainer contable septiembre 2025');

-- OCTUBRE 2025 (trimestre actual Q4-2025, asegurar >=10 clientes con facturación)
INSERT INTO invoices (engagement_id, issued_by_id, invoice_number, issue_date, due_date, amount_total, status, notes) VALUES
    -- TechNova (Fiscal)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B12345678') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-610', '2025-10-05', '2025-11-05', 4700.00, 'issued', 'Retainer fiscal octubre 2025'),
    -- TechNova (Laboral)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B12345678') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-611', '2025-10-01', '2025-10-31', 2600.00, 'paid',   'Nóminas octubre 2025'),
    -- Climed (Contable)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99887766') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-612', '2025-10-15', '2025-11-15', 1800.00, 'paid',   'Reporting contable octubre 2025'),
    -- Brío (Fiscal)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='F44556677') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='carmen.ruiz@iberconsulting.es'), 'INV-2025-613', '2025-10-20', '2025-11-20', 900.00,  'issued', 'Retainer fiscal octubre 2025'),
    -- BioFarma (Fiscal)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A11221122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-614', '2025-10-05', '2025-11-05', 5200.00, 'issued', 'Retainer fiscal octubre 2025'),
    -- EnerGreen (Legal)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B66778899') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Legal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='laura.martin@iberconsulting.es'), 'INV-2025-615', '2025-10-05', '2025-11-05', 4000.00, 'issued', 'Honorarios legales Q4 2025'),
    -- Logística Atlántica (Contable)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B11223344') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-616', '2025-10-05', '2025-11-05', 1500.00, 'issued', 'Retainer contable octubre 2025'),
    -- Retail Ciudad (Laboral)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B55667788') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='javier.lopez@iberconsulting.es'), 'INV-2025-617', '2025-10-26', '2025-11-26', 2100.00, 'issued', 'Nóminas octubre 2025'),
    -- AIStart Iberia (Fiscal)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B77889900') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Fiscal') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='marta.gomez@iberconsulting.es'), 'INV-2025-618', '2025-10-25', '2025-11-25', 1100.00, 'issued', 'Retainer fiscal octubre 2025'),
    -- Hoteles Sol y Mar (Laboral)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='B99001122') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Laboral') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='anna.puig@iberconsulting.es'), 'INV-2025-619', '2025-10-10', '2025-11-10', 3500.00, 'paid',   'Nóminas hotel octubre 2025'),
    -- Construcciones Norte (Contable)
    ((SELECT engagement_id FROM engagements WHERE client_id=(SELECT client_id FROM clients WHERE tax_id='A33445566') AND service_line_id=(SELECT service_line_id FROM service_lines WHERE name='Contable') LIMIT 1),
     (SELECT employee_id FROM employees WHERE email='diego.herrera@iberconsulting.es'), 'INV-2025-620', '2025-10-01', '2025-11-01', 2400.00, 'issued', 'Contabilidad mensual octubre 2025');

-- Líneas de detalle para las nuevas facturas (1 línea por factura con el total)
-- Usamos subconsultas por invoice_number para evitar suposiciones de IDs
INSERT INTO invoice_items (invoice_id, item_description, quantity, unit_price) VALUES
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-110'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-111'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-112'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-120'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-121'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2024-122'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-501'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-502'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-503'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-520'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-521'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-522'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-523'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-530'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-531'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-532'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-540'), 'Honorarios legales trimestrales', 1, 4000.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-541'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-542'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-543'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-550'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-551'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-552'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-560'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-561'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-563'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-570'), 'Honorarios legales trimestrales', 1, 4000.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-571'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-572'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-573'), 'Honorarios contables', 1, 2400.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-580'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-581'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-582'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-583'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-590'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-591'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-592'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-610'), 'Retainer fiscal', 1, 4700.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-611'), 'Nóminas mes', 1, 2600.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-612'), 'Honorarios contables', 1, 1800.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-613'), 'Retainer fiscal', 1, 900.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-614'), 'Retainer fiscal', 1, 5200.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-615'), 'Honorarios legales trimestrales', 1, 4000.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-616'), 'Honorarios contables', 1, 1500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-617'), 'Nóminas mes', 1, 2100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-618'), 'Retainer fiscal', 1, 1100.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-619'), 'Nóminas mes', 1, 3500.00),
    ((SELECT invoice_id FROM invoices WHERE invoice_number='INV-2025-620'), 'Honorarios contables', 1, 2400.00);

-- Notas:
-- - Primeras facturas tras inicio del engagement pensadas para variar el "lead time":
--   B11223344: start 2024-10-01 -> 1ª factura 2024-11-05 (~35 días)
--   A11221122: start 2025-02-01 -> 1ª factura 2025-02-05 (4 días)
--   B55667788: start 2024-08-15 -> 1ª factura 2024-11-28 (~105 días)
--   B66778899: start 2025-01-15 -> 1ª factura 2025-04-05 (~80 días)
--   B77889900: start 2025-02-20 -> 1ª factura 2025-02-25 (5 días)
--   B99001122: start 2024-11-05 -> 1ª factura 2024-11-10 (5 días)
--   A33445566: start 2025-05-01 -> 1ª factura 2025-07-01 (~61 días)

-- Con esto hay actividad suficiente por línea y cliente en los últimos 12 meses,
-- mezcla de estados (paid/issued/overdue) y al menos 10 clientes con facturas
-- en octubre de 2025 para análisis de TOP-10 trimestral y concentración.
