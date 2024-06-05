from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from wtforms import StringField, BooleanField, DateField, TextAreaField, HiddenField
from wtforms.validators import DataRequired
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rows.db'

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

ROWS_PER_PAGE = 10


class IdentifiedIssue(db.Model):
    __tablename__ = 'identified_issues'

    id = db.Column(db.Integer, primary_key=True)
    identified_issue = db.Column(db.String, unique=True)

    def __init__(self, identified_issue):
        self.identified_issue = identified_issue

    @staticmethod
    def check_repeats(identified_issue):
        return db.session.query(
            db.exists().where(IdentifiedIssue.identified_issue == identified_issue)
        ).scalar()

    @staticmethod
    def add_issues(issues_string):
        issues = [issue.strip() for issue in issues_string.split(',')]
        for issue in issues:
            if not IdentifiedIssue.check_repeats(issue):
                new_issue = IdentifiedIssue(issue)
                db.session.add(new_issue)
        db.session.commit()


class RowForm(FlaskForm):
    csrf_token = HiddenField()
    incident = StringField('Incident', validators=[DataRequired()])
    prep_checkbox = BooleanField('Prep')
    prep_date = DateField('Prep Date')
    assigned_to = StringField('Assigned To', validators=[DataRequired()])
    issue_date = DateField('Date', validators=[DataRequired()])
    in_scope = BooleanField('In Scope')
    comments = TextAreaField('Comments')
    rca = StringField('Root Cause Analysis')
    identified_issue = StringField('Identified Issue', validators=[DataRequired()])


class Row(db.Model):
    __tablename__ = 'rows'

    id = db.Column(db.Integer, primary_key=True)
    incident = db.Column(db.String)
    prep = db.Column(db.String)
    assigned_to = db.Column(db.String(100), nullable=True)
    issue_date = db.Column(db.String)
    in_scope = db.Column(db.String)
    comments = db.Column(db.String)
    rca = db.Column(db.String)
    identified_issue = db.Column(db.String)

    def __init__(self, incident, prep, assigned_to, issue_date, in_scope, comments, rca, identified_issue):
        self.incident = incident
        self.prep = prep
        self.assigned_to = assigned_to
        self.issue_date = issue_date
        self.in_scope = in_scope
        self.comments = comments
        self.rca = rca
        self.identified_issue = identified_issue

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = RowForm()

    if request.method == 'POST':
        prep = f"Yes {form.prep_date.data}" if form.prep_checkbox.data else "No"
        in_scope = "Yes" if form.in_scope.data else "No"

        identified_issues = request.form.get('identified_issue')

        new_row = Row(
            incident=form.incident.data,
            prep=prep,
            assigned_to=form.assigned_to.data,
            issue_date=form.issue_date.data,
            in_scope=in_scope,
            comments=form.comments.data,
            rca=form.rca.data,
            identified_issue=identified_issues
        )
        db.session.add(new_row)
        db.session.commit()

        IdentifiedIssue.add_issues(identified_issues)

    rows = Row.query.all()

    return render_template('index.html', rows=rows, form=form)

def edit_row(row_id):
    row = Row.query.get_or_404(row_id)
    row.incident = request.form['incident']
    row.prep = request.form['prep']
    row.assigned_to = request.form['assigned_to']
    row.issue_date = request.form['issue_date']
    row.in_scope = 'Yes' if request.form.get('in_scope') == 'true' else 'No'
    row.comments = request.form['comments']
    row.rca = request.form['rca']
    row.identified_issue = request.form['identified_issue']

    db.session.commit()

    return redirect(url_for('index'))

@app.route('/delete_row/<int:row_id>', methods=['POST'])
def delete_row(row_id):
    row = Row.query.get_or_404(row_id)
    db.session.delete(row)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/save_changes', methods=['POST'])
def save_changes():
    edited_rows = request.form

    for key in edited_rows:
        if key.startswith('incident_'):
            row_id = key.split('_')[1]
            row = Row.query.get_or_404(row_id)

            incident = edited_rows[f'incident_{row_id}']
            prep = edited_rows.get(f'prep_{row_id}', '')
            assigned_to = edited_rows.get(f'assigned_to_{row_id}', '')
            issue_date = edited_rows[f'issue_date_{row_id}']
            in_scope = edited_rows.get(f'in_scope_{row_id}')
            comments = edited_rows[f'comments_{row_id}']
            rca = edited_rows[f'rca_{row_id}']
            identified_issue = edited_rows[f'identified_issue_{row_id}']

            row.incident = incident
            row.prep = prep
            row.assigned_to = assigned_to
            row.issue_date = issue_date
            row.in_scope = in_scope
            row.comments = comments
            row.rca = rca
            row.identified_issue = identified_issue

            db.session.commit()

    return redirect(url_for('index'))

@app.route('/get_issues', methods=['GET'])
def get_issues():
    issues = IdentifiedIssue.query.all()
    return jsonify([{'text': issue.identified_issue} for issue in issues])

if __name__ == "__main__":
    app.run(port=5000, debug=True)
