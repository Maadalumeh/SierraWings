from app import app, init_database

# Initialize database structure
with app.app_context():
    init_database()

# Import routes after app initialization
import routes
import routes_account_deletion
import routes_announcement
import routes_profile
import routes_maintenance
import routes_weather

# Initialize drone wireless management
try:
    from drone_wireless import initialize_drone_wireless
    drone_wireless = initialize_drone_wireless(app)
except ImportError:
    print("Drone wireless system not available - continuing without it")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
