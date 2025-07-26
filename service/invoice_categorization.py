import os
import json
import re
import tempfile
from PIL import Image
import fitz  # PyMuPDFservice/invoice_categorization.py
import google.generativeai as genai

def extract_invoices_from_files(
    api_key: str,
    file_list: list,
    valid_extensions=(".png", ".jpg", ".jpeg", ".webp", ".pdf")
):
    # Setup Gemini API
    genai.configure(api_key=api_key)
    vision_model = genai.GenerativeModel("gemini-2.5-pro")

    def clean_json_response(text):
        match = re.search(r"```json(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        try:
            first_brace = text.index("{")
            last_brace = text.rindex("}")
            return text[first_brace:last_brace + 1].strip()
        except ValueError:
            return text.strip()

    def extract_text_from_pdf(file_path):
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"❌ Failed to read PDF {file_path}: {e}")
            return ""

    def process_with_gemini(input_data, filename, is_image=True):
        if is_image:
            prompt = """You are an expert invoice analyzer.
            From the invoice image, extract the following details in JSON format:
            ```json
            {
  "biller_name": "<name of the person/shop/organization who issued the billed>",
  "billing_date": "<date of the bill in YYYY-MM-DD format if available>",
  "category": "<automatically determined category, such as grocery, rent, utility, food, etc.>",
  "items": [
    {"item": "<item name>", "price": "<price>"}
  ],
  "total": "<total amount>"
}
```"""

            try:
                response = vision_model.generate_content([prompt, input_data])
                raw_text = response.text.strip()
            except Exception as e:
                print(f"❌ Gemini image processing failed for {filename}: {e}")
                return {"file": filename, "error": str(e)}
        else:
            prompt = f"""You are an expert invoice parser.

From the following invoice text, extract the following details in JSON format:

```json
{{
  "biller_name": "<name of the person/shop/organization who issued the bill>",
  "billing_date": "<date of the bill in YYYY-MM-DD format if available>",
  "category": "<automatically determined category, such as grocery, rent, utility, food, etc.>",
  "items": [
    {{"item": "<item name>", "price": "<price>"}}
  ],
  "total": "<total amount>"
}}
Invoice text:
{text}
"""
            try:
                response = vision_model.generate_content(prompt)
                raw_text = response.text.strip()
            except Exception as e:
                print(f"❌ Gemini text processing failed for {filename}: {e}")
                return {"file": filename, "error": str(e)}

        cleaned_text = clean_json_response(raw_text)
        try:
            invoice_info = json.loads(cleaned_text)
        except json.JSONDecodeError:
            print(f"⚠️ Could not parse JSON for {filename}. Raw output saved.")
            return {
                "file": filename,
                "biller_name": "unknown",
                "billing_date": "unknown",
                "category": "unknown",
                "items": {},
                "total": "unknown",
                "raw_response": raw_text
            }

        # ✅ Convert items list to dictionary
        if isinstance(invoice_info.get("items"), list):
            invoice_info["items"] = {
                item.get("item", f"item_{i}"): item.get("price", "unknown")
                for i, item in enumerate(invoice_info["items"])
                if isinstance(item, dict)
            }

        invoice_info["file"] = filename
        return invoice_info

    all_invoice_data = []

    for file_obj, filename in file_list:
        ext = os.path.splitext(filename)[-1].lower()
        if ext not in valid_extensions:
            all_invoice_data.append({"file": filename, "error": "Unsupported file type"})
            continue

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file_obj.save(tmp.name)
                temp_path = tmp.name

            if ext == ".pdf":
                text = extract_text_from_pdf(temp_path)
                if text.strip():
                    invoice_info = process_with_gemini(text, filename, is_image=False)
                else:
                    invoice_info = {"file": filename, "error": "Empty or unreadable PDF"}
            else:
                with Image.open(temp_path) as image:
                    invoice_info = process_with_gemini(image, filename, is_image=True)

            all_invoice_data.append(invoice_info)

        except Exception as e:
            all_invoice_data.append({"file": filename, "error": f"Failed to process: {e}"})

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return all_invoice_data
