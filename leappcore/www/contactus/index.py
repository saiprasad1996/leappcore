import frappe
from frappe import _


def get_context(context):
    """Contact Us page context"""
    # Disable CSRF check for contact form
    frappe.flags.ignore_csrf_check = True
    
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.no_cache = 1
    
    # Handle form submission
    if frappe.request.method == "POST":
        try:
            save_contact_response()
            context.success_message = _("Thank you for contacting us! We'll get back to you soon.")
        except Exception as e:
            frappe.clear_messages()
            context.error_message = str(e)
            frappe.log_error(frappe.get_traceback(), "Contact Form Submission Error")
    
    return context


def save_contact_response():
    """Save contact form submission"""
    # Get form data
    contact_name = frappe.form_dict.get("contact_name")
    email = frappe.form_dict.get("email")
    phone = frappe.form_dict.get("phone")
    message = frappe.form_dict.get("message")
    
    # Validate required fields
    if not contact_name or not message:
        frappe.throw(_("Please fill in all required fields"), frappe.ValidationError)
    
    if not email and not phone:
        frappe.throw(_("Please provide either an email address or phone number"), frappe.ValidationError)
    
    # Validate email format if provided
    if email:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            frappe.throw(_("Please provide a valid email address"), frappe.ValidationError)
    
    try:
        # Create contact response
        contact_response = frappe.get_doc({
            "doctype": "ContactResponse",
            "contact_name": contact_name,
            "email": email,
            "phone": phone,
            "message": message
        })
        contact_response.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Send notification email to admin
        send_admin_notification(contact_name, email, phone, message)
        
        # Send confirmation email to user
        if email:
            send_user_confirmation(email, contact_name)
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Contact Response Save Error")
        raise


def send_admin_notification(contact_name, email, phone, message):
    """Send notification to admin about new contact submission"""
    try:
        admin_emails = frappe.get_all("User", 
            filters={"role": "System Manager", "enabled": 1},
            fields=["email"],
            pluck="email"
        )
        
        if not admin_emails:
            return
        
        subject = f"New Contact Form Submission from {contact_name}"
        
        email_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc700;">New Contact Form Submission</h2>
            <p>You have received a new message from the LEAPP contact form:</p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: bold;">Name:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{contact_name}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: bold;">Email:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{email or 'Not provided'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; font-weight: bold;">Phone:</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{phone or 'Not provided'}</td>
                </tr>
            </table>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #ffc700; margin: 20px 0;">
                <p style="margin: 0; font-weight: bold;">Message:</p>
                <p style="margin: 10px 0 0 0;">{message}</p>
            </div>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                This is an automated notification from the LEAPP contact form.
            </p>
        </div>
        """
        
        frappe.sendmail(
            recipients=admin_emails,
            subject=subject,
            message=email_message,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Contact Form Admin Notification Error")


def send_user_confirmation(email, contact_name):
    """Send confirmation email to user"""
    try:
        subject = _("Thank you for contacting LEAPP!")
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc700;">Thank You for Contacting Us!</h2>
            <p>Dear {contact_name},</p>
            
            <p>We have received your message and appreciate you taking the time to contact us.</p>
            
            <p>Our team will review your inquiry and get back to you as soon as possible, typically within 24-48 hours.</p>
            
            <p>In the meantime, feel free to explore our platform:</p>
            <ul>
                <li><a href="{frappe.utils.get_url('/courses')}" style="color: #ffc700;">Browse Courses</a></li>
                <li><a href="{frappe.utils.get_url('/events')}" style="color: #ffc700;">View Events</a></li>
                <li><a href="{frappe.utils.get_url('/aboutus')}" style="color: #ffc700;">Learn About Us</a></li>
            </ul>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>The LEAPP Team</strong>
            </p>
            
            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
            <p style="font-size: 12px; color: #666;">
                This is an automated confirmation email. Please do not reply to this email.
            </p>
        </div>
        """
        
        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Contact Form User Confirmation Error")
