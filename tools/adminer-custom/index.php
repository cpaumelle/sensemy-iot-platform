<?php
// index.php - Adminer Favorites (V4)
$favorites = [
    'Ingest DB - V4' => [
        'server' => 'ingest-database-v4',
        'username' => getenv('V4_INGEST_DB_USER'),
        'db' => getenv('V4_INGEST_DB_NAME'),
    ],
    'Device DB - V4' => [
        'server' => 'device-database-v4',
        'username' => getenv('V4_DEVICE_DB_USER'),
        'db' => getenv('V4_DEVICE_DB_NAME'),
    ],
    'Analytics DB - V4' => [
        'server' => 'analytics-database-v4',
        'username' => getenv('V4_ANALYTICS_DB_USER'),
        'db' => getenv('V4_ANALYTICS_DB_NAME'),
    ],
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V4 Database Shortcuts</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2em; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 2em; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .db-link { display: block; padding: 1em; margin: 1em 0; background: #e3f2fd; border-radius: 5px; text-decoration: none; color: #1976d2; }
        .db-link:hover { background: #bbdefb; }
        .desc { font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Database Shortcuts</h1>
        <?php foreach ($favorites as $label => $data): ?>
             <a href="adminer.php?pgsql=<?= urlencode($data['server']) ?>&username=<?= urlencode($data['username']) ?>&db=<?= urlencode($data['db']) ?>" class="db-link">
                <?= htmlspecialchars($data['icon']) ?> <strong><?= htmlspecialchars($label) ?></strong><br>
                <span class="desc"><?= htmlspecialchars($data['description']) ?></span>
            </a>
        <?php endforeach; ?>
        
        <p style="text-align: center; margin-top: 2em;">
            <a href="adminer.php" style="color: #666;">Standard Adminer Login</a>
        </p>
    </div>
</body>
</html>
