import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

def create_pdf():
    # Destino: Escritorio del usuario E-100
    desktop_path = r"C:\Users\E-100\Desktop\Contraseñas_iAgentPay.pdf"
    
    # Crear el Canvas PDF
    c = canvas.Canvas(desktop_path, pagesize=letter)
    width, height = letter
    
    # Dibujar Fondo / Cabecera
    c.setFillColor(HexColor('#0b0f19'))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    # Título Principal
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 60, "iAgent-Pay v8.5.0")
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 80, "Credenciales y Contraseñas Maestras")
    
    # Contenido - Sección 1: Tesorería
    c.setFillColor(HexColor('#000000'))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 150, "1. Contraseña del Dashboard (Tesorería)")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 170, "Uso: Requerida para cambiar las billeteras de comisiones (EVM, Solana, XRPL).")
    c.setFont("Courier-Bold", 14)
    c.setFillColor(HexColor('#cc0000'))
    c.drawString(50, height - 190, "Santsant2")
    
    # Contenido - Sección 2: Base de Datos VPS
    c.setFillColor(HexColor('#000000'))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 240, "2. Contraseña Base de Datos PostgreSQL (VPS)")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 260, "Uso: Requerida para conectarse a la Base de Datos iagent_db en el servidor en vivo.")
    c.setFont("Courier-Bold", 14)
    c.setFillColor(HexColor('#cc0000'))
    c.drawString(50, height - 280, "Santsantillan2-DB")
    
    # Contenido - Sección 3: Acceso SSH VPS
    c.setFillColor(HexColor('#000000'))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 330, "3. Contraseña de Acceso SSH (VPS Root)")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 350, "Uso: Credencial root para entrar al servidor (187.124.76.64).")
    c.setFont("Courier-Bold", 14)
    c.setFillColor(HexColor('#cc0000'))
    c.drawString(50, height - 370, "Santsantillan2-")
    
    # Disclaimer
    c.setFillColor(HexColor('#666666'))
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "IMPORTANTE: Guarda este documento en un lugar seguro. Contiene información confidencial.")
    
    c.save()
    print(f"PDF generado exitosamente en: {desktop_path}")

if __name__ == "__main__":
    create_pdf()
