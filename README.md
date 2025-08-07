# BookMyShow Movie Alert System 🎬

A modern, robust Python application to monitor movie booking availability on BookMyShow and alert you when tickets become available.

## Features ✨

- **Multi-Movie Monitoring**: Track multiple movies simultaneously
- **Multiple Alert Methods**: Desktop notifications, email, SMS, and sound alerts
- **Configurable Check Intervals**: Set different check frequencies for each movie
- **Robust Error Handling**: Handles network issues and site changes gracefully
- **Secure Configuration**: Keeps sensitive credentials in config files
- **CLI Interface**: Easy-to-use command line interface
- **Logging**: Comprehensive logging for monitoring and debugging

## Setup 🚀

### Quick Setup
```bash
# Run the setup script
./setup.sh

# Activate the virtual environment
source movie_alert_env/bin/activate

# Run the application
python movie_alert.py
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv movie_alert_env
source movie_alert_env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python movie_alert.py
```

## Configuration ⚙️

### Environment Variables Setup
1. Copy the example environment file: `cp .env.example .env`
2. Edit `.env` with your actual credentials
3. The application will automatically load environment variables

### Configuration Files
- `config.json`: Movie and alert settings
- `.env`: Sensitive credentials (not committed to git)

Configuration overview:
1. **Add Movies**: Configure movies to monitor in `config.json`
2. **Set Alert Preferences**: Enable/disable different types of alerts
3. **Configure Credentials**: Set up credentials in `.env` file

### Example Configuration

```json
{
  "movies": [
    {
      "name": "Avengers: Endgame",
      "url": "https://in.bookmyshow.com/movies/avengers-endgame/ET00000000",
      "city": "mumbai",
      "check_interval": 300,
      "enabled": true
    }
  ],
  "alerts": {
    "email_enabled": true,
    "sms_enabled": true,
    "desktop_enabled": true,
    "sound_enabled": true
  },
  "notifications": {
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "to_email": "recipient@gmail.com"
    },
    "twilio": {
      "account_sid": "your-twilio-account-sid",
      "auth_token": "your-twilio-auth-token",
      "from_number": "+1234567890",
      "to_number": "+9876543210"
    }
  }
}
```

## Usage 📱

### Interactive Mode
```bash
python movie_alert.py
```

### Command Line Options
```bash
# Add a new movie
python movie_alert.py --add-movie "Movie Name" "URL" "city" 300

# List configured movies
python movie_alert.py --list

# Check all movies once
python movie_alert.py --check-once

# Start continuous monitoring
python movie_alert.py --monitor
```

## Setting Up Notifications 📧

### Email Alerts (Gmail)
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password: [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Add your credentials to `config.json`

### SMS Alerts (Twilio)
1. Sign up for a Twilio account: [Twilio.com](https://twilio.com)
2. Get your Account SID and Auth Token from the Twilio Console
3. Purchase a phone number for sending SMS
4. Add your credentials to `config.json`

## How to Find Movie URLs 🔍

1. Go to [BookMyShow](https://in.bookmyshow.com)
2. Search for your movie
3. Click on the movie
4. Copy the URL from your browser
5. Add it to your configuration

Example URL format:
```
https://in.bookmyshow.com/movies/movie-name/ET00123456
```

## Features in Detail 🔍

### Smart Detection
- Monitors multiple indicators for booking availability
- Handles dynamic content loading
- Robust against minor site changes

### Alert System
- **Desktop Notifications**: Cross-platform desktop alerts
- **Email Alerts**: HTML-formatted email notifications
- **SMS Alerts**: Text message alerts via Twilio
- **Sound Alerts**: System sound notifications (macOS)

### Monitoring
- Configurable check intervals per movie
- Automatic retry on network errors
- Comprehensive logging
- Rate limiting to avoid being blocked

### Security
- Credentials stored in separate config file
- No hardcoded sensitive information
- Environment variable support

## Troubleshooting 🔧

### Common Issues

1. **Import Errors**: Make sure you've activated the virtual environment
2. **Network Errors**: Check your internet connection and the movie URL
3. **No Alerts**: Verify your notification configuration in `config.json`
4. **Permission Denied**: Make sure the setup script is executable (`chmod +x setup.sh`)

### Logs
Check `movie_alerts.log` for detailed error messages and monitoring history.

## Cloud Deployment 🌐

### Environment Variables for Production
Set these environment variables in your cloud platform:

```bash
# Required for SMS alerts
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token  
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+0987654321

# Optional for email alerts
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=recipient@example.com

# Production settings
LOG_LEVEL=WARNING  # Reduces log verbosity
```

### Deployment Platforms

#### Heroku
```bash
# Set environment variables
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set LOG_LEVEL=WARNING

# Deploy
git add .
git commit -m "Deploy BookMyShow Alert"
git push heroku main
```

#### Railway/Render
1. Connect your GitHub repository
2. Set environment variables in the dashboard
3. Deploy automatically

#### DigitalOcean/AWS
Use systemd service or Docker for continuous monitoring.

## Legal Considerations ⚖️

- Use responsibly and respect BookMyShow's Terms of Service
- Don't set overly aggressive check intervals (minimum recommended: 5 minutes)  
- This tool is for personal use only

## Contributing 🤝

Feel free to submit issues, feature requests, or pull requests to improve the application.

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy Movie Watching! 🍿**
