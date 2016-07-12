# -*- coding: utf-8 -*-

from specification import *


class Attendance(object):

    def __init__(self, employee=False, sign_in=False, sign_out=False):
        self.employee = employee
        self.sign_in = sign_in
        self.sign_out = sign_out

class AttendanceSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return isinstance(candidate, Attendance)

class EmployeeSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'employee', False)

class SignInSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'sign_in', False)

class SignOutSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'sign_out', False)


if __name__ == '__main__':
    print '\nAttendance'
    ade_attendance = Attendance(True, 0, 0)
    abas_attendance = Attendance(True, 10, 0)
    agus_attendance = Attendance(True, 0, 5)
    joni_attendance = Attendance(True, 3, 2)
    attendance_specification = AttendanceSpecification().\
        and_specification(SignInSpecification()).\
        and_specification(SignOutSpecification())

    print(attendance_specification.is_satisfied_by(ade_attendance))
    print(attendance_specification.is_satisfied_by(abas_attendance))
    print(attendance_specification.is_satisfied_by(agus_attendance))
    print(attendance_specification.is_satisfied_by(joni_attendance))