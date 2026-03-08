const express = require('express');
const axios = require('axios');
const winston = require('winston');

const app = express();
app.use(express.json());

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

app.post('/notify/slack', async (req, res) => {
  const { message, webhook_url } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }

  try {
    if (webhook_url) {
      await axios.post(webhook_url, { text: message });
      logger.info('Slack notification sent', { message });
    } else {
      logger.info('Slack notification (simulated)', { message });
    }
    res.json({ status: 'sent', message });
  } catch (err) {
    logger.error('Notification failed', { error: err.message });
    res.status(500).json({ error: 'Failed to send notification' });
  }
});

app.post('/notify/email', async (req, res) => {
  const { to, subject, body } = req.body;
  logger.info('Email notification (simulated)', { to, subject });
  res.json({ status: 'sent', to, subject });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'notify-service' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => logger.info(`Notify service running on port ${PORT}`));
