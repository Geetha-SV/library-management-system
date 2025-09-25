from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:geethasasi@localhost:5432/librarydb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=1)

class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrower = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow)
    return_date = db.Column(db.Date, nullable=True)
    book = db.relationship('Book')

# ----------- ROUTES ------------ #

@app.route('/')
def index(): 
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    if q:
        books = Book.query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%'))
        ).all()
    else:
        books = Book.query.all()
    borrows = Borrow.query.filter(Borrow.return_date == None).all()
    return render_template('index.html', books=books, borrows=borrows)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash('Logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        quantity = int(request.form['quantity'])
        book = Book(title=title, author=author, isbn=isbn, quantity=quantity)
        db.session.add(book)
        db.session.commit()
        flash('Book added!', 'success')
        return redirect(url_for('index'))
    return render_template('add_book.html')

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    books = Book.query.all()
    if request.method == 'POST':
        book_id = request.form['book_id']
        borrower = request.form['borrower']
        book = Book.query.get(book_id)
        if book and book.quantity > 0:
            borrow = Borrow(book_id=book.id, borrower=borrower)
            book.quantity -= 1
            db.session.add(borrow)
            db.session.commit()
            flash('Book issued!', 'success')
        else:
            flash('Book unavailable.', 'danger')
        return redirect(url_for('index'))
    return render_template('issue_book.html', books=books)

@app.route('/return_book/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    borrow = Borrow.query.get(borrow_id)
    if borrow and borrow.return_date is None:
        borrow.return_date = datetime.utcnow().date()
        book = Book.query.get(borrow.book_id)
        book.quantity += 1
        db.session.commit()
        flash('Book returned!', 'success')
    return redirect(url_for('index'))

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.isbn = request.form['isbn']
        book.quantity = int(request.form['quantity'])
        db.session.commit()
        flash('Book updated successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get_or_404(book_id)
    borrows = Borrow.query.filter_by(book_id=book.id).all()
    if borrows:
        flash('Cannot delete: This book has current or past borrow records.', 'danger')
        return redirect(url_for('index'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/history')
def history():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    history_entries = Borrow.query.order_by(Borrow.issue_date.desc()).all()
    return render_template('history.html', history_entries=history_entries)

if __name__ == "__main__":
    app.run(debug=True)