from flask import Blueprint, jsonify,Flask, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized, Forbidden
import requests
from google.cloud import firestore
import os
from datetime import datetime

receipt_blueprint = Blueprint("receipt", __name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
db = firestore.Client()
collection_name = 'receipt'

CORS(
    receipt_blueprint,
    resources={r"/*": {"origins": "*"}},
    origins=["*"],
)


@receipt_blueprint.route("/get-all", methods=["GET"])
def get_all():
    try:
        collection_ref = db.collection(collection_name) 
        query = collection_ref.where('ITEMS_MISSED', '==', True)
        docs = query.stream()
        results = []
        for doc in docs:
              data = doc.to_dict()
              results.append({
            'id': data.get('ID'),  # Firestore document ID
            'date': data.get('DATE').isoformat() if data.get('DATE') else None,
            'items_missed': data.get('ITEMS_MISSED'),
            'source_id': data.get('SOURCE_ID'),
                            })
        return jsonify(results), 200
    except BadRequest as e:
        raise BadRequest(str(e))
    except Exception as e:
        raise BadRequest("An error occurred during registration: " + str(e))

@receipt_blueprint.route("/getById/<string:custom_id>", methods=["GET"])
def get_by_id(custom_id):
    try:
        # Query documents where ID field matches
        query = db.collection(collection_name).where('ID', '==', custom_id).limit(1)
        results = query.stream()

        # Get the first matching document
        doc = next(results, None)

        if doc:
            data = doc.to_dict()
            return jsonify({
                'id': doc.id,  # Firestore-generated doc ID
                'date': data.get('DATE').isoformat() if data.get('DATE') else None,
                'items_missed': data.get('ITEMS_MISSED'),
                'source_id': data.get('SOURCE_ID'),
                'ID': data.get('ID')  # Include custom ID if you want
            })
        else:
            return jsonify({'error': 'Document with given ID not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
@receipt_blueprint.route('/addReceipts', methods=['POST'])
def add_item():
    data = request.get_json()

    # Basic validation
    required_fields = ['ID','DATE', 'ITEMS_MISSED', 'SOURCE_ID']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Convert date string to Firestore Timestamp
        date = datetime.fromisoformat(data['DATE'])

        # Create document
        doc_ref = db.collection(collection_name).add({
            'ID': data['ID'],  
            'DATE': date,
            'ITEMS_MISSED': bool(data['ITEMS_MISSED']),
            'SOURCE_ID': data['SOURCE_ID']
        })

        return jsonify({'message': 'Document added', 'id': doc_ref[1].id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@receipt_blueprint.route('/updateReceipts/<string:item_id>', methods=['PATCH'])
def update_item(item_id):
    data = request.get_json()
    
    allowed_fields = {'DATE', 'ITEMS_MISSED', 'SOURCE_ID'}
    update_data = {}

    try:
        # Validate and prepare update fields
        for field in data:
            if field not in allowed_fields:
                return jsonify({'error': f'Invalid field: {field}'}), 400
            if field == 'DATE':
                update_data['DATE'] = datetime.fromisoformat(data['DATE'])
            else:
                update_data[field] = data[field]
        query = db.collection(collection_name).where('ID', '==', item_id).limit(1)
        results = query.stream()
        doc = next(results, None)

        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        doc.reference.update(update_data)

        return jsonify({'message': f'Document with ID={item_id} updated successfully'}), 200

    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO 8601'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


    except Exception as e:
        return jsonify({'error': str(e)}), 500
