# SierraWings Drone Control Platform

## Overview

SierraWings is a comprehensive web-based drone control platform designed for medical delivery services in Sierra Leone. The application provides real-time drone tracking, mission management, and role-based access control for patients, medical facilities, and system administrators. Built with Flask and featuring live telemetry data, interactive mapping, and secure authentication, it serves as a complete solution for emergency medical drone deliveries.

## System Architecture

### Backend Architecture
- **Framework**: Flask with Blueprint-based modular architecture
- **Database**: SQLite (development) with SQLAlchemy ORM
- **Authentication**: Flask-Login with role-based access control
- **Session Management**: Flask sessions with secure cookie handling
- **Password Security**: Werkzeug password hashing
- **Email Service**: SendGrid integration for notifications
- **Real-time Communication**: WebSocket-ready for live telemetry

### Frontend Architecture
- **UI Framework**: Bootstrap 5 for responsive design
- **Mapping**: Leaflet.js for interactive drone tracking
- **JavaScript**: Vanilla JS for dynamic interactions
- **Icons**: Font Awesome for consistent iconography
- **Styling**: Dark theme with yellow accent color (#FFC107), sports app inspired design
- **Typography**: Inter font family for modern aesthetics
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Theme**: Dark cards with subtle shadows and rounded corners
- **Analytics**: Chart.js for data visualization and performance tracking

## Key Components

### Authentication System
- **Role-based Registration**: Three distinct user roles (Patient, Hospital/Clinic, Admin)
- **Invite Code System**: Secure registration for Healthcare Provider and Admin roles (codes kept confidential)
- **Password Management**: Secure hashing, password reset functionality
- **Two-Factor Authentication**: TOTP-based 2FA with backup codes
- **Session Security**: Secure session management with Flask-Login

### User Management
- **Patient Role**: Open registration, medical delivery requests, real-time tracking
- **Hospital/Clinic Role**: Invitation-based, clinic profile management, patient records
- **Admin Role**: Full system access, user management, drone fleet oversight

### Drone Operations
- **Real-time Telemetry**: Live GPS tracking, battery monitoring, flight status
- **Mission Management**: Complete workflow from request to delivery
- **Fleet Management**: Drone status monitoring, maintenance tracking
- **Live Control**: Direct communication with Pixhawk flight controllers

### Data Models
- **User**: Authentication, profile, role management
- **Drone**: Fleet management, status tracking, specifications
- **Mission**: Delivery requests, status workflow, telemetry logs
- **ClinicProfile**: Medical facility information, licensing, specialties
- **HospitalPatient**: Patient records with GDPR compliance
- **TelemetryLog**: Real-time flight data storage
- **PaymentTransaction**: Financial transaction tracking

## Data Flow

### Mission Lifecycle
1. **Request Creation**: Patients request medical deliveries through web interface
2. **Clinic Review**: Medical facilities accept/reject requests based on availability
3. **Drone Dispatch**: Approved missions assigned to available drones
4. **Live Tracking**: Real-time telemetry updates throughout flight
5. **Delivery Completion**: Mission status updates and payment processing

### Real-time Updates
- **Telemetry Streaming**: Continuous GPS, battery, and flight data
- **Status Notifications**: Live mission status updates across all user roles
- **Map Visualization**: Dynamic flight path rendering with Leaflet.js
- **Dashboard Metrics**: Real-time statistics and operational insights

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and application structure
- **SQLAlchemy**: Database ORM and query management
- **Flask-Login**: User session and authentication management
- **Werkzeug**: Password hashing and security utilities
- **SendGrid**: Email service for notifications and 2FA
- **PyMAVLink**: Drone communication protocol (planned)

### Frontend Dependencies
- **Bootstrap 5**: Responsive UI framework
- **Leaflet.js**: Interactive mapping and geospatial visualization
- **Font Awesome**: Icon library
- **jQuery**: DOM manipulation and AJAX requests

### Hardware Integration
- **Pixhawk Flight Controllers**: Primary drone control system
- **Raspberry Pi**: Onboard computing and wireless communication
- **GPS Modules**: Location tracking and navigation
- **Telemetry Radios**: Long-range communication (optional)

## Deployment Strategy

### Development Environment
- **Database**: SQLite for local development
- **Configuration**: Environment variables for sensitive data
- **Debug Mode**: Flask development server with hot reload
- **Static Assets**: Local file serving for CSS, JS, and images

### Production Considerations
- **Database Migration**: PostgreSQL for production scalability
- **HTTPS**: SSL/TLS encryption for secure communications
- **Load Balancing**: Support for multiple application instances
- **Monitoring**: Application performance and error tracking
- **Backup Strategy**: Regular database backups and recovery procedures

### Hardware Deployment
- **Raspberry Pi Integration**: On-drone computing with wireless connectivity
- **Network Discovery**: Automatic drone detection and registration
- **Failover Systems**: Redundant communication channels
- **Maintenance Protocols**: Remote diagnostics and updates

## Changelog

```
Changelog:
- July 04, 2025. Initial setup
- July 13, 2025. Production deployment ready - cleaned database, updated invite codes, added admin creation script
- July 13, 2025. Complete UI overhaul - implemented modern mobile-first design with yellow accent theme, updated logo, new CSS framework
- July 13, 2025. Dark theme implementation - created sports app inspired dark theme with analytics charts, Chart.js integration, enhanced patient dashboard
- July 14, 2025. Text naturalization - removed all hyphens from words across entire application to appear more natural (e.g., "life saving" instead of "life-saving", "real time" instead of "real-time", "24 7" instead of "24/7")
- July 14, 2025. Security update - updated invite codes to new secure values and removed public documentation of codes for enhanced security
- July 14, 2025. Data privacy rights implementation - added comprehensive GDPR-compliant data privacy management with user access, correction, deletion, data portability, and complaint filing features for both patient and hospital users
- July 14, 2025. Age verification system - implemented age restriction preventing users under 13 from creating accounts, with date of birth validation during registration
- July 14, 2025. Admin violation tracking - created admin dashboard for tracking policy violations, account deactivation/reactivation, and violation history management
- July 14, 2025. Dashboard enhancements - fixed profile button 500 error by passing user object to template, improved delivery history structure with better card layout and hover effects, added interactive 2D map with Leaflet.js showing drone locations and user position on patient dashboard
- July 14, 2025. Live geolocation implementation - added real GPS location access for delivery requests with proper permission handling, location accuracy feedback, error handling for different permission states, and automatic address lookup using reverse geocoding. Users can now click "Use Current Location" to get their real GPS coordinates for delivery addresses
- July 14, 2025. Theme system implementation - added comprehensive dark/light theme toggle with accessibility features, updated logo and favicon with user-provided images, implemented custom CSS theme system with proper color variables, added keyboard navigation support (Alt+T for theme toggle), and enhanced visual design with new background colors and improved user experience for people with vision problems
- July 14, 2025. Dark theme removal - removed all dark theme functionality per user request, disabled theme toggle button, removed all dark theme CSS variables and styles, updated JavaScript to only use light theme, maintaining clean light theme interface throughout all panels
- July 14, 2025. Eye-friendly color scheme implementation - updated color palette to reduce eye strain with softer backgrounds (#fafbfc), warmer text colors (#2c3e50, #546e7a), improved contrast ratios, gentle blue accent (#3498db), enhanced line spacing (1.6-1.7), larger font sizes (16px base), rounded corners (8px), and accessibility features including focus states and reduced motion support
- July 14, 2025. Hospital management system completion - fully implemented hospital dashboard with patient registration, medical records management, hospital search functionality for patients, strict data isolation between hospitals, GDPR compliant data processing with access logging, and paperwork reduction through digital patient management system
- July 15, 2025. Medical theme implementation - removed complex theme system and implemented clean medical theme with medical blue color palette, medical icons throughout interface (heartbeat, ambulance, user-md, shield-virus), medical-focused navigation and footer, emergency response styling, and professional medical service branding
- July 15, 2025. Blue medical theme refinement - updated header from light teal to professional deep medical blue (#1E4A72), improved text contrast with high-contrast dark text colors, enhanced button styling with better shadows and hover effects, updated PWA manifest and meta tags to match new blue theme, improved navbar with white text on blue background for better readability
- July 15, 2025. Text naturalization and contrast enhancement - removed hyphens from all text (e.g., "life-saving" to "life saving", "role-based" to "role based"), changed all text colors to pure black (#000000) for maximum contrast, added highlighted description boxes with white background and medical blue borders, increased description text size to 1.1rem with font-weight 600, added text shadows for better readability, enhanced PWA functionality for online app installation
- July 15, 2025. Sky blue theme implementation - updated color palette from deep medical blue to friendly sky blue (#3498DB), changed text colors to comfortable blue-gray (#2C3E50) instead of harsh black, softened description highlight boxes with lighter background and reduced border thickness, reduced font weight from 600 to 500 for better readability, updated PWA manifest colors to match sky blue theme
- July 15, 2025. Description styling improvements - further softened main description background with subtle gradients and reduced opacity borders, added individual description boxes for each step in "HOW IT WORKS" section with matching styling, implemented consistent visual hierarchy with sky blue accents and comfortable spacing
- July 15, 2025. Sky blue color refinement - darkened primary sky blue color from #3498DB to #2980B9 for more professional appearance, updated secondary colors to create better hierarchy, adjusted PWA manifest colors and shadow effects to match darker sky blue theme
- July 15, 2025. Header color update and Flask-Mail integration - updated header to professional charcoal blue (#1A252F) for better visual satisfaction, integrated Flask-Mail for OTP email verification and notifications replacing SendGrid dependency, fixed login button functionality with proper error handling and user feedback, enhanced email templates with medical theme styling
- July 15, 2025. Dark floating description theme - transformed description boxes to dark floating theme with charcoal blue gradient backgrounds (#2C3E50 to #34495E), enhanced shadows for floating appearance, added hover effects with increased elevation, changed text color to light gray (#ECF0F1) for better contrast, applied consistent styling to both main descriptions and step descriptions
- July 15, 2025. Description background thickness adjustment - reduced padding and shadow intensity to make description backgrounds thinner and less bulky, decreased vertical padding from large to small spacing, reduced shadow blur and opacity for subtler floating effect, adjusted transform values for gentler hover animations
- July 15, 2025. Username authentication system - updated login system to use username instead of email for authentication, added helpful placeholders and guidance text to username fields, improved user experience to match modern app conventions where users create and login with usernames
- July 15, 2025. Complete notification system implementation - created comprehensive notification service for OTP verification and delivery updates, integrated email notifications for all mission status changes (requested, accepted, assigned, in transit, delivered, failed), implemented complete delivery workflow with proper notification triggers for patients and clinics, fixed OTP verification system to work properly for all user roles
- July 15, 2025. Authentication system overhaul - removed invite code requirements from registration for admin/hospital roles, moved invite codes to login process for enhanced security, disabled OTP verification for admin/hospital users (only patients need email verification), updated login form with dynamic access code field, improved app store download section alignment with better responsive design, added custom Sierra mobile app SVG illustration with phone mockup showing app interface, cleared all existing user accounts for fresh start
- July 16, 2025. Real OTP verification system implementation - set up working OTP email delivery with user's Gmail credentials (Ramandhan01@gmail.com), implemented 6-digit code generation and email sending, created professional OTP verification page with auto-submit functionality, added role-specific automated welcome emails after verification, fixed all duplicate code issues in authentication system
- July 16, 2025. Maintenance alert system creation - built comprehensive maintenance alert service for sending email notifications to all users during app maintenance, created admin interface for sending custom and quick template alerts, implemented emergency, scheduled, and completion alert types, added beautiful email templates with role-specific messaging, integrated maintenance alert management in admin dashboard with professional UI design
- July 16, 2025. Gamification system implementation - enhanced SierraWings with playful drone status emoji indicators, interactive maintenance timeline visualization with clickable items, user engagement badge system with progress tracking, floating action buttons for quick access, mission criticality color schemes, and progress ring analytics. All features maintain professional medical platform integrity while improving user engagement
- July 16, 2025. PWA logo and icon optimization - created properly sized PWA icons (72x72 to 512x512) from the SierraWings logo, updated manifest.json with correct icon paths, implemented service worker for offline functionality and push notifications, fixed admin dashboard API errors, and optimized app installation experience with professional branding
- July 16, 2025. Enhanced user experience features - implemented contextual help tooltips with guided tours for first-time users, animated mission progress visualization with real-time drone tracking, one-click emoji feedback system with automatic email delivery to sierrawingsofficial@gmail.com, and personalized dashboard widgets with role-specific content and customizable layouts. All features excluded from registration and login pages for clean authentication experience
- July 16, 2025. Email notification system upgrade - automated all feedback submissions to send directly to sierrawingsofficial@gmail.com with user details and ratings, maintenance alerts now include delivery reports to official email, improved email templates with professional formatting and comprehensive user information
- July 16, 2025. Professional button system implementation - created comprehensive professional button design system with gradient backgrounds, hover animations, and medical theme colors. Updated all dashboard templates to use professional buttons, fixed JavaScript gamification errors, added professional quick action panels for each user role, implemented contextual help tooltips with professional styling, and built personalized dashboard widgets. All features maintain consistent app-like styling with high contrast support and responsive design
- July 16, 2025. Weather widget and circular button improvements - implemented real-time weather conditions widget for drone flight operations with rainfall detection, wind speed monitoring, and flight status indicators. Enhanced circular floating action buttons with improved design, larger size, better shadows, emergency button pulsing animation, and professional styling. Fixed JavaScript scope issues and duplicate class definitions for better performance
- July 16, 2025. Complete system overhaul - implemented comprehensive feature set including: movable floating feedback button routing to SierraWingsOfficial@gmail.com, edit profile functionality across all user modes, real-time GPS location services with "Use Current Location" button, live drone tracking map with 30-second refresh, account deletion request system with admin approval workflow, broadcast announcement system with manual dismissal, maintenance mode with full-screen banner display, real-time weather API integration with flight safety assessment, minimized widgets with expand functionality, medical items dropdown in delivery requests, social media links integration (TikTok, X, WhatsApp), and responsive mobile-friendly design. All features fully functional with proper error handling and user feedback
- July 16, 2025. Social media links update - separated WhatsApp community link (https://chat.whatsapp.com/DNVfWh3a5BQ2FWhvpJArgc) for group discussions and WhatsApp followers channel link (https://whatsapp.com/channel/0029Vb5diMZCcW4tl18Biv17) for updates in the Follow Us section, updated all references to properly distinguish between community and followers channels
- July 16, 2025. Patient dashboard simplification - removed live drone tracking mode, interactive map functionality, and 4 widgets from patient dashboard per user request. Dashboard now focuses on essential delivery management features including statistics cards, recent delivery requests, quick actions, and emergency contacts. Eliminated all Leaflet.js map components and geolocation tracking to provide cleaner, more focused user experience
- July 16, 2025. Circular button removal - removed specific circular floating action buttons from patient dashboard: "request emergency", "monitor your delivery", "view your delivery", and "share experience" buttons. Kept only the "Request Delivery" circular button for essential functionality. Updated gamification.js to streamline patient quick actions
- July 16, 2025. Dashboard widget buttons simplification - removed "Track Orders", "Emergency", and "Feedback" professional card buttons from patient dashboard widget system. Kept only "Request Delivery" button in dashboard widgets. Updated dashboard-widgets.js getPatientActions() method to provide cleaner patient interface
- July 16, 2025. Emergency button restoration - added back "Emergency" button to patient dashboard per user request. Fixed JavaScript syntax errors in gamification.js file by adding missing helper functions. Emergency button now available in both floating action buttons (🚨) and dashboard widgets (📞) for quick access to emergency services
- July 16, 2025. Feedback system implementation - created comprehensive feedback submission system with direct Gmail integration using SierraWingsOfficial@gmail.com. Built floating feedback button, API endpoints, form page, and professional email delivery. Users can now send feedback directly to official Gmail account with user details and role information
- July 16, 2025. Homepage community section removal - removed "Join Our Community" section from homepage including WhatsApp community button and social media links per user request. Maintained floating WhatsApp community button for easy access while cleaning up homepage content
- July 16, 2025. Homepage mobile optimization - completely reorganized homepage layout to reduce mobile scrolling by removing services section and app download section, compacting hero section, features section, and "How It Works" section, adding mobile-specific CSS optimizations for better spacing and typography, and hiding map on mobile devices to create cleaner mobile experience
- July 16, 2025. Social media integration - added "Follow Us" section to footer with TikTok, Instagram, and X (Twitter) buttons, implemented professional button styling with hover effects and mobile-responsive design, integrated social media links for SierraWingsOfficial accounts
- July 16, 2025. Social media repositioning - moved "Follow Us" section from footer to homepage under "How It Works" section, added WhatsApp channel icon, created circular icon design with brand colors and hover effects, updated X icon to use proper X symbol (𝕏), updated WhatsApp link to channel URL (https://whatsapp.com/channel/0029Vb5diMZCcW4tl18Biv17)
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```