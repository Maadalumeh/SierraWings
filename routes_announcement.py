"""
SierraWings Announcement System
Handles admin announcements, app updates, and maintenance alerts
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models import Announcement, User
from functools import wraps
import logging

announcement_bp = Blueprint('announcements', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@announcement_bp.route('/announcements')
@login_required
def view_announcements():
    """View announcements for patients and hospitals"""
    if current_user.role == 'admin':
        return redirect(url_for('announcements.admin_announcements'))
    
    # Get all active announcements for current user's role
    announcements = Announcement.query.filter(
        (Announcement.target_role == current_user.role) | 
        (Announcement.target_role == 'all')
    ).filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
    
    return render_template('announcements/view_announcements.html', 
                         announcements=announcements)

@announcement_bp.route('/admin/announcements')
@login_required
@admin_required
def admin_announcements():
    """Admin dashboard for managing announcements"""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements/admin_announcements.html', 
                         announcements=announcements)

@announcement_bp.route('/admin/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_announcement():
    """Create new announcement"""
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        announcement_type = request.form.get('announcement_type')
        target_role = request.form.get('target_role')
        priority = request.form.get('priority', 'normal')
        
        if not title or not message:
            flash('Title and message are required.', 'error')
            return render_template('announcements/create_announcement.html')
        
        announcement = Announcement(
            title=title,
            message=message,
            announcement_type=announcement_type,
            target_role=target_role,
            priority=priority,
            admin_id=current_user.id,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        try:
            db.session.add(announcement)
            db.session.commit()
            flash(f'Announcement "{title}" created successfully!', 'success')
            
            # Log the announcement creation
            logging.info(f"Admin {current_user.username} created announcement: {title}")
            
            return redirect(url_for('announcements.admin_announcements'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating announcement. Please try again.', 'error')
            logging.error(f"Error creating announcement: {str(e)}")
    
    return render_template('announcements/create_announcement.html')

@announcement_bp.route('/admin/announcements/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(announcement_id):
    """Edit existing announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.message = request.form.get('message')
        announcement.announcement_type = request.form.get('announcement_type')
        announcement.target_role = request.form.get('target_role')
        announcement.priority = request.form.get('priority', 'normal')
        announcement.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Announcement updated successfully!', 'success')
            return redirect(url_for('announcements.admin_announcements'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating announcement. Please try again.', 'error')
            logging.error(f"Error updating announcement: {str(e)}")
    
    return render_template('announcements/edit_announcement.html', 
                         announcement=announcement)

@announcement_bp.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    """Delete announcement"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting announcement. Please try again.', 'error')
        logging.error(f"Error deleting announcement: {str(e)}")
    
    return redirect(url_for('announcements.admin_announcements'))

@announcement_bp.route('/admin/announcements/<int:announcement_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_announcement(announcement_id):
    """Toggle announcement active status"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    try:
        announcement.is_active = not announcement.is_active
        announcement.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = 'activated' if announcement.is_active else 'deactivated'
        flash(f'Announcement {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating announcement status. Please try again.', 'error')
        logging.error(f"Error toggling announcement: {str(e)}")
    
    return redirect(url_for('announcements.admin_announcements'))

@announcement_bp.route('/announcements/<int:announcement_id>/dismiss', methods=['POST'])
@login_required
def dismiss_announcement(announcement_id):
    """Dismiss announcement for current user"""
    from models import AnnouncementDismissal
    
    # Check if already dismissed
    existing_dismissal = AnnouncementDismissal.query.filter_by(
        user_id=current_user.id,
        announcement_id=announcement_id
    ).first()
    
    if not existing_dismissal:
        dismissal = AnnouncementDismissal(
            user_id=current_user.id,
            announcement_id=announcement_id,
            dismissed_at=datetime.utcnow()
        )
        
        try:
            db.session.add(dismissal)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error dismissing announcement: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': True})

@announcement_bp.route('/api/announcements/count')
@login_required
def get_announcement_count():
    """Get count of unread announcements for current user"""
    from models import AnnouncementDismissal
    
    # Get all active announcements for user's role
    announcements = Announcement.query.filter(
        (Announcement.target_role == current_user.role) | 
        (Announcement.target_role == 'all')
    ).filter_by(is_active=True).all()
    
    # Get dismissed announcements for current user
    dismissed_ids = [d.announcement_id for d in AnnouncementDismissal.query.filter_by(
        user_id=current_user.id
    ).all()]
    
    # Count unread announcements
    unread_count = len([a for a in announcements if a.id not in dismissed_ids])
    
    return jsonify({
        'unread_count': unread_count,
        'total_count': len(announcements)
    })

@announcement_bp.route('/api/announcements/latest')
@login_required
def get_latest_announcements():
    """Get latest announcements for current user"""
    from models import AnnouncementDismissal
    
    announcements = Announcement.query.filter(
        (Announcement.target_role == current_user.role) | 
        (Announcement.target_role == 'all')
    ).filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(5).all()
    
    # Get dismissed announcements for current user
    dismissed_ids = [d.announcement_id for d in AnnouncementDismissal.query.filter_by(
        user_id=current_user.id
    ).all()]
    
    announcements_data = []
    for announcement in announcements:
        announcements_data.append({
            'id': announcement.id,
            'title': announcement.title,
            'message': announcement.message,
            'type': announcement.announcement_type,
            'priority': announcement.priority,
            'created_at': announcement.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_dismissed': announcement.id in dismissed_ids
        })
    
    return jsonify(announcements_data)

@announcement_bp.route('/api/announcements/preview')
@login_required
def get_announcement_preview():
    """Get announcement preview for dashboard widget"""
    from models import AnnouncementDismissal
    
    try:
        # Get all active announcements for user's role
        announcements = Announcement.query.filter(
            (Announcement.target_role == current_user.role) | 
            (Announcement.target_role == 'all')
        ).filter_by(is_active=True).order_by(Announcement.created_at.desc()).limit(10).all()
        
        # Get dismissed announcements for current user
        dismissed_ids = [d.announcement_id for d in AnnouncementDismissal.query.filter_by(
            user_id=current_user.id
        ).all()]
        
        # Filter out dismissed announcements
        active_announcements = [a for a in announcements if a.id not in dismissed_ids]
        
        announcements_data = []
        for announcement in active_announcements:
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.title,
                'message': announcement.message,
                'announcement_type': announcement.announcement_type,
                'priority': announcement.priority,
                'created_at': announcement.created_at.isoformat(),
                'view_url': url_for('announcements.view_announcements')
            })
        
        return jsonify({
            'announcements': announcements_data,
            'total': len(announcements_data)
        })
        
    except Exception as e:
        logging.error(f"Error getting announcement preview: {str(e)}")
        return jsonify({
            'announcements': [],
            'total': 0,
            'error': str(e)
        })