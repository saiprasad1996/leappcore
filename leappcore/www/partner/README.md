# LEAPP Partner Portal

## Overview
A comprehensive partner portal for LEAPP platform that allows partners to manage their profile, create and manage offerings, and organize events. The portal consists of three main sections accessible through a unified navigation interface.

## Directory Structure
```
/partner/
├── profile/
│   ├── index.py       # Partner profile management
│   └── index.html     # Profile UI
├── verification/
│   ├── index.py       # Partner verification checklist (draft/submit)
│   └── index.html
├── offering/
│   └── register/
│       ├── index.py   # Offering create/edit backend
│       └── index.html # Offering form UI
└── event/
    └── register/
        ├── index.py   # Event create/edit backend
        └── index.html # Event form UI
```

### Partner Verification (`/partner/verification`)
- Checklist fields come from Desk **Partner Verification Template** (Individual / Organisation), chosen from signup `partner_type` on Partner Profile.
- Lifecycle: Draft → Submitted → Under Review → Verified | Rejected (resubmit) ; admin may Revoke.
- Admin review queue: `/admin/verification`. Templates: `/app/partner-verification-template`.
- Verified badge uses `Partner Profile.is_verified` (not a publish gate).
- Partner guidelines (static): `/partner/guidelines` — linked from the verification checklist “agree to guidelines” checkbox.

## Pages Created

### 1. Partner Profile (`/partner/profile`)
**Purpose**: Manage partner profile information

**Features**:
- ✅ View and edit organization details
- ✅ Professional information management
- ✅ User info display card with avatar
- ✅ Partner rating display
- ✅ Area/Location selection
- ✅ Quick link to account settings

**Form Fields**:
- Organization Name
- Area/Location (dropdown from Area doctype)
- Occupation
- Highest Qualification
- Languages
- Availability

**Backend**:
- Creates/updates `Partner Profile` doctype
- Permission checks for Leapp Partner role
- Auto-loads existing profile data
- Validation and error handling

---

### 2. Offering Registration (`/partner/offering/register`)
**Purpose**: Create and manage course offerings

**Features**:
- ✅ Create new offerings
- ✅ Edit existing offerings
- ✅ View all partner's offerings in sidebar
- ✅ Quick status indicators (Active/Inactive)
- ✅ Form validation
- ✅ Auto-save and redirect

**Form Sections**:
1. **Basic Information**
   - Title (required, unique)
   - Subtitle/Tagline
   - Full Description

2. **Pricing & Details**
   - Price (₹)
   - Duration (hours)
   - Skill Level (Beginner/Intermediate/Advanced)
   - Total Sessions

3. **Status**
   - Active checkbox

**Sidebar Features**:
- List of all partner's offerings
- Shows title, subtitle, price
- Active/Inactive badges
- Click to edit functionality
- "New Offering" button

**Backend**:
- Creates/updates `Offering` doctype
- Auto-sets provider to current user
- Permission validation
- Supports both create and edit modes

---

### 3. Event Registration (`/partner/event/register`)
**Purpose**: Create and manage events

**Features**:
- ✅ Create new events
- ✅ Edit existing events
- ✅ View all partner's events in sidebar
- ✅ DateTime pickers for scheduling
- ✅ Status indicators
- ✅ Area selection

**Form Sections**:
1. **Event Information**
   - Event Name (required, unique)
   - Heading
   - Short Description (for preview)
   - Long Description (detailed)

2. **Schedule & Location**
   - Start Date & Time (datetime picker)
   - End Date & Time (datetime picker)
   - Area (dropdown)
   - Venue Address (multi-line)

3. **Status**
   - Active checkbox

**Sidebar Features**:
- List of all partner's events
- Shows event name, heading
- Date indicator with calendar icon
- Active/Inactive badges
- Click to edit functionality
- "New Event" button

**Backend**:
- Creates/updates `Leapp Event` doctype
- Auto-sets organizer to current user
- Permission validation
- Supports both create and edit modes

---

## Common Features Across All Pages

### Navigation
- Consistent navigation tabs at top
- Active tab highlighting
- Easy switching between sections

### Design Elements
- **Color Scheme**: Yellow (#ffc700) primary, gray accents
- **Icons**: Material Symbols for sections
- **Responsive**: Mobile-friendly grid layouts
- **Dark Mode**: Full dark mode support
- **Typography**: Plus Jakarta Sans font

### User Experience
- Auto-hiding success messages (5 seconds)
- Clear error messages
- Form validation (client & server)
- Cancel and Save buttons
- Loading states

### Security
- **Authentication**: Login required
- **Authorization**: Leapp Partner role required
- **CSRF Protection**: All forms protected
- **Permission Checks**: Users can only edit their own content
- **Data Validation**: Server-side validation

---

## Access URLs

| Page | URL | Permission Required |
|------|-----|-------------------|
| Partner Profile | `/partner/profile` | Leapp Partner |
| Offering Registration | `/partner/offering/register` | Leapp Partner |
| Edit Offering | `/partner/offering/register?id=[ID]` | Leapp Partner (owner) |
| Event Registration | `/partner/event/register` | Leapp Partner |
| Edit Event | `/partner/event/register?id=[ID]` | Leapp Partner (owner) |

---

## Data Models

### Partner Profile
- Links to User doctype
- Stores organization and professional info
- One profile per partner

### Offering
- Created by partner (provider field)
- Multiple offerings per partner
- Can be active/inactive
- Featured flag (admin controlled)

### Leapp Event
- Created by partner (organizer field)
- Multiple events per partner
- DateTime scheduling
- Can be active/inactive
- Linked to Area

---

## Future Enhancements

Potential improvements for the partner portal:

1. **File Uploads**
   - Add image upload for offerings
   - Featured image for events
   - Profile picture upload
   - Sample video upload

2. **Advanced Features**
   - Offering categories selection
   - Program outline builder
   - Instructor assignment
   - Pricing tiers
   - Schedule management

3. **Analytics Dashboard**
   - View offering performance
   - Event registration stats
   - Revenue tracking
   - User engagement metrics

4. **Bulk Operations**
   - Duplicate offerings
   - Bulk activate/deactivate
   - Export data

5. **Communication**
   - Messages from users
   - Notification center
   - Email alerts

---

## Technical Notes

### Dependencies
- Frappe Framework
- LEAPP custom doctypes:
  - Partner Profile
  - Offering
  - Leapp Event
  - Area
  - Offering Category

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript required
- Supports datetime-local input type

### Performance
- Lazy loading of sidebar lists
- Client-side form validation
- Optimized database queries
- Proper indexing on doctypes

---

## Testing

To test the partner portal:

1. **Create a Partner Account**
   ```
   Visit: /signup/partner
   Fill in partner signup form
   ```

2. **Access Partner Profile**
   ```
   Visit: /partner/profile
   Fill in organization details
   Save profile
   ```

3. **Create an Offering**
   ```
   Visit: /partner/offering/register
   Fill in offering details
   Mark as active
   Submit
   ```

4. **Create an Event**
   ```
   Visit: /partner/event/register
   Fill in event details
   Set dates and venue
   Mark as active
   Submit
   ```

5. **Edit Content**
   - Click on any item in the sidebar
   - Update fields
   - Save changes

---

## Support

For issues or questions:
- Check Frappe error logs
- Verify user has "Leapp Partner" role
- Ensure doctypes are synced
- Check permissions on doctypes

---

## License
Part of the LEAPP platform - All rights reserved
