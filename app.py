from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from config import Config
import time
from gotrue.errors import AuthApiError

app = Flask(__name__)
app.config.from_object(Config)

SUPABASE_URL = ''
SUPABASE_KEY = ''

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        data = request.form
        email = data['email']
        password = data['password']
        
        response = supabase.auth.sign_in_with_password({'email': email, 'password': password})
        
        if response.get('error'):
            return jsonify(response['error']), 400
        
        return jsonify(response['data']), 200
    
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        email = data['email']
        password = data['password']
        org_name = data['org_name']
        
        try:
            user_response = supabase.auth.sign_up({'email': email, 'password': password})
        except AuthApiError as e:
            if 'rate limit' in str(e).lower():
                return jsonify({'error': 'Too many requests. Please try again later.'}), 429
            else:
                return jsonify({'error': str(e)}), 400
        
        if user_response.get('error'):
            return jsonify(user_response['error']), 400
        
        user_id = user_response['data']['user']['id']
        
        org_response = supabase.table('organisation').insert({
            'name': org_name,
            'status': 0,
            'personal': False,
            'created_at': int(time.time())
        }).execute()
        
        if org_response.status_code != 201:
            return jsonify(org_response['data']), 400
        
        org_id = org_response.data[0]['id']
        
        member_response = supabase.table('member').insert({
            'org_id': org_id,
            'user_id': user_id,
            'role_id': 1,
            'status': 0,
            'created_at': int(time.time())
        }).execute()
        
        if member_response.status_code != 201:
            return jsonify(member_response['data']), 400
        
        return jsonify({'message': 'User and organisation created successfully'}), 201
    
    return render_template('signup.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        data = request.form
        email = data['email']
        
        response = supabase.auth.api.reset_password_for_email(email)
        
        if response.get('error'):
            return jsonify(response['error']), 400
        
        return jsonify({'message': 'Password reset email sent'}), 200
    
    return render_template('reset_password.html')

@app.route('/invite-member', methods=['GET', 'POST'])
def invite_member():
    if request.method == 'POST':
        data = request.form
        org_id = data['org_id']
        user_id = data['user_id']
        role_id = data['role_id']
        
        response = supabase.table('member').insert({
            'org_id': org_id,
            'user_id': user_id,
            'role_id': role_id,
            'status': 0,
            'created_at': int(time.time())
        }).execute()
        
        if response.status_code != 201:
            return jsonify(response['data']), 400
        
        return jsonify({'message': 'Member invited successfully'}), 201
    
    return render_template('invite_member.html')

@app.route('/delete-member', methods=['GET', 'POST'])
def delete_member():
    if request.method == 'POST':
        data = request.form
        member_id = data['member_id']
        
        response = supabase.table('member').delete().eq('id', member_id).execute()
        
        if response.status_code != 200:
            return jsonify(response['data']), 400
        
        return jsonify({'message': 'Member deleted successfully'}), 200
    
    return render_template('delete_member.html')

@app.route('/update-member-role', methods=['GET', 'POST'])
def update_member_role():
    if request.method == 'POST':
        data = request.form
        member_id = data['member_id']
        role_id = data['role_id']
        
        response = supabase.table('member').update({'role_id': role_id}).eq('id', member_id).execute()
        
        if response.status_code != 200:
            return jsonify(response['data']), 400
        
        return jsonify({'message': 'Member role updated successfully'}), 200
    
    return render_template('update_member_role.html')

if __name__ == '__main__':
    app.run(debug=True)

