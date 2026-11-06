from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LeaveRequest(db.Model):
    __tablename__ = "Leave_Requests"

    id = db.Column(db.Integer, primary_key = True)
    employee_id = db.Column(db.Integer, nullable = False)
    leave_type = db.Column(db.String(50), nullable = False)
    start_date = db.Column(db.Date, nullable = False)
    end_date = db.Column(db.Date, nullable = False)
    reason = db.Column(db.Text, nullable = False)
    status = db.Column(db.String(20), nullable = False, default = "Pending")


def add_leave(employee_id, leave_type, start_date, end_date, reason):
    new_leave = LeaveRequest(
        employee_id = employee_id,
        leave_type = leave_type,
        start_date = start_date,
        end_date = end_date,
        reason = reason
    )

    db.session.add(new_leave)
    db.session.commit()

    return new_leave

def view_leaves(employee_id):
    leaves = db.session.execute(
        db.select(LeaveRequest)
        .filter_by(employee_id = employee_id)
        .order_by(LeaveRequest.id.desc())
    ).scalars().all()

    return leaves

def get_leave_by_id(leave_id):
    leave = db.session.get(LeaveRequest, leave_id)

    return leave

def update_leave(leave, leave_type, start_date, end_date, reason):

    leave.leave_type = leave_type
    leave.start_date = start_date
    leave.end_date = end_date
    leave.reason = reason

    db.session.commit()

class User(db.Model):
    __tablename__  = "Users"

    id = db.Column(db.Integer, primary_key = True)
    username =  db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.String(255), nullable = False)


