from flask import Blueprint, jsonify, request, session
import pandas as pd
import os
from datetime import datetime
from src.routes.auth import require_auth, require_admin

data_bp = Blueprint('data', __name__)

# Path to the Excel file
EXCEL_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'NEW(new)CounterTeam.xlsx')

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

@data_bp.route('/submissions', methods=['GET'])
@require_admin
def get_submissions():
    """Get all submissions data (admin only)"""
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    # Convert DataFrame to list of dictionaries
    submissions = df.to_dict('records')
    
    # Handle NaN values by converting them to None
    for submission in submissions:
        for key, value in submission.items():
            if pd.isna(value):
                submission[key] = None
    
    return jsonify(submissions)

@data_bp.route('/submissions/user/<name>', methods=['GET'])
@require_auth
def get_submissions_by_user(name):
    """Get submissions for a specific user"""
    user_data = session.get('user')
    
    # Users can only access their own data unless they're admin
    if user_data.get('role') != 'admin' and user_data.get('name') != name:
        return jsonify({'error': 'Access denied'}), 403
    
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    # Filter by user name (case-sensitive as per requirements)
    user_submissions = df[df['Name'] == name]
    
    if user_submissions.empty:
        return jsonify([])
    
    submissions = user_submissions.to_dict('records')
    
    # Handle NaN values
    for submission in submissions:
        for key, value in submission.items():
            if pd.isna(value):
                submission[key] = None
    
    return jsonify(submissions)

@data_bp.route('/submissions/my', methods=['GET'])
@require_auth
def get_my_submissions():
    """Get submissions for the current authenticated user"""
    user_data = session.get('user')
    user_name = user_data.get('name')
    
    if not user_name:
        return jsonify({'error': 'User name not found'}), 400
    
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    # Filter by user name (case-sensitive as per requirements)
    user_submissions = df[df['Name'] == user_name]
    
    if user_submissions.empty:
        return jsonify([])
    
    submissions = user_submissions.to_dict('records')
    
    # Handle NaN values
    for submission in submissions:
        for key, value in submission.items():
            if pd.isna(value):
                submission[key] = None
    
    return jsonify(submissions)

@data_bp.route('/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users data (admin only)"""
    df = load_users_data()
    if df.empty:
        return jsonify({'error': 'No users data found'}), 404
    
    users = df.to_dict('records')
    
    # Handle NaN values
    for user in users:
        for key, value in user.items():
            if pd.isna(value):
                user[key] = None
    
    return jsonify(users)

@data_bp.route('/analytics/summary', methods=['GET'])
@require_admin
def get_summary_analytics():
    """Get summary analytics for admin dashboard"""
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    # Calculate summary statistics
    total_submissions = len(df)
    unique_members = df['Name'].nunique() if 'Name' in df.columns else 0
    
    # Count accepted vs rejected
    accepted_count = len(df[df['Is this rejected (Slice / Miner)'] == 'Accepted']) if 'Is this rejected (Slice / Miner)' in df.columns else 0
    rejected_count = len(df[df['Is this rejected (Slice / Miner)'] == 'Rejected']) if 'Is this rejected (Slice / Miner)' in df.columns else 0
    
    # Count tasks changed by leaders
    changed_count = len(df[df['Is this Changed (Slice / Miner)'].notna()]) if 'Is this Changed (Slice / Miner)' in df.columns else 0
    
    # Most common reviewer mistake
    mistake_column = 'In you opinion, What is the reason for reviewer mistake?'
    most_common_mistake = None
    if mistake_column in df.columns:
        mistake_counts = df[mistake_column].value_counts()
        if not mistake_counts.empty:
            most_common_mistake = mistake_counts.index[0]
    
    # Reviewer with most rejected tasks
    reviewer_with_most_rejected = None
    if 'Name' in df.columns and 'Is this rejected (Slice / Miner)' in df.columns:
        rejected_by_reviewer = df[df['Is this rejected (Slice / Miner)'] == 'Rejected']['Name'].value_counts()
        if not rejected_by_reviewer.empty:
            reviewer_with_most_rejected = rejected_by_reviewer.index[0]
    
    return jsonify({
        'total_submissions': total_submissions,
        'unique_members': unique_members,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'changed_count': changed_count,
        'most_common_mistake': most_common_mistake,
        'reviewer_with_most_rejected': reviewer_with_most_rejected
    })

@data_bp.route('/analytics/user/<name>', methods=['GET'])
@require_auth
def get_user_analytics(name):
    """Get analytics for a specific user"""
    user_data = session.get('user')
    
    # Users can only access their own analytics unless they're admin
    if user_data.get('role') != 'admin' and user_data.get('name') != name:
        return jsonify({'error': 'Access denied'}), 403
    
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    # Filter by user name
    user_df = df[df['Name'] == name]
    
    if user_df.empty:
        return jsonify({'error': 'No data found for this user'}), 404
    
    # Calculate user-specific statistics
    total_submitted = len(user_df)
    
    accepted_count = len(user_df[user_df['Is this rejected (Slice / Miner)'] == 'Accepted']) if 'Is this rejected (Slice / Miner)' in user_df.columns else 0
    rejected_count = len(user_df[user_df['Is this rejected (Slice / Miner)'] == 'Rejected']) if 'Is this rejected (Slice / Miner)' in user_df.columns else 0
    
    # Tasks reviewed by leader
    leader_reviewed = len(user_df[user_df['Leader Name'].notna()]) if 'Leader Name' in user_df.columns else 0
    
    # Tasks changed by leader
    changed_by_leader = len(user_df[user_df['Is this Changed (Slice / Miner)'].notna()]) if 'Is this Changed (Slice / Miner)' in user_df.columns else 0
    
    # Alignment with QC
    aligned_column = 'Are The Qc And the reviewer allign on the same answer'
    fully_aligned = 0
    misaligned = 0
    if aligned_column in user_df.columns:
        aligned_data = user_df[aligned_column].value_counts()
        fully_aligned = aligned_data.get('Yes', 0)
        misaligned = aligned_data.get('No', 0)
    
    # Last submission date
    last_submission = None
    if 'Timestamp' in user_df.columns:
        timestamps = pd.to_datetime(user_df['Timestamp'], errors='coerce')
        if not timestamps.isna().all():
            last_submission = timestamps.max().isoformat()
    
    # Reason for reviewer mistakes (for pie chart)
    mistake_reasons = {}
    mistake_column = 'In you opinion, What is the reason for reviewer mistake?'
    if mistake_column in user_df.columns:
        mistake_counts = user_df[mistake_column].value_counts()
        mistake_reasons = mistake_counts.to_dict()
    
    return jsonify({
        'total_submitted': total_submitted,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'leader_reviewed': leader_reviewed,
        'changed_by_leader': changed_by_leader,
        'fully_aligned': fully_aligned,
        'misaligned': misaligned,
        'last_submission': last_submission,
        'mistake_reasons': mistake_reasons
    })

@data_bp.route('/analytics/my', methods=['GET'])
@require_auth
def get_my_analytics():
    """Get analytics for the current authenticated user"""
    user_data = session.get('user')
    user_name = user_data.get('name')
    
    if not user_name:
        return jsonify({'error': 'User name not found'}), 400
    
    return get_user_analytics(user_name)

@data_bp.route('/analytics/charts/rejection-by-task-type', methods=['GET'])
@require_admin
def get_rejection_by_task_type():
    """Get rejection rate by task type for charts (admin only)"""
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    if 'Task Type' not in df.columns or 'Is this rejected (Slice / Miner)' not in df.columns:
        return jsonify({'error': 'Required columns not found'}), 404
    
    # Group by task type and calculate rejection rates
    task_type_stats = df.groupby('Task Type')['Is this rejected (Slice / Miner)'].value_counts().unstack(fill_value=0)
    
    result = []
    for task_type in task_type_stats.index:
        accepted = task_type_stats.loc[task_type].get('Accepted', 0)
        rejected = task_type_stats.loc[task_type].get('Rejected', 0)
        total = accepted + rejected
        rejection_rate = (rejected / total * 100) if total > 0 else 0
        
        result.append({
            'task_type': task_type,
            'accepted': int(accepted),
            'rejected': int(rejected),
            'total': int(total),
            'rejection_rate': round(rejection_rate, 2)
        })
    
    return jsonify(result)

@data_bp.route('/analytics/charts/submission-trend', methods=['GET'])
@require_admin
def get_submission_trend():
    """Get submission trend over time for line charts (admin only)"""
    df = load_submissions_data()
    if df.empty:
        return jsonify({'error': 'No data found'}), 404
    
    if 'Timestamp' not in df.columns:
        return jsonify({'error': 'Timestamp column not found'}), 404
    
    # Convert timestamp to datetime
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    
    # Group by date and count submissions
    df['Date'] = df['Timestamp'].dt.date
    daily_counts = df.groupby('Date').size().reset_index(name='count')
    
    # Convert to list of dictionaries
    result = []
    for _, row in daily_counts.iterrows():
        result.append({
            'date': row['Date'].isoformat(),
            'count': int(row['count'])
        })
    
    return jsonify(result)

