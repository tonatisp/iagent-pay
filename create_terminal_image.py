from PIL import Image, ImageDraw, ImageFont
import os

def create_terminal_image():
    # Config
    width, height = 800, 400
    bg_color = (10, 10, 15) # Dark Blue/Black
    text_color = (50, 255, 50) # Matrix Green
    alert_color = (255, 50, 50) # Red
    
    img = Image.new('RGB', (width, height), bg_color)
    d = ImageDraw.Draw(img)
    
    # Try to load a code font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    lines = [
        "> agent = AgentPay(wallet, daily_limit=10.0)",
        "> agent.pay_agent('0xHacker...', 100.0)",
        " ",
        "Analyzing transaction...",
        "Checking Daily Limit (10.0 ETH)...",
        "⚠️  Spending 100.0 ETH exceeds limit!",
        " ",
        "🚨 SECURITY ALERT: BLOCKED",
        "Transaction rejected by Capital Guard.",
        "Your wallet is safe."
    ]

    y = 40
    for line in lines:
        if "🚨" in line or "⚠️" in line or "rejected" in line:
            fill = alert_color
        elif ">" in line:
            fill = (200, 200, 200) # White/Grey input
        else:
            fill = text_color
            
        d.text((40, y), line, fill=fill, font=font)
        y += 30

    # Draw a "Window" border
    d.rectangle([0, 0, width-1, height-1], outline=(50, 50, 70), width=5)
    
    # Save
    img.save("capital_guard_terminal.png")
    print("✅ Terminal image created.")

if __name__ == "__main__":
    create_terminal_image()
