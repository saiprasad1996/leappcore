import frappe
from frappe import _


@frappe.whitelist()
def record_interest(offering_id=None, event_id=None):
    """Record customer interest in an offering or event"""
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("Please log in to show interest"), frappe.AuthenticationError)
    
    # Check if user is a partner
    if "Leapp Partner" in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Partners cannot show interest in offerings or events"), frappe.ValidationError)
    
    if offering_id:
        return record_offering_interest(offering_id)
    elif event_id:
        return record_event_interest(event_id)
    else:
        frappe.throw(_("Please provide an offering ID or event ID"), frappe.ValidationError)


def record_offering_interest(offering_id):
    """Record customer interest in an offering"""
    # Get offering details
    if not frappe.db.exists("Offering", offering_id):
        frappe.throw(_("Offering not found"), frappe.DoesNotExistError)
    
    offering = frappe.get_doc("Offering", offering_id)
    customer = frappe.session.user
    provider = offering.provider
    
    # Check if interest already exists
    existing_interest = frappe.db.exists("Customer Interest", {
        "customer": customer,
        "offering": offering_id,
        "interest_type": "OFFERING"
    })
    
    if existing_interest:
        return {
            "success": True,
            "message": _("You've already shown interest in this offering"),
            "already_interested": True,
            "interest_id": existing_interest
        }
    
    try:
        # Create new interest
        interest = frappe.get_doc({
            "doctype": "Customer Interest",
            "customer": customer,
            "provider": provider,
            "interest_type": "OFFERING",
            "offering": offering_id,
            "status": "NEW"
        })
        interest.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Send notification to partner
        send_offering_interest_notification(customer, provider, offering)
        
        return {
            "success": True,
            "message": _("Thank you for showing interest! The partner will contact you soon."),
            "already_interested": False,
            "interest_id": interest.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Record Interest Error")
        frappe.throw(_("An error occurred. Please try again."))


def record_event_interest(event_id):
    """Record customer interest in an event"""
    # Get event details
    if not frappe.db.exists("Leapp Event", event_id):
        frappe.throw(_("Event not found"), frappe.DoesNotExistError)
    
    event = frappe.get_doc("Leapp Event", event_id)
    customer = frappe.session.user
    organizer = event.organizer
    
    # Check if interest already exists
    existing_interest = frappe.db.exists("Customer Interest", {
        "customer": customer,
        "event": event_id,
        "interest_type": "EVENT"
    })
    
    if existing_interest:
        return {
            "success": True,
            "message": _("You've already shown interest in this event"),
            "already_interested": True,
            "interest_id": existing_interest
        }
    
    try:
        # Create new interest
        interest = frappe.get_doc({
            "doctype": "Customer Interest",
            "customer": customer,
            "provider": organizer,
            "interest_type": "EVENT",
            "event": event_id,
            "status": "NEW"
        })
        interest.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Send notification to organizer
        send_event_interest_notification(customer, organizer, event)
        
        return {
            "success": True,
            "message": _("Thank you for showing interest! The organizer will contact you soon."),
            "already_interested": False,
            "interest_id": interest.name
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Record Event Interest Error")
        frappe.throw(_("An error occurred. Please try again."))


@frappe.whitelist()
def check_interest(offering_id=None, event_id=None):
    """Check if current user has shown interest in an offering or event"""
    if frappe.session.user == "Guest":
        return {"interested": False}
    
    if offering_id:
        existing_interest = frappe.db.exists("Customer Interest", {
            "customer": frappe.session.user,
            "offering": offering_id,
            "interest_type": "OFFERING"
        })
    elif event_id:
        existing_interest = frappe.db.exists("Customer Interest", {
            "customer": frappe.session.user,
            "event": event_id,
            "interest_type": "EVENT"
        })
    else:
        return {"interested": False}
    
    return {
        "interested": bool(existing_interest),
        "interest_id": existing_interest if existing_interest else None
    }


def send_offering_interest_notification(customer, provider, offering):
    """Send email notification to partner about new offering interest"""
    try:
        customer_info = frappe.get_doc("User", customer)
        
        subject = f"New Interest in '{offering.title}'"
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc700;">New Customer Interest! 🎉</h2>
            <p>Great news! A customer has shown interest in your offering.</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-left: 4px solid #ffc700; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Offering Details</h3>
                <p style="margin: 5px 0;"><strong>Title:</strong> {offering.title}</p>
                <p style="margin: 5px 0;"><strong>Price:</strong> ₹{offering.price}</p>
            </div>
            
            <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc700; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Customer Details</h3>
                <p style="margin: 5px 0;"><strong>Name:</strong> {customer_info.full_name}</p>
                <p style="margin: 5px 0;"><strong>Email:</strong> {customer_info.email}</p>
                {f'<p style="margin: 5px 0;"><strong>Phone:</strong> {customer_info.phone}</p>' if customer_info.phone else ''}
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Review the customer's profile</li>
                <li>Contact the customer via email or phone</li>
                <li>Update the interest status in your partner dashboard</li>
            </ol>
            
            <div style="margin: 30px 0;">
                <a href="{frappe.utils.get_url('/partner/interests')}" 
                   style="background-color: #ffc700; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    View All Interests
                </a>
            </div>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>The LEAPP Team</strong>
            </p>
        </div>
        """
        
        frappe.sendmail(
            recipients=provider,
            subject=subject,
            message=message,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Interest Notification Email Error")


def send_event_interest_notification(customer, organizer, event):
    """Send email notification to organizer about new event interest"""
    try:
        customer_info = frappe.get_doc("User", customer)
        
        subject = f"New Interest in '{event.event_name}'"
        
        event_date = event.start_datetime.strftime('%B %d, %Y at %I:%M %p') if event.start_datetime else 'TBD'
        
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ffc700;">New Event Interest! 🎉</h2>
            <p>Great news! A customer has shown interest in your event.</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-left: 4px solid #ffc700; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Event Details</h3>
                <p style="margin: 5px 0;"><strong>Event:</strong> {event.event_name}</p>
                <p style="margin: 5px 0;"><strong>Date:</strong> {event_date}</p>
                {f'<p style="margin: 5px 0;"><strong>Venue:</strong> {event.venue_address}</p>' if event.venue_address else ''}
            </div>
            
            <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc700; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Customer Details</h3>
                <p style="margin: 5px 0;"><strong>Name:</strong> {customer_info.full_name}</p>
                <p style="margin: 5px 0;"><strong>Email:</strong> {customer_info.email}</p>
                {f'<p style="margin: 5px 0;"><strong>Phone:</strong> {customer_info.phone}</p>' if customer_info.phone else ''}
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Review the customer's profile</li>
                <li>Contact the customer via email or phone</li>
                <li>Send event details and registration information</li>
            </ol>
            
            <div style="margin: 30px 0;">
                <a href="{frappe.utils.get_url('/partner/interests')}" 
                   style="background-color: #ffc700; color: #000; padding: 12px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    View All Interests
                </a>
            </div>
            
            <p style="margin-top: 30px;">
                Best regards,<br>
                <strong>The LEAPP Team</strong>
            </p>
        </div>
        """
        
        frappe.sendmail(
            recipients=organizer,
            subject=subject,
            message=message,
            delayed=False
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Event Interest Notification Email Error")

@frappe.whitelist(allow_guest=False)
def update_interest_status(interest_id, new_status):
    """Update the status of a customer interest"""
    # Validate status
    valid_statuses = ["NEW", "CONTACTED", "CONFIRMED", "CLOSED"]
    if new_status not in valid_statuses:
        frappe.throw(_("Invalid status. Must be one of: ") + ", ".join(valid_statuses))
    
    # Check if interest exists
    if not frappe.db.exists("Customer Interest", interest_id):
        frappe.throw(_("Interest not found"), frappe.DoesNotExistError)
    
    # Get the interest document
    interest = frappe.get_doc("Customer Interest", interest_id)
    
    # Check if current user is the provider
    if interest.provider != frappe.session.user:
        frappe.throw(_("You do not have permission to update this interest"), frappe.PermissionError)
    
    # Store old status for history
    old_status = interest.status
    
    # Update the status
    interest.status = new_status
    interest.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {
        "success": True,
        "message": _("Status updated successfully"),
        "old_status": old_status,
        "new_status": new_status
    }


@frappe.whitelist(allow_guest=False)
def get_interest_history(interest_id):
    """Get the version history of a customer interest"""
    # Check if interest exists
    if not frappe.db.exists("Customer Interest", interest_id):
        frappe.throw(_("Interest not found"), frappe.DoesNotExistError)
    
    # Get the interest document
    interest = frappe.get_doc("Customer Interest", interest_id)
    
    # Check if current user is the provider
    if interest.provider != frappe.session.user:
        frappe.throw(_("You do not have permission to view this interest"), frappe.PermissionError)
    
    # Get version history
    versions = frappe.get_all(
        "Version",
        filters={
            "docname": interest_id,
            "ref_doctype": "Customer Interest"
        },
        fields=["name", "creation", "owner", "data"],
        order_by="creation desc",
        limit=20
    )
    
    history = []
    for v in versions:
        try:
            import json
            data = json.loads(v.data) if v.data else {}
            changed = data.get("changed", [])
            
            # Find status changes
            for change in changed:
                if len(change) >= 3 and change[0] == "status":
                    history.append({
                        "timestamp": v.creation,
                        "timestamp_ago": frappe.utils.pretty_date(v.creation),
                        "old_value": change[1],
                        "new_value": change[2],
                        "user": v.owner
                    })
        except:
            pass
    
    return history
