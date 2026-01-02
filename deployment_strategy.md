## Deployment Steps

Based on your updated preferences (Vercel for the frontend and no cloud platforms for the database, implying a local or self-hosted setup for the backend and Elasticsearch), here are the regenerated deployment steps. This assumes you'll host the backend and database on a VPS (e.g., DigitalOcean, Linode, or AWS EC2 instance) using Docker, as the app is containerized. The frontend will be deployed to Vercel, which can proxy API requests to your VPS backend.

Prerequisites
  * Ensure your code is pushed to GitHub (the repo is ahead by 1 commit—run git push to sync).
  * Set up a VPS with Docker installed (e.g., Ubuntu on DigitalOcean; costs ~$5-10/month for a small instance).
  * Have a domain or static IP for the VPS (for API access).
  * Prepare environment variables (e.g., Elasticsearch credentials) for production.

**Step 1: Prepare and Push Code to GitHub**
  * Commit any local changes: git add . && git commit -m "Prepare for deployment".
  * Push to GitHub: git push origin main.  

**Step 2: Deploy the Backend and Database to Your VPS**
Use Docker Compose on your VPS to run the backend (FastAPI) and Elasticsearch.

  1. Set Up the VPS 

  - SSH into your VPS.
  - Install Docker and Docker Compose if not already installed:  

      
    `sudo apt update && sudo apt install docker.io docker-compose`  
    `sudo systemctl start docker && sudo systemctl enable docker`
      

  * Clone your repo: `git clone https://github.com/swade1/kiro-animal-humane.git && cd kiro-animal-humane/deployment/docker`.
  2. Configure and Run Docker:
  
  * Edit docker-compose.yml if needed (e.g., adjust ports or volumes for persistence).
  * Set environment variables (create a .env file or export them):
    ```
    export ELASTICSEARCH_HOST=localhost
    export ELASTICSEARCH_PORT=9200
    # Add other vars like API keys
    ```
  * Run the containers: docker-compose up -d.
  * Verify: Check docker ps (should show backend on port 8000, Elasticsearch on 9200). Test locally: curl http://localhost:8000/api/overview.
  3. Expose and Secure:
  
  * Configure your VPS firewall to allow ports 8000 (backend) and optionally 9200 (if needed externally).
  * Set up a reverse proxy (e.g., Nginx on the VPS) to serve the backend on port 80/443 with SSL (using Let's Encrypt).
  * Note the backend URL (e.g., https://your-vps-domain.com).
  4. Data Migration (If Needed):
  
  * Run your migration scripts (e.g., docker exec -it <container> python migrate.py) to populate Elasticsearch.

**Step 3: Deploy the Frontend to Vercel**
Vercel supports React and can proxy API calls to your VPS backend.

   1. Connect Vercel to GitHub:
   
  * Log in to Vercel, create a new project, and import your kiro-animal-humane repo.
  * Set the root directory to animal-humane/react-app.
   
   2. Configure Build Settings:
   
  * Build Command: npm run build
  * Output Directory: build
  * Node Version: 18.x or latest.
   
   3. Set Up API Proxying:  
  * In Vercel's project settings, add environment variables or a vercel.json file in animal-humane/react-app/:
     ```
     {
      "rewrites": [
        { "source": "/api/:path*", "destination": "https://your-vps-domain.com/api/:path*" }
      ]
     }
     ```
    This proxies frontend API calls to your VPS backend.
   
   4. Deploy:
   
  * Push to GitHub or trigger a deploy in Vercel. It will build and host the site.
  * Note the deployed frontend URL (e.g., https://your-app.vercel.app).
   
   5. Verify:  
  * Visit the Vercel URL and test the tabs/modals to ensure API calls work and the app loads correctly.

**Step 4: Final Configuration and Testing**

  * Domain Setup: Point your domain to Vercel and VPS if using custom domains.
  * SSL: Enable HTTPS on both Vercel (automatic) and your VPS (via Nginx/Certbot).
  * Monitoring: Use VPS logs (docker logs <container>) and Vercel's dashboard for issues.
  * Full Test: Access the deployed frontend, interact with all features, and confirm data fetching.
  * Backup: Regularly back up Elasticsearch data from your VPS.

Potential Issues and Tips
  * Costs: VPS ~$5-10/month; Vercel has a generous free tier.
  * Performance: Since the database is small, a basic VPS should suffice, but monitor resource usage.
  * Security: Use strong passwords, keep Docker updated, and restrict Elasticsearch access.
  * Local Fallback: If you meant to keep everything local (not production-ready), run Docker on your machine and access via local IP, but this won't work for public users.
  * Once deployed, share the URLs if you need troubleshooting. Let me know if you need commands for a specific VPS provider.
