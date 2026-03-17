SiteGuard Safety Monitor

SiteGuard is a Raspberry Pi–based construction site safety monitoring system designed to collect, process, and display live environmental safety data. The system is built around a Raspberry Pi 4 Model B and uses multiple sensors to monitor conditions such as air quality, weather, wind speed, motion, and noise levels.

The project is intended to serve as a low-cost, deployable prototype that can help identify potentially hazardous site conditions before they lead to incidents. Sensor data is collected in real time, processed through a modular architecture, logged locally, and displayed through a web-based dashboard.

---

Project Features

- Real-time sensor monitoring
- Alert generation when thresholds are exceeded
- Local event and reading storage using SQLite
- Web dashboard for live metrics and recent trends
- Modular architecture for adding new sensors later

---

Planned / Supported Sensor Inputs

- BME280  
  - Temperature
  - Humidity
  - Pressure

- PMS5003  
  - PM2.5 / air quality

- Microphone / noise sensor  
  - Estimated dBA level

Potential Future Add-ons

- PIR motion sensor  
  - Motion detection

- Anemometer  
  - Wind speed

---

Repository Structure

```text
safety-monitor/
├── collector/
│   ├── main.py
│   ├── sensors/
│   │   ├── base.py
│   │   ├── weather.py
│   │   ├── anemometer.py
│   │   ├── mic_noise.py
│   │   └── pir_motion.py
│   ├── processing/
│   │   ├── filters.py
│   │   ├── derived.py
│   │   └── rules.py
│   ├── messaging/
│   │   └── zmq_pub.py
│   └── storage/
│       └── sqlite.py
├── ui/
│   ├── server.py
│   ├── messaging/
│   │   └── zmq_sub.py
│   ├── templates/
│   │   └── dashboard.html
│   └── static/
│       ├── style.css
│       └── dashboard.js
├── scripts/
│   ├── collector.service
│   └── ui.service
├── config/
│   └── config.yaml
├── requirements.txt
└── README.md

Github Repo: https://github.com/JakobieGuger/Siteguard