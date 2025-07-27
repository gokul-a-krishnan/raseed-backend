from flask import Blueprint, jsonify,Flask, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from google.cloud import firestore
import os
from service.receipt import getAllReceipts,getReceiptById, addReceipt,update_receipt
from service.invoice_categorization import extract_invoices_from_files

receipt_blueprint = Blueprint("receipt", __name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
db = firestore.Client()
collection_name = 'receipt'

CORS(
    receipt_blueprint,
    resources={r"/*": {"origins": "*"}},
    origins=["*"],
)

@receipt_blueprint.route('/add-receipts', methods=['POST'])
def add_item():
    data = request.get_json()
    try:    
        return addReceipt(data), 200   
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@receipt_blueprint.route("/get-all", methods=["GET"])
def get_all():
    try:
        return getAllReceipts(),200
    except BadRequest as e:
        raise BadRequest(str(e))
    except Exception as e:
        raise BadRequest("An error occurred during registration: " + str(e))

@receipt_blueprint.route("/get-by-id/<string:custom_id>", methods=["GET"])
def get_by_id(custom_id):
    try:
        return getReceiptById(custom_id),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    
@receipt_blueprint.route('/update-receipts/<string:item_id>', methods=['PATCH'])
def update_item(item_id):
    data = request.get_json()
    try:
        return update_receipt(data,item_id), 200
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO 8601'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500