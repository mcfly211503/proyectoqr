from flask import Flask, request, jsonify
import smtplib
import os
from xml.etree.ElementTree import tostring
import segno
from PIL import Image
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask_cors import CORS # Importante para que el HTML pueda hablar con el Python
# Importa aquí tus librerías de QR y correo (seguro usas qrcode, fpdf, smtplib, etc.)

app = Flask(__name__)
CORS(app) # Esto permite que tu HTML (desde GitHub Pages o local) acceda a Render

@app.route('/procesar', methods=['POST'])
def procesar():
    # 1. Recibimos el JSON en lugar de usar input()
    datos = request.json
    
    nombre = datos.get('nombre')
    correo = datos.get('correo')
    url_para_qr = datos.get('url_qr')



nombre = nombre.replace(" ", "_")
data= url_para_qr

# Obtiene la carpeta donde está corriendo tu script (en Render o en tu PC)
directorios_base = os.getcwd()

# Creamos una carpeta temporal si no existe (opcional pero recomendado)
folder_path = os.path.join(directorios_base, "temp_files")
os.makedirs(folder_path, exist_ok=True)

# Rutas universales (funcionan en Windows, Linux/Render)
base_path = os.path.join(folder_path, f"qr_base_{nombre}.png")
final_path = os.path.join(folder_path, f"qr_con_logo_{nombre}.png")

qr = segno.make_qr(data, error='h')
qr.save(
    base_path,
    scale=15,
    dark="#24ff50",
    light="#001a05",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logo_path = os.path.join(BASE_DIR, "imagenes", "barca.png")

# Ahora abres la imagen normalmente
logo = Image.open(logo_path).convert("RGBA")

logo_size = int(qr_img.size[0] * 0.23)
logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

pos = (
    (qr_img.size[0] - logo_size) // 2,
    (qr_img.size[1] - logo_size) // 2,
)

qr_img.paste(logo, pos, logo)
qr_img.save(final_path)

os.remove(base_path)



pdf = FPDF()


pdf.add_page()


pdf.set_font("Helvetica", size=12)
pdf.cell(200, 10, text="Su link esta listo", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

image_path = final_path 

if os.path.exists(image_path):

    pdf.image(image_path, x=50, y=50, w=100)
else:
    print(f"Error: Image file not found at '{image_path}'")


folder_temp = os.path.join(os.getcwd(), "archivos_generados")

# 2. Creamos la carpeta si no existe (importante para que no dé error)
if not os.path.exists(folder_temp):
    os.makedirs(folder_temp)

# 3. Definimos la ruta del PDF usando esa carpeta
output_filename = os.path.join(folder_temp, f"qr_pdf_{nombre}.pdf")

# 4. Guardamos el PDF
pdf.output(output_filename)

print(f"Archivo guardado temporalmente en: {output_filename}")



email = os.getenv("EMAIL_USER")
contra= os.getenv("EMAIL_PASS")
receiver_email = correo

subject = "Generacion de QR"
message = "Aqui tiene el qr que solicito"

# Preparar correo
msg = MIMEMultipart()
msg['From'] = email
msg['To'] = receiver_email
msg['Subject'] = subject

# Cuerpo del correo
msg.attach(MIMEText(message, 'plain'))

# Adjuntar PDF
with open(output_filename, "rb") as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', f'attachment; filename=qr_pdf_{nombre}.pdf')
msg.attach(part)

#adjuntar imagen
with open(final_path, "rb") as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', f'attachment; filename=qr_imagen_{nombre}.png')
msg.attach(part)

# Conectar al servidor y enviar
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(email, contra)
server.sendmail(email, receiver_email, msg.as_string())
server.quit()

os.remove(final_path)
os.remove(output_filename)

print(f"Procesando para: {nombre}, Correo: {correo}")
    
    # Respondemos al HTML que todo salió bien
return jsonify({"status": "ok", "message": "Proceso completado"}), 200

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
