const express = require('express');
const { Pool } = require('pg');
const promClient = require('prom-client');
const winston = require('winston');

const app = express();
app.use(express.json());

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()]
});

const register = new promClient.Registry();
promClient.collectDefaultMetrics({ register });

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status'],
  registers: [register]
});

const httpRequestTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'route', 'status'],
  registers: [register]
});

const pool = new Pool({
  host: process.env.DB_HOST || 'postgres',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'orders',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres'
});

pool.query(`
  CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    product VARCHAR(255),
    quantity INT,
    created_at TIMESTAMP DEFAULT NOW()
  )
`).catch(err => logger.error('DB init error:', err));

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on('finish', () => {
    end({ method: req.method, route: req.route?.path || req.path, status: res.statusCode });
    httpRequestTotal.inc({ method: req.method, route: req.route?.path || req.path, status: res.statusCode });
  });
  next();
});

app.post('/orders', async (req, res) => {
  try {
    const { customer_name, product, quantity } = req.body;
    const result = await pool.query(
      'INSERT INTO orders (customer_name, product, quantity) VALUES ($1, $2, $3) RETURNING *',
      [customer_name, product, quantity]
    );
    logger.info('Order created', { orderId: result.rows[0].id });
    res.status(201).json(result.rows[0]);
  } catch (err) {
    logger.error('Order creation failed', { error: err.message });
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/orders/:id', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM orders WHERE id = $1', [req.params.id]);
    if (result.rows.length === 0) return res.status(404).json({ error: 'Order not found' });
    res.json(result.rows[0]);
  } catch (err) {
    logger.error('Order fetch failed', { error: err.message });
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'order-service' });
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => logger.info(`Order service running on port ${PORT}`));
