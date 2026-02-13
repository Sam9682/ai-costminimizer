# CostMinimizer Web Interface - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Application
```bash
# Clone repository
git clone https://github.com/aws-samples/sample-costminimizer.git
cd sample-costminimizer

# Start web interface (one command does everything!)
./start-web-interface.sh    # Linux/Mac
# or
.\start-web-interface.ps1   # Windows PowerShell
```

### Step 2: Open Your Browser
Navigate to:
- **HTTP**: http://localhost:6000
- **HTTPS**: https://localhost:6001 (recommended)

### Step 3: Enter AWS Credentials
1. Fill in your AWS credentials:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Session Token (if using temporary credentials)
   - Select your AWS Region

2. Click "Validate Credentials"

3. Once validated, you can:
   - Generate cost optimization reports
   - Chat with AI assistant about your AWS costs
   - Get Docker commands for CLI usage

## 📊 Generate Your First Report

1. **Select Report Types** (all selected by default):
   - ✅ Cost Explorer (CE) - Spending patterns and trends
   - ✅ Trusted Advisor (TA) - Best practice recommendations
   - ✅ Compute Optimizer (CO) - Rightsizing recommendations
   - ☐ Cost & Usage Report (CUR) - Detailed billing analysis

2. **Click "Generate Reports"**
   - Wait 5-10 minutes for comprehensive analysis
   - Reports saved to `/root/cow` directory

3. **Review Results**
   - Excel reports with detailed recommendations
   - PowerPoint presentations for stakeholders

## 💬 Ask the AI Assistant

Once reports are generated, ask questions like:

**Cost Analysis:**
- "What are my top 5 AWS services by cost?"
- "Show me my spending trends over the last 3 months"
- "Which accounts have the highest costs?"

**Optimization:**
- "How can I reduce my EC2 costs?"
- "What Reserved Instance recommendations do you have?"
- "Show me underutilized resources"

**Specific Services:**
- "Analyze my S3 storage costs"
- "What Lambda optimizations are available?"
- "Review my RDS spending"

## 🐳 Use Docker Command (Optional)

The web interface generates Docker commands for CLI usage:

```bash
# Copy the command from the web interface
docker run -it \
  -v $HOME/.aws:/root/.aws \
  -v $HOME/cow:/root/cow \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  costminimizer --ce --ta --co --region us-east-1
```

## 🔧 Common Tasks

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Update Application
```bash
git pull origin main
docker-compose up -d --build
```

## ❓ Troubleshooting

### "Unable to locate credentials"
- Ensure you've validated credentials in the web interface
- Check that credentials have required IAM permissions

### "Port already in use"
- Change ports in `.env` file:
  ```bash
  HTTP_PORT=7000
  HTTPS_PORT=7001
  ```
- Restart: `docker-compose down && docker-compose up -d`

### "SSL certificate error"
- Accept self-signed certificate in browser
- Or use HTTP instead: http://localhost:6000

### "Reports taking too long"
- This is normal! Reports can take 5-15 minutes
- Check logs: `docker-compose logs -f`
- Ensure AWS services are enabled in your account

## 📚 Next Steps

- **Read Full Documentation**: [WEB_INTERFACE.md](WEB_INTERFACE.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **CLI Usage**: See [README.md](README.md) for command-line options
- **MCP Integration**: [MCP_SETUP.md](MCP_SETUP.md) for AI assistant setup

## 🆘 Need Help?

- **GitHub Issues**: https://github.com/aws-samples/sample-costminimizer/issues
- **Documentation**: Check README.md and other .md files
- **AWS Support**: For AWS-specific questions

## 🎯 Pro Tips

1. **Generate reports monthly** to track cost trends
2. **Use the AI chat** to understand complex cost patterns
3. **Export reports** to share with your team
4. **Set up automation** using the Docker commands
5. **Review Trusted Advisor** recommendations first for quick wins

## 🔐 Security Reminder

- Never commit credentials to version control
- Use IAM roles when running on EC2
- Rotate credentials regularly
- Use MFA for sensitive accounts
- Keep SECRET_KEY secure in production

---

**Ready to optimize your AWS costs?** Start the application and begin saving! 💰
