from flask import Blueprint, jsonify,Flask, request
from google.cloud import firestore
from datetime import datetime
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account.json"
db = firestore.Client()
collection_name = 'receipt'

def getAllReceipts():
    try:
        collection_ref = db.collection(collection_name) 
        query = collection_ref.where('ITEMS_MISSED', '==', True)
        docs = query.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()              
            # Handle date safely
            raw_date = data.get('DATE')
            iso_date = None
            if isinstance(raw_date, datetime):
                iso_date = raw_date.isoformat()
            elif isinstance(raw_date, str):
                try:
                    iso_date = datetime.fromisoformat(raw_date).isoformat()
                except ValueError:
                    iso_date = None

            # Normalize items field
            items_raw = data.get('ITEMS', {})
            items_list = []

            if isinstance(items_raw, dict):
                items_list = [
                    {"item": key, "price": value}
                    for key, value in items_raw.items()
                ]
            elif isinstance(items_raw, list):
                # Already a list of dicts, assume correct
                items_list = items_raw
            # else: leave items_list as []

              
            results.append({
            'id': data.get('ID'), 
            'biller_name': data.get('BILLER_NAME'),
            'date': iso_date,
            'bill_value': data.get('BILL_VALUE'),
            'items_missed': data.get('ITEMS_MISSED'),
            'source_id': data.get('SOURCE_ID'),
            'items':data.get('ITEMS', {})
                            })
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)})
    
def getReceiptById(custom_id):
       # Query documents where ID field matches
        query = db.collection(collection_name).where('ID', '==', custom_id).limit(1)
        results = query.stream()

        # Get the first matching document
        doc = next(results, None)

        if doc:
            data = doc.to_dict()
            return jsonify({
                'biller_name': data.get('BILLER_NAME'),
                'bill_value': data.get('BILL_VALUE'),
                'date': data.get('DATE').isoformat() if data.get('DATE') else None,
                'items_missed': data.get('ITEMS_MISSED'),
                'source_id': data.get('SOURCE_ID'),
                'ID': data.get('ID')  ,
                'items':data.get('ITEMS', {})

            })
        else:
            return jsonify({'error': 'Document with given ID not found'})

def addReceipt(data):
    # Basic validation
    required_fields = ['ID','BILLER_NAME','BILL_VALUE','DATE', 'ITEMS_MISSED', 'SOURCE_ID','ITEMS']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'})

    try:
        # Convert date string to Firestore Timestamp
        date = datetime.fromisoformat(data['DATE'])

        # Create document
        doc_ref = db.collection(collection_name).add({
            'ID': data['ID'],  
            'DATE': date,
            'ITEMS_MISSED': bool(data['ITEMS_MISSED']),
            'SOURCE_ID': data['SOURCE_ID'],
            'ITEMS': data['ITEMS'],
        })

        return jsonify({'message': 'Document added', 'id': doc_ref[1].id})

    except Exception as e:
        return jsonify({'error': str(e)})
    
def update_receipt(data,item_id):  
    allowed_fields = {'DATE', 'ITEMS_MISSED', 'SOURCE_ID', 'BILLER_NAME', 'BILL_VALUE', 'ITEMS'}
    update_data = {}

    try:
        # Find the document with matching ID
        query = db.collection(collection_name).where('ID', '==', item_id).limit(1)
        results = query.stream()
        doc = next(results, None)

        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        doc_data = doc.to_dict()

        # Validate and prepare update fields
        for field in data:
            if field not in allowed_fields:
                return jsonify({'error': f'Invalid field: {field}'}), 400

            if field == 'DATE':
                update_data['DATE'] = datetime.fromisoformat(data['DATE'])

            if field == 'ITEMS':
                # Merge new items into existing list
                existing_items = doc_data.get('ITEMS', [])
                new_items = data['ITEMS']

                if not isinstance(new_items, list):
                    return jsonify({'error': 'ITEMS must be a list'}), 400

                update_data['ITEMS'] = existing_items + new_items

            else:
                update_data[field] = data[field]

        # Update Firestore document
        doc.reference.update(update_data)
        return jsonify({'message': f'Document with ID={item_id} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

     