from flask import Flask, request, render_template, redirect, url_for
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


class RowForm(FlaskForm):
    csrf_token = HiddenField()
    incident = StringField('Incident', validators=[DataRequired()])
    prep_checkbox = BooleanField('Prep')
    prep_date = DateField('Prep Date')
    assigned_to = StringField('Assigned To', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    in_scope = BooleanField('In Scope')
    comments = TextAreaField('Comments')
    rca = StringField('Root Cause Analysis')


class Row(db.Model):
    __tablename__ = 'rows'

    id = db.Column(db.Integer, primary_key=True)
    incident = db.Column(db.String)
    prep = db.Column(db.String)
    assigned_to = db.Column(db.String(100), nullable=True)
    date = db.Column(db.String)
    in_scope = db.Column(db.String)
    comments = db.Column(db.String)
    rca = db.Column(db.String)

    def __init__(self, incident, prep, assigned_to, date, in_scope, comments, rca):
        self.incident = incident
        self.prep = prep
        self.assigned_to = assigned_to
        self.date = date
        self.in_scope = in_scope
        self.comments = comments
        self.rca = rca

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = RowForm()
    if request.method == 'POST':
        prep = f"Yes {form.prep_date.data}" if form.prep_checkbox.data else "No"
        in_scope = "Yes" if form.in_scope.data else "No"

        new_row = Row(
            incident=form.incident.data,
            prep=prep,
            assigned_to=form.assigned_to.data,
            date=form.date.data,
            in_scope=in_scope,
            comments=form.comments.data,
            rca=form.rca.data
        )
        db.session.add(new_row)
        db.session.commit()

    rows = Row.query.all()

    return render_template('index.html', rows=rows, form=form)

def edit_row(row_id):
    row = Row.query.get_or_404(row_id)
    row.incident = request.form['incident']
    row.prep = request.form['prep']
    row.assigned_to = request.form['assigned_to']
    row.date = request.form['date']
    row.in_scope = 'Yes' if request.form.get('in_scope') == 'true' else 'No'
    app.logger.debug(f"In scope checkbox: {row.in_scope}")
    row.comments = request.form['comments']
    row.rca = request.form['rca']

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
            date = edited_rows[f'date_{row_id}']
            in_scope = edited_rows.get(f'in_scope_{row_id}')
            comments = edited_rows[f'comments_{row_id}']
            rca = edited_rows[f'rca_{row_id}']

            row.incident = incident
            row.prep = prep
            row.assigned_to = assigned_to
            row.date = date
            row.in_scope = in_scope
            row.comments = comments
            row.rca = rca

            db.session.commit()

            app.logger.debug(f"In scope checkbox: {edited_rows.get(f'in_scope_{row_id}')}")

    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(port=5000, debug=True)