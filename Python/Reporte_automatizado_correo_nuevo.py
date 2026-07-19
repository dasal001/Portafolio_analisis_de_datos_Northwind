import pandas as pd
import os
import mysql.connector
import smtplib
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

# ─────────────────────────────────────────
REMITENTE    = "darylasv.xd@gmail.com"
CONTRASENA   = "ftit jwxe bmmb vgdq"
DESTINATARIO = "darylpythonprueba@gmail.com"
# ─────────────────────────────────────────

# Conexión a MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="kamisama.1",
    database="northwind"
)
print("✅ Conexión exitosa")

# Directorio de trabajo
directorio = r"C:\Users\Daryl Salinas\Desktop\Portafolio"
os.chdir(directorio)
print("Directorio actual:", os.getcwd())

# ── Carga de datos ──

# Top 10 productos por cantidad
df_productos = pd.read_sql("""
    select p.product_name as Producto, sum(o.quantity) as Cantidad
    from products p 
    join order_details o on o.product_id = p.id
    group by p.product_name
    order by Cantidad desc
    limit 10;
""", conn)

# Top 5 clientes por ingreso total (para igualar el visual de Power BI)
df_clientes = pd.read_sql("""
    select 
	CONCAT(c.first_name, ' ', c.last_name) AS Cliente , 
    round(sum(od.quantity * od.unit_price * (1 - od.discount))) as Ingreso_Total -- calculo del ingreso con el descuento incluido
    from customers c
    join orders o on c.id = o.customer_id
    join order_details od on o.id = od.order_id
    group by c.id -- agrupo por id por que pueden existir nombres iguales
    order by Ingreso_Total desc
    LIMIT 5
""", conn)

# Evolución mensual de ventas (Ingreso_Total por mes)
df_evolucion = pd.read_sql("""
    SELECT DATE_FORMAT(o.order_date, '%Y-%m') AS Mes,
    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount))) AS Ingreso_Total
    FROM orders o
    JOIN order_details od ON o.id = od.order_id
    GROUP BY Mes
    ORDER BY Mes
""", conn)

# KPIs generales (para las tarjetas del reporte)
kpi = pd.read_sql("""
    SELECT
    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount))) AS Ingreso_Total,
    SUM(od.quantity) AS Cantidad_productos
    FROM order_details od
""", conn)

ingreso_total_kpi = kpi["Ingreso_Total"].iloc[0]
cantidad_total_kpi = kpi["Cantidad_productos"].iloc[0]

conn.close()
print("✅ Datos cargados")

# ── Generar Gráficos ──

# Gráfico 1: Barras horizontales - Top 10 productos
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.barh(
    df_productos["Producto"],
    df_productos["Cantidad"],
    color="#2E4057"
)
ax1.set_title("Top 10 Productos Más Vendidos", fontsize=14, fontweight="bold")
ax1.set_xlabel("Cantidad")
ax1.invert_yaxis()
plt.tight_layout()
plt.savefig("grafico_productos.png", dpi=150)
plt.close()

# Gráfico 2: Barras horizontales - Ingresos por cliente (top 5)
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.barh(
    df_clientes["Cliente"],
    df_clientes["Ingreso_Total"],
    color=[plt.cm.Blues(0.4 + 0.6 * i / len(df_clientes))
           for i in range(len(df_clientes))]
)
ax2.set_title("Ingreso Total por Cliente (Top 5)", fontsize=14, fontweight="bold")
ax2.set_xlabel("Ingreso Total")
ax2.invert_yaxis()
plt.tight_layout()
plt.savefig("grafico_clientes.png", dpi=150)
plt.close()

# Gráfico 5: Línea - Evolución mensual de ventas
fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.plot(
    df_evolucion["Mes"],
    df_evolucion["Ingreso_Total"],
    marker="o",
    color="#1F77B4",
    linewidth=2
)
ax3.set_title("Evolución de Ventas Mes a Mes", fontsize=14, fontweight="bold")
ax3.set_xlabel("Mes")
ax3.set_ylabel("Ingreso Total")
ax3.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("grafico_evolucion.png", dpi=150)
plt.close()

print("✅ Gráficos generados")

# ── Generar PDF ──
fecha    = datetime.now().strftime("%d-%m-%Y")
ruta_pdf = f"reporte_northwind_{fecha}.pdf"
doc      = SimpleDocTemplate(ruta_pdf, pagesize=letter)
estilos  = getSampleStyleSheet()
contenido = []

# Título
contenido.append(Paragraph(f"<b>Reporte Northwind - Ventas y Cantidad</b>", estilos["Title"]))
contenido.append(Paragraph(f"Generado el {fecha}", estilos["Normal"]))
contenido.append(Spacer(1, 15))

# KPIs
kpi_texto = (
    f"<b>Ingreso_Total:</b> {ingreso_total_kpi:,.0f}"
    f"&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;"
    f"<b>Cantidad_productos:</b> {cantidad_total_kpi:,.0f}"
)
contenido.append(Paragraph(kpi_texto, estilos["Heading2"]))
contenido.append(Spacer(1, 20))

# Tabla 1 + Gráfico 1: Top productos
contenido.append(Paragraph("<b>1. Top 10 Productos Más Vendidos por Cantidad</b>", estilos["Heading2"]))
contenido.append(Spacer(1, 10))
datos1 = [df_productos.columns.tolist()] + df_productos.values.tolist()
tabla1 = Table(datos1, colWidths=[300, 100])
tabla1.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
    ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
    ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
    ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
    ("PADDING",    (0, 0), (-1, -1), 6),
]))
contenido.append(tabla1)
contenido.append(Spacer(1, 15))
contenido.append(Image("grafico_productos.png", width=450, height=220))
contenido.append(Spacer(1, 25))

# Tabla 2 + Gráfico 2: Ingreso por cliente
contenido.append(Paragraph("<b>2. Ingreso Total que Generó Cada Cliente</b>", estilos["Heading2"]))
contenido.append(Spacer(1, 10))
datos2 = [df_clientes.columns.tolist()] + df_clientes.values.tolist()
tabla2 = Table(datos2, colWidths=[300, 100])
tabla2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4057")),
    ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
    ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
    ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
    ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
    ("PADDING",    (0, 0), (-1, -1), 6),
]))
contenido.append(tabla2)
contenido.append(Spacer(1, 15))
contenido.append(Image("grafico_clientes.png", width=450, height=220))
contenido.append(Spacer(1, 25))

# Gráfico 5: Evolución mensual
contenido.append(Paragraph("<b>3. Evolución de Ventas Mes a Mes</b>", estilos["Heading2"]))
contenido.append(Spacer(1, 10))
contenido.append(Image("grafico_evolucion.png", width=450, height=180))
contenido.append(Spacer(1, 25))

# Conclusiones / Insights
contenido.append(Paragraph("<b>Conclusiones</b>", estilos["Heading2"]))
contenido.append(Spacer(1, 8))
insights = [
    "Coffee lidera las ventas por volumen muy por delante del resto, seguido de Beer, mostrando una fuerte concentración de la demanda en bebidas dentro del top 10.",
    "Se identificó que el 30% del ingreso depende de solo 2 clientes, sugiriendo una oportunidad de diversificación de cartera.",
    "Pico de abril impulsado por Beer: coincide con el National Beer Day (7 de abril, EE.UU.), fecha de alto consumo estacional en el mercado estadounidense.",
    "Tras el pico de abril, el ingreso cae y se estabiliza en niveles más bajos entre mayo y julio, sugiriendo que el repunte fue puntual y no se sostuvo en el tiempo.",
]
lista_insights = ListFlowable(
    [ListItem(Paragraph(texto, estilos["Normal"]), leftIndent=10) for texto in insights],
    bulletType="bullet",
    start="•",
)
contenido.append(lista_insights)

doc.build(contenido)
print(f"✅ PDF generado: {ruta_pdf}")

# ── Enviar correo ──
mensaje = MIMEMultipart()
mensaje["From"]    = REMITENTE
mensaje["To"]      = DESTINATARIO
mensaje["Subject"] = f"Reporte Northwind - {fecha}"

cuerpo = f"""
<html>
  <body>
    <h2>Reporte Northwind</h2>
    <p>Adjunto el reporte del <b>{fecha}</b>:</p>
    <ul>
      <li>Top 10 productos más vendidos</li>
      <li>Ingresos totales por cliente</li>
      <li>Evolución de ventas mes a mes</li>
    </ul>
    <p>Saludos,<br>Daryl</p>
  </body>
</html>
"""
mensaje.attach(MIMEText(cuerpo, "html"))

with open(ruta_pdf, "rb") as archivo:
    adjunto = MIMEBase("application", "octet-stream")
    adjunto.set_payload(archivo.read())
    encoders.encode_base64(adjunto)
    adjunto.add_header("Content-Disposition", f"attachment; filename={ruta_pdf}")
    mensaje.attach(adjunto)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
    servidor.login(REMITENTE, CONTRASENA)
    servidor.sendmail(REMITENTE, DESTINATARIO, mensaje.as_string())
    print(f"✅ Reporte enviado a {DESTINATARIO}")