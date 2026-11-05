<?php
header('Content-Type: text/html; charset=utf-8');

$flag_file = '/opt/ctf/internal/flag.txt';
$remote = $_SERVER['REMOTE_ADDR'] ?? '';

if (in_array($remote, ['127.0.0.1', '::1'], true)) {
    foreach (['HTTP_X_FORWARDED_FOR', 'HTTP_CLIENT_IP', 'HTTP_X_REAL_IP', 'HTTP_FORWARDED'] as $h) {
        if (!empty($_SERVER[$h])) {
            exit('Hacker?');
        }
    }

    if (!preg_match('#^qwb2026#i', $_SERVER['HTTP_USER_AGENT'] ?? '')) {
        exit('Hacker?');
    }

    header('Content-Type: text/plain; charset=utf-8');
    echo trim((string)file_get_contents($flag_file)), PHP_EOL;
    exit;
}

highlight_file(__FILE__);

if (!isset($_REQUEST['url'])) {
    exit;
}
$url = (string)$_REQUEST['url'];

if (preg_match('#(file|dict|ftp|tftp|sftp|ssh|smb|telnet|ldapi|phar|expect|zlib|glob|data|zip):/+#i', $url)) {
    die('Hacker?');
}

if (strpos($url, '\\') !== false || substr_count($url, '@') > 1) {
    die('Hacker?');
}
$host = strtolower(trim((string)parse_url($url, PHP_URL_HOST), '[]'));
if ($host !== '127.0.0.1' && $host !== '::1' && $host !== 'localhost') {
    die('Hacker?');
}

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_HEADER, 0);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 0);
curl_setopt($ch, CURLOPT_USERAGENT, 'internal-preview/1.0');
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 3);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
curl_exec($ch);
