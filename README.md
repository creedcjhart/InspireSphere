# ReviewSphere Blog Platform

A modern blog platform with admin features and Google AdSense integration.

## Features

- User authentication with role-based access control
- Rich text editor for blog posts
- Image upload support
- Draft/Published post status
- Google AdSense integration
- Responsive design
- Admin dashboard

## Setup Instructions

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your_secret_key
   MAIL_USERNAME=your_email
   MAIL_PASSWORD=your_email_password
   ```

3. Initialize the database:
   ```bash
   python app.py
   ```

4. Create owner account using setup_owner.py

## Google AdSense Integration

1. Replace `YOUR_PUBLISHER_ID` in templates/includes/ads.html with your AdSense publisher ID
2. Replace `YOUR_AD_SLOT_ID` with your ad slot IDs
3. Wait for Google AdSense approval

## Deployment Steps

1. Choose a hosting provider (e.g., Heroku, DigitalOcean)
2. Set up environment variables on the hosting platform
3. Configure domain name and SSL certificate
4. Deploy the application

## Backup

Run backup_site.py to create a backup of your website:
```bash
python backup_site.py
```

## Security Notes

- Keep your .env file secure and never commit it to version control
- Regularly update dependencies
- Monitor Google AdSense compliance
