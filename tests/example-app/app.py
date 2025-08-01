#!/usr/bin/env python3
"""
Example Web Application for Testing Web Eval Agent

A comprehensive Flask application with various interactive features
to demonstrate and test the web-eval CLI tool capabilities.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import time
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'web-eval-test-secret-key-12345'

# In-memory storage for demo purposes
users = {}
todos = []
messages = []
counter = 0

@app.route('/')
def home():
    """Homepage with navigation and overview."""
    return render_template('index.html', counter=counter)

@app.route('/counter', methods=['GET', 'POST'])
def counter_page():
    """Interactive counter with increment/decrement buttons."""
    global counter
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'increment':
            counter += 1
        elif action == 'decrement':
            counter -= 1
        elif action == 'reset':
            counter = 0
    
    return render_template('counter.html', counter=counter)

@app.route('/forms')
def forms_page():
    """Page with various form types for testing."""
    return render_template('forms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form with validation."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation
        errors = []
        if not name:
            errors.append('Name is required')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if not subject:
            errors.append('Subject is required')
        if not message:
            errors.append('Message is required')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('forms.html', name=name, email=email, subject=subject, message=message)
        
        # Store message
        messages.append({
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        flash('Message sent successfully!', 'success')
        return redirect(url_for('contact_success'))
    
    return render_template('forms.html')

@app.route('/contact/success')
def contact_success():
    """Contact form success page."""
    return render_template('contact_success.html')

@app.route('/todo')
def todo_page():
    """Todo list application."""
    return render_template('todo.html', todos=todos)

@app.route('/api/todos', methods=['GET', 'POST'])
def api_todos():
    """API endpoint for todo operations."""
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('text'):
            return jsonify({'error': 'Todo text is required'}), 400
        
        todo = {
            'id': len(todos) + 1,
            'text': data['text'],
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        todos.append(todo)
        return jsonify(todo), 201
    
    return jsonify(todos)

@app.route('/api/todos/<int:todo_id>', methods=['PUT', 'DELETE'])
def api_todo_item(todo_id):
    """API endpoint for individual todo operations."""
    todo = next((t for t in todos if t['id'] == todo_id), None)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404
    
    if request.method == 'PUT':
        data = request.get_json()
        if 'completed' in data:
            todo['completed'] = bool(data['completed'])
        if 'text' in data:
            todo['text'] = data['text']
        return jsonify(todo)
    
    elif request.method == 'DELETE':
        todos.remove(todo)
        return '', 204

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login form with session management."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html', username=username)
        
        # Simple authentication (demo purposes)
        if username in users and users[username]['password'] == password:
            session['user'] = username
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html', username=username)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration form."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        errors = []
        if not username:
            errors.append('Username is required')
        elif username in users:
            errors.append('Username already exists')
        
        if not email or '@' not in email:
            errors.append('Valid email is required')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', username=username, email=email)
        
        # Create user
        users[username] = {
            'email': email,
            'password': password,
            'created_at': datetime.now().isoformat()
        }
        
        session['user'] = username
        flash(f'Account created successfully! Welcome, {username}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """User dashboard (requires login)."""
    if 'user' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    user_data = users.get(session['user'], {})
    return render_template('dashboard.html', user=session['user'], user_data=user_data)

@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/interactive')
def interactive_page():
    """Page with various interactive elements."""
    return render_template('interactive.html')

@app.route('/api/random-quote')
def random_quote():
    """API endpoint that returns a random quote."""
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Life is what happens to you while you're busy making other plans. - John Lennon",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle"
    ]
    
    # Simulate some processing time
    time.sleep(0.5)
    
    return jsonify({
        'quote': random.choice(quotes),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/slow-endpoint')
def slow_endpoint():
    """Slow API endpoint for testing timeouts."""
    time.sleep(3)  # 3 second delay
    return jsonify({
        'message': 'This endpoint is intentionally slow',
        'delay': '3 seconds',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/error-endpoint')
def error_endpoint():
    """API endpoint that returns an error."""
    return jsonify({'error': 'This is an intentional error for testing'}), 500

@app.route('/modal-test')
def modal_test():
    """Page with modal dialogs for testing."""
    return render_template('modal_test.html')

if __name__ == '__main__':
    print("🚀 Starting Example Web Application")
    print("📍 Available at: http://localhost:5000")
    print("🧪 Ready for web-eval testing!")
    app.run(debug=True, host='0.0.0.0', port=5000)
