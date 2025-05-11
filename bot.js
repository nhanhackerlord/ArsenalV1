const fs = require('fs');
const https = require('https');
const TelegramBot = require('node-telegram-bot-api');

// === CONFIG ===
const TELEGRAM_TOKEN = '7567331917:AAHPY5MjMiWV8_1STW2q5Q7sbzGiAokpbio'; // Thay bằng token bot thật
const CHAT_ID = '-1002673143239'; // Thay bằng chat_id thật
const PROXY_URLS = [
    'https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&country=vn&proxy_format=ipport&format=text&timeout=20000',
    'https://www.proxy-list.download/api/v1/get?type=https',
    'https://www.socks-proxy.net/',
    'https://www.proxy-listen.de/ProxyList/free-proxy-list.txt',
    'https://www.sslproxies.org/',
    'https://www.us-proxy.org/',
    'https://www.freeproxylists.net/',
    'https://www.proxynova.com/proxy-server-list/',
    'https://www.freesockslist.com/',
    'https://www.proxyserverlist24.top/freeproxy/',
    'https://www.infosniper.net/proxy_list.txt',
    'https://www.geonode.com/proxies'
]; // Các nguồn API proxy khác nhau

const bot = new TelegramBot(TELEGRAM_TOKEN, { polling: false });

// === HÀM LẤY PROXY TỪ NHIỀU NGUỒN ===
function fetchAndSendProxy() {
    let allProxies = [];

    // Lặp qua từng URL để lấy proxy
    PROXY_URLS.forEach(url => {
        https.get(url, (res) => {
            let data = '';

            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                const proxies = data.trim().split('\n').filter(line => line.trim());
                allProxies = [...allProxies, ...proxies]; // Gộp tất cả proxy từ các nguồn

                // Loại bỏ các proxy trùng lặp
                allProxies = [...new Set(allProxies)];

                const proxyCount = allProxies.length;

                const now = new Date();
                const time = now.toLocaleString('en-GB', {
                    timeZone: 'Asia/Ho_Chi_Minh',
                    hour12: false
                }).replace(',', '');

                fs.appendFile('proxy.txt', allProxies.join('\n') + '\n', (err) => {
                    if (err) return console.error('[❌] Lỗi ghi file:', err);

                    console.log(`[✅] proxy.txt đã cập nhật (${proxyCount} proxies)`);

                    const caption = `Count: ${proxyCount}\nTime: ${time}\nFree Proxy On @Beonetworkjs\n🌸 𝐁𝐞𝐨𝐍𝐞𝐭𝐰𝐨𝐫𝐤 𝐉𝐒 🌸`;

                    bot.sendDocument(CHAT_ID, 'proxy.txt', {
                        caption: caption,
                        parse_mode: 'HTML'
                    }).then(() => {
                        console.log('[📤] Đã gửi proxy.txt kèm caption lên Telegram');
                    }).catch(error => {
                        console.error('[❌] Gửi Telegram lỗi:', error.message);
                    });
                });
            });
        }).on('error', err => {
            console.error('[❌] Tải proxy lỗi:', err.message);
        });
    });
}

// === CHẠY NGAY VÀ LẶP MỖI 10 PHÚT ===
fetchAndSendProxy();