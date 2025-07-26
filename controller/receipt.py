from flask import Blueprint, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized, Forbidden


receipt_blueprint = Blueprint("receipt", __name__)

CORS(
    receipt_blueprint,
    resources={r"/*": {"origins": "*"}},
    origins=["*"],
)


@receipt_blueprint.route("/get-all", methods=["POST"])
def get_all(body):
    try:
        return jsonify({"message": "User registered successfully"}), 201
    except BadRequest as e:
        raise BadRequest(str(e))
    except Exception as e:
        raise BadRequest("An error occurred during registration: " + str(e))