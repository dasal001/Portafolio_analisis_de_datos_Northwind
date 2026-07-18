-- 1 ver tablas
SHOW TABLES;

-- 2 VER DESCRIPCION
use northwind;

DESCRIBE orders;
DESCRIBE CUSTOMERS;
DESCRIBE PRODUCTS;
DESCRIBE inventory_transactions;

-- 3 CUENTA LOS NUMEROS DE REGISTROS DE CADA TABLA
select 'Clientes' AS tabla, count(*) as cantidad from customers
union all 
select 'Pedidos', count(*) from orders
union all 
select 'Productos', count(*) from products
union all 
select 'Inventarios de transaccion', count(*) from inventory_transactions;

-- 4 CONTAR LA CANTIDADN DE PRODUCTOS POR CATEGORIA
SELECT category, count(*) as total_productos from products
group by category
order by total_productos DESC;

-- Analisis
-- 1.- top 10 productos mas vendidos por cantidad
select p.product_name as nombre_producto, sum(o.quantity) as cantidad
from products p 
join order_details o on o.product_id = p.id
group by p.product_name
order by cantidad desc
limit 10;

-- 2.- Ingreso total que genero cada cliente ordenado DESC
select 
	CONCAT(c.first_name, ' ', c.last_name) AS Nombres , 
    round(sum(od.quantity * od.unit_price * (1 - od.discount))) as Ingreso_Total -- calculo del ingreso con el descuento incluido
from customers c
join orders o on c.id = o.customer_id
join order_details od on o.id = od.order_id
group by c.id -- agrupo por id por que pueden existir nombres iguales
order by Ingreso_Total desc;

-- 3.- Empleado que cerro mas ventas y cuanto ingreso genero cada uno
Select 
	CONCAT(e.first_name, ' ', e.last_name) AS Nombres,
    COUNT(DISTINCT o.id) AS Total_Pedidos,
	round(sum(od.quantity * od.unit_price * (1 - od.discount))) as Ingreso_Total
from employees e 
join orders o on e.id = o.employee_id
join order_details od on o.id = od.order_id
group by e.id
order by Ingreso_Total Desc;

-- 4.- El transportista(Shipper) mas utilizado y el costo promedio de envio
select 
	s.company as compañia,-- decidi analisar la compañia ya que los registros del nombre y apellido estaban nulos en la tabla
    count(o.id) as total_envios,
    ROUND(AVG(o.shipping_fee), 2) AS promedio_envio,
    ROUND(SUM(o.shipping_fee), 2) AS ingreso_total_envios
from shippers s
join orders o on s.id = o.shipper_id
group by s.id, s.company
order by total_envios desc;

-- 5.- Evolucion de ventas mes a mes durante todo el periodo
select 
	year(order_date) as Año,
	monthname(order_date) as Mes,
	round(sum(od.quantity * od.unit_price * (1 - od.discount))) as Ingreso_Total
from orders o 
join order_details od on o.id = od.order_id
group by year(o.order_date),monthname(o.order_date);

-- 6.- Categoria de productos que genera mas ingresos
SELECT 
    p.category,
    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount))) AS Ingreso_Total,
    ROUND(
        SUM(od.quantity * od.unit_price * (1 - od.discount)) /
        (SELECT SUM(od.quantity * od.unit_price * (1 - od.discount)) 
         FROM order_details od) * 100, 1
    ) AS Porcentaje
FROM products p 
JOIN order_details od ON p.id = od.product_id
GROUP BY p.category
ORDER BY Ingreso_Total DESC;

-- 7.-Productos con stock bajo el nivel de reorden que aun nontiene una orden de compra activa
SELECT 
    p.product_name AS Producto,
    p.reorder_level AS Nivel_Reorden,
    p.target_level AS Nivel_Objetivo
FROM products p
LEFT JOIN purchase_order_details pod ON p.id = pod.product_id
LEFT JOIN purchase_orders po ON pod.purchase_order_id = po.id
WHERE po.id IS NULL
ORDER BY p.product_name;

-- 8.- tiempo promedio entre fecha de orden y fecha de envio por compañia de transporte
select 
	s.company,
    round(avg(datediff( o.shipped_date,o.order_date)),1) as Dias_Promedio_Envio
from orders o
join shippers s on o.shipper_id = s.id
group by s.company
order by Dias_Promedio_Envio desc;

