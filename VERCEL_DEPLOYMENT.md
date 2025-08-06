# Vercel Deployment Instructions for CTF AI System

## Quick Deploy to Vercel

### Method 1: Direct Import (Recommended)
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import from Git repository
4. Select this repository
5. Vercel will automatically detect the configuration
6. Click "Deploy"

### Method 2: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project directory
vercel --prod
```

## Configuration Files Created

### `vercel.json`
- Main Vercel configuration
- Routes static files and API endpoints
- Sets Python runtime to 3.9
- Configures maximum Lambda size

### `api/index.py`
- Entry point for Vercel Python functions
- Imports the Flask app from `app_minimal.py`
- Handles WSGI compatibility

### `runtime.txt`
- Specifies Python version (3.9.18)
- Required for Vercel Python builds

### `.vercelignore`
- Excludes unnecessary files from deployment
- Reduces bundle size
- Excludes test files and cache directories

## Environment Variables (Optional)

Set these in Vercel dashboard if you want server features:

```bash
# Optional - for writeup storage
DATABASE_URL=postgresql://user:pass@host:port/db

# Optional - for shared database
SHARED_DATABASE_URL=postgresql://user:pass@host:port/db

# Optional - Flask secret (auto-generated if not set)
SECRET_KEY=your-secret-key-here
```

## Key Features for Vercel

✅ **Client-Side AI Processing** - No server compute needed for AI  
✅ **Zero Dependencies** - Works without any environment variables  
✅ **Static Asset Optimization** - CSS, JS, and HTML files served efficiently  
✅ **Automatic HTTPS** - Vercel provides SSL certificates  
✅ **Global CDN** - Fast loading worldwide  
✅ **Serverless Functions** - API endpoints scale automatically  

## Post-Deployment Testing

After deployment, test these features:

1. **Chat Interface**: Ask "How do I test for SQL injection?"
2. **Model Status**: Check that it shows "Client-Side AI"
3. **File Upload**: Upload a TXT file with CTF writeup content
4. **Data Collection**: Verify it works (server feature)
5. **Training**: Test manual training (server feature)

## Troubleshooting

### Build Errors
- Check that `app_minimal.py` is in the root directory
- Verify Python dependencies in current environment
- Ensure all static files are in `static/` folder

### Runtime Errors
- Check Vercel Function logs for Python errors
- Verify Flask app configuration
- Test locally first with `python app_minimal.py`

### Client AI Not Working
- Check browser console for JavaScript errors
- Verify `static/client_ai.js` is loading
- Test internet connection for model downloads

## Domain Configuration

After deployment, you can:
- Use the provided `.vercel.app` domain
- Add a custom domain in Vercel settings
- Configure DNS records for your domain

## Production Ready Features

✅ Client-side AI models run in user's browser  
✅ No server resources used for AI processing  
✅ Works offline after model download  
✅ Automatic model caching  
✅ Expert CTF knowledge across all categories  
✅ File upload and training capabilities  
✅ Responsive design for mobile devices  
✅ Secure HTTPS encryption  

## Success Verification

Your deployment is successful when:
1. Website loads at your Vercel URL
2. Chat responds with CTF expertise
3. Status shows "Client-Side AI" is working
4. File uploads function correctly
5. All 4 tabs (Chat, Upload, Data, Training) work

## Cost Information

- **Vercel Free Tier**: Perfect for this application
- **Client-Side AI**: Zero server compute costs
- **Bandwidth**: Minimal usage due to client-side processing
- **Function Invocations**: Only for file uploads and data collection

Deploy now and start helping with CTF challenges using real AI models running in users' browsers!