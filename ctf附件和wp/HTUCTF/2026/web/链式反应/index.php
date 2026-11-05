<?php
error_reporting(0);
include("flag.php");
highlight_file(__FILE__);

class Software
{
    private $plugin;

    public function __destruct()
    {
        $hook = $this->plugin->dispatch();
        $hook();
    }
}

class Plugin
{
    private $config;

    public function __call($name, $args)
    {
        return $this->config->loader;
    }
}

class Config
{
    private $worker;

    public function __get($name)
    {
        return $this->worker;
    }
}

class Worker
{
    private $eagle;

    public function __invoke()
    {
        echo $this->eagle;
    }
}

class Eagle
{
    private $token;
    private $armed = false;

    public function __wakeup()
    {
        $this->armed = ($this->token === "black-eagle");
    }

    public function __toString()
    {
        if ($this->armed) {
            global $flag;
            echo $flag;
        }
        return "";
    }
}

$raw = $_POST['data'] ?? $_GET['data'] ?? null;

if ($raw === null) {
    echo "<br>用 <b>?data=</b> 传点东西进来。";
} else {
    $obj = @unserialize($raw);

    if (!is_object($obj) || !($obj instanceof Software)) {
        die("<br>入口对象非法，链式反应无法启动。");
    }

    unset($obj);
    echo "<br>链式反应已终止。";
}

用 ?data= 传点东西进来。