# Demo IberConsulting: Gestión Fiscal y Laboral

La base de datos `fiscal_consulting_demo` modela los procesos internos de una firma española de asesoramiento fiscal, laboral y contable con oficinas repartidas por todo el país. Se ha diseñado para alimentar la demo del congreso, cubriendo desde la asignación de equipos hasta la facturación y el seguimiento de casos de cumplimiento.

## Esquema general
- **Oficinas y servicios**: `offices`, `service_lines`, `employees` describen la estructura interna y la especialización de la firma.
- **Clientes y ubicaciones**: `clients` y `client_offices` registran la cartera, puntos de contacto y oficinas del cliente.
- **Proyectos y casos**: `engagements`, `engagement_offices`, `compliance_cases` y `case_tasks` articulan la gestión de encargos y obligaciones concretas.
- **Documentación y entregables**: `documents`, `tax_returns`, `payroll_reports`, `financial_statements` almacenan los outputs claves hacia cliente y reguladores.
- **Facturación**: `invoices` e `invoice_items` cubren el flujo económico asociado a cada proyecto.
- **Catálogos**: se emplean tipos enumerados (`client_category`, `engagement_status`, etc.) para facilitar validaciones en la demo.

## Tablas y relaciones

### `offices`
- Define las sedes físicas en Madrid, Barcelona, Valencia y Sevilla.
- Relación 1:N con `employees` (cada empleado pertenece a una oficina) y con `engagement_offices` (qué oficina atiende un proyecto).

### `service_lines`
- Catálogo de líneas de servicio (Fiscal, Laboral, Contable, Gobierno corporativo).
- Relación 1:N con `employees` y `engagements` para reflejar especialización.

### `employees`
- Personal de la firma con rol, grado profesional, fecha de alta y asignaciones.
- FK hacia `offices` y `service_lines`.
- Referenciado por `clients.account_manager_id`, `engagements.lead_consultant_id`, `compliance_cases.assigned_lead_id`, `case_tasks.assigned_to_id`, `documents.uploaded_by`, `payroll_reports.submitted_by_id`, `financial_statements.prepared_by_id / approved_by_id` e `invoices.issued_by_id`.

### `clients`
- Información fiscal y de contacto de cada cliente (tipo, industria, gestor principal).
- Relación 1:N con `client_offices`, `engagements`, `tax_returns`, `payroll_reports` y `financial_statements`.

### `client_offices`
- Ubicaciones operativas de cada cliente con persona de contacto local.
- FK obligatoria a `clients` con borrado en cascada.

### `engagements`
- Contratos o proyectos en curso con datos de estado, fee recurrente, frecuencia de facturación y probabilidad de renovación.
- Relación N:1 con `clients`, `service_lines` y `employees` (consultor líder).
- Relación N:M con `offices` mediante `engagement_offices`.
- Origen de `compliance_cases`, `payroll_reports`, `financial_statements` e `invoices`.

### `engagement_offices`
- Tabla puente que indica qué oficinas intervienen en cada proyecto.
- Clave primaria compuesta (`engagement_id`, `office_id`).

### `compliance_cases`
- Casos concretos (declaraciones, auditorías, justificación de fondos) derivados de un proyecto.
- Incluye estado de trabajo, prioridad y consultor responsable.
- Relación 1:N con `case_tasks`, `documents` y `tax_returns` (vía FK opcional).

### `case_tasks`
- Tareas operativas dentro de cada caso con responsable, estado y comentarios de seguimiento.
- Se borran en cascada si se elimina el caso asociado.

### `documents`
- Repositorio lógico de entregables y soportes cargados durante los casos.
- Almacena metadatos de firma y ruta de almacenamiento (pensada para enlazar con un gestor documental en la demo).

### `tax_returns`
- Declaraciones fiscales (IVA, IS, Seguridad Social, retenciones) preparadas para los clientes.
- Pueden vincularse a un `compliance_case` concreto cuando el origen es un expediente.

### `payroll_reports`
- Informes periódicos de nómina enviados a cada cliente, con métricas clave (empleados procesados, coste de Seguridad Social).
- Vinculados al `engagement` laboral correspondiente.

### `financial_statements`
- Estados financieros elaborados para cada cliente: tipo (mensual, trimestral, anual), cifras clave y aprobadores internos.
- Registra quién elabora y quién aprueba el informe, reforzando trazabilidad para la demo.

### `invoices`
- Facturas emitidas contra cada proyecto con estado (`paid`, `issued`, etc.).
- Referencia al consultor que la emite y sirve como cabecera para el detalle de conceptos.

### `invoice_items`
- Desglose línea a línea de cada factura con cálculo automático (`line_total`).
- Se destruye en cascada al eliminar la factura.

## Ejemplos de navegación de datos
1. **Panorama por cliente**: `clients` → `engagements` → `compliance_cases` y `invoices` permite mostrar en la demo la foto completa de obligaciones y facturación.
2. **Control de calidad interno**: `compliance_cases` + `case_tasks` + `documents` ofrece trazabilidad sobre quién hizo qué y cuándo.
3. **Seguimiento económico**: `financial_statements` junto con `invoices` demuestra cómo se integra la información contable del cliente con la facturación del despacho.

## Consideraciones para la demo
- Los tipos enumerados garantizan integridad de estados y facilitan filtros en la interfaz.
- Se incluyen índices en tablas críticas (`employees`, `clients`, `compliance_cases`, `payroll_reports`, `financial_statements`) para que las consultas de LangChain muestren tiempos de respuesta ágiles durante la presentación.
- Los datos de ejemplo cubren varios sectores (tecnología, servicios, salud, administración, creativo) y distintas situaciones operativas (casos en progreso, en espera del cliente, facturas pagadas y vencidas) para enriquecer los escenarios de demostración.
