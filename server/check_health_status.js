const { initDatabase, all, saveDatabase } = require('./config/database');

async function checkHealthStatus() {
    try {
        await initDatabase();
        
        const healthStatuses = all('SELECT DISTINCT health_status FROM elderly');
        console.log('Health status values in database:');
        console.log(healthStatuses);
        
        const elderlyData = all('SELECT id, name, health_status, risk_level FROM elderly LIMIT 10');
        console.log('\nSample elderly data:');
        console.log(elderlyData);
        
        saveDatabase();
    } catch (error) {
        console.error('Error:', error);
    }
}

checkHealthStatus();