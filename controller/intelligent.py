from flask import Blueprint, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from google.cloud import firestore
import os
from service.receipt import getAllReceipts, getReceiptById, addReceipt, update_receipt
from service.invoice_categorization import extract_invoices_from_files
from dotenv import load_dotenv

load_dotenv(override=True)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

intelligent_blueprint = Blueprint("intelligent", __name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
db = firestore.Client()
collection_name = 'receipt'
api_key = GEMINI_API_KEY


CORS(
    intelligent_blueprint,
    resources={r"/*": {"origins": "*"}},
    origins=["*"],
)


@intelligent_blueprint.route('/categorize-receipts', methods=['POST'])
def categorize_receipt():
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        file_list = [(file, file.filename) for file in files]
        result = extract_invoices_from_files(api_key, file_list)
        return jsonify(result), 200
    except BadRequest as e:
        raise BadRequest(str(e))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# @intelligent_blueprint.route('/xx', methods=['POST'])
# def categorize_receipt():
#     try:

#         return jsonify(xx), 200
#     except BadRequest as e:
#         raise BadRequest(str(e))
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
