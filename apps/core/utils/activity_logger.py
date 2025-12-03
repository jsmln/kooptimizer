"""
Activity Logger Utility
======================
Centralized utility for logging user activities across the system.
"""
from django.db import transaction
from apps.cooperatives.models import ActivityLog
from apps.users.models import User
from apps.account_management.models import Cooperatives, Admin, Staff as AccountStaff, Officers
from apps.cooperatives.models import Officer as CoopOfficer


def get_user_name(user_id, role):
    """Get the full name of a user based on their role"""
    try:
        if role == 'admin':
            admin = Admin.objects.get(user_id=user_id)
            return admin.fullname or admin.user.username if admin.user else 'Unknown Admin'
        elif role == 'staff':
            staff = AccountStaff.objects.get(user_id=user_id)
            return staff.fullname or staff.user.username if staff.user else 'Unknown Staff'
        elif role == 'officer':
            officer = CoopOfficer.objects.filter(user_id=user_id).first()
            if officer:
                return officer.fullname or officer.user.username if officer.user else 'Unknown Officer'
            return 'Unknown Officer'
        else:
            user = User.objects.get(user_id=user_id)
            return user.username
    except Exception as e:
        print(f"Error getting user name: {e}")
        return 'Unknown User'


def get_cooperative_name(coop_id):
    """Get the name of a cooperative"""
    try:
        coop = Cooperatives.objects.get(coop_id=coop_id)
        return coop.cooperative_name
    except Cooperatives.DoesNotExist:
        return 'Unknown Cooperative'
    except Exception as e:
        print(f"Error getting cooperative name: {e}")
        return 'Unknown Cooperative'


def log_activity(action_type, description, user_id=None, user_role=None, affected_user_id=None, 
                affected_user_role=None, coop_id=None, user_fullname=None, user_organization=None):
    """
    Log an activity to the activity_logs table.
    
    Args:
        action_type: Type of action (e.g., 'create_user', 'deactivate_user', 'approve_cooperative')
        description: Detailed description of the action
        user_id: ID of the user performing the action
        user_role: Role of the user performing the action
        affected_user_id: ID of the user affected by the action (if applicable)
        affected_user_role: Role of the affected user (if applicable)
        coop_id: ID of the cooperative affected (if applicable)
        user_fullname: Full name of the user performing the action (optional, will be fetched if not provided)
        user_organization: Organization/cooperative name of the user (optional)
    """
    try:
        with transaction.atomic():
            # Get user fullname if not provided
            if not user_fullname and user_id and user_role:
                user_fullname = get_user_name(user_id, user_role)
            
            # Get user organization if not provided (for officers)
            if not user_organization and user_id and user_role == 'officer':
                try:
                    officer = CoopOfficer.objects.filter(user_id=user_id).first()
                    if officer and officer.coop:
                        user_organization = officer.coop.cooperative_name
                except Exception:
                    pass
            
            # Get user object if user_id is provided
            user_obj = None
            if user_id:
                try:
                    user_obj = User.objects.get(user_id=user_id)
                except User.DoesNotExist:
                    pass
            
            # Get cooperative object if coop_id is provided
            coop_obj = None
            if coop_id:
                try:
                    coop_obj = Cooperatives.objects.get(coop_id=coop_id)
                except Cooperatives.DoesNotExist:
                    pass
            
            # Check for duplicate log entry within the last 10 seconds
            # This prevents duplicate logs from multiple rapid calls, frontend double-clicks, or retries
            from django.utils import timezone
            from datetime import timedelta
            
            # Build comprehensive duplicate check query
            # Always check: action_type, description, user (performer), and time window
            # This ensures one action = one log, even with rapid calls, retries, or double-clicks
            duplicate_filter = {
                'action_type': action_type,
                'description': description,
                'created_at__gte': timezone.now() - timedelta(seconds=10)
            }
            
            # Always check user (performer) - this is the key identifier
            if user_obj:
                duplicate_filter['user'] = user_obj
            elif user_fullname:
                # Fallback: check by user_fullname if user_obj is not available
                duplicate_filter['user_fullname'] = user_fullname
            
            # Add cooperative check for cooperative-related actions to ensure uniqueness
            if action_type in ['approve_cooperative', 'decline_cooperative', 'deactivate_cooperative', 
                             'reactivate_cooperative', 'update_cooperative_profile']:
                if coop_obj:
                    duplicate_filter['coop'] = coop_obj
            
            # Check for duplicate
            recent_duplicate = ActivityLog.objects.filter(**duplicate_filter).first()
            
            # Only create log if no recent duplicate exists
            if not recent_duplicate:
                ActivityLog.objects.create(
                    action_type=action_type,
                    description=description,
                    user_fullname=user_fullname,
                    user_organization=user_organization,
                    user=user_obj,
                    coop=coop_obj
                )
    except Exception as e:
        # Log error but don't fail the main operation
        print(f"Error logging activity: {e}")
        import traceback
        traceback.print_exc()


# Convenience functions for common actions
def log_user_creation(performer_id, performer_role, created_user_id, created_user_role, created_user_name):
    """Log when a user is created"""
    log_activity(
        action_type='create_user',
        description=f'Created {created_user_role} account for {created_user_name}',
        user_id=performer_id,
        user_role=performer_role,
        affected_user_id=created_user_id,
        affected_user_role=created_user_role,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_user_deactivation(performer_id, performer_role, deactivated_user_id, deactivated_user_role, deactivated_user_name):
    """Log when a user is deactivated"""
    log_activity(
        action_type='deactivate_user',
        description=f'Deactivated {deactivated_user_role} account: {deactivated_user_name}',
        user_id=performer_id,
        user_role=performer_role,
        affected_user_id=deactivated_user_id,
        affected_user_role=deactivated_user_role,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_user_reactivation(performer_id, performer_role, reactivated_user_id, reactivated_user_role, reactivated_user_name):
    """Log when a user is reactivated"""
    log_activity(
        action_type='reactivate_user',
        description=f'Reactivated {reactivated_user_role} account: {reactivated_user_name}',
        user_id=performer_id,
        user_role=performer_role,
        affected_user_id=reactivated_user_id,
        affected_user_role=reactivated_user_role,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_user_update(performer_id, performer_role, updated_user_id, updated_user_role, updated_user_name):
    """Log when user data is updated"""
    log_activity(
        action_type='update_user',
        description=f'Updated {updated_user_role} account data: {updated_user_name}',
        user_id=performer_id,
        user_role=performer_role,
        affected_user_id=updated_user_id,
        affected_user_role=updated_user_role,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_cooperative_approval(performer_id, performer_role, coop_id, coop_name):
    """Log when a cooperative profile is approved"""
    log_activity(
        action_type='approve_cooperative',
        description=f'Approved cooperative profile: {coop_name}',
        user_id=performer_id,
        user_role=performer_role,
        coop_id=coop_id,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_cooperative_decline(performer_id, performer_role, coop_id, coop_name):
    """Log when a cooperative profile is declined/cancelled"""
    log_activity(
        action_type='decline_cooperative',
        description=f'Declined/Cancelled approval for cooperative profile: {coop_name}',
        user_id=performer_id,
        user_role=performer_role,
        coop_id=coop_id,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_cooperative_deactivation(performer_id, performer_role, coop_id, coop_name):
    """Log when a cooperative is deactivated"""
    log_activity(
        action_type='deactivate_cooperative',
        description=f'Deactivated cooperative: {coop_name}',
        user_id=performer_id,
        user_role=performer_role,
        coop_id=coop_id,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_cooperative_reactivation(performer_id, performer_role, coop_id, coop_name):
    """Log when a cooperative is reactivated"""
    log_activity(
        action_type='reactivate_cooperative',
        description=f'Reactivated cooperative: {coop_name}',
        user_id=performer_id,
        user_role=performer_role,
        coop_id=coop_id,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_announcement_sent(performer_id, performer_role, announcement_type, recipient_count, recipient_type='cooperatives', coop_names=None, officer_names=None):
    """Log when an announcement is sent"""
    # Build description with recipient details
    description_parts = [f'Sent {announcement_type} announcement']
    
    if officer_names and len(officer_names) > 0:
        # If we have specific officer names, use them
        if len(officer_names) <= 3:
            names_str = ', '.join(officer_names)
        else:
            names_str = ', '.join(officer_names[:3]) + f' and {len(officer_names) - 3} others'
        description_parts.append(f'to {names_str}')
        
        if coop_names and len(coop_names) > 0:
            if len(coop_names) == 1:
                description_parts.append(f'of cooperative {coop_names[0]}')
            else:
                description_parts.append(f'of cooperatives {", ".join(coop_names[:2])}{" and more" if len(coop_names) > 2 else ""}')
    elif coop_names and len(coop_names) > 0:
        # If we have cooperative names, use them
        if len(coop_names) == 1:
            description_parts.append(f'to officers of cooperative {coop_names[0]}')
        else:
            description_parts.append(f'to officers of {len(coop_names)} cooperatives')
    else:
        # Fallback to count
        description_parts.append(f'to {recipient_count} {recipient_type}')
    
    description = ' '.join(description_parts)
    
    log_activity(
        action_type='send_announcement',
        description=description,
        user_id=performer_id,
        user_role=performer_role,
        user_fullname=get_user_name(performer_id, performer_role)
    )


def log_officer_profile_update(officer_id, coop_id, coop_name):
    """Log when an officer updates their cooperative profile"""
    log_activity(
        action_type='update_cooperative_profile',
        description=f'Updated cooperative profile: {coop_name}',
        user_id=officer_id,
        user_role='officer',
        coop_id=coop_id,
        user_fullname=get_user_name(officer_id, 'officer'),
        user_organization=coop_name
    )

