from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rows.db'

db = SQLAlchemy(app)


class Row(db.Model):
    __tablename__ = 'rows'

    id = db.Column(db.Integer, primary_key=True)
    incident = db.Column(db.String)
    prep = db.Column(db.String)
    assigned_to = db.Column(db.String)
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
    if request.method == 'POST':
        prep_checkbox = request.form.get('prep_checkbox')
        in_scope_checkbox = request.form.get('in_scope')

        incident = request.form['incident']
        prep_date = request.form['prep_date']
        prep = f"Yes {prep_date}" if prep_checkbox else "No"
        in_scope = "Yes" if in_scope_checkbox else "No"
        assigned_to = request.form['assigned_to']
        date = request.form['date']
        comments = request.form['comments']
        rca = request.form['rca']

        new_row = Row(incident, prep, assigned_to, date, in_scope, comments, rca)
        db.session.add(new_row)
        db.session.commit()

    rows = Row.query.all()
    return render_template('index.html', rows=rows)


if __name__ == "__main__":
    app.run(port=5000, debug=True)