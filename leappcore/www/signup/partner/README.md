# Partner Signup Page

## Overview
This is a specialized signup page for LEAPP Partners - organizations and educators who want to create and manage offerings on the LEAPP platform.

## Files Created
- `/signup/partner/index.py` - Backend handler for partner signup
- `/signup/partner/index.html` - Frontend template for partner signup form

## Features

### Enhanced Form Fields
Unlike the regular user signup, the partner signup includes:
- **Personal Information**
  - Full Name (required)
  - Email Address (required)
  - Phone Number (optional)

- **Organization Information**
  - Organization Name (required)
  - City (optional)
  - Address (optional)

- **Security**
  - Password (required, min 8 characters)
  - Confirm Password (required)

### User Role
Partners are automatically assigned the **"Leapp Partner"** role upon signup, which grants them special permissions to:
- Create and manage offerings
- Access partner-specific features
- View partner dashboard

### Email Verification
New partners receive a welcome email with:
- Verification link
- Partner program information
- Next steps guidance

### Design Features
- ✅ Matches the LEAPP theme perfectly
- ✅ Organized into logical sections with icons
- ✅ Responsive design (mobile-friendly)
- ✅ Dark mode support
- ✅ Form validation (client & server-side)
- ✅ Password visibility toggle
- ✅ Google OAuth support (if configured)

## Access
The partner signup page is accessible at:
```
http://localhost:8000/signup/partner
```

## Usage Flow
1. User fills out the partner signup form
2. Form is validated (both client and server-side)
3. User account is created with "Leapp Partner" role
4. Welcome email is sent with verification link
5. User is redirected to success page
6. User verifies email and can start using partner features

## Customization Notes

### Adding Custom Fields
If you have a separate `Partner` doctype, uncomment lines 130-137 in `index.py`:
```python
partner_profile = frappe.get_doc({
    "doctype": "Partner",
    "user": user.name,
    "organization_name": organization_name,
    "phone": phone,
    "address": address,
    "city": city,
})
partner_profile.insert(ignore_permissions=True)
```

### Email Template
The welcome email template can be customized in the `send_partner_welcome_email()` function in `index.py`.

## Security
- Password minimum length: 8 characters
- CSRF protection enabled
- Email verification required
- Passwords are hashed before storage
- Form validation on both client and server

## Related Pages
- Regular signup: `/signup`
- Login: `/login`
- Success page: `/signup-success`
