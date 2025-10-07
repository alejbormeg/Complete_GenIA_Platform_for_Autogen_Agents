¡Perfecto! Te dejo un **esquema entidad-relación (ER)** y, después, un **resumen breve de cada tabla** con la información que guarda.

```mermaid
erDiagram
    OFFICES ||--o{ EMPLOYEES : aloja
    SERVICE_LINES ||--o{ EMPLOYEES : pertenece_a

    EMPLOYEES ||--o{ CLIENTS : es_account_manager_de
    CLIENTS ||--o{ CLIENT_OFFICES : tiene
    CLIENTS ||--o{ ENGAGEMENTS : contrata

    SERVICE_LINES ||--o{ ENGAGEMENTS : clasifica
    EMPLOYEES ||--o{ ENGAGEMENTS : lidera(lead_consultant)

    OFFICES }o--o{ ENGAGEMENTS : "opera_en (ENGAGEMENT_OFFICES)"

    ENGAGEMENTS ||--o{ COMPLIANCE_CASES : genera
    EMPLOYEES ||--o{ COMPLIANCE_CASES : asignado_como_lead

    COMPLIANCE_CASES ||--o{ CASE_TASKS : desglosa
    EMPLOYEES ||--o{ CASE_TASKS : asignado_a

    COMPLIANCE_CASES ||--o{ DOCUMENTS : adjunta
    EMPLOYEES ||--o{ DOCUMENTS : sube

    CLIENTS ||--o{ TAX_RETURNS : declara
    COMPLIANCE_CASES }o--o{ TAX_RETURNS : referencia_opcional

    CLIENTS ||--o{ PAYROLL_REPORTS : presenta
    ENGAGEMENTS }o--o{ PAYROLL_REPORTS : vinculo_opcional
    EMPLOYEES ||--o{ PAYROLL_REPORTS : presentado_por

    CLIENTS ||--o{ FINANCIAL_STATEMENTS : reporta
    ENGAGEMENTS }o--o{ FINANCIAL_STATEMENTS : vinculo_opcional
    EMPLOYEES ||--o{ FINANCIAL_STATEMENTS : preparado_por
    EMPLOYEES ||--o{ FINANCIAL_STATEMENTS : aprobado_por

    ENGAGEMENTS ||--o{ INVOICES : factura
    EMPLOYEES ||--o{ INVOICES : emitida_por
    INVOICES ||--o{ INVOICE_ITEMS : detalla
```

# Resumen de tablas (qué guardan)

* **offices**
  Maestros de oficinas: nombre, región/ciudad, dirección, contacto, fecha de apertura y capacidad. PK: `office_id`.

* **service_lines**
  Líneas/áreas de servicio (Fiscal, Laboral, Contable, Legal): nombre, categoría y descripción. PK: `service_line_id`.

* **employees**
  Empleados y su organización: nombre, email, rol, grado, si es manager, fecha de alta, oficina y línea de servicio, y banda salarial. FK a `offices` y `service_lines`. PK: `employee_id`.

* **clients**
  Clientes y datos de relación: razón social, nombre comercial, NIF, categoría (ENUM), industria, sede, contacto, fecha de onboarding, account manager (FK a `employees`), riesgo y moneda de facturación. PK: `client_id`.

* **client_offices**
  Sedes del cliente: nombre de sitio, ciudad, dirección, tamaño y contacto local. FK a `clients`. PK: `client_office_id`.

* **engagements**
  Contratos/servicios en curso: cliente (FK), línea de servicio (FK), lead consultant (FK a `employees`), fechas, estado (ENUM), fee/retainer, frecuencia de facturación, descripción y probabilidad de renovación. PK: `engagement_id`.

* **engagement_offices** *(tabla puente)*
  Relación N:M entre `engagements` y `offices` para indicar en qué oficinas se ejecuta cada compromiso. PK compuesta `(engagement_id, office_id)`.

* **compliance_cases**
  Casos de cumplimiento (p. ej., IVA trimestral, IS anual): engagement (FK), código único, tipo, ejercicio/periodo, vencimiento, estado y prioridad (ENUM), lead asignado (FK a `employees`) y notas. PK: `case_id`.

* **case_tasks**
  Tareas operativas de un caso: nombre, asignado (FK a `employees`), fecha límite, estado (check), fecha de cierre y comentarios. FK a `compliance_cases`. PK: `task_id`.

* **documents**
  Documentos subidos por caso: tipo, nombre de fichero, ruta de almacenamiento, fecha de subida y si está firmado. FK a `compliance_cases` y a `employees` (quien sube). PK: `document_id`.

* **tax_returns**
  Declaraciones tributarias (CIT, VAT, IRPF, SS, etc.): cliente (FK), *opcionalmente* caso relacionado (FK), ejercicio/periodo, importes (a pagar/pagado), fecha de presentación y estado (check). PK: `tax_return_id`.

* **payroll_reports**
  Informes de nómina mensuales: cliente (FK), *opcional* engagement (FK), mes reportado, nº empleados procesados, masa salarial, cotización SS, presentado por (FK a `employees`) y fecha de envío. PK: `payroll_report_id`.

* **financial_statements**
  Estados financieros (mensual/trimestral/anual): cliente (FK), *opcional* engagement (FK), periodo (inicio/fin), ingresos, gastos, costes de personal, provisión de impuestos; preparado por y aprobado por (FKs a `employees`) y fecha de aprobación. PK: `statement_id`.

* **invoices**
  Facturas emitidas por engagement: número único, fechas (emisión/vencimiento), total, estado (ENUM) y notas; emitida por (FK a `employees`). FK a `engagements`. PK: `invoice_id`.

* **invoice_items**
  Líneas de factura: descripción, cantidad, precio unitario y total calculado. FK a `invoices`. PK: `invoice_item_id`.

# Catálogos / ENUMs

* `client_category`: *corporate | sme | individual | public*
* `engagement_status`: *planning | active | on_hold | completed | cancelled*
* `case_status`: *scheduled | in_progress | waiting_client | submitted | closed*
* `case_priority`: *low | medium | high | critical*
* `invoice_status`: *draft | issued | paid | overdue | void*
* `statement_kind`: *monthly | quarterly | annual*
* `tax_kind`: *CIT | VAT | IRPF | SOCIAL_SECURITY | WITHHOLDING*

> Nota: varias tablas incluyen una columna `id` generada que duplica la PK (ej. `employees.id` = `employee_id`) para compatibilidad con consultas NL→SQL.
> Índices útiles ya creados: por oficina en empleados, gestor de cuenta en clientes, vencimientos de casos, mes en nóminas y rango en estados financieros.
