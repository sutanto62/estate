# -*- coding: utf-8 -*-

from specification import *


class Attendance(object):

    def __init__(self, employee=False, sign_in=False, sign_out=False, action=False):
        self.employee = employee
        self.sign_in = sign_in
        self.sign_out = sign_out
        self.action = action

class UpkeepFingerprint(object):

    def __init__(self, sign_in=False, sign_out=False, attendance_code=False, action=False):
        self.sign_in = sign_in
        self.sign_out = sign_out
        self.attendance_code = attendance_code
        self.action = action


class UpkeepFingerprintSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return isinstance(candidate, UpkeepFingerprint)


class EmployeeSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'employee', False)


class ActionSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'action', False)


class AttendanceSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return isinstance(candidate, Attendance)


class SignInSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'sign_in', False)


class SignOutSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'sign_out', False)


class SignInOutSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'sign_in', False) or getattr(candidate, 'sign_out', False)


class AttendanceCodeSpecification(CompositeSpecification):

    def is_satisfied_by(self, candidate):
        return getattr(candidate, 'attendance_code', False)


if __name__ == '__main__':
    print '\nAttendance'
    ade_attendance = Attendance(True, 0, 0)
    abas_attendance = Attendance(True, 1, 1)
    agus_attendance = Attendance(True, 0, 5)
    joni_attendance = Attendance(True, 3, 2)
    aisah_attendance = Attendance(1,1,0)

    attendance_specification = AttendanceSpecification().\
        and_specification(SignInSpecification()).\
        and_specification(SignOutSpecification())

    single_attendance_specification = AttendanceSpecification().\
        and_specification(EmployeeSpecification()).\
        and_specification(SignInOutSpecification())

    print(attendance_specification.is_satisfied_by(ade_attendance))
    print(attendance_specification.is_satisfied_by(abas_attendance))
    print(attendance_specification.is_satisfied_by(agus_attendance))
    print(attendance_specification.is_satisfied_by(joni_attendance))
    print(single_attendance_specification.is_satisfied_by(aisah_attendance))

    print '\nUpkeep Fingerprint'


    fingerprint_specification = UpkeepFingerprintSpecification().\
        and_specification(ActionSpecification()). \
        or_specification(SignInSpecification()). \
        and_specification(SignOutSpecification()). \
        and_specification(AttendanceCodeSpecification())

    action_specification = UpkeepFingerprintSpecification().\
        and_specification(SignInSpecification()).\
        and_specification(SignOutSpecification()).\
        and_specification(AttendanceCodeSpecification()).\
        or_specification(ActionSpecification())

    single_specification = UpkeepFingerprintSpecification().\
        and_specification(AttendanceCodeSpecification()).\
        and_specification(SignInOutSpecification())

    abas_fingerprint = UpkeepFingerprint(1,1,1)
    akil_fingerprint = UpkeepFingerprint(1,0,1)
    dipo_fingerprint = UpkeepFingerprint(0,0,0,1)
    khl_borongan_fingerprint = UpkeepFingerprint(1,1,1,0)

    print ('In,Out: %s' % fingerprint_specification.is_satisfied_by(abas_fingerprint))
    print ('In Only: %s' % fingerprint_specification.is_satisfied_by(akil_fingerprint))
    print ('Action no In/Out: %s' % action_specification.is_satisfied_by(dipo_fingerprint))
    print ('Borongan single in or out: %s' % single_specification.is_satisfied_by(khl_borongan_fingerprint))