import os
import sys
import pandas as pd
from flask import Flask, send_from_directory, send_file, jsonify, request, session
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'your-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Load data
def load_data():
    try:
        excel_path = os.path.join(os.path.dirname(__file__), '..', 'NEW(new)CounterTeam.xlsx')
        submissions_df = pd.read_excel(excel_path, sheet_name='Form Responses 1')
        users_df = pd.read_excel(excel_path, sheet_name='Users')
        return submissions_df, users_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

submissions_df, users_df = load_data()

# Authentication routes
@app.route('/api/auth/signin', methods=['POST'])
def signin():
    data = request.get_json()
    email = data.get('email', '').strip()
    
    # Check if user exists in Users sheet
    user_row = users_df[users_df['Email'].str.lower() == email.lower()]
    
    if user_row.empty:
        return jsonify({'error': 'User not found or not authorized'}), 401
    
    user_info = user_row.iloc[0]
    user_data = {
        'email': user_info['Email'],
        'role': user_info['Role']
    }
    
    session['user'] = user_data
    return jsonify({'user': user_data})

@app.route('/api/auth/signout', methods=['POST'])
def signout():
    session.pop('user', None)
    return jsonify({'message': 'Signed out successfully'})

@app.route('/api/auth/verify', methods=['GET'])
def verify():
    user = session.get('user')
    if user:
        return jsonify({'authenticated': True, 'user': user})
    return jsonify({'authenticated': False})

# Data routes
@app.route('/api/submissions', methods=['GET'])
def get_all_submissions():
    user = session.get('user')
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(submissions_df.fillna('').to_dict('records'))

@app.route('/api/submissions/my', methods=['GET'])
def get_my_submissions():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Extract name from email (assuming format like ME116268@meti.services)
    email_prefix = user['email'].split('@')[0]
    user_submissions = submissions_df[submissions_df['Name'].str.contains(email_prefix, case=False, na=False)]
    
    return jsonify(user_submissions.fillna('').to_dict('records'))

@app.route('/api/users', methods=['GET'])
def get_users():
    user = session.get('user')
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(users_df.fillna('').to_dict('records'))

@app.route('/api/analytics/summary', methods=['GET'])
def get_admin_analytics():
    user = session.get('user')
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    analytics = {
        'unique_members': submissions_df['Name'].nunique(),
        'total_submissions': len(submissions_df),
        'accepted_count': len(submissions_df[submissions_df['Is this rejected (Slice / Miner)'] == 'Accepted']),
        'rejected_count': len(submissions_df[submissions_df['Is this rejected (Slice / Miner)'] == 'Rejected']),
        'changed_count': len(submissions_df[submissions_df['Is this Changed (Slice / Miner)'] == 'Yes']),
        'most_common_mistake': submissions_df['In your opinion, what is the reason for reviewer mistake?'].mode().iloc[0] if not submissions_df['In your opinion, what is the reason for reviewer mistake?'].mode().empty else 'No data',
        'reviewer_with_most_rejected': submissions_df[submissions_df['Is this rejected (Slice / Miner)'] == 'Rejected']['Name'].mode().iloc[0] if not submissions_df[submissions_df['Is this rejected (Slice / Miner)'] == 'Rejected']['Name'].mode().empty else 'No data'
    }
    
    return jsonify(analytics)

@app.route('/api/analytics/my', methods=['GET'])
def get_my_analytics():
    user = session.get('user')
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Extract name from email
    email_prefix = user['email'].split('@')[0]
    user_submissions = submissions_df[submissions_df['Name'].str.contains(email_prefix, case=False, na=False)]
    
    analytics = {
        'total_submitted': len(user_submissions),
        'accepted_count': len(user_submissions[user_submissions['Is this rejected (Slice / Miner)'] == 'Accepted']),
        'rejected_count': len(user_submissions[user_submissions['Is this rejected (Slice / Miner)'] == 'Rejected']),
        'leader_reviewed': len(user_submissions[user_submissions['Leader Name'].notna()]),
        'changed_by_leader': len(user_submissions[user_submissions['Is this Changed (Slice / Miner)'] == 'Yes']),
        'fully_aligned': len(user_submissions[user_submissions['Are the QC and Reviewer aligned on the same answer'] == 'Yes']),
        'misaligned': len(user_submissions[user_submissions['Are the QC and Reviewer aligned on the same answer'] == 'No']),
        'last_submission': user_submissions['Timestamp'].max() if not user_submissions.empty else None,
        'mistake_reasons': user_submissions['In your opinion, what is the reason for reviewer mistake?'].value_counts().to_dict()
    }
    
    return jsonify(analytics)

@app.route('/api/analytics/charts/rejection-by-task-type', methods=['GET'])
def get_rejection_by_task_type():
    user = session.get('user')
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    chart_data = []
    for task_type in submissions_df['Task Type'].unique():
        if pd.isna(task_type):
            continue
        task_data = submissions_df[submissions_df['Task Type'] == task_type]
        accepted = len(task_data[task_data['Is this rejected (Slice / Miner)'] == 'Accepted'])
        rejected = len(task_data[task_data['Is this rejected (Slice / Miner)'] == 'Rejected'])
        chart_data.append({
            'task_type': task_type,
            'accepted': accepted,
            'rejected': rejected
        })
    
    return jsonify(chart_data)

@app.route('/api/analytics/charts/submission-trend', methods=['GET'])
def get_submission_trend():
    user = session.get('user')
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Convert timestamp to date and count submissions per day
    submissions_df['Date'] = pd.to_datetime(submissions_df['Timestamp']).dt.date
    trend_data = submissions_df.groupby('Date').size().reset_index(name='count')
    trend_data['date'] = trend_data['Date'].astype(str)
    
    return jsonify(trend_data[['date', 'count']].to_dict('records'))

# Serve React app
@app.route('/')
def serve_react_app():
    return send_file(os.path.join(app.static_folder, 'index.html'))

# Handle React Router routes
@app.route('/<path:path>')
def serve_react_routes(path):
    # If the path is for an API route, let Flask handle it
    if path.startswith('api/'):
        return {'error': 'API endpoint not found'}, 404
    
    # If the file exists in static folder, serve it
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # Otherwise, serve the React app (for client-side routing)
    return send_file(os.path.join(app.static_folder, 'index.html'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

