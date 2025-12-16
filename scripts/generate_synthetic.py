
import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_native_invoice(path):
    doc = fitz.open()
    page = doc.new_page()
    
    # Title
    page.insert_text((50, 50), "INVOICE #12345", fontsize=24, color=(0, 0, 0))
    page.insert_text((50, 80), "Date: 2024-10-25", fontsize=12)
    
    # Vendor Info
    page.insert_text((50, 110), "Vendor: Synthetic Supplies Co.", fontsize=12)
    page.insert_text((50, 125), "Address: 123 Fake St, Simenton, CA 90210", fontsize=12)
    
    # Customer Info
    page.insert_text((300, 110), "Bill To: John Doe", fontsize=12)
    page.insert_text((300, 125), "Address: 456 Null Ave, Testville, NY 10001", fontsize=12)
    
    # Header
    y_start = 160
    page.draw_line((50, y_start), (550, y_start))
    page.insert_text((50, y_start + 15), "Item Description", fontsize=12)
    page.insert_text((350, y_start + 15), "Qty", fontsize=12)
    page.insert_text((450, y_start + 15), "Price", fontsize=12)
    page.insert_text((520, y_start + 15), "Total", fontsize=12)
    page.draw_line((50, y_start + 20), (550, y_start + 20))
    
    # Items
    items = [
        ("Widget A", 2, 10.00),
        ("Gadget B (Red)", 1, 25.50),
        ("Service Fee", 1, 50.00),
    ]
    
    y = y_start + 40
    total = 0
    for desc, qty, price in items:
        line_total = qty * price
        total += line_total
        page.insert_text((50, y), desc, fontsize=12)
        page.insert_text((350, y), str(qty), fontsize=12)
        page.insert_text((450, y), f"${price:.2f}", fontsize=12)
        page.insert_text((520, y), f"${line_total:.2f}", fontsize=12)
        y += 20
        
    # Total
    y += 10
    page.draw_line((50, y), (550, y))
    page.insert_text((450, y + 20), "Grand Total:", fontsize=12)
    page.insert_text((520, y + 20), f"${total:.2f}", fontsize=12)

    doc.save(path)
    print(f"Created native invoice: {path}")

def create_fake_scanned_doc(path):
    # create an image first using PIL
    img = Image.new('RGB', (1200, 1600), color='white')
    d = ImageDraw.Draw(img)
    
    # We don't have a guaranteed font file, so load default or try basic system font
    # PIL default font is variable size, usually small.
    # Let's just draw text. 
    try:
        font = ImageFont.truetype("Arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()

    d.text((100, 100), "SCANNED DOCUMENT (CONFIDENTIAL)", fill='black', font=font)
    d.text((100, 200), "This is a simulated scanned document.", fill='black', font=font)
    d.text((100, 250), "It contains text that exists only as pixels.", fill='black', font=font)
    d.text((100, 300), "The OCR engine should find this text.", fill='black', font=font)
    
    # Add some noise/artifacts if we wanted, but sticking to clean image for now
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Insert image into PDF
    import io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    page.insert_image(page.rect, stream=img_byte_arr.getvalue())
    
    doc.save(path)
    print(f"Created fake scanned doc: {path}")

def create_table_doc(path):
    doc = fitz.open()
    page = doc.new_page()
    
    page.insert_text((50, 40), "Performance Metrics Table", fontsize=18)
    
    # Draw a visual grid
    rows = 6
    cols = 4
    x_start = 50
    y_start = 80
    col_width = 120
    row_height = 30
    
    headers = ["Metric", "Q1", "Q2", "Q3"]
    data = [
        ["Revenue", "100k", "120k", "110k"],
        ["Cost", "50k", "55k", "52k"],
        ["Profit", "50k", "65k", "58k"],
        ["Users", "1000", "1200", "1150"],
        ["Churn", "5%", "4%", "4.5%"],
    ]

    # Draw horizontal lines
    for i in range(rows + 1):
        y = y_start + i * row_height
        page.draw_line((x_start, y), (x_start + cols * col_width, y))
        
    # Draw vertical lines
    for j in range(cols + 1):
        x = x_start + j * col_width
        page.draw_line((x, y_start), (x, y_start + rows * row_height))
        
    # Fill text
    # Headers
    for j, h in enumerate(headers):
        x = x_start + j * col_width + 10
        y = y_start + 20
        page.insert_text((x, y), h, fontsize=12)
        
    # Data
    for i, row in enumerate(data):
        y = y_start + (i + 1) * row_height + 20
        for j, val in enumerate(row):
            x = x_start + j * col_width + 10
            page.insert_text((x, y), val, fontsize=12)

    doc.save(path)
    print(f"Created table doc: {path}")

def main():
    out_dir = "in_synthetic"
    ensure_dir(out_dir)
    
    create_native_invoice(os.path.join(out_dir, "synthetic_native_invoice.pdf"))
    create_fake_scanned_doc(os.path.join(out_dir, "synthetic_scanned_doc.pdf"))
    create_table_doc(os.path.join(out_dir, "synthetic_table.pdf"))
    print("Done. Synthetic PDFs created in 'in_synthetic/'")

if __name__ == "__main__":
    main()
