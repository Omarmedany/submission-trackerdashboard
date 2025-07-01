from flask import Blueprint, jsonify, request, session
import pandas as pd
import os
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)

# Path to the Excel file
EXCEL_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'NEW(new)CounterTeam.xlsx')

def load_users_data():
    """Load users data from Excel file"""
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Users')
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error loading users data: {e}")
        return pd.DataFrame()

def load_submissions_data():
    """Load submissions data from Excel file"""
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Form Responses 1')
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"Error loading submissions data: {e}")
        return pd.DataFrame()

def find_user_name_by_email(email):
    """Find user name from submissions data based on email pattern"""
    submissions_df = load_submissions_data()
    if submissions_df.empty or 'Name' not in submissions_df.columns:
        return None
    
    # Get unique names from submissions
    unique_names = submissions_df['Name'].dropna().unique()
    
    # For now, we'll return the first name if email exists in users
    # In a real scenario, you might want to implement a more sophisticated mapping
    users_df = load_users_data()
    if not users_df.empty and email in users_df['Email'].values:
        # Return the first non-null name from submissions as a fallback
        if len(unique_names) > 0:
            return unique_names[0]
    
    return None

@auth_bp.route('/signin', methods=['POST'])
def signin():
    """Sign in user with email"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    users_df = load_users_data()
    if users_df.empty:
        return jsonify({'error': 'No users data found'}), 404
    
    # Find user by email
    user_row = users_df[users_df['Email'] == email]
    
    if user_row.empty:
        return jsonify({'error': 'User not found or not authorized'}), 401
    
    user_data = user_row.iloc[0].to_dict()
    
    # Handle NaN values
    for key, value in user_data.items():
        if pd.isna(value):
            user_data[key] = None
    
    # Generate a simple session token
    session_token = secrets.token_urlsafe(32)
    
    # Find associated name from submissions data
    user_name = find_user_name_by_email(email)
    
    # Store session info (in a real app, you'd use a proper session store)
    session_data = {
        'email': user_data['Email'],
        'role': user_data['Role'],
        'name': user_name,
        'token': session_token,
        'expires': (datetime.now() + timedelta(hours=24)).isoformat()
    }
    
    # Store in Flask session for simplicity
    session['user'] = session_data
    
    return jsonify({
        'success': True,
        'user': {
            'email': user_data['Email'],
            'role': user_data['Role'],
            'name': user_name,
            'token': session_token
        }
    })

@auth_bp.route('/signout', methods=['POST'])
def signout():
    """Sign out user"""
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Signed out successfully'})

@auth_bp.route('/verify', methods=['GET'])
def verify_session():
    """Verify current session"""
    user_data = session.get('user')
    
    if not user_data:
        return jsonify({'authenticated': False}), 401
    
    # Check if session has expired
    try:
        expires = datetime.fromisoformat(user_data['expires'])
        if datetime.now() > expires:
            session.pop('user', None)
            return jsonify({'authenticated': False, 'error': 'Session expired'}), 401
    except:
        session.pop('user', None)
        return jsonify({'authenticated': False, 'error': 'Invalid session'}), 401
    
    return jsonify({
        'authenticated': True,
        'user': {
            'email': user_data['email'],
            'role': user_data['role'],
            'name': user_data['name']
        }
    })

@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """Check if email exists in users database"""
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    users_df = load_users_data()
    if users_df.empty:
        return jsonify({'exists': False})
    
    # Check if email exists
    email_exists = email in users_df['Email'].values
    
    return jsonify({'exists': email_exists})

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user_data = session.get('user')
        if not user_data:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if session has expired
        try:
            expires = datetime.fromisoformat(user_data['expires'])
            if datetime.now() > expires:
                session.pop('user', None)
                return jsonify({'error': 'Session expired'}), 401
        except:
            session.pop('user', None)
            return jsonify({'error': 'Invalid session'}), 401
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_admin(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        user_data = session.get('user')
        if not user_data:
            return jsonify({'error': 'Authentication required'}), 401
        
        if user_data.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

