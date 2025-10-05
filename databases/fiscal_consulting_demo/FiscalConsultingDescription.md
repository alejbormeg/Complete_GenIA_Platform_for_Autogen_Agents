# **Diccionario de datos — `fiscal_consulting_demo`**

## 1) Esquema y convenciones

* **Esquema**: `fiscal_consulting_demo`
  El script hace `DROP SCHEMA ... CASCADE`, `CREATE SCHEMA` y `SET search_path TO fiscal_consulting_demo`.
* **PKs**: todas las tablas principales usan `SERIAL` (entero auto-incremental) como **Primary Key**.
* **Convenciones**:

  * Campos de relación usan sufijo `_id`.
  * Varios FKs definen comportamiento explícito de **ON DELETE** (ver detalle por tabla).

---

## 2) Tipos enumerados (dominios controlados)

| Enum                | Valores permitidos                                                            |
| ------------------- | ----------------------------------------------------------------------------- |
| `client_category`   | `'corporate'`, `'sme'`, `'individual'`, `'public'`                            |
| `engagement_status` | `'planning'`, `'active'`, `'on_hold'`, `'completed'`, `'cancelled'`           |
| `case_status`       | `'scheduled'`, `'in_progress'`, `'waiting_client'`, `'submitted'`, `'closed'` |
| `case_priority`     | `'low'`, `'medium'`, `'high'`, `'critical'`                                   |
| `invoice_status`    | `'draft'`, `'issued'`, `'paid'`, `'overdue'`, `'void'`                        |
| `statement_kind`    | `'monthly'`, `'quarterly'`, `'annual'`                                        |
| `tax_kind`          | `'CIT'`, `'VAT'`, `'IRPF'`, `'SOCIAL_SECURITY'`, `'WITHHOLDING'`              |

---

## 3) Tablas (definición precisa)

A continuación, cada tabla con **columnas**, **claves**, **restricciones** e **índices** relevantes.

### 3.1 `offices`

**Descripción**: Oficinas de la firma.

**Columnas**

| Columna         | Tipo      | Nulo | Default | Restricciones / Comentarios     |
| --------------- | --------- | ---: | ------- | ------------------------------- |
| `office_id`     | `SERIAL`  |   NO | —       | **PK**                          |
| `name`          | `TEXT`    |   NO | —       |                                 |
| `region`        | `TEXT`    |   NO | —       |                                 |
| `city`          | `TEXT`    |   NO | —       |                                 |
| `address`       | `TEXT`    |   NO | —       |                                 |
| `phone`         | `TEXT`    |   SÍ | —       |                                 |
| `email`         | `TEXT`    |   SÍ | —       | **UNIQUE**                      |
| `opened_date`   | `DATE`    |   SÍ | —       |                                 |
| `headcount_cap` | `INTEGER` |   SÍ | `50`    | **CHECK** (`headcount_cap > 0`) |

**Relaciones**

* Referenciada por: `employees.office_id` (**ON DELETE SET NULL**), `engagement_offices.office_id` (**ON DELETE CASCADE**).

---

### 3.2 `service_lines`

**Descripción**: Líneas de servicio (fiscal, laboral, contable, etc.).

**Columnas**

| Columna           | Tipo     | Nulo | Default | Restricciones / Comentarios |
| ----------------- | -------- | ---: | ------- | --------------------------- |
| `service_line_id` | `SERIAL` |   NO | —       | **PK**                      |
| `name`            | `TEXT`   |   NO | —       |                             |
| `category`        | `TEXT`   |   NO | —       |                             |
| `description`     | `TEXT`   |   SÍ | —       |                             |

**Relaciones**

* Referenciada por: `employees.service_line_id` (**ON DELETE SET NULL**), `engagements.service_line_id` (**ON DELETE RESTRICT**).

---

### 3.3 `employees`

**Descripción**: Empleados/consultores de la firma.

**Columnas**

| Columna           | Tipo            | Nulo | Default | Restricciones / Comentarios                                       |
| ----------------- | --------------- | ---: | ------- | ----------------------------------------------------------------- |
| `employee_id`     | `SERIAL`        |   NO | —       | **PK**                                                            |
| `full_name`       | `TEXT`          |   NO | —       |                                                                   |
| `email`           | `TEXT`          |   NO | —       | **UNIQUE**                                                        |
| `phone`           | `TEXT`          |   SÍ | —       |                                                                   |
| `role`            | `TEXT`          |   NO | —       |                                                                   |
| `grade`           | `TEXT`          |   NO | —       |                                                                   |
| `is_manager`      | `BOOLEAN`       |   SÍ | `FALSE` |                                                                   |
| `hire_date`       | `DATE`          |   NO | —       |                                                                   |
| `office_id`       | `INTEGER`       |   SÍ | —       | **FK** → `offices.office_id` (**ON DELETE SET NULL**)             |
| `service_line_id` | `INTEGER`       |   SÍ | —       | **FK** → `service_lines.service_line_id` (**ON DELETE SET NULL**) |
| `salary_band`     | `NUMERIC(10,2)` |   SÍ | —       |                                                                   |

**Relaciones (como FK de otras tablas)**

* Referenciado por:

  * `clients.account_manager_id` (**ON DELETE SET NULL**)
  * `engagements.lead_consultant_id` (**ON DELETE SET NULL**)
  * `compliance_cases.assigned_lead_id` (**ON DELETE SET NULL**)
  * `case_tasks.assigned_to_id` (**ON DELETE SET NULL**)
  * `documents.uploaded_by` (**ON DELETE SET NULL**)
  * `payroll_reports.submitted_by_id` (**ON DELETE SET NULL**)
  * `financial_statements.prepared_by_id` y `approved_by_id` (**ON DELETE SET NULL**)
  * `invoices.issued_by_id` (**ON DELETE SET NULL**)

**Índices**

* (Indirecto) Existe `idx_employees_office` **en** `employees(office_id)`.

---

### 3.4 `clients`

**Descripción**: Clientes de la firma.

**Columnas**

| Columna               | Tipo              | Nulo | Default    | Restricciones / Comentarios                               |
| --------------------- | ----------------- | ---: | ---------- | --------------------------------------------------------- |
| `client_id`           | `SERIAL`          |   NO | —          | **PK**                                                    |
| `legal_name`          | `TEXT`            |   NO | —          |                                                           |
| `trade_name`          | `TEXT`            |   SÍ | —          |                                                           |
| `tax_id`              | `TEXT`            |   NO | —          | **UNIQUE**                                                |
| `category`            | `client_category` |   NO | —          | Enum                                                      |
| `industry`            | `TEXT`            |   SÍ | —          |                                                           |
| `headquarters_city`   | `TEXT`            |   SÍ | —          |                                                           |
| `headquarters_region` | `TEXT`            |   SÍ | —          |                                                           |
| `contact_name`        | `TEXT`            |   SÍ | —          |                                                           |
| `contact_email`       | `TEXT`            |   SÍ | —          |                                                           |
| `contact_phone`       | `TEXT`            |   SÍ | —          |                                                           |
| `onboarding_date`     | `DATE`            |   NO | —          |                                                           |
| `account_manager_id`  | `INTEGER`         |   SÍ | —          | **FK** → `employees.employee_id` (**ON DELETE SET NULL**) |
| `risk_rating`         | `TEXT`            |   SÍ | `'Medium'` |                                                           |
| `billing_currency`    | `TEXT`            |   SÍ | `'EUR'`    |                                                           |

**Relaciones**

* Referenciada por: `client_offices.client_id` (**ON DELETE CASCADE**), `engagements.client_id` (**ON DELETE CASCADE**), `tax_returns.client_id` (**ON DELETE CASCADE**), `payroll_reports.client_id` (**ON DELETE CASCADE**), `financial_statements.client_id` (**ON DELETE CASCADE**).

**Índices**

* `idx_clients_account_manager` en `clients(account_manager_id)`.

---

### 3.5 `client_offices`

**Descripción**: Sedes/sucursales de cada cliente.

**Columnas**

| Columna            | Tipo      | Nulo | Default | Restricciones / Comentarios                          |
| ------------------ | --------- | ---: | ------- | ---------------------------------------------------- |
| `client_office_id` | `SERIAL`  |   NO | —       | **PK**                                               |
| `client_id`        | `INTEGER` |   NO | —       | **FK** → `clients.client_id` (**ON DELETE CASCADE**) |
| `site_name`        | `TEXT`    |   NO | —       |                                                      |
| `city`             | `TEXT`    |   NO | —       |                                                      |
| `address`          | `TEXT`    |   NO | —       |                                                      |
| `employees_count`  | `INTEGER` |   SÍ | —       |                                                      |
| `lead_contact`     | `TEXT`    |   SÍ | —       |                                                      |
| `lead_email`       | `TEXT`    |   SÍ | —       |                                                      |

---

### 3.6 `engagements`

**Descripción**: Encargos/contratos activos o planificados por cliente y línea de servicio.

**Columnas**

| Columna               | Tipo                | Nulo | Default      | Restricciones / Comentarios                                       |
| --------------------- | ------------------- | ---: | ------------ | ----------------------------------------------------------------- |
| `engagement_id`       | `SERIAL`            |   NO | —            | **PK**                                                            |
| `client_id`           | `INTEGER`           |   NO | —            | **FK** → `clients.client_id` (**ON DELETE CASCADE**)              |
| `service_line_id`     | `INTEGER`           |   NO | —            | **FK** → `service_lines.service_line_id` (**ON DELETE RESTRICT**) |
| `lead_consultant_id`  | `INTEGER`           |   SÍ | —            | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)         |
| `start_date`          | `DATE`              |   NO | —            |                                                                   |
| `end_date`            | `DATE`              |   SÍ | —            |                                                                   |
| `status`              | `engagement_status` |   NO | `'planning'` | Enum                                                              |
| `retainer_fee`        | `NUMERIC(12,2)`     |   SÍ | —            |                                                                   |
| `billing_frequency`   | `TEXT`              |   SÍ | —            | **CHECK** in (`'monthly'`,`'quarterly'`,`'annual'`,`'one-off'`)   |
| `description`         | `TEXT`              |   SÍ | —            |                                                                   |
| `renewal_probability` | `NUMERIC(5,2)`      |   SÍ | —            | **CHECK** `BETWEEN 0 AND 100`                                     |

**Relaciones**

* N:M con `offices` mediante `engagement_offices`.
* 1:N hacia `compliance_cases`, `invoices`, `payroll_reports` (opcional), `financial_statements` (opcional).

---

### 3.7 `engagement_offices` (tabla de unión N:M)

**Descripción**: Relaciona encargos con oficinas.

**Columnas**

| Columna         | Tipo      | Nulo | Default | Restricciones / Comentarios                                  |
| --------------- | --------- | ---: | ------- | ------------------------------------------------------------ |
| `engagement_id` | `INTEGER` |   SÍ | —       | **FK** → `engagements.engagement_id` (**ON DELETE CASCADE**) |
| `office_id`     | `INTEGER` |   SÍ | —       | **FK** → `offices.office_id` (**ON DELETE CASCADE**)         |

**Claves**

* **PK compuesta**: (`engagement_id`, `office_id`).

---

### 3.8 `compliance_cases`

**Descripción**: Expedientes de cumplimiento (IVA, IS, auditorías, etc.) vinculados a un encargo.

**Columnas**

| Columna            | Tipo            | Nulo | Default    | Restricciones / Comentarios                                  |
| ------------------ | --------------- | ---: | ---------- | ------------------------------------------------------------ |
| `case_id`          | `SERIAL`        |   NO | —          | **PK**                                                       |
| `engagement_id`    | `INTEGER`       |   NO | —          | **FK** → `engagements.engagement_id` (**ON DELETE CASCADE**) |
| `case_code`        | `TEXT`          |   NO | —          | **UNIQUE**                                                   |
| `case_type`        | `TEXT`          |   NO | —          |                                                              |
| `fiscal_year`      | `INTEGER`       |   NO | —          |                                                              |
| `fiscal_period`    | `TEXT`          |   SÍ | —          |                                                              |
| `due_date`         | `DATE`          |   SÍ | —          |                                                              |
| `status`           | `case_status`   |   NO | —          | Enum                                                         |
| `priority`         | `case_priority` |   NO | `'medium'` | Enum                                                         |
| `assigned_lead_id` | `INTEGER`       |   SÍ | —          | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)    |
| `notes`            | `TEXT`          |   SÍ | —          |                                                              |

**Relaciones**

* 1:N hacia `case_tasks` y `documents`.
* Referenciada opcionalmente por `tax_returns.case_id` (**ON DELETE SET NULL**).

**Índices**

* `idx_cases_due_date` en `compliance_cases(due_date)`.

---

### 3.9 `case_tasks`

**Descripción**: Tareas de cada expediente.

**Columnas**

| Columna          | Tipo        | Nulo | Default | Restricciones / Comentarios                                          |
| ---------------- | ----------- | ---: | ------- | -------------------------------------------------------------------- |
| `task_id`        | `SERIAL`    |   NO | —       | **PK**                                                               |
| `case_id`        | `INTEGER`   |   NO | —       | **FK** → `compliance_cases.case_id` (**ON DELETE CASCADE**)          |
| `task_name`      | `TEXT`      |   NO | —       |                                                                      |
| `assigned_to_id` | `INTEGER`   |   SÍ | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)            |
| `due_date`       | `DATE`      |   SÍ | —       |                                                                      |
| `status`         | `TEXT`      |   NO | —       | **CHECK** in (`'pending'`,`'in_progress'`,`'completed'`,`'blocked'`) |
| `completed_at`   | `TIMESTAMP` |   SÍ | —       |                                                                      |
| `comments`       | `TEXT`      |   SÍ | —       |                                                                      |

---

### 3.10 `documents`

**Descripción**: Documentos asociados a expedientes.

**Columnas**

| Columna        | Tipo        | Nulo | Default | Restricciones / Comentarios                                 |
| -------------- | ----------- | ---: | ------- | ----------------------------------------------------------- |
| `document_id`  | `SERIAL`    |   NO | —       | **PK**                                                      |
| `case_id`      | `INTEGER`   |   SÍ | —       | **FK** → `compliance_cases.case_id` (**ON DELETE CASCADE**) |
| `uploaded_by`  | `INTEGER`   |   SÍ | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)   |
| `doc_type`     | `TEXT`      |   NO | —       |                                                             |
| `file_name`    | `TEXT`      |   NO | —       |                                                             |
| `storage_path` | `TEXT`      |   NO | —       |                                                             |
| `uploaded_at`  | `TIMESTAMP` |   NO | `NOW()` |                                                             |
| `is_signed`    | `BOOLEAN`   |   SÍ | `FALSE` |                                                             |

---

### 3.11 `tax_returns`

**Descripción**: Declaraciones/impuestos presentados por cliente (posible enlace a expediente).

**Columnas**

| Columna         | Tipo            | Nulo | Default | Restricciones / Comentarios                                  |
| --------------- | --------------- | ---: | ------- | ------------------------------------------------------------ |
| `tax_return_id` | `SERIAL`        |   NO | —       | **PK**                                                       |
| `client_id`     | `INTEGER`       |   NO | —       | **FK** → `clients.client_id` (**ON DELETE CASCADE**)         |
| `case_id`       | `INTEGER`       |   SÍ | —       | **FK** → `compliance_cases.case_id` (**ON DELETE SET NULL**) |
| `fiscal_year`   | `INTEGER`       |   NO | —       |                                                              |
| `tax_type`      | `tax_kind`      |   NO | —       | Enum                                                         |
| `period`        | `TEXT`          |   SÍ | —       |                                                              |
| `amount_due`    | `NUMERIC(12,2)` |   SÍ | —       |                                                              |
| `amount_paid`   | `NUMERIC(12,2)` |   SÍ | —       |                                                              |
| `filing_date`   | `DATE`          |   SÍ | —       |                                                              |
| `status`        | `TEXT`          |   SÍ | —       | **CHECK** in (`'draft'`,`'filed'`,`'accepted'`,`'rejected'`) |

---

### 3.12 `payroll_reports`

**Descripción**: Reportes de nóminas por cliente y mes (enlazables a un engagement).

**Columnas**

| Columna                   | Tipo            | Nulo | Default | Restricciones / Comentarios                                   |
| ------------------------- | --------------- | ---: | ------- | ------------------------------------------------------------- |
| `payroll_report_id`       | `SERIAL`        |   NO | —       | **PK**                                                        |
| `client_id`               | `INTEGER`       |   NO | —       | **FK** → `clients.client_id` (**ON DELETE CASCADE**)          |
| `engagement_id`           | `INTEGER`       |   SÍ | —       | **FK** → `engagements.engagement_id` (**ON DELETE SET NULL**) |
| `reporting_month`         | `DATE`          |   NO | —       | (convención: primer día del mes)                              |
| `employees_processed`     | `INTEGER`       |   NO | —       |                                                               |
| `total_gross_pay`         | `NUMERIC(12,2)` |   NO | —       |                                                               |
| `social_security_contrib` | `NUMERIC(12,2)` |   NO | —       |                                                               |
| `submitted_by_id`         | `INTEGER`       |   NO | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)     |
| `submission_date`         | `DATE`          |   NO | —       |                                                               |

**Índices**

* `idx_payroll_reports_month` en `payroll_reports(reporting_month)`.

---

### 3.13 `financial_statements`

**Descripción**: Estados financieros por cliente (mensuales, trimestrales o anuales), opcionalmente ligados a un engagement.

**Columnas**

| Columna          | Tipo             | Nulo | Default | Restricciones / Comentarios                                   |
| ---------------- | ---------------- | ---: | ------- | ------------------------------------------------------------- |
| `statement_id`   | `SERIAL`         |   NO | —       | **PK**                                                        |
| `client_id`      | `INTEGER`        |   NO | —       | **FK** → `clients.client_id` (**ON DELETE CASCADE**)          |
| `engagement_id`  | `INTEGER`        |   SÍ | —       | **FK** → `engagements.engagement_id` (**ON DELETE SET NULL**) |
| `statement_type` | `statement_kind` |   NO | —       | Enum                                                          |
| `period_start`   | `DATE`           |   NO | —       |                                                               |
| `period_end`     | `DATE`           |   NO | —       |                                                               |
| `revenue`        | `NUMERIC(14,2)`  |   SÍ | —       |                                                               |
| `expenses`       | `NUMERIC(14,2)`  |   SÍ | —       |                                                               |
| `payroll_costs`  | `NUMERIC(14,2)`  |   SÍ | —       |                                                               |
| `tax_provision`  | `NUMERIC(14,2)`  |   SÍ | —       |                                                               |
| `prepared_by_id` | `INTEGER`        |   SÍ | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)     |
| `approved_by_id` | `INTEGER`        |   SÍ | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)     |
| `approval_date`  | `DATE`           |   SÍ | —       |                                                               |

**Índices**

* `idx_financial_statements_period` en `financial_statements(period_start, period_end)`.

---

### 3.14 `invoices`

**Descripción**: Facturas emitidas por engagement.

**Columnas**

| Columna          | Tipo             | Nulo | Default | Restricciones / Comentarios                                  |
| ---------------- | ---------------- | ---: | ------- | ------------------------------------------------------------ |
| `invoice_id`     | `SERIAL`         |   NO | —       | **PK**                                                       |
| `engagement_id`  | `INTEGER`        |   NO | —       | **FK** → `engagements.engagement_id` (**ON DELETE CASCADE**) |
| `issued_by_id`   | `INTEGER`        |   SÍ | —       | **FK** → `employees.employee_id` (**ON DELETE SET NULL**)    |
| `invoice_number` | `TEXT`           |   NO | —       | **UNIQUE**                                                   |
| `issue_date`     | `DATE`           |   NO | —       |                                                              |
| `due_date`       | `DATE`           |   NO | —       |                                                              |
| `amount_total`   | `NUMERIC(12,2)`  |   NO | —       |                                                              |
| `status`         | `invoice_status` |   NO | —       | Enum                                                         |
| `notes`          | `TEXT`           |   SÍ | —       |                                                              |

**Relaciones**

* 1:N hacia `invoice_items`.

---

### 3.15 `invoice_items`

**Descripción**: Partidas (líneas) de cada factura.

**Columnas**

| Columna            | Tipo            | Nulo | Default  | Restricciones / Comentarios                                  |
| ------------------ | --------------- | ---: | -------- | ------------------------------------------------------------ |
| `invoice_item_id`  | `SERIAL`        |   NO | —        | **PK**                                                       |
| `invoice_id`       | `INTEGER`       |   NO | —        | **FK** → `invoices.invoice_id` (**ON DELETE CASCADE**)       |
| `item_description` | `TEXT`          |   NO | —        |                                                              |
| `quantity`         | `INTEGER`       |   NO | `1`      |                                                              |
| `unit_price`       | `NUMERIC(12,2)` |   NO | —        |                                                              |
| `line_total`       | `NUMERIC(12,2)` |   NO | generado | **GENERATED ALWAYS AS** (`quantity * unit_price`) **STORED** |

---

## 4) Índices definidos explícitamente

* `idx_employees_office` en **`employees(office_id)`**
* `idx_clients_account_manager` en **`clients(account_manager_id)`**
* `idx_cases_due_date` en **`compliance_cases(due_date)`**
* `idx_payroll_reports_month` en **`payroll_reports(reporting_month)`**
* `idx_financial_statements_period` en **`financial_statements(period_start, period_end)`**

> **Nota**: además de estos índices, las **PK** y **UNIQUE** crean índices implícitos sobre sus columnas.

---

## 5) Mapa de relaciones (cardinalidades y reglas ON DELETE)

* **clients (1) — (N) client_offices**: `client_offices.client_id` **ON DELETE CASCADE**.

* **clients (1) — (N) engagements**: `engagements.client_id` **ON DELETE CASCADE**.

* **clients (1) — (N) tax_returns**: `tax_returns.client_id` **ON DELETE CASCADE**.

* **clients (1) — (N) payroll_reports**: `payroll_reports.client_id` **ON DELETE CASCADE**.

* **clients (1) — (N) financial_statements**: `financial_statements.client_id` **ON DELETE CASCADE**.

* **service_lines (1) — (N) employees**: `employees.service_line_id` **ON DELETE SET NULL**.

* **service_lines (1) — (N) engagements**: `engagements.service_line_id` **ON DELETE RESTRICT**.

* **offices (1) — (N) employees**: `employees.office_id` **ON DELETE SET NULL**.

* **offices (N) — (M) engagements** vía **engagement_offices** con **PK (engagement_id, office_id)**; ambos FKs **ON DELETE CASCADE**.

* **employees (1) — (N) clients** como account manager: `clients.account_manager_id` **ON DELETE SET NULL**.

* **employees (1) — (N) engagements** como lead consultant: `engagements.lead_consultant_id` **ON DELETE SET NULL**.

* **employees (1) — (N) compliance_cases** como assigned lead: `compliance_cases.assigned_lead_id` **ON DELETE SET NULL**.

* **employees (1) — (N) case_tasks** como assigned_to: `case_tasks.assigned_to_id` **ON DELETE SET NULL**.

* **employees (1) — (N) documents** como uploaded_by: `documents.uploaded_by` **ON DELETE SET NULL**.

* **employees (1) — (N) payroll_reports** como submitted_by: `payroll_reports.submitted_by_id` **ON DELETE SET NULL**.

* **employees (1) — (N) financial_statements** como prepared_by / approved_by: ambos **ON DELETE SET NULL**.

* **employees (1) — (N) invoices** como issued_by: `invoices.issued_by_id` **ON DELETE SET NULL**.

* **engagements (1) — (N) compliance_cases**: `compliance_cases.engagement_id` **ON DELETE CASCADE**.

* **engagements (1) — (N) invoices**: `invoices.engagement_id` **ON DELETE CASCADE**.

* **engagements (1) — (N) payroll_reports** (opcional): `payroll_reports.engagement_id` **ON DELETE SET NULL**.

* **engagements (1) — (N) financial_statements** (opcional): `financial_statements.engagement_id` **ON DELETE SET NULL**.

* **compliance_cases (1) — (N) case_tasks**: `case_tasks.case_id` **ON DELETE CASCADE**.

* **compliance_cases (1) — (N) documents**: `documents.case_id` **ON DELETE CASCADE**.

* **compliance_cases (1) — (N) tax_returns** (opcional): `tax_returns.case_id` **ON DELETE SET NULL**.

* **invoices (1) — (N) invoice_items**: `invoice_items.invoice_id` **ON DELETE CASCADE**.

---

## 6) Reglas y checks relevantes

* **`offices.headcount_cap > 0`**.
* **`engagements.billing_frequency`** ∈ {`'monthly'`,`'quarterly'`,`'annual'`,`'one-off'`}.
* **`engagements.renewal_probability`** ∈ **[0, 100]**.
* **`case_tasks.status`** ∈ {`'pending'`,`'in_progress'`,`'completed'`,`'blocked'`}.
* **`tax_returns.status`** ∈ {`'draft'`,`'filed'`,`'accepted'`,`'rejected'`}.
* **`invoice_items.line_total`** : columna **generada** (`quantity * unit_price`) **STORED**.
* **Campos `status`/`type` enumerados**: usan **enums** donde corresponde (`engagement_status`, `case_status`, `case_priority`, `invoice_status`, `statement_kind`, `tax_kind`, `client_category`).

---

## 7) Resumen conceptual (para RAG)

* **Entidades núcleo**: `clients`, `engagements`, `compliance_cases`, `invoices`, `tax_returns`, `payroll_reports`, `financial_statements`, `employees`, `offices`, `service_lines`.
* **Asociaciones clave**:

  * **Cliente → Engagements → (Cases/Invoices/Reports/Statements)**.
  * **Case → Tasks/Docs** y opcionalmente **→ Tax Returns**.
  * **Engagement ⇄ Offices** (N:M).
  * **Employees** intervienen en múltiples roles (lead, assigned_to, prepared_by, approved_by, issued_by, uploaded_by, submitted_by).
* **Borrado en cascada** cuidadosamente aplicado en entidades dependientes (p. ej., eliminar un `client` cascada a sus `engagements`, que a su vez cascada a `compliance_cases`, `invoices`, etc., según la cadena de FKs).
* **Índices** dirigidos a flujos de reporting y navegación por FK.
