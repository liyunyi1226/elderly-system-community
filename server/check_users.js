const { initDatabase, all, saveDatabase } = require('./config/database');

async function checkUsers() {
    try {
        await initDatabase();
        
        const users = all('SELECT id, username, real_name, role FROM users');
        console.log('Users in database:');
        console.log(users);
        
        saveDatabase();
    } catch (error) {
        console.error('Error:', error);
    }
}

checkUsers();