from functools import wraps

from flask import jsonify, render_template, request

from exceptions import DirectoryError
from models import EmployeeIn


def register_routes(app, directory, logger, api_key, status_map):
    @app.before_request
    def log_request():
        logger.info(f"{request.method} {request.path}")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(DirectoryError)
    def handle_directory_error(err):
        status = status_map.get(type(err), 400)
        logger.error(f"{status} - {err}")
        return jsonify({"error": str(err)}), status

    def require_api_key(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.headers.get("X-API-Key")
            if key != api_key:
                logger.error("401 - missing or invalid API key")
                return jsonify({"error": "Missing or invalid API key"}), 401
            return f(*args, **kwargs)

        return wrapper

    @app.route("/employees", methods=["POST"])
    @require_api_key
    def create_employee():
        employee_in = EmployeeIn.from_dict(request.get_json(silent=True))
        employee = directory.add_employee(employee_in)
        return jsonify(employee.to_dict()), 201

    @app.route("/employees", methods=["GET"])
    def list_employees_route():
        department = request.args.get("department")
        employees = directory.list_employees(department)
        return jsonify([e.to_dict() for e in employees])

    @app.route("/employees/search", methods=["GET"])
    def search_employees():
        query = request.args.get("q", "")
        return jsonify([e.to_dict() for e in directory.search(query)])

    @app.route("/employees/<employee_id>", methods=["GET"])
    def get_employee_route(employee_id):
        return jsonify(directory.get_employee(employee_id).to_dict())

    @app.route("/employees/<employee_id>", methods=["PUT"])
    @require_api_key
    def update_employee_route(employee_id):
        employee_in = EmployeeIn.from_dict(request.get_json(silent=True))
        employee = directory.update_employee(employee_id, employee_in)
        return jsonify(employee.to_dict())

    @app.route("/employees/<employee_id>", methods=["DELETE"])
    @require_api_key
    def delete_employee_route(employee_id):
        directory.remove_employee(employee_id)
        return "", 204
