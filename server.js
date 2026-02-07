// =====================================================
// Сервер для обработки заявок с сайта ChiParts
// =====================================================

const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 10000; // Render использует порт из переменной окружения

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public'))); // Раздача статики из папки public

// Настройки Telegram
const BOT_TOKEN = process.env.BOT_TOKEN || '8218450565:AAFDSOHTUWidvp-gIHHIrx_AB2z8iCMfUTg';
const ADMIN_CHAT_IDS = (process.env.ADMIN_CHAT_IDS || '-5264176031').split(',');

// Логирование заявок в файл (на Render файлы временные, но для отладки оставим)
const LOG_FILE = path.join(__dirname, 'orders.log');

function logOrder(order) {
    const timestamp = new Date().toLocaleString('ru-RU');
    const logEntry = `[${timestamp}] ${JSON.stringify(order, null, 2)}\n\n`;
    
    fs.appendFile(LOG_FILE, logEntry, (err) => {
        if (err) console.error('Ошибка записи лога:', err);
    });
}

// Отправка сообщения в Telegram
async function sendTelegramMessage(message) {
    const promises = ADMIN_CHAT_IDS.map(async (chatId) => {
        try {
            await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
                chat_id: chatId.trim(),
                text: message,
                parse_mode: 'HTML'
            });
            console.log(`✅ Заявка отправлена в группу ${chatId}`);
            return true;
        } catch (error) {
            console.error(`❌ Ошибка отправки в ${chatId}:`, error.message);
            return false;
        }
    });
    
    return Promise.all(promises);
}

// API эндпоинт для заявок
app.post('/api/order', async (req, res) => {
    try {
        const { name, phone, carBrand, carModel, partName, comment, source } = req.body;
        
        // Валидация данных
        if (!name || !phone || !partName) {
            return res.status(400).json({
                success: false,
                message: 'Необходимо заполнить все обязательные поля'
            });
        }
        
        // Форматирование данных
        const formattedPhone = phone.replace(/\D/g, '');
        const timestamp = new Date().toLocaleString('ru-RU');
        const sourceLabel = source === 'website' ? '🌐 Сайт' : '📱 Telegram-бот';
        
        // Формирование сообщения для админа
        const adminMessage = `
🆕 <b>НОВАЯ ЗАЯВКА ${sourceLabel}</b> 🆕

⏰ <b>Время:</b> ${timestamp}

👤 <b>Имя:</b> ${name}
📱 <b>Телефон:</b> +${formattedPhone}
🚗 <b>Марка:</b> ${carBrand}
🚘 <b>Модель:</b> ${carModel}
🔧 <b>Деталь:</b> ${partName}
💬 <b>Комментарий:</b> ${comment || 'Без комментария'}

━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 <i>Для связи: +${formattedPhone}</i>
        `;
        
        // Отправка в группу
        const results = await sendTelegramMessage(adminMessage);
        
        // Логирование
        const orderData = {
            timestamp,
            name,
            phone: `+${formattedPhone}`,
            carBrand,
            carModel,
            partName,
            comment: comment || 'Без комментария',
            source,
            sentTo: results.filter(r => r).length
        };
        
        logOrder(orderData);
        
        // Проверка успешной отправки
        if (results.some(r => r)) {
            console.log('✅ Заявка успешно обработана');
            res.json({
                success: true,
                message: 'Заявка успешно отправлена',
                order: orderData
            });
        } else {
            console.error('❌ Не удалось отправить заявку ни в одну группу');
            res.status(500).json({
                success: false,
                message: 'Ошибка при отправке заявки. Попробуйте позже.'
            });
        }
        
    } catch (error) {
        console.error('❌ Критическая ошибка:', error);
        res.status(500).json({
            success: false,
            message: 'Внутренняя ошибка сервера',
            error: error.message
        });
    }
});

// API эндпоинт для получения статистики
app.get('/api/stats', (req, res) => {
    try {
        if (fs.existsSync(LOG_FILE)) {
            const logContent = fs.readFileSync(LOG_FILE, 'utf8');
            const orderCount = (logContent.match(/НОВАЯ ЗАЯВКА/g) || []).length;
            
            res.json({
                success: true,
                totalOrders: orderCount,
                lastUpdate: new Date().toLocaleString('ru-RU')
            });
        } else {
            res.json({
                success: true,
                totalOrders: 0,
                lastUpdate: new Date().toLocaleString('ru-RU')
            });
        }
    } catch (error) {
        res.status(500).json({
            success: false,
            message: 'Ошибка получения статистики'
        });
    }
});

// Главная страница — отдаём статический файл
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Catch-all для остальных путей (для корректной работы одностраничника)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Запуск сервера
app.listen(PORT, '0.0.0.0', () => {
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║                                                            ║');
    console.log('║         🚀 ChiParts - Сервер запущен успешно!            ║');
    console.log('║                                                            ║');
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log(`║  🌐 Сайт:        http://localhost:${PORT}                  ║`);
    console.log(`║  📡 API:         http://localhost:${PORT}/api/order        ║`);
    console.log(`║  📊 Статистика:  http://localhost:${PORT}/api/stats        ║`);
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log(`║  🤖 Bot Token:   ${BOT_TOKEN.substring(0, 15)}...          ║`);
    console.log(`║  👥 Admin Chat:  ${ADMIN_CHAT_IDS.join(', ')}              ║`);
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log('║  ✅ Сервер готов принимать заявки!                        ║');
    console.log('║                                                            ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    
    // Отправка тестового сообщения в группу
    const testMessage = `
✅ <b>Сервер ChiParts запущен на Render!</b>

Статус: ✅ Работает нормально
Время запуска: ${new Date().toLocaleString('ru-RU')}
Порт: ${PORT}
URL: https://${process.env.RENDER_EXTERNAL_URL || 'localhost'}

Сервер готов принимать заявки с сайта.
    `;
    
    sendTelegramMessage(testMessage).then(() => {
        console.log('✅ Тестовое сообщение отправлено в группу');
    }).catch(err => {
        console.error('❌ Не удалось отправить тестовое сообщение:', err);
    });
});