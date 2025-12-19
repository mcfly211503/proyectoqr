from flask import Flask, request, jsonify, send_from_directory
import os
import segno
import resend
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route('/procesar', methods=['POST'])
def procesar():
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
        qr.save(base_path, scale=15, dark="#24d900", light="#ffffff")

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

        # 2. Configurar Resend
        resend.api_key = os.getenv("RESEND_API_KEY")
        
        # Leemos los archivos para adjuntar
        with open(output_filename, "rb") as f:
            pdf_data = list(f.read())
        with open(base_path, "rb") as f:
            image_data = list(f.read())

        # 3. Enviar con Resend
        params = {
            "from": "Arturo Maldonado <noreply@arturomaldonadoportafolio.space>",
            "to": correo,
            "subject": "Tu Código QR solicitado",
            "html": f"""
                <h3>¡Hola {nombre_original}!</h3>
                <p>Adjunto encontrarás el código QR en formato imagen y el documento PDF que generaste.</p>
                <p>Saludos,<br>Arturo Maldonado</p>
            """,
            "attachments": [
                {
                    "filename": f"qr_pdf_{nombre}.pdf",
                    "content": pdf_data,
                },
                {
                    "filename": f"qr_imagen_{nombre}.png",
                    "content": image_data,
                }
            ]
        }

        resend.Emails.send(params)

        # Limpieza
        if os.path.exists(base_path): os.remove(base_path)
        if os.path.exists(output_filename): os.remove(output_filename)

        print(f"✅ Éxito: Procesado para {nombre_original}")
        return jsonify({"status": "ok", "message": "Proceso completado"}), 200

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
