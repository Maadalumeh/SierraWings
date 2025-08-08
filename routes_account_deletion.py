"""
Account Deletion Request Routes
Handles user requests to delete their accounts
"""

from flask import jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import app, db
from models import AccountDeletionRequest, User
from datetime import datetime

@app.route('/request-account-deletion', methods=['POST'])
@login_required
def request_account_deletion():
    """Submit account deletion request"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        # Check if user already has a pending request
        existing_request = AccountDeletionRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({
                'success': False,
                'message': 'You already have a pending account deletion request.'
            })
        
        # Create new deletion request
        deletion_request = AccountDeletionRequest(
            user_id=current_user.id,
            reason=reason
        )
        
        db.session.add(deletion_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deletion request submitted successfully.',
            'request_date': deletion_request.requested_at.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error submitting request: {str(e)}'
        }), 500

@app.route('/account-deletion-status')
@login_required
def account_deletion_status():
    """Check if user has a pending deletion request"""
    try:
        existing_request = AccountDeletionRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({
                'success': True,
                'has_pending_request': True,
                'request_date': existing_request.requested_at.isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'has_pending_request': False
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'has_pending_request': False,
            'message': f'Error checking status: {str(e)}'
        }), 500

@app.route('/admin/account-deletion')
@login_required
def admin_account_deletion_panel():
    """Admin panel for managing account deletion requests"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        pending_requests = AccountDeletionRequest.query.filter_by(status='pending').all()
        approved_requests = AccountDeletionRequest.query.filter_by(status='approved').all()
        rejected_requests = AccountDeletionRequest.query.filter_by(status='rejected').all()
        
        return render_template('admin_account_deletion_panel.html',
                             pending_requests=pending_requests,
                             approved_requests=approved_requests,
                             rejected_requests=rejected_requests)
    except Exception as e:
        flash(f'Error loading deletion requests: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/account-deletion/<int:request_id>/process', methods=['POST'])
@login_required
def process_account_deletion_request(request_id):
    """Process account deletion request (approve/reject)"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        status = data.get('status')  # 'approved' or 'rejected'
        
        deletion_request = AccountDeletionRequest.query.get_or_404(request_id)
        
        if deletion_request.status != 'pending':
            return jsonify({
                'success': False,
                'message': 'Request has already been processed'
            })
        
        deletion_request.status = status
        deletion_request.processed_at = datetime.utcnow()
        deletion_request.processed_by = current_user.id
        
        # If approved, mark user account for deletion
        if status == 'approved':
            user = User.query.get(deletion_request.user_id)
            if user:
                user.is_active = False
                user.deletion_scheduled = True
                
                # Send notification email about approval
                try:
                    from mail_service import send_email
                    send_email(
                        user.email,
                        'Account Deletion Request Approved - SierraWings',
                        f'''
                        <h3>Account Deletion Request Approved</h3>
                        <p>Dear {user.username},</p>
                        <p>Your account deletion request has been approved. Your account will be permanently deleted within 7 days.</p>
                        <p>If you have any questions, please contact our support team.</p>
                        <p>Best regards,<br>SierraWings Team</p>
                        '''
                    )
                except Exception as e:
                    logging.error(f"Error sending approval email: {str(e)}")
        
        elif status == 'rejected':
            # Send notification email about rejection
            try:
                user = User.query.get(deletion_request.user_id)
                if user:
                    from mail_service import send_email
                    send_email(
                        user.email,
                        'Account Deletion Request Rejected - SierraWings',
                        f'''
                        <h3>Account Deletion Request Rejected</h3>
                        <p>Dear {user.username},</p>
                        <p>Your account deletion request has been reviewed and rejected.</p>
                        <p>If you have any questions about this decision, please contact our support team.</p>
                        <p>Best regards,<br>SierraWings Team</p>
                        '''
                    )
            except Exception as e:
                logging.error(f"Error sending rejection email: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Request {status} successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing request: {str(e)}'
        }), 500

@app.route('/admin/account-deletion/<int:request_id>/details')
@login_required
def get_account_deletion_details(request_id):
    """Get detailed information about an account deletion request"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        deletion_request = AccountDeletionRequest.query.get_or_404(request_id)
        user = User.query.get(deletion_request.user_id)
        
        return jsonify({
            'success': True,
            'request': {
                'id': deletion_request.id,
                'reason': deletion_request.reason,
                'status': deletion_request.status,
                'requested_at': deletion_request.requested_at.isoformat(),
                'processed_at': deletion_request.processed_at.isoformat() if deletion_request.processed_at else None,
                'feedback': getattr(deletion_request, 'feedback', None),
                'additional_info': getattr(deletion_request, 'additional_info', None),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching details: {str(e)}'
        }), 500

# Route is already defined in main routes.py file

@app.route('/admin/account_deletion_requests')
@login_required
def admin_account_deletion_requests():
    """Admin view for managing account deletion requests"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all deletion requests
    deletion_requests = AccountDeletionRequest.query.join(User).order_by(
        AccountDeletionRequest.requested_at.desc()
    ).all()
    
    return render_template('admin_account_deletion_requests.html', 
                         deletion_requests=deletion_requests)

@app.route('/admin/process_account_deletion/<int:request_id>', methods=['POST'])
@login_required
def process_account_deletion(request_id):
    """Process account deletion request (approve/reject)"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        deletion_request = AccountDeletionRequest.query.get_or_404(request_id)
        
        action = request.form.get('action')
        admin_notes = request.form.get('admin_notes', '')
        
        if action == 'approve':
            # Delete the user account
            user_to_delete = User.query.get(deletion_request.user_id)
            if user_to_delete:
                db.session.delete(user_to_delete)
            
            deletion_request.status = 'approved'
            flash(f'Account deletion approved for {user_to_delete.username}', 'success')
            
        elif action == 'reject':
            deletion_request.status = 'rejected'
            flash(f'Account deletion rejected for {deletion_request.user.username}', 'info')
        
        deletion_request.processed_at = datetime.utcnow()
        deletion_request.processed_by = current_user.id
        deletion_request.admin_notes = admin_notes
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing request: {str(e)}', 'error')
    
    return redirect(url_for('admin_account_deletion_requests'))

