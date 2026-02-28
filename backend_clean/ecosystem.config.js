// Configuration PM2 pour Football Backend
module.exports = {
  apps: [{
    name: 'football-backend',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/path/to/backend_clean',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: '/path/to/backend_clean'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
}
