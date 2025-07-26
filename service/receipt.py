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
              results.append({
            'id': data.get('ID'),  # Firestore document ID
            'date': data.get('DATE').isoformat() if data.get('DATE') else None,
            'items_missed': data.get('ITEMS_MISSED'),
            'source_id': data.get('SOURCE_ID'),
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
                'id': doc.id,  # Firestore-generated doc ID
                'date': data.get('DATE').isoformat() if data.get('DATE') else None,
                'items_missed': data.get('ITEMS_MISSED'),
                'source_id': data.get('SOURCE_ID'),
                'ID': data.get('ID')  # Include custom ID if you want
            })
        else:
            return jsonify({'error': 'Document with given ID not found'})

def addReceipt(data):
    # Basic validation
    required_fields = ['ID','DATE', 'ITEMS_MISSED', 'SOURCE_ID']
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
            'SOURCE_ID': data['SOURCE_ID']
        })

        return jsonify({'message': 'Document added', 'id': doc_ref[1].id})

    except Exception as e:
        return jsonify({'error': str(e)})
    
def update_receipt(data,item_id):  
    allowed_fields = {'DATE', 'ITEMS_MISSED', 'SOURCE_ID'}
    update_data = {}

    try:
        # Validate and prepare update fields
        for field in data:
            if field not in allowed_fields:
                return jsonify({'error': f'Invalid field: {field}'})
            if field == 'DATE':
                update_data['DATE'] = datetime.fromisoformat(data['DATE'])
            else:
                update_data[field] = data[field]
        query = db.collection(collection_name).where('ID', '==', item_id).limit(1)
        results = query.stream()
        doc = next(results, None)

        if not doc:
            return jsonify({'error': 'Document not found'})
        doc.reference.update(update_data)

        return jsonify({'message': f'Documen`t with ID={item_id} updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

     