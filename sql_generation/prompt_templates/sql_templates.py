simple_criterion = '''**Criteria:**
Simple SQL queries may satisfy one or more of the following criteria:
- Simple queries should select data from a single table only.
- Basic aggregate functions are permitted, such as `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.
- No joins are allowed; the query must operate on a single table.

**Example of Simple SQL Query:**
```sql
SELECT name, department_name
FROM employees
WHERE level > 5
ORDER BY age DESC;
```'''

moderate_criterion = '''**Criteria:**
Moderate SQL queries may satisfy one or more of the following criteria:
- Involves table joins, such as `JOIN`, `INNER JOIN`, `LEFT JOIN`, `CROSS JOIN`, etc.
- Includes subqueries within the `SELECT` or `WHERE` clauses.
- Utilizes aggregate functions alongside a `GROUP BY` clause.
- Contains complex `WHERE` conditions, including `IN`, `BETWEEN`, `LIKE`.
- Incorporate a `HAVING` clause to filter aggregated results.
- Uses aggregate functions like `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, etc.

**Example of Moderate SQL Query:**
```sql
SELECT e.name, d.department_name, AVG(s.salary) AS average_salary
FROM employees e
INNER JOIN departments d ON e.department_id = d.department_id
LEFT JOIN salaries s ON e.employee_id = s.employee_id
WHERE e.age > 30 AND e.status = 'active'
GROUP BY e.name, d.department_name
HAVING AVG(s.salary) > 50000;
```'''

complex_criterion = '''**Criteria:**
Complex SQL queries may satisfy one or more of the following criteria:
- Contains complex nested subqueries.
- Utilizes multiple types of joins, including self-joins.
- Includes window functions, such as `ROW_NUMBER`, `RANK`, etc.
- Uses Common Table Expressions (CTEs) for improved readability.
- Combines multiple aggregate functions.
- Involves complex `WHERE` and `HAVING` clauses with multiple conditions.
- Utilizes advanced functions and operators.

**Example of Complex SQL Query:**
```sql
WITH EmployeeCTE AS (
    SELECT employee_id, name, department_id, ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank
    FROM employees
)
SELECT e.name, d.department_name
FROM EmployeeCTE e
INNER JOIN departments d ON e.department_id = d.department_id
WHERE e.rank <= 3;
```'''

highly_complex_criterion = '''**Criteria:**
Highly complex SQL queries may satisfy one or more of the following criteria:
- Includes multiple Common Table Expressions (CTEs) for readability.
- Combines nested subqueries and various joins.
- Utilizes recursive CTEs for hierarchical or recursive queries.
- Extensively uses advanced window functions.
- May involve `UNION` or `UNION ALL` to combine result sets.
- Implements complex logic with advanced analytical functions.
- Employs a wide range of SQL clauses and conditions.
- Utilizes a broad spectrum of SQL functions and advanced features.

**Example of Highly Complex SQL Query:**
```sql
WITH RECURSIVE EmployeeHierarchy AS (
    SELECT employee_id, name, manager_id, department_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.employee_id, e.name, e.manager_id, e.department_id, eh.level + 1
    FROM employees e
    JOIN EmployeeHierarchy eh ON e.manager_id = eh.employee_id
),
DepartmentSalaries AS (
    SELECT eh.employee_id, eh.name, eh.level, d.department_name, s.salary, d.department_id
    FROM EmployeeHierarchy eh
    INNER JOIN departments d ON eh.department_id = d.department_id
    INNER JOIN salaries s ON eh.employee_id = s.employee_id
),
DepartmentStats AS (
    SELECT 
        d.department_id,
        COUNT(e.employee_id) AS employee_count,
        AVG(s.salary) AS average_salary
    FROM employees e
    INNER JOIN salaries s ON e.employee_id = s.employee_id
    INNER JOIN departments d ON e.department_id = d.department_id
    GROUP BY d.department_id
)
SELECT ds.name, ds.level, 
    SUM(ds.salary) OVER (PARTITION BY ds.department_id ORDER BY ds.level, ds.name) AS cumulative_salary
FROM DepartmentSalaries ds
INNER JOIN DepartmentStats dstat ON ds.department_id = dstat.department_id
ORDER BY ds.level, ds.name;
```'''

complexity2criterion = {
    "Simple": simple_criterion,
    "Moderate": moderate_criterion,
    "Complex": complex_criterion,
    "Highly Complex": highly_complex_criterion
}