from exceptions import InvalidEmployeeDataError


class EmployeeIn:
    def __init__(self, name, email, department, role):
        self.name = name
        self.email = email
        self.department = department
        self.role = role

    @classmethod
    def from_dict(cls, data):
        if not data:
            raise InvalidEmployeeDataError("Request body is empty or not valid JSON")

        required = ["name", "email", "department", "role"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            raise InvalidEmployeeDataError(f"Missing fields: {', '.join(missing)}")

        if "@" not in data["email"]:
            raise InvalidEmployeeDataError(f"Invalid email: {data['email']}")

        return cls(data["name"], data["email"], data["department"], data["role"])

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "role": self.role,
        }


class Employee(EmployeeIn):
    def __init__(self, employee_id, name, email, department, role):
        super().__init__(name, email, department, role)
        self.employee_id = employee_id

    def to_dict(self):
        data = super().to_dict()
        data["employee_id"] = self.employee_id
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["employee_id"],
            data["name"],
            data["email"],
            data["department"],
            data["role"],
        )
