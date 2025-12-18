from flask import Flask, request, jsonify, send_from_directory # Agregamos send_from_directory
import smtplib
import os
import segno
from PIL import Image
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route('/procesar', methods=['POST'])
def procesar():
    # --- TODO ESTO DEBE TENER 4 ESPACIOS HACIA LA DERECHA ---
    try:
        # 1. Recibimos el JSON
        datos = request.json
        nombre_original = datos.get('nombre')
        correo = datos.get('correo')
        url_para_qr = datos.get('url_qr')

        nombre = nombre_original.replace(" ", "_")
        data = url_para_qr

        # Directorios
        directorios_base = os.getcwd()
        folder_path = os.path.join(directorios_base, "temp_files")
        os.makedirs(folder_path, exist_ok=True)

        base_path = os.path.join(folder_path, f"qr_base_{nombre}.png")

        # Generar QR
        qr = segno.make_qr(data, error='h')
        qr.save(base_path, scale=15, dark="#24ff50", light="#001a05")

        
        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, text="Su link esta listo", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

        if os.path.exists(base_path):
            pdf.image(base_path, x=50, y=50, w=100)

        folder_temp = os.path.join(os.getcwd(), "archivos_generados")
        os.makedirs(folder_temp, exist_ok=True)
        output_filename = os.path.join(folder_temp, f"qr_pdf_{nombre}.pdf")
        pdf.output(output_filename)

        # Configurar Email (Variables de entorno de Render)
        email_emisor = os.getenv("EMAIL_USER")
        contra = os.getenv("EMAIL_PASS")
        
        subject = "Generacion de QR"
        message = f"Hola {nombre_original}, aqui tiene el qr que solicito."

        msg = MIMEMultipart()
        msg['From'] = email_emisor
        msg['To'] = correo
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Adjuntar PDF
        with open(output_filename, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename=qr_pdf_{nombre}.pdf')
        msg.attach(part)

        # Enviar
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_emisor, contra)
        server.sendmail(email_emisor, correo, msg.as_string())
        server.quit()

        # Limpieza
        if os.path.exists(base_path): os.remove(base_path)
        if os.path.exists(output_filename): os.remove(output_filename)

        print(f"✅ Éxito: Procesado para {nombre_original}")
        return jsonify({"status": "ok", "message": "Proceso completado"}), 200

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# FUERA de la función
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)




