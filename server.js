process.env["NODE_TLS_REJECT_UNAUTHORIZED"]=0;
const express = require('express');
const crypto = require('crypto');
// Load API key from environment variable
const API_KEY = process.env.API_KEY;

// Secure API key middleware
function apiKeyAuth(req, res, next) {
    const clientKey = req.headers['x-api-key'];
    if (!API_KEY || !clientKey ||
        !crypto.timingSafeEqual(Buffer.from(clientKey), Buffer.from(API_KEY))) {
        console.warn(`Unauthorized access attempt from ${req.ip}`);
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}
const path = require('path');
const { OpenAIAPI } = require('./openai');
const sqlite3 = require('sqlite3').verbose();

// Initialize SQLite database
const db = new sqlite3.Database('./chatbot_logs.db', (err) => {
    if (err) {
        console.error('Could not connect to database', err);
    } else {
        console.log('Connected to SQLite database');
    }
});

// Create logs table if it doesn't exist
db.run(`CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT,
    bot_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

const app = express();
const port = process.env.PORT || 3000;


app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Apply API key middleware to protected routes
app.use('/getChatbotResponse', apiKeyAuth);
app.use('/logs', apiKeyAuth);

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/getChatbotResponse', async (req, res) => {
    const userMessage = req.body.userMessage;

    // Use OpenAI API to generate a response
    const chatbotResponse = await OpenAIAPI.generateResponse(userMessage);

    // Save interaction to SQLite
    db.run(
        'INSERT INTO logs (user_message, bot_response) VALUES (?, ?)',
        [userMessage, chatbotResponse],
        (err) => {
            if (err) {
                console.error('Failed to save log:', err);
            }
        }
    );

    // Send the response back to the client
    res.json({ chatbotResponse });
})
// Endpoint to get logs
app.get('/logs', (req, res) => {
    db.all('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100', [], (err, rows) => {
        if (err) {
            res.status(500).json({ error: 'Failed to fetch logs' });
        } else {
            res.json(rows);
        }
    });
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});