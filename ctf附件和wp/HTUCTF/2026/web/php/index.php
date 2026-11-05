<?php
include("flag.php");
highlight_file(__FILE__);

$pass1 = isset($_GET['a'])
    && $_GET['a'] !== "admin"
    && $_GET['a'][0] == "admin";

$pass2 = isset($_GET['num'])
    && strlen($_GET['num']) < 5
    && $_GET['num'] > 10000;

$pass3 = isset($_POST['x'], $_POST['y'])
    && $_POST['x'] !== $_POST['y']
    && md5($_POST['x']) == md5($_POST['y']);

if ($pass1 && $pass2 && $pass3) {
    echo "三关全过，算你有点东西，flag 拿去。";
    echo $flag;
} else {
    echo "就这？三关都过不去，还想拿 flag？";
}
