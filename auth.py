from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email, EmailNotValidError
import pyotp
import qrcode
import io
import base64
import json
import secrets
import random
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from models import User, LoginLog
from app import db
from email_service import send_welcome_email, send_email_verification_otp
from mail_service import send_otp_email, send_welcome_email as send_welcome_mail
import random

bp = Blueprint('auth', __name__)

# Invite codes for role-based registration (kept secure and not exposed to frontend)
INVITE_CODES = {
    'clinic': '947316',  # Healthcare Provider Secret Code
    'admin': '583927'    # Administrator Secret Code
}

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        invite_code = request.form.get('invite_code', '').strip()
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username.lower()).first()
        
        def log_login_attempt(user_id, success, failure_reason=None):
            """Log login attempt for admin tracking"""
            login_log = LoginLog(
                user_id=user_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                success=success,
                failure_reason=failure_reason
            )
            db.session.add(login_log)
            
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                log_login_attempt(user.id, False, 'Account deactivated')
                db.session.commit()
                flash('Your account has been deactivated. Please contact support for assistance.', 'error')
                return render_template('login.html')
            # Skip email verification check for now (can be re-enabled when email service is configured)
            # elif not user.email_verified:
            #     log_login_attempt(user.id, False, 'Email not verified')
            #     db.session.commit()
            #     # Store user ID for verification
            #     session['verify_user_id'] = user.id
            #     flash('Please verify your email address before logging in.', 'warning')
            #     return redirect(url_for('auth.verify_email'))
            else:
                # Check invite code for admin and clinic users during login
                if user.role in ['admin', 'clinic']:
                    if not invite_code:
                        log_login_attempt(user.id, False, f'Missing invite code for {user.role} login')
                        db.session.commit()
                        flash(f'Access code required for {user.role} login.', 'error')
                        return render_template('login.html')
                    elif invite_code != INVITE_CODES.get(user.role):
                        log_login_attempt(user.id, False, f'Invalid invite code for {user.role} login')
                        db.session.commit()
                        flash('Invalid access code.', 'error')
                        return render_template('login.html')
                
                log_login_attempt(user.id, True)
                db.session.commit()
                login_user(user, remember=remember)
                
                # Redirect based on user role
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'clinic':
                    return redirect(url_for('hospital.dashboard'))
                else:
                    return redirect(url_for('index'))
        else:
            if user:
                log_login_attempt(user.id, False, 'Invalid password')
                db.session.commit()
            else:
                # Log attempt with email for tracking
                login_log = LoginLog(
                    user_id=None,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    success=False,
                    failure_reason=f'User not found: {username}'
                )
                db.session.add(login_log)
                db.session.commit()
            
            flash('Invalid username or password. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '').lower().strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        invite_code = request.form.get('invite_code', '').strip()
        
        # Validation
        errors = []
        
        if not all([email, username, password, confirm_password, role, first_name, last_name]):
            errors.append('Please fill in all required fields.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if role not in ['patient', 'clinic', 'admin']:
            errors.append('Invalid role selected.')
        
        # No invite codes required during registration anymore
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')
            
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            errors.append('An account with this username already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User()
            user.email = email
            user.username = username.lower()
            user.password_hash = generate_password_hash(password)
            user.role = role
            user.first_name = first_name
            user.last_name = last_name
            user.phone = phone or None
            user.address = address or None
            
            # Generate real OTP for email verification  
            import random
            otp_code = str(random.randint(100000, 999999))  # 6-digit OTP
            user.email_verification_token = otp_code
            user.email_verification_expires = datetime.utcnow() + timedelta(minutes=15)
            user.email_verification_sent_at = datetime.utcnow()
            user.email_verified = False
            
            db.session.add(user)
            db.session.commit()
            
            # Send real OTP email
            from mail_service import send_otp_email
            if send_otp_email(user.email, user.full_name or user.username, otp_code):
                session['verify_user_id'] = user.id
                flash('Registration successful! Please check your email for verification code.', 'success')
                return redirect(url_for('auth.verify_email'))
            else:
                flash('Registration successful, but email verification failed. Please contact support.', 'warning')
                return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('user_profile.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            # Validate email
            email = request.form.get('email', '').strip().lower()
            
            try:
                validate_email(email)
            except EmailNotValidError:
                flash('Please enter a valid email address.', 'error')
                return render_template('edit_profile.html')
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                flash('This email is already in use by another account.', 'error')
                return render_template('edit_profile.html')
            
            # Update user information
            current_user.email = email
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.phone = request.form.get('phone', '').strip() or None
            current_user.address = request.form.get('address', '').strip() or None
            
            # Change password if provided
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password:
                if not current_password:
                    flash('Current password is required to change password.', 'error')
                    return render_template('edit_profile.html')
                
                if not check_password_hash(current_user.password_hash, current_password):
                    flash('Current password is incorrect.', 'error')
                    return render_template('edit_profile.html')
                
                if new_password != confirm_password:
                    flash('New passwords do not match.', 'error')
                    return render_template('edit_profile.html')
                
                if len(new_password) < 6:
                    flash('Password must be at least 6 characters long.', 'error')
                    return render_template('edit_profile.html')
                
                current_user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.settings'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
    
    return render_template('edit_profile.html')

@bp.route('/profile/2fa')
@login_required
def two_factor_setup():
    if current_user.two_factor_enabled:
        return render_template('2fa_manage.html')
    
    # Generate new secret for setup
    secret = pyotp.random_base32()
    session['temp_2fa_secret'] = secret
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        current_user.email,
        issuer_name="SierraWings Emergency Medical"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    qr_code_data = base64.b64encode(img_buffer.getvalue()).decode()
    
    return render_template('2fa_setup.html', 
                         secret=secret, 
                         qr_code=qr_code_data)

@bp.route('/profile/2fa/verify', methods=['POST'])
@login_required
def verify_2fa_setup():
    temp_secret = session.get('temp_2fa_secret')
    if not temp_secret:
        flash('2FA setup session expired. Please try again.', 'error')
        return redirect(url_for('auth.two_factor_setup'))
    
    token = request.form.get('token')
    if not token:
        flash('Please enter the verification code.', 'error')
        return redirect(url_for('auth.two_factor_setup'))
    
    totp = pyotp.TOTP(temp_secret)
    if totp.verify(token):
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Save 2FA settings
        current_user.two_factor_enabled = True
        current_user.two_factor_secret = temp_secret
        current_user.backup_codes = json.dumps(backup_codes)
        
        db.session.commit()
        session.pop('temp_2fa_secret', None)
        
        flash('Two-factor authentication enabled successfully!', 'success')
        return render_template('2fa_backup_codes.html', backup_codes=backup_codes)
    else:
        flash('Invalid verification code. Please try again.', 'error')
        return redirect(url_for('auth.two_factor_setup'))

@bp.route('/profile/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    token = request.form.get('token')
    password = request.form.get('password')
    
    if not password or not current_user.password_hash or not check_password_hash(current_user.password_hash, password):
        flash('Incorrect password.', 'error')
        return redirect(url_for('auth.two_factor_setup'))
    
    # Verify 2FA token or backup code
    is_valid = False
    if current_user.two_factor_secret:
        totp = pyotp.TOTP(current_user.two_factor_secret)
        if token and totp.verify(token):
            is_valid = True
        else:
            # Check backup codes
            backup_codes = json.loads(current_user.backup_codes or '[]')
            if token and token.upper() in backup_codes:
                backup_codes.remove(token.upper())
                current_user.backup_codes = json.dumps(backup_codes)
                is_valid = True
    
    if is_valid:
        current_user.two_factor_enabled = False
        current_user.two_factor_secret = None
        current_user.backup_codes = None
        db.session.commit()
        flash('Two-factor authentication disabled.', 'success')
    else:
        flash('Invalid verification code.', 'error')
    
    return redirect(url_for('auth.profile'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/settings')
@login_required
def settings():
    return render_template('profile.html', user=current_user)

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate secure reset token
            import secrets
            import string
            reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
            user.reset_token = reset_token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # Send professional reset email
            from email_service import send_password_reset_email
            send_password_reset_email(user.email, user.full_name, reset_token)
            
        # Always show success message for security
        flash('Password reset instructions have been sent to your email address if it exists in our system.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        flash('Invalid or expired reset token. Please request a new password reset.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Validate password strength
        import re
        if not (re.search(r'[A-Z]', password) and 
                re.search(r'[a-z]', password) and 
                re.search(r'\d', password) and 
                re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
            flash('Password must contain uppercase, lowercase, number, and special character.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update password and clear reset token
        user.password_hash = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        
        flash('Your password has been successfully updated. You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@bp.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    """Email verification with OTP"""
    if 'verify_user_id' not in session:
        flash('No verification pending. Please register first.', 'error')
        return redirect(url_for('auth.register'))
    
    user_id = session['verify_user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('Verification session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    if user.email_verified:
        flash('Email already verified. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        
        if not otp_code:
            flash('Please enter the verification code.', 'error')
            return render_template('verify_otp.html', user=user)
        
        # Check if OTP expired
        if datetime.utcnow() > user.email_verification_expires:
            flash('Verification code expired. Please request a new one.', 'error')
            return render_template('verify_otp.html', user=user, expired=True)
        
        # Verify OTP
        if otp_code == user.email_verification_token:
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_expires = None
            db.session.commit()
            
            # Clear session
            session.pop('verify_user_id', None)
            
            # Send role-specific welcome email
            from mail_service import send_welcome_email
            send_welcome_email(user.email, user.full_name or user.username, user.role)
            
            flash('Email verified successfully! Welcome to SierraWings!', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid verification code. Please try again.', 'error')
            return render_template('verify_otp.html', user=user)
    
    return render_template('verify_otp.html', user=user)

@bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend email verification OTP"""
    if 'verify_user_id' not in session:
        flash('No verification pending. Please register first.', 'error')
        return redirect(url_for('auth.register'))
    
    user_id = session['verify_user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('Verification session expired. Please register again.', 'error')
        return redirect(url_for('auth.register'))
    
    if user.email_verified:
        flash('Email already verified. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    # Generate new OTP
    import random
    otp_code = str(random.randint(100000, 999999))
    user.email_verification_token = otp_code
    user.email_verification_expires = datetime.utcnow() + timedelta(minutes=15)
    user.email_verification_sent_at = datetime.utcnow()
    db.session.commit()
    
    # Send new OTP email
    from mail_service import send_otp_email
    if send_otp_email(user.email, user.full_name or user.username, otp_code):
        flash('New verification code sent to your email!', 'success')
    else:
        flash('Failed to send verification code. Please try again.', 'error')
    
    return redirect(url_for('auth.verify_email'))
