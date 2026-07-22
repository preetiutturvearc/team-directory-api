class DirectoryError(Exception):
    """Base class for all directory-related errors."""


class EmployeeNotFoundError(DirectoryError):
    def __init__(self, employee_id):
        super().__init__(f"Employee with id '{employee_id}' not found")


class DuplicateEmailError(DirectoryError):
    def __init__(self, email):
        super().__init__(f"Email '{email}' is already in use")


class InvalidEmployeeDataError(DirectoryError):
    pass
