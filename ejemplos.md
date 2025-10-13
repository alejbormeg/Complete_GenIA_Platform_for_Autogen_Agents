¡Claro! Basándome en tu esquema de `fiscal_consulting_demo` (tablas como `offices`, `employees`, `clients`, `engagements`, `compliance_cases`, `invoices`, `invoice_items`, etc.), aquí tienes 5 retos NL→SQL ordenados de menor a mayor dificultad, con una posible solución en SQL. Ajusta nombres de columnas si en tu DDL difieren (p.ej., `issued_at` vs `invoice_date`). 

---

## 1) Fácil — Listado simple con 1–2 joins

**NL**: “Lista el nombre y la línea de servicio de los empleados que trabajan en la oficina de Madrid.”
**SQL**:

```sql
SELECT e.full_name,
       sl.name AS service_line
FROM employees e
JOIN offices o           ON e.office_id = o.id
JOIN service_lines sl    ON e.service_line_id = sl.id
WHERE o.name = 'Madrid';
```

*(Relación offices→employees y employees→service_lines.)* 

---

## 2) Intermedia — Filtro por catálogo + deduplicación

**NL**: “Devuélveme los clientes que tienen al menos un engagement ACTIVO en la línea Fiscal, junto con su account manager.”
**SQL**:

```sql
SELECT DISTINCT c.name AS client_name,
       am.full_name AS account_manager
FROM clients c
JOIN engagements g         ON g.client_id = c.id
JOIN service_lines sl      ON g.service_line_id = sl.id
LEFT JOIN employees am     ON c.account_manager_id = am.id
WHERE sl.name = 'Fiscal'
  AND g.status = 'active';
```

*(Catálogo `service_lines`, estado del `engagement` y nexo con `clients`.)* 

---

## 3) Intermedia+ — Agregación por responsable y estado

**NL**: “¿Cuántos casos de cumplimiento abiertos o en progreso tiene cada consultor responsable, por estado?”
**SQL**:

```sql
SELECT lead.full_name AS responsible,
       cc.status,
       COUNT(*) AS cases_count
FROM compliance_cases cc
JOIN employees lead ON cc.assigned_lead_id = lead.id
WHERE cc.status IN ('open', 'in_progress')
GROUP BY lead.full_name, cc.status
ORDER BY lead.full_name, cc.status;
```

*(Trazabilidad de `compliance_cases` y su responsable.)* 

---

## 4) Avanzada — KPI económico por cliente con “paid vs pending”

**NL**: “Para cada cliente, dame el importe total **pagado** y **pendiente** (según el estado de la factura) sumando las líneas de factura.”
**SQL**:

```sql
SELECT c.name AS client_name,
       SUM(CASE WHEN i.status = 'paid'   THEN ii.line_total ELSE 0 END) AS amount_paid,
       SUM(CASE WHEN i.status <> 'paid'  THEN ii.line_total ELSE 0 END) AS amount_pending
FROM clients c
JOIN engagements g   ON g.client_id = c.id
JOIN invoices i      ON i.engagement_id = g.id
JOIN invoice_items ii ON ii.invoice_id = i.id
GROUP BY c.name
ORDER BY amount_pending DESC, amount_paid DESC;
```

*(Cadena cliente→engagements→invoices→invoice_items para seguimiento económico.)* 

---

## 5) Experta — CTE + ventana + filtro temporal

**NL**: “Top-5 consultores que **más facturación han emitido** en los últimos 12 meses, con su ranking y el total facturado.”
**SQL**:

```sql
WITH last_year_invoices AS (
    SELECT i.issued_by_id,
           ii.line_total
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_id = i.id
    WHERE i.issued_at >= (CURRENT_DATE - INTERVAL '12 months')
)
SELECT e.full_name AS consultant,
       SUM(lyi.line_total) AS total_billed,
       RANK() OVER (ORDER BY SUM(lyi.line_total) DESC) AS rnk
FROM last_year_invoices lyi
JOIN employees e ON e.id = lyi.issued_by_id
GROUP BY e.full_name
ORDER BY rnk
LIMIT 5;
```

*(Uso de CTE, ventana y fecha de emisión de la factura; ajusta `issued_at` si tu campo de fecha se llama distinto.)* 

---

Si quieres, te preparo un **CSV de prompts NL y sus SQL** para cargar en tu evaluador de NL2SQL, o los adapto al dialecto exacto de tu motor (Postgres, MySQL, etc.).



Preguntas finales:


¿Cómo evoluciona la facturación mensual (últimos 12 meses) por línea de servicio y cliente?

Top-10 clientes por importe facturado en el trimestre actual y su peso sobre el total (% de concentración).

Ticket medio por cliente (importe medio por factura) y nº de facturas por mes; resaltar variación MoM.

Facturas vencidas vs. pagadas vs. emitidas por mes (conteo e importe), separando overdue/paid/issued.

Tiempo desde el inicio del engagement hasta la primera factura por cliente (mediana por línea de servicio).