from flask import Flask, request, jsonify, render_template
import sqlite3
import io, sys
import os
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database setup
def create_database():
    conn = sqlite3.connect('saved_codes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_database()

# Ensure the 'Submitted files' directory exists
os.makedirs('Submitted files', exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.form['code']
    try:
        # Write the code to a temporary file
        with open('temp_code.py', 'w') as f:
            f.write(code)

        # Execute the code using subprocess with increased timeout
        result = subprocess.run(['python', 'temp_code.py'], capture_output=True, text=True, timeout=30)

        # Check for timeout and handle it
        if result.returncode == -9:  # -9 is often used for timeout termination
            return jsonify({'error': 'Execution timed out. Please optimize your code.'})

        # Return the output or error
        if result.returncode == 0:
            return jsonify({'result': result.stdout})
        else:
            return jsonify({'error': result.stderr})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/save', methods=['POST'])
def save_code():
    code = request.form['code']
    try:
        conn = sqlite3.connect('saved_codes.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO codes (code) VALUES (?)", (code,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Code saved to database'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit_code():
    code = request.form['code']
    try:
        # Save the code to a .py file
        file_count = len(os.listdir('Submitted files'))
        file_path = os.path.join('Submitted files', f'submitted_code_{file_count + 1}.py')
        with open(file_path, 'w') as file:
            file.write(code)

        # Save the code to the database
        conn = sqlite3.connect('saved_codes.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO codes (code) VALUES (?)", (code,))
        conn.commit()
        conn.close()

        return jsonify({'message': f'Code submitted and saved as {file_path}.'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')


