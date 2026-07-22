import json
import logging
import threading
import time
import uuid

from exceptions import DuplicateEmailError, EmployeeNotFoundError
from models import Employee

logger = logging.getLogger(__name__)


class EmployeeDirectory:
    def __init__(self, storage_path="directory.json"):
        self._employees = {}
        self._storage_path = storage_path
        self._lock = threading.Lock()

    def add_employee(self, employee_in):
        with self._lock:
            self._assert_email_available(employee_in.email)
            employee_id = uuid.uuid4().hex[:8]
            employee = Employee(
                employee_id,
                employee_in.name,
                employee_in.email,
                employee_in.department,
                employee_in.role,
            )
            self._employees[employee_id] = employee
            self._save()
        logger.info(f"Created employee {employee_id}")
        return employee

    def get_employee(self, employee_id):
        employee = self._employees.get(employee_id)
        if employee is None:
            raise EmployeeNotFoundError(employee_id)
        return employee

    def list_employees(self, department=None):
        employees = list(self._employees.values())
        if department:
            employees = [e for e in employees if e.department == department]
        return employees

    def update_employee(self, employee_id, employee_in):
        with self._lock:
            self.get_employee(employee_id)
            self._assert_email_available(employee_in.email, exclude_id=employee_id)
            updated = Employee(
                employee_id,
                employee_in.name,
                employee_in.email,
                employee_in.department,
                employee_in.role,
            )
            self._employees[employee_id] = updated
            self._save()
        logger.info(f"Updated employee {employee_id}")
        return updated

    def remove_employee(self, employee_id):
        with self._lock:
            self.get_employee(employee_id)
            del self._employees[employee_id]
            self._save()
        logger.info(f"Deleted employee {employee_id}")

    def search(self, query):
        query = query.lower()
        return [e for e in self._employees.values() if query in e.name.lower()]

    def _assert_email_available(self, email, exclude_id=None):
        for emp_id, employee in self._employees.items():
            if employee.email == email and emp_id != exclude_id:
                raise DuplicateEmailError(email)

    def _save(self):
        self.save_to_file(self._storage_path)

    def save_to_file(self, path):
        data = [e.to_dict() for e in self._employees.values()]
        # To re-run the Milestone 7 before/after demo: uncomment the line
        # below and temporarily remove the "with self._lock:" in
        # add_employee. It widens the gap between reading in-memory state
        # and writing to disk, so concurrent unlocked saves reliably
        # corrupt directory.json (proves the race; safe to leave off
        # otherwise since the lock alone is what actually matters).
        # time.sleep(0.05)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, path):
        try:
            with open(path) as f:
                data = json.load(f)
            self._employees = {d["employee_id"]: Employee.from_dict(d) for d in data}
            logger.info(f"Loaded {len(self._employees)} employees from {path}")
        except FileNotFoundError:
            logger.warning(f"No existing directory file at {path}, starting empty")
            self._employees = {}
        except json.JSONDecodeError:
            logger.warning(f"Corrupt directory file at {path}, starting empty")
            self._employees = {}
