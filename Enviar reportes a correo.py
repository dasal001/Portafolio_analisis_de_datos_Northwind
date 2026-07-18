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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
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

# Carga de datos
df_productos = pd.read_sql("""
    SELECT p.product_name AS Producto, SUM(od.quantity) AS Cantidad
    FROM products p
    JOIN order_details od ON p.id = od.product_id
    GROUP BY p.product_name
    ORDER BY Cantidad DESC
    LIMIT 10
""", conn)

df_clientes = pd.read_sql("""
    SELECT concat(c.first_name , " " , c.last_name) AS Cliente,
    ROUND(SUM(od.quantity * od.unit_price * (1 - od.discount))) AS Ingreso_Total
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    JOIN order_details od ON o.id = od.order_id
    GROUP BY c.id, Cliente
    ORDER BY Ingreso_Total DESC
""", conn)

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

# Gráfico 2: Embudo simulado - Ingresos por cliente
fig2, ax2 = plt.subplots(figsize=(10, 8))
ax2.barh(
    df_clientes["Cliente"],
    df_clientes["Ingreso_Total"],
    color=[plt.cm.Blues(0.4 + 0.6 * i / len(df_clientes))
           for i in range(len(df_clientes))]
)
ax2.set_title("Ingresos Totales por Cliente", fontsize=14, fontweight="bold")
ax2.set_xlabel("Ingreso Total")
ax2.invert_yaxis()
plt.tight_layout()
plt.savefig("grafico_clientes.png", dpi=150)
plt.close()

print("✅ Gráficos generados")

# ── Generar PDF ──
fecha    = datetime.now().strftime("%d-%m-%Y")
ruta_pdf = f"reporte_northwind_{fecha}.pdf"
doc      = SimpleDocTemplate(ruta_pdf, pagesize=letter)
estilos  = getSampleStyleSheet()
contenido = []

# Título
contenido.append(Paragraph(f"<b>Reporte Northwind - {fecha}</b>", estilos["Title"]))
contenido.append(Spacer(1, 20))

# Tabla 1
contenido.append(Paragraph("<b>Top 10 Productos Más Vendidos</b>", estilos["Heading2"]))
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
contenido.append(Spacer(1, 20))

# Gráfico 1
contenido.append(Image("grafico_productos.png", width=450, height=220))
contenido.append(Spacer(1, 30))

# Tabla 2
contenido.append(Paragraph("<b>Ingresos Totales por Cliente</b>", estilos["Heading2"]))
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
contenido.append(Spacer(1, 20))

# Gráfico 2
contenido.append(Image("grafico_clientes.png", width=450, height=280))

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